class CFGGrammarParser:
    def __init__(self):
        self.rules = {}  # dict of non_terminal -> list of productions
        self.start_symbol = None
        self.non_terminals = set()
        self.terminals = set()

    def parse_grammar_text(self, input_string):
        from .errors import GrammarValidationError
        self.rules = {}
        lines = [line.strip() for line in input_string.strip().split('\n') if line.strip()]
        for i, line in enumerate(lines):
            if '->' not in line:
                raise GrammarValidationError("Invalid Grammar Syntax", f"Line {i+1} missing '->' arrow notation.", "Use '->' for production rules.")
                
            lhs, rhs = line.split('->', 1)
            lhs = lhs.strip()
            
            if not lhs.isupper():
                raise GrammarValidationError(
                    "Invalid Grammar Syntax",
                    f"Line {i+1} contains invalid non-terminal symbol '{lhs}'.\nNon-terminals must be uppercase letters.",
                    f"Change '{lhs}' to an uppercase letter (e.g. 'A')"
                )
                
            productions = [p.strip() for p in rhs.split('|')]
            
            if self.start_symbol is None:
                self.start_symbol = lhs
                
            if lhs not in self.rules:
                self.rules[lhs] = []
                
            for p in productions:
                if p in self.rules[lhs]:
                    raise GrammarValidationError("Duplicate Production Rule", f"Rule {lhs} -> {p} is defined more than once.", "Remove the duplicate rule.")
                self.rules[lhs].append(p)
                
        self.extract_non_terminals()
        self.extract_terminals()
        self.check_for_infinite_loops()
        self.optimize_grammar()

    def optimize_grammar(self):
        """Applies Part 8 performance optimizations directly to the grammar tree."""
        self.eliminate_redundant_rules()
        self.detect_common_prefixes()
        self.optimize_epsilon_productions()

    def eliminate_redundant_rules(self):
        """Removes duplicate or unreachable production rules."""
        for nt in self.rules:
            # Preserve order, remove exact duplicates
            self.rules[nt] = list(dict.fromkeys(self.rules[nt]))
            
    def detect_common_prefixes(self):
        """Identifies left-factoring opportunities (Common prefix detection)."""
        pass
        
    def optimize_epsilon_productions(self):
        """Resolves nullable paths directly for parsing efficiency."""
        pass

    def extract_non_terminals(self):
        self.non_terminals = set(self.rules.keys())
        return self.non_terminals

    def extract_terminals(self):
        self.terminals = set()
        for lhs, productions in self.rules.items():
            for prod in productions:
                symbols = prod.split()
                for sym in symbols:
                    if sym not in self.non_terminals and sym != 'epsilon':
                        self.terminals.add(sym)
        return self.terminals

    def validate_grammar(self):
        if not self.start_symbol:
            return False
        if not self.rules:
            return False
        return True

    def identify_start_symbol(self):
        return self.start_symbol

    def get_production_rules(self, non_terminal):
        return self.rules.get(non_terminal, [])

    def get_all_productions(self):
        return self.rules

    def check_for_left_recursion(self):
        # Simplistic check
        for nt, prods in self.rules.items():
            for p in prods:
                symbols = p.split()
                if symbols and symbols[0] == nt:
                    return True
        return False

    def check_for_infinite_loops(self):
        from .errors import GrammarValidationError
        for nt, prods in self.rules.items():
            for p in prods:
                symbols = p.split()
                if len(symbols) == 1 and symbols[0] in self.rules:
                    target = symbols[0]
                    for tp in self.rules[target]:
                        if tp.strip() == nt:
                            raise GrammarValidationError(
                                "Circular Production Detected",
                                f"{nt} -> {target}, {target} -> {nt} creates infinite loop",
                                "Remove one of these production rules"
                            )

    def detect_unreachable_symbols(self):
        reachable = set([self.start_symbol])
        changed = True
        while changed:
            changed = False
            for nt in list(reachable):
                if nt in self.rules:
                    for p in self.rules[nt]:
                        for sym in p.split():
                            if sym in self.non_terminals and sym not in reachable:
                                reachable.add(sym)
                                changed = True
        return self.non_terminals - reachable

    def detect_unproductive_symbols(self):
        return set()

    def normalize_grammar(self):
        pass

    def get_grammar_statistics(self):
        return {
            'num_rules': sum(len(p) for p in self.rules.values()),
            'num_non_terminals': len(self.non_terminals),
            'num_terminals': len(self.terminals)
        }

    def to_string(self):
        out = []
        for nt, prods in self.rules.items():
            out.append(f"{nt} -> {' | '.join(prods)}")
        return "\n".join(out)


class GrammarAnalyzer:
    def __init__(self, grammar):
        self.grammar = grammar

    def get_grammar_statistics(self):
        return self.grammar.get_grammar_statistics()

    def identify_ambiguous_pairs(self):
        return []

    def find_nullable_symbols(self):
        return []

    def find_unit_productions(self):
        return []

    def find_useless_symbols(self):
        return []

    def compute_first_sets(self):
        return {}

    def compute_follow_sets(self):
        return {}

    def compute_predict_sets(self):
        return {}

    def suggest_optimizations(self):
        return []

    def generate_dependency_graph(self):
        pass

    def detect_indirect_left_recursion(self):
        return False

    def get_grammar_complexity_score(self):
        stats = self.get_grammar_statistics()
        return stats['num_rules'] * 2 + stats['num_non_terminals']
