#!/usr/bin/env python3
"""
企业 AI 痛点场景 & Demo 匹配生成器
====================================
输入公司名称（可选：行业、规模等补充信息），
自动生成该企业可能面临的痛点场景 + 对应 Demo 推荐表格。

用法：
  python3 demo_企业痛点生成器.py 四川九洲电器集团
  python3 demo_企业痛点生成器.py 宁德时代 --info "动力电池制造，员工3万+"
  python3 demo_企业痛点生成器.py 中国银行四川分行 --info "国有银行，零售+对公"
  python3 demo_企业痛点生成器.py --auto  # 用内置示例演示
"""

import os, sys, json, time, argparse

try:
    from zhipuai import ZhipuAI
except ImportError:
    print("❌ 请安装依赖：pip install zhipuai")
    sys.exit(1)

ZHIPU_API_KEY = os.getenv("BIGMODEL_API_KEY", "1790d449b46d437bbc8b101815048d64.lEMGH4tememSXbvH")
client = ZhipuAI(api_key=ZHIPU_API_KEY)
MODEL = "glm-4-plus"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Demo 武器库（行业通用版，20个Demo）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEMO_LIBRARY = {
    "A1": {
        "名称": "AI三级能力演示",
        "类别": "认知启蒙",
        "实现": "Python脚本",
        "描述": "工具→助手→Agent，同一问题三种AI能力层级对比",
        "难度": "★",
        "适用行业": "全行业",
        "关键词": ["AI认知", "能力边界", "决策层科普"],
    },
    "A2": {
        "名称": "Prompt Engineering 工坊",
        "类别": "认知启蒙",
        "实现": "交互式Notebook",
        "描述": "6种Prompt技巧 × 行业真实案例，差Prompt vs 好Prompt对比",
        "难度": "★",
        "适用行业": "全行业",
        "关键词": ["Prompt", "业务人员", "效率提升"],
    },
    "A3": {
        "名称": "AI能力边界测试",
        "类别": "认知启蒙",
        "实现": "Python脚本",
        "描述": "3个成功+2个失败任务，校准AI预期，硬规则靠代码/模糊判断靠模型",
        "难度": "★",
        "适用行业": "全行业",
        "关键词": ["认知校准", "降火", "决策层"],
    },
    "B1": {
        "名称": "文档合规审查",
        "类别": "文档智能",
        "实现": "Python + 规则引擎",
        "描述": "证书过期检测、盖章核查、参数校验 + AI语义审查，双引擎架构",
        "难度": "★★",
        "适用行业": "投标型企业、金融、医药、建筑",
        "关键词": ["标书", "投标", "合规", "审查", "申报", "资质", "证书过期"],
    },
    "B2": {
        "名称": "跨文档一致性检查",
        "类别": "文档智能",
        "实现": "Python + 规则引擎",
        "描述": "多文档参数交叉比对 + AI语义矛盾检测，生成修改清单",
        "难度": "★★",
        "适用行业": "军工、航空、汽车、法律",
        "关键词": ["文档一致性", "多文档", "名词统一", "军标", "标准化"],
    },
    "B3": {
        "名称": "合同智能审批",
        "类别": "文档智能",
        "实现": "Dify工作流 / Python",
        "描述": "合同文本→结构化提取→规则校验→风险评估→审批建议",
        "难度": "★★",
        "适用行业": "全行业",
        "关键词": ["合同", "审批", "法务", "风险", "采购", "销售"],
    },
    "B4": {
        "名称": "智能文档生成",
        "类别": "文档智能",
        "实现": "Agent代码",
        "描述": "输入参数→自动生成技术方案/报告/标书，套用企业模板格式",
        "难度": "★★",
        "适用行业": "全行业",
        "关键词": ["文档生成", "报告", "技术方案", "模板"],
    },
    "B5": {
        "名称": "会议纪要自动整理",
        "类别": "文档智能",
        "实现": "Dify工作流",
        "描述": "语音转写→结构化纪要（议题/结论/待办/责任人）",
        "难度": "★",
        "适用行业": "全行业",
        "关键词": ["会议", "纪要", "办公效率", "自动化"],
    },
    "C1": {
        "名称": "企业知识库（RAG）",
        "类别": "知识与搜索",
        "实现": "Dify + 向量库",
        "描述": "企业文档→语义搜索→带引用的智能问答，替代关键词搜索",
        "难度": "★★",
        "适用行业": "全行业",
        "关键词": ["知识库", "搜索", "RAG", "制度", "规章", "FAQ"],
    },
    "C2": {
        "名称": "多知识库权限隔离",
        "类别": "知识与搜索",
        "实现": "Agent代码",
        "描述": "按部门/密级/项目隔离知识库，RBAC权限 + 审计日志",
        "难度": "★★★",
        "适用行业": "军工、金融、医疗、政府",
        "关键词": ["权限", "保密", "涉密", "隔离", "合规", "RBAC"],
    },
    "C3": {
        "名称": "标准法规智能问答",
        "类别": "知识与搜索",
        "实现": "RAG + Agent",
        "描述": "行业标准/法规灌入知识库，自然语言提问→精确引用条文",
        "难度": "★★",
        "适用行业": "制造、医药、金融、建筑",
        "关键词": ["标准", "法规", "规范", "条文", "查询"],
    },
    "D1": {
        "名称": "外观质检AI",
        "类别": "专业判断",
        "实现": "Python + 多模态",
        "描述": "图像→缺陷检测→经验库比对→判定合格/不合格→质检报告",
        "难度": "★★★",
        "适用行业": "制造业（电子/汽车/食品/纺织）",
        "关键词": ["质检", "外观", "瑕疵", "缺陷", "视觉", "检验"],
    },
    "D2": {
        "名称": "设备故障诊断",
        "类别": "专业判断",
        "实现": "Agent + 知识库",
        "描述": "故障现象→AI分析原因（概率排序）→排查方案→历史案例匹配",
        "难度": "★★",
        "适用行业": "制造、能源、运维、物业",
        "关键词": ["故障", "维修", "诊断", "运维", "设备", "维保"],
    },
    "D3": {
        "名称": "供应商风险评估",
        "类别": "专业判断",
        "实现": "Browser-Use Agent",
        "描述": "AI自动在政府平台查询供应商资质/信用/涉诉→综合评估报告",
        "难度": "★★★",
        "适用行业": "全行业",
        "关键词": ["供应商", "采购", "风险", "资质", "尽调"],
    },
    "D4": {
        "名称": "竞品情报监控",
        "类别": "专业判断",
        "实现": "Browser-Use Agent",
        "描述": "自动采集招标公告/中标信息/行业动态→竞品分析日报",
        "难度": "★★★",
        "适用行业": "所有B2B企业",
        "关键词": ["竞品", "招标", "中标", "市场", "情报", "监控"],
    },
    "E1": {
        "名称": "多Agent辩论",
        "类别": "协同决策",
        "实现": "Python多Agent",
        "描述": "CEO/CFO/CTO三视角辩论决策议题，支持事件注入，适合决策层",
        "难度": "★★",
        "适用行业": "全行业（决策层）",
        "关键词": ["决策", "辩论", "多视角", "战略", "投资"],
    },
    "E2": {
        "名称": "跨部门工单流转",
        "类别": "协同决策",
        "实现": "Dify + MCP",
        "描述": "AI Agent通过MCP连接多业务系统，自动创建/流转/催办工单",
        "难度": "★★★",
        "适用行业": "中大型企业",
        "关键词": ["工单", "流程", "跨部门", "OA", "审批", "MCP"],
    },
    "E3": {
        "名称": "生产排程优化",
        "类别": "协同决策",
        "实现": "Agent + 规则引擎",
        "描述": "订单+资源约束→AI排程建议→what-if分析→瓶颈识别",
        "难度": "★★★",
        "适用行业": "制造业",
        "关键词": ["排程", "生产", "产能", "排产", "车间", "工序"],
    },
    "E4": {
        "名称": "项目风险预警",
        "类别": "协同决策",
        "实现": "Browser-Use + Agent",
        "描述": "外部风险采集（价格/政策/舆情）+ 内部进度分析→风险预警",
        "难度": "★★★",
        "适用行业": "全行业",
        "关键词": ["风险", "预警", "项目", "监控", "价格波动"],
    },
    "E5": {
        "名称": "AI辅助编程（内网版）",
        "类别": "协同决策",
        "实现": "内网模型部署 + IDE插件",
        "描述": "内网部署代码模型，VS Code插件式代码补全/审查/对话",
        "难度": "★★★",
        "适用行业": "有研发团队的企业",
        "关键词": ["编程", "代码", "开发", "Cursor", "Copilot", "软件"],
    },
}


