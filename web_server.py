from flask import Flask, send_from_directory, jsonify, request
import os
import webbrowser
from threading import Timer
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.grammar_parser import CFGGrammarParser
from backend.recursive_parser import RecursiveDescentParser
from backend.ambiguity_detector import AmbiguityDetector
from backend.tree_visualizer import TreeVisualizer

app = Flask(__name__, static_folder='frontend')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/parse', methods=['POST'])
def parse_grammar():
    data = request.json
    grammar_text = data.get('grammar', '')
    target_string = data.get('target', '')
    max_depth = data.get('max_depth', 15)
    
    try:
        # 1. Parse Grammar
        g = CFGGrammarParser()
        g.parse_grammar_text(grammar_text)
        
        if not g.start_symbol:
            return jsonify({"status": "error", "message": "No start symbol found in grammar."})
            
        # 2. Parse String
        parser = RecursiveDescentParser(g)
        parser.set_max_depth(max_depth)
        trees = parser.parse(target_string)
        
        # 3. Detect Ambiguity
        detector = AmbiguityDetector(g, trees)
        is_ambiguous = detector.detect_ambiguity()
        unique_trees_count = detector.count_distinct_trees(trees)
        
        # 4. Generate Visualizations (ASCII art)
        tree_arts = []
        # Return at most 2 trees to fit the UI dual view
        for i, t in enumerate(trees[:2]):
            visualizer = TreeVisualizer(t)
            art = visualizer.render_ascii_tree()
            tree_arts.append(art)
            
        return jsonify({
            "status": "success",
            "is_ambiguous": is_ambiguous,
            "total_trees": unique_trees_count,
            "trees": tree_arts
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def open_browser():
    import subprocess
    import platform
    import webbrowser
    
    url = "http://localhost:5000"
    if platform.system() == "Windows":
        # Launch MS Edge in chromeless "App Mode" to simulate a native desktop app
        subprocess.Popen(f'start msedge --app="{url}" --window-size=1600,1000', shell=True)
    else:
        webbrowser.open_new(url)

if __name__ == '__main__':
    from threading import Timer
    Timer(1, open_browser).start()
    app.run(port=5000, debug=False)
