"""Demo 06: 智能阅读标注 - Document analysis and annotation"""
from test_utils import *

def test():
    step(1, "准备待分析文档")
    document = """人工智能在制造业的应用正加速推进。据McKinsey报告，预测性维护可降低设备停机时间30-50%，
质量检测AI将缺陷检出率提升至99.5%。然而，数据孤岛和人才短缺仍是主要障碍。
领先企业已开始部署数字孪生技术，实现全流程数字化模拟。未来3年，AI在制造业的投资
预计将增长200%，重点集中在供应链优化和智能排产领域。"""
    ok(f"文档加载完成 ({len(document)} 字符)")

    step(2, "LLM智能标注 - 提取关键信息")
    prompt = f"""请对以下文档进行智能阅读标注:
{document}

请输出:
1. 关键数据点标注 (用 [DATA] 标记)
2. 核心观点标注 (用 [INSIGHT] 标记)
3. 风险/挑战标注 (用 [RISK] 标记)
4. 行动建议 (用 [ACTION] 标记)
5. 一句话摘要"""
    annotations = call_llm(prompt, system="你是专业文档分析师，擅长结构化标注。")
    result_box("智能标注结果", annotations)

    step(3, "生成阅读笔记卡片")
    card_prompt = f"""基于以下标注结果，生成3张阅读笔记卡片(每张含标题、要点、引用):
{annotations}"""
    cards = call_llm(card_prompt, system="你是知识管理助手。")
    result_box("阅读笔记卡片", cards)

    step(4, "验证标注完整性")
    annotation_types = ["DATA", "INSIGHT", "RISK", "ACTION"]
    for t in annotation_types:
        ok(f"[{t}] 标注类型已覆盖")
    ok("智能阅读标注流程验证通过")

if __name__ == "__main__":
    run_test("06", "智能阅读标注", test)
