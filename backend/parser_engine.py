import re
from typing import List, Dict, Any, Optional, Set, Tuple

class ParseNode:
    def __init__(self, symbol: str, children: Optional[List['ParseNode']] = None):
        self.symbol = symbol
        self.children = children if children is not None else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "children": [c.to_dict() for c in self.children]
        }

    def s_expr(self) -> str:
        """Unambiguous parenthesized S-expression AST stringifier for structural deduplication."""
        if not self.children:
            return self.symbol
        return f"({self.symbol} {' '.join(c.s_expr() for c in self.children)})"

    def get_yield(self) -> List[str]:
        """Leaf tokens yield."""
        if not self.children:
            return [self.symbol] if self.symbol not in ["ε", "eps", "epsilon"] else []
        leaves = []
        for c in self.children:
            leaves.extend(c.get_yield())
        return leaves


class EarleyItem:
    def __init__(self, lhs: str, rhs: Tuple[str, ...], dot: int, origin: int, operation: str = ""):
        self.lhs = lhs
        self.rhs = tuple(rhs)
        self.dot = dot
        self.origin = origin
        self.operation = operation

    def next_symbol(self) -> Optional[str]:
        if self.dot < len(self.rhs):
            return self.rhs[self.dot]
        return None

    def is_complete(self) -> bool:
        return self.dot >= len(self.rhs) or self.rhs == ("ε",)

    def rule_string(self) -> str:
        rhs_list = list(self.rhs)
        if rhs_list == ["ε"]:
            return f"{self.lhs} -> ε •"
        rhs_list.insert(self.dot, "•")
        return f"{self.lhs} -> {' '.join(rhs_list)}"

    def key(self) -> Tuple[str, Tuple[str, ...], int, int]:
        return (self.lhs, self.rhs, self.dot, self.origin)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule_string(),
            "item": self.rule_string(),
            "origin": self.origin,
            "operation": self.operation
        }


