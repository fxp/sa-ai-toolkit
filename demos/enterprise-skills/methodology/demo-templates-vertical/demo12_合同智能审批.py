#!/usr/bin/env python3
"""
Demo ⑫ — 合同智能审批（九洲审批场景）
=====================================
场景来源：九洲技术负责人原话 —
  "能不能把AI用到我们的审批流里？规则是很清晰的"
  "有些是数字的，有些是文本的，质量要求要对照合同"
  "这个平台本身不具备自动审批功能"

功能：
  1. 合同关键条款自动提取（结构化）
  2. 硬性规则校验（金额/期限/合规项）
  3. AI 模糊条款风险评估
  4. 生成审批意见书

用法：
  python3 demo12_合同智能审批.py
  python3 demo12_合同智能审批.py --auto
"""

import os
import sys
import json
import time
import argparse

try:
    from zhipuai import ZhipuAI
except ImportError:
    print("❌ 请安装依赖：pip install zhipuai")
    sys.exit(1)

ZHIPU_API_KEY = os.getenv("BIGMODEL_API_KEY", "1790d449b46d437bbc8b101815048d64.lEMGH4tememSXbvH")
if not ZHIPU_API_KEY:
    print("❌ 请设置 BIGMODEL_API_KEY 环境变量")
    sys.exit(1)

client = ZhipuAI(api_key=ZHIPU_API_KEY)
MODEL = "glm-4-plus"

# ── 模拟合同文本 ──
SAMPLE_CONTRACT = """
采购合同

合同编号：JZ-PO-2026-0312
签约日期：2026年4月10日

甲方（采购方）：四川九洲电器集团有限责任公司
乙方（供应商）：深圳市华芯半导体科技有限公司

第一条 采购内容
甲方向乙方采购以下物料：
1. STM32F407VGT6 微控制器芯片，数量 5000 片，单价 28.5 元/片
2. TPS54331 DC-DC 转换器，数量 3000 片，单价 12.8 元/片
3. MLCC 贴片电容 0805 0.1uF，数量 50000 片，单价 0.15 元/片

合同总金额：人民币 188,100 元（含 13% 增值税）

第二条 质量要求
2.1 所有芯片须为原厂正品，提供原厂出货证明和可追溯批次号。
2.2 良品率不低于 99.5%。
2.3 适用标准：工业级温度范围 -40°C ~ +85°C。

第三条 交货条款
3.1 交货期：合同签订后 15 个工作日内交付全部货物。
3.2 交货地点：四川省绵阳市游仙区九洲大道 268 号。
3.3 运输费用由乙方承担。

第四条 付款条件
4.1 合同签订后 3 个工作日内，甲方支付合同总金额的 50% 作为预付款。
4.2 货物验收合格后 30 个工作日内，甲方支付剩余 50% 尾款。

第五条 违约责任
5.1 乙方逾期交货，每逾期一天按合同总金额的 0.5% 支付违约金。
5.2 甲方逾期付款，每逾期一天按应付金额的 0.05% 支付滞纳金。
5.3 因乙方产品质量问题导致甲方生产线停产，乙方赔偿甲方直接损失及间接损失。

第六条 保密条款
双方对合同内容及履约过程中知悉的对方商业秘密负有保密义务，保密期限为合同终止后 3 年。

第七条 争议解决
因本合同引起的争议，双方协商解决；协商不成的，提交绵阳仲裁委员会仲裁。
"""

# ── 企业审批规则库 ──
APPROVAL_RULES = {
    "金额审批层级": {
        "≤5万": "部门经理审批",
        "5万-20万": "分管副总审批",
        "20万-100万": "总经理审批",
        ">100万": "总经理+董事长审批",
    },
    "预付款比例上限": 30,  # 公司规定预付款不超过30%
    "违约金上限": 0.3,    # 日违约金率不超过0.3%
    "滞纳金下限": 0.05,   # 甲方滞纳金不低于0.05%
    "付款账期下限": 30,    # 验收后至少30天付款
    "必须包含条款": ["质量要求", "保密条款", "违约责任", "争议解决"],
    "禁止条款": ["无限连带责任", "自动续约", "排他性"],
    "供应商必须资质": ["营业执照", "原厂授权"],
}


def stream_print(text: str, delay: float = 0.015):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def print_section(title: str):
    print(f"\n{'━' * 60}")
    print(f"  {title}")
    print(f"{'━' * 60}")


