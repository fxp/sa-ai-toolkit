#!/usr/bin/env python3.11
"""
Enterprise AI Architecture Generator
企业AI演示方案生成器
=======================================
输入：企业画像 (profile.json)
输出：DEMO总表.md + RUNBOOK.md + newco_crew.py + narrative.md

用法：
  python3.11 generator.py --interactive
  python3.11 generator.py --company "招商银行" --industry "banking-finance" --pain-points "A,D,E,G" --minutes 90
  python3.11 generator.py --profile outputs/cmb-bank/profile.json
  python3.11 generator.py --profile outputs/cmb-bank/profile.json --preview
"""

import os, sys, json, re, argparse, textwrap
from pathlib import Path
from datetime import datetime

# ── 路径 ──
ROOT       = Path(__file__).parent.resolve()
DEMO_LIB   = ROOT / "demo-library"
IND_PAT    = ROOT / "industry-patterns"
OUTPUTS    = ROOT / "outputs"

# ── API ──
BIGMODEL_KEY = os.getenv("BIGMODEL_API_KEY", "1790d449b46d437bbc8b101815048d64.lEMGH4tememSXbvH")

# ══════════════════════════════════════════════════
# 评分引擎
# ══════════════════════════════════════════════════

# 痛点代码 → Demo评分加成 (demo_id: bonus_score)
PAIN_BONUS: dict[str, dict[str, int]] = {
    "A": {"01": 3, "02": 2, "05": 2, "06": 2, "10": 2},
    "B": {"01": 3, "04": 2, "07": 2, "08": 2},
    "C": {"07": 3, "04": 2, "08": 2, "13": 2},
    "D": {"02": 3, "06": 2, "08": 1},
    "E": {"04": 3, "07": 2, "09": 2, "13": 3},
    "F": {"07": 3, "09": 2, "13": 2},
    "G": {"04": 2, "05": 3, "13": 2},
    "H": {"08": 3, "09": 2, "14": 2},
    "I": {"06": 3, "09": 3, "02": 1},
    "J": {"01": 3, "03": 3},
    "K": {"05": 3, "11": 2, "12": 2, "10": 1},
    "L": {"05": 3, "06": 2, "11": 1},
    "M": {"03": 2, "11": 3, "12": 3},
}

# 行业匹配度（行业关键词 → Demo默认匹配分）
INDUSTRY_BOOST: dict[str, dict[str, int]] = {
    "banking-finance":    {"05": 2, "02": 2, "07": 2, "04": 1, "06": 1},
    "manufacturing":      {"03": 2, "02": 2, "04": 2, "05": 1, "11": 1},
    "aerospace-defense":  {"02": 3, "03": 2, "05": 2, "06": 2, "07": 2, "09": 1},
    "healthcare":         {"02": 3, "05": 2, "06": 2, "09": 2},
    "retail-ecommerce":   {"05": 3, "07": 2, "04": 2, "01": 1},
    "consulting-research":{"09": 3, "06": 3, "08": 2, "02": 2},
    "logistics":          {"01": 3, "04": 2, "05": 2, "13": 2},
    "real-estate":        {"10": 2, "06": 2, "07": 2, "02": 1},
    "energy":             {"04": 3, "05": 2, "03": 2, "01": 2},
    "tech-software":      {"03": 3, "08": 3, "11": 3, "12": 2, "14": 2},
}

# 基础冲击力分数（所有行业通用）
BASE_IMPACT = {
    "01": 6, "02": 8, "03": 5, "04": 9, "05": 8,
    "06": 6, "07": 9, "08": 7, "09": 7, "10": 10,
    "11": 5, "12": 5, "13": 9, "14": 7,
}

MUST_INCLUDE = {"02", "05", "10"}   # 任何企业必选

DEMO_NAMES = {
    "01": "MCP工具编排",     "02": "Karpathy知识库",  "03": "遗留代码迁移",
    "04": "指挥/CEO看板",   "05": "AI监督员",         "06": "智能阅读标注",
    "07": "多Agent辩论",    "08": "一人军团",          "09": "AutoResearch科研",
    "10": "品牌PPT生成",    "11": "前端自动化测试",   "12": "移动端自动化测试",
    "13": "群体智能推演",   "14": "Ralph自主迭代",
}

DEMO_ACTS = {
    "01": 1, "14": 1,
    "02": 2, "03": 2,
    "04": 3, "05": 3, "06": 3,
    "07": 4, "08": 4, "09": 4, "10": 4,
    "11": 4, "12": 4, "13": 4,
}

DEMO_MODES = {
    "01": "embedded", "14": "embedded",
    "02": "embedded", "03": "embedded",
    "04": "embedded", "05": "embedded", "06": "embedded",
    "07": "standalone", "08": "standalone", "09": "standalone", "10": "standalone",
    "11": "backup", "12": "backup", "13": "backup",
}

# ══════════════════════════════════════════════════
# 核心函数
# ══════════════════════════════════════════════════

