/**
 * Agent Execution Engine
 * Handles LLM calls, success rate calculation, and task simulation
 * Based on METR's Org-Uplift Game parameters
 */

const Engine = (() => {
  // ── METR capability parameters ──
  const DEFAULT_PARAMS = {
    timeHorizon: 200,       // hours
    speedMultiplier: 2,     // 2x Claude Opus fast mode
    writingQuality: 'entry-level employee with context',
    // Success rates by task difficulty (human-equivalent hours)
    successCurve: [
      { maxHours: 10,  rate: 0.95 },
      { maxHours: 40,  rate: 0.80 },
      { maxHours: 100, rate: 0.65 },
      { maxHours: 200, rate: 0.50 },
      { maxHours: 500, rate: 0.10 },
    ],
  };

  let apiKey = '';
  let params = { ...DEFAULT_PARAMS };
  let backendUrl = '';  // CLI backend API URL (e.g. http://127.0.0.1:8766)

  function configure(key, customParams = {}, backend = '') {
    apiKey = key;
    params = { ...DEFAULT_PARAMS, ...customParams };
    backendUrl = backend;
  }

  function getSuccessRate(estimatedHours) {
    for (const tier of params.successCurve) {
      if (estimatedHours <= tier.maxHours) return tier.rate;
    }
    return 0.05;
  }

  function rollDice(successRate) {
    const roll = Math.random();
    return {
      roll: Math.round(roll * 100),
      threshold: Math.round(successRate * 100),
      success: roll < successRate,
    };
  }

  // Bottleneck classification keywords
  const BOTTLENECK_PATTERNS = {
    'human-data':    ['collect data', 'gather', 'interview', 'survey', 'manual', '人工', '收集', '调研', '访谈'],
    'ml-experiment': ['train', 'experiment', 'benchmark', 'evaluate model', 'GPU', '训练', '实验', '跑模型'],
    'peer-review':   ['review', 'feedback', 'approve', 'sign off', '评审', '反馈', '审批', '确认'],
    'external':      ['external', 'vendor', 'partner', 'client', 'customer', '外部', '供应商', '客户', '合作方'],
    'decision':      ['decide', 'choose', 'prioritize', 'convention', 'standard', '决策', '选择', '优先级', '规范'],
    'coordination':  ['coordinate', 'sync', 'align', 'meeting', 'standup', '协调', '同步', '对齐', '会议'],
  };

  function classifyBottlenecks(text) {
    const lower = text.toLowerCase();
    const found = [];
    for (const [type, keywords] of Object.entries(BOTTLENECK_PATTERNS)) {
      if (keywords.some(kw => lower.includes(kw))) {
        found.push(type);
      }
    }
    return found.length ? found : ['none'];
  }

  const BOTTLENECK_LABELS = {
    'human-data':    '人工数据收集',
    'ml-experiment': 'ML实验等待',
    'peer-review':   '同事评审',
    'external':      '外部反馈',
    'decision':      '决策/规范',
    'coordination':  '跨团队协调',
    'none':          '无瓶颈',
  };

  // ── Backend API call (routes to uplift_cli.py server) ──
  async function callBackend(endpoint, body) {
    const resp = await fetch(`${backendUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!resp.ok) throw new Error(`Backend ${resp.status}`);
    return resp.json();
  }

  // ── LLM call ──
  async function callAgent(task, context, playerName, scenario) {
    // Route through CLI backend if configured
    if (backendUrl) {
      try {
        return await callBackend('/api/task', {
          task, context, player: playerName, scenario, apiKey,
        });
      } catch (e) {
        console.warn('Backend call failed, falling back:', e);
        // fall through to direct call or mock
      }
    }

    if (!apiKey) {
      return mockAgentResponse(task, context);
    }

    const systemPrompt = `你是一个模拟的高级AI Agent，正在参与"组织生产力提升"桌面推演实验。

## 你的能力参数
- 时间窗口：${params.timeHorizon}小时（你可以连续工作这么久不出错）
- 速度：人类工程师的${params.speedMultiplier}倍
- 写作质量：${params.writingQuality}
- 你只能基于提供的上下文工作，不能凭空创造数据

## 当前场景
${scenario || '通用工作场景'}

## 你的主人
${playerName || '研究员'}

## 输出格式要求
请用以下JSON格式回复（确保是合法JSON）：
{
  "steps": ["步骤1描述", "步骤2描述", "步骤3描述"],
  "deliverable": "产出物的简短描述",
  "estimatedHours": 数字（人类等效小时数）,
  "blockers": ["需要人类反馈的点1", "可能的风险2"],
  "confidence": "high/medium/low",
  "notes": "补充说明（如果有）"
}`;

    try {
      const resp = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: 'glm-5',
          max_tokens: 1024,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: `任务：${task}\n\n上下文：${context || '无额外上下文'}` },
          ],
        }),
      });

      if (!resp.ok) {
        const err = await resp.text();
        throw new Error(`API ${resp.status}: ${err}`);
      }

      const data = await resp.json();
      const text = data.choices?.[0]?.message?.content || '';

      // Try to parse JSON from the response
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        try {
          return JSON.parse(jsonMatch[0]);
        } catch {
          // fall through to text parsing
        }
      }

      return {
        steps: [text.slice(0, 200)],
        deliverable: text.slice(0, 100),
        estimatedHours: 20,
        blockers: [],
        confidence: 'medium',
        notes: text,
      };
    } catch (err) {
      console.error('Agent call failed:', err);
      return {
        steps: [`[API调用失败: ${err.message}]`],
        deliverable: '执行失败',
        estimatedHours: 0,
        blockers: ['API连接问题'],
        confidence: 'low',
        notes: err.message,
        error: true,
      };
    }
  }

  function mockAgentResponse(task, context) {
    const hours = 5 + Math.floor(Math.random() * 40);
    return Promise.resolve({
      steps: [
        '分析任务需求和约束条件',
        '搜索相关资料和已有代码/文档',
        '生成初版产出物并自检',
      ],
      deliverable: `针对「${task.slice(0, 30)}...」的初版交付物`,
      estimatedHours: hours,
      blockers: Math.random() > 0.6
        ? ['需要确认输出格式偏好', '某些数据源需要人工提供']
        : [],
      confidence: hours < 20 ? 'high' : hours < 80 ? 'medium' : 'low',
      notes: '[离线模式 - 未连接LLM API，使用模拟结果]',
    });
  }

  // ── Execute a full agent task ──
  async function executeTask(task, context, playerName, scenario) {
    const agentResult = await callAgent(task, context, playerName, scenario);
    const estimatedHours = agentResult.estimatedHours || 20;
    const successRate = getSuccessRate(estimatedHours);
    const dice = rollDice(successRate);
    const bottlenecks = classifyBottlenecks(
      (agentResult.blockers || []).join(' ') + ' ' + task
    );

    return {
      ...agentResult,
      successRate: Math.round(successRate * 100),
      dice,
      bottlenecks,
      timestamp: new Date().toISOString(),
    };
  }

  // ── Statistics ──
  function computeStats(allTasks) {
    if (!allTasks.length) return {
      totalTasks: 0, successCount: 0, successRate: 0,
      totalAgentHours: 0, avgHoursPerTask: 0,
      bottleneckCounts: {}, productivityMultiplier: 1,
    };

    const successCount = allTasks.filter(t => t.dice?.success).length;
    const totalHours = allTasks.reduce((s, t) => s + (t.estimatedHours || 0), 0);
    const bottleneckCounts = {};
    for (const t of allTasks) {
      for (const b of (t.bottlenecks || [])) {
        bottleneckCounts[b] = (bottleneckCounts[b] || 0) + 1;
      }
    }
    // METR estimate: 3-5x speedup
    const baselineHours = totalHours; // what humans would spend
    const agentHours = totalHours / params.speedMultiplier;
    const wallClockDays = 2; // 4 turns = 2 days
    const baselineDays = baselineHours / 8; // 8hr workday

    return {
      totalTasks: allTasks.length,
      successCount,
      successRate: Math.round((successCount / allTasks.length) * 100),
      totalAgentHours: Math.round(totalHours),
      avgHoursPerTask: Math.round(totalHours / allTasks.length),
      bottleneckCounts,
      productivityMultiplier: baselineDays > 0
        ? Math.round((baselineDays / wallClockDays) * 10) / 10
        : 1,
    };
  }

  return {
    configure,
    executeTask,
    computeStats,
    getSuccessRate,
    classifyBottlenecks,
    BOTTLENECK_LABELS,
    DEFAULT_PARAMS,
    get params() { return { ...params }; },
    get hasApiKey() { return !!apiKey; },
    get hasBackend() { return !!backendUrl; },
    get backendUrl() { return backendUrl; },
    callBackend,
  };
})();
