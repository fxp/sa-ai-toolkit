/**
 * METR Org-Uplift Game — Main Application
 * State machine: setup → standup → work → (repeat 4x) → report
 */

const App = (() => {
  // ── State ──
  const PHASES = ['setup', 'standup', 'work', 'roundSummary', 'finalReport'];
  const TOTAL_ROUNDS = 4;
  const HOURS_PER_ROUND = 5;
  const STANDUP_SECONDS = 300;  // 5 min
  const WORK_SECONDS = 600;     // 10 min

  let state = loadState() || {
    phase: 'setup',
    round: 1,
    scenario: null,
    players: [],
    context: '',
    apiKey: '',
    // Per-round data: rounds[roundIndex][playerIndex][hourIndex]
    rounds: {},
    // All agent tasks across rounds
    allTasks: [],
    // Standup notes per round
    standups: {},
    timerEnd: null,
  };

  // ── Persistence ──
  function saveState() {
    try {
      localStorage.setItem('metr-uplift-state', JSON.stringify(state));
    } catch (e) { /* quota */ }
  }

  function loadState() {
    try {
      const s = localStorage.getItem('metr-uplift-state');
      return s ? JSON.parse(s) : null;
    } catch { return null; }
  }

  function resetGame() {
    localStorage.removeItem('metr-uplift-state');
    location.reload();
  }

  // ── Timer ──
  let timerInterval = null;

  function startTimer(seconds, onTick, onEnd) {
    stopTimer();
    state.timerEnd = Date.now() + seconds * 1000;
    saveState();
    timerInterval = setInterval(() => {
      const remaining = Math.max(0, Math.ceil((state.timerEnd - Date.now()) / 1000));
      onTick(remaining);
      if (remaining <= 0) {
        stopTimer();
        onEnd();
      }
    }, 250);
  }

  function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;
  }

  function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${String(s).padStart(2, '0')}`;
  }

  // ── Rendering helpers ──
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  function show(id) { const el = $(id); if (el) el.classList.remove('hidden'); }
  function hide(id) { const el = $(id); if (el) el.classList.add('hidden'); }

  function renderRoundIndicator() {
    const el = $('#round-indicator');
    if (!el) return;
    const phaseLabels = { standup: 'Standup', work: '工作模拟', roundSummary: '回合总结', finalReport: '最终报告' };
    const roundNames = ['Day1上午', 'Day1下午', 'Day2上午', 'Day2下午'];
    el.innerHTML = Array.from({ length: TOTAL_ROUNDS }, (_, i) => {
      const num = i + 1;
      const active = num === state.round && state.phase !== 'finalReport';
      const done = num < state.round || state.phase === 'finalReport';
      const cls = active ? 'bg-blue-600 text-white' : done ? 'bg-green-500 text-white' : 'bg-gray-700 text-gray-400';
      return `<span class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-mono ${cls}">
        ${done ? '&#10003;' : ''} R${num} ${roundNames[i]}
      </span>`;
    }).join('') + (state.phase !== 'setup'
      ? `<span class="ml-4 text-gray-300 text-sm">${phaseLabels[state.phase] || ''}</span>`
      : '');
  }

  // ══════════════════════════════════════
  // PHASE: Setup
  // ══════════════════════════════════════
  function renderSetup() {
    const main = $('#main-content');
    main.innerHTML = `
      <div class="max-w-3xl mx-auto space-y-6">
        <div class="text-center mb-4">
          <h2 class="text-2xl font-bold text-white mb-2">METR Org-Uplift Game</h2>
          <p class="text-gray-400">模拟拥有200小时AI Agent的未来工作方式 | 基于METR 2026.03研究</p>
        </div>

        <!-- Guide Banner -->
        <div class="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4 text-sm">
          <div class="flex gap-3">
            <span class="text-blue-400 text-lg flex-shrink-0">&#9432;</span>
            <div class="text-blue-200">
              <div class="font-bold mb-1">游戏设置 — 你需要做什么？</div>
              <ol class="list-decimal list-inside space-y-1 text-blue-300/80">
                <li><strong>填写API Key</strong>（可选）— 填入BigModel Key可让AI真正执行任务；不填则用骰子模拟</li>
                <li><strong>选择场景</strong> — 点击下方卡片选一个预设场景，或选"自定义"从头配置</li>
                <li><strong>调整参与者</strong> — 修改姓名/角色/项目，对应你们团队的真实情况效果最好</li>
                <li><strong>点击「开始推演」</strong> — 进入4回合推演（模拟2天工作），每回合15分钟</li>
              </ol>
              <div class="mt-2 text-blue-400/60 text-xs">推演总流程：设置 → [Standup 5分钟 → 工作模拟 10分钟] × 4回合 → 最终报告</div>
            </div>
          </div>
        </div>

        <!-- API Key -->
        <div class="bg-gray-800 rounded-lg p-4">
          <label class="block text-sm font-medium text-gray-300 mb-2">BigModel API Key (可选，不填则使用离线模拟)</label>
          <input type="password" id="api-key-input" placeholder="输入BigModel平台API Key..." value="${state.apiKey || ''}"
            class="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none" />
          <p class="text-xs text-gray-500 mt-1">使用GLM-5模型 | API Key仅在浏览器本地使用，直接调用BigModel API</p>
        </div>

        <!-- Backend URL -->
        <div class="bg-gray-800 rounded-lg p-4">
          <label class="block text-sm font-medium text-gray-300 mb-2">CLI后端地址 (可选，运行 <code class="text-xs bg-gray-700 px-1 rounded">python uplift_cli.py serve</code> 后填入)</label>
          <input type="text" id="backend-url-input" placeholder="http://127.0.0.1:8766" value="${state.backendUrl || ''}"
            class="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none text-sm" />
          <p class="text-xs text-gray-500 mt-1">填入后Agent任务将通过Python后端执行（支持更多功能）；留空则直接在浏览器中运行</p>
        </div>

        <!-- Scenario Selection -->
        <div class="bg-gray-800 rounded-lg p-4">
          <label class="block text-sm font-medium text-gray-300 mb-3">选择场景</label>
          <div class="grid grid-cols-2 gap-3" id="scenario-cards">
            ${Object.values(Scenarios).filter(s => s && s.id).map(s => `
              <button data-scenario="${s.id}"
                class="scenario-card text-left p-4 rounded-lg border-2 transition-all
                  ${state.scenario === s.id ? 'border-blue-500 bg-gray-700' : 'border-gray-600 bg-gray-900 hover:border-gray-500'}">
                <div class="font-bold text-white">${s.name}</div>
                <div class="text-sm text-gray-400 mt-1">${s.description}</div>
                <div class="text-xs text-gray-500 mt-2">${s.players.length}名参与者</div>
              </button>
            `).join('')}
          </div>
        </div>

        <!-- Players (shown after scenario selection) -->
        <div id="players-section" class="${state.scenario ? '' : 'hidden'}">
          <div class="bg-gray-800 rounded-lg p-4">
            <div class="flex items-center justify-between mb-3">
              <label class="text-sm font-medium text-gray-300">参与者配置</label>
              <button id="add-player-btn" class="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded hover:bg-gray-600">+ 添加</button>
            </div>
            <div id="players-list" class="space-y-2"></div>
          </div>
        </div>

        <!-- Context -->
        <div id="context-section" class="${state.scenario ? '' : 'hidden'}">
          <div class="bg-gray-800 rounded-lg p-4">
            <label class="block text-sm font-medium text-gray-300 mb-2">场景上下文</label>
            <textarea id="context-input" rows="3" placeholder="描述当前项目背景和目标..."
              class="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none text-sm"
            >${state.context || ''}</textarea>
          </div>
        </div>

        <!-- AI Parameters -->
        <div id="params-section" class="${state.scenario ? '' : 'hidden'}">
          <div class="bg-gray-800 rounded-lg p-4">
            <label class="block text-sm font-medium text-gray-300 mb-3">AI Agent 能力参数</label>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="text-xs text-gray-400">时间窗口 (小时)</label>
                <input type="number" id="param-horizon" value="${state.aiParams?.timeHorizon || 200}"
                  class="w-full bg-gray-900 border border-gray-600 rounded px-3 py-1.5 text-white text-sm mt-1" />
              </div>
              <div>
                <label class="text-xs text-gray-400">速度倍数</label>
                <input type="number" id="param-speed" value="${state.aiParams?.speedMultiplier || 2}" step="0.5"
                  class="w-full bg-gray-900 border border-gray-600 rounded px-3 py-1.5 text-white text-sm mt-1" />
              </div>
            </div>
            <div class="mt-3 p-3 bg-gray-900 rounded text-xs text-gray-400 font-mono">
              成功率: <=40h → 80% | <=200h → 50% | >200h → 10%
            </div>
          </div>
        </div>

        <!-- Start Buttons -->
        <div class="text-center space-y-3">
          <div>
            <button id="start-game-btn" class="px-8 py-3 bg-blue-600 text-white rounded-lg font-bold text-lg hover:bg-blue-500 transition disabled:opacity-40 disabled:cursor-not-allowed"
              ${state.scenario ? '' : 'disabled'}>
              开始推演
            </button>
            ${localStorage.getItem('metr-uplift-state') ? '<button id="resume-btn" class="ml-4 px-4 py-3 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600">恢复上次</button>' : ''}
          </div>
          <div>
            <button id="auto-sim-btn" class="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:from-purple-500 hover:to-pink-500 transition disabled:opacity-40 disabled:cursor-not-allowed text-sm"
              ${state.scenario && state.scenario !== 'custom' ? '' : 'disabled'}>
              &#9889; 一键模拟 — 自动完成全部4回合
            </button>
            <p class="text-xs text-gray-500 mt-1">自动生成所有内容并运行完整推演流程，适合演示和快速体验</p>
          </div>
        </div>
      </div>
    `;

    // Event bindings
    $$('.scenario-card').forEach(card => {
      card.addEventListener('click', () => {
        const id = card.dataset.scenario;
        state.scenario = id;
        const sc = Scenarios[id];
        state.players = JSON.parse(JSON.stringify(sc.players));
        state.context = sc.context;
        state.aiParams = { ...sc.aiParams };
        renderSetup();
      });
    });

    renderPlayersList();

    $('#add-player-btn')?.addEventListener('click', () => {
      const colors = ['#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#6366F1'];
      state.players.push({
        name: `玩家${state.players.length + 1}`,
        role: '角色',
        project: '项目描述',
        color: colors[state.players.length % colors.length],
      });
      renderPlayersList();
    });

    $('#auto-sim-btn')?.addEventListener('click', () => {
      state.apiKey = $('#api-key-input')?.value || '';
      state.context = $('#context-input')?.value || '';
      state.backendUrl = $('#backend-url-input')?.value || '';
      const horizon = parseInt($('#param-horizon')?.value) || 200;
      const speed = parseFloat($('#param-speed')?.value) || 2;
      Engine.configure(state.apiKey, { timeHorizon: horizon, speedMultiplier: speed }, state.backendUrl);
      state.phase = 'autoSim';
      state.round = 1;
      state.rounds = {};
      state.allTasks = [];
      state.standups = {};
      saveState();
      runAutoSimulation();
    });

    $('#start-game-btn')?.addEventListener('click', () => {
      state.apiKey = $('#api-key-input')?.value || '';
      state.context = $('#context-input')?.value || '';
      state.backendUrl = $('#backend-url-input')?.value || '';
      const horizon = parseInt($('#param-horizon')?.value) || 200;
      const speed = parseFloat($('#param-speed')?.value) || 2;
      Engine.configure(state.apiKey, { timeHorizon: horizon, speedMultiplier: speed }, state.backendUrl);
      state.phase = 'standup';
      state.round = 1;
      state.rounds = {};
      state.allTasks = [];
      state.standups = {};
      saveState();
      render();
    });

    $('#resume-btn')?.addEventListener('click', () => {
      Engine.configure(state.apiKey, state.aiParams || {}, state.backendUrl || '');
      render();
    });
  }

  function renderPlayersList() {
    const container = $('#players-list');
    if (!container) return;
    container.innerHTML = state.players.map((p, i) => `
      <div class="flex items-center gap-2 bg-gray-900 rounded p-2">
        <span class="w-3 h-3 rounded-full flex-shrink-0" style="background:${p.color}"></span>
        <input value="${p.name}" data-idx="${i}" data-field="name" placeholder="姓名"
          class="player-input bg-transparent border-b border-gray-700 text-white text-sm px-1 py-0.5 w-20 focus:border-blue-500 focus:outline-none" />
        <input value="${p.role}" data-idx="${i}" data-field="role" placeholder="角色"
          class="player-input bg-transparent border-b border-gray-700 text-gray-300 text-sm px-1 py-0.5 w-24 focus:border-blue-500 focus:outline-none" />
        <input value="${p.project}" data-idx="${i}" data-field="project" placeholder="当前项目"
          class="player-input bg-transparent border-b border-gray-700 text-gray-400 text-sm px-1 py-0.5 flex-1 focus:border-blue-500 focus:outline-none" />
        ${state.players.length > 1 ? `<button data-remove="${i}" class="remove-player text-gray-600 hover:text-red-400 text-xs px-1">x</button>` : ''}
      </div>
    `).join('');

    container.querySelectorAll('.player-input').forEach(inp => {
      inp.addEventListener('change', () => {
        state.players[inp.dataset.idx][inp.dataset.field] = inp.value;
      });
    });
    container.querySelectorAll('.remove-player').forEach(btn => {
      btn.addEventListener('click', () => {
        state.players.splice(parseInt(btn.dataset.remove), 1);
        renderPlayersList();
      });
    });
  }

  // ══════════════════════════════════════
  // AUTO SIMULATION
  // ══════════════════════════════════════
  async function runAutoSimulation() {
    const script = Scenarios._simScripts?.[state.scenario];
    if (!script) {
      alert('当前场景暂无模拟脚本，请选择 NewCo客服产品 场景');
      state.phase = 'setup';
      render();
      return;
    }

    const main = $('#main-content');
    const roundNames = ['Day1 上午', 'Day1 下午', 'Day2 上午', 'Day2 下午'];
    let simLog = [];

    function renderSimUI(currentRound, currentStep, stepDetail, progress) {
      main.innerHTML = `
        <div class="max-w-3xl mx-auto">
          <div class="text-center mb-6">
            <h2 class="text-2xl font-bold text-white mb-2">&#9889; 自动模拟运行中</h2>
            <p class="text-gray-400">正在自动生成内容并完成全部4回合推演</p>
          </div>

          <!-- Progress bar -->
          <div class="mb-6">
            <div class="flex justify-between text-sm text-gray-400 mb-2">
              <span>回合 ${currentRound} / ${TOTAL_ROUNDS} — ${roundNames[currentRound - 1]}</span>
              <span>${Math.round(progress)}%</span>
            </div>
            <div class="w-full bg-gray-800 rounded-full h-3">
              <div class="bg-gradient-to-r from-purple-500 to-pink-500 rounded-full h-3 transition-all duration-500" style="width:${progress}%"></div>
            </div>
          </div>

          <!-- Current step -->
          <div class="bg-gray-800 rounded-lg p-4 mb-4">
            <div class="flex items-center gap-3 mb-2">
              <span class="animate-spin text-purple-400">&#9696;</span>
              <span class="text-white font-bold">${currentStep}</span>
            </div>
            <div class="text-sm text-gray-400">${stepDetail}</div>
          </div>

          <!-- Live log -->
          <div class="bg-gray-900 rounded-lg p-4 max-h-80 overflow-y-auto font-mono text-xs" id="sim-log">
            ${simLog.map(l => `<div class="${l.type === 'success' ? 'text-green-400' : l.type === 'info' ? 'text-blue-400' : l.type === 'warn' ? 'text-yellow-400' : 'text-gray-500'}">${l.time} ${l.msg}</div>`).join('')}
          </div>

          <!-- Round indicators -->
          <div class="flex justify-center gap-3 mt-6">
            ${Array.from({ length: TOTAL_ROUNDS }, (_, i) => {
              const done = i + 1 < currentRound;
              const active = i + 1 === currentRound;
              const cls = done ? 'bg-green-500 text-white' : active ? 'bg-purple-500 text-white animate-pulse' : 'bg-gray-700 text-gray-500';
              return `<span class="px-4 py-2 rounded-full text-sm font-mono ${cls}">${done ? '&#10003; ' : ''}R${i + 1}</span>`;
            }).join('')}
          </div>
        </div>
      `;
      // Auto-scroll log
      const logEl = document.getElementById('sim-log');
      if (logEl) logEl.scrollTop = logEl.scrollHeight;
    }

    let simClock = { day: 1, hour: 9 };
    function setSimClock(round, hourOffset = 0) {
      const day = round <= 2 ? 1 : 2;
      const startHour = round % 2 === 1 ? 9 : 14;
      simClock = { day, hour: startHour + hourOffset };
    }
    function fmtSimTime() {
      const hh = String(simClock.hour).padStart(2, '0');
      return `[D${simClock.day} ${hh}:00]`;
    }
    function log(msg, type = 'info') {
      simLog.push({ time: fmtSimTime(), msg, type });
    }

    function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

    // ── Run all 4 rounds ──
    for (let round = 1; round <= TOTAL_ROUNDS; round++) {
      state.round = round;
      const rKey = `r${round}`;
      const rIdx = round - 1;
      const baseProgress = ((round - 1) / TOTAL_ROUNDS) * 100;

      // ── Standup phase ──
      setSimClock(round, 0);
      renderSimUI(round, `Standup — ${roundNames[rIdx]}`, '填写各玩家的进展汇报...', baseProgress);
      log(`── 回合 ${round} (${roundNames[rIdx]}) 开始 ──`, 'info');
      await delay(400);

      state.standups[rKey] = state.players.map((p, pi) => {
        const s = script.standups[rIdx]?.[pi] || { done: '', plan: '继续推进项目', blockers: '' };
        log(`${p.name}: 计划「${s.plan.slice(0, 40)}...」`, 'info');
        return s;
      });
      await delay(300);

      // ── Work phase ──
      state.rounds[rKey] = state.players.map(() =>
        Array.from({ length: HOURS_PER_ROUND }, () => ({ playerAction: '', agentTask: '', agentResult: null }))
      );

      for (let pi = 0; pi < state.players.length; pi++) {
        const player = state.players[pi];
        for (let h = 0; h < HOURS_PER_ROUND; h++) {
          const actionData = script.actions[rIdx]?.[pi]?.[h];
          if (!actionData) continue;

          setSimClock(round, h);
          const stepProgress = baseProgress + ((pi * HOURS_PER_ROUND + h) / (state.players.length * HOURS_PER_ROUND)) * (100 / TOTAL_ROUNDS);
          state.rounds[rKey][pi][h].playerAction = actionData.playerAction;

          if (actionData.agentTask) {
            renderSimUI(round, `${player.name} — Hour ${h + 1}`, `Agent任务: ${actionData.agentTask.slice(0, 60)}...`, stepProgress);
            log(`${player.name} [H${h + 1}]: ${actionData.playerAction}`, 'info');
            log(`  → Agent: ${actionData.agentTask.slice(0, 50)}...`, 'warn');

            const result = await Engine.executeTask(
              actionData.agentTask,
              state.context + '\n当前项目: ' + player.project,
              player.name,
              state.context,
            );

            state.rounds[rKey][pi][h].agentTask = actionData.agentTask;
            state.rounds[rKey][pi][h].agentResult = result;
            state.allTasks.push({ ...result, player: pi, round, hour: h, task: actionData.agentTask });

            const icon = result.dice.success ? '&#10003;' : '&#10007;';
            const status = result.dice.success ? 'success' : 'warn';
            log(`  ← ${result.dice.success ? '成功' : '失败'} (${result.dice.roll}/${result.dice.threshold}) ${result.estimatedHours}h — ${(result.deliverable || '').slice(0, 40)}`, status);
            await delay(200);
          } else {
            log(`${player.name} [H${h + 1}]: ${actionData.playerAction}`, 'info');
          }
        }
      }

      setSimClock(round, HOURS_PER_ROUND - 1);
      log(`回合 ${round} 完成 ✓`, 'success');
      saveState();
      await delay(300);
    }

    // ── Done → Final Report ──
    log('', 'info');
    log('══ 全部4回合模拟完成 ══', 'success');
    renderSimUI(TOTAL_ROUNDS, '模拟完成!', '正在生成最终报告...', 100);
    await delay(800);

    state.phase = 'finalReport';
    saveState();
    render();
  }

  // ══════════════════════════════════════
  // PHASE: Standup
  // ══════════════════════════════════════
  function renderStandup() {
    const roundNames = ['Day1 上午', 'Day1 下午', 'Day2 上午', 'Day2 下午'];
    const rKey = `r${state.round}`;
    if (!state.standups[rKey]) {
      state.standups[rKey] = state.players.map(() => ({ done: '', plan: '', blockers: '' }));
    }

    const main = $('#main-content');
    main.innerHTML = `
      <div class="max-w-4xl mx-auto">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-white">Standup | 回合${state.round} - ${roundNames[state.round - 1]}</h2>
          <div class="flex items-center gap-4">
            <span id="timer" class="text-2xl font-mono text-yellow-400"></span>
            <button id="skip-standup" class="text-sm px-3 py-1 bg-gray-700 text-gray-300 rounded hover:bg-gray-600">跳过 &rarr;</button>
          </div>
        </div>

        <!-- Guide Banner -->
        <div class="bg-yellow-900/20 border border-yellow-700/40 rounded-lg p-3 mb-4 text-sm">
          <div class="flex gap-3">
            <span class="text-yellow-400 text-lg flex-shrink-0">&#9201;</span>
            <div class="text-yellow-200/90">
              <div class="font-bold mb-1">Standup（5分钟）— 像真实晨会一样快速同步</div>
              <div class="text-yellow-300/60 space-y-0.5">
                <div>每位参与者花1-2分钟填写三栏：<strong>上回合完成了什么</strong> / <strong>这回合计划做什么</strong> / <strong>有什么阻塞</strong></div>
                <div>关键思考：你打算让AI Agent帮你做哪些事？哪些事必须你自己做？</div>
                <div class="text-xs mt-1">&#10148; 填完后点击「开始工作模拟」进入下一阶段${state.round === 1 ? '（第一回合"完成了什么"可以留空）' : ''}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="grid gap-4">
          ${state.players.map((p, i) => `
            <div class="bg-gray-800 rounded-lg p-4 border-l-4" style="border-color:${p.color}">
              <div class="flex items-center gap-2 mb-3">
                <span class="font-bold text-white">${p.name}</span>
                <span class="text-xs text-gray-400 bg-gray-700 px-2 py-0.5 rounded">${p.role}</span>
                <span class="text-xs text-gray-500">${p.project}</span>
              </div>
              <div class="grid grid-cols-3 gap-3">
                <div>
                  <label class="text-xs text-gray-400 block mb-1">上回合完成了什么</label>
                  <textarea data-player="${i}" data-field="done" rows="2" placeholder="${state.round === 1 ? '（第一回合，无）' : '...'}"
                    class="standup-input w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
                  >${state.standups[rKey][i].done}</textarea>
                </div>
                <div>
                  <label class="text-xs text-gray-400 block mb-1">这回合计划做什么</label>
                  <textarea data-player="${i}" data-field="plan" rows="2" placeholder="本回合目标..."
                    class="standup-input w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
                  >${state.standups[rKey][i].plan}</textarea>
                </div>
                <div>
                  <label class="text-xs text-gray-400 block mb-1">阻塞/依赖</label>
                  <textarea data-player="${i}" data-field="blockers" rows="2" placeholder="需要什么帮助..."
                    class="standup-input w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
                  >${state.standups[rKey][i].blockers}</textarea>
                </div>
              </div>
            </div>
          `).join('')}
        </div>

        <div class="text-center mt-6">
          <button id="start-work" class="px-8 py-3 bg-green-600 text-white rounded-lg font-bold hover:bg-green-500 transition">
            开始工作模拟 &rarr;
          </button>
        </div>
      </div>
    `;

    // Save standup inputs on change
    main.querySelectorAll('.standup-input').forEach(ta => {
      ta.addEventListener('input', () => {
        state.standups[rKey][ta.dataset.player][ta.dataset.field] = ta.value;
        saveState();
      });
    });

    // Timer
    const timerEl = $('#timer');
    startTimer(STANDUP_SECONDS,
      (remaining) => { timerEl.textContent = formatTime(remaining); },
      () => { timerEl.textContent = '00:00'; timerEl.classList.add('text-red-400'); }
    );

    $('#skip-standup').addEventListener('click', goToWork);
    $('#start-work').addEventListener('click', goToWork);
  }

  function goToWork() {
    stopTimer();
    state.phase = 'work';
    saveState();
    render();
  }

  // ══════════════════════════════════════
  // PHASE: Work Simulation
  // ══════════════════════════════════════
  function renderWork() {
    const roundNames = ['Day1 上午', 'Day1 下午', 'Day2 上午', 'Day2 下午'];
    const rKey = `r${state.round}`;
    if (!state.rounds[rKey]) {
      state.rounds[rKey] = state.players.map(() =>
        Array.from({ length: HOURS_PER_ROUND }, () => ({
          playerAction: '',
          agentTask: '',
          agentResult: null,
        }))
      );
    }

    const main = $('#main-content');
    main.innerHTML = `
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-white">工作模拟 | 回合${state.round} - ${roundNames[state.round - 1]}</h2>
        <div class="flex items-center gap-4">
          <span id="timer" class="text-2xl font-mono text-yellow-400"></span>
          <button id="end-round" class="text-sm px-3 py-1 bg-orange-600 text-white rounded hover:bg-orange-500">结束回合</button>
        </div>
      </div>

      <!-- Guide Banner -->
      <div class="bg-green-900/20 border border-green-700/40 rounded-lg p-3 mb-4 text-sm">
        <div class="flex gap-3">
          <span class="text-green-400 text-lg flex-shrink-0">&#9881;</span>
          <div class="text-green-200/90">
            <div class="font-bold mb-1">工作模拟（10分钟）— 模拟半天的工作</div>
            <div class="text-green-300/60 space-y-0.5">
              <div><strong>Step 1:</strong> 点击玩家标签切换到你的视角</div>
              <div><strong>Step 2:</strong> 在每个小时格子里填写「你自己在做什么」（如：评审Agent产出、参加会议、做决策）</div>
              <div><strong>Step 3:</strong> 在下方Agent面板输入要交给AI的任务，选择对应小时，点击「执行」</div>
              <div><strong>Step 4:</strong> 查看Agent执行结果 — 绿色=成功，红色=失败（基于任务难度的骰子判定）</div>
              <div class="text-xs mt-1">&#10148; 思考：你是在<em>执行</em>还是在<em>管理Agent</em>？这就是METR发现的核心转变 | 完成后点击右上角「结束回合」</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Player tabs -->
      <div class="flex gap-2 mb-4 border-b border-gray-700 pb-2" id="player-tabs">
        ${state.players.map((p, i) => `
          <button data-tab="${i}" class="player-tab px-4 py-2 rounded-t text-sm font-medium transition
            ${i === 0 ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white'}">
            <span class="inline-block w-2 h-2 rounded-full mr-1" style="background:${p.color}"></span>
            ${p.name}
          </button>
        `).join('')}
      </div>

      <!-- Hourly grid (for active player) -->
      <div id="work-grid"></div>

      <!-- Agent execution panel -->
      <div class="mt-4 bg-gray-800 rounded-lg p-4" id="agent-panel">
        <h3 class="text-sm font-bold text-gray-300 mb-3">Agent 执行面板</h3>
        <div class="flex gap-3">
          <input id="agent-task-input" placeholder="输入Agent指令（例如：调研AI客服竞品的技术架构）"
            class="flex-1 bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none" />
          <select id="agent-hour-select" class="bg-gray-900 border border-gray-600 rounded px-2 text-white text-sm">
            ${Array.from({ length: HOURS_PER_ROUND }, (_, h) => `<option value="${h}">Hour ${h + 1}</option>`).join('')}
          </select>
          <button id="run-agent" class="px-4 py-2 bg-purple-600 text-white rounded font-medium hover:bg-purple-500 transition flex items-center gap-2">
            <span id="agent-spinner" class="hidden animate-spin">&#9696;</span>
            执行
          </button>
        </div>
        <div id="agent-result" class="mt-3 hidden"></div>
      </div>

      <!-- Round stats sidebar -->
      <div class="mt-4 grid grid-cols-4 gap-3" id="round-stats">
        <div class="bg-gray-800 rounded p-3 text-center">
          <div class="text-2xl font-bold text-blue-400" id="stat-tasks">0</div>
          <div class="text-xs text-gray-400">Agent任务</div>
        </div>
        <div class="bg-gray-800 rounded p-3 text-center">
          <div class="text-2xl font-bold text-green-400" id="stat-success">0%</div>
          <div class="text-xs text-gray-400">成功率</div>
        </div>
        <div class="bg-gray-800 rounded p-3 text-center">
          <div class="text-2xl font-bold text-yellow-400" id="stat-hours">0h</div>
          <div class="text-xs text-gray-400">Agent工时</div>
        </div>
        <div class="bg-gray-800 rounded p-3 text-center">
          <div class="text-2xl font-bold text-purple-400" id="stat-bottleneck">-</div>
          <div class="text-xs text-gray-400">主要瓶颈</div>
        </div>
      </div>
    `;

    let activePlayer = 0;

    function renderGrid() {
      const grid = $('#work-grid');
      const data = state.rounds[rKey][activePlayer];
      grid.innerHTML = `
        <div class="grid grid-cols-5 gap-2">
          ${data.map((cell, h) => `
            <div class="bg-gray-800 rounded-lg p-3 ${cell.agentResult ? 'ring-1 ring-gray-600' : ''}">
              <div class="text-xs text-gray-500 mb-2 font-mono">Hour ${h + 1}</div>
              <textarea data-hour="${h}" placeholder="你在做什么..."
                class="action-input w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-white h-16 resize-none focus:border-blue-500 focus:outline-none"
              >${cell.playerAction}</textarea>
              ${cell.agentResult ? `
                <div class="mt-2 p-2 rounded text-xs ${cell.agentResult.dice?.success ? 'bg-green-900/30 border border-green-800' : 'bg-red-900/30 border border-red-800'}">
                  <div class="flex items-center justify-between mb-1">
                    <span class="font-bold ${cell.agentResult.dice?.success ? 'text-green-400' : 'text-red-400'}">
                      ${cell.agentResult.dice?.success ? '&#10003; 成功' : '&#10007; 失败'}
                    </span>
                    <span class="text-gray-400">${cell.agentResult.dice?.roll}/${cell.agentResult.dice?.threshold}</span>
                  </div>
                  <div class="text-gray-300 truncate" title="${cell.agentResult.deliverable || ''}">${cell.agentResult.deliverable || ''}</div>
                  <div class="text-gray-500 mt-1">${cell.agentResult.estimatedHours || 0}h | ${cell.agentResult.confidence || '-'}</div>
                </div>
              ` : `
                <div class="mt-2 text-xs text-gray-600 italic">无Agent任务</div>
              `}
            </div>
          `).join('')}
        </div>
      `;

      grid.querySelectorAll('.action-input').forEach(ta => {
        ta.addEventListener('input', () => {
          state.rounds[rKey][activePlayer][parseInt(ta.dataset.hour)].playerAction = ta.value;
          saveState();
        });
      });
    }

    // Player tab switching
    $$('.player-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        activePlayer = parseInt(tab.dataset.tab);
        $$('.player-tab').forEach(t => t.classList.remove('bg-gray-800', 'text-white'));
        $$('.player-tab').forEach(t => t.classList.add('text-gray-400'));
        tab.classList.add('bg-gray-800', 'text-white');
        tab.classList.remove('text-gray-400');
        renderGrid();
      });
    });

    // Agent execution
    $('#run-agent').addEventListener('click', async () => {
      const task = $('#agent-task-input').value.trim();
      if (!task) return;
      const hour = parseInt($('#agent-hour-select').value);
      const spinner = $('#agent-spinner');
      const resultEl = $('#agent-result');

      spinner.classList.remove('hidden');
      $('#run-agent').disabled = true;
      resultEl.classList.remove('hidden');
      resultEl.innerHTML = '<div class="text-gray-400 text-sm animate-pulse">Agent正在执行任务...</div>';

      const result = await Engine.executeTask(
        task,
        state.context + '\n当前项目: ' + state.players[activePlayer].project,
        state.players[activePlayer].name,
        state.context,
      );

      spinner.classList.add('hidden');
      $('#run-agent').disabled = false;

      // Save result
      state.rounds[rKey][activePlayer][hour].agentTask = task;
      state.rounds[rKey][activePlayer][hour].agentResult = result;
      state.allTasks.push({ ...result, player: activePlayer, round: state.round, hour, task });
      saveState();

      // Show result
      resultEl.innerHTML = `
        <div class="p-3 rounded ${result.dice.success ? 'bg-green-900/20 border border-green-800' : 'bg-red-900/20 border border-red-800'}">
          <div class="flex items-center gap-3 mb-2">
            <span class="text-lg font-bold ${result.dice.success ? 'text-green-400' : 'text-red-400'}">
              ${result.dice.success ? '&#10003; 执行成功' : '&#10007; 执行失败'}
            </span>
            <span class="text-sm text-gray-400">骰子: ${result.dice.roll} / 阈值: ${result.dice.threshold} (成功率${result.successRate}%)</span>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div class="text-gray-400 text-xs mb-1">执行步骤</div>
              <ol class="list-decimal list-inside text-gray-300 space-y-1">
                ${(result.steps || []).map(s => `<li>${s}</li>`).join('')}
              </ol>
            </div>
            <div>
              <div class="text-gray-400 text-xs mb-1">产出物</div>
              <div class="text-white">${result.deliverable || '-'}</div>
              <div class="mt-2 text-gray-400 text-xs">耗时: ${result.estimatedHours}h | 信心: ${result.confidence}</div>
              ${(result.blockers || []).length ? `
                <div class="mt-2 text-gray-400 text-xs">阻塞项:</div>
                <ul class="text-yellow-400 text-xs">${result.blockers.map(b => `<li>- ${b}</li>`).join('')}</ul>
              ` : ''}
              <div class="mt-1 text-xs text-gray-500">瓶颈: ${(result.bottlenecks || []).map(b => Engine.BOTTLENECK_LABELS[b] || b).join(', ')}</div>
            </div>
          </div>
        </div>
      `;

      renderGrid();
      updateRoundStats();
      $('#agent-task-input').value = '';
    });

    // Timer
    const timerEl = $('#timer');
    startTimer(WORK_SECONDS,
      (remaining) => { timerEl.textContent = formatTime(remaining); },
      () => { timerEl.textContent = '00:00'; timerEl.classList.add('text-red-400'); }
    );

    $('#end-round').addEventListener('click', endRound);

    renderGrid();
    updateRoundStats();
  }

  async function updateRoundStats() {
    const roundTasks = state.allTasks.filter(t => t.round === state.round);
    const stats = await Engine.computeStats(roundTasks);
    const el = (id, val) => { const e = $(id); if (e) e.textContent = val; };
    el('#stat-tasks', stats.totalTasks);
    el('#stat-success', stats.totalTasks ? stats.successRate + '%' : '-');
    el('#stat-hours', stats.totalAgentHours + 'h');
    const topBottleneck = Object.entries(stats.bottleneckCounts)
      .filter(([k]) => k !== 'none')
      .sort((a, b) => b[1] - a[1])[0];
    el('#stat-bottleneck', topBottleneck ? Engine.BOTTLENECK_LABELS[topBottleneck[0]] || topBottleneck[0] : '-');
  }

  function endRound() {
    stopTimer();
    if (state.round >= TOTAL_ROUNDS) {
      state.phase = 'finalReport';
    } else {
      state.phase = 'roundSummary';
    }
    saveState();
    render();
  }

  // ══════════════════════════════════════
  // PHASE: Round Summary
  // ══════════════════════════════════════
  async function renderRoundSummary() {
    const roundTasks = state.allTasks.filter(t => t.round === state.round);
    const stats = await Engine.computeStats(roundTasks);

    const main = $('#main-content');
    main.innerHTML = `
      <div class="max-w-3xl mx-auto">
        <h2 class="text-xl font-bold text-white mb-4">回合 ${state.round} 总结</h2>

        <!-- Guide Banner -->
        <div class="bg-purple-900/20 border border-purple-700/40 rounded-lg p-3 mb-4 text-sm">
          <div class="flex gap-3">
            <span class="text-purple-400 text-lg flex-shrink-0">&#128202;</span>
            <div class="text-purple-200/90">
              <div class="font-bold mb-1">回合复盘 — 观察数据，思考瓶颈</div>
              <div class="text-purple-300/60 space-y-0.5">
                <div>查看本回合的Agent任务成功率、工时消耗和瓶颈分布</div>
                <div>讨论：哪些任务适合交给Agent？哪些任务因为等人类反馈而被阻塞了？</div>
                <div class="text-xs mt-1">&#10148; 反思完毕后点击「进入回合 ${state.round + 1}」继续推演（共4回合）</div>
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4 mb-6">
          <div class="bg-gray-800 rounded-lg p-4 text-center">
            <div class="text-3xl font-bold text-blue-400">${stats.totalTasks}</div>
            <div class="text-sm text-gray-400 mt-1">Agent任务总数</div>
          </div>
          <div class="bg-gray-800 rounded-lg p-4 text-center">
            <div class="text-3xl font-bold text-green-400">${stats.successRate}%</div>
            <div class="text-sm text-gray-400 mt-1">成功率</div>
          </div>
          <div class="bg-gray-800 rounded-lg p-4 text-center">
            <div class="text-3xl font-bold text-purple-400">${stats.totalAgentHours}h</div>
            <div class="text-sm text-gray-400 mt-1">Agent等效工时</div>
          </div>
        </div>

        ${roundTasks.length ? `
          <div class="bg-gray-800 rounded-lg p-4 mb-4">
            <h3 class="text-sm font-bold text-gray-300 mb-2">任务明细</h3>
            <div class="space-y-2">
              ${roundTasks.map(t => `
                <div class="flex items-center gap-2 text-sm">
                  <span class="${t.dice?.success ? 'text-green-400' : 'text-red-400'}">${t.dice?.success ? '&#10003;' : '&#10007;'}</span>
                  <span class="text-white flex-1 truncate">${t.task}</span>
                  <span class="text-gray-400">${state.players[t.player]?.name}</span>
                  <span class="text-gray-500">${t.estimatedHours}h</span>
                </div>
              `).join('')}
            </div>
          </div>
        ` : '<div class="text-gray-500 text-center py-8">本回合没有执行Agent任务</div>'}

        ${Object.keys(stats.bottleneckCounts).filter(k => k !== 'none').length ? `
          <div class="bg-gray-800 rounded-lg p-4 mb-4">
            <h3 class="text-sm font-bold text-gray-300 mb-2">瓶颈分布</h3>
            ${Object.entries(stats.bottleneckCounts).filter(([k]) => k !== 'none').map(([k, v]) => `
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm text-gray-300 w-28">${Engine.BOTTLENECK_LABELS[k] || k}</span>
                <div class="flex-1 bg-gray-900 rounded-full h-4">
                  <div class="bg-yellow-500 rounded-full h-4" style="width:${Math.min(100, v / stats.totalTasks * 100)}%"></div>
                </div>
                <span class="text-xs text-gray-400 w-8">${v}</span>
              </div>
            `).join('')}
          </div>
        ` : ''}

        <div class="text-center mt-6">
          <button id="next-round" class="px-8 py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-500 transition">
            进入回合 ${state.round + 1} &rarr;
          </button>
        </div>
      </div>
    `;

    $('#next-round').addEventListener('click', () => {
      state.round++;
      state.phase = 'standup';
      saveState();
      render();
    });
  }

  // ══════════════════════════════════════
  // PHASE: Final Report
  // ══════════════════════════════════════
  async function renderFinalReport() {
    const stats = await Engine.computeStats(state.allTasks);
    const bottleneckEntries = Object.entries(stats.bottleneckCounts)
      .filter(([k]) => k !== 'none')
      .sort((a, b) => b[1] - a[1]);

    // Per-player stats
    const playerStats = await Promise.all(state.players.map(async (p, i) => {
      const tasks = state.allTasks.filter(t => t.player === i);
      const s = await Engine.computeStats(tasks);
      return { ...p, ...s, taskCount: tasks.length };
    }));

    const main = $('#main-content');
    main.innerHTML = `
      <div class="max-w-4xl mx-auto">
        <div class="text-center mb-4">
          <h2 class="text-2xl font-bold text-white mb-2">推演最终报告</h2>
          <p class="text-gray-400">模拟2天 | ${state.players.length}名参与者 | AI时间窗口${Engine.params.timeHorizon}h</p>
        </div>

        <!-- Guide Banner -->
        <div class="bg-emerald-900/20 border border-emerald-700/40 rounded-lg p-3 mb-6 text-sm">
          <div class="flex gap-3">
            <span class="text-emerald-400 text-lg flex-shrink-0">&#127942;</span>
            <div class="text-emerald-200/90">
              <div class="font-bold mb-1">推演完成 — 现在做什么？</div>
              <div class="text-emerald-300/60 space-y-0.5">
                <div><strong>1. 看生产力倍增</strong> — 左上角的数字是你们2天完成的工作量相当于正常多少天，METR的基准是3-5x</div>
                <div><strong>2. 看瓶颈分布</strong> — 哪类瓶颈最多？这就是你们组织引入AI后最需要优化的流程</div>
                <div><strong>3. 对照METR洞察</strong> — 底部5条洞察，讨论哪些在你们推演中得到了验证</div>
                <div><strong>4. 带走行动项</strong> — 点击「导出JSON」保存完整数据，作为AI采用的ROI论据</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Headline metrics -->
        <div class="grid grid-cols-4 gap-4 mb-6">
          <div class="bg-gradient-to-br from-blue-900/50 to-blue-800/30 rounded-lg p-5 text-center border border-blue-700/50">
            <div class="text-4xl font-bold text-blue-300">${stats.productivityMultiplier}x</div>
            <div class="text-sm text-blue-400 mt-1">生产力倍增</div>
            <div class="text-xs text-gray-500 mt-1">METR预估: 3-5x</div>
          </div>
          <div class="bg-gradient-to-br from-green-900/50 to-green-800/30 rounded-lg p-5 text-center border border-green-700/50">
            <div class="text-4xl font-bold text-green-300">${stats.totalTasks}</div>
            <div class="text-sm text-green-400 mt-1">Agent任务总量</div>
          </div>
          <div class="bg-gradient-to-br from-purple-900/50 to-purple-800/30 rounded-lg p-5 text-center border border-purple-700/50">
            <div class="text-4xl font-bold text-purple-300">${stats.totalAgentHours}h</div>
            <div class="text-sm text-purple-400 mt-1">Agent等效工时</div>
          </div>
          <div class="bg-gradient-to-br from-yellow-900/50 to-yellow-800/30 rounded-lg p-5 text-center border border-yellow-700/50">
            <div class="text-4xl font-bold text-yellow-300">${stats.successRate}%</div>
            <div class="text-sm text-yellow-400 mt-1">整体成功率</div>
          </div>
        </div>

        <!-- Per-player breakdown -->
        <div class="bg-gray-800 rounded-lg p-4 mb-4">
          <h3 class="text-sm font-bold text-gray-300 mb-3">参与者表现</h3>
          <div class="space-y-3">
            ${playerStats.map(p => `
              <div class="flex items-center gap-3">
                <span class="w-3 h-3 rounded-full flex-shrink-0" style="background:${p.color}"></span>
                <span class="text-white w-20">${p.name}</span>
                <span class="text-gray-400 text-sm w-24">${p.role}</span>
                <div class="flex-1 flex items-center gap-2">
                  <span class="text-sm text-blue-400">${p.taskCount}任务</span>
                  <span class="text-sm text-green-400">${p.successRate}%成功</span>
                  <span class="text-sm text-purple-400">${p.totalAgentHours}h工时</span>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Bottleneck analysis -->
        <div class="bg-gray-800 rounded-lg p-4 mb-4">
          <h3 class="text-sm font-bold text-gray-300 mb-3">瓶颈分析 (METR核心发现)</h3>
          <p class="text-xs text-gray-400 mb-3">METR发现：AI Agent时代的瓶颈从"执行"转移到"决策/反馈/协调"，瓶颈-工作比可达 >100:1</p>
          ${bottleneckEntries.length ? `
            <div class="space-y-2">
              ${bottleneckEntries.map(([k, v]) => {
                const pct = Math.round(v / stats.totalTasks * 100);
                return `
                  <div class="flex items-center gap-3">
                    <span class="text-sm text-gray-300 w-28">${Engine.BOTTLENECK_LABELS[k] || k}</span>
                    <div class="flex-1 bg-gray-900 rounded-full h-5 relative">
                      <div class="bg-gradient-to-r from-yellow-600 to-orange-500 rounded-full h-5 transition-all" style="width:${Math.max(8, pct)}%"></div>
                      <span class="absolute inset-0 flex items-center justify-center text-xs text-white font-mono">${pct}%</span>
                    </div>
                    <span class="text-xs text-gray-400 w-8">${v}次</span>
                  </div>`;
              }).join('')}
            </div>
          ` : '<div class="text-gray-500 text-sm">未检测到明显瓶颈</div>'}
        </div>

        <!-- Key insights from METR -->
        <div class="bg-gray-800 rounded-lg p-4 mb-4">
          <h3 class="text-sm font-bold text-gray-300 mb-3">METR核心洞察对照</h3>
          <div class="space-y-2 text-sm">
            <div class="flex gap-2"><span class="text-yellow-400">1.</span><span class="text-gray-300">"没有时间在实施前发展想法" — Agent收到指令后立即执行，MVP从天级变为小时级</span></div>
            <div class="flex gap-2"><span class="text-yellow-400">2.</span><span class="text-gray-300">"夜间喂饱Agent" — 下班前安排长时间运行的任务，第二天收获结果</span></div>
            <div class="flex gap-2"><span class="text-yellow-400">3.</span><span class="text-gray-300">"优先级和组织成为关键瓶颈" — 你的时间从"执行"转向"决策+写规格+审查产出"</span></div>
            <div class="flex gap-2"><span class="text-yellow-400">4.</span><span class="text-gray-300">"推测性执行" — Agent可以预测同事反馈/实验结果，提前并行迭代</span></div>
            <div class="flex gap-2"><span class="text-yellow-400">5.</span><span class="text-gray-300">"初级员工处于劣势" — 领域专长决定了给Agent下达指令的质量</span></div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-center gap-4 mt-6">
          <button id="export-report" class="px-6 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition">导出JSON</button>
          <button id="new-game" class="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 transition">新的推演</button>
        </div>
      </div>
    `;

    $('#export-report').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify({ state, stats, bottleneckEntries }, null, 2)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `org-uplift-report-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
    });

    $('#new-game').addEventListener('click', resetGame);
  }

  // ══════════════════════════════════════
  // Main render dispatcher
  // ══════════════════════════════════════
  function render() {
    renderRoundIndicator();
    switch (state.phase) {
      case 'setup':        renderSetup(); break;
      case 'autoSim':      runAutoSimulation(); break;
      case 'standup':      renderStandup(); break;
      case 'work':         renderWork(); break;
      case 'roundSummary': renderRoundSummary(); break;
      case 'finalReport':  renderFinalReport(); break;
    }
  }

  function init() {
    if (state.apiKey || state.backendUrl) {
      Engine.configure(state.apiKey || '', state.aiParams || {}, state.backendUrl || '');
    }
    render();
  }

  return { init, resetGame };
})();

document.addEventListener('DOMContentLoaded', App.init);
