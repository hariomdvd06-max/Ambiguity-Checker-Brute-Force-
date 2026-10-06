import json
import csv
from datetime import datetime
import io

class ResultsProcessor:
    def __init__(self, db_manager):
        self.db = db_manager

    def export_to_json(self, session_id):
        session = self.db.get_session_details(session_id)
        if not session: return "{}"
        
        grammar = self.db.load_grammar(session['grammar_id'])
        cursor = self.db.conn.cursor()
        
        # Get rules
        cursor.execute("SELECT non_terminal, production_sequence FROM production_rules WHERE grammar_id = ?", (grammar['grammar_id'],))
        rules_raw = cursor.fetchall()
        rules_dict = {}
        for r in rules_raw:
            rules_dict.setdefault(r['non_terminal'], []).append(r['production_sequence'])
            
        # Get trees
        cursor.execute("SELECT * FROM parse_trees WHERE session_id = ?", (session_id,))
        trees_raw = cursor.fetchall()
        trees = []
        for t in trees_raw:
            trees.append({
                "tree_number": t['tree_number'],
                "derivation_sequence": " -> ".join(json.loads(t['derivation_sequence'])) if t['derivation_sequence'] else "",
                "production_rules": json.loads(t['derivation_sequence']) if t['derivation_sequence'] else [],
                "derivation_steps": len(json.loads(t['derivation_sequence'])) if t['derivation_sequence'] else 0,
                "tree_structure": json.loads(t['tree_structure']) if t['tree_structure'] else {}
            })
            
        # Get analysis
        cursor.execute("SELECT * FROM ambiguity_analysis WHERE session_id = ?", (session_id,))
        analysis_raw = cursor.fetchone()
        analysis = {}
        if analysis_raw:
            analysis = {
                "ambiguous": bool(analysis_raw['ambiguous_flag']),
                "severity": analysis_raw['severity_level'],
                "conflicting_rules": [],
                "explanation": analysis_raw['explanation']
            }
            
        data = {
            "metadata": {
                "export_date": datetime.now().isoformat() + "Z",
                "grammar_name": grammar['name'],
                "grammar_id": grammar['grammar_id'],
                "target_string": session['target_string'],
                "session_id": session_id
            },
            "grammar": {
                "start_symbol": grammar['start_symbol'],
                "total_rules": grammar['total_rules'],
                "total_terminals": grammar['total_terminals'],
                "total_non_terminals": grammar['total_non_terminals'],
                "rules": rules_dict
            },
            "parsing_results": {
                "target_string": session['target_string'],
                "ambiguous": bool(session['is_ambiguous']),
                "total_trees": session['total_trees_found'],
                "parsing_time_ms": session['parsing_time_ms'],
                "nodes_explored": session['nodes_explored'],
                "trees": trees
            },
            "analysis": analysis
        }
        return json.dumps(data, indent=2)

    def export_to_csv(self):
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT s.session_id, g.name as Grammar_Name, s.target_string, s.total_trees_found, 
                   s.is_ambiguous, s.parsing_time_ms, s.nodes_explored, s.parsing_timestamp
            FROM parsing_sessions s
            JOIN grammars g ON s.grammar_id = g.grammar_id
            ORDER BY s.session_id DESC
        """)
        sessions = cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Session_ID', 'Grammar_Name', 'Target_String', 'Total_Trees', 'Ambiguous', 'Parsing_Time_ms', 'Nodes_Explored', 'Date_Time'])
        
        for s in sessions:
            writer.writerow([
                s['session_id'], s['Grammar_Name'], s['target_string'], s['total_trees_found'],
                'YES' if s['is_ambiguous'] else 'NO', s['parsing_time_ms'] or 0, s['nodes_explored'] or 0, s['parsing_timestamp']
            ])
            
        return output.getvalue()

    def export_to_text(self, session_id):
        session = self.db.get_session_details(session_id)
        if not session: return "Session not found."
        
        grammar = self.db.load_grammar(session['grammar_id'])
        cursor = self.db.conn.cursor()
        
        cursor.execute("SELECT * FROM parse_trees WHERE session_id = ?", (session_id,))
        trees_raw = cursor.fetchall()
        
        cursor.execute("SELECT * FROM ambiguity_analysis WHERE session_id = ?", (session_id,))
        analysis_raw = cursor.fetchone()
        
        lines = []
        lines.append("═══════════════════════════════════════════════════════════════════════")
        lines.append("                     TOC AMBIGUITY CHECKER - REPORT                    ")
        lines.append("═══════════════════════════════════════════════════════════════════════\n")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Grammar: {grammar['name']} (ID: {grammar['grammar_id']})")
        lines.append(f"Target String: \"{session['target_string']}\"")
        lines.append(f"Session ID: {session_id}\n")
        
        lines.append("GRAMMAR DEFINITION:")
        lines.append("───────────────────")
        lines.append(grammar['raw_grammar'])
        lines.append(f"\nStart Symbol: {grammar['start_symbol']}")
        lines.append(f"Total Non-terminals: {grammar['total_non_terminals']}")
        lines.append(f"Total Terminals: {grammar['total_terminals']}")
        lines.append(f"Total Rules: {grammar['total_rules']}\n")
        
        lines.append("PARSING STATISTICS:")
        lines.append("───────────────────")
        lines.append(f"Parsing Time: {session['parsing_time_ms'] or 0} ms")
        lines.append(f"Nodes Explored: {session['nodes_explored'] or 0}")
        lines.append(f"Maximum Depth Reached: {session['max_depth_reached'] or 0}\n")
        
        lines.append("RESULTS:")
        lines.append("────────")
        lines.append(f"Ambiguous: {'YES' if session['is_ambiguous'] else 'NO'}")
        lines.append(f"Total Parse Trees: {session['total_trees_found']}")
        if analysis_raw:
            lines.append(f"Ambiguity Severity: {str(analysis_raw['severity_level']).upper()}\n")
            
        for i, t in enumerate(trees_raw):
            lines.append(f"PARSE TREE {i+1}:")
            lines.append("─────────────")
            # ASCII Art generation would be here, skipping for brevity
            lines.append(f"[Tree Structure JSON Snippet Omitted]")
            lines.append(f"Derivation: {' -> '.join(json.loads(t['derivation_sequence'])) if t['derivation_sequence'] else ''}\n")
            
        lines.append("ANALYSIS:")
        lines.append("─────────")
        if analysis_raw:
            lines.append(analysis_raw['explanation'])
            
        lines.append("\n═══════════════════════════════════════════════════════════════════════")
        return "\n".join(lines)