def score_demos(profile: dict) -> list[dict]:
    """对14个Demo评分，返回排序后的列表"""
    industry = profile.get("industry", "")
    pain_points = profile.get("pain_points", [])
    offline_req = profile.get("offline_required", False)

    scores = []
    for did in [f"{i:02d}" for i in range(1, 15)]:
        # 痛点匹配分 (40%)
        pain_score = 0
        for pp in pain_points:
            pain_score += PAIN_BONUS.get(pp, {}).get(did, 0)
        pain_score = min(pain_score, 10)

        # 行业匹配分 (40%)
        ind_score = INDUSTRY_BOOST.get(industry, {}).get(did, 0)
        # 必选Demo给满分行业分
        if did in MUST_INCLUDE:
            ind_score = max(ind_score, 5)

        # 冲击力分 (20%)
        impact = BASE_IMPACT.get(did, 5)

        # 离线惩罚
        offline_penalty = 0
        if offline_req:
            offline_map = {"01": -3, "06": -2, "07": -2, "09": -2, "13": -4}
            offline_penalty = offline_map.get(did, 0)

        total = (pain_score * 0.4 + ind_score * 0.4 + impact * 0.2) * 10 / 10
        total += offline_penalty

        # 必选加分
        if did in MUST_INCLUDE:
            total = max(total, 7.0)

        scores.append({
            "id": did,
            "name": DEMO_NAMES[did],
            "act": DEMO_ACTS[did],
            "mode": DEMO_MODES[did],
            "pain_score": round(pain_score, 1),
            "ind_score": round(ind_score, 1),
            "impact": impact,
            "total": round(total, 1),
            "must": did in MUST_INCLUDE,
            "offline": did in {"02", "03", "04", "05", "08", "10", "11", "12", "14"},
        })

    scores.sort(key=lambda x: (-x["must"], -x["total"]))
    return scores


def select_demos(scores: list[dict], target_count: int = 11) -> dict:
    """按嵌入/独立/备选分配Demo"""
    must = [s for s in scores if s["must"]]
    rest = [s for s in scores if not s["must"]]

    # 嵌入式: Act1(2个) + Act2(2个) + Act3(2-3个) = 6-7个
    embedded_pool = [s for s in rest if s["mode"] == "embedded"]
    standalone_pool = [s for s in rest if s["mode"] == "standalone"]
    backup_pool = [s for s in rest if s["mode"] == "backup"]

    # 选嵌入式（除必选外）
    embedded_sel = embedded_pool[:4]  # Act1和Act2各选2个
    # Act3: 必选中05已定，再选1-2个
    act3_extra = [s for s in embedded_pool if s["act"] == 3 and s["id"] not in {x["id"] for x in embedded_sel}]
    embedded_sel += act3_extra[:1]

    # 独立式: 选3个（07/08/09，10是必选）
    standalone_sel = standalone_pool[:3]

    # 备选: 选2个
    backup_sel = backup_pool[:2]

    selected = must + embedded_sel + standalone_sel
    selected = list({s["id"]: s for s in selected}.values())  # 去重

    return {
        "must": must,
        "embedded": [s for s in selected if s["mode"] == "embedded" and not s["must"]],
        "standalone": [s for s in selected if s["mode"] == "standalone" and not s["must"]],
        "backup": backup_sel,
        "all_selected": selected,
    }


def load_industry_pattern(industry: str) -> dict:
    """加载行业预置数据"""
    pat_file = IND_PAT / f"{industry}.json"
    if pat_file.exists():
        return json.loads(pat_file.read_text(encoding="utf-8"))
    return {}


def load_demo_template(demo_id: str) -> str:
    """加载Demo模板文件"""
    tpl_file = DEMO_LIB / f"{demo_id}-*.md"
    matches = list(DEMO_LIB.glob(f"{demo_id}-*.md"))
    if matches:
        return matches[0].read_text(encoding="utf-8")
    return ""


def fill_template(template: str, variables: dict) -> str:
    """用变量字典替换模板中的 {{占位符}}"""
    for key, val in variables.items():
        template = template.replace(f"{{{{{key}}}}}", str(val))
    return template


def glm_fill(prompt: str) -> str:
    """调用BigModel GLM生成内容"""
    try:
        import requests
        resp = requests.post(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            headers={"Authorization": f"Bearer {BIGMODEL_KEY}", "Content-Type": "application/json"},
            json={
                "model": "glm-4-flash",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
            },
            timeout=45,
        )
        return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"[GLM调用失败: {e}]"


# ══════════════════════════════════════════════════
# 生成各输出文件
# ══════════════════════════════════════════════════

def generate_score_report(scores: list[dict], selection: dict, profile: dict) -> str:
    """生成Demo评分报告"""
    company = profile.get("company_name", "企业")
    lines = [
        f"# {company} — Demo评分报告",
        f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"行业：{profile.get('industry_zh', profile.get('industry', ''))}",
        f"痛点：{', '.join(profile.get('pain_points', []))}",
        "\n## 评分明细\n",
        "| ID | 名称 | 痛点匹配(40%) | 行业匹配(40%) | 冲击力(20%) | 综合 | 必选 | 模式 | 入选 |",
        "|----|----|------------|------------|-----------|------|------|------|------|",
    ]
    selected_ids = {s["id"] for s in selection["all_selected"]}
    for s in sorted(scores, key=lambda x: x["id"]):
        sel = "✅" if s["id"] in selected_ids else "—"
        must = "⭐" if s["must"] else ""
        lines.append(
            f"| {s['id']} | {s['name']} | {s['pain_score']} | {s['ind_score']} | "
            f"{s['impact']} | **{s['total']}** | {must} | {s['mode']} | {sel} |"
        )
    lines += [
        "\n## 必选Demo (3个)",
        *[f"- **{s['id']} {s['name']}**：{s['mode']}" for s in selection["must"]],
        "\n## 优选嵌入式Demo",
        *[f"- {s['id']} {s['name']} (Act{s['act']})" for s in selection["embedded"]],
        "\n## 优选独立式Demo (Act 4)",
        *[f"- {s['id']} {s['name']}" for s in selection["standalone"]],
        "\n## 备选Demo",
        *[f"- {s['id']} {s['name']}" for s in selection["backup"]],
    ]
    return "\n".join(lines)