def stream_print(text: str, delay: float = 0.012):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()


def analyze_company(company_name: str, extra_info: str = "") -> dict:
    """Step 1: 用 LLM 分析企业背景，输出结构化 JSON"""

    prompt = f"""你是一位资深的企业AI咨询顾问。请根据公司名称（及补充信息）分析该企业的基本情况。

公司名称：{company_name}
补充信息：{extra_info if extra_info else '无'}

请输出严格的JSON格式（不要输出其他内容），包含以下字段：

{{
  "公司全称": "...",
  "行业": "...",
  "细分领域": "...",
  "企业性质": "央企/国企/民企/外企/合资",
  "估计规模": "大型/中型/小型",
  "估计员工数": "...",
  "主营业务": ["业务1", "业务2", "业务3"],
  "核心部门": ["部门1", "部门2", "部门3", "部门4", "部门5"],
  "行业特征": {{
    "是否投标型业务": true/false,
    "是否有生产制造": true/false,
    "是否有质检需求": true/false,
    "是否有保密要求": true/false,
    "是否有大量文档": true/false,
    "是否有供应链管理": true/false,
    "是否有研发团队": true/false,
    "是否有合同管理": true/false,
    "是否有设备运维": true/false,
    "是否面向B端客户": true/false
  }},
  "可能的痛点场景": [
    {{
      "场景名称": "...",
      "痛点描述": "一句话描述该企业在此场景的具体痛苦（要具体到行业术语）",
      "涉及部门": "...",
      "紧急程度": "高/中/低",
      "AI解决思路": "一句话说明AI怎么解决"
    }}
  ]
}}

要求：
1. 痛点场景至少列出8-12个，覆盖研发、生产、质量、供应链、销售、管理各环节
2. 痛点描述必须具体到该行业的术语（不要泛泛而谈）
3. 如果你不确定该公司的信息，基于行业常识合理推测
4. JSON必须合法，可被Python json.loads解析"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是企业AI咨询顾问，熟悉各行业的数字化痛点。输出严格JSON。"},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2500,
        temperature=0.3,
    )
    raw = resp.choices[0].message.content.strip()
    # 清理 markdown 代码块
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()
    return json.loads(raw)


def match_demos(company_profile: dict) -> list:
    """Step 2: 用 LLM 将痛点场景与 Demo 武器库做智能匹配"""

    demo_brief = []
    for did, d in DEMO_LIBRARY.items():
        demo_brief.append(
            f"{did}|{d['名称']}|{d['类别']}|{d['实现']}|{d['描述']}|关键词:{','.join(d['关键词'])}"
        )
    demo_text = "\n".join(demo_brief)

    pain_text = json.dumps(company_profile["可能的痛点场景"], ensure_ascii=False, indent=2)

    prompt = f"""你是企业AI方案架构师。请将该企业的痛点场景与Demo武器库做最佳匹配。

