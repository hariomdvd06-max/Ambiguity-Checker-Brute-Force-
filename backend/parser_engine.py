import time
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

    def serialize(self) -> str:
        if not self.children:
            return f"Leaf({self.symbol})"
        return f"Node({self.symbol}:[{','.join(c.serialize() for c in self.children)}])"


class EarleyItem:
    def __init__(self, lhs: str, rhs: List[str], dot: int, origin: int, operation: str):
        self.lhs = lhs
        self.rhs = rhs
        self.dot = dot
        self.origin = origin
        self.operation = operation

    def next_symbol(self) -> Optional[str]:
        if self.dot < len(self.rhs):
            return self.rhs[self.dot]
        return None

    def is_complete(self) -> bool:
        return self.dot >= len(self.rhs) or (self.rhs == ["ε"])

    def rule_string(self) -> str:
        rhs_with_dot = list(self.rhs)
        if rhs_with_dot == ["ε"]:
            return f"{self.lhs} -> ε •"
        else:
            rhs_with_dot.insert(self.dot, "•")
            return f"{self.lhs} -> {' '.join(rhs_with_dot)}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule_string(),
            "origin": self.origin,
            "operation": self.operation
        }

    def key(self) -> Tuple:
        return (self.lhs, tuple(self.rhs), self.dot, self.origin)


class CFGParserEngine:
    def __init__(self, start_symbol: str, rules: Dict[str, List[List[str]]]):
        self.start_symbol = start_symbol.strip()
        self.rules = rules

    @staticmethod
    def tokenize_rhs(rhs_str: str) -> List[str]:
        rhs_str = rhs_str.strip()
        if rhs_str.lower() in ["eps", "epsilon", "ε", ""]:
            return ["ε"]
        if " " in rhs_str:
            return [t for t in rhs_str.split() if t]
        return list(rhs_str)

    def extract_tokens(self, target_string: str) -> List[str]:
        cleaned = target_string.strip()
        if cleaned in ["ε", "eps", "epsilon", ""]:
            return []
        if " " in cleaned:
            return [t for t in cleaned.split() if t]
        return list(cleaned)

    def generate_earley_chart(self, target_string: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        tokens = self.extract_tokens(target_string)
        n = len(tokens)

        # S_0 to S_n
        chart: List[List[EarleyItem]] = [[] for _ in range(n + 1)]
        seen: List[Set[Tuple]] = [set() for _ in range(n + 1)]
        execution_steps: List[Dict[str, Any]] = []

        def add_item(k: int, item: EarleyItem, op_type: str, reasoning: str, parent_idx: Optional[int] = None) -> bool:
            k_tuple = item.key()
            if k_tuple not in seen[k]:
                seen[k].add(k_tuple)
                item_idx = len(chart[k])
                chart[k].append(item)
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

        # Initial start item: γ -> • S
        init_item = EarleyItem("γ", [self.start_symbol], 0, 0, "Initial")
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
                            if prod == ["ε"]:
                                new_item = EarleyItem(nxt, ["ε"], 1, k, f"Predictor from ({item.lhs}->...)")
                            else:
                                new_item = EarleyItem(nxt, prod, 0, k, f"Predictor from ({item.lhs}->...)")
                            
                            reasoning = (
                                f"Dot ke aage Non-Terminal '{nxt}' mila (State S_{k} ke Item #{i}). "
                                f"Isliye {nxt} ke production ({new_item.rule_string()}) me dot ko starting position par rakh kar State S_{k} me add kiya gaya."
                            )
                            add_item(k, new_item, "PREDICTOR", reasoning, i)

                    # Terminal match for Scanner
                    elif k < n and nxt == tokens[k]:
                        new_item = EarleyItem(item.lhs, item.rhs, item.dot + 1, item.origin, f"Scanner ('{tokens[k]}')")
                        reasoning = (
                            f"Target string ka agla input character '{tokens[k]}' hai. "
                            f"State S_{k} ke Item #{i} ({item.rule_string()}) me dot ke aage '{tokens[k]}' match hua, "
                            f"isliye dot ko 1 position aage shift karke naye state set S_{k+1} me move kiya gaya."
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
                                f"Item #{i} ({item.rule_string()}) ke aakhir me dot pohoch gaya (rule complete). "
                                f"Iska origin index S_{origin} tha. Ab S_{origin} ke Item #{prev_idx} ({prev_item.rule_string()}) me "
                                f"'{item.lhs}' complete hone par dot ko aage badhakar State S_{k} me add kiya gaya."
                            )
                            add_item(k, new_item, "COMPLETER", reasoning, prev_idx)
                i += 1

        # Format output
        output_chart = []
        for k in range(n + 1):
            token_label = "Start (ε)" if k == 0 else f"Token {k}: '{tokens[k-1]}'"
            output_chart.append({
                "state_set": f"S_{k}",
                "token_label": token_label,
                "items": [it.to_dict() for it in chart[k]]
            })
        return output_chart, execution_steps

    def find_all_parse_trees(self, target_string: str, timeout_seconds: float = 3.0) -> Tuple[List[ParseNode], bool]:
        target_tokens = self.extract_tokens(target_string)
        n = len(target_tokens)
        max_depth = max(2 * n + 6, 14)

        results: List[ParseNode] = []
        seen_tree_signatures: Set[str] = set()
        start_time = time.time()
        timed_out = False

        def get_yield(node: ParseNode) -> List[str]:
            if not node.children:
                return [node.symbol] if node.symbol not in ["ε", "eps", "epsilon"] else []
            leaves = []
            for c in node.children:
                leaves.extend(get_yield(c))
            return leaves

        memo: Dict[Tuple[str, int, int], List[ParseNode]] = {}

        def expand_node(symbol: str, current_depth: int, ancestors: Tuple[str, ...]) -> List[ParseNode]:
            nonlocal timed_out
            if time.time() - start_time > timeout_seconds:
                timed_out = True
                return []
            if current_depth > max_depth or ancestors.count(symbol) > 2:
                return []
            if symbol not in self.rules:
                return [ParseNode(symbol)]

            memo_key = (symbol, current_depth, len(ancestors))
            if memo_key in memo:
                return memo[memo_key]

            possible_trees = []
            productions = self.rules[symbol]

            for prod in productions:
                if timed_out:
                    break
                if prod == ["ε"]:
                    possible_trees.append(ParseNode(symbol, [ParseNode("ε")]))
                    continue

                child_subtrees = []
                valid = True
                for s in prod:
                    sub = expand_node(s, current_depth + 1, ancestors + (symbol,))
                    if not sub:
                        valid = False
                        break
                    child_subtrees.append(sub)

                if valid:
                    from itertools import product
                    for combo in product(*child_subtrees):
                        cand = ParseNode(symbol, list(combo))
                        if len(get_yield(cand)) <= n:
                            possible_trees.append(cand)

            memo[memo_key] = possible_trees
            return possible_trees

        all_candidates = expand_node(self.start_symbol, 0, ())
        for tree in all_candidates:
            if get_yield(tree) == target_tokens:
                sig = tree.serialize()
                if sig not in seen_tree_signatures:
                    seen_tree_signatures.add(sig)
                    results.append(tree)
                    if len(results) >= 2:
                        break

        return results, timed_out