def generate_demo_table(selection: dict, profile: dict, pattern: dict) -> str:
    """生成DEMO总表.md"""
    company = profile.get("company_name", "企业")
    industry_zh = profile.get("industry_zh", profile.get("industry", ""))
    mins = profile.get("presentation_minutes", 90)
    scenarios = pattern.get("demo_scenarios", {})

    def get_sc(did: str, key: str) -> str:
        return scenarios.get(did, {}).get(key, f"[{key}]")

    # 构建选中Demo列表（按Act排序）
    all_sel = sorted(selection["all_selected"], key=lambda x: (x["act"], x["mode"] != "embedded"))
    embedded = [s for s in all_sel if s["mode"] == "embedded"]
    standalone = [s for s in all_sel if s["mode"] == "standalone"]
    backup = selection["backup"]

    lines = [
        f"# 📋 Demo总表 — {company}专版",
        f"\n> 行业：{industry_zh}  |  总时长：约{mins}分钟  |  生成：{datetime.now().strftime('%Y-%m-%d')}",
        "> 叙事主线：**技术 → 行业 → 工作 → 行动**\n",
        "## 总览\n",
        "| 序号 | Demo名称 | 模式 | 幕次 | 时长 |",
        "|------|---------|------|------|------|",
    ]
    for i, s in enumerate(all_sel, 1):
        mode_zh = "嵌入" if s["mode"] == "embedded" else "独立"
        dur = "2min" if s["mode"] == "embedded" else ("5min" if s["id"] in {"07","10"} else "3-4min")
        lines.append(f"| {chr(64+i)} | {s['name']} | {mode_zh} | Act {s['act']} | {dur} |")
    for i, s in enumerate(backup, 1):
        lines.append(f"| 备{i} | {s['name']} | 备选 | Act 4 | 2-3min |")

    # Act 1
    act1 = [s for s in embedded if s["act"] == 1]
    if act1:
        lines += ["\n---\n## ACT 1: 技术\n"]
        for s in act1:
            sc = scenarios.get(s["id"], {})
            lines += [
                f"### 【{s['id']}】{s['name']}",
                f"\n**触发点**：讲完AI范式转变时说——",
                f'\n> "现在证明。{sc.get("roleA", "员工")}一句话跨越{sc.get("systemA","系统A")}和{sc.get("systemB","系统B")}——"\n',
                "**核心价值**：" + DEMO_NAMES[s["id"]],
                "\n---\n",
            ]

    # Act 2
    act2 = [s for s in embedded if s["act"] == 2]
    if act2:
        lines += ["## ACT 2: 行业\n"]
        for s in act2:
            sc = scenarios.get(s["id"], {})
            lines += [
                f"### 【{s['id']}】{s['name']}",
                f"\n**触发点**：讲完行业冲击时说——",
                f'\n> "{sc.get("metaphor", "行业知识正在被重塑")}——我演示——"\n',
                "\n---\n",
            ]

    # Act 3
    act3 = [s for s in embedded if s["act"] == 3]
    if act3:
        lines += ["## ACT 3: 工作\n"]
        for s in act3:
            sc = scenarios.get(s["id"], {})
            lines += [
                f"### 【{s['id']}】{s['name']}",
                f"\n**触发点**：讲完工作变革时说——",
                f'\n> "{sc.get("role", "管理者")}的工作是怎么变的？——我演示——"\n',
                "\n---\n",
            ]

    # Act 4
    lines += ["## ACT 4: 行动\n"]
    for s in standalone:
        sc = scenarios.get(s["id"], {})
        lines += [
            f"### 【{s['id']}】{s['name']} · 独立演示",
            f"\n**开场白**：",
            f'> "{sc.get("topic", DEMO_NAMES[s["id"]] + "——演示开始")}"',
            "\n---\n",
        ]

    if backup:
        lines += ["## 备选Demo\n"]
        for s in backup:
            lines.append(f"- **{s['id']} {s['name']}**：时间充裕时加入")

    return "\n".join(lines)