【企业信息】
公司：{company_profile.get('公司全称', '')}
行业：{company_profile.get('行业', '')}
主营：{', '.join(company_profile.get('主营业务', []))}

【痛点场景】
{pain_text}

【Demo武器库】（编号|名称|类别|实现方式|描述|关键词）
{demo_text}

请输出严格JSON数组，每个元素：
[
  {{
    "痛点序号": 1,
    "场景名称": "...",
    "匹配Demo": ["B1", "B3"],
    "推荐优先级": "P0必做/P1强烈推荐/P2建议/P3可选",
    "落地难度": "★/★★/★★★",
    "预期价值": "一句话，量化描述（如：审查效率提升10倍、避免年损失XX万）",
    "定制要点": "一句话说明该Demo需要针对此企业做什么定制"
  }}
]

要求：
1. 每个痛点匹配1-3个最相关的Demo
2. 必须输出至少8条匹配
3. 优先级分布合理：P0不超过3个，P1不超过4个
4. 另外追加2-3个该企业可能没意识到但你认为有价值的"隐藏场景"（标注为"AI顾问追加"）"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是企业AI方案架构师。输出严格JSON数组。"},
            {"role": "user", "content": prompt},
        ],
        max_tokens=2500,
        temperature=0.3,
    )
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()
    return json.loads(raw)


