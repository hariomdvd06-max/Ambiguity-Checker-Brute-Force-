import unittest
import os
import sys

# Ensure project root is loaded
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.grammar_parser import CFGGrammarParser
from backend.recursive_parser import RecursiveDescentParser
from backend.ambiguity_detector import AmbiguityDetector
from database.db_manager import DatabaseManager
from backend.errors import GrammarValidationError, ParsingError

class TestGrammarParser(unittest.TestCase):
    def test_valid_grammar(self):
        parser = CFGGrammarParser()
        parser.parse_grammar_text("S -> A B\\nA -> a\\nB -> b")
        parser.start_symbol = "S"
        self.assertTrue(parser.validate_grammar())

    def test_invalid_grammar_loop(self):
        parser = CFGGrammarParser()
        with self.assertRaises(GrammarValidationError):
            parser.parse_grammar_text("S -> S")
            parser.start_symbol = "S"
            parser.validate_grammar()
            
    def test_missing_start_symbol(self):
        parser = CFGGrammarParser()
        parser.parse_grammar_text("A -> a")
        parser.start_symbol = ""
        self.assertFalse(parser.validate_grammar())

class TestRecursiveParser(unittest.TestCase):
    def test_parsing_valid_string(self):
        g = CFGGrammarParser()
        g.parse_grammar_text("S -> a b")
        g.start_symbol = "S"
        g.validate_grammar()
        
        parser = RecursiveDescentParser(g)
        trees = parser.parse("ab")
        self.assertEqual(len(trees), 1)
        self.assertEqual(trees[0].get_yield(), "ab")

    def test_invalid_terminal_in_string(self):
        g = CFGGrammarParser()
        g.parse_grammar_text("S -> a b")
        g.start_symbol = "S"
        g.validate_grammar()
        
        parser = RecursiveDescentParser(g)
        with self.assertRaises(ParsingError):
            parser.parse("xyz")

class TestAmbiguityDetection(unittest.TestCase):
    def test_ambiguous_grammar(self):
        g = CFGGrammarParser()
        g.parse_grammar_text("S -> A | B\\nA -> a\\nB -> a")
        g.start_symbol = "S"
        g.validate_grammar()
        
        parser = RecursiveDescentParser(g)
        trees = parser.parse("a")
        
        detector = AmbiguityDetector(g, trees)
        self.assertTrue(detector.detect_ambiguity())
        
        # Test tree comparison hash functionality implicitly tested here
        self.assertGreater(detector.count_distinct_trees(detector.parse_trees), 1)

    def test_unambiguous_grammar(self):
        g = CFGGrammarParser()
        g.parse_grammar_text("S -> ( S ) | a")
        g.start_symbol = "S"
        g.validate_grammar()
        
        parser = RecursiveDescentParser(g)
        trees = parser.parse("(a)")
        
        detector = AmbiguityDetector(g, trees)
        self.assertFalse(detector.detect_ambiguity())
        self.assertEqual(detector.count_distinct_trees(detector.parse_trees), 1)

class TestDatabaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseManager()

    def test_crud_grammar(self):
        g = CFGGrammarParser()
        g.parse_grammar_text("S -> x y z")
        g.start_symbol = "S"
        g.validate_grammar()
        
        # Create
        gid = self.db.save_grammar("Test_Integration_Grammar", "desc", g)
        self.assertIsNotNone(gid)
        
        # Read
        loaded = self.db.load_grammar(gid)
        self.assertEqual(loaded['name'], "Test_Integration_Grammar")
        self.assertEqual(loaded['start_symbol'], "S")
        
        # Delete
        self.db.delete_grammar(gid)
        loaded_after = self.db.load_grammar(gid)
        self.assertIsNone(loaded_after)

if __name__ == '__main__':
    unittest.main()
