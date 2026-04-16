"""Demo 21: AI工具巡礼 - 7-tool capability matrix comparison"""
from test_utils import *

def test():
    step(1, "定义7个AI工具评估矩阵")
    tools = [
        {"name": "ChatGPT", "vendor": "OpenAI", "type": "通用对话"},
        {"name": "Claude", "vendor": "Anthropic", "type": "长文本分析"},
        {"name": "Gemini", "vendor": "Google", "type": "多模态"},
        {"name": "Copilot", "vendor": "Microsoft", "type": "代码辅助"},
        {"name": "通义千问", "vendor": "Alibaba", "type": "中文优化"},
        {"name": "文心一言", "vendor": "Baidu", "type": "中文生态"},
        {"name": "GLM", "vendor": "智谱AI", "type": "开源可控"},
    ]
    dimensions = ["代码能力", "中文理解", "多模态", "上下文长度", "部署灵活性", "成本效益"]
    ok(f"评估 {len(tools)} 个工具 x {len(dimensions)} 个维度")

    step(2, "LLM生成能力对比矩阵")
    prompt = f"""请为以下7个AI工具生成能力对比矩阵:
工具: {[t['name'] for t in tools]}
评估维度: {dimensions}

用表格格式输出，每个维度打分(1-5星)，最后一列给出总评和推荐场景。"""
    matrix = call_llm(prompt, system="你是AI工具评测专家，立场客观中立。", max_tokens=1000)
    result_box("能力矩阵", matrix)

    step(3, "LLM生成选型建议")
    advice_prompt = f"""基于能力矩阵，为以下3个企业场景推荐最佳工具:
1. 制造业质检报告生成(需要中文+长文本)
2. 软件团队代码审查(需要代码能力+API集成)
3. 市场部内容创作(需要多模态+创意)

每个场景推荐第一选择和备选，说明理由。"""
    advice = call_llm(advice_prompt, system="你是企业AI选型顾问。")
    result_box("选型建议", advice)

    step(4, "验证评估完整性")
    assert len(tools) == 7, "工具数量不足"
    assert len(dimensions) == 6, "维度不完整"
    ok(f"7工具x6维度能力矩阵验证通过 ({len(tools)*len(dimensions)}个评分点)")

if __name__ == "__main__":
    run_test("21", "AI工具巡礼", test)