def render_table(company_profile: dict, matches: list):
    """Step 3: 渲染最终的表格输出"""

    name = company_profile.get("公司全称", "未知企业")
    industry = company_profile.get("行业", "")
    nature = company_profile.get("企业性质", "")
    scale = company_profile.get("估计规模", "")
    biz = ", ".join(company_profile.get("主营业务", []))
    depts = ", ".join(company_profile.get("核心部门", []))

    print()
    print("█" * 70)
    print(f"  🏭 {name}")
    print(f"  📊 行业：{industry} | 性质：{nature} | 规模：{scale}")
    print(f"  💼 主营：{biz}")
    print(f"  🏢 核心部门：{depts}")
    print("█" * 70)

    # ── 行业特征标签 ──
    traits = company_profile.get("行业特征", {})
    tags = [k.replace("是否", "").replace("有", "")
            for k, v in traits.items() if v]
    if tags:
        print(f"\n  🏷️  行业特征：{'  '.join(f'[{t}]' for t in tags)}")

    # ── 痛点 → Demo 匹配表 ──
    print(f"\n{'━' * 70}")
    print("  📋 痛点场景 × AI Demo 匹配方案")
    print(f"{'━' * 70}\n")

    # 按优先级分组
    p0 = [m for m in matches if "P0" in m.get("推荐优先级", "")]
    p1 = [m for m in matches if "P1" in m.get("推荐优先级", "")]
    p2 = [m for m in matches if "P2" in m.get("推荐优先级", "")]
    p3 = [m for m in matches if "P3" in m.get("推荐优先级", "")]

    def print_group(title: str, items: list, emoji: str):
        if not items:
            return
        print(f"  {emoji} {title}")
        print(f"  {'─' * 65}")
        for m in items:
            seq = m.get("痛点序号", "?")
            scene = m.get("场景名称", "")
            demos = m.get("匹配Demo", [])
            diff = m.get("落地难度", "")
            value = m.get("预期价值", "")
            custom = m.get("定制要点", "")

            # 展开Demo名称
            demo_names = []
            for did in demos:
                if did in DEMO_LIBRARY:
                    d = DEMO_LIBRARY[did]
                    demo_names.append(f"{did}-{d['名称']}({d['实现']})")
                else:
                    demo_names.append(did)

            print(f"\n  [{seq}] {scene}")
            print(f"      Demo → {' + '.join(demo_names)}")
            print(f"      难度 {diff}  |  价值：{value}")
            print(f"      定制：{custom}")
        print()

    print_group("🔴 P0 — 必做（立竿见影）", p0, "🔴")
    print_group("🟠 P1 — 强烈推荐（高ROI）", p1, "🟠")
    print_group("🟡 P2 — 建议（锦上添花）", p2, "🟡")
    print_group("🟢 P3 — 可选（远期探索）", p3, "🟢")

    # ── 落地路线图 ──
    print(f"{'━' * 70}")
    print("  🗺️  建议落地路线图")
    print(f"{'━' * 70}")
    print()
    print("  Phase 1（0-3月）快速见效")
    for m in p0:
        demos_str = "+".join(m.get("匹配Demo", []))
        print(f"    → [{demos_str}] {m.get('场景名称', '')}")
    print()
    print("  Phase 2（3-6月）规模推广")
    for m in p1:
        demos_str = "+".join(m.get("匹配Demo", []))
        print(f"    → [{demos_str}] {m.get('场景名称', '')}")
    print()
    print("  Phase 3（6-12月）深度智能")
    for m in (p2 + p3):
        demos_str = "+".join(m.get("匹配Demo", []))
        print(f"    → [{demos_str}] {m.get('场景名称', '')}")

    # ── Demo 使用统计 ──
    print(f"\n{'━' * 70}")
    print("  📊 Demo 覆盖统计")
    print(f"{'━' * 70}\n")
    demo_count = {}
    for m in matches:
        for did in m.get("匹配Demo", []):
            demo_count[did] = demo_count.get(did, 0) + 1
    for did, cnt in sorted(demo_count.items(), key=lambda x: -x[1]):
        d = DEMO_LIBRARY.get(did, {})
        bar = "█" * cnt + "░" * (5 - cnt)
        print(f"    {did} {d.get('名称', '?'):　<12} {bar} 命中{cnt}个场景")

    print(f"\n{'━' * 70}")
    print(f"  ✅ 共识别 {len(matches)} 个场景，匹配 {len(demo_count)} 个独立Demo")
    print(f"  📎 P0={len(p0)}  P1={len(p1)}  P2={len(p2)}  P3={len(p3)}")
    print(f"{'━' * 70}\n")