def generate_runbook(selection: dict, profile: dict, pattern: dict) -> str:
    """生成RUNBOOK.md"""
    company = profile.get("company_name", "企业")
    audience = "、".join(profile.get("audience_roles", ["管理层"]))
    scenarios = pattern.get("demo_scenarios", {})

    lines = [
        f"# 🎬 {company} AI演示 RUNBOOK",
        f"\n受众：{audience}",
        f"生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "---\n",
        "## 演示前准备（提前30分钟）\n",
        "```bash",
        "# 1. 确认API Key",
        f'export BIGMODEL_API_KEY="{BIGMODEL_KEY}"',
        "",
        "# 2. 启动CrewAI编排脚本",
        "python3.11 newco_crew.py --list",
        "",
        "# 3. 预热各工具（各跑一次）",
        "python3.11 newco_crew.py --run-tool kb",
        "python3.11 newco_crew.py --run-tool dashboard",
        "python3.11 newco_crew.py --run-tool supervisor",
        "python3.11 newco_crew.py --run-tool ppt",
        "```\n",
        "---\n",
        "## 开场调查问题（破冰）\n",
    ]

    # 开场调查（基于受众定制）
    pain = profile.get("pain_points", [])
    q1 = "你每周有多少时间花在信息整理而不是决策上？" if "E" in pain else "你每天处理多少重复性文档工作？"
    q2 = "有没有因为找不到公司内部知识而重复造轮子？" if "D" in pain else "有没有因为跨部门协作效率低而延误项目？"
    q3 = "如果AI能帮你完成60%的重复工作，你愿意花多少时间学？"

    lines += [f'> 1. "{q1}"  → 让全场举手，记下比例', f'> 2. "{q2}"  → 建立共鸣', f'> 3. "{q3}"  → 引发期待\n', "---\n"]

    # 每个选中Demo的详细流程
    all_sel = sorted(selection["all_selected"], key=lambda x: (x["act"], x["id"]))
    for s in all_sel:
        sc = scenarios.get(s["id"], {})
        tpl = load_demo_template(s["id"])
        demo_name = s["name"]

        lines += [
            f"## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"## DEMO {s['id']}: {demo_name}",
            f"## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        ]

        # 开场白
        opener = sc.get("metaphor") or sc.get("topic") or f"演示{demo_name}的价值"
        lines += [f"### 📋 开场白（30秒）", f'> "{opener}——我演示一下"\n']

        # 企业专属场景
        lines += ["### 🏢 企业场景\n"]
        if sc:
            # 从场景数据中提取关键信息
            scene_parts = []
            for key in ["kbName", "dashName", "topic", "project"]:
                if sc.get(key):
                    scene_parts.append(sc[key])
            if scene_parts:
                lines.append(f"> **{company}场景**：{'，'.join(scene_parts[:2])}\n")

        # 演示流程
        lines += ["### 🎬 演示流程\n"]
        # 从模板中提取演示流程
        if "## 演示流程" in tpl:
            flow_start = tpl.index("## 演示流程")
            flow_end = tpl.index("## ", flow_start + 5) if "## " in tpl[flow_start + 5:] else len(tpl)
            flow_text = tpl[flow_start:flow_end].strip()
            # 替换通用变量为企业特定值
            for key, val in sc.items():
                flow_text = flow_text.replace(f"{{{{{key}}}}}", str(val))
            lines.append(flow_text)
        else:
            lines.append("*[参考demo-library模板]*\n")

        # WOW时刻和收尾
        if "## WOW时刻" in tpl:
            wow_start = tpl.index("## WOW时刻")
            wow_end = tpl.index("## ", wow_start + 5) if "## " in tpl[wow_start + 5:] else len(tpl)
            wow_text = tpl[wow_start:wow_end].strip()
            for key, val in sc.items():
                wow_text = wow_text.replace(f"{{{{{key}}}}}", str(val))
            lines += ["\n### ⭐ WOW时刻\n", wow_text]

        if "## 收尾金句" in tpl:
            outro_start = tpl.index("## 收尾金句")
            outro_end = tpl.index("## ", outro_start + 5) if "## " in tpl[outro_start + 5:] else len(tpl)
            outro = tpl[outro_start:outro_end].strip()
            for key, val in sc.items():
                outro = outro.replace(f"{{{{{key}}}}}", str(val))
            lines += ["\n### 💬 收尾语\n", outro]

        lines += ["\n### ⚠️ 备用方案", "如果演示失败：口头描述场景，展示预录截图。\n", "---\n"]

    # 答疑指南
    lines += [
        "## 答疑处理指南\n",
        "| 常见问题 | 回答框架 |",
        "|---------|---------|",
        "| AI会取代我们的工作吗？ | 取代的是重复性任务，创造的是监督员岗位。变化不是消失，是升级。 |",
        "| 数据安全怎么保证？ | 私有化部署+数据不出内网。NemoClaw安全框架5层防护。 |",
        "| 成本很高吧？ | API调用按需付费。GLM-4-Flash每千Token约0.01元。 |",
        "| 多久能见效？ | 知识库类：2周内。流程自动化：1个月内。战略价值：6-12个月。 |",
        "| 有没有失败案例？ | 失败通常是因为没有做好需求分析和数据准备，而不是AI本身的问题。 |",
    ]

    return "\n".join(lines)


def generate_crew_script(selection: dict, profile: dict, pattern: dict) -> str:
    """生成定制化的newco_crew.py"""
    company = profile.get("company_name", "企业")
    industry_zh = profile.get("industry_zh", "")
    scenarios = pattern.get("demo_scenarios", {})
    selected_ids = {s["id"] for s in selection["all_selected"]}

    # 从原始orchestrator读取基础代码
    orig = Path(__file__).parent.parent / "orchestrator" / "newco_crew.py"
    if orig.exists():
        base = orig.read_text(encoding="utf-8")
    else:
        base = ""

    # 构建企业专属Task描述
    tasks_code = []
    sc = scenarios  # shorthand

    act_map = {
        "act1": [],
        "act2": [],
        "act3": [],
        "act4": [],
    }

    for s in sorted(selection["all_selected"], key=lambda x: x["id"]):
        did = s["id"]
        act_key = f"act{s['act']}"
        s_data = sc.get(did, {})

        if did == "01":
            task_desc = (
                f"【Act{s['act']}·MCP工具编排】为{company}设计MCP跨系统方案：连接"
                f"{s_data.get('systemA','系统A')}+{s_data.get('systemB','系统B')}+{s_data.get('systemC','系统C')}，"
                f"演示{s_data.get('roleA','员工')}一句话完成{s_data.get('output','跨系统任务')}。"
            )
            act_map[act_key].append(('mcp_architect', task_desc, 'MCP编排方案'))

        elif did == "02":
            task_desc = (
                f"【Act{s['act']}·知识库】使用karpathy_knowledge_base工具，"
                f"为{company}编译{s_data.get('kbName','企业知识库')}。"
                f"输入'编译知识库，提取所有核心概念'。然后回答：{s_data.get('question','知识问题')}。"
            )
            act_map[act_key].append(('knowledge_engineer', task_desc, '知识库编译结果'))

        elif did == "03":
            task_desc = (
                f"【Act{s['act']}·代码迁移】评估{company}的{s_data.get('systemName','遗留系统')}("
                f"{s_data.get('scale','大规模')})从{s_data.get('oldLang','旧语言')}迁移到"
                f"{s_data.get('newLang','新语言')}的方案。对比传统({s_data.get('oldCost','高')})vs AI({s_data.get('newCost','低')})成本。"
            )
            act_map[act_key].append(('legacy_migrator', task_desc, '迁移评估'))

        elif did == "04":
            task_desc = (
                f"【Act{s['act']}·看板】使用ceo_dashboard工具，为{company}的{s_data.get('role','管理者')}生成"
                f"{s_data.get('dashName','管理看板')}。输入数据：{s_data.get('kpi1','')}，{s_data.get('kpi2','')}，"
                f"风险：{s_data.get('risk','')}。"
            )
            act_map[act_key].append(('ceo_advisor', task_desc, '管理看板'))

        elif did == "05":
            t1 = s_data.get('t1', '标准工单1')
            t2 = s_data.get('t2', '边界工单2')
            t3 = s_data.get('t3', '标准工单3')
            t4 = s_data.get('t4', '边界工单4')
            t5 = s_data.get('t5', '高敏感工单5')
            ticket_type = s_data.get('ticketType', '工单')
            task_desc = (
                f"【Act{s['act']}·监督员】使用ai_supervisor工具处理{company}的{ticket_type}："
                f"'1.{t1} 2.{t2} 3.{t3} 4.{t4} 5.{t5}'。分析自动处理率和人工审核原因。"
            )
            act_map[act_key].append(('supervisor', task_desc, '监督员审核报告'))

        elif did == "06":
            task_desc = (
                f"【Act{s['act']}·智能阅读】使用hypothesis_annotator工具分析{company}的"
                f"{s_data.get('docType','行业文档')}：https://en.wikipedia.org/wiki/Artificial_intelligence。"
                f"用4种标注类型（🔴关键/🟡非共识/🟢策略/💬批评）输出标注结果。"
            )
            act_map[act_key].append(('pm_reader', task_desc, '文档标注报告'))

        elif did == "07":
            task_desc = (
                f"【Act{s['act']}·战略辩论】模拟{company}的{s_data.get('roleA','角色A')}/"
                f"{s_data.get('roleB','角色B')}/{s_data.get('roleC','角色C')}三方辩论："
                f"{s_data.get('topic','重大决策议题')}。关键数字：{s_data.get('keyNumber','N/A')}。"
                f"风险点：{s_data.get('risk','N/A')}。输出3轮交锋+共识方案。100字以内。"
            )
            act_map[act_key].append(('strategy_debater', task_desc, '战略辩论记录'))

        elif did == "08":
            task_desc = (
                f"【Act{s['act']}·一人军团】{company}的{s_data.get('user','员工')}规划"
                f"'{s_data.get('project','内部工具')}'MVP。用/office-hours格式输出5个核心问题+"
                f"技术选型+功能列表。然后用playwright_frontend_test工具测试https://example.com验证能力。100字以内。"
            )
            act_map[act_key].append(('opc_builder', task_desc, 'MVP规划+测试'))

        elif did == "09":
            task_desc = (
                f"【Act{s['act']}·科研】使用auto_research工具，输入'{s_data.get('topic','研究课题')}'。"
                f"展示15-Stage管线：文献综述(关键词:{s_data.get('keywords','')})→实验设计→预期指标→论文摘要。100字以内。"
            )
            act_map[act_key].append(('researcher', task_desc, '科研方案'))

        elif did == "10":
            task_desc = (
                f"【Act{s['act']}·PPT压轴🎤】使用ppt_generator工具，生成{company}的{s_data.get('pptType','报告PPT')}："
                f"{s_data.get('content','核心内容要点')}。品牌规范：{s_data.get('brand','深色主题')}。"
                f"这是全流程的最终产出，展示{s_data.get('scale','企业规模化')}的价值。100字以内。"
            )
            act_map[act_key].append(('ppt_designer', task_desc, '汇报PPT'))

    # 生成Task代码块
    task_blocks = []
    for act_key, tasks in act_map.items():
        act_num = act_key.replace("act", "")
        for agent_key, desc, expected in tasks:
            task_blocks.append(
                f'    all_tasks.append(("{act_key}", Task(\n'
                f'        description=f"{desc}{{max_w}}",\n'
                f'        expected_output="{expected}",\n'
                f'        agent=agents["{agent_key}"],\n'
                f'    )))'
            )

    tasks_str = "\n".join(task_blocks)

    # 构建完整脚本
    header = f'''#!/usr/bin/env python3.11
"""
{company} AI公司操作系统 — CrewAI编排
行业：{industry_zh}
生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}
由 enterprise-skills/generator.py 自动生成

用法：
  python3.11 newco_crew.py --demo          # 全幕演示
  python3.11 newco_crew.py --act 4 --demo  # 仅Act4
  python3.11 newco_crew.py --list          # 查看工具
  python3.11 newco_crew.py --run-tool ppt  # 单工具测试
"""
'''

    # 如果有原始文件，做替换；否则生成最小版本
    if base:
        # 替换头部注释
        script = re.sub(r'#!/usr/bin/env python3.11\n""".*?"""', header.strip(), base, flags=re.DOTALL, count=1)
        # 替换Task定义块
        task_marker_start = "    # === Act 1: 技术 ==="
        task_marker_end = "    # 按Act筛选"
        if task_marker_start in script and task_marker_end in script:
            before = script[:script.index(task_marker_start)]
            after = script[script.index(task_marker_end):]
            script = before + f"    # === {company} 定制Task ===\n{tasks_str}\n\n    " + after
        return script
    else:
        return header + f"\n# [企业专属Task已定义，需要完整orchestrator基础代码]\n# Tasks:\n{tasks_str}\n"


def generate_narrative(selection: dict, profile: dict, pattern: dict) -> str:
    """生成4幕叙事大纲"""
    company = profile.get("company_name", "企业")
    industry_zh = profile.get("industry_zh", "")
    mins = profile.get("presentation_minutes", 90)
    goal = profile.get("demo_goal", "推动AI采用")
    scenarios = pattern.get("demo_scenarios", {})

    act1_demos = [s for s in selection["all_selected"] if s["act"] == 1]
    act2_demos = [s for s in selection["all_selected"] if s["act"] == 2]
    act3_demos = [s for s in selection["all_selected"] if s["act"] == 3]
    act4_demos = [s for s in selection["all_selected"] if s["act"] == 4]

    # 用GLM生成开场Hook（如果可用）
    sc_07 = scenarios.get("07", {})
    topic_hint = sc_07.get("topic", "AI对本行业的影响")

    lines = [
        f"# {company} AI分享 — 4幕叙事大纲",
        f"\n行业：{industry_zh}  |  时长：{mins}分钟  |  目标：{goal}",
        f"\n生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "---\n",
        "## 开场（5分钟）\n",
        "**开场调查问题**（让全场举手，建立共鸣）：\n",
    ]

    pain = profile.get("pain_points", [])
    q1 = "你有没有花超过1小时找一个本来应该知道的内部答案？" if "D" in pain else "你觉得自己每天有多少工作是重复性的？"
    q2 = "你有没有经历过：开了3次会，还没把一个决策推下去？" if "C" in pain else "你有没有因为信息分散在多个系统而漏掉重要信息？"
    sc_05 = scenarios.get("05", {})
    q3 = f"如果AI能自动处理{sc_05.get('autoRate','60%')}的{sc_05.get('ticketType','重复工作')}，你会用来做什么？"

    lines += [
        f'1. "{q1}"  → 预期：约70%的人举手 → 说明：这就是知识护城河问题',
        f'2. "{q2}"  → 预期：约60%的人举手 → 说明：这就是AI多Agent的机会',
        f'3. "{q3}"  → 制造期待\n',
        f"**开场金句**：\n> \"{company}在{industry_zh}领域的竞争力，"
        f"从今天起不再只取决于人的能力，而是人×AI的乘积。\"\n",
        "---\n",
    ]

    act_configs = [
        (1, "技术：AI能做什么？", act1_demos, 20),
        (2, "行业：我们的行业怎么用？", act2_demos, 20),
        (3, "工作：你的工作会怎么变？", act3_demos, 20),
        (4, "行动：我们下一步做什么？", act4_demos, 25),
    ]

    cumulative = 5
    for act_num, theme, demos, duration in act_configs:
        lines += [
            f"## 第{act_num}幕：{theme} ({duration}分钟，累计{cumulative+duration}分钟)\n",
            f"**核心论点**：{'AI工具的本质是协议，而不是APP' if act_num==1 else '行业护城河正在重构，数据和知识才是关键' if act_num==2 else '工作不是消失，而是人的位置在变' if act_num==3 else '现在行动：从一个小场景开始，不要等大项目'}",
        ]
        if demos:
            lines += ["\n**Demo穿插**："]
            for s in demos:
                sc = scenarios.get(s["id"], {})
                lines.append(f"- [{s['id']}] {s['name']}：演示{sc.get('topic', '') or sc.get('kbName', '') or DEMO_NAMES[s['id']]}（{2 if s['mode']=='embedded' else 5}分钟）")

        endings = {
            1: "这不是工具升级，是工作方式的重构。",
            2: "护城河不消失，只是从流程壁垒变成知识壁垒。",
            3: "不是AI在替代人，是用AI的人在替代不用AI的人。",
            4: f"{company}的AI时代，从今天这个会议室开始。",
        }
        lines += [
            f"\n**幕结金句**：\n> \"{endings.get(act_num, '')}\"",
            "\n---\n",
        ]
        cumulative += duration

    # 时间分配
    lines += [
        "## 时间分配\n",
        "| 环节 | 时长 | 累计 |",
        "|------|------|------|",
        "| 开场 | 5min | 5min |",
        "| 第1幕 | 20min | 25min |",
        "| 第2幕 | 20min | 45min |",
        "| 休息 | 10min | 55min |",
        "| 第3幕 | 15min | 70min |",
        "| 第4幕 | 15min | 85min |",
        "| Q&A | 5min | 90min |",
        "\n## 超时应急预案\n",
        "| 砍的优先级 | 内容 |",
        "|-----------|------|",
        "| 第1刀 | 备选Demo（Playwright/Maestro）|",
        "| 第2刀 | 第3幕最后一个嵌入Demo |",
        "| 第3刀 | AutoResearch |",
        "| **绝不砍** | 知识库Demo + AI监督员 + PPT生成 |",
    ]

    return "\n".join(lines)


# ══════════════════════════════════════════════════
# 交互式配置
# ══════════════════════════════════════════════════

INDUSTRY_MAP = {
    "1": ("banking-finance", "商业银行/金融机构"),
    "2": ("manufacturing", "制造业"),
    "3": ("aerospace-defense", "航空航天/军工国防"),
    "4": ("healthcare", "医疗/医药/医疗器械"),
    "5": ("retail-ecommerce", "零售/电商/消费品"),
    "6": ("consulting-research", "咨询/研究机构"),
    "7": ("logistics", "物流/供应链"),
    "8": ("real-estate", "地产/建筑"),
    "9": ("energy", "能源/公用事业"),
    "10": ("tech-software", "科技/软件"),
}

PAIN_MAP = {
    "A": "大量重复性文档处理",
    "B": "跨部门协作效率低",
    "C": "会议多但决策慢",
    "D": "员工花时间查找内部知识",
    "E": "数据有但难以快速形成洞察",
    "F": "专家资源稀缺，评审排队",
    "G": "风险识别滞后",
    "H": "从想法到原型周期太长",
    "I": "技术文档阅读消化慢",
    "J": "遗留系统多，技术债高",
    "K": "质量管控依赖人工，漏检率高",
    "L": "合规审查工作量大",
    "M": "测试覆盖率低，Bug成本高",
}


def interactive_profile() -> dict:
    """交互式采集企业画像"""
    print("\n" + "═" * 60)
    print("🏢 企业AI演示方案生成器 — 画像采集")
    print("═" * 60)

    company = input("\n1. 企业名称：").strip() or "示例企业"
    company_slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]+', '-', company).strip('-')[:30]

    print("\n2. 所在行业（输入编号）：")
    for k, (_, zh) in INDUSTRY_MAP.items():
        print(f"   {k:>2}. {zh}")
    ind_choice = input("选择（1-10）：").strip()
    industry, industry_zh = INDUSTRY_MAP.get(ind_choice, ("manufacturing", "制造业"))

    size_map = {"1": ("startup", "<100人"), "2": ("mid", "100-1000人"), "3": ("large", "1000-1万人"), "4": ("enterprise", ">1万人")}
    print("\n3. 员工规模：")
    for k, (_, zh) in size_map.items():
        print(f"   {k}. {zh}")
    size_choice = input("选择（1-4）：").strip()
    size, size_zh = size_map.get(size_choice, ("large", "1000-1万人"))

    audience = input("\n4. 受众群体（例如：全行中高层管理者）：").strip() or "管理层"

    print("\n5. 核心痛点（多选，用逗号分隔，例如 A,D,E）：")
    for k, v in PAIN_MAP.items():
        print(f"   {k}. {v}")
    pain_input = input("选择：").strip().upper()
    pain_points = [p.strip() for p in pain_input.split(",") if p.strip() in PAIN_MAP]

    print("\n6. 敏感约束：")
    offline = input("   数据是否必须离线/不能上云？(y/n): ").strip().lower() == "y"
    sensitivity = "high" if input("   是否有监管合规要求？(y/n): ").strip().lower() == "y" else "medium"

    goal = input("\n7. 演示核心目标（例如：说服CTO批准AI试点预算）：").strip() or "推动AI试点"
    minutes = int(input("8. 演示总时长（分钟，默认90）：").strip() or "90")

    return {
        "company_name": company,
        "company_slug": company_slug,
        "industry": industry,
        "industry_zh": industry_zh,
        "size": size,
        "size_zh": size_zh,
        "audience_dept": audience,
        "audience_roles": [audience],
        "audience_tech_level": "mixed",
        "pain_points": pain_points,
        "pain_points_custom": "",
        "key_systems": [],
        "data_sensitivity": sensitivity,
        "offline_required": offline,
        "sensitive_topics": [],
        "compliance": [],
        "demo_goal": goal,
        "presentation_minutes": minutes,
        "target_demo_count": 11,
        "budget_emphasis": False,
        "primary_language": "zh",
    }