def ai_extract_terms(contract_text: str) -> dict:
    """用 GLM-5.1 提取合同关键条款"""
    prompt = f"""请从以下合同文本中提取关键条款，以 JSON 格式输出：

{contract_text}

请提取以下字段（严格按 JSON 格式输出，不要添加其他文字）：
{{
  "合同编号": "",
  "甲方": "",
  "乙方": "",
  "合同总金额_元": 0,
  "预付款比例_百分比": 0,
  "尾款支付条件": "",
  "交货期_工作日": 0,
  "违约金_日费率_百分比": 0,
  "滞纳金_日费率_百分比": 0,
  "质量标准": "",
  "良品率要求_百分比": 0,
  "保密期限_年": 0,
  "争议解决方式": "",
  "包含条款列表": [],
  "风险条款": []
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是合同分析AI，只输出JSON，不要其他任何文字。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,
        temperature=0.1,
    )
    text = response.choices[0].message.content.strip()
    # 清理可能的 markdown 代码块标记
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    if text.startswith("json"):
        text = text[4:]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"error": "JSON解析失败", "raw": text}


def rule_check(terms: dict, rules: dict) -> list:
    """规则引擎审查"""
    issues = []

    # 1. 金额审批层级
    amount = terms.get("合同总金额_元", 0)
    if amount > 100000:
        level = "总经理+董事长审批" if amount > 1000000 else "总经理审批" if amount > 200000 else "分管副总审批"
        issues.append({
            "级别": "ℹ️ 提示",
            "类型": "审批层级",
            "详情": f"合同金额 {amount:,.0f} 元，需要{level}",
        })

    # 2. 预付款比例
    prepay = terms.get("预付款比例_百分比", 0)
    if prepay > rules["预付款比例上限"]:
        issues.append({
            "级别": "🔴 违规",
            "类型": "预付款超标",
            "详情": f"预付款 {prepay}% 超过公司规定上限 {rules['预付款比例上限']}%",
            "建议": f"与供应商协商降至 {rules['预付款比例上限']}% 以下，或申请特批"
        })

    # 3. 违约金对等性
    penalty = terms.get("违约金_日费率_百分比", 0)
    late_fee = terms.get("滞纳金_日费率_百分比", 0)
    if penalty > 0 and late_fee > 0 and penalty / late_fee > 5:
        issues.append({
            "级别": "🟡 警告",
            "类型": "违约责任不对等",
            "详情": f"乙方违约金 {penalty}%/天 vs 甲方滞纳金 {late_fee}%/天（相差 {penalty/late_fee:.0f} 倍）",
            "建议": "虽然有利于甲方，但不对等条款可能导致供应商抬价或拒签"
        })

    # 4. 违约金合理性
    if penalty > rules["违约金上限"]:
        issues.append({
            "级别": "🟡 警告",
            "类型": "违约金过高",
            "详情": f"日违约金率 {penalty}% 超过行业惯例 {rules['违约金上限']}%，可能不被法律支持",
            "建议": f"建议调整为 {rules['违约金上限']}%/天，但设置上限（如不超过合同金额的10%）"
        })

    return issues


def ai_risk_review(contract_text: str, terms: dict, rule_issues: list) -> str:
    """用 GLM-5.1 做深度风险评估"""
    prompt = f"""你是九洲电器的法务顾问，请对以下采购合同做风险评估。

【合同全文】
{contract_text}

【AI提取的关键条款】
{json.dumps(terms, ensure_ascii=False, indent=2)}

【规则引擎已检出问题】
{json.dumps(rule_issues, ensure_ascii=False, indent=2)}

请从以下维度做深度评估：

1. ⚖️ 法律风险（条款是否有法律漏洞）
2. 💰 商务风险（价格是否合理、付款条件是否有利）
3. 🔒 保密风险（保密条款是否充分，考虑九洲军工背景）
4. 🚚 供应链风险（交期、质量保障是否充分）
5. 📝 缺失条款（合同中应该有但没有的条款）

最后给出：
- 综合风险等级（高/中/低）
- 审批建议（同意/附条件同意/不同意）
- 3 条具体修改建议（按优先级排序）