def save_markdown(company_profile: dict, matches: list, filename: str):
    """保存为 Markdown 文件"""

    name = company_profile.get("公司全称", "未知企业")
    industry = company_profile.get("行业", "")
    nature = company_profile.get("企业性质", "")
    biz = ", ".join(company_profile.get("主营业务", []))

    lines = [
        f"# {name} — AI 痛点场景 & Demo 匹配方案\n",
        f"> 自动生成 | 行业：{industry} | 性质：{nature}\n",
        f"> 主营业务：{biz}\n",
        "\n---\n",
        "\n## 痛点 × Demo 匹配总表\n",
        "| 优先级 | 场景 | 匹配Demo | 难度 | 预期价值 | 定制要点 |",
        "|--------|------|---------|------|---------|---------|",
    ]

    for m in matches:
        pri = m.get("推荐优先级", "")
        scene = m.get("场景名称", "")
        demos = " + ".join(m.get("匹配Demo", []))
        diff = m.get("落地难度", "")
        value = m.get("预期价值", "")
        custom = m.get("定制要点", "")
        lines.append(f"| {pri} | {scene} | {demos} | {diff} | {value} | {custom} |")

    lines.append("\n---\n")
    lines.append("\n## 落地路线图\n")

    for phase, plist, label in [
        ("Phase 1（0-3月）", [m for m in matches if "P0" in m.get("推荐优先级", "")], "快速见效"),
        ("Phase 2（3-6月）", [m for m in matches if "P1" in m.get("推荐优先级", "")], "规模推广"),
        ("Phase 3（6-12月）", [m for m in matches if "P2" in m.get("推荐优先级", "") or "P3" in m.get("推荐优先级", "")], "深度智能"),
    ]:
        lines.append(f"\n### {phase} — {label}\n")
        for m in plist:
            demos = "+".join(m.get("匹配Demo", []))
            lines.append(f"- **[{demos}]** {m.get('场景名称', '')} — {m.get('预期价值', '')}")

    lines.append("\n---\n")
    lines.append("\n## Demo 详情参考\n")
    demo_used = set()
    for m in matches:
        for did in m.get("匹配Demo", []):
            demo_used.add(did)
    for did in sorted(demo_used):
        d = DEMO_LIBRARY.get(did, {})
        lines.append(f"\n### {did} — {d.get('名称', '?')}\n")
        lines.append(f"- **类别**：{d.get('类别', '')}")
        lines.append(f"- **实现方式**：{d.get('实现', '')}")
        lines.append(f"- **描述**：{d.get('描述', '')}")
        lines.append(f"- **难度**：{d.get('难度', '')}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  💾 已保存 Markdown：{filename}")


