import sqlite3
import json
import os
import queue
from datetime import datetime

from config import DB_PATH

class DatabaseManager:
    _pool = queue.Queue(maxsize=10)

    def __init__(self):
        self.conn = None
        self.connect_database()

    @classmethod
    def get_pooled_connection(cls):
        try:
            return cls._pool.get_nowait()
        except queue.Empty:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            conn.cursor().execute("PRAGMA foreign_keys = ON;")
            return conn

    @classmethod
    def release_connection(cls, conn):
        try:
            cls._pool.put_nowait(conn)
        except queue.Full:
            conn.close()

    def connect_database(self):
        if not self.conn:
            self.conn = self.get_pooled_connection()
        return self.conn

    def create_tables(self):
        pass # Handled by the external database.py initialization

    def save_grammar(self, name, description, parser):
        cursor = self.conn.cursor()
        stats = parser.get_grammar_statistics()
        
        cursor.execute('''
            INSERT INTO grammars (name, description, start_symbol, raw_grammar, total_rules, total_terminals, total_non_terminals)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, description, parser.start_symbol, parser.to_string(), 
              stats['num_rules'], stats['num_terminals'], stats['num_non_terminals']))
        grammar_id = cursor.lastrowid
        
        # Save each production rule
        idx = 0
        for nt, prods in parser.rules.items():
            for p in prods:
                cursor.execute('''
                    INSERT INTO production_rules (grammar_id, non_terminal, production_sequence, production_index)
                    VALUES (?, ?, ?, ?)
                ''', (grammar_id, nt, p, idx))
                idx += 1
                
        self.conn.commit()
        return grammar_id

    def load_grammar(self, grammar_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM grammars WHERE grammar_id = ?', (grammar_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_grammar(self, grammar_id, grammar_text):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE grammars SET raw_grammar = ?, modified_at = CURRENT_TIMESTAMP WHERE grammar_id = ?', 
                       (grammar_text, grammar_id))
        self.conn.commit()

    def delete_grammar(self, grammar_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM grammars WHERE grammar_id = ?', (grammar_id,))
        self.conn.commit()

    def get_all_grammars(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM grammars')
        return [dict(row) for row in cursor.fetchall()]

    def get_example_grammars(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM grammars WHERE is_example = TRUE')
        return [dict(row) for row in cursor.fetchall()]

    def save_parsing_session(self, grammar_id, target_string, results):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO parsing_sessions (grammar_id, target_string, total_trees_found, is_ambiguous, parsing_time_ms)
            VALUES (?, ?, ?, ?, ?)
        ''', (grammar_id, target_string, results.get('total_trees'), results.get('is_ambiguous'), results.get('time_ms')))
        self.conn.commit()
        return cursor.lastrowid

    def save_parse_tree(self, session_id, tree_number, tree_data, derivation):
        cursor = self.conn.cursor()
        # Compute dummy hash or get from tree
        tree_hash = str(hash(json.dumps(tree_data)))
        
        cursor.execute('''
            INSERT INTO parse_trees (session_id, tree_number, tree_structure, derivation_sequence, tree_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, tree_number, json.dumps(tree_data), json.dumps(derivation), tree_hash))
        tree_id = cursor.lastrowid
        self.conn.commit()
        return tree_id

    def save_derivation_steps(self, tree_id, derivation_steps):
        cursor = self.conn.cursor()
        for i, step in enumerate(derivation_steps):
            cursor.execute('''
                INSERT INTO derivation_steps (tree_id, step_number, applied_rule)
                VALUES (?, ?, ?)
            ''', (tree_id, i + 1, step))
        self.conn.commit()

    def save_ambiguity_analysis(self, session_id, analysis_report):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO ambiguity_analysis (session_id, ambiguous_flag, severity_level, explanation)
            VALUES (?, ?, ?, ?)
        ''', (session_id, analysis_report['is_ambiguous'], analysis_report.get('severity', 'low'), 
              analysis_report.get('explanation', '')))
        self.conn.commit()

    def get_parsing_history(self, grammar_id, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM parsing_sessions WHERE grammar_id = ? ORDER BY parsing_timestamp DESC LIMIT ?', 
                       (grammar_id, limit))
        return [dict(row) for row in cursor.fetchall()]

    def get_session_details(self, session_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM parsing_sessions WHERE session_id = ?', (session_id,))
        return dict(cursor.fetchone())

    def export_session_to_json(self, session_id):
        details = self.get_session_details(session_id)
        return json.dumps(details, indent=2)

    def load_from_json(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def update_user_preference(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO user_preferences (preference_key, preference_value) 
            VALUES (?, ?)
            ON CONFLICT(preference_key) DO UPDATE SET preference_value = excluded.preference_value
        ''', (key, str(value)))
        self.conn.commit()

    def get_user_preference(self, key):
        cursor = self.conn.cursor()
        cursor.execute('SELECT preference_value FROM user_preferences WHERE preference_key = ?', (key,))
        row = cursor.fetchone()
        return row['preference_value'] if row else None

    def cleanup_old_sessions(self, days=30):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM parsing_sessions WHERE parsing_timestamp < datetime('now', '-{} days')".format(days))
        self.conn.commit()

    def get_statistics(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as total FROM grammars')
        total_grammars = cursor.fetchone()['total']
        return {'total_grammars': total_grammars}

    def close_connection(self):
        if self.conn:
            self.release_connection(self.conn)
            self.conn = None
