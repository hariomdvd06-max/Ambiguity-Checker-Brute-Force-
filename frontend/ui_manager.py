import os
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