# ══════════════════════════════════════════════════
# 主函数
# ══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="企业AI演示方案生成器")
    parser.add_argument("--interactive", action="store_true", help="交互式配置")
    parser.add_argument("--profile", type=str, help="画像JSON文件路径")
    parser.add_argument("--company", type=str, help="企业名称")
    parser.add_argument("--industry", type=str, default="manufacturing", help="行业代码")
    parser.add_argument("--size", type=str, default="large", help="规模")
    parser.add_argument("--pain-points", type=str, default="A,D,E", help="痛点代码，逗号分隔")
    parser.add_argument("--minutes", type=int, default=90, help="演示时长（分钟）")
    parser.add_argument("--audience", type=str, default="管理层", help="受众描述")
    parser.add_argument("--preview", action="store_true", help="仅预览，不写文件")
    parser.add_argument("--step", type=str, choices=["analyze", "design", "package"], help="只执行某个步骤")
    args = parser.parse_args()

    # ── 获取企业画像 ──
    if args.interactive:
        profile = interactive_profile()
    elif args.profile:
        profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    elif args.company:
        profile = {
            "company_name": args.company,
            "company_slug": re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]+', '-', args.company).strip('-')[:30],
            "industry": args.industry,
            "industry_zh": args.industry,
            "size": args.size,
            "audience_dept": args.audience,
            "audience_roles": [args.audience],
            "pain_points": [p.strip().upper() for p in args.pain_points.split(",")],
            "data_sensitivity": "medium",
            "offline_required": False,
            "demo_goal": "推动AI采用",
            "presentation_minutes": args.minutes,
            "target_demo_count": 11,
        }
    else:
        parser.print_help()
        sys.exit(0)

    company = profile.get("company_name", "企业")
    slug = profile.get("company_slug") or re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]+', '-', company).strip('-')[:30]

    print(f"\n{'═'*60}")
    print(f"🏢 正在为 {company} 生成AI演示方案")
    print(f"{'═'*60}")

    # ── 1. 评分 ──
    print("📊 计算Demo评分...")
    scores = score_demos(profile)
    selection = select_demos(scores, profile.get("target_demo_count", 11))

    print(f"✅ 已选 {len(selection['all_selected'])} 个Demo：")
    for s in sorted(selection["all_selected"], key=lambda x: x["id"]):
        tag = "⭐必选" if s["must"] else ("嵌入" if s["mode"] == "embedded" else "独立")
        print(f"   [{s['id']}] {s['name']} ({tag}, Act{s['act']})")

    if args.preview:
        print("\n[预览模式] 不生成文件。")
        return

    # ── 2. 加载行业数据 ──
    print("🌐 加载行业预置数据...")
    pattern = load_industry_pattern(profile.get("industry", ""))

    # ── 3. 输出目录 ──
    out_dir = OUTPUTS / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── 4. 生成各文件 ──
    print("📝 生成文件中...", end="", flush=True)

    # profile.json
    (out_dir / "profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    print(" profile", end="", flush=True)

    # score_report.md
    (out_dir / "score_report.md").write_text(generate_score_report(scores, selection, profile), encoding="utf-8")
    print(" score", end="", flush=True)

    # DEMO总表.md
    (out_dir / "DEMO总表.md").write_text(generate_demo_table(selection, profile, pattern), encoding="utf-8")
    print(" demo表", end="", flush=True)

    # RUNBOOK.md
    (out_dir / "RUNBOOK.md").write_text(generate_runbook(selection, profile, pattern), encoding="utf-8")
    print(" runbook", end="", flush=True)

    # narrative.md
    (out_dir / "narrative.md").write_text(generate_narrative(selection, profile, pattern), encoding="utf-8")
    print(" narrative", end="", flush=True)

    # newco_crew.py
    crew_script = generate_crew_script(selection, profile, pattern)
    crew_path = out_dir / "newco_crew.py"
    crew_path.write_text(crew_script, encoding="utf-8")
    crew_path.chmod(0o755)
    print(" crew.py", end="", flush=True)

    print(f"\n\n{'═'*60}")
    print(f"✅ 生成完成！输出目录：{out_dir}")
    print(f"{'═'*60}")
    print(f"\n文件列表：")
    for f in sorted(out_dir.iterdir()):
        size = f.stat().st_size
        print(f"  {f.name:<25} {size:>7,} bytes")
    print(f"\n运行演示：")
    print(f"  python3.11 {out_dir}/newco_crew.py --list")
    print(f"  python3.11 {out_dir}/newco_crew.py --demo")
    print(f"  python3.11 {out_dir}/newco_crew.py --act 4 --demo")


if __name__ == "__main__":
    main()