class CFGParserEngine:
    def __init__(self, start_symbol: str, rules: Dict[str, List[List[str]]]):
        self.start_symbol = start_symbol.strip()
        self.rules: Dict[str, List[Tuple[str, ...]]] = {}
        for lhs, prods in rules.items():
            cleaned_lhs = lhs.strip()
            self.rules[cleaned_lhs] = [tuple(p) for p in prods]

        self.non_terminals: Set[str] = set(self.rules.keys())
        self.terminals: Set[str] = set()

        for lhs, prods in self.rules.items():
            for p in prods:
                for sym in p:
                    if sym not in self.non_terminals and sym not in ["ε", "eps", "epsilon"]:
                        self.terminals.add(sym)

    @staticmethod
    def tokenize_rhs(rhs_str: str, non_terminals: Optional[Set[str]] = None) -> List[str]:
        cleaned = rhs_str.strip()
        if cleaned.lower() in ["ε", "eps", "epsilon", "''", '""', ""]:
            return ["ε"]

        # Intelligent Lexer: handles multi-character identifiers, multi-char operators, single symbols
        # Sort candidate non-terminals and known multi-char tokens by length descending
        candidates = []
        if non_terminals:
            candidates.extend([re.escape(nt) for nt in sorted(non_terminals, key=len, reverse=True)])

        # Multi-char operators and common keywords
        common_tokens = [
            r'&&', r'\|\|', r'==', r'!=', r'<=', r'>=', r'->', r'=>',
            r'\btrue\b', r'\bfalse\b', r'\bif\b', r'\bthen\b', r'\belse\b',
            r'\bid\b', r'\bnum\b'
        ]
        candidates.extend(common_tokens)

        # General identifiers [A-Za-z_][A-Za-z0-9_']* or numbers or single char operators
        general_pattern = r'[A-Za-z_][A-Za-z0-9_\']*|[0-9]+|[+\-*/()^%,;<>!=ε]'

        pattern = '|'.join(candidates + [general_pattern])
        tokens = [m.group(0) for m in re.finditer(pattern, cleaned)]
        return tokens if tokens else [cleaned]

    def extract_tokens(self, target_string: str) -> List[str]:
        cleaned = target_string.strip()
        if cleaned.lower() in ["ε", "eps", "epsilon", "''", '""', ""]:
            return []

        # If user explicitly provided space-delimited string, e.g. "id + id * id", "a b a", "( ( a ) )"
        # Match tokens by prioritizing grammar terminals (longest match first)
        terminals_sorted = [re.escape(t) for t in sorted(self.terminals, key=len, reverse=True) if t]
        
        fallback_pattern = r'&&|\|\||==|!=|<=|>=|->|=>|[A-Za-z_][A-Za-z0-9_\']*|[0-9]+|[+\-*/()^%,;<>!=]'
        if terminals_sorted:
            pattern = '|'.join(terminals_sorted + [fallback_pattern])
        else:
            pattern = fallback_pattern

        tokens = [m.group(0) for m in re.finditer(pattern, cleaned)]
        return tokens

    def generate_earley_chart(self, tokens: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], bool, Any]:
        """
        Runs generalized Earley parser recognizing arbitrary CFGs in O(n^3) time.
        Returns (output_chart, execution_steps, is_recognized, internal_data).
        """
        n = len(tokens)
        chart: List[List[EarleyItem]] = [[] for _ in range(n + 1)]
        chart_set: List[Set[Tuple[str, Tuple[str, ...], int, int]]] = [set() for _ in range(n + 1)]
        completed_set: List[Set[Tuple[str, int]]] = [set() for _ in range(n + 1)]
        execution_steps: List[Dict[str, Any]] = []

        def add_item(k: int, item: EarleyItem, op_type: str, reasoning: str, parent_idx: Optional[int] = None) -> bool:
            k_key = item.key()
            if k_key not in chart_set[k]:
                chart_set[k].add(k_key)
                item_idx = len(chart[k])
                chart[k].append(item)
                if item.is_complete():
                    completed_set[k].add((item.lhs, item.origin))
                execution_steps.append({
                    "step_number": len(execution_steps) + 1,
                    "target_state_set": f"S_{k}",
                    "item_index": item_idx,
                    "operation_type": op_type,
                    "item_added": item.rule_string(),
                    "origin": item.origin,
                    "human_reasoning": reasoning,
                    "highlight_parent_item": parent_idx
                })
                return True
            return False

        # Initial start item: γ -> • S at 0
        init_item = EarleyItem("γ", (self.start_symbol,), 0, 0, "INITIAL")
        add_item(
            0,
            init_item,
            "INITIAL",
            f"Step 0: Grammar me augmented start production γ -> • {self.start_symbol} add ki gayi index 0 par (State Set S_0).",
            None
        )

        for k in range(n + 1):
            i = 0
            while i < len(chart[k]):
                item = chart[k][i]
                nxt = item.next_symbol()

                if not item.is_complete() and nxt is not None:
                    # Non-terminal -> Predictor
                    if nxt in self.rules:
                        for prod in self.rules[nxt]:
                            if prod == ("ε",):
                                new_item = EarleyItem(nxt, ("ε",), 1, k, f"Predictor from ({item.lhs}->...)")
                            else:
                                new_item = EarleyItem(nxt, prod, 0, k, f"Predictor from ({item.lhs}->...)")

                            reasoning = (
                                f"Non-Terminal '{nxt}' encountered after dot (State S_{k} Item #{i}). "
                                f"Adding predicted rule ({new_item.rule_string()}) starting at state S_{k}."
                            )
                            add_item(k, new_item, "PREDICTOR", reasoning, i)

                    # Terminal match for Scanner
                    elif k < n and nxt == tokens[k]:
                        new_item = EarleyItem(item.lhs, item.rhs, item.dot + 1, item.origin, f"Scanner ('{tokens[k]}')")
                        reasoning = (
                            f"Input token '{tokens[k]}' matches terminal after dot in Item #{i}. "
                            f"Advancing dot to state S_{k+1}."
                        )
                        add_item(k + 1, new_item, "SCANNER", reasoning, i)

                # Completer
                if item.is_complete():
                    origin = item.origin
                    for prev_idx, prev_item in enumerate(chart[origin]):
                        if not prev_item.is_complete() and prev_item.next_symbol() == item.lhs:
                            new_item = EarleyItem(
                                prev_item.lhs,
                                prev_item.rhs,
                                prev_item.dot + 1,
                                prev_item.origin,
                                f"Completer: [{item.lhs}] done"
                            )
                            reasoning = (
                                f"Rule ({item.rule_string()}) completed at S_{k} with origin S_{origin}. "
                                f"Advancing symbol '{item.lhs}' in S_{origin} Item #{prev_idx} into State S_{k}."
                            )
                            add_item(k, new_item, "COMPLETER", reasoning, prev_idx)
                i += 1

        is_recognized = ("γ", (self.start_symbol,), 1, 0) in chart_set[n]

        # Format output chart
        output_chart = []
        for k in range(n + 1):
            tok_str = "ε" if k == 0 else (tokens[k-1] if k-1 < len(tokens) else "")
            tok_lbl = "Start (ε)" if k == 0 else f"Token {k}: '{tok_str}'"
            output_chart.append({
                "state_index": k,
                "state_set": f"S_{k}",
                "token": tok_str,
                "token_label": tok_lbl,
                "items": [it.to_dict() for it in chart[k]]
            })

        internal_data = {
            "chart": chart,
            "chart_set": chart_set,
            "completed_set": completed_set,
            "tokens": tokens
        }
        return output_chart, execution_steps, is_recognized, internal_data

    def find_all_parse_trees(self, tokens: List[str], internal_data: Any) -> List[ParseNode]:
        """
        Reconstructs parse trees directly from completed Earley chart reduction nodes (SPPF / backpointers).
        Enumerates up to 2 distinct valid parse trees using structural deduplication and dynamic depth guard.
        """
        chart = internal_data["chart"]
        chart_set = internal_data["chart_set"]
        completed_set = internal_data["completed_set"]

        n = len(tokens)
        max_depth = max(30, n * 4)

        memo: Dict[Tuple[str, int, int], List[ParseNode]] = {}

        def get_trees_for(sym: str, start: int, end: int, depth: int, active_path: Set[Tuple[str, int, int]]) -> List[ParseNode]:
            if depth > max_depth:
                return []

            state_key = (sym, start, end)
            if state_key in active_path:
                # Cycle prevention (e.g. A => A over the identical span)
                return []

            if state_key in memo:
                return memo[state_key]

            # Terminal symbol
            if sym in self.terminals:
                if start + 1 == end and start < n and tokens[start] == sym:
                    return [ParseNode(sym)]
                return []

            # Epsilon symbol
            if sym in ["ε", "eps", "epsilon"]:
                if start == end:
                    return [ParseNode("ε")]
                return []

            # Non-terminal symbol: find completed productions for sym with origin start in chart[end]
            rules_for_sym: List[Tuple[str, ...]] = []
            for item in chart[end]:
                if item.lhs == sym and item.origin == start and item.is_complete():
                    if item.rhs not in rules_for_sym:
                        rules_for_sym.append(item.rhs)

            trees: List[ParseNode] = []
            seen_exprs: Set[str] = set()
            new_active = active_path | {state_key}

            for rhs in rules_for_sym:
                if rhs == ("ε",):
                    cand = ParseNode(sym, [ParseNode("ε")])
                    se = cand.s_expr()
                    if se not in seen_exprs:
                        seen_exprs.add(se)
                        trees.append(cand)
                    continue

                m = len(rhs)

                def find_splits(p: int, cur_k: int):
                    if p == m:
                        if cur_k == end:
                            yield []
                        return

                    next_sym = rhs[p]
                    prefix_dot = p + 1

                    if next_sym in self.terminals:
                        next_k = cur_k + 1
                        if next_k <= end and cur_k < n and tokens[cur_k] == next_sym:
                            if (sym, rhs, prefix_dot, start) in chart_set[next_k]:
                                for rest in find_splits(p + 1, next_k):
                                    yield [(next_sym, cur_k, next_k)] + rest
                    elif next_sym in ["ε", "eps", "epsilon"]:
                        next_k = cur_k
                        if (sym, rhs, prefix_dot, start) in chart_set[next_k]:
                            for rest in find_splits(p + 1, next_k):
                                yield [(next_sym, cur_k, next_k)] + rest
                    else:
                        for next_k in range(cur_k, end + 1):
                            if (sym, rhs, prefix_dot, start) in chart_set[next_k]:
                                if (next_sym, cur_k) in completed_set[next_k]:
                                    for rest in find_splits(p + 1, next_k):
                                        yield [(next_sym, cur_k, next_k)] + rest

                for split in find_splits(0, start):
                    child_options = []
                    valid_split = True
                    for c_sym, cs, ce in split:
                        c_trees = get_trees_for(c_sym, cs, ce, depth + 1, new_active)
                        if not c_trees:
                            valid_split = False
                            break
                        child_options.append(c_trees)

                    if not valid_split:
                        continue

                    from itertools import product
                    for combo in product(*child_options):
                        cand = ParseNode(sym, list(combo))
                        se = cand.s_expr()
                        if se not in seen_exprs:
                            seen_exprs.add(se)
                            trees.append(cand)
                            if len(trees) >= 2 and sym == self.start_symbol and start == 0 and end == n:
                                memo[state_key] = trees
                                return trees
                        if len(trees) >= 2:
                            break
                    if len(trees) >= 2 and sym == self.start_symbol and start == 0 and end == n:
                        break

            memo[state_key] = trees
            return trees

        return get_trees_for(self.start_symbol, 0, n, 0, set())

    @staticmethod
    def get_leftmost_derivation_steps(root: Optional[ParseNode]) -> List[str]:
        """
        Generates clean leftmost derivation step strings, e.g. ["E => E + E", "E => a", ...]
        """
        if not root:
            return []

        sentential = [root]
        steps = []

        def sentential_to_str(nodes: List[Any]) -> str:
            res = []
            for n in nodes:
                if isinstance(n, str):
                    if n not in ["ε", "eps", "epsilon"]:
                        res.append(n)
                else:
                    if not n.children:
                        if n.symbol not in ["ε", "eps", "epsilon"]:
                            res.append(n.symbol)
                    else:
                        res.append(n.symbol)
            return ' '.join(res) if res else 'ε'

        safety = 0
        while safety < 100:
            safety += 1
            target_idx = None
            for i, n in enumerate(sentential):
                if hasattr(n, 'children') and n.children:
                    target_idx = i
                    break
            if target_idx is None:
                break

            target = sentential[target_idx]
            rhs_symbols = [c.symbol for c in target.children]
            rule_application = f"{target.symbol} => {' '.join(rhs_symbols)}"

            new_sentential = sentential[:target_idx] + list(target.children) + sentential[target_idx+1:]
            sentential = new_sentential
            steps.append(rule_application)

        return steps
