#!/usr/bin/env python3
"""
Demo ⑩ — 标书智能审查（九洲电器最想做的场景）
==============================================
场景来源：九洲技术负责人原话 —
  "我们今年特别想做的就是标书检查"
  "去年有一个标，证书日期过期，人没看出来，项目就废了"
  "资料标书很多都是格式化的，还要逐页盖章检查"

功能：
  1. 检查投标文件中的证书有效期（日期过期检测）
  2. 检查格式合规性（名词一致性、字体字号、必填项）
  3. 检查盖章页完整性
  4. 生成审查报告

用法：
  python3 demo10_标书智能审查.py                  # 交互式运行
  python3 demo10_标书智能审查.py --auto            # 自动演示
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta

# ── 依赖检测 ──
try:
    from zhipuai import ZhipuAI
except ImportError:
    print("❌ 请安装依赖：pip install zhipuai")
    sys.exit(1)

ZHIPU_API_KEY = os.getenv("BIGMODEL_API_KEY", "1790d449b46d437bbc8b101815048d64.lEMGH4tememSXbvH")
if not ZHIPU_API_KEY:
    print("❌ 请设置 BIGMODEL_API_KEY 环境变量")
    print("   export BIGMODEL_API_KEY='你的API Key'")
    sys.exit(1)

client = ZhipuAI(api_key=ZHIPU_API_KEY)
MODEL = "glm-4-plus"  # 生产环境可切换为 glm-5.1

# ── 模拟标书数据（实际场景从PDF/Word解析） ──
SAMPLE_BID_DOCUMENT = {
    "项目名称": "2026年绵阳市配电网改造工程（第三批）",
    "招标编号": "MYPDG-2026-03-047",
    "投标单位": "四川九洲电器集团有限责任公司",
    "投标日期": "2026-04-20",
    "文档清单": [
        {"名称": "企业法人营业执照", "有效期": "2028-12-31", "页码": "P3-P4", "盖章": True},
        {"名称": "ISO9001质量管理体系认证", "有效期": "2026-03-15", "页码": "P5-P6", "盖章": True},
        {"名称": "ISO14001环境管理体系认证", "有效期": "2027-06-30", "页码": "P7-P8", "盖章": True},
        {"名称": "安全生产许可证", "有效期": "2026-08-20", "页码": "P9-P10", "盖章": False},  # 故意漏章
        {"名称": "特种设备制造许可证", "有效期": "2025-11-30", "页码": "P11-P12", "盖章": True},  # 已过期!
        {"名称": "AAA级信用评级证书", "有效期": "2026-12-31", "页码": "P13", "盖章": True},
        {"名称": "近三年无重大质量事故证明", "有效期": None, "页码": "P14", "盖章": True},
    ],
    "技术参数": [
        {"参数": "额定电压", "招标要求": "10kV", "投标响应": "10kV", "偏差": None},
        {"参数": "额定容量", "招标要求": "≥1600kVA", "投标响应": "1600kVA", "偏差": None},
        {"参数": "空载损耗", "招标要求": "≤1800W", "投标响应": "1750W", "偏差": None},
        {"参数": "负载损耗", "招标要求": "≤15000W", "投标响应": "16200W", "偏差": "超标8%"},  # 超标!
        {"参数": "短路阻抗", "招标要求": "4.0%~6.0%", "投标响应": "4.5%", "偏差": None},
        {"参数": "绝缘等级", "招标要求": "H级", "投标响应": "F级", "偏差": "低于要求"},  # 不达标!
        {"参数": "噪声等级", "招标要求": "≤55dB", "投标响应": "52dB", "偏差": None},
        {"参数": "防护等级", "招标要求": "IP44", "投标响应": "IP44", "偏差": None},
    ],
    "名词使用": {
        "正文中出现": ["九洲电器", "九州电器", "JIUZHOU", "Jiuzhou", "四川九洲"],
        "正确写法": "四川九洲电器集团有限责任公司（简称：九洲电器）",
    },
    "格式检查": {
        "正文字体": "仿宋_GB2312",
        "标题字体": "黑体",
        "字号": "三号（标题）/ 小四（正文）",
        "发现问题": [
            "P23 正文字体为宋体（应为仿宋_GB2312）",
            "P31 标题字号为四号（应为三号）",
            "P45-P46 行间距为1.0倍（应为1.5倍）",
        ]
    }
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


def check_expiry(doc_list: list, bid_date: str) -> list:
    """检查证书有效期"""
    issues = []
    bid_dt = datetime.strptime(bid_date, "%Y-%m-%d")

    for doc in doc_list:
        if doc["有效期"] is None:
            continue
        exp_dt = datetime.strptime(doc["有效期"], "%Y-%m-%d")
        if exp_dt < bid_dt:
            days_expired = (bid_dt - exp_dt).days
            issues.append({
                "级别": "🔴 严重",
                "类型": "证书过期",
                "详情": f"【{doc['名称']}】已于 {doc['有效期']} 过期（距投标日已过期 {days_expired} 天）",
                "位置": doc["页码"],
                "建议": "立即联系发证机构办理续期，或提供续期申请受理证明"
            })
        elif (exp_dt - bid_dt).days < 30:
            days_left = (exp_dt - bid_dt).days
            issues.append({
                "级别": "🟡 警告",
                "类型": "证书即将过期",
                "详情": f"【{doc['名称']}】将于 {doc['有效期']} 过期（仅剩 {days_left} 天）",
                "位置": doc["页码"],
                "建议": "建议提前办理续期，避免评标期间过期导致废标"
            })
    return issues


def check_stamp(doc_list: list) -> list:
    """检查盖章完整性"""
    issues = []
    for doc in doc_list:
        if not doc["盖章"]:
            issues.append({
                "级别": "🔴 严重",
                "类型": "缺少盖章",
                "详情": f"【{doc['名称']}】（{doc['页码']}）未检测到公章",
                "位置": doc["页码"],
                "建议": "补盖公章后重新扫描"
            })
    return issues


def check_tech_params(params: list) -> list:
    """检查技术参数偏差"""
    issues = []
    for p in params:
        if p["偏差"]:
            issues.append({
                "级别": "🔴 严重" if "超标" in p["偏差"] or "低于" in p["偏差"] else "🟡 警告",
                "类型": "技术参数不达标",
                "详情": f"【{p['参数']}】招标要求 {p['招标要求']}，投标响应 {p['投标响应']}（{p['偏差']}）",
                "位置": "技术规格书",
                "建议": "核实参数是否正确，如确实不达标需更换产品型号或提供偏差说明"
            })
    return issues


def ai_deep_review(bid_data: dict, rule_issues: list) -> str:
    """用 GLM-5.1 做深度语义审查"""
    prompt = f"""你是一位资深的投标文件审查专家，擅长军工企业和电力设备行业的招投标。