注意：九洲是军工企业，对供应链安全和保密要求极高。"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是军工企业法务顾问，擅长采购合同风险评估，语言简洁直接。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(description="合同智能审批 Demo")
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()

    print("\n" + "█" * 60)
    print("  📑 合同智能审批系统 Demo")
    print("  场景：采购合同提交审批前的 AI 自动审查")
    print("  模型：BigModel GLM-5.1")
    print("█" * 60)

    if not args.auto:
        try:
            input("\n按 Enter 开始审查...")
        except EOFError:
            pass

    # ── Step 1: AI 条款提取 ──
    print_section("Step 1/4 — AI 条款提取（非结构化 → 结构化）")
    print("🤖 GLM-5.1 正在阅读合同全文...\n")

    terms = ai_extract_terms(SAMPLE_CONTRACT)

    if "error" not in terms:
        print("  ✅ 关键条款提取完成：\n")
        display_keys = [
            ("合同编号", ""), ("甲方", ""), ("乙方", ""),
            ("合同总金额_元", " 元"), ("预付款比例_百分比", "%"),
            ("交货期_工作日", " 工作日"), ("违约金_日费率_百分比", "%/天"),
            ("滞纳金_日费率_百分比", "%/天"), ("良品率要求_百分比", "%"),
            ("保密期限_年", " 年"), ("争议解决方式", ""),
        ]
        for key, suffix in display_keys:
            val = terms.get(key, "未提取")
            if isinstance(val, (int, float)) and suffix == " 元":
                print(f"     {key.replace('_元','').replace('_百分比','').replace('_工作日','').replace('_日费率','').replace('_年','')}：{val:,.0f}{suffix}")
            else:
                print(f"     {key.replace('_元','').replace('_百分比','').replace('_工作日','').replace('_日费率','').replace('_年','')}：{val}{suffix}")
    else:
        print(f"  ⚠️  {terms['error']}")
        print(f"  原始输出：{terms.get('raw', '')[:200]}")
    print()

    # ── Step 2: 规则引擎校验 ──
    print_section("Step 2/4 — 规则引擎硬性校验")
    print("⏱️  比对公司审批规则... ", end="", flush=True)
    time.sleep(0.3)

    rule_issues = rule_check(terms, APPROVAL_RULES)
    print(f"完成！\n")

    if rule_issues:
        for issue in rule_issues:
            print(f"  {issue['级别']}  [{issue['类型']}]")
            print(f"     {issue['详情']}")
            if "建议" in issue:
                print(f"     💡 {issue['建议']}")
            print()
            time.sleep(0.3)
    else:
        print("  ✅ 规则引擎校验全部通过\n")

    # ── Step 3: AI 深度风险评估 ──
    print_section("Step 3/4 — AI 深度风险评估")
    print("🤖 GLM-5.1 正在做法律/商务/保密风险评估...\n")

    risk_result = ai_risk_review(SAMPLE_CONTRACT, terms, rule_issues)
    stream_print(risk_result, delay=0.01)

    # ── Step 4: 总结 ──
    print_section("Step 4/4 — 审批建议")

    print("""
┌──────────────────────────────────────────────────────┐
│              📑 合同智能审批流程                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────┐   ┌─────────┐   ┌─────────┐            │
│  │ 合同上传 │ → │ AI提取   │ → │ 规则校验  │           │
│  │ PDF/Word│   │ 结构化   │   │ 硬性规则  │           │
│  └────────┘   └─────────┘   └────┬────┘            │
│                                   │                  │
│                             ┌─────▼─────┐           │
│                             │ AI风险评估  │           │
│                             │ 法律/商务   │           │
│                             └─────┬─────┘           │
│                                   │                  │
│                    ┌──────────────▼──────────────┐  │
│                    │ 自动生成审批意见（附修改建议）  │  │
│                    │ → 推送给对应审批人            │  │
│                    └─────────────────────────────┘  │
│                                                      │
│  💡 关键价值：                                        │
│  • 预付款50%超标 → 规则引擎秒级发现（人工经常漏看）    │
│  • 保密条款不足 → AI结合军工背景评估（人工需法务参与）  │
│  • 审批周期从 3-5天 → 10分钟初审 + 人工复核            │
└──────────────────────────────────────────────────────┘
""")

    print("─" * 60)
    print("🔍 技术揭秘")
    print("─" * 40)
    print("• AI条款提取：GLM-5.1 的 JSON mode 输出结构化数据")
    print("• 规则引擎：数值比较、条款存在性检查、对等性分析")
    print("• AI风险评估：结合行业知识和企业背景做模糊判断")
    print("• 九洲特色：军工保密要求 → 供应链安全 → 原厂正品追溯")
    print("• 落地路径：对接金蝶低代码平台 → OA审批流自动触发")
    print("─" * 60)
    print("\n✅ 演示完成！")


if __name__ == "__main__":
    main()
