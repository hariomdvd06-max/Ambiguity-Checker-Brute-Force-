class AmbiguityDetector:
    def __init__(self, grammar, parse_trees):
        self.grammar = grammar
        self.parse_trees = parse_trees
        self.is_ambiguous = False

    def detect_ambiguity(self):
        distinct_count = self.count_distinct_trees(self.parse_trees)
        self.is_ambiguous = distinct_count > 1
        return self.is_ambiguous

    def count_distinct_trees(self, trees):
        unique_hashes = set()
        for t in trees:
            unique_hashes.add(t.get_structural_hash())
        return len(unique_hashes)

    def compare_tree_structures(self, tree1, tree2):
        return tree1.compare_with(tree2)

    def find_conflicting_productions(self):
        return []

    def identify_ambiguous_substrings(self):
        return []

    def get_ambiguity_report(self):
        self.detect_ambiguity()
        return {
            'is_ambiguous': self.is_ambiguous,
            'total_trees': len(self.parse_trees),
            'distinct_trees': self.count_distinct_trees(self.parse_trees),
            'severity': self.calculate_ambiguity_severity()
        }

    def calculate_ambiguity_severity(self):
        count = self.count_distinct_trees(self.parse_trees)
        if count <= 1:
            return 'low'
        elif count <= 5:
            return 'medium'
        return 'high'

    def suggest_disambiguated_grammar(self):
        return "Disambiguation suggestions not yet implemented."

    def analyze_structural_differences(self, tree1, tree2):
        return "Structural difference analysis not yet implemented."

    def generate_conflict_explanation(self):
        if not self.is_ambiguous:
            return "No conflicts. Grammar is unambiguous for this string."
        return "Multiple valid parse trees exist, indicating ambiguity."


import json
import csv
from datetime import datetime
import io

