"""CEO Agent — morning brief, metrics, decisions, mood, competitors, actions.

Deterministic synthetic data keyed off the company name so the same company
always returns the same numbers/texts for a stable demo.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any

try:
    from faker import Faker  # type: ignore
except Exception:  # pragma: no cover
    Faker = None  # type: ignore


def _seed_from(company: str) -> int:
    return int(hashlib.md5(company.encode("utf-8")).hexdigest()[:8], 16)


# ----- Preset content (3 brief sets, each bilingual) -----

_BRIEF_SETS: list[dict[str, list[dict[str, str]]]] = [
    {
        "en": [
            {"title": "GPU cluster utilization hit 94% overnight", "priority": "high",
             "detail": "Inference latency P99 up 18%. Two options: (A) activate H200 burst ($180k/wk), (B) rate-limit tier-2. Recommend A — retention risk > cost.",
             "source": "Datadog + Snowflake"},
            {"title": "Competitor X shipped multi-agent orchestration", "priority": "medium",
             "detail": "Their GA yesterday targets same ICP. Sales reports 3 deals mentioned it. We ship similar in 6 weeks. Consider accelerating.",
             "source": "Gong + LinkedIn"},
            {"title": "Engineering attrition risk in Platform team", "priority": "medium",
             "detail": "2 senior ICs interviewed externally this week. Both GPU infra. Losing either delays roadmap 4-8 weeks. Schedule skip-levels.",
             "source": "Lattice + Gem"},
        ],
        "zh": [
            {"title": "GPU 集群昨夜利用率突破 94%", "priority": "high",
             "detail": "推理 P99 延迟+18%。两选项：(A) 激活 H200 弹性 ($180k/周)，(B) 限流二级客户。建议 A — 留存风险 > 成本。",
             "source": "Datadog + Snowflake"},
            {"title": "竞品 X 发布多 Agent 编排", "priority": "medium",
             "detail": "昨日 GA，目标客户同我们。销售反馈本周 3 单主动提及。我方类似功能 6 周后，建议加速。",
             "source": "Gong + LinkedIn"},
            {"title": "Platform 团队流失风险", "priority": "medium",
             "detail": "本周 2 位 senior IC 外部面试。均在 GPU 基础设施组，流失会让路线图延期 4-8 周。建议越级沟通。",
             "source": "Lattice + Gem"},
        ],
    },
    {
        "en": [
            {"title": "Enterprise pipeline $8.4M slipped from Q2", "priority": "high",
             "detail": "3 Fortune 500 deals pushed to Q3 citing procurement freeze. All started in January — suggests TOFU quality issue.",
             "source": "Salesforce + Clari"},
            {"title": "Open-source community contribution spike", "priority": "low",
             "detail": "GitHub PRs up 340% WoW after Karpathy tweet. 47 new external contributors. Triage within 48h.",
             "source": "GitHub + Linear"},
            {"title": "Board deck needs narrative refresh", "priority": "medium",
             "detail": "AI infra tailwind is table stakes. Competitors pitch platform moats. Our real advantage: distribution. Draft attached.",
             "source": "AI-generated"},
        ],
        "zh": [
            {"title": "$8.4M 企业管道从 Q2 滑到 Q3", "priority": "high",
             "detail": "3 笔财富500强订单推迟到 Q3，统一理由采购冻结。都在 1 月启动，暗示 TOFU 质量问题。",
             "source": "Salesforce + Clari"},
            {"title": "开源社区贡献激增", "priority": "low",
             "detail": "GitHub PR 周同比 +340%，起因 Karpathy 推文。47 位新外部贡献者。48h 内 triage。",
             "source": "GitHub + Linear"},
            {"title": "董事会 Deck 需要新叙事", "priority": "medium",
             "detail": "AI 基建顺风已烂大街。竞品讲平台护城河。我们真正的优势：分销能力。草稿已附。",
             "source": "AI 生成"},
        ],
    },
    {
        "en": [
            {"title": "Customer NPS dropped 8 points in EMEA", "priority": "high",
             "detail": "Latency complaints from 3 largest accounts. Frankfurt region latency P95 up 240ms since last deploy. Rollback candidate.",
             "source": "Delighted + Datadog"},
            {"title": "New compliance reg in California (SB-1047)", "priority": "medium",
             "detail": "Effective Q3. Adds safety eval requirements for models >10^23 FLOPs. Legal drafted response. Review by EOW.",
             "source": "Legal + Policy team"},
            {"title": "Two acquisition targets surfaced", "priority": "low",
             "detail": "Both <$50M ARR, complementary agent tooling. M&A team wants greenlight for initial calls. Low commitment.",
             "source": "Corp Dev"},
        ],
        "zh": [
            {"title": "EMEA 客户 NPS 下跌 8 分", "priority": "high",
             "detail": "3 大客户投诉延迟。法兰克福区 P95 自上次发版起+240ms。可回滚。",
             "source": "Delighted + Datadog"},
            {"title": "加州新合规法规 (SB-1047)", "priority": "medium",
             "detail": "Q3 生效。对 >10^23 FLOPs 模型增加安全评估要求。Legal 已草拟回复，本周内审阅。",
             "source": "法务 + 政策组"},
            {"title": "两个收购目标浮现", "priority": "low",
             "detail": "均 <$50M ARR，Agent 工具互补。M&A 组申请首次接触许可，承诺度低。",
             "source": "Corp Dev"},
        ],
    },
]

_DECISIONS: dict[str, list[dict[str, str]]] = {
    "en": [
        {"title": "Approve H200 GPU burst capacity ($720k/mo)", "risk": "low",
         "ai_rec": "APPROVE. Payback < 1mo if avoids 1 churn.", "impact": "+$2.1M ARR"},
        {"title": "Reorg: merge Platform + Infra teams", "risk": "high",
         "ai_rec": "DEFER. Timing bad (Q4 sprint). Revisit post-launch.", "impact": "-15% overhead, +attrition risk"},
        {"title": "Hire VP Sales Enterprise (US-East)", "risk": "medium",
         "ai_rec": "APPROVE. Pre-close top 2 candidates in parallel. 11wk ramp.", "impact": "+$4.8M Q4 pipeline"},
    ],
    "zh": [
        {"title": "批准 H200 GPU 弹性容量 ($720k/月)", "risk": "low",
         "ai_rec": "建议批准。如避免 1 客户流失，回本 < 1 个月。", "impact": "+$2.1M ARR"},
        {"title": "合并 Platform + Infra 团队", "risk": "high",
         "ai_rec": "建议推迟。时机不对 (Q4 冲刺期)，发布后重评。", "impact": "-15%管理成本, +流失风险"},
        {"title": "招聘 VP Sales Enterprise (美东)", "risk": "medium",
         "ai_rec": "建议批准。Top 2 候选人并行预 close。Ramp 11 周。", "impact": "+$4.8M Q4 管道"},
    ],
}

_COMPETITORS: dict[str, list[dict[str, str]]] = {
    "en": [
        {"time": "2h ago", "source": "TechCrunch", "text": "Anthropic launches Claude for Enterprise — overlaps with our mid-market ICP", "sentiment": "threat"},
        {"time": "6h ago", "source": "LinkedIn", "text": "Competitor X poached our Director of ML (Janet K.) — 4yr tenure", "sentiment": "threat"},
        {"time": "1d ago", "source": "HackerNews", "text": "OSS challenger hits 12k stars in 2 weeks — 80% of our features, free", "sentiment": "watch"},
        {"time": "2d ago", "source": "The Information", "text": "Rival raised $400M Series D at $4.2B — 2x our valuation", "sentiment": "threat"},
        {"time": "3d ago", "source": "Gong", "text": "3 prospect calls this week mentioned Competitor Y price cut", "sentiment": "watch"},
        {"time": "4d ago", "source": "Reddit", "text": "Former Competitor Z employee AMA: roadmap in disarray", "sentiment": "opportunity"},
        {"time": "5d ago", "source": "Twitter", "text": "Our logo mentioned in 42 CIO threads this week (7x baseline)", "sentiment": "opportunity"},
    ],
    "zh": [
        {"time": "2 小时前", "source": "TechCrunch", "text": "Anthropic 推 Claude for Enterprise — 与我们中端 ICP 重合", "sentiment": "threat"},
        {"time": "6 小时前", "source": "LinkedIn", "text": "竞品 X 挖走我们 ML 总监 Janet K.（4年司龄）", "sentiment": "threat"},
        {"time": "1 天前", "source": "HackerNews", "text": "开源挑战者 2 周涨到 12k star — 80% 功能免费", "sentiment": "watch"},
        {"time": "2 天前", "source": "The Information", "text": "对手融 $400M D 轮，估值 $4.2B（我们 2 倍）", "sentiment": "threat"},
        {"time": "3 天前", "source": "Gong", "text": "本周 3 个电话提到竞品 Y 降价", "sentiment": "watch"},
        {"time": "4 天前", "source": "Reddit", "text": "竞品 Z 前员工 AMA：组织调整后路线图混乱", "sentiment": "opportunity"},
        {"time": "5 天前", "source": "Twitter", "text": "我们 logo 本周被 42 条 CIO 帖提到（基线 7 倍）", "sentiment": "opportunity"},
    ],
}

_ACTIONS: dict[str, list[dict[str, Any]]] = {
    "en": [
        {"priority": 1, "title": "10:30 AM — Skip-level with Platform team", "why": "Before lunch. Two ICs critical.", "owner": "You"},
        {"priority": 2, "title": "12:00 PM — Approve GPU burst in Slack #exec", "why": "$720k decision, evidence attached.", "owner": "You"},
        {"priority": 3, "title": "2:00 PM — Call Fortune 500 buyer (deal slip)", "why": "$3.2M at stake. Freeze may be negotiable.", "owner": "You + Head of Sales"},
        {"priority": 4, "title": "3:30 PM — Review Competitor X launch analysis", "why": "Product + Marketing standup prep.", "owner": "Product delivers, you review"},
        {"priority": 5, "title": "5:00 PM — Check-in with CFO on burn forecast", "why": "Runway revision post-GPU decision.", "owner": "You + CFO"},
    ],
    "zh": [
        {"priority": 1, "title": "10:30 — Platform 团队越级沟通", "why": "午餐前。两位资深 IC 关键。", "owner": "你"},
        {"priority": 2, "title": "12:00 — Slack #exec 批准 GPU 弹性预算", "why": "$720k 决策，证据已附。", "owner": "你"},
        {"priority": 3, "title": "14:00 — 致电财富500强客户（订单滑期）", "why": "$3.2M 订单。采购冻结可能可谈。", "owner": "你 + 销售负责人"},
        {"priority": 4, "title": "15:30 — 审阅竞品 X 发布分析", "why": "产品+市场明早早会准备。", "owner": "产品交付，你审阅"},
        {"priority": 5, "title": "17:00 — 与 CFO 对齐烧钱预测", "why": "GPU 决策后重算 runway。", "owner": "你 + CFO"},
    ],
}

_DEPTS_EN = ["Engineering", "Product", "Sales", "Marketing", "Customer Success", "Finance", "People", "Design"]
_DEPTS_ZH = ["工程", "产品", "销售", "市场", "客户成功", "财务", "人力", "设计"]
_MOOD_LABELS = {"en": ["Focused", "Tired", "Anxious", "Happy", "Motivated"],
                "zh": ["专注", "疲惫", "焦虑", "开心", "积极"]}

# Business events that actually bend the ARR curve. Month index is 0..8 in the
# historical window (labels May..Jan). Impact is a multiplicative delta applied
# that month on top of the baseline growth.
_ARR_EVENTS: list[dict[str, Any]] = [
    {"month": 1, "type": "launch",  "impact": 0.08,   "en": "Enterprise Tier GA (+$4M)",     "zh": "企业版 GA 上线 (+$4M)"},
    {"month": 3, "type": "churn",   "impact": -0.07,  "en": "Lost ACME logo (-$1.2M)",       "zh": "流失 ACME 大客户 (-$1.2M)"},
    {"month": 4, "type": "win",     "impact": 0.05,   "en": "Signed Globex ($2.2M ARR)",     "zh": "签下 Globex ($2.2M ARR)"},
    {"month": 6, "type": "outage",  "impact": -0.025, "en": "US-East outage, 6h",            "zh": "美东宕机 6 小时"},
    {"month": 7, "type": "launch",  "impact": 0.09,   "en": "APAC region live",              "zh": "APAC 区域上线"},
    {"month": 8, "type": "win",     "impact": 0.04,   "en": "Hiring Copilot wedge in HR BU", "zh": "招聘 Copilot 切入 HR 行业"},
]


class CEOAgent:
    """Stateless agent — everything is derived from `company` + brief_idx + lang."""

    def __init__(self, company: str = "NewCo Inc", seed: int | None = None) -> None:
        self.company = company
        self.seed = seed if seed is not None else _seed_from(company)
        self._rng = random.Random(self.seed)

    # ----- public API -----

    def morning_brief(self, brief_idx: int = 0, lang: str = "en") -> list[dict[str, str]]:
        lang = lang if lang in ("en", "zh") else "en"
        bset = _BRIEF_SETS[brief_idx % len(_BRIEF_SETS)]
        return list(bset.get(lang, bset["en"]))

    def metrics(self, lang: str = "en") -> dict[str, Any]:
        r = random.Random(self.seed)
        headcount = 500 + r.randint(0, 4000)
        nrr = 100 + r.randint(5, 40)
        enps = r.randint(20, 60)
        burn = round(0.8 + r.random() * 1.4, 1)
        runway = r.randint(14, 36)

        # Event-driven ARR: 9 months historical, 3 months forecast, real inflections.
        labels = ["May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]
        HIST = 9  # May..Jan are historical, Feb..Apr are forecast
        baseline_mom = 0.042  # 4.2% baseline monthly growth
        events = _ARR_EVENTS  # module-level defs (below)
        # Build historical path
        series_arr: list[float] = []
        val = 50.0  # starting ARR $M
        for i in range(HIST):
            # baseline growth + small noise
            val *= 1 + baseline_mom + (r.random() - 0.5) * 0.012
            # apply any event landing this month
            for ev in events:
                if ev["month"] == i:
                    val *= 1 + ev["impact"]
            series_arr.append(round(val, 1))
        actual_now = series_arr[-1]
        # Forecast: pipeline-weighted growth (higher) — but show widening uncertainty.
        forecast = [None] * HIST
        forecast_low = [None] * HIST
        forecast_high = [None] * HIST
        forecast[HIST - 1] = actual_now
        forecast_low[HIST - 1] = actual_now
        forecast_high[HIST - 1] = actual_now
        fval = actual_now
        for i in range(HIST, 12):
            growth = 0.058  # 5.8% MoM forecast
            fval *= 1 + growth
            # band widens with distance
            widen = (i - HIST + 1) * 0.03
            forecast.append(round(fval, 1))
            forecast_low.append(round(fval * (1 - widen), 1))
            forecast_high.append(round(fval * (1 + widen), 1))
        # Target: plan that was set at start of year; mildly ambitious.
        target_start = series_arr[0] * 1.05
        target_end = round(forecast[-1] * 1.12, 1)
        tstep = (target_end - target_start) / 11
        series_target = [round(target_start + tstep * i, 1) for i in range(12)]

        # Display labels — use actual current value
        arr_val = int(round(actual_now))
        arr_prev_q = series_arr[max(0, HIST - 4)] if HIST >= 4 else series_arr[0]
        arr_change_pct = round((actual_now / arr_prev_q - 1) * 100)

        # Radar 0-10 per dept
        depts = _DEPTS_EN if lang == "en" else _DEPTS_ZH
        radar_current = [round(6 + r.random() * 3.5, 1) for _ in depts]
        radar_prev = [max(0, round(v - 0.3 + r.random() * 0.8, 1)) for v in radar_current]

        # Event annotations for the chart
        ev_annotations = [{
            "month_idx": ev["month"],
            "type": ev["type"],
            "impact_pct": round(ev["impact"] * 100, 1),
            "label": ev["zh"] if lang == "zh" else ev["en"],
        } for ev in events]

        return {
            "company": self.company,
            "arr": f"${arr_val}M",
            "arr_change": f"+{arr_change_pct}% QoQ",
            "headcount": headcount,
            "headcount_delta": f"+{r.randint(5, 25)} this week" if lang == "en" else f"本周+{r.randint(5, 25)}",
            "nrr": f"{nrr}%",
            "nrr_change": f"+{r.randint(1, 5)}pt MoM",
            "enps": f"+{enps}",
            "enps_change": f"-{r.randint(2, 7)} MoM",
            "burn": f"{burn}x",
            "burn_label": "Healthy" if burn < 1.5 else "Watch" if lang == "en" else ("健康" if burn < 1.5 else "关注"),
            "runway": f"{runway}mo",
            "runway_label": "at current burn" if lang == "en" else "按当前烧钱",
            "series": {
                "labels": labels,
                "arr": series_arr + [None] * (12 - HIST),  # historical segment
                "forecast": forecast,                       # forecast segment (overlaps last historical point)
                "forecast_low": forecast_low,
                "forecast_high": forecast_high,
                "target": series_target,
                "events": ev_annotations,
                "history_end_idx": HIST - 1,
                "radar_labels": depts,
                "radar_current": radar_current,
                "radar_prev": radar_prev,
            },
        }

    def decisions(self, lang: str = "en") -> list[dict[str, str]]:
        lang = lang if lang in ("en", "zh") else "en"
        return [dict(d) for d in _DECISIONS[lang]]

    def mood_heatmap(self, lang: str = "en") -> dict[str, Any]:
        lang = lang if lang in ("en", "zh") else "en"
        r = random.Random(self.seed ^ 0xA5A5)
        depts = _DEPTS_EN if lang == "en" else _DEPTS_ZH
        rows = []
        for i, d in enumerate(depts):
            size = 30 + r.randint(0, 500)
            mood = [r.randint(1, 5) for _ in range(5)]
            rows.append({"dept": d, "size": size, "mood": mood})
        return {"labels": _MOOD_LABELS[lang], "rows": rows}

    def competitor_feed(self, lang: str = "en") -> list[dict[str, str]]:
        lang = lang if lang in ("en", "zh") else "en"
        return [dict(c) for c in _COMPETITORS[lang]]

    def action_queue(self, lang: str = "en") -> list[dict[str, Any]]:
        lang = lang if lang in ("en", "zh") else "en"
        return [dict(a) for a in _ACTIONS[lang]]

    def projects(self, lang: str = "en") -> list[dict[str, Any]]:
        """Macro rollup — one row per active project. For the top-level panel."""
        lang = lang if lang in ("en", "zh") else "en"
        return [_project_summary(p, lang) for p in _PROJECTS]

    def project_detail(self, project_id: str, lang: str = "en") -> dict[str, Any] | None:
        """Full drill-down — milestones, blockers, activity, metrics, next actions."""
        lang = lang if lang in ("en", "zh") else "en"
        for p in _PROJECTS:
            if p["id"] == project_id:
                return _project_detail(p, lang)
        return None

    def ask(self, query: str, lang: str = "en") -> dict[str, Any]:
        """Meta-style CEO Agent. Match the query to a canned demo plan, else
        synthesize a generic multi-tool trace. Returns plan + steps + answer + citations."""
        lang = lang if lang in ("en", "zh") else "en"
        q = (query or "").strip().lower()
        preset = _match_ask_preset(q, lang)
        if preset is not None:
            return {"query": query, "lang": lang, **preset}
        return {"query": query, "lang": lang, **_generic_ask_trace(query, lang)}

    def all(self, brief_idx: int = 0, lang: str = "en") -> dict[str, Any]:
        return {
            "company": self.company,
            "lang": lang,
            "brief": self.morning_brief(brief_idx, lang),
            "metrics": self.metrics(lang),
            "decisions": self.decisions(lang),
            "mood": self.mood_heatmap(lang),
            "competitors": self.competitor_feed(lang),
            "actions": self.action_queue(lang),
        }


# ============================================================
# Ask-anything Agent — Meta-style CEO Agent demo presets
# ============================================================

_ASK_PRESETS: list[dict[str, Any]] = [
    {
        "id": "eng-velocity",
        "keywords_en": ["platform", "velocity", "ship", "bottleneck", "engineering", "throughput", "prs"],
        "keywords_zh": ["platform", "吞吐", "瓶颈", "工单", "研发", "工程", "产出"],
        "chip_en": "How much did Platform ship last week? Where's the bottleneck?",
        "chip_zh": "Platform 团队上周交付如何？瓶颈在哪？",
        "dept": {"en": "Engineering", "zh": "工程"},
        "en": {
            "plan": "Pull Platform team's PR throughput from GitHub, cross-reference with Jira cycle time, then ask Slack for blockers.",
            "steps": [
                {"tool": "github.list_prs", "args": {"team": "platform", "since": "7d"}, "observation": "47 PRs merged (+12% WoW), but p95 review latency is 38h (+65%)."},
                {"tool": "jira.cycle_time", "args": {"project": "PLAT", "range": "7d"}, "observation": "Median cycle 4.1d; Infra subteam at 7.3d (2x rest)."},
                {"tool": "slack.search", "args": {"channel": "#platform-eng", "q": "blocked OR waiting"}, "observation": "11 messages flagging review backlog on the GPU-scheduler refactor PR."},
                {"tool": "lattice.pulse", "args": {"team": "platform"}, "observation": "Sentiment dipped from 7.8 → 6.9 this week."},
            ],
            "answer": "Platform merged 47 PRs last week (+12% WoW), but that masks a review-latency problem: p95 is up to 38h and Infra's cycle time is 7.3d, 2x the rest of the team. The bottleneck is the GPU-scheduler refactor PR — 11 Slack threads reference it as blocking. Pulse sentiment dropped 0.9 this week. Recommend: pair a senior reviewer onto that PR and unblock Infra by Friday.",
            "citations": [
                {"source": "GitHub · platform org", "time": "live"},
                {"source": "Jira · PLAT project", "time": "live"},
                {"source": "Slack · #platform-eng", "time": "7d"},
                {"source": "Lattice · pulse survey", "time": "this week"},
            ],
        },
        "zh": {
            "plan": "从 GitHub 拉 Platform 团队 PR 吞吐，叠加 Jira cycle time，再在 Slack 上找堵点。",
            "steps": [
                {"tool": "github.list_prs", "args": {"team": "platform", "since": "7d"}, "observation": "合并 47 个 PR（环比 +12%），但 review p95 延迟 38 小时（+65%）。"},
                {"tool": "jira.cycle_time", "args": {"project": "PLAT", "range": "7d"}, "observation": "中位 cycle 4.1 天；Infra 子组 7.3 天，是其他组的 2 倍。"},
                {"tool": "slack.search", "args": {"channel": "#platform-eng", "q": "blocked OR waiting"}, "observation": "11 条消息抱怨 GPU-scheduler 重构 PR 的评审积压。"},
                {"tool": "lattice.pulse", "args": {"team": "platform"}, "observation": "本周情绪从 7.8 → 6.9。"},
            ],
            "answer": "Platform 上周合入 47 个 PR（环比 +12%），但掩盖了评审积压问题：p95 升到 38 小时，Infra 子组 cycle time 7.3 天，是其他组的 2 倍。瓶颈在 GPU-scheduler 重构 PR——Slack 上 11 条消息提到被它阻塞。脉冲情绪本周下降 0.9。建议：安排一名 senior 评审配对该 PR，本周五前解锁 Infra。",
            "citations": [
                {"source": "GitHub · platform org", "time": "实时"},
                {"source": "Jira · PLAT 项目", "time": "实时"},
                {"source": "Slack · #platform-eng", "time": "7 天"},
                {"source": "Lattice · 脉冲问卷", "time": "本周"},
            ],
        },
    },
    {
        "id": "apac-churn",
        "keywords_en": ["apac", "churn", "asia", "retention", "nrr"],
        "keywords_zh": ["apac", "亚太", "流失", "留存", "续费"],
        "chip_en": "Why is APAC churn up this quarter?",
        "chip_zh": "APAC 本季度流失为什么上升？",
        "dept": {"en": "Sales / CS", "zh": "销售 / 客户成功"},
        "en": {
            "plan": "Segment APAC churned logos, listen to the exit calls, and check Support tickets for a common root cause.",
            "steps": [
                {"tool": "snowflake.query", "args": {"table": "arr_movement", "region": "APAC", "range": "90d"}, "observation": "Gross churn 4.8% (up from 2.1% Q-1). 7 logos lost, $2.3M ARR."},
                {"tool": "gong.transcripts", "args": {"outcome": "churned", "region": "APAC"}, "observation": "5 of 7 exit calls mention 'latency in Singapore region' unprompted."},
                {"tool": "zendesk.top_tags", "args": {"region": "APAC", "range": "90d"}, "observation": "Tag 'latency-sg' up 180% QoQ."},
                {"tool": "datadog.p99", "args": {"region": "ap-southeast-1", "range": "90d"}, "observation": "P99 inference latency 2.8s vs 0.9s in us-east."},
            ],
            "answer": "APAC churn tripled from 2.1% → 4.8% this quarter, costing $2.3M ARR across 7 logos. The dominant root cause is Singapore-region inference latency: P99 is 2.8s vs 0.9s in us-east — called out in 5 of 7 exit calls and tagged 'latency-sg' on 180% more tickets QoQ. Fix is a Singapore GPU footprint, not a commercial issue.",
            "citations": [
                {"source": "Snowflake · arr_movement", "time": "90d"},
                {"source": "Gong · exit calls", "time": "quarter"},
                {"source": "Zendesk · APAC tags", "time": "90d"},
                {"source": "Datadog · ap-southeast-1", "time": "90d"},
            ],
        },
        "zh": {
            "plan": "切分 APAC 流失客户，听离场电话，再查工单寻找共性根因。",
            "steps": [
                {"tool": "snowflake.query", "args": {"table": "arr_movement", "region": "APAC", "range": "90d"}, "observation": "毛流失 4.8%（上季度 2.1%）。流失 7 个客户，$2.3M ARR。"},
                {"tool": "gong.transcripts", "args": {"outcome": "churned", "region": "APAC"}, "observation": "7 通离场电话中 5 通主动提到「新加坡区延迟」。"},
                {"tool": "zendesk.top_tags", "args": {"region": "APAC", "range": "90d"}, "observation": "标签「latency-sg」环比 +180%。"},
                {"tool": "datadog.p99", "args": {"region": "ap-southeast-1", "range": "90d"}, "observation": "P99 推理延迟 2.8s，美东为 0.9s。"},
            ],
            "answer": "APAC 流失率从 2.1% 跳到 4.8%，流失 7 家客户共 $2.3M ARR。主因是新加坡区推理延迟：P99 2.8 秒，美东仅 0.9 秒——7 通离场电话里 5 通提到，相关工单标签环比上涨 180%。根因是基础设施，不是商务问题，建议补齐新加坡 GPU。",
            "citations": [
                {"source": "Snowflake · arr_movement", "time": "90 天"},
                {"source": "Gong · 离场电话", "time": "本季"},
                {"source": "Zendesk · APAC 标签", "time": "90 天"},
                {"source": "Datadog · ap-southeast-1", "time": "90 天"},
            ],
        },
    },
    {
        "id": "hire-runway",
        "keywords_en": ["hire", "runway", "burn", "40 engineers", "headcount", "cash"],
        "keywords_zh": ["招", "40 个", "runway", "烧钱", "现金流", "编制"],
        "chip_en": "If we hire 40 more engineers, how short does runway get?",
        "chip_zh": "再招 40 个工程师后 runway 剩多久？",
        "dept": {"en": "Finance", "zh": "财务"},
        "en": {
            "plan": "Pull current burn, model the incremental fully-loaded cost, subtract from cash, recompute runway under two ARR-growth scenarios.",
            "steps": [
                {"tool": "netsuite.current_state", "args": {}, "observation": "Cash $148M, monthly burn $6.2M, ARR $84M growing 6% MoM."},
                {"tool": "model.fully_loaded_cost", "args": {"role": "senior_eng", "n": 40, "region_mix": "us:30,eu:10"}, "observation": "Incremental burn $1.34M/mo starting month 2 (ramp)."},
                {"tool": "model.runway", "args": {"scenario": "status_quo"}, "observation": "Runway drops from 23.9 mo → 19.4 mo."},
                {"tool": "model.runway", "args": {"scenario": "growth_holds"}, "observation": "If ARR growth holds 6% MoM, runway to 22.1 mo; breakeven shifts by ~3 months."},
            ],
            "answer": "Adding 40 engineers costs an incremental $1.34M/mo fully-loaded (US-weighted). At current burn and cash, runway shortens from 23.9 to 19.4 months in the flat case. If ARR keeps compounding at 6% MoM, runway holds at 22.1 months but breakeven slips ~3 months. Verdict: affordable, but plan the next raise 6 months earlier.",
            "citations": [
                {"source": "NetSuite · GL", "time": "live"},
                {"source": "Finance model · v2026.04", "time": "current"},
                {"source": "Workday · comp bands", "time": "current"},
            ],
        },
        "zh": {
            "plan": "拉当前烧钱率，建模新增全成本，按两种 ARR 增长情景重算 runway。",
            "steps": [
                {"tool": "netsuite.current_state", "args": {}, "observation": "现金 $148M，月烧 $6.2M，ARR $84M 月环比 +6%。"},
                {"tool": "model.fully_loaded_cost", "args": {"role": "senior_eng", "n": 40, "region_mix": "us:30,eu:10"}, "observation": "第 2 个月起月增烧钱 $1.34M（含爬坡）。"},
                {"tool": "model.runway", "args": {"scenario": "status_quo"}, "observation": "runway 从 23.9 → 19.4 个月。"},
                {"tool": "model.runway", "args": {"scenario": "growth_holds"}, "observation": "若 ARR 保持 6% 月复合，runway 为 22.1 个月；盈亏平衡点晚约 3 个月。"},
            ],
            "answer": "招 40 名工程师每月增烧 $1.34M（含美欧配比）。保持现状 runway 从 23.9 个月降到 19.4 个月；若 ARR 保持 6% 月复合增长，runway 为 22.1 个月，但盈亏平衡推迟约 3 个月。结论：承受得起，但下一轮融资要提前 6 个月启动。",
            "citations": [
                {"source": "NetSuite · 总账", "time": "实时"},
                {"source": "财务模型 · v2026.04", "time": "当前"},
                {"source": "Workday · 薪资带", "time": "当前"},
            ],
        },
    },
    {
        "id": "hipo-design",
        "keywords_en": ["design", "hipo", "high-potential", "promote", "promotion"],
        "keywords_zh": ["design", "设计", "高潜", "晋升", "提拔"],
        "chip_en": "Who on Design is high-potential but not yet promoted?",
        "chip_zh": "Design 团队谁是高潜但还没被晋升？",
        "dept": {"en": "People", "zh": "人才"},
        "en": {
            "plan": "Cross-reference performance calibration with tenure at level and 360 feedback, filter Design.",
            "steps": [
                {"tool": "lattice.calibration", "args": {"org": "design"}, "observation": "12 ICs rated 'exceeds' last 2 cycles."},
                {"tool": "workday.tenure_at_level", "args": {"org": "design", "min_months": 18}, "observation": "Of those 12, 4 have been at level >=18 months."},
                {"tool": "lattice.360_feedback", "args": {"ids": ["..."]}, "observation": "3 of 4 show repeated cross-team praise (PM, Eng, Research)."},
                {"tool": "gem.interview_signal", "args": {"ids": ["..."]}, "observation": "1 of 3 had an external interview this month."},
            ],
            "answer": "Three design ICs fit the HiPO-not-yet-promoted profile: Priya R. (Sr → Staff, 22mo, 3 cross-team endorsements), Marcus K. (Sr, 19mo, strong research partnership), and Jamie L. (Mid → Sr, 20mo, currently interviewing externally — act this week). I'd prioritize Jamie for a retention conversation before a formal promo packet lands.",
            "citations": [
                {"source": "Lattice · H2 calibration", "time": "last 2 cycles"},
                {"source": "Workday · tenure", "time": "live"},
                {"source": "Lattice · 360 feedback", "time": "12mo"},
                {"source": "Gem · interview signal", "time": "30d"},
            ],
        },
        "zh": {
            "plan": "交叉比对绩效校准、在级任职时长与 360 反馈，筛 Design。",
            "steps": [
                {"tool": "lattice.calibration", "args": {"org": "design"}, "observation": "12 位 IC 过去 2 个周期评为「超预期」。"},
                {"tool": "workday.tenure_at_level", "args": {"org": "design", "min_months": 18}, "observation": "其中 4 位在当前级别 ≥18 个月。"},
                {"tool": "lattice.360_feedback", "args": {"ids": ["..."]}, "observation": "4 人中 3 人获跨团队（产品/工程/研究）多次表扬。"},
                {"tool": "gem.interview_signal", "args": {"ids": ["..."]}, "observation": "3 人中 1 人本月参加了外部面试。"},
            ],
            "answer": "Design 有三位符合「高潜未晋升」：Priya R.（Sr → Staff，22 个月，跨团队 3 次背书）、Marcus K.（Sr，19 个月，研究合作强）、Jamie L.（Mid → Sr，20 个月，本月在外部面试——需本周行动）。建议先给 Jamie 做留任沟通，再走正式晋升包。",
            "citations": [
                {"source": "Lattice · H2 校准", "time": "过去 2 个周期"},
                {"source": "Workday · 在级时长", "time": "实时"},
                {"source": "Lattice · 360 反馈", "time": "12 个月"},
                {"source": "Gem · 面试信号", "time": "30 天"},
            ],
        },
    },
    {
        "id": "gpu-spike",
        "keywords_en": ["gpu", "spike", "utilization", "94%", "cluster", "overnight"],
        "keywords_zh": ["gpu", "利用率", "突破", "集群", "昨夜"],
        "chip_en": "Why did GPU utilization spike to 94% last night?",
        "chip_zh": "昨夜 GPU 利用率为什么突破 94%？",
        "dept": {"en": "Infrastructure", "zh": "基础设施"},
        "en": {
            "plan": "Attribute the spike to a tenant, check if it's an expected batch job, then assess risk.",
            "steps": [
                {"tool": "datadog.gpu_util", "args": {"range": "12h"}, "observation": "94% peak at 02:17 UTC, held for 47 min."},
                {"tool": "k8s.top_consumers", "args": {"window": "02:00-03:30 UTC"}, "observation": "72% attributable to tenant 'acme-enterprise' batch inference."},
                {"tool": "billing.contract", "args": {"tenant": "acme-enterprise"}, "observation": "Plan allows burst to 30% reserved capacity; they used 68%."},
                {"tool": "pagerduty.incidents", "args": {"range": "12h"}, "observation": "No incidents — P99 latency rose 18% but stayed within SLO."},
            ],
            "answer": "Last night's 94% GPU spike was 72% driven by one tenant, acme-enterprise, running an unscheduled batch inference at 02:17 UTC that exceeded their 30% burst allowance (hit 68%). It did not breach SLO, but it crowded out tier-2 traffic for 47 minutes. Either tighten burst enforcement or upsell them to a higher tier — Sales says they're a likely yes.",
            "citations": [
                {"source": "Datadog · GPU utilization", "time": "12h"},
                {"source": "Kubernetes · consumer report", "time": "12h"},
                {"source": "Billing · contracts", "time": "current"},
                {"source": "PagerDuty · incidents", "time": "12h"},
            ],
        },
        "zh": {
            "plan": "把峰值归因到某个租户，判断是否为计划内批任务，再评估风险。",
            "steps": [
                {"tool": "datadog.gpu_util", "args": {"range": "12h"}, "observation": "02:17 UTC 峰值 94%，持续 47 分钟。"},
                {"tool": "k8s.top_consumers", "args": {"window": "02:00-03:30 UTC"}, "observation": "72% 来自租户 acme-enterprise 的批量推理。"},
                {"tool": "billing.contract", "args": {"tenant": "acme-enterprise"}, "observation": "合约允许爆发到预留容量 30%，实际用到 68%。"},
                {"tool": "pagerduty.incidents", "args": {"range": "12h"}, "observation": "无事故——P99 延迟 +18%，仍在 SLO 内。"},
            ],
            "answer": "昨夜 94% 的 GPU 峰值，72% 来自一个租户 acme-enterprise 在 02:17 UTC 的计划外批量推理，爆发用量 68%（合约上限 30%）。未违反 SLO，但挤占了二级客户 47 分钟。建议：要么收紧爆发执行，要么升级他们到更高档位——销售判断成单率很高。",
            "citations": [
                {"source": "Datadog · GPU 利用率", "time": "12 小时"},
                {"source": "Kubernetes · 租户消耗", "time": "12 小时"},
                {"source": "Billing · 合约", "time": "当前"},
                {"source": "PagerDuty · 事件", "time": "12 小时"},
            ],
        },
    },
    {
        "id": "complaints-feature",
        "keywords_en": ["complaint", "complaints", "feature", "ticket", "support"],
        "keywords_zh": ["投诉", "功能", "工单", "客户", "提到"],
        "chip_en": "What feature comes up most in customer complaints (last 7 days)?",
        "chip_zh": "过去 7 天客户投诉里提到最多的功能是什么？",
        "dept": {"en": "Product / Support", "zh": "产品 / 客服"},
        "en": {
            "plan": "Pull 7-day support tickets, cluster by feature with an embedding model, rank by count and sentiment-weighted severity.",
            "steps": [
                {"tool": "zendesk.tickets", "args": {"range": "7d", "type": "complaint"}, "observation": "1,284 tickets in period."},
                {"tool": "embedding.cluster", "args": {"model": "claude-embed-v3", "k": 12}, "observation": "Top cluster: 'multi-agent orchestration reliability' — 284 tickets (22%)."},
                {"tool": "sentiment.weight", "args": {"cluster": "multi-agent"}, "observation": "Severity 4.3/5 avg; 61% tagged 'blocker'."},
                {"tool": "linear.open_bugs", "args": {"feature": "multi-agent"}, "observation": "9 open P1 bugs, oldest 11 days."},
            ],
            "answer": "The dominant cluster is multi-agent orchestration reliability: 284 tickets (22% of complaints this week), 4.3/5 severity, 61% tagged blocker. Linear shows 9 open P1 bugs in that feature, oldest 11 days. Sessions consistently cite 'agent loses context after tool call 5'. Root cause isn't capacity — it's engineering triage. Suggest Product escalate to a war room.",
            "citations": [
                {"source": "Zendesk · complaints", "time": "7d"},
                {"source": "Embedding cluster · k=12", "time": "7d"},
                {"source": "Linear · P1 bugs", "time": "live"},
            ],
        },
        "zh": {
            "plan": "拉 7 天客服工单，用 embedding 按功能聚类，按数量 × 情绪严重度排序。",
            "steps": [
                {"tool": "zendesk.tickets", "args": {"range": "7d", "type": "complaint"}, "observation": "期内 1,284 条工单。"},
                {"tool": "embedding.cluster", "args": {"model": "claude-embed-v3", "k": 12}, "observation": "最大簇：「多 Agent 编排可靠性」——284 条（22%）。"},
                {"tool": "sentiment.weight", "args": {"cluster": "multi-agent"}, "observation": "平均严重度 4.3/5，61% 标为阻塞。"},
                {"tool": "linear.open_bugs", "args": {"feature": "multi-agent"}, "observation": "9 个 P1 未修 bug，最久 11 天。"},
            ],
            "answer": "最大投诉簇是多 Agent 编排可靠性：284 条（本周投诉的 22%），严重度 4.3/5，61% 标「阻塞」。Linear 上该功能有 9 个 P1 bug 未修，最久 11 天。会话一致反映「第 5 次调用工具后 Agent 丢失上下文」。根因不是容量而是工程优先级，建议产品升级为作战室。",
            "citations": [
                {"source": "Zendesk · 投诉工单", "time": "7 天"},
                {"source": "Embedding 聚类 · k=12", "time": "7 天"},
                {"source": "Linear · P1 bug", "time": "实时"},
            ],
        },
    },
    {
        "id": "eu-ai-act",
        "keywords_en": ["eu", "ai act", "compliance", "article 13", "legal", "regulat"],
        "keywords_zh": ["欧盟", "ai 法案", "ai法案", "合规", "第 13 条", "article 13", "法务"],
        "chip_en": "Which product line is most exposed to EU AI Act Article 13?",
        "chip_zh": "欧盟 AI 法案第 13 条对哪条产品线影响最大？",
        "dept": {"en": "Legal / Compliance", "zh": "法务 / 合规"},
        "en": {
            "plan": "Map product lines to risk categories, match against Article 13 transparency obligations, rank by EU revenue exposure.",
            "steps": [
                {"tool": "compliance.map", "args": {"regulation": "eu_ai_act", "article": "13"}, "observation": "Article 13 = transparency + instructions-for-use for high-risk systems."},
                {"tool": "product.risk_register", "args": {}, "observation": "3 lines classified high-risk: Hiring Copilot, Credit Scoring API, Content Moderation."},
                {"tool": "snowflake.query", "args": {"table": "arr_by_line", "region": "EU"}, "observation": "Hiring Copilot $14M EU ARR, Credit Scoring $4M, Content Mod $2M."},
                {"tool": "docs.coverage", "args": {"requirement": "instructions_for_use"}, "observation": "Hiring Copilot at 40% coverage, Credit Scoring 75%, Content Mod 90%."},
            ],
            "answer": "Hiring Copilot is the biggest exposure: $14M in EU ARR, classified high-risk, and only 40% covered on Article 13's instructions-for-use requirement. Credit Scoring is smaller ($4M) but better prepared (75%). Content Mod is near-ready. Priority is a Hiring Copilot remediation plan before the Aug 2026 enforcement date — ~$14M ARR at risk if we miss.",
            "citations": [
                {"source": "Compliance map · EU AI Act", "time": "v2026.03"},
                {"source": "Product risk register", "time": "current"},
                {"source": "Snowflake · arr_by_line", "time": "MTD"},
                {"source": "Docs coverage tracker", "time": "live"},
            ],
        },
        "zh": {
            "plan": "把产品线对照风险等级，匹配第 13 条透明度义务，按欧盟营收暴露排序。",
            "steps": [
                {"tool": "compliance.map", "args": {"regulation": "eu_ai_act", "article": "13"}, "observation": "第 13 条 = 高风险系统的透明度与使用说明。"},
                {"tool": "product.risk_register", "args": {}, "observation": "3 条高风险：招聘 Copilot、信用评分 API、内容审核。"},
                {"tool": "snowflake.query", "args": {"table": "arr_by_line", "region": "EU"}, "observation": "招聘 Copilot 欧盟 ARR $14M，信用评分 $4M，内容审核 $2M。"},
                {"tool": "docs.coverage", "args": {"requirement": "instructions_for_use"}, "observation": "招聘 Copilot 覆盖 40%，信用评分 75%，内容审核 90%。"},
            ],
            "answer": "暴露最大的是招聘 Copilot：欧盟 ARR $14M，高风险，第 13 条「使用说明」仅覆盖 40%。信用评分营收较小（$4M）但准备更好（75%）。内容审核接近达标。建议：在 2026 年 8 月执行日期前为招聘 Copilot 启动合规修补计划——不然 $14M ARR 面临风险。",
            "citations": [
                {"source": "合规映射 · 欧盟 AI 法案", "time": "v2026.03"},
                {"source": "产品风险注册表", "time": "当前"},
                {"source": "Snowflake · arr_by_line", "time": "月初至今"},
                {"source": "文档覆盖看板", "time": "实时"},
            ],
        },
    },
    {
        "id": "candidate-poach",
        "keywords_en": ["candidate", "poach", "linkedin", "competitor x", "hiring loss"],
        "keywords_zh": ["候选人", "挖角", "linkedin", "流失候选人"],
        "chip_en": "After Competitor X's launch, how many candidates did we lose on LinkedIn?",
        "chip_zh": "竞品 X 发布后，我们在 LinkedIn 上流失了多少候选人？",
        "dept": {"en": "Recruiting", "zh": "招聘"},
        "en": {
            "plan": "Count open reqs whose candidates updated 'Competitor X' in their LinkedIn profile or responded to their recruiters in the 14 days post-launch.",
            "steps": [
                {"tool": "gem.pipeline_state", "args": {"range": "14d", "stage": "final+offer"}, "observation": "Of 38 candidates in final or offer stage: 6 dropped or declined."},
                {"tool": "linkedin.profile_diff", "args": {"ids": ["..."]}, "observation": "4 of 6 added Competitor X as new employer this week."},
                {"tool": "email.reply_intent", "args": {"domain": "competitorx.ai"}, "observation": "11 additional active pipeline candidates replied to Competitor X recruiters."},
                {"tool": "gem.offer_accept_rate", "args": {"range": "30d"}, "observation": "Offer accept dropped 82% → 71% post-launch."},
            ],
            "answer": "We directly lost 4 candidates to Competitor X in the 14 days after their launch (6 drops total, 4 confirmed to them on LinkedIn). Another 11 active pipeline candidates are engaging with their recruiters. Offer accept rate fell from 82% to 71% in the same window. Recommend an immediate counter-packet with updated equity refresh for any candidate at final/offer stage.",
            "citations": [
                {"source": "Gem · pipeline state", "time": "14d"},
                {"source": "LinkedIn · profile diffs", "time": "14d"},
                {"source": "Gmail · recruiter reply intents", "time": "14d"},
                {"source": "Gem · offer accept rate", "time": "30d"},
            ],
        },
        "zh": {
            "plan": "统计发布后 14 天内，候选人在 LinkedIn 上更新为「竞品 X」或回复其招聘者的数量。",
            "steps": [
                {"tool": "gem.pipeline_state", "args": {"range": "14d", "stage": "final+offer"}, "observation": "终面 / offer 阶段 38 人中 6 人放弃或拒 offer。"},
                {"tool": "linkedin.profile_diff", "args": {"ids": ["..."]}, "observation": "6 人中 4 人本周将新雇主更新为竞品 X。"},
                {"tool": "email.reply_intent", "args": {"domain": "competitorx.ai"}, "observation": "另有 11 位在途候选人回复了竞品 X 招聘者。"},
                {"tool": "gem.offer_accept_rate", "args": {"range": "30d"}, "observation": "offer 接受率从 82% 降到 71%。"},
            ],
            "answer": "竞品 X 发布后 14 天内，我们直接流失 4 位候选人给他们（共 6 人放弃，4 人在 LinkedIn 上确认入职竞品 X）；另有 11 位在途候选人在跟他们沟通。同期 offer 接受率从 82% 降到 71%。建议：对终面 / offer 阶段候选人立即启动留任方案（股权刷新）。",
            "citations": [
                {"source": "Gem · 管道状态", "time": "14 天"},
                {"source": "LinkedIn · 资料变更", "time": "14 天"},
                {"source": "Gmail · 招聘者回复意向", "time": "14 天"},
                {"source": "Gem · offer 接受率", "time": "30 天"},
            ],
        },
    },
]


def _match_ask_preset(q_lower: str, lang: str) -> dict[str, Any] | None:
    best = None
    best_hits = 0
    for preset in _ASK_PRESETS:
        kws = preset["keywords_zh"] if lang == "zh" else preset["keywords_en"]
        hits = sum(1 for kw in kws if kw in q_lower)
        if hits > best_hits:
            best_hits = hits
            best = preset
    if best_hits < 1:
        return None
    body = best["zh" if lang == "zh" else "en"]
    return {
        "matched_preset": best["id"],
        "department": best["dept"]["zh" if lang == "zh" else "en"],
        "plan": body["plan"],
        "steps": [dict(s) for s in body["steps"]],
        "answer": body["answer"],
        "citations": [dict(c) for c in body["citations"]],
    }


def ask_chips(lang: str = "en") -> list[dict[str, str]]:
    """Demo question chips grouped by department — shown on the dashboard."""
    lang = lang if lang in ("en", "zh") else "en"
    return [{"id": p["id"], "dept": p["dept"][lang], "q": p["chip_zh" if lang == "zh" else "chip_en"]} for p in _ASK_PRESETS]


def _generic_ask_trace(query: str, lang: str) -> dict[str, Any]:
    if lang == "zh":
        return {
            "matched_preset": None,
            "department": "跨部门",
            "plan": "把问题分解为子查询，并行调用 3-4 个系统，再综合结果。",
            "steps": [
                {"tool": "snowflake.query", "args": {"question": query[:80]}, "observation": "检索到 12 个候选数据点，保留前 3。"},
                {"tool": "slack.search", "args": {"q": query[:40]}, "observation": "过去 7 天相关讨论 8 条。"},
                {"tool": "lattice.lookup", "args": {"topic": query[:40]}, "observation": "相关人员与 OKR 3 条。"},
                {"tool": "synthesize.answer", "args": {}, "observation": "交叉比对后整合成答案。"},
            ],
            "answer": "这是一个演示 Agent：问题未命中预置 demo，已并行调用 3 个系统给出通用回答。可尝试下方预置问题以看到完整多工具追踪与引用。",
            "citations": [
                {"source": "Snowflake", "time": "实时"},
                {"source": "Slack", "time": "7 天"},
                {"source": "Lattice", "time": "当前"},
            ],
        }
    return {
        "matched_preset": None,
        "department": "Cross-functional",
        "plan": "Decompose the question into sub-queries, call 3-4 systems in parallel, synthesize.",
        "steps": [
            {"tool": "snowflake.query", "args": {"question": query[:80]}, "observation": "12 candidate data points retrieved; kept top 3."},
            {"tool": "slack.search", "args": {"q": query[:40]}, "observation": "8 relevant threads in the past 7 days."},
            {"tool": "lattice.lookup", "args": {"topic": query[:40]}, "observation": "3 related people and OKRs."},
            {"tool": "synthesize.answer", "args": {}, "observation": "Cross-referenced and composed answer."},
        ],
        "answer": "This is a demo Agent: your question didn't match a preset, so I ran a generic 3-system lookup. Try one of the preset chips below to see a full multi-tool trace with specific numbers and cited sources.",
        "citations": [
            {"source": "Snowflake", "time": "live"},
            {"source": "Slack", "time": "7d"},
            {"source": "Lattice", "time": "current"},
        ],
    }


# ============================================================
# Active projects — macro rollup + drill-down detail
# ============================================================

_PROJECTS: list[dict[str, Any]] = [
    {
        "id": "mao-v2",
        "owner": "Priya R.",
        "status": "yellow",
        "progress": 72,
        "budget": {"spent": 1.2, "total": 2.0, "unit": "$M"},
        "en": {
            "name": "Multi-Agent Orchestration v2",
            "dept": "Engineering",
            "eta": "3 weeks",
            "macro": "API rewrite shipped; reliability blockers on long tool-chains delay GA.",
            "milestones": [
                {"title": "API v2 design freeze", "status": "done", "date": "Feb 12"},
                {"title": "Public beta", "status": "done", "date": "Mar 28"},
                {"title": "Context-preserving tool chain (>5 calls)", "status": "in_progress", "date": "Apr 24"},
                {"title": "GA — $2M new ARR target", "status": "pending", "date": "May 15"},
            ],
            "blockers": [
                {"severity": "high", "text": "Agent loses context after the 5th tool call — 9 open P1 bugs (oldest 11d)."},
                {"severity": "medium", "text": "Throughput on streaming endpoint is 30% below SLO."},
            ],
            "activity": [
                {"when": "today 11:04", "what": "PR #4812 merged: rework tool-state serializer", "source": "GitHub"},
                {"when": "yesterday",    "what": "War room convened — CS escalated 3 enterprise complaints", "source": "Slack #war-room-mao"},
                {"when": "2 days ago",  "what": "Linear P1 MAO-221 demoted to P2 after root-cause found", "source": "Linear"},
            ],
            "next_actions": [
                "Pair Marcus K. onto MAO-219 to unblock context chain by Friday",
                "Carve out 2 SRE days for streaming-endpoint perf",
            ],
            "key_metrics": [
                {"label": "Open P1 bugs", "value": "9"},
                {"label": "CSAT on beta", "value": "6.8 / 10"},
                {"label": "Pipeline tied to GA", "value": "$8.4M"},
            ],
        },
        "zh": {
            "name": "多 Agent 编排 v2",
            "dept": "工程",
            "eta": "3 周",
            "macro": "API 重写已上线；长工具链可靠性阻塞 GA 发布。",
            "milestones": [
                {"title": "API v2 设计冻结", "status": "done", "date": "2 月 12 日"},
                {"title": "公开 Beta", "status": "done", "date": "3 月 28 日"},
                {"title": "工具链上下文保持（>5 次调用）", "status": "in_progress", "date": "4 月 24 日"},
                {"title": "GA ——$2M 新增 ARR 目标", "status": "pending", "date": "5 月 15 日"},
            ],
            "blockers": [
                {"severity": "high", "text": "第 5 次工具调用后上下文丢失 —— 9 个 P1 bug 未修（最久 11 天）。"},
                {"severity": "medium", "text": "流式端点吞吐低于 SLO 30%。"},
            ],
            "activity": [
                {"when": "今天 11:04", "what": "PR #4812 已合入：重写 tool-state 序列化器", "source": "GitHub"},
                {"when": "昨天",       "what": "作战室开会 —— CS 升级了 3 个企业投诉", "source": "Slack #war-room-mao"},
                {"when": "2 天前",     "what": "Linear P1 MAO-221 在定位根因后降级为 P2", "source": "Linear"},
            ],
            "next_actions": [
                "安排 Marcus K. 配对 MAO-219，周五前解锁上下文链",
                "预留 2 人天 SRE 处理流式端点性能",
            ],
            "key_metrics": [
                {"label": "未修 P1 bug", "value": "9"},
                {"label": "Beta CSAT", "value": "6.8 / 10"},
                {"label": "GA 绑定管道", "value": "$8.4M"},
            ],
        },
    },
    {
        "id": "apac-gpu",
        "owner": "Diego M.",
        "status": "red",
        "progress": 42,
        "budget": {"spent": 3.8, "total": 9.5, "unit": "$M"},
        "en": {
            "name": "APAC GPU Expansion (Singapore)",
            "dept": "Infrastructure",
            "eta": "6 weeks (slipped 2wk)",
            "macro": "Blocked on H100 allocation from vendor; APAC churn already costing $2.3M ARR.",
            "milestones": [
                {"title": "Site selection + power contract", "status": "done", "date": "Jan 20"},
                {"title": "Hardware PO placed (240× H100)", "status": "done", "date": "Feb 28"},
                {"title": "Rack & stack first 80 nodes", "status": "in_progress", "date": "Apr 30"},
                {"title": "Production traffic cutover", "status": "pending", "date": "Jun 06"},
            ],
            "blockers": [
                {"severity": "high", "text": "Vendor slipped 160× H100 delivery to late May (original: Apr 5)."},
                {"severity": "medium", "text": "Interconnect certification open with regulator, 3-week typical."},
            ],
            "activity": [
                {"when": "this morning", "what": "Escalation call with vendor CEO; offered 80-unit early partial on Apr 22", "source": "Gmail"},
                {"when": "yesterday",    "what": "Datadog: APAC p99 still 2.8s, unchanged WoW", "source": "Datadog"},
                {"when": "3 days ago",   "what": "Singapore power contract signed, 30MW reserved", "source": "DocuSign"},
            ],
            "next_actions": [
                "Accept partial 80-unit delivery Apr 22 to start traffic draining by May 10",
                "Trigger contractual penalty clause on late 160-unit shipment",
            ],
            "key_metrics": [
                {"label": "APAC p99 latency", "value": "2.8s"},
                {"label": "APAC ARR at risk", "value": "$6.1M"},
                {"label": "Spend vs budget", "value": "$3.8M / $9.5M"},
            ],
        },
        "zh": {
            "name": "APAC GPU 扩容（新加坡）",
            "dept": "基础设施",
            "eta": "6 周（延期 2 周）",
            "macro": "供应商 H100 到货延期卡主；APAC 流失已损失 $2.3M ARR。",
            "milestones": [
                {"title": "选址 + 电力合同", "status": "done", "date": "1 月 20 日"},
                {"title": "硬件下单（240× H100）", "status": "done", "date": "2 月 28 日"},
                {"title": "前 80 节点上架", "status": "in_progress", "date": "4 月 30 日"},
                {"title": "生产流量切换", "status": "pending", "date": "6 月 6 日"},
            ],
            "blockers": [
                {"severity": "high", "text": "供应商将 160× H100 延至 5 月底（原定 4 月 5 日）。"},
                {"severity": "medium", "text": "互联认证在监管侧待批，通常 3 周。"},
            ],
            "activity": [
                {"when": "今早",   "what": "与供应商 CEO 升级会；对方承诺 4 月 22 日先发 80 单元", "source": "Gmail"},
                {"when": "昨天",   "what": "Datadog：APAC p99 仍 2.8 秒，周环比持平", "source": "Datadog"},
                {"when": "3 天前", "what": "新加坡电力合同签订，预留 30MW", "source": "DocuSign"},
            ],
            "next_actions": [
                "接受 4 月 22 日 80 单元先发，5 月 10 日起逐步导流",
                "对 160 单元延期触发合同违约条款",
            ],
            "key_metrics": [
                {"label": "APAC p99 延迟", "value": "2.8 秒"},
                {"label": "APAC 风险 ARR", "value": "$6.1M"},
                {"label": "支出 / 预算", "value": "$3.8M / $9.5M"},
            ],
        },
    },
    {
        "id": "eu-ai-act",
        "owner": "Lena S.",
        "status": "yellow",
        "progress": 38,
        "budget": {"spent": 0.4, "total": 1.1, "unit": "$M"},
        "en": {
            "name": "Hiring Copilot — EU AI Act compliance",
            "dept": "Legal / Product",
            "eta": "10 weeks (Aug enforcement)",
            "macro": "Instructions-for-use coverage 40%; on track but narrow. $14M EU ARR at stake.",
            "milestones": [
                {"title": "Risk classification signed off", "status": "done", "date": "Mar 10"},
                {"title": "Technical documentation draft", "status": "in_progress", "date": "May 01"},
                {"title": "Notified body pre-assessment", "status": "pending", "date": "Jun 20"},
                {"title": "Enforcement readiness", "status": "pending", "date": "Aug 02"},
            ],
            "blockers": [
                {"severity": "medium", "text": "Need 2 technical writers; open req stalled in People for 3 weeks."},
            ],
            "activity": [
                {"when": "today",      "what": "Notion doc 'HC-AI-Act-v3' updated by Priya R., +1,200 words", "source": "Notion"},
                {"when": "2 days ago", "what": "Compliance tracker: coverage 40% (+8% WoW)", "source": "Internal tracker"},
            ],
            "next_actions": [
                "Unblock tech-writer reqs — escalate to Head of People",
                "Schedule Bundesagentur walkthrough for week of May 13",
            ],
            "key_metrics": [
                {"label": "Instructions-for-use coverage", "value": "40%"},
                {"label": "EU ARR at risk", "value": "$14M"},
                {"label": "Days to enforcement", "value": "106"},
            ],
        },
        "zh": {
            "name": "招聘 Copilot — 欧盟 AI 法案合规",
            "dept": "法务 / 产品",
            "eta": "10 周（8 月生效）",
            "macro": "使用说明覆盖 40%，按进度可达标但留白不多。$14M 欧盟 ARR 暴露。",
            "milestones": [
                {"title": "风险分级签字", "status": "done", "date": "3 月 10 日"},
                {"title": "技术文档草稿", "status": "in_progress", "date": "5 月 1 日"},
                {"title": "指定机构预评估", "status": "pending", "date": "6 月 20 日"},
                {"title": "执法日就绪", "status": "pending", "date": "8 月 2 日"},
            ],
            "blockers": [
                {"severity": "medium", "text": "需要 2 名技术写手，招聘编制在 People 卡住 3 周。"},
            ],
            "activity": [
                {"when": "今天",   "what": "Notion 文档 HC-AI-Act-v3 由 Priya R. 更新，+1,200 字", "source": "Notion"},
                {"when": "2 天前", "what": "合规看板：覆盖 40%（周环比 +8%）", "source": "内部看板"},
            ],
            "next_actions": [
                "打通技术写手编制 —— 升级至 People 负责人",
                "约 Bundesagentur 在 5 月 13 日当周走查",
            ],
            "key_metrics": [
                {"label": "使用说明覆盖", "value": "40%"},
                {"label": "风险欧盟 ARR", "value": "$14M"},
                {"label": "距执法日", "value": "106 天"},
            ],
        },
    },
    {
        "id": "ent-ga",
        "owner": "Rahul K.",
        "status": "green",
        "progress": 88,
        "budget": {"spent": 1.6, "total": 2.0, "unit": "$M"},
        "en": {
            "name": "Enterprise Tier GA",
            "dept": "Product",
            "eta": "2 weeks",
            "macro": "All launch gates green; 14 design-partner logos ready to convert on day 1.",
            "milestones": [
                {"title": "Design partner program", "status": "done", "date": "Q1"},
                {"title": "SOC 2 Type II report", "status": "done", "date": "Mar 15"},
                {"title": "Pricing + packaging locked", "status": "done", "date": "Apr 05"},
                {"title": "GA launch event", "status": "in_progress", "date": "May 02"},
            ],
            "blockers": [{"severity": "low", "text": "Last-mile billing-proration bug, fix in flight."}],
            "activity": [
                {"when": "today",       "what": "Marketing site sign-off from Brand team", "source": "Figma"},
                {"when": "3 days ago",  "what": "Sales enablement complete — 100% AE attestation", "source": "Highspot"},
            ],
            "next_actions": [
                "Confirm press embargo lift time with 4 launch partners",
                "Pre-populate 14 design-partner upgrade quotes in Salesforce",
            ],
            "key_metrics": [
                {"label": "Design partners committed", "value": "14"},
                {"label": "Day-1 ARR commit", "value": "$4.2M"},
                {"label": "Runbook steps passed", "value": "47 / 48"},
            ],
        },
        "zh": {
            "name": "企业版 GA",
            "dept": "产品",
            "eta": "2 周",
            "macro": "所有发布闸门绿灯；14 个设计合作客户准备在 Day 1 转正。",
            "milestones": [
                {"title": "设计合作计划", "status": "done", "date": "Q1"},
                {"title": "SOC 2 Type II", "status": "done", "date": "3 月 15 日"},
                {"title": "定价包装锁定", "status": "done", "date": "4 月 5 日"},
                {"title": "GA 发布活动", "status": "in_progress", "date": "5 月 2 日"},
            ],
            "blockers": [{"severity": "low", "text": "末端计费按比例分摊 bug 修复中。"}],
            "activity": [
                {"when": "今天",   "what": "品牌组批准 Marketing 站点", "source": "Figma"},
                {"when": "3 天前", "what": "销售赋能完成 —— AE 100% 应试", "source": "Highspot"},
            ],
            "next_actions": [
                "与 4 家发布伙伴确认新闻禁运解除时间",
                "在 Salesforce 预置 14 份设计合作升级报价",
            ],
            "key_metrics": [
                {"label": "承诺设计合作客户", "value": "14"},
                {"label": "Day 1 承诺 ARR", "value": "$4.2M"},
                {"label": "Runbook 步骤通过", "value": "47 / 48"},
            ],
        },
    },
    {
        "id": "series-d",
        "owner": "Mei H. (CFO)",
        "status": "green",
        "progress": 55,
        "budget": {"spent": 0.3, "total": 0.8, "unit": "$M"},
        "en": {
            "name": "Series D — $220M target",
            "dept": "Finance / CEO",
            "eta": "8 weeks to term sheet",
            "macro": "3 lead term sheets expected by May 30; interest strongest at $2.4B pre.",
            "milestones": [
                {"title": "Deck + data room ready", "status": "done", "date": "Mar 01"},
                {"title": "First-round partner meetings", "status": "done", "date": "Apr 12"},
                {"title": "Second-round + diligence", "status": "in_progress", "date": "May 10"},
                {"title": "Term sheet selection", "status": "pending", "date": "May 30"},
            ],
            "blockers": [{"severity": "low", "text": "Legal wants updated Hiring Copilot EU risk memo before final diligence."}],
            "activity": [
                {"when": "today",       "what": "Sequoia partner meeting #2 went 45 min over; positive signal", "source": "Calendar"},
                {"when": "2 days ago",  "what": "Data room access granted to 2 new firms", "source": "Shareworks"},
            ],
            "next_actions": [
                "Publish updated EU AI Act memo by Apr 24 (unblocks diligence)",
                "Close competitive pricing refresh for April MRR in model",
            ],
            "key_metrics": [
                {"label": "Firms in active diligence", "value": "6"},
                {"label": "Indicative pre-money range", "value": "$2.0B–$2.6B"},
                {"label": "Target close", "value": "Jun 30"},
            ],
        },
        "zh": {
            "name": "D 轮融资 —— $220M 目标",
            "dept": "财务 / CEO",
            "eta": "8 周到 term sheet",
            "macro": "预期 5 月 30 日前收到 3 份领投 term sheet；$2.4B pre 估值反馈最强。",
            "milestones": [
                {"title": "BP + data room 就绪", "status": "done", "date": "3 月 1 日"},
                {"title": "首轮合伙人会议", "status": "done", "date": "4 月 12 日"},
                {"title": "二轮 + 尽调", "status": "in_progress", "date": "5 月 10 日"},
                {"title": "term sheet 选择", "status": "pending", "date": "5 月 30 日"},
            ],
            "blockers": [{"severity": "low", "text": "法务需更新招聘 Copilot 欧盟风险备忘才进入最终尽调。"}],
            "activity": [
                {"when": "今天",   "what": "红杉二次合伙人会超时 45 分钟，积极信号", "source": "日历"},
                {"when": "2 天前", "what": "Data room 已向 2 家新机构开放", "source": "Shareworks"},
            ],
            "next_actions": [
                "4 月 24 日前发布更新欧盟 AI 法案备忘（解锁尽调）",
                "将 4 月 MRR 的竞争定价刷新入模型",
            ],
            "key_metrics": [
                {"label": "尽调中机构数", "value": "6"},
                {"label": "指示 pre-money 区间", "value": "$2.0B–$2.6B"},
                {"label": "目标关账", "value": "6 月 30 日"},
            ],
        },
    },
    {
        "id": "comp-x-counter",
        "owner": "Jordan T.",
        "status": "yellow",
        "progress": 45,
        "budget": {"spent": 0.2, "total": 0.6, "unit": "$M"},
        "en": {
            "name": "Competitor X counter-launch",
            "dept": "Marketing / Product Marketing",
            "eta": "3 weeks",
            "macro": "Narrative locked; waiting on one feature to credibly claim parity + advantage.",
            "milestones": [
                {"title": "Competitive teardown report", "status": "done", "date": "Apr 02"},
                {"title": "Positioning + messaging v2", "status": "done", "date": "Apr 10"},
                {"title": "Parity feature GA (depends on MAO v2)", "status": "in_progress", "date": "May 08"},
                {"title": "Counter-launch blog + press", "status": "pending", "date": "May 12"},
            ],
            "blockers": [
                {"severity": "medium", "text": "Depends on MAO v2 GA landing by May 8 — currently yellow."},
            ],
            "activity": [
                {"when": "today",       "what": "LinkedIn: 4 design partners signaled willingness to quote in launch", "source": "LinkedIn Sales Navigator"},
                {"when": "yesterday",  "what": "Analyst briefing with Forrester scheduled May 09", "source": "Calendar"},
            ],
            "next_actions": [
                "Align launch date with MAO v2 GA (hard dependency)",
                "Lock 3 customer quotes for press by May 05",
            ],
            "key_metrics": [
                {"label": "Press relationships briefed", "value": "11"},
                {"label": "Analyst meetings booked", "value": "4"},
                {"label": "Pipeline tied to counter", "value": "$5.8M"},
            ],
        },
        "zh": {
            "name": "竞品 X 反击发布",
            "dept": "市场 / 产品市场",
            "eta": "3 周",
            "macro": "叙事已锁定；等一项对等功能落地后可发声。",
            "milestones": [
                {"title": "竞品拆解报告", "status": "done", "date": "4 月 2 日"},
                {"title": "定位 + 信息 v2", "status": "done", "date": "4 月 10 日"},
                {"title": "对等功能 GA（依赖 MAO v2）", "status": "in_progress", "date": "5 月 8 日"},
                {"title": "反击发布博客 + 公关", "status": "pending", "date": "5 月 12 日"},
            ],
            "blockers": [
                {"severity": "medium", "text": "强依赖 MAO v2 GA 在 5 月 8 日前落地 —— 当前黄灯。"},
            ],
            "activity": [
                {"when": "今天",     "what": "LinkedIn：4 个设计合作客户愿意为发布引述", "source": "LinkedIn Sales Navigator"},
                {"when": "昨天",     "what": "与 Forrester 分析师简报定在 5 月 9 日", "source": "日历"},
            ],
            "next_actions": [
                "发布日期与 MAO v2 GA 绑定（硬依赖）",
                "5 月 5 日前锁定 3 条客户引言用于公关",
            ],
            "key_metrics": [
                {"label": "已简报媒体关系", "value": "11"},
                {"label": "已约分析师", "value": "4"},
                {"label": "绑定管道", "value": "$5.8M"},
            ],
        },
    },
]


def _project_summary(p: dict[str, Any], lang: str) -> dict[str, Any]:
    body = p["zh" if lang == "zh" else "en"]
    return {
        "id": p["id"],
        "name": body["name"],
        "dept": body["dept"],
        "owner": p["owner"],
        "status": p["status"],
        "progress": p["progress"],
        "eta": body["eta"],
        "macro": body["macro"],
        "budget": dict(p["budget"]),
    }


def _project_detail(p: dict[str, Any], lang: str) -> dict[str, Any]:
    body = p["zh" if lang == "zh" else "en"]
    return {
        "id": p["id"],
        "name": body["name"],
        "dept": body["dept"],
        "owner": p["owner"],
        "status": p["status"],
        "progress": p["progress"],
        "eta": body["eta"],
        "macro": body["macro"],
        "budget": dict(p["budget"]),
        "milestones": [dict(m) for m in body["milestones"]],
        "blockers": [dict(b) for b in body["blockers"]],
        "activity": [dict(a) for a in body["activity"]],
        "next_actions": list(body["next_actions"]),
        "key_metrics": [dict(m) for m in body["key_metrics"]],
    }

