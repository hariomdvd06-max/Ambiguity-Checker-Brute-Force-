// ============================================================================
// CFG AMBIGUITY CHECKER — ADVANCED FRONTEND CONTROLLER (ENGINE v2.0)
// ============================================================================

// --- PWA Installation Logic ---
let deferredPrompt = null;
const installBtn = document.getElementById('install-btn');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  if (installBtn) {
    installBtn.style.display = 'flex';
  }
});

if (installBtn) {
  installBtn.addEventListener('click', async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        installBtn.style.display = 'none';
      }
      deferredPrompt = null;
    } else {
      alert("PWA Install prompt is not available right now. The app may already be installed or can be installed via browser menu.");
    }
  });
}

window.addEventListener('appinstalled', () => {
  if (installBtn) installBtn.style.display = 'none';
  console.log('CFG Ambiguity Engine PWA successfully installed!');
});

// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./service-worker.js')
      .then((reg) => console.log('SW Registered:', reg.scope))
      .catch((err) => console.error('SW Registration Failed:', err));
  });
}

// ============================================================================
// --- DYNAMIC GRAMMAR RULES BUILDER & INPUT VALIDATION ---
// ============================================================================
const rulesContainer = document.getElementById('rules-container');
const addRuleBtn = document.getElementById('add-rule-btn');
const startSymbolInput = document.getElementById('start-symbol');
const targetStringInput = document.getElementById('target-string');
const validationHintBox = document.getElementById('validation-hint-box');

function createRuleRow(lhs = '', rhs = '') {
  const row = document.createElement('div');
  row.className = 'flex items-center gap-2 rule-row group';
  row.innerHTML = `
    <input type="text" value="${lhs}" placeholder="LHS" class="w-20 luxury-input px-2.5 py-1.5 text-xs text-center font-bold text-indigo-300 rounded-lg outline-none rule-lhs" />
    <span class="text-slate-500 text-xs font-mono select-none px-0.5">→</span>
    <input type="text" value="${rhs}" placeholder="RHS (e.g. E + E | a)" class="flex-1 luxury-input px-3 py-1.5 text-xs text-slate-200 rounded-lg outline-none rule-rhs" />
    <button type="button" class="delete-rule text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors cursor-pointer" title="Delete rule">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
    </button>
  `;
  row.querySelector('.delete-rule').addEventListener('click', () => {
    if (document.querySelectorAll('.rule-row').length > 1) {
      row.remove();
      validateInputsRealTime();
    }
  });

  row.querySelectorAll('input').forEach(inp => {
    inp.addEventListener('input', validateInputsRealTime);
  });

  rulesContainer.appendChild(row);
  validateInputsRealTime();
}

addRuleBtn.addEventListener('click', () => {
  createRuleRow('', '');
});

// Real-Time UI Validation Hints & Error Handling
function validateInputsRealTime() {
  const startSymbol = startSymbolInput.value.trim();
  const targetString = targetStringInput.value.trim();
  const ruleRows = document.querySelectorAll('.rule-row');

  const definedLHS = new Set();
  const rules = [];

  ruleRows.forEach(row => {
    const lhs = row.querySelector('.rule-lhs').value.trim();
    const rhs = row.querySelector('.rule-rhs').value.trim();
    if (lhs) {
      definedLHS.add(lhs);
      rules.push({ lhs, rhs });
    }
  });

  if (!validationHintBox) return;

  const errors = [];
  const warnings = [];

  if (!startSymbol) {
    errors.push("Start symbol is required.");
  } else if (definedLHS.size > 0 && !definedLHS.has(startSymbol)) {
    warnings.push(`Start symbol '${startSymbol}' is not defined as LHS in any production rule.`);
  }

  // Check for undefined uppercase non-terminals in RHS
  const upperPattern = /\b[A-Z][A-Za-z0-9_']*\b/g;
  rules.forEach(r => {
    let match;
    while ((match = upperPattern.exec(r.rhs)) !== null) {
      const sym = match[0];
      if (!definedLHS.has(sym) && sym !== 'EPS' && sym !== 'EPSILON') {
        warnings.push(`Non-terminal '${sym}' referenced in rule '${r.lhs}' is not defined as LHS.`);
      }
    }
  });

  if (errors.length > 0) {
    validationHintBox.className = 'text-xs rounded-xl p-3 hint-error space-y-1 block shadow-sm';
    validationHintBox.innerHTML = errors.map(e => `<div>⛔ ${e}</div>`).join('');
  } else if (warnings.length > 0) {
    validationHintBox.className = 'text-xs rounded-xl p-3 hint-warning space-y-1 block shadow-sm';
    validationHintBox.innerHTML = warnings.map(w => `<div>⚠️ ${w}</div>`).join('');
  } else if (rules.length > 0) {
    validationHintBox.className = 'text-xs rounded-xl p-2.5 hint-valid block shadow-sm';
    validationHintBox.innerHTML = `✓ Grammar syntax valid & start symbol '${startSymbol}' confirmed.`;
  } else {
    validationHintBox.className = 'hidden';
  }
}

if (startSymbolInput) startSymbolInput.addEventListener('input', validateInputsRealTime);
if (targetStringInput) targetStringInput.addEventListener('input', validateInputsRealTime);

// Quick Presets Loader
function loadPreset(presetName) {
  rulesContainer.innerHTML = '';

  if (presetName === 'arithmetic') {
    startSymbolInput.value = 'E';
    createRuleRow('E', 'E + E | E * E | a');
    targetStringInput.value = 'a + a * a + a';
  } else if (presetName === 'dangling') {
    startSymbolInput.value = 'S';
    createRuleRow('S', 'if c then S else S | if c then S | a');
    targetStringInput.value = 'if c then if c then a else a';
  } else if (presetName === 'parens') {
    startSymbolInput.value = 'S';
    createRuleRow('S', '( S ) | a');
    targetStringInput.value = '( ( a ) )';
  } else if (presetName === 'palindrome') {
    startSymbolInput.value = 'S';
    createRuleRow('S', 'a S a | b S b | ε');
    targetStringInput.value = 'a b a';
  }

  validateInputsRealTime();
}

document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const preset = btn.getAttribute('data-preset');
    loadPreset(preset);
  });
});

// Initialize with Arithmetic Grammar preset
loadPreset('arithmetic');

// Enter key shortcut on target string
if (targetStringInput) {
  targetStringInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      document.getElementById('check-btn').click();
    }
  });
}

// ============================================================================
// --- DUAL PARSE TREE DYNAMIC SVG VISUALIZER ---
// ============================================================================

/**
 * Dynamically renders ANY tree structure regardless of branching factor (binary, ternary, n-ary).
 * Automatically calculates SVG width/height and node spacing based on depth and leaf count.
 */
function renderTreeSVG(rootNode) {
  if (!rootNode) return '';

  // 1. Measure depths, leaves, and subtree widths
  let leafIndex = 0;
  let maxDepth = 0;

  function measure(node, depth) {
    node.depth = depth;
    if (depth > maxDepth) maxDepth = depth;

    if (!node.children || node.children.length === 0) {
      node.isLeaf = true;
      node.leafIndex = leafIndex++;
      node.leafCount = 1;
    } else {
      node.isLeaf = false;
      let count = 0;
      node.children.forEach(c => {
        measure(c, depth + 1);
        count += c.leafCount;
      });
      node.leafCount = count;
    }
  }
  measure(rootNode, 0);

  const totalLeaves = Math.max(1, leafIndex);
  const xSpacing = Math.max(52, Math.min(84, 520 / totalLeaves));
  const ySpacing = 64;
  const paddingX = 40;
  const paddingTop = 36;
  const totalWidth = Math.max(340, totalLeaves * xSpacing + paddingX * 2);
  const totalHeight = (maxDepth + 1) * ySpacing + paddingTop + 20;

  // 2. Position nodes (leaf-midpoint tidy positioning)
  function position(node) {
    if (node.isLeaf) {
      node.x = paddingX + node.leafIndex * xSpacing + xSpacing / 2;
    } else {
      node.children.forEach(position);
      const firstX = node.children[0].x;
      const lastX = node.children[node.children.length - 1].x;
      node.x = (firstX + lastX) / 2;
    }
    node.y = paddingTop + node.depth * ySpacing;
  }
  position(rootNode);

  // 3. Render edges and nodes into SVG
  let edgesSvg = '';
  let nodesSvg = '';

  function render(node) {
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => {
        const startY = node.y + 13;
        const endY = child.y - 13;
        const midY = (startY + endY) / 2;
        edgesSvg += `
          <path class="tree-svg-edge" d="M ${node.x} ${startY} C ${node.x} ${midY}, ${child.x} ${midY}, ${child.x} ${endY}" />
        `;
        render(child);
      });
    }

    const sym = node.symbol;
    const isEps = (sym === 'ε' || sym === 'eps' || sym === 'epsilon');
    const isLeaf = node.isLeaf;

    let bgFill = '#1e1b4b';
    let strokeCol = '#818cf8';
    let textCol = '#c7d2fe';
    let fontStyle = 'normal';

    if (isEps) {
      bgFill = '#451a03';
      strokeCol = '#f59e0b';
      textCol = '#fde68a';
      fontStyle = 'italic';
    } else if (isLeaf) {
      bgFill = '#064e3b';
      strokeCol = '#34d399';
      textCol = '#a7f3d0';
    }

    const boxWidth = Math.max(32, sym.length * 8.5 + 16);
    const boxHeight = 26;

    nodesSvg += `
      <g class="tree-svg-node transition-transform duration-150 cursor-pointer" transform="translate(${node.x}, ${node.y})">
        <rect x="${-boxWidth / 2}" y="${-boxHeight / 2}" width="${boxWidth}" height="${boxHeight}" rx="7" fill="${bgFill}" stroke="${strokeCol}" stroke-width="1.6" filter="drop-shadow(0 2px 4px rgba(0,0,0,0.5))" />
        <text x="0" y="4.5" fill="${textCol}" font-size="11" font-weight="700" font-style="${fontStyle}" text-anchor="middle">${sym}</text>
      </g>
    `;
  }
  render(rootNode);

  return `
    <div class="tree-svg-wrapper">
      <svg class="block mx-auto min-w-full" viewBox="0 0 ${totalWidth} ${totalHeight}" style="min-width:${totalWidth}px; height:${totalHeight}px;" preserveAspectRatio="xMidYMid meet">
        <defs>
          <filter id="tree-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        ${edgesSvg}
        ${nodesSvg}
      </svg>
    </div>
  `;
}

/**
 * Renders the clean "Single Unique Derivation" card in Tree 2 slot when only 1 tree exists.
 */
function renderSingleDerivationCard(targetString) {
  return `
    <div class="single-derivation-card space-y-3">
      <div class="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 mx-auto shadow-sm">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <div>
        <h4 class="text-xs font-bold text-white uppercase tracking-wider">Single Unique Derivation</h4>
        <p class="text-[11px] text-emerald-400 font-mono mt-0.5">Strictly Unambiguous for "${targetString}"</p>
      </div>
      <p class="text-xs text-slate-400 max-w-xs mx-auto leading-relaxed">
        This grammar generates the target string through exactly 1 canonical parse tree. In Formal Language Theory, demonstrating ambiguity requires finding at least 2 distinct parse trees.
      </p>
      <div class="flex items-center justify-center gap-2 pt-1 flex-wrap">
        <span class="px-2.5 py-1 rounded text-[10px] font-mono bg-white/[0.04] text-slate-300 border border-white/[0.08]">L(G) Member: Yes</span>
        <span class="px-2.5 py-1 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-bold">Alternative Trees: 0</span>
      </div>
    </div>
  `;
}

// ============================================================================
// --- API COMMUNICATION & AMBIGUITY EVALUATION ---
// ============================================================================
const checkBtn = document.getElementById('check-btn');
const verdictCard = document.getElementById('verdict-card');
const verdictBadge = document.getElementById('verdict-badge');
const treeCountBadge = document.getElementById('tree-count-badge');
const explanationText = document.getElementById('explanation-text');
const treesContainer = document.getElementById('trees-container');
const emptyState = document.getElementById('empty-state');
const tree1Box = document.getElementById('tree-1');
const tree2Box = document.getElementById('tree-2');

// Smart backend URL: defaults to local port 8000 when served on localhost / file, or deployed Render URL
const BACKEND_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:')
  ? 'http://127.0.0.1:8000'
  : 'https://cfg-ambiguity-backend.onrender.com';

checkBtn.addEventListener('click', async () => {
  const startSymbol = startSymbolInput.value.trim();
  const targetString = targetStringInput.value.trim();

  const ruleRows = document.querySelectorAll('.rule-row');
  const rules = [];
  ruleRows.forEach(row => {
    const lhs = row.querySelector('.rule-lhs').value.trim();
    const rhs = row.querySelector('.rule-rhs').value.trim();
    if (lhs && rhs) {
      rules.push({ lhs, rhs });
    }
  });

  if (!startSymbol) {
    alert('Please specify a Start Symbol.');
    return;
  }

  if (rules.length === 0) {
    alert('Please provide at least one valid grammar rule.');
    return;
  }

  checkBtn.disabled = true;
  checkBtn.innerHTML = `
    <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
    </svg>
    <span>Evaluating with Earley Parser...</span>
  `;

  try {
    const payload = {
      start_symbol: startSymbol,
      rules: rules,
      target_string: targetString
    };

    const res = await fetch(`${BACKEND_URL}/api/check-ambiguity`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Evaluation failed on the server.');
    }

    const data = await res.json();
    console.log("Full Backend Response:", data);

    // 1. Render Verdict
    emptyState.classList.add('hidden');
    verdictCard.classList.remove('hidden');

    if (data.is_ambiguous) {
      verdictBadge.textContent = data.status_badge || 'AMBIGUOUS CFG';
      verdictBadge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20 shadow-sm';
    } else if (data.is_in_language) {
      verdictBadge.textContent = data.status_badge || 'UNAMBIGUOUS / SINGLE TREE';
      verdictBadge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm';
    } else {
      verdictBadge.textContent = data.status_badge || 'NOT IN LANGUAGE';
      verdictBadge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm';
    }

    treeCountBadge.textContent = `Trees Found: ${data.trees_found ?? data.tree_count ?? 0}`;
    explanationText.textContent = data.explanation;

    // 2. Render Parse Trees (SVG Canvases)
    tree1Box.innerHTML = '';
    tree2Box.innerHTML = '';

    const tree1 = data.parse_tree_1 || (data.trees && data.trees[0]);
    const tree2 = data.parse_tree_2 || (data.trees && data.trees[1]);

    if (tree1) {
      treesContainer.classList.remove('hidden');
      tree1Box.innerHTML = renderTreeSVG(tree1);

      if (tree2) {
        tree2Box.parentElement.classList.remove('hidden');
        tree2Box.innerHTML = renderTreeSVG(tree2);
      } else {
        // Single tree exists: show the clean "Single Unique Derivation" card
        tree2Box.parentElement.classList.remove('hidden');
        tree2Box.innerHTML = renderSingleDerivationCard(data.target_string);
      }

      // 3. Render Derivation Flow Automaton
      renderDerivationFlowGraph(data);
    } else {
      treesContainer.classList.add('hidden');
      const derivationCard = document.getElementById('derivation-automaton-card');
      if (derivationCard) derivationCard.classList.add('hidden');
    }

    // 4. Render Earley Parser Chart & Simulation Controller
    executionSteps = data.execution_steps || [];
    resetSimulation();
    renderEarleyChart(data.earley_chart);

  } catch (error) {
    alert('Error: ' + error.message);
  } finally {
    checkBtn.disabled = false;
    checkBtn.innerHTML = `<span>Evaluate Ambiguity</span>`;
  }
});

// ============================================================================
// --- DERIVATION FLOW AUTOMATON (DIVERGENCE & CONVERGENCE ENGINE) ---
// ============================================================================

let graphStage = 0;
let graphMaxStages = 0;
let graphPlayInterval = null;
let currentDerivationData = null;
let graphAnimationDelay = 2000;

const derivationAutomatonCard = document.getElementById('derivation-automaton-card');
const derivationSvg = document.getElementById('derivation-svg');
const graphStatusBar = document.getElementById('graph-status-bar');
const graphPrevBtn = document.getElementById('graph-prev-btn');
const graphPlayBtn = document.getElementById('graph-play-btn');
const graphNextBtn = document.getElementById('graph-next-btn');
const graphResetBtn = document.getElementById('graph-reset-btn');
const graphSpeedSelect = document.getElementById('graph-speed-select');

if (graphSpeedSelect) {
  graphSpeedSelect.addEventListener('change', (e) => {
    graphAnimationDelay = parseInt(e.target.value, 10) || 2000;
    if (graphPlayInterval) startGraphPlay();
  });
}

function renderDerivationFlowGraph(data) {
  if (!derivationAutomatonCard || !derivationSvg) return;

  const isAmbiguous = data.is_ambiguous;
  const targetString = data.target_string;
  const steps1 = data.derivation_steps_1 || [];
  const steps2 = data.derivation_steps_2 || [];

  if (steps1.length === 0) {
    derivationAutomatonCard.classList.add('hidden');
    return;
  }

  derivationAutomatonCard.classList.remove('hidden');
  stopGraphPlay();

  const isDual = isAmbiguous && steps2.length > 0;

  // Find exact divergence step
  let divergenceStep = 0;
  while (divergenceStep < steps1.length && divergenceStep < steps2.length && steps1[divergenceStep] === steps2[divergenceStep]) {
    divergenceStep++;
  }

  // Sample or full steps
  const totalStages = 4; // Start -> Diverge -> Intermediate -> Accept
  const totalWidth = 900;

  derivationSvg.setAttribute('viewBox', `0 0 ${totalWidth} 260`);
  derivationSvg.setAttribute('preserveAspectRatio', 'xMinYMid meet');

  const startX = 85;
  const acceptX = totalWidth - 85;
  const divergeX = 300;
  const midX = 570;

  const startSym = (data.parse_tree_1 && data.parse_tree_1.symbol) || 'S';
  const displayTarget = targetString.length > 12 ? targetString.slice(0, 11) + '…' : targetString;

  const rule1Diverge = steps1[divergenceStep] || steps1[0] || 'Rule 1';
  const rule2Diverge = steps2[divergenceStep] || steps2[0] || 'Rule 2';
  const rule1Mid = steps1[steps1.length - 1] || 'Yield w';
  const rule2Mid = steps2[steps2.length - 1] || 'Yield w';

  graphMaxStages = 3; // 0: Start, 1: Divergence, 2: Intermediate, 3: Accepted convergence
  currentDerivationData = {
    targetString,
    isDual,
    divergenceStep,
    rule1Diverge,
    rule2Diverge,
    rule1Mid,
    rule2Mid,
    steps1,
    steps2
  };

  let svg = `
    <defs>
      <marker id="arr-inactive" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#475569" />
      </marker>
      <marker id="arr-active" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#818cf8" />
      </marker>
      <marker id="arr-success" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#34d399" />
      </marker>
      <filter id="svg-glow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="3.5" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
      </filter>
    </defs>
  `;

  // Start indicator
  svg += `
    <line x1="${startX - 55}" y1="130" x2="${startX - 28}" y2="130" stroke="#6366f1" stroke-width="2" marker-end="url(#arr-active)"/>
    <text x="${startX - 42}" y="118" fill="#a5b4fc" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">Start</text>
  `;

  // Start Node
  svg += `
    <g id="g-node-start" class="derivation-node cursor-pointer">
      <circle cx="${startX}" cy="130" r="24" fill="#312e81" stroke="#818cf8" stroke-width="2.5" filter="url(#svg-glow)"/>
      <text x="${startX}" y="135" fill="#ffffff" font-size="14" font-weight="bold" font-family="monospace" text-anchor="middle">${startSym}</text>
    </g>
  `;

  // Final Accepted Node
  svg += `
    <g id="g-node-accept" class="derivation-node transition-all duration-300">
      <circle id="accept-outer-circle" cx="${acceptX}" cy="130" r="28" fill="none" stroke="#475569" stroke-width="2"/>
      <circle id="accept-inner-circle" cx="${acceptX}" cy="130" r="23" fill="#0f172a" stroke="#475569" stroke-width="2"/>
      <text id="accept-text" x="${acceptX}" y="135" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">${displayTarget}</text>
      <text x="${acceptX}" y="172" fill="#64748b" font-size="10" font-family="sans-serif" font-weight="600" text-anchor="middle">Accepted (w)</text>
    </g>
  `;

  if (isDual) {
    // Upper Branch (Tree 1 - Indigo) & Lower Branch (Tree 2 - Violet)
    svg += `
      <text x="${startX + 40}" y="42" fill="#818cf8" font-size="10" font-family="sans-serif" font-weight="bold">✦ Tree 1 (Leftmost Branch 1)</text>
      <text x="${startX + 40}" y="226" fill="#c084fc" font-size="10" font-family="sans-serif" font-weight="bold">✦ Tree 2 (Leftmost Branch 2)</text>
    `;

    // Path 1 (Upper): Start -> Divergence -> Mid -> Accept
    svg += `
      <!-- Edge Up 1: Start to Diverge Node -->
      <path id="edge-up-0" data-stage="1" d="M ${startX + 22},120 C ${startX + 60},70 ${divergeX - 50},70 ${divergeX - 22},70" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
      <g id="lbl-up-0" data-stage="1" class="derivation-label opacity-60">
        <rect x="${(startX + divergeX) / 2 - 50}" y="56" width="100" height="18" rx="4" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
        <text x="${(startX + divergeX) / 2}" y="69" fill="#94a3b8" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">${rule1Diverge}</text>
      </g>

      <!-- Node Up 1 (Divergence state) -->
      <g id="node-up-1" data-stage="1" class="derivation-node">
        <circle cx="${divergeX}" cy="70" r="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>
        <text x="${divergeX}" y="74" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">q₁₁</text>
        <text x="${divergeX}" y="36" fill="#818cf8" font-size="9" font-family="monospace" text-anchor="middle">Diverge Pt</text>
      </g>

      <!-- Edge Up 2: Diverge to Mid -->
      <line id="edge-up-1" data-stage="2" x1="${divergeX + 20}" y1="70" x2="${midX - 20}" y2="70" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
      <g id="lbl-up-1" data-stage="2" class="derivation-label opacity-60">
        <rect x="${(divergeX + midX) / 2 - 45}" y="56" width="90" height="18" rx="4" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
        <text x="${(divergeX + midX) / 2}" y="69" fill="#94a3b8" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">${rule1Mid}</text>
      </g>

      <!-- Node Up 2 (Mid state) -->
      <g id="node-up-2" data-stage="2" class="derivation-node">
        <circle cx="${midX}" cy="70" r="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>
        <text x="${midX}" y="74" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">q₁₂</text>
      </g>

      <!-- Edge Up 3: Mid to Accept (Convergence) -->
      <path id="edge-up-final" data-stage="3" d="M ${midX + 20},70 C ${midX + 50},70 ${acceptX - 55},122 ${acceptX - 28},126" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
    `;

    // Path 2 (Lower): Start -> Divergence -> Mid -> Accept
    svg += `
      <!-- Edge Down 1: Start to Diverge Node -->
      <path id="edge-down-0" data-stage="1" d="M ${startX + 22},140 C ${startX + 60},190 ${divergeX - 50},190 ${divergeX - 22},190" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
      <g id="lbl-down-0" data-stage="1" class="derivation-label opacity-60">
        <rect x="${(startX + divergeX) / 2 - 50}" y="178" width="100" height="18" rx="4" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
        <text x="${(startX + divergeX) / 2}" y="191" fill="#94a3b8" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">${rule2Diverge}</text>
      </g>

      <!-- Node Down 1 (Divergence state) -->
      <g id="node-down-1" data-stage="1" class="derivation-node">
        <circle cx="${divergeX}" cy="190" r="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>
        <text x="${divergeX}" y="194" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">q₂₁</text>
        <text x="${divergeX}" y="224" fill="#c084fc" font-size="9" font-family="monospace" text-anchor="middle">Diverge Pt</text>
      </g>

      <!-- Edge Down 2: Diverge to Mid -->
      <line id="edge-down-1" data-stage="2" x1="${divergeX + 20}" y1="190" x2="${midX - 20}" y2="190" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
      <g id="lbl-down-1" data-stage="2" class="derivation-label opacity-60">
        <rect x="${(divergeX + midX) / 2 - 45}" y="178" width="90" height="18" rx="4" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
        <text x="${(divergeX + midX) / 2}" y="191" fill="#94a3b8" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">${rule2Mid}</text>
      </g>

      <!-- Node Down 2 (Mid state) -->
      <g id="node-down-2" data-stage="2" class="derivation-node">
        <circle cx="${midX}" cy="190" r="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>
        <text x="${midX}" y="194" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">q₂₂</text>
      </g>

      <!-- Edge Down 3: Mid to Accept (Convergence) -->
      <path id="edge-down-final" data-stage="3" d="M ${midX + 20},190 C ${midX + 50},190 ${acceptX - 55},138 ${acceptX - 28},134" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
    `;
  } else {
    // Single linear branch (Unambiguous)
    svg += `
      <line id="edge-lin-1" data-stage="1" x1="${startX + 24}" y1="130" x2="${divergeX - 20}" y2="130" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
      <g id="lbl-lin-1" data-stage="1" class="derivation-label opacity-60">
        <rect x="${(startX + divergeX) / 2 - 45}" y="112" width="90" height="18" rx="3" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
        <text x="${(startX + divergeX) / 2}" y="125" fill="#94a3b8" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">${rule1Diverge}</text>
      </g>

      <g id="node-lin-1" data-stage="1" class="derivation-node">
        <circle cx="${divergeX}" cy="130" r="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>
        <text x="${divergeX}" y="134" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">q₁</text>
      </g>

      <line id="edge-lin-2" data-stage="2" x1="${divergeX + 20}" y1="130" x2="${midX - 20}" y2="130" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
      <g id="lbl-lin-2" data-stage="2" class="derivation-label opacity-60">
        <rect x="${(divergeX + midX) / 2 - 45}" y="112" width="90" height="18" rx="3" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
        <text x="${(divergeX + midX) / 2}" y="125" fill="#94a3b8" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">${rule1Mid}</text>
      </g>

      <g id="node-lin-2" data-stage="2" class="derivation-node">
        <circle cx="${midX}" cy="130" r="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>
        <text x="${midX}" y="134" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">q₂</text>
      </g>

      <line id="edge-lin-3" data-stage="3" x1="${midX + 20}" y1="130" x2="${acceptX - 28}" y2="130" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
    `;
  }

  derivationSvg.innerHTML = svg;
  setGraphStage(0);
}

function setGraphStage(stage) {
  if (!currentDerivationData) return;
  graphStage = Math.max(0, Math.min(stage, graphMaxStages));

  const { isDual, targetString, rule1Diverge, rule2Diverge } = currentDerivationData;

  document.querySelectorAll('#derivation-svg [data-stage]').forEach(el => {
    const s = parseInt(el.getAttribute('data-stage'), 10);
    const isActive = (s <= graphStage);
    const tagName = el.tagName.toLowerCase();

    if (tagName === 'path' || tagName === 'line') {
      if (isActive) {
        if (s === graphMaxStages && isDual) {
          el.setAttribute('stroke', '#34d399');
          el.setAttribute('stroke-width', '2.5');
          el.setAttribute('marker-end', 'url(#arr-success)');
          el.setAttribute('filter', 'url(#svg-glow)');
        } else {
          el.setAttribute('stroke', '#818cf8');
          el.setAttribute('stroke-width', '2.5');
          el.setAttribute('marker-end', 'url(#arr-active)');
          el.setAttribute('filter', 'url(#svg-glow)');
        }
      } else {
        el.setAttribute('stroke', '#334155');
        el.setAttribute('stroke-width', '2');
        el.setAttribute('marker-end', 'url(#arr-inactive)');
        el.removeAttribute('filter');
      }
    } else if (tagName === 'g') {
      const circle = el.querySelector('circle');
      const text = el.querySelector('text');
      const rect = el.querySelector('rect');

      if (circle) {
        if (isActive) {
          circle.setAttribute('stroke', '#818cf8');
          circle.setAttribute('fill', '#1e1b4b');
          circle.setAttribute('stroke-width', '2.5');
          circle.setAttribute('filter', 'url(#svg-glow)');
          if (text) text.setAttribute('fill', '#ffffff');
        } else {
          circle.setAttribute('stroke', '#334155');
          circle.setAttribute('fill', '#0f172a');
          circle.setAttribute('stroke-width', '2');
          circle.removeAttribute('filter');
          if (text) text.setAttribute('fill', '#94a3b8');
        }
      }

      if (rect) {
        if (isActive) {
          el.classList.remove('opacity-60');
          el.classList.add('opacity-100');
          rect.setAttribute('stroke', '#6366f1');
          if (text) text.setAttribute('fill', '#c7d2fe');
        } else {
          el.classList.remove('opacity-100');
          el.classList.add('opacity-60');
          rect.setAttribute('stroke', '#334155');
          if (text) text.setAttribute('fill', '#94a3b8');
        }
      }
    }
  });

  const acceptOuter = document.getElementById('accept-outer-circle');
  const acceptInner = document.getElementById('accept-inner-circle');
  const acceptText = document.getElementById('accept-text');

  if (graphStage === graphMaxStages) {
    if (acceptOuter) {
      acceptOuter.setAttribute('stroke', '#34d399');
      acceptOuter.setAttribute('stroke-width', '3');
      acceptOuter.setAttribute('filter', 'url(#svg-glow)');
    }
    if (acceptInner) {
      acceptInner.setAttribute('stroke', '#34d399');
      acceptInner.setAttribute('fill', '#064e3b');
    }
    if (acceptText) acceptText.setAttribute('fill', '#a7f3d0');
  } else {
    if (acceptOuter) {
      acceptOuter.setAttribute('stroke', '#475569');
      acceptOuter.setAttribute('stroke-width', '2');
      acceptOuter.removeAttribute('filter');
    }
    if (acceptInner) {
      acceptInner.setAttribute('stroke', '#475569');
      acceptInner.setAttribute('fill', '#0f172a');
    }
    if (acceptText) acceptText.setAttribute('fill', '#94a3b8');
  }

  // Live status bar updates
  if (graphStatusBar) {
    if (graphStage === 0) {
      graphStatusBar.innerHTML = `<span class="text-indigo-400 font-bold">Start:</span> Automaton initialized for target string <span class="text-white font-mono font-bold">"${targetString}"</span>. Click <strong>'Play Derivation'</strong> or <strong>'Next ›'</strong> to observe flow.`;
    } else if (graphStage === 1 && isDual) {
      graphStatusBar.innerHTML = `<span class="text-amber-400 font-bold uppercase tracking-wider">⚡ Divergence Point:</span> Tree 1 applies <span class="text-indigo-300 font-mono font-bold bg-indigo-950 px-1.5 py-0.5 rounded border border-indigo-700">${rule1Diverge}</span> while Tree 2 applies <span class="text-purple-300 font-mono font-bold bg-purple-950 px-1.5 py-0.5 rounded border border-purple-700">${rule2Diverge}</span>!`;
    } else if (graphStage === 2 && isDual) {
      graphStatusBar.innerHTML = `<span class="text-indigo-400 font-bold">Intermediate Derivations:</span> Both concurrent branches continue expanding sentential forms toward yield <span class="text-white font-mono font-bold">"${targetString}"</span>.`;
    } else if (graphStage === graphMaxStages) {
      if (isDual) {
        graphStatusBar.innerHTML = `<span class="text-emerald-400 font-bold font-mono text-sm tracking-wide">✓ AMBIGUITY PROVEN:</span> 2 distinct derivation sequences both converge to yield target string <span class="text-white font-mono font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-600">"${targetString}"</span>!`;
      } else {
        graphStatusBar.innerHTML = `<span class="text-emerald-400 font-bold font-mono">✓ UNAMBIGUOUS:</span> Single unique derivation sequence successfully generated target string <span class="text-white font-mono font-bold">"${targetString}"</span>.`;
      }
      stopGraphPlay();
    }
  }
}

function startGraphPlay() {
  stopGraphPlay();
  if (graphStage >= graphMaxStages) {
    graphStage = 0;
    setGraphStage(0);
  }

  if (graphPlayBtn) {
    graphPlayBtn.textContent = '⏸ Pause';
    graphPlayBtn.className = 'px-3.5 py-1 bg-amber-600 hover:bg-amber-500 text-white text-xs rounded-lg font-bold shadow transition-all';
  }

  setGraphStage(graphStage + 1);

  const delay = graphSpeedSelect ? (parseInt(graphSpeedSelect.value, 10) || graphAnimationDelay) : graphAnimationDelay;
  graphPlayInterval = setInterval(() => {
    if (graphStage < graphMaxStages) {
      setGraphStage(graphStage + 1);
    } else {
      stopGraphPlay();
    }
  }, delay);
}

function stopGraphPlay() {
  if (graphPlayInterval) {
    clearInterval(graphPlayInterval);
    graphPlayInterval = null;
  }
  if (graphPlayBtn) {
    graphPlayBtn.textContent = '▶ Play Derivation';
    graphPlayBtn.className = 'px-3.5 py-1 luxury-btn-primary text-white text-xs rounded-lg font-bold shadow transition-all';
  }
}

if (graphPlayBtn) {
  graphPlayBtn.addEventListener('click', () => {
    if (graphPlayInterval) stopGraphPlay();
    else startGraphPlay();
  });
}

if (graphNextBtn) {
  graphNextBtn.addEventListener('click', () => {
    stopGraphPlay();
    if (graphStage < graphMaxStages) setGraphStage(graphStage + 1);
  });
}

if (graphPrevBtn) {
  graphPrevBtn.addEventListener('click', () => {
    stopGraphPlay();
    if (graphStage > 0) setGraphStage(graphStage - 1);
  });
}

if (graphResetBtn) {
  graphResetBtn.addEventListener('click', () => {
    stopGraphPlay();
    setGraphStage(0);
  });
}

// ============================================================================
// --- EARLEY PARSER TABLE RENDERING & FILTERING ---
// ============================================================================
function renderEarleyChart(chart) {
  const earleyContainer = document.getElementById('earley-container');
  const earleyFilterBar = document.getElementById('earley-filter-bar');
  const earleyStatesList = document.getElementById('earley-states-list');

  if (!chart || chart.length === 0) {
    if (earleyContainer) earleyContainer.classList.add('hidden');
    if (simulationPanel) simulationPanel.classList.add('hidden');
    return;
  }

  if (earleyContainer) earleyContainer.classList.remove('hidden');
  if (simulationPanel) {
    simulationPanel.classList.remove('hidden');
    if (totalStepsLabel) totalStepsLabel.textContent = executionSteps.length;
    if (currentStepLabel) currentStepLabel.textContent = '0';
  }

  // Populate filter pills
  if (earleyFilterBar) {
    let pillsHtml = `<button type="button" class="state-pill active" data-filter="all">All States (${chart.length})</button>`;
    chart.forEach(s => {
      const setName = s.state_set || `S_${s.state_index}`;
      pillsHtml += `<button type="button" class="state-pill" data-filter="${setName}">${setName} (${s.items.length})</button>`;
    });
    earleyFilterBar.innerHTML = pillsHtml;

    earleyFilterBar.querySelectorAll('.state-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        earleyFilterBar.querySelectorAll('.state-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.getAttribute('data-filter');
        filterEarleyStates(filter);
      });
    });
  }

  if (earleyStatesList) {
    earleyStatesList.innerHTML = '';

    chart.forEach(set => {
      const setName = set.state_set || `S_${set.state_index}`;
      const tokenLabel = set.token_label || `Token '${set.token}'`;

      let rows = set.items.map((item, idx) => `
        <tr id="earley-row-${setName}-${idx}" class="earley-row border-b border-white/[0.04] text-xs hover:bg-white/[0.03] transition-all duration-200">
          <td class="p-2.5 text-slate-500 font-mono w-10 text-[11px]">${idx}</td>
          <td class="p-2.5 text-indigo-300 font-mono font-medium">${item.item || item.rule}</td>
          <td class="p-2.5 text-center text-slate-400 font-mono w-20 text-[11px]">${item.origin}</td>
          <td class="p-2.5 text-slate-400 text-xs">${item.operation}</td>
        </tr>
      `).join('');

      earleyStatesList.innerHTML += `
        <div id="earley-box-${setName}" class="earley-state-box border border-white/[0.08] rounded-xl overflow-hidden mb-4 bg-[#0a0d15]/80 shadow-md transition-all">
          <div class="bg-white/[0.03] px-4 py-2.5 font-bold text-xs text-white flex items-center justify-between border-b border-white/[0.06]">
            <span class="text-indigo-400 font-mono font-bold">${setName}</span>
            <span class="text-slate-400 font-mono text-[11px]">${tokenLabel} &bull; ${set.items.length} items</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left bg-transparent">
              <thead>
                <tr class="text-[10px] text-slate-400 border-b border-white/[0.06] bg-white/[0.02] uppercase tracking-wider font-mono">
                  <th class="p-2.5 w-10">#</th>
                  <th class="p-2.5">Item</th>
                  <th class="p-2.5 text-center w-20">Origin</th>
                  <th class="p-2.5">Operation</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
      `;
    });
  }
}

function filterEarleyStates(filter) {
  const boxes = document.querySelectorAll('.earley-state-box');
  boxes.forEach(box => {
    if (filter === 'all' || box.id === `earley-box-${filter}`) {
      box.style.display = 'block';
    } else {
      box.style.display = 'none';
    }
  });
}

// ============================================================================
// --- MANUAL WALKTHROUGH & SIMULATION CONTROLLER ---
// ============================================================================
let executionSteps = [];
let currentStepIndex = -1;
let playInterval = null;

