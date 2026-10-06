import os
import shutil

# Move and rename core backend files
moves = {
    "backend/database_manager.py": "database/db_manager.py",
    "ambiguity.db": "database/toc_db.sqlite",
    "backend/grammar.py": "backend/grammar_parser.py",
    "backend/parser.py": "backend/recursive_parser.py",
    "backend/tree.py": "backend/tree_visualizer.py"
}

for src, dst in moves.items():
    if os.path.exists(src):
        os.rename(src, dst)

# Create config.py
with open("config.py", "w") as f:
    f.write("""import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'toc_db.sqlite')
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
""")

# Fix db_manager.py DB_PATH and imports
if os.path.exists("database/db_manager.py"):
    with open("database/db_manager.py", "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace(
        "DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ambiguity.db')",
        "from config import DB_PATH"
    )
    with open("database/db_manager.py", "w", encoding="utf-8") as f:
        f.write(content)

# Split ambiguity.py
if os.path.exists("backend/ambiguity.py"):
    with open("backend/ambiguity.py", "r", encoding="utf-8") as f:
        amb_content = f.read()
    
    parts = amb_content.split("class ResultsProcessor:")
    detector_code = parts[0]
    processor_code = "import json\nimport csv\nfrom datetime import datetime\nimport io\n\nclass ResultsProcessor:" + parts[1]
    
    with open("backend/ambiguity_detector.py", "w", encoding="utf-8") as f:
        f.write(detector_code)
    
    with open("backend/results_processor.py", "w", encoding="utf-8") as f:
        f.write(processor_code)
        
    os.remove("backend/ambiguity.py")

# Create requirements.txt
with open("requirements.txt", "w") as f:
    f.write("") # SQLite is built-in

# Write markdown files
with open("docs/README.md", "w") as f: f.write("# TOC Ambiguity Checker\\n")
with open("docs/USER_GUIDE.md", "w") as f: f.write("# User Guide\\n")
with open("docs/THEORY.md", "w") as f: f.write("# Parsing Theory\\n")