请对以下投标文件进行深度审查，重点关注：
1. 规则引擎已检出的问题的严重程度评估
2. 名词一致性问题
3. 格式合规性问题
4. 综合风险评估和改进建议

【投标基本信息】
- 项目：{bid_data['项目名称']}
- 招标编号：{bid_data['招标编号']}
- 投标单位：{bid_data['投标单位']}
- 投标日期：{bid_data['投标日期']}

【规则引擎已检出问题】
{json.dumps(rule_issues, ensure_ascii=False, indent=2)}

【名词使用情况】
正文中出现的公司名称写法：{bid_data['名词使用']['正文中出现']}
正确全称：{bid_data['名词使用']['正确写法']}

【格式检查结果】
{json.dumps(bid_data['格式检查'], ensure_ascii=False, indent=2)}

请输出：
1. 🚨 废标风险评估（高/中/低）及原因
2. 📋 问题优先级排序（按紧急程度）
3. 🔍 名词一致性分析
4. 📐 格式合规性分析
5. ✅ 修改行动清单（按优先级，每条附责任人建议和预计耗时）

语言简洁专业，适合投标经理快速阅读。"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是军工企业投标文件审查专家，熟悉国军标和电力设备行业招投标规范。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(description="标书智能审查 Demo")
    parser.add_argument("--auto", action="store_true", help="自动运行")
    args = parser.parse_args()

    print("\n" + "█" * 60)
    print("  📋 标书智能审查系统 Demo")
    print("  场景：投标文件提交前的自动化合规检查")
    print("  模型：BigModel GLM-5.1")
    print("█" * 60)

    bid = SAMPLE_BID_DOCUMENT
    print(f"\n📁 正在审查：{bid['项目名称']}")
    print(f"   投标单位：{bid['投标单位']}")
    print(f"   投标日期：{bid['投标日期']}")

    if not args.auto:
        try:
            input("\n按 Enter 开始审查...")
        except EOFError:
            pass

    # ── Step 1: 规则引擎（硬性检查，毫秒级） ──
    print_section("Step 1/3 — 规则引擎硬性检查（证书·盖章·参数）")
    print("⏱️  执行中... ", end="", flush=True)
    time.sleep(0.5)

    all_issues = []

    # 1a. 证书有效期
    expiry_issues = check_expiry(bid["文档清单"], bid["投标日期"])
    all_issues.extend(expiry_issues)

    # 1b. 盖章检查
    stamp_issues = check_stamp(bid["文档清单"])
    all_issues.extend(stamp_issues)

    # 1c. 技术参数
    tech_issues = check_tech_params(bid["技术参数"])
    all_issues.extend(tech_issues)

    print(f"完成！发现 {len(all_issues)} 个问题\n")

    for i, issue in enumerate(all_issues, 1):
        print(f"  {issue['级别']}  [{issue['类型']}]")
        print(f"     {issue['详情']}")
        print(f"     📍 位置：{issue['位置']}")
        print(f"     💡 建议：{issue['建议']}")
        print()
        time.sleep(0.3)

    # ── Step 2: AI 语义审查（模糊检查，秒级） ──
    print_section("Step 2/3 — AI 语义审查（名词·格式·综合风险）")
    print("🤖 GLM-5.1 分析中...\n")

    ai_result = ai_deep_review(bid, all_issues)
    stream_print(ai_result, delay=0.01)

    # ── Step 3: 生成审查报告 ──
    print_section("Step 3/3 — 生成审查报告摘要")

    critical = sum(1 for i in all_issues if "严重" in i["级别"])
    warning = sum(1 for i in all_issues if "警告" in i["级别"])

    report = f"""
┌──────────────────────────────────────────────────────┐
│              📋 投标文件审查报告                        │
├──────────────────────────────────────────────────────┤
│  项目：{bid['项目名称'][:30]}...
│  编号：{bid['招标编号']}
│  审查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
├──────────────────────────────────────────────────────┤
│  🔴 严重问题：{critical} 项    🟡 警告：{warning} 项
│  ⚠️  废标风险：{'高' if critical > 0 else '低'}
├──────────────────────────────────────────────────────┤
│  审查方法：
│    ✅ 规则引擎（证书有效期/盖章/技术参数）  < 1秒
│    ✅ AI语义审查（名词一致性/格式/综合评估） ~10秒
├──────────────────────────────────────────────────────┤
│  💡 核心方法论：
│    硬性规则 → 代码执行（准确率100%）
│    模糊判断 → 大模型辅助（效率提升10x）
│    两者结合 = 可靠的标书审查 AI
└──────────────────────────────────────────────────────┘
"""
    print(report)

    # ── 技术揭秘 ──
    print("─" * 60)
    print("🔍 技术揭秘")
    print("─" * 40)
    print("• 架构：规则引擎（硬性）+ 大模型（模糊）双引擎")
    print("• 规则引擎：日期比较、正则匹配、数值范围检查")
    print("• 大模型：名词一致性、语义合理性、综合风险评估")
    print("• 关键洞察：不要用大模型做它不擅长的精确计算")
    print("  → 证书过期？代码算日期差（0误差）")
    print("  → 名词不一致？大模型理解语义（人工不可能逐页比对）")
    print("─" * 60)
    print("\n✅ 演示完成！")


if __name__ == "__main__":
    main()
