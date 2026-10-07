# MASTER ARCHITECTURAL DIRECTIVE & PRD: CFG AMBIGUITY CHECKER (BRUTE FORCE)

## 0. Meta Instructions & Operational Context
- **Target System:** Full-Stack Cross-Platform Application (Mobile + Desktop).
- **Execution Mode:** Automated implementation via Antigravity, Ralph Loop, and Stitch MCP.
- **Key Objective:** Implement an unambiguous, strictly dynamic Context-Free Grammar (CFG) Ambiguity Checker using bounded-depth Brute-Force parse-tree generation. No hardcoded or pre-seeded grammar problems are allowed.
- **Delivery Standard:** Fully working, deployable files with 100% complete logic (no `// TODO` or truncated sections).

---

## 1. Project Directory Layout
Ensure the workspace is structured exactly as follows:

```text
cfg-ambiguity-checker/
├── backend/
│   ├── main.py              # FastAPI app, CORS, API routes
│   ├── parser_engine.py     # TOC CFG data models, tokenizer, brute-force engine
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Main PWA HTML shell (Stitch container + PWA bootstrap)
│   ├── manifest.json        # Web app manifest for PWA installation
│   ├── service-worker.js    # Offline asset caching & PWA compliance
│   ├── styles.css           # Custom styling, tree connectors, animations
│   ├── app.js               # Dynamic rule state, API integration, Tree visualizer
│   └── icons/
│       ├── icon-192.png     # PWA icon 192x192
│       └── icon-512.png     # PWA icon 512x512
├── PRD.md
├── progress.txt
└── README.md
```

---

## 2. Backend Implementation (Python + FastAPI)

### File: `backend/requirements.txt`
```plaintext
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
pydantic>=2.0.0
```

### File: `backend/parser_engine.py`
Adheres to:
- **Grammar Representation:**
  - Non-Terminals: Capital letters or strings matching `[A-Z][A-Za-z0-9_]*`.
  - Terminals: Lowercase letters, digits, or standard arithmetic operators (`+`, `*`, `(`, `)`, etc.).
  - Epsilon: `ε`, `eps`, or `""`.
- **Infinite Recursion Guard (Bounded Depth & Length):**
  - For string of length $n = |w|$:
  - Non-epsilon productions increase sentential form length.
  - Epsilon and unit productions ($A \to B$) constrained with cycle-detector or bounded max-depth: $\text{max\_depth} = \max(2 \times n + 4, 12)$.
- **Parse Tree Data Structure:**
  - Serialized as nested JSON nodes: `{"symbol": str, "children": [TreeNodes...]}`.
- **Tree Uniqueness Verification:**
  - Distinct if post-order traversals or serialized nested JSON representations differ.

### File: `backend/main.py`
FastAPI application with CORS, Pydantic validation models, rule tokenization, and `/api/check-ambiguity` endpoint.

---

## 3. PWA Architecture Files

### File: `frontend/manifest.json`
Web app manifest configured for PWA installation with dark/slate aesthetic.

### File: `frontend/service-worker.js`
Offline asset caching and lifecycle management for PWA compliance.

---

## 4. Frontend UI (Stitch MCP Integration & Responsive Layout)
- Responsive slate-styled layout using Tailwind CSS.
- Mobile First: single column on mobile, dual column on desktop (`lg:grid-cols-12`).
- Dynamic production rules builder with `+ Add Production Rule` and row deletion.
- Color-coded verdict banner (Ambiguous = Rose, Unambiguous = Emerald).
- Side-by-side parse tree visualization with tree nodes, branches, and terminal badges.
- PWA install prompt button (`#install-btn`).

---

## 5. Execution Verification Steps
1. Run backend: `uvicorn main:app --reload --port 8000` from `backend/`
2. Run frontend: `python -m http.server 3000` from `frontend/`
3. Test Case 1 (Ambiguous): $S \to S + S \mid a$, Target: `a+a+a`. Expected: `is_ambiguous: true`, 2 trees.
4. Test Case 2 (Unambiguous): $S \to aSb \mid \varepsilon$, Target: `aabb`. Expected: `is_ambiguous: false`, 1 tree.
5. Test Case 3 (PWA Trigger): Service Worker registration and install prompt.
