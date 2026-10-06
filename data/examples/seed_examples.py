import sys
import os

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager
from backend.grammar_parser import CFGGrammarParser

def seed_examples():
    db = DatabaseManager()
    
    examples = [
        {
            "name": "Simple Ambiguous",
            "description": "Basic ambiguity example",
            "grammar": "S -> A B | C D\nA -> a\nB -> b\nC -> a\nD -> b",
            "start": "S",
            "is_ambiguous": True,
            "difficulty": "beginner"
        },
        {
            "name": "Arithmetic Expression",
            "description": "Classic compiler design example - dangling operator",
            "grammar": "E -> E + E | E * E | ( E ) | id",
            "start": "E",
            "is_ambiguous": True,
            "difficulty": "intermediate"
        },
        {
            "name": "Balanced Parentheses",
            "description": "Unambiguous grammar - deterministic parsing",
            "grammar": "S -> ( S ) S | epsilon",
            "start": "S",
            "is_ambiguous": False,
            "difficulty": "beginner"
        },
        {
            "name": "Dangling Else",
            "description": "Classic compiler ambiguity problem",
            "grammar": "S -> if E then S | if E then S else S | x\nE -> true | false",
            "start": "S",
            "is_ambiguous": True,
            "difficulty": "advanced"
        },
        {
            "name": "Complex Nested Expressions",
            "description": "Multiple levels of ambiguity",
            "grammar": "E -> E + E | E * E | E ^ E | ( E ) | id\nT -> a | b | c",
            "start": "E",
            "is_ambiguous": True,
            "difficulty": "advanced"
        }
    ]

    count = 0
    for ex in examples:
        all_g = db.get_all_grammars()
        if any(g['name'] == ex['name'] for g in all_g):
            continue
            
        parser = CFGGrammarParser()
        parser.parse_grammar_text(ex['grammar'])
        parser.start_symbol = ex['start']
        
        if parser.validate_grammar():
            gid = db.save_grammar(ex['name'], ex['description'], parser)
            cursor = db.conn.cursor()
            cursor.execute('''
                UPDATE grammars 
                SET is_example = TRUE, is_ambiguous = ?, difficulty_level = ?
                WHERE grammar_id = ?
            ''', (ex['is_ambiguous'], ex['difficulty'], gid))
            db.conn.commit()
            print(f"Seeded Example: {ex['name']}")
            count += 1
            
    if count == 0:
        print("Example grammars are already seeded.")
    else:
        print(f"Successfully seeded {count} example grammars.")

if __name__ == "__main__":
    seed_examples()
