import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'ambiguity.db')

def get_connection():
    """Returns a database connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: grammars
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grammars (
        grammar_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        start_symbol TEXT NOT NULL,
        total_rules INTEGER,
        total_terminals INTEGER,
        total_non_terminals INTEGER,
        raw_grammar TEXT NOT NULL,
        is_ambiguous BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_example BOOLEAN DEFAULT FALSE,
        difficulty_level TEXT CHECK(difficulty_level IN ('beginner', 'intermediate', 'advanced'))
    );
    """)

    # Table 2: production_rules
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS production_rules (
        rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
        grammar_id INTEGER NOT NULL,
        non_terminal TEXT NOT NULL,
        production_sequence TEXT NOT NULL,
        production_index INTEGER,
        FOREIGN KEY (grammar_id) REFERENCES grammars(grammar_id) ON DELETE CASCADE,
        UNIQUE(grammar_id, non_terminal, production_index)
    );
    """)

    # Table 3: parsing_sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parsing_sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        grammar_id INTEGER NOT NULL,
        target_string TEXT NOT NULL,
        parsing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_trees_found INTEGER,
        is_ambiguous BOOLEAN,
        parsing_time_ms FLOAT,
        nodes_explored INTEGER,
        max_depth_reached INTEGER,
        error_message TEXT,
        FOREIGN KEY (grammar_id) REFERENCES grammars(grammar_id) ON DELETE CASCADE
    );
    """)

    # Table 4: parse_trees
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parse_trees (
        tree_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        tree_number INTEGER,
        tree_structure TEXT NOT NULL,
        derivation_sequence TEXT NOT NULL,
        derivation_steps INTEGER,
        production_rules_used TEXT,
        tree_hash TEXT UNIQUE,
        FOREIGN KEY (session_id) REFERENCES parsing_sessions(session_id) ON DELETE CASCADE
    );
    """)

    # Table 5: derivation_steps
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS derivation_steps (
        step_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tree_id INTEGER NOT NULL,
        step_number INTEGER,
        current_string TEXT,
        applied_rule TEXT,
        non_terminal_replaced TEXT,
        rule_production TEXT,
        FOREIGN KEY (tree_id) REFERENCES parse_trees(tree_id) ON DELETE CASCADE
    );
    """)

    # Table 6: user_preferences
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
        pref_id INTEGER PRIMARY KEY AUTOINCREMENT,
        preference_key TEXT UNIQUE NOT NULL,
        preference_value TEXT,
        data_type TEXT DEFAULT 'string'
    );
    """)

    # Table 7: saved_results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        result_name TEXT NOT NULL,
        result_description TEXT,
        export_format TEXT DEFAULT 'json',
        file_path TEXT,
        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES parsing_sessions(session_id) ON DELETE CASCADE
    );
    """)

    # Table 8: ambiguity_analysis
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ambiguity_analysis (
        analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        ambiguous_flag BOOLEAN,
        conflicting_rules TEXT,
        common_substrings TEXT,
        structural_differences TEXT,
        derivation_alternatives INTEGER,
        severity_level TEXT CHECK(severity_level IN ('low', 'medium', 'high')),
        explanation TEXT,
        FOREIGN KEY (session_id) REFERENCES parsing_sessions(session_id) ON DELETE CASCADE
    );
    """)

    # Optimization Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_grammar_id_sessions ON parsing_sessions(grammar_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id_trees ON parse_trees(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_target_string_sessions ON parsing_sessions(target_string);")

    conn.commit()
    conn.close()
    print(f"Database initialized successfully with 8 tables at {DB_PATH}")

if __name__ == "__main__":
    initialize_database()
