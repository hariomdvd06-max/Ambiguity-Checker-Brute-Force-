import sys

class MenusMixin:
    def show_main_menu(self):

        self.clear_screen()
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║              TOC AMBIGUITY CHECKER - MAIN MENU                ║")
        print("║                  (Grammar Analysis Tool)                      ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
        print("[1] Load Existing Grammar")
        print("[2] Create New Grammar")
        print("[3] View Example Grammars")
        print("[4] Parse String Against Grammar")
        print("[5] View Parsing History")
        print("[6] Manage Saved Grammars")
        print("[7] View Statistics & Reports")
        print("[8] Settings & Preferences")
        print("[9] Help & Documentation")
        print("[0] Exit Application")
        
        choice = input("\nEnter Choice: ")
        
        if choice == '1': self.screen_load_grammar()
        elif choice == '2': self.screen_create_grammar()
        elif choice == '3': self.screen_example_grammars()
        elif choice == '4': self.screen_parse_string()
        elif choice == '5': self.screen_parsing_history()
        elif choice == '6': self.screen_manage_grammars()
        elif choice == '7': self.screen_statistics()
        elif choice == '8': self.screen_settings()
        elif choice == '9': self.screen_help()
        elif choice == '0': sys.exit(0)

    