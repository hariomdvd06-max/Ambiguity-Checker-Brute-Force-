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
      // Fallback instruction for users on unsupported environments or already installed apps
      alert("PWA Install prompt abhi available nahi hai. Ya toh app pehle se installed hai, ya aap browser ke top-right 3 dots menu se 'Add to Home screen' / 'Install App' par click kar sakte hain.");
    }
  });
}

window.addEventListener('appinstalled', () => {
  if (installBtn) {
    installBtn.style.display = 'none';
  }
  console.log('App successfully installed!');
});

// Register Service Worker for PWA compliance
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./service-worker.js')
      .then((reg) => console.log('SW Registered:', reg.scope))
      .catch((err) => console.error('SW Registration Failed:', err));
  });
}

// --- Dynamic Rules State Management ---
const rulesContainer = document.getElementById('rules-container');
const addRuleBtn = document.getElementById('add-rule-btn');

function createRuleRow(lhs = '', rhs = '') {
  const row = document.createElement('div');
  row.className = 'flex items-center gap-2 rule-row group';
  row.innerHTML = `
    <input type="text" value="${lhs}" placeholder="LHS" class="w-16 luxury-input px-2.5 py-1.5 text-xs text-center font-bold text-indigo-300 rounded-lg outline-none" />
    <span class="text-slate-500 text-xs font-mono select-none px-0.5">→</span>
    <input type="text" value="${rhs}" placeholder="RHS (e.g. S + S | a)" class="flex-1 luxury-input px-3 py-1.5 text-xs text-slate-200 rounded-lg outline-none" />
    <button type="button" class="delete-rule text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors cursor-pointer" title="Delete rule">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
    </button>
  `;
  row.querySelector('.delete-rule').addEventListener('click', () => {
    if (document.querySelectorAll('.rule-row').length > 1) {
      row.remove();
    }
  });
  rulesContainer.appendChild(row);
}

// Default initial starter grammar
createRuleRow('S', 'S + S | a');
addRuleBtn.addEventListener('click', () => createRuleRow('', ''));

// Quick Presets Loader
function loadPreset(presetName) {
  rulesContainer.innerHTML = '';
  const startSymInput = document.getElementById('start-symbol');
  const targetStrInput = document.getElementById('target-string');

  if (presetName === 'classic') {
    startSymInput.value = 'S';
    createRuleRow('S', 'S + S | a');
    targetStrInput.value = 'a+a+a';
  } else if (presetName === 'dangling') {
    startSymInput.value = 'S';
    createRuleRow('S', 'i C t S | i C t S e S | a');
    createRuleRow('C', 'b');
    targetStrInput.value = 'i b t i b t a e a';
  } else if (presetName === 'boolean') {
    startSymInput.value = 'E';
    createRuleRow('E', 'E or E | E and E | t | f');
    targetStrInput.value = 't or t and f';
  } else if (presetName === 'parens') {
    startSymInput.value = 'S';
    createRuleRow('S', '( S ) S | ε');
    targetStrInput.value = '()()';
  }
}

document.querySelectorAll('.preset-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const preset = btn.getAttribute('data-preset');
    loadPreset(preset);
  });
});

// Enter key shortcut on target string
const targetStringInput = document.getElementById('target-string');
if (targetStringInput) {
  targetStringInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      document.getElementById('check-btn').click();
    }
  });
}

// --- Tree Visualization Renderer ---
function renderTreeDOM(node) {
  const container = document.createElement('div');
  container.className = 'tree-node';

  const badge = document.createElement('div');
  const isLeaf = !node.children || node.children.length === 0;
  const isEpsilon = node.symbol === 'ε' || node.symbol === 'eps' || node.symbol === 'epsilon';

  let badgeClass = 'node-badge';
  if (isEpsilon) {
    badgeClass += ' epsilon';
  } else if (isLeaf) {
    badgeClass += ' terminal';
  }
  badge.className = badgeClass;
  badge.textContent = node.symbol;
  container.appendChild(badge);

  if (!isLeaf) {
    const childrenContainer = document.createElement('div');
    childrenContainer.className = 'node-children';
    node.children.forEach(child => {
      childrenContainer.appendChild(renderTreeDOM(child));
    });
    container.appendChild(childrenContainer);
  }

  return container;
}

// --- API Execution ---
const checkBtn = document.getElementById('check-btn');
const verdictCard = document.getElementById('verdict-card');
const verdictBadge = document.getElementById('verdict-badge');
const treeCountBadge = document.getElementById('tree-count-badge');
const explanationText = document.getElementById('explanation-text');
const treesContainer = document.getElementById('trees-container');
const emptyState = document.getElementById('empty-state');
const tree1Box = document.getElementById('tree-1');
const tree2Box = document.getElementById('tree-2');

// Localhost ya relative hatakar apna Render backend URL daalein:
const BACKEND_URL = "https://cfg-ambiguity-backend.onrender.com"; // <-- apna Render URL yahan rakhein

checkBtn.addEventListener('click', async () => {
  const startSymbol = document.getElementById('start-symbol').value.trim();
  const targetString = document.getElementById('target-string').value.trim();

  const ruleRows = document.querySelectorAll('.rule-row');
  const rules = [];
  ruleRows.forEach(row => {
    const inputs = row.querySelectorAll('input');
    const lhs = inputs[0].value.trim();
    const rhs = inputs[1].value.trim();
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

  if (!targetString) {
    alert('Please provide a target string to evaluate.');
    return;
  }

  checkBtn.disabled = true;
  checkBtn.innerHTML = `
    <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
    </svg>
    <span>Evaluating...</span>
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

    // Render results
    emptyState.classList.add('hidden');
    verdictCard.classList.remove('hidden');

    if (data.is_ambiguous) {
      verdictBadge.textContent = 'AMBIGUOUS CFG';
      verdictBadge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20 shadow-sm';
    } else if (data.tree_count === 1) {
      verdictBadge.textContent = 'UNAMBIGUOUS / SINGLE TREE';
      verdictBadge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm';
    } else {
      verdictBadge.textContent = 'NOT IN LANGUAGE / NO TREE';
      verdictBadge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm';
    }

    treeCountBadge.textContent = `Trees Found: ${data.tree_count}`;
    explanationText.textContent = data.explanation;

    // Render Parse Trees
    tree1Box.innerHTML = '';
    tree2Box.innerHTML = '';

    if (data.trees.length > 0) {
      treesContainer.classList.remove('hidden');
      tree1Box.appendChild(renderTreeDOM(data.trees[0]));

      if (data.trees.length > 1) {
        tree2Box.parentElement.classList.remove('hidden');
        tree2Box.appendChild(renderTreeDOM(data.trees[1]));
      } else {
        tree2Box.parentElement.classList.add('hidden');
      }

      // Render Interactive Derivation Flow Graph
      renderDerivationFlowGraph(data.trees, data.target_string, data.is_ambiguous);
    } else {
      treesContainer.classList.add('hidden');
      const derivationCard = document.getElementById('derivation-automaton-card');
      if (derivationCard) derivationCard.classList.add('hidden');
    }

    // Render Earley Parser Chart & Simulation Controller
    const earleyContainer = document.getElementById('earley-container');
    const earleyStatesList = document.getElementById('earley-states-list');

    executionSteps = data.execution_steps || [];
    resetSimulation();

    if (data.earley_chart && data.earley_chart.length > 0) {
      console.log("Earley Chart found, rendering...", data.earley_chart);
      if (earleyContainer) {
        earleyContainer.classList.remove('hidden');
        earleyContainer.style.display = 'block';
      }
      if (simulationPanel) {
        simulationPanel.classList.remove('hidden');
        if (totalStepsLabel) totalStepsLabel.textContent = executionSteps.length;
        if (currentStepLabel) currentStepLabel.textContent = '0';
      }

      if (earleyStatesList) {
        earleyStatesList.innerHTML = '';

        data.earley_chart.forEach(set => {
          let rows = set.items.map((item, idx) => `
            <tr id="earley-row-${set.state_set}-${idx}" class="earley-row border-b border-white/[0.04] text-xs hover:bg-white/[0.03] transition-all duration-200">
              <td class="p-2.5 text-slate-500 font-mono w-10 text-[11px]">${idx}</td>
              <td class="p-2.5 text-indigo-300 font-mono font-medium">${item.rule}</td>
              <td class="p-2.5 text-center text-slate-400 font-mono w-20 text-[11px]">${item.origin}</td>
              <td class="p-2.5 text-slate-400 text-xs">${item.operation}</td>
            </tr>
          `).join('');

          earleyStatesList.innerHTML += `
            <div class="border border-white/[0.08] rounded-xl overflow-hidden mb-4 bg-[#0a0d15]/80 shadow-md">
              <div class="bg-white/[0.03] px-4 py-2.5 font-bold text-xs text-white flex items-center justify-between border-b border-white/[0.06]">
                <span class="text-indigo-400 font-mono font-bold">${set.state_set}</span>
                <span class="text-slate-400 font-mono text-[11px]">${set.token_label}</span>
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
    } else {
      console.warn("No earley_chart field found in response!");
      if (earleyContainer) {
        earleyContainer.classList.add('hidden');
        earleyContainer.style.display = 'none';
      }
      if (simulationPanel) simulationPanel.classList.add('hidden');
    }

  } catch (error) {
    alert('Error: ' + error.message);
  } finally {
    checkBtn.disabled = false;
    checkBtn.innerHTML = `<span>Evaluate Ambiguity</span>`;
  }
});

// --- Interactive Earley Simulation & Manual Solver Engine ---
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
    btnPlayPause.className = 'px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs rounded-lg font-bold shadow transition-all';
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
    btnPlayPause.className = 'px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs rounded-lg font-bold shadow transition-all';
  }

  // Advance first step immediately
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

  // Clear previous row highlights
  document.querySelectorAll('.earley-row').forEach(row => {
    row.classList.remove('bg-indigo-900/60', 'border-l-4', 'border-indigo-400', 'text-white', 'shadow-md', 'ring-1', 'ring-indigo-500/50');
  });

  currentStepIndex = index;
  if (currentStepLabel) currentStepLabel.textContent = (index + 1);

  const step = executionSteps[index];

  // Highlight active row in table
  const rowId = `earley-row-${step.target_state_set}-${step.item_index}`;
  const targetRow = document.getElementById(rowId);
  if (targetRow) {
    targetRow.classList.add('bg-indigo-900/60', 'border-l-4', 'border-indigo-400', 'text-white', 'shadow-md', 'ring-1', 'ring-indigo-500/50');
    targetRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Operation badge color styling
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

// Bind simulation event listeners
if (btnPlayPause) {
  btnPlayPause.addEventListener('click', () => {
    if (playInterval) {
      stopPlay();
    } else {
      startPlay();
    }
  });
}

if (btnNextStep) {
  btnNextStep.addEventListener('click', () => {
    stopPlay();
    if (currentStepIndex < executionSteps.length - 1) {
      stepTo(currentStepIndex + 1);
    }
  });
}

if (btnPrevStep) {
  btnPrevStep.addEventListener('click', () => {
    stopPlay();
    if (currentStepIndex > 0) {
      stepTo(currentStepIndex - 1);
    }
  });
}

if (btnResetSteps) {
  btnResetSteps.addEventListener('click', resetSimulation);
}

if (playbackSpeed) {
  playbackSpeed.addEventListener('change', () => {
    if (playInterval) {
      startPlay();
    }
  });
}

// ============================================================================
// --- INTERACTIVE DERIVATION FLOW AUTOMATON (DUAL-BRANCH VISUALIZER) ---
// ============================================================================

let graphStage = 0;
let graphMaxStages = 0;
let graphPlayInterval = null;
let currentDerivationData = null;
let graphAnimationDelay = 2500;

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
    graphAnimationDelay = parseInt(e.target.value, 10) || 2500;
    if (graphPlayInterval) {
      startGraphPlay();
    }
  });
}

function extractLeftmostDerivation(tree) {
  if (!tree) return [];

  function cloneTree(node) {
    return {
      symbol: node.symbol,
      children: node.children ? node.children.map(cloneTree) : []
    };
  }

  const root = cloneTree(tree);
  let sententialNodes = [root];
  
  const steps = [{
    stepNum: 0,
    rule: "Start",
    sentential: root.symbol,
    appliedRule: ""
  }];

  let safety = 0;
  while (safety++ < 40) {
    const leftmostIdx = sententialNodes.findIndex(n => n.children && n.children.length > 0);
    if (leftmostIdx === -1) break;

    const targetNode = sententialNodes[leftmostIdx];
    const rhsSymbols = targetNode.children.map(c => c.symbol);
    const ruleStr = `${targetNode.symbol} → ${rhsSymbols.join(' ')}`;

    sententialNodes.splice(leftmostIdx, 1, ...targetNode.children);

    const sententialStr = sententialNodes
      .map(c => c.symbol)
      .filter(s => s !== 'ε')
      .join(' ');

    steps.push({
      stepNum: steps.length,
      rule: ruleStr,
      sentential: sententialStr || "ε",
      appliedRule: ruleStr
    });
  }

  return steps;
}

function renderDerivationFlowGraph(trees, targetString, isAmbiguous) {
  if (!derivationAutomatonCard || !derivationSvg) return;

  if (!trees || trees.length === 0) {
    derivationAutomatonCard.classList.add('hidden');
    return;
  }

  derivationAutomatonCard.classList.remove('hidden');
  stopGraphPlay();

  const path1 = extractLeftmostDerivation(trees[0]);
  const path2 = isAmbiguous && trees.length > 1 ? extractLeftmostDerivation(trees[1]) : [];

  const isDual = isAmbiguous && path2.length > 0;
  const maxPathLen = Math.max(path1.length, path2.length);
  
  let numInter = 2;
  if (maxPathLen <= 3) numInter = 1;
  else if (maxPathLen <= 4) numInter = 2;
  else numInter = 3;

  const totalSteps = numInter + 1;
  const totalWidth = Math.max(850, (totalSteps + 1) * 160);

  // Configure responsive attributes on SVG canvas
  derivationSvg.setAttribute('viewBox', `0 0 ${totalWidth} 260`);
  derivationSvg.setAttribute('preserveAspectRatio', 'xMinYMid meet');
  derivationSvg.style.width = '100%';
  derivationSvg.style.height = 'auto';

  // Safe left padding and right padding to avoid clipping on mobile
  const startX = 85;
  const acceptX = totalWidth - 85;

  let xCoords = [];
  for (let i = 0; i < numInter; i++) {
    xCoords.push(startX + ((i + 1) / (numInter + 1)) * (acceptX - startX));
  }

  function samplePath(path, count) {
    if (path.length <= 1) return [];
    if (count === 1) {
      return [{
        rule: path[1].appliedRule,
        sentential: path[1].sentential
      }];
    }
    if (count === 2) {
      const idx1 = 1;
      const idx2 = path.length > 2 ? path.length - 1 : 1;
      return [
        { rule: path[idx1].appliedRule, sentential: path[idx1].sentential },
        { rule: path[idx2].appliedRule, sentential: path[idx2].sentential }
      ];
    }
    const idx1 = 1;
    const idx2 = Math.min(Math.floor(path.length / 2), path.length - 1);
    const idx3 = path.length - 1;
    return [
      { rule: path[idx1].appliedRule, sentential: path[idx1].sentential },
      { rule: path[idx2].appliedRule, sentential: path[idx2].sentential },
      { rule: path[idx3].appliedRule, sentential: path[idx3].sentential }
    ];
  }

  const upperMilestones = samplePath(path1, numInter);
  const lowerMilestones = isDual ? samplePath(path2, numInter) : [];

  graphMaxStages = numInter + 1;
  currentDerivationData = {
    targetString,
    isDual,
    numInter,
    totalWidth,
    startX,
    acceptX,
    path1,
    path2,
    upperMilestones,
    lowerMilestones
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

  // Start indicator line and text
  svg += `
    <line x1="${startX - 60}" y1="130" x2="${startX - 28}" y2="130" stroke="#6366f1" stroke-width="2" marker-end="url(#arr-active)"/>
    <text x="${startX - 44}" y="118" fill="#a5b4fc" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">Start</text>
  `;

  // Start Node at (startX, 130)
  const startSymbol = trees[0].symbol;
  svg += `
    <g id="g-node-start" class="derivation-node cursor-pointer transition-all duration-300">
      <circle cx="${startX}" cy="130" r="24" fill="#312e81" stroke="#818cf8" stroke-width="2.5" filter="url(#svg-glow)"/>
      <text x="${startX}" y="135" fill="#ffffff" font-size="14" font-weight="bold" font-family="monospace" text-anchor="middle">${startSymbol}</text>
    </g>
  `;

  // Final Accepted Node at (acceptX, 130)
  const displayTarget = targetString.length > 8 ? targetString.slice(0, 7) + '…' : targetString;
  svg += `
    <g id="g-node-accept" class="derivation-node transition-all duration-300">
      <circle id="accept-outer-circle" cx="${acceptX}" cy="130" r="28" fill="none" stroke="#475569" stroke-width="2"/>
      <circle id="accept-inner-circle" cx="${acceptX}" cy="130" r="23" fill="#0f172a" stroke="#475569" stroke-width="2"/>
      <text id="accept-text" x="${acceptX}" y="135" fill="#94a3b8" font-size="12" font-weight="bold" font-family="monospace" text-anchor="middle">${displayTarget}</text>
      <text x="${acceptX}" y="172" fill="#64748b" font-size="10" font-family="sans-serif" font-weight="600" text-anchor="middle">Accepted (w)</text>
    </g>
  `;

  // Branch Labels (Upper: Tree 1 / Lower: Tree 2)
  if (isDual) {
    svg += `
      <text x="${startX + 38}" y="44" fill="#818cf8" font-size="10" font-family="sans-serif" font-weight="bold" opacity="0.9">✦ Tree 1 (Leftmost Branch)</text>
      <text x="${startX + 38}" y="224" fill="#c084fc" font-size="10" font-family="sans-serif" font-weight="bold" opacity="0.9">✦ Tree 2 (Alternative Branch)</text>
    `;

    // Upper Branch (y = 70)
    const x0 = xCoords[0];
    svg += `
      <path id="edge-up-0" data-stage="1" d="M ${startX + 22},120 C ${startX + 50},70 ${x0 - 45},70 ${x0 - 22},70" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path transition-all duration-300"/>
      <g id="lbl-up-0" data-stage="1" class="derivation-label transition-all duration-300 opacity-60">
        <rect x="${(startX + 22 + x0) / 2 - 45}" y="58" width="90" height="18" rx="4" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
        <text x="${(startX + 22 + x0) / 2}" y="71" fill="#94a3b8" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">${upperMilestones[0].rule}</text>
      </g>
    `;

    for (let i = 0; i < numInter; i++) {
      const xi = xCoords[i];
      const m = upperMilestones[i];
      const stageIdx = i + 1;

      svg += `
        <g id="node-up-${i}" data-stage="${stageIdx}" class="derivation-node transition-all duration-300">
          <circle cx="${xi}" cy="70" r="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>
          <text x="${xi}" y="74" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">q₁${i + 1}</text>
          <text x="${xi}" y="38" fill="#818cf8" font-size="9" font-family="monospace" text-anchor="middle">${m.sentential.length > 11 ? m.sentential.slice(0, 10) + '…' : m.sentential}</text>
        </g>
      `;

      if (i < numInter - 1) {
        const xNext = xCoords[i + 1];
        const nextM = upperMilestones[i + 1];
        const nextStage = i + 2;
        svg += `
          <line id="edge-up-${i + 1}" data-stage="${nextStage}" x1="${xi + 20}" y1="70" x2="${xNext - 20}" y2="70" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path transition-all duration-300"/>
          <g id="lbl-up-${i + 1}" data-stage="${nextStage}" class="derivation-label transition-all duration-300 opacity-60">
            <rect x="${(xi + xNext) / 2 - 40}" y="52" width="80" height="16" rx="3" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
            <text x="${(xi + xNext) / 2}" y="64" fill="#94a3b8" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">${nextM.rule}</text>
          </g>
        `;
      }
    }

    const xLastUp = xCoords[numInter - 1];
    const finalStage = numInter + 1;
    svg += `
      <path id="edge-up-final" data-stage="${finalStage}" d="M ${xLastUp + 20},70 C ${xLastUp + 45},70 ${acceptX - 55},122 ${acceptX - 28},126" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path transition-all duration-300"/>
    `;

    // Lower Branch (y = 190)
    svg += `
      <path id="edge-down-0" data-stage="1" d="M ${startX + 22},140 C ${startX + 50},190 ${x0 - 45},190 ${x0 - 22},190" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path transition-all duration-300"/>
      <g id="lbl-down-0" data-stage="1" class="derivation-label transition-all duration-300 opacity-60">
        <rect x="${(startX + 22 + x0) / 2 - 45}" y="180" width="90" height="18" rx="4" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
        <text x="${(startX + 22 + x0) / 2}" y="193" fill="#94a3b8" font-size="10" font-family="monospace" font-weight="bold" text-anchor="middle">${lowerMilestones[0].rule}</text>
      </g>
    `;

    for (let i = 0; i < numInter; i++) {
      const xi = xCoords[i];
      const m = lowerMilestones[i];
      const stageIdx = i + 1;

      svg += `
        <g id="node-down-${i}" data-stage="${stageIdx}" class="derivation-node transition-all duration-300">
          <circle cx="${xi}" cy="190" r="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>
          <text x="${xi}" y="194" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">q₂${i + 1}</text>
          <text x="${xi}" y="222" fill="#c084fc" font-size="9" font-family="monospace" text-anchor="middle">${m.sentential.length > 11 ? m.sentential.slice(0, 10) + '…' : m.sentential}</text>
        </g>
      `;

      if (i < numInter - 1) {
        const xNext = xCoords[i + 1];
        const nextM = lowerMilestones[i + 1];
        const nextStage = i + 2;
        svg += `
          <line id="edge-down-${i + 1}" data-stage="${nextStage}" x1="${xi + 20}" y1="190" x2="${xNext - 20}" y2="190" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path transition-all duration-300"/>
          <g id="lbl-down-${i + 1}" data-stage="${nextStage}" class="derivation-label transition-all duration-300 opacity-60">
            <rect x="${(xi + xNext) / 2 - 40}" y="188" width="80" height="16" rx="3" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
            <text x="${(xi + xNext) / 2}" y="200" fill="#94a3b8" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">${nextM.rule}</text>
          </g>
        `;
      }
    }

    const xLastDown = xCoords[numInter - 1];
    svg += `
      <path id="edge-down-final" data-stage="${finalStage}" d="M ${xLastDown + 20},190 C ${xLastDown + 45},190 ${acceptX - 55},138 ${acceptX - 28},134" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path transition-all duration-300"/>
    `;
  } else {
    // Single linear branch (Unambiguous)
    const x0 = xCoords[0];
    for (let i = 0; i < numInter; i++) {
      const xi = xCoords[i];
      const m = upperMilestones[i];
      const stageIdx = i + 1;

      if (i === 0) {
        svg += `
          <line id="edge-linear-0" data-stage="1" x1="${startX + 24}" y1="130" x2="${xi - 20}" y2="130" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
          <g id="lbl-linear-0" data-stage="1" class="derivation-label transition-all duration-300 opacity-60">
            <rect x="${(startX + 24 + xi) / 2 - 40}" y="112" width="80" height="16" rx="3" fill="#090d16" fill-opacity="0.95" stroke="#334155" stroke-width="1"/>
            <text x="${(startX + 24 + xi) / 2}" y="124" fill="#94a3b8" font-size="9" font-family="monospace" font-weight="bold" text-anchor="middle">${m.rule}</text>
          </g>
        `;
      } else {
        const xPrev = xCoords[i - 1];
        svg += `
          <line id="edge-linear-${i}" data-stage="${stageIdx}" x1="${xPrev + 20}" y1="130" x2="${xi - 20}" y2="130" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
        `;
      }

      svg += `
        <g id="node-linear-${i}" data-stage="${stageIdx}" class="derivation-node transition-all duration-300">
          <circle cx="${xi}" cy="130" r="20" fill="#0f172a" stroke="#334155" stroke-width="2"/>
          <text x="${xi}" y="134" fill="#94a3b8" font-size="11" font-weight="bold" font-family="monospace" text-anchor="middle">q${i + 1}</text>
          <text x="${xi}" y="98" fill="#818cf8" font-size="9" font-family="monospace" text-anchor="middle">${m.sentential}</text>
        </g>
      `;
    }

    const xLast = xCoords[numInter - 1];
    const finalStage = numInter + 1;
    svg += `
      <line id="edge-linear-final" data-stage="${finalStage}" x1="${xLast + 20}" y1="130" x2="${acceptX - 28}" y2="130" stroke="#334155" stroke-width="2" marker-end="url(#arr-inactive)" class="derivation-path"/>
    `;
  }

  derivationSvg.innerHTML = svg;
  setGraphStage(0);
}

function setGraphStage(stage) {
  if (!currentDerivationData) return;
  graphStage = Math.max(0, Math.min(stage, graphMaxStages));

  const { isDual, upperMilestones, lowerMilestones, targetString } = currentDerivationData;

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
    if (acceptText) {
      acceptText.setAttribute('fill', '#a7f3d0');
    }
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
    if (acceptText) {
      acceptText.setAttribute('fill', '#94a3b8');
    }
  }

  if (graphStatusBar) {
    if (graphStage === 0) {
      graphStatusBar.innerHTML = `<span class="text-indigo-400 font-bold">Start Symbol [${currentDerivationData.path1[0].sentential}]:</span> Derivation initialized for target string <span class="text-white font-mono font-bold">"${targetString}"</span>. Click <strong>'Play Derivation'</strong> or <strong>'Next ›'</strong> to observe flow.`;
    } else if (graphStage === 1 && isDual) {
      graphStatusBar.innerHTML = `<span class="text-amber-400 font-bold uppercase tracking-wider">⚡ Divergence Point:</span> Tree 1 applies <span class="text-indigo-300 font-mono font-bold bg-indigo-950 px-1.5 py-0.5 rounded border border-indigo-700">${upperMilestones[0].rule}</span> while Tree 2 applies <span class="text-purple-300 font-mono font-bold bg-purple-950 px-1.5 py-0.5 rounded border border-purple-700">${lowerMilestones[0].rule}</span>!`;
    } else if (graphStage < graphMaxStages && isDual) {
      const idx = graphStage - 1;
      const up = upperMilestones[idx];
      const down = lowerMilestones[idx];
      graphStatusBar.innerHTML = `<span class="text-indigo-400 font-bold">Step ${graphStage}:</span> Upper branch sentential form: <span class="text-indigo-200 font-mono font-bold">${up ? up.sentential : '...'}</span> | Lower branch: <span class="text-purple-200 font-mono font-bold">${down ? down.sentential : '...'}</span>`;
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
    graphPlayBtn.className = 'px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs rounded-lg font-bold shadow transition-all';
  }

  // Step first stage forward
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
    graphPlayBtn.className = 'px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs rounded-lg font-bold shadow transition-all';
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
