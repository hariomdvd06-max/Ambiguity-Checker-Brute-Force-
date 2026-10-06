from .tree_visualizer import ParseTree, ParseTreeNode

class RecursiveDescentParser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.memo = {}
        self.visited_states = set()
        self.trees = []
        self.max_depth = 100
        self.timeout_seconds = 60
        self.nodes_explored = 0

    def set_max_depth(self, depth):
        self.max_depth = depth

    def set_timeout(self, seconds):
        self.timeout_seconds = seconds

    def clear_memo(self):
        self.memo = {}
        self.visited_states = set()

    def memoize_result(self, state, result):
        self.memo[state] = result

    def check_epsilon_production(self):
        # Additional checks if grammar uses epsilon
        pass

    def get_parsing_statistics(self):
        return {
            "nodes_explored": self.nodes_explored,
            "max_depth": self.max_depth,
            "trees_found": len(self.trees)
        }

    def parse(self, target_string):
        from .errors import ParsingError
        
        if len(target_string) > 1000:
            raise ParsingError("String Too Long", "Target string exceeds 1000 characters limit.", "Provide a shorter string.")
            
        single_char_terminals = {t for t in self.grammar.terminals if len(t) == 1}
        multi_char_terminals = {t for t in self.grammar.terminals if len(t) > 1}
        
        if not multi_char_terminals and single_char_terminals:
            for char in target_string.replace(" ", ""):
                if char not in single_char_terminals and char != 'epsilon':
                    raise ParsingError(
                        "String Contains Invalid Symbols",
                        f"String contains '{char}' which is not in grammar terminals",
                        f"Valid Terminals: {{{', '.join(self.grammar.terminals)}}}"
                    )
                    
        return self.find_all_derivations(target_string)

    def find_all_derivations(self, target_string):
        self.trees = []
        self.clear_memo()
        self.nodes_explored = 0
        self.target_string = target_string
        
        if not self.grammar.start_symbol:
            return []

        # Start recursive parsing
        results = self.parse_symbol(self.grammar.start_symbol, target_string, 0)
        
        # After building valid derivation paths that consume the entire string, we build trees
        for res in results:
            if not res['remaining']: # Fully consumed
                tree = self.build_parse_tree(res['derivation'])
                self.trees.append(tree)

        return self.trees

    def parse_symbol(self, symbol, remaining_string, depth):
        self.nodes_explored += 1
        
        if depth > self.max_depth:
            # We reached the derivation depth limit without consuming the string.
            return []
            
        state = (symbol, remaining_string, depth)
        if state in self.visited_states:
            return self.memo.get(state, [])
            
        self.visited_states.add(state)
        results = []
        
        if symbol in self.grammar.terminals or symbol not in self.grammar.non_terminals:
            # Match terminal
            res = self.match_terminal(symbol, remaining_string)
            if res is not None:
                results.append({
                    'derivation': [(symbol, None, True)],
                    'remaining': res
                })
        else:
            # Expand non-terminal
            for production in self.grammar.get_production_rules(symbol):
                symbols = production.split()
                if symbols == ['epsilon']:
                    symbols = []
                
                # Kick off expansion of the RHS symbols
                prod_results = self.expand_non_terminal(symbols, remaining_string, depth + 1)
                for pr in prod_results:
                    results.append({
                        'derivation': [(symbol, production, False)] + pr['derivation'],
                        'remaining': pr['remaining']
                    })
                
        self.memoize_result(state, results)
        return results

    def match_terminal(self, terminal, remaining_string):
        remaining_string = remaining_string.lstrip()
        if remaining_string.startswith(terminal):
            return remaining_string[len(terminal):].lstrip()
        return None

    def expand_non_terminal(self, symbols, remaining_string, depth):
        if not symbols:
            return [{'derivation': [], 'remaining': remaining_string}]
            
        first_symbol = symbols[0]
        rest_symbols = symbols[1:]
        
        results = []
        first_results = self.parse_symbol(first_symbol, remaining_string, depth)
        
        for res in first_results:
            new_remaining = res['remaining']
            # Recursively expand the rest of the symbols
            rest_results = self.expand_non_terminal(rest_symbols, new_remaining, depth)
            for rres in rest_results:
                results.append({
                    'derivation': res['derivation'] + rres['derivation'],
                    'remaining': rres['remaining']
                })
            
        return results

    def build_parse_tree(self, derivation_path):
        # derivation_path is a list of tuples: (symbol, production, is_terminal)
        if not derivation_path:
            return None
            
        # Reconstruct tree from top-down left-to-right derivation path
        path_iter = iter(derivation_path)
        
        def build_node():
            try:
                sym, prod, is_term = next(path_iter)
            except StopIteration:
                return None
                
            node = ParseTreeNode(sym, prod, is_term)
            if not is_term and prod:
                rhs_symbols = prod.split()
                if rhs_symbols != ['epsilon']:
                    for _ in rhs_symbols:
                        child = build_node()
                        if child:
                            node.add_child(child)
            return node
            
        root = build_node()
        return ParseTree(root)
