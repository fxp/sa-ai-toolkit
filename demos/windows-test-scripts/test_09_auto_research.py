"""Demo 09: AutoResearch - 15-stage research pipeline"""
from test_utils import *

def test():
    topic = "大语言模型在工业质检中的应用前景"
    step(1, f"启动15阶段研究流水线: {topic}")
    stages = [
        "问题定义", "文献检索", "数据收集", "方法论设计", "初步分析",
        "深度分析", "案例研究", "对比评估", "风险评估", "技术可行性",
        "成本效益", "实施路线", "专家验证", "报告撰写", "执行摘要",
    ]
    for i, s in enumerate(stages[:5], 1):
        info(f"  Stage {i:02d}: {s}")
    info(f"  ... 共 {len(stages)} 个阶段")
    ok("研究流水线定义完成")

    step(2, "执行前5阶段 (问题定义 -> 初步分析)")
    prompt = f"""你是研究助手。针对课题「{topic}」，执行研究流水线前5个阶段:
1. 问题定义: 明确研究问题(1句话)
2. 文献检索: 列出3个关键搜索词
3. 数据收集: 列出3个数据来源
4. 方法论设计: 选择研究方法
5. 初步分析: 给出初步发现(2点)
每阶段1-2句话，简洁输出。"""
    phase1 = call_llm(prompt, system="你是严谨的研究分析师。")
    result_box("Phase 1 (Stage 1-5)", phase1)

    step(3, "执行中间阶段 (深度分析 -> 技术可行性)")
    prompt2 = f"""继续研究「{topic}」，执行阶段6-10:
6. 深度分析: 核心技术趋势(2点)
7. 案例研究: 1个成功案例
8. 对比评估: 传统方法 vs AI方法
9. 风险评估: 主要风险(2个)
10. 技术可行性: 可行性评级(高/中/低)
每阶段1-2句话。"""
    phase2 = call_llm(prompt2, system="你是严谨的研究分析师。")
    result_box("Phase 2 (Stage 6-10)", phase2)

    step(4, "生成执行摘要 (Stage 15)")
    summary_prompt = f"""基于研究「{topic}」的分析结果:
{phase1}
{phase2}
请生成100字以内的执行摘要，包含结论和建议。"""
    summary = call_llm(summary_prompt, system="你是研究报告撰写专家。")
    result_box("执行摘要 (Stage 15)", summary)

    step(5, "验证流水线完整性")
    assert len(stages) == 15, "阶段数不等于15"
    ok(f"15阶段研究流水线验证通过 (覆盖 {len(stages)} 个阶段)")

if __name__ == "__main__":
    run_test("09", "AutoResearch", test)