def main():
    parser = argparse.ArgumentParser(description="企业AI痛点场景&Demo匹配生成器")
    parser.add_argument("company", nargs="?", help="公司名称")
    parser.add_argument("--info", type=str, default="", help="补充信息（行业、规模等）")
    parser.add_argument("--auto", action="store_true", help="使用内置示例演示")
    parser.add_argument("--save", action="store_true", help="保存为Markdown文件")
    args = parser.parse_args()

    print("\n" + "█" * 70)
    print("  🏭 企业 AI 痛点场景 & Demo 匹配生成器")
    print("  输入公司名称 → 自动分析痛点 → 匹配最佳Demo方案")
    print("█" * 70)

    if args.auto:
        company = "四川九洲电器集团"
        extra = "军工背景电气设备制造，4个事业部，员工3000+，已有Dify平台和8块L20 GPU"
    elif args.company:
        company = args.company
        extra = args.info
    else:
        print("\n请输入公司名称（直接回车使用示例）：", end="")
        try:
            company = input().strip()
        except EOFError:
            company = ""
        if not company:
            company = "四川九洲电器集团"
            extra = "军工背景电气设备制造"
            print(f"  → 使用示例：{company}")
        else:
            print("补充信息（行业、规模等，可选，直接回车跳过）：", end="")
            try:
                extra = input().strip()
            except EOFError:
                extra = ""

    # ── Step 1: 企业分析 ──
    print(f"\n{'─' * 50}")
    print(f"  🔍 Step 1/3 — 分析企业背景：{company}")
    print(f"{'─' * 50}")
    print("  🤖 AI 正在分析企业行业特征和潜在痛点...\n")

    try:
        profile = analyze_company(company, extra)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON解析失败，正在重试... ({e})")
        profile = analyze_company(company, extra)

    biz = ", ".join(profile.get("主营业务", []))
    pains = profile.get("可能的痛点场景", [])
    print(f"  ✅ 识别行业：{profile.get('行业', '?')}")
    print(f"  ✅ 主营业务：{biz}")
    print(f"  ✅ 识别痛点：{len(pains)} 个场景")

    for i, p in enumerate(pains, 1):
        urg = p.get("紧急程度", "")
        emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(urg, "⚪")
        print(f"     {emoji} [{i}] {p.get('场景名称', '')} — {p.get('痛点描述', '')[:40]}...")
        time.sleep(0.1)

    # ── Step 2: Demo 匹配 ──
    print(f"\n{'─' * 50}")
    print(f"  🎯 Step 2/3 — 痛点场景 × Demo 智能匹配")
    print(f"{'─' * 50}")
    print("  🤖 AI 正在从20个Demo中匹配最佳方案...\n")

    try:
        matches = match_demos(profile)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON解析失败，正在重试... ({e})")
        matches = match_demos(profile)

    print(f"  ✅ 匹配完成：{len(matches)} 个场景已匹配\n")

    # ── Step 3: 渲染输出 ──
    print(f"{'─' * 50}")
    print(f"  📊 Step 3/3 — 生成方案表格")
    print(f"{'─' * 50}")

    render_table(profile, matches)

    # ── 保存文件 ──
    if args.save or args.auto:
        safe_name = company.replace(" ", "_").replace("/", "_")
        out_dir = os.path.dirname(os.path.abspath(__file__))
        md_path = os.path.join(out_dir, f"{safe_name}-AI痛点Demo匹配.md")
        save_markdown(profile, matches, md_path)

    print("✅ 生成完成！\n")


if __name__ == "__main__":
    main()
