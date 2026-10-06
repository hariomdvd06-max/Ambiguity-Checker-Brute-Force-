import os
import re

with open("main.py", "r", encoding="utf-8") as f:
    main_content = f.read()

# Very basic extraction:
# We know where the methods are.
menus_code = """import sys

class MenusMixin:
    def show_main_menu(self):
""" + main_content.split("def show_main_menu(self):")[1].split("def screen_load_grammar(self):")[0]

screens_code = """from backend.grammar_parser import CFGGrammarParser
from backend.recursive_parser import RecursiveDescentParser
from backend.ambiguity_detector import AmbiguityDetector
from backend.results_processor import ResultsProcessor
from backend.tree_visualizer import TreeVisualizer
from backend.errors import GrammarValidationError, ParsingError

class ScreensMixin:
    def screen_load_grammar(self):
""" + main_content.split("def screen_load_grammar(self):")[1].split("if __name__ == \"__main__\":")[0]

ui_manager_code = """import os
from database.db_manager import DatabaseManager
from .menus import MenusMixin
from .screens import ScreensMixin

class ConsoleApp(MenusMixin, ScreensMixin):
    def __init__(self):
        self.db = DatabaseManager()
        self.current_grammar_id = None
        self.current_grammar = None

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def run(self):
        while True:
            self.show_main_menu()
"""

main_code = """from frontend.ui_manager import ConsoleApp

if __name__ == "__main__":
    app = ConsoleApp()
    app.run()
"""

with open("frontend/menus.py", "w", encoding="utf-8") as f: f.write(menus_code)
with open("frontend/screens.py", "w", encoding="utf-8") as f: f.write(screens_code)
with open("frontend/ui_manager.py", "w", encoding="utf-8") as f: f.write(ui_manager_code)
with open("main.py", "w", encoding="utf-8") as f: f.write(main_code)

# rename database.py to database/schema_runner.py just to keep the logic
if os.path.exists("database.py"):
    os.rename("database.py", "database/schema_runner.py")
    
# Create schema.sql
with open("database/schema.sql", "w") as f:
    f.write("-- SQLite Schema for TOC Ambiguity Checker\\n")
