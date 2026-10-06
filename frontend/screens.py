from backend.grammar_parser import CFGGrammarParser
from backend.recursive_parser import RecursiveDescentParser
from backend.ambiguity_detector import AmbiguityDetector
from backend.results_processor import ResultsProcessor
from backend.tree_visualizer import TreeVisualizer
from backend.errors import GrammarValidationError, ParsingError

class ScreensMixin:
    def screen_load_grammar(self):

        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                   LOAD GRAMMAR FROM DATABASE                  ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        
        grammars = self.db.get_all_grammars()
        print(f"{'ID':<4} | {'Name':<25} | {'Rules':<5} | {'Terminals':<10} | {'Ambiguous':<9} | {'Created'}")
        print("─" * 75)
        for g in grammars:
            print(f"{g['grammar_id']:<4} | {g['name']:<25} | {g.get('total_rules', 0):<5} | {g.get('total_terminals', 0):<10} | {str(bool(g.get('is_ambiguous', False))):<9} | {g.get('created_at', '')[:10]}")
            
        choice = input("\nSelect Grammar ID (or 0 to go back): ")
        if choice == '0' or not choice.isdigit():
            return
            
        grammar_id = int(choice)
        g_data = self.db.load_grammar(grammar_id)
        if g_data:
            self.current_grammar_id = grammar_id
            self.current_grammar = CFGGrammarParser()
            self.current_grammar.parse_grammar_text(g_data['raw_grammar'])
            print(f"Loaded '{g_data['name']}' successfully.")
            input("Press Enter to continue...")
        else:
            print("Grammar not found.")
            input()

    def screen_create_grammar(self):
        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                     CREATE NEW GRAMMAR                        ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        name = input("Grammar Name: ")
        desc = input("Description: ")
        start = input("Start Symbol (default: S): ") or "S"
        
        print("\nEnter Production Rules (Leave empty line to finish):")
        rules = []
        i = 1
        while True:
            rule = input(f"Rule {i}: ")
            if not rule:
                break
            rules.append(rule)
            i += 1
            
        grammar_text = "\n".join(rules)
        print("\n[V] Validate  [S] Save  [C] Cancel")
        action = input("Choice: ").upper()
        if action == 'S':
            from backend.errors import GrammarValidationError
            parser = CFGGrammarParser()
            try:
                parser.parse_grammar_text(grammar_text)
                parser.start_symbol = start
                if parser.validate_grammar():
                    self.db.save_grammar(name, desc, parser)
                    print("\nGrammar saved successfully!")
                else:
                    print("\nGrammar validation failed: Start symbol missing.")
            except GrammarValidationError as e:
                print(e)
            input("Press Enter to continue...")

    def screen_example_grammars(self):
        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║           EXAMPLE GRAMMARS (Built-in Collection)              ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        examples = self.db.get_example_grammars()
        if not examples:
            print("No example grammars found. Run `python seed_examples.py` to seed.")
            
        for i, g in enumerate(examples):
            print(f"\nEXAMPLE {i+1}: {g['name']}")
            print("─" * 50)
            print(f"Description: {g.get('description', '')}")
            print(f"Difficulty: {str(g.get('difficulty_level', '')).upper()} | Ambiguous: {'YES' if g.get('is_ambiguous') else 'NO'}")
            print("\nGrammar:")
            print(g['raw_grammar'])
            
            print("\n[L] Load This  [N] Next Example")
            choice = input("Choice (or Enter to continue): ").upper()
            if choice == 'L':
                self.current_grammar_id = g['grammar_id']
                self.current_grammar = CFGGrammarParser()
                self.current_grammar.parse_grammar_text(g['raw_grammar'])
                self.current_grammar.start_symbol = g['start_symbol']
                print(f"Loaded '{g['name']}' successfully.")
                input("Press Enter to return to menu...")
                return
            
        input("\nPress Enter to return to menu...")

    def screen_parse_string(self):
        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                 PARSE STRING AGAINST GRAMMAR                  ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        
        if not self.current_grammar:
            print("No grammar loaded. Please load a grammar first.")
            input()
            return
            
        print(f"Current Grammar ID: {self.current_grammar_id}")
        print(f"Start Symbol: {self.current_grammar.start_symbol}")
        
        target = input("\nEnter Target String: ")
        
        print("\nAdvanced Options:")
        print("[✓] Show all parse trees")
        print("Maximum Parsing Depth: 15")
        
        action = input("\n[S] Start Parsing  [B] Back : ").upper()
        if action == 'S':
            from backend.errors import ParsingError
            parser = RecursiveDescentParser(self.current_grammar)
            parser.set_max_depth(15)
            
            try:
                trees = parser.parse(target)
                
                ambiguity = AmbiguityDetector(self.current_grammar, trees)
                is_ambiguous = ambiguity.detect_ambiguity()
                
                stats = parser.get_parsing_statistics()
                stats['is_ambiguous'] = is_ambiguous
                
                # Save session
                session_id = self.db.save_parsing_session(self.current_grammar_id, target, stats)
                
                # Save trees and derivation steps
                for i, t in enumerate(trees):
                    tree_id = self.db.save_parse_tree(session_id, i+1, t.to_dict(), t.get_derivation_sequence())
                    self.db.save_derivation_steps(tree_id, t.get_derivation_sequence())
                    
                report = ambiguity.get_ambiguity_report()
                report['explanation'] = ambiguity.generate_conflict_explanation()
                self.db.save_ambiguity_analysis(session_id, report)
                
                self.screen_parsing_results(target, stats, trees, is_ambiguous, ambiguity, session_id)
            except ParsingError as e:
                print(e)
                input("\nPress Enter to return to menu...")
            
    def screen_parsing_results(self, target, stats, trees, is_ambiguous, ambiguity, session_id):
        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                  PARSING RESULTS & ANALYSIS                   ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print(f"Input String: '{target}'")
        print(f"Nodes Explored: {stats['nodes_explored']} | Trees Found: {stats['trees_found']}")
        print("═══════════════════════════════════════════════════════════════")
        
        if is_ambiguous:
            print("AMBIGUITY STATUS: ✓ YES - GRAMMAR IS AMBIGUOUS")
        else:
            print("AMBIGUITY STATUS: ✗ NO - GRAMMAR IS UNAMBIGUOUS")
        print("═══════════════════════════════════════════════════════════════")
        
        print("\n[1] View Trees  [2] Export JSON  [3] Export Text  [4] Back")
        choice = input("Choice: ")
        if choice == '1':
            for i, t in enumerate(trees):
                print(f"\n--- Tree #{i+1} ---")
                from backend.tree_visualizer import TreeVisualizer
                vis = TreeVisualizer(t)
                print(vis.render_ascii_tree())
            input("\nPress Enter to continue...")
        elif choice == '2':
            from backend.results_processor import ResultsProcessor
            rp = ResultsProcessor(self.db)
            json_out = rp.export_to_json(session_id)
            print("\n" + json_out)
            with open(f"export_session_{session_id}.json", "w") as f: f.write(json_out)
            print(f"\nSaved to export_session_{session_id}.json")
            input("\nPress Enter...")
        elif choice == '3':
            from backend.results_processor import ResultsProcessor
            rp = ResultsProcessor(self.db)
            txt_out = rp.export_to_text(session_id)
            print("\n" + txt_out)
            with open(f"export_session_{session_id}.txt", "w", encoding='utf-8') as f: f.write(txt_out)
            print(f"\nSaved to export_session_{session_id}.txt")
            input("\nPress Enter...")

    def screen_parsing_history(self):
        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                     PARSING HISTORY LOG                       ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        if not self.current_grammar_id:
            print("Please load a grammar first to see its history.")
            input()
            return
            
        history = self.db.get_parsing_history(self.current_grammar_id)
        print(f"{'ID':<4} | {'String':<15} | {'Trees':<5} | {'Ambiguous':<9}")
        print("─" * 45)
        for h in history:
            print(f"{h['session_id']:<4} | {h['target_string']:<15} | {h.get('total_trees_found', 0):<5} | {str(bool(h.get('is_ambiguous'))):<9}")
            
        input("\nPress Enter to go back...")

    def screen_statistics(self):
        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                 STATISTICS & ANALYSIS REPORTS                 ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        stats = self.db.get_statistics()
        print(f"Total Grammars Stored: {stats.get('total_grammars', 0)}")
        input("\nPress Enter to go back...")
        
    def screen_manage_grammars(self):
        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                     MANAGE SAVED GRAMMARS                     ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        grammars = self.db.get_all_grammars()
        for g in grammars:
            print(f"[{g['grammar_id']}] {g['name']}")
        choice = input("\nEnter Grammar ID to DELETE (or 0 to go back): ")
        if choice.isdigit() and choice != '0':
            self.db.delete_grammar(int(choice))
            print("Grammar deleted successfully.")
            input("Press Enter...")
            
    def screen_help(self):
        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                     HELP & DOCUMENTATION                      ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print("TOC Ambiguity Checker validates CFG syntax, checks for loops,")
        print("and parses input strings to detect structural ambiguity.")
        print("Use A-Z for non-terminals. Use 'epsilon' for empty string.")
        print("Example Rule: S -> A B | epsilon")
        input("\nPress Enter to go back...")

    def screen_settings(self):
        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║                  SETTINGS & USER PREFERENCES                  ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        max_depth = self.db.get_user_preference("max_depth") or 15
        print(f"[1] Max Parsing Depth: {max_depth}")
        choice = input("\nSelect setting to change (or 0 to go back): ")
        if choice == '1':
            new_val = input("Enter new max depth: ")
            if new_val.isdigit():
                self.db.update_user_preference("max_depth", new_val)
                print("Setting updated.")
        input("\nPress Enter to go back...")

