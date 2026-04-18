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
        arr_val = 80 + r.randint(0, 120)  # $M
        headcount = 500 + r.randint(0, 4000)
        nrr = 100 + r.randint(5, 40)
        enps = r.randint(20, 60)
        burn = round(0.8 + r.random() * 1.4, 1)
        runway = r.randint(14, 36)
        arr_change = f"+{r.randint(8, 25)}% QoQ"
        # 12-month ARR series ending at arr_val
        start = max(40, arr_val - r.randint(40, 80))
        step = (arr_val - start) / 11
        series_arr = [round(start + step * i, 1) for i in range(12)]
        target_end = round(arr_val * 1.25, 0)
        target_start = round(start * 1.08, 0)
        tstep = (target_end - target_start) / 11
        series_target = [round(target_start + tstep * i, 1) for i in range(12)]
        # Radar 0-10 per dept
        depts = _DEPTS_EN if lang == "en" else _DEPTS_ZH
        radar_current = [round(6 + r.random() * 3.5, 1) for _ in depts]
        radar_prev = [max(0, round(v - 0.3 + r.random() * 0.8, 1)) for v in radar_current]

        return {
            "company": self.company,
            "arr": f"${arr_val}M",
            "arr_change": arr_change,
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
                "labels": ["May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"],
                "arr": series_arr,
                "target": series_target,
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
