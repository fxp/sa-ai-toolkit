/**
 * Agent Execution Engine — thin HTTP client.
 *
 * All business logic (dice rolls, success curves, bottleneck classification,
 * stats aggregation) lives server-side in demos/org-uplift-py/core.py and is
 * exposed via /api/org_uplift?action=execute and /api/org_uplift?action=stats. This module preserves
 * the original public interface so docs/org-uplift/app.js does not need to
 * change.
 */

const Engine = (() => {
  const DEFAULT_PARAMS = {
    timeHorizon: 200,
    speedMultiplier: 2,
    writingQuality: 'entry-level employee with context',
  };

  // Mirror of server BOTTLENECK_LABELS so the UI can render without an extra round-trip.
  const BOTTLENECK_LABELS = {
    'human-data':    '人工数据收集',
    'ml-experiment': 'ML实验等待',
    'peer-review':   '同事评审',
    'external':      '外部反馈',
    'decision':      '决策/规范',
    'coordination':  '跨团队协调',
    'none':          '无瓶颈',
  };

  let apiKey = '';
  let params = { ...DEFAULT_PARAMS };
  let backendUrl = '';

  function configure(key, customParams = {}, backend = '') {
    apiKey = key;
    params = { ...DEFAULT_PARAMS, ...customParams };
    backendUrl = backend;
  }

  async function _post(path, body) {
    const base = backendUrl || '';
    const resp = await fetch(`${base}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!resp.ok) throw new Error(`API ${path} → ${resp.status}: ${await resp.text()}`);
    return resp.json();
  }

  async function executeTask(task, context, playerName, scenario) {
    try {
      return await _post('/api/org_uplift?action=execute', {
        task, context, player: playerName, scenario,
      });
    } catch (err) {
      console.error('executeTask failed:', err);
      return {
        steps: [`[API调用失败: ${err.message}]`],
        deliverable: '执行失败',
        estimatedHours: 0,
        blockers: ['API连接问题'],
        confidence: 'low',
        notes: err.message,
        task,
        player: playerName,
        successRate: 0,
        dice: { roll: 0, threshold: 0, success: false },
        bottlenecks: ['none'],
        timestamp: new Date().toISOString(),
        error: true,
      };
    }
  }

  async function computeStats(allTasks) {
    try {
      return await _post('/api/org_uplift?action=stats', { tasks: allTasks || [] });
    } catch (err) {
      console.error('computeStats failed:', err);
      return {
        totalTasks: (allTasks || []).length,
        successCount: 0, successRate: 0,
        totalAgentHours: 0, avgHoursPerTask: 0,
        bottleneckCounts: {}, productivityMultiplier: 1,
        error: err.message,
      };
    }
  }

  return {
    configure,
    executeTask,
    computeStats,
    BOTTLENECK_LABELS,
    DEFAULT_PARAMS,
    get params() { return { ...params }; },
    get hasApiKey() { return !!apiKey; },
    get hasBackend() { return !!backendUrl; },
    get backendUrl() { return backendUrl; },
  };
})();