const simulationPanel = document.getElementById('simulation-panel');
const currentStepLabel = document.getElementById('current-step-label');
const totalStepsLabel = document.getElementById('total-steps-label');
const btnPrevStep = document.getElementById('btn-prev-step');
const btnPlayPause = document.getElementById('btn-play-pause');
const btnNextStep = document.getElementById('btn-next-step');
const btnResetSteps = document.getElementById('btn-reset-steps');
const playbackSpeed = document.getElementById('playback-speed');
const reasoningBox = document.getElementById('reasoning-box');

function stopPlay() {
  if (playInterval) {
    clearInterval(playInterval);
    playInterval = null;
  }
  if (btnPlayPause) {
    btnPlayPause.textContent = '▶ Play Auto';
    btnPlayPause.className = 'px-3.5 py-1 luxury-btn-primary text-white text-xs rounded-lg font-bold shadow transition-all cursor-pointer';
  }
}

function startPlay() {
  stopPlay();
  if (!executionSteps || executionSteps.length === 0) return;

  if (currentStepIndex >= executionSteps.length - 1) {
    currentStepIndex = -1;
  }

  if (btnPlayPause) {
    btnPlayPause.textContent = '⏸ Pause';
    btnPlayPause.className = 'px-3.5 py-1 bg-amber-600 hover:bg-amber-500 text-white text-xs rounded-lg font-bold shadow transition-all cursor-pointer';
  }

  stepTo(currentStepIndex + 1);

  const speed = parseInt(playbackSpeed ? playbackSpeed.value : '800', 10) || 800;
  playInterval = setInterval(() => {
    if (currentStepIndex < executionSteps.length - 1) {
      stepTo(currentStepIndex + 1);
    } else {
      stopPlay();
    }
  }, speed);
}

function resetSimulation() {
  stopPlay();
  currentStepIndex = -1;
  if (currentStepLabel) currentStepLabel.textContent = '0';
  document.querySelectorAll('.earley-row').forEach(row => {
    row.classList.remove('bg-indigo-900/60', 'border-l-4', 'border-indigo-400', 'text-white', 'shadow-md', 'ring-1', 'ring-indigo-500/50');
  });
  if (reasoningBox) {
    reasoningBox.innerHTML = `Click 'Next Step' or 'Play Auto' to begin the manual derivation walkthrough...`;
  }
}

function stepTo(index) {
  if (index < 0 || index >= executionSteps.length) return;

  document.querySelectorAll('.earley-row').forEach(row => {
    row.classList.remove('bg-indigo-900/60', 'border-l-4', 'border-indigo-400', 'text-white', 'shadow-md', 'ring-1', 'ring-indigo-500/50');
  });

  currentStepIndex = index;
  if (currentStepLabel) currentStepLabel.textContent = (index + 1);

  const step = executionSteps[index];

  // If a filter is currently active that hides this state box, reveal it
  const parentBox = document.getElementById(`earley-box-${step.target_state_set}`);
  if (parentBox && parentBox.style.display === 'none') {
    parentBox.style.display = 'block';
  }

  const rowId = `earley-row-${step.target_state_set}-${step.item_index}`;
  const targetRow = document.getElementById(rowId);
  if (targetRow) {
    targetRow.classList.add('bg-indigo-900/60', 'border-l-4', 'border-indigo-400', 'text-white', 'shadow-md', 'ring-1', 'ring-indigo-500/50');
    targetRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  let badgeColor = 'bg-slate-700 text-slate-200 border-slate-600';
  if (step.operation_type === 'INITIAL') {
    badgeColor = 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
  } else if (step.operation_type === 'PREDICTOR') {
    badgeColor = 'bg-blue-500/20 text-blue-400 border-blue-500/40';
  } else if (step.operation_type === 'SCANNER') {
    badgeColor = 'bg-purple-500/20 text-purple-400 border-purple-500/40';
  } else if (step.operation_type === 'COMPLETER') {
    badgeColor = 'bg-amber-500/20 text-amber-400 border-amber-500/40';
  }

  if (reasoningBox) {
    reasoningBox.innerHTML = `
      <div class="space-y-2 w-full">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${badgeColor}">${step.operation_type}</span>
          <span class="font-mono text-xs font-semibold text-white bg-slate-900 px-2 py-0.5 rounded border border-slate-700">${step.target_state_set} : ${step.item_added}</span>
          <span class="text-[11px] text-slate-400 font-mono">(origin: S_${step.origin})</span>
        </div>
        <div class="text-xs text-indigo-100 font-sans leading-relaxed pt-1.5 border-t border-slate-800/80">
          ${step.human_reasoning}
        </div>
      </div>
    `;
  }

  if (index === executionSteps.length - 1) {
    stopPlay();
  }
}

if (btnPlayPause) {
  btnPlayPause.addEventListener('click', () => {
    if (playInterval) stopPlay();
    else startPlay();
  });
}

if (btnNextStep) {
  btnNextStep.addEventListener('click', () => {
    stopPlay();
    if (currentStepIndex < executionSteps.length - 1) stepTo(currentStepIndex + 1);
  });
}

if (btnPrevStep) {
  btnPrevStep.addEventListener('click', () => {
    stopPlay();
    if (currentStepIndex > 0) stepTo(currentStepIndex - 1);
  });
}

if (btnResetSteps) {
  btnResetSteps.addEventListener('click', resetSimulation);
}

if (playbackSpeed) {
  playbackSpeed.addEventListener('change', () => {
    if (playInterval) startPlay();
  });
}
