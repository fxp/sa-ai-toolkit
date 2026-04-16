"""Demo 19: 投资人视角 - AI industrial stock analysis"""
from test_utils import *

def test():
    step(1, "定义分析标的和数据")
    target = {
        "公司": "智造科技(虚拟)",
        "行业": "工业AI / 智能制造",
        "市值": "¥85亿",
        "营收增速": "45% YoY",
        "毛利率": "62%",
        "研发占比": "28%",
        "客户数": 230,
        "ARR": "¥3.2亿",
    }
    for k, v in target.items():
        info(f"  {k}: {v}")
    ok("标的数据加载完成")

    step(2, "LLM生成行业分析")
    industry_prompt = f"""你是AI产业投资分析师。分析以下工业AI公司:
{target}
请输出:
1. 行业赛道评估(TAM/SAM/SOM)
2. 竞争格局(列出3个竞品)
3. 技术壁垒评估
4. 增长驱动因素"""
    industry = call_llm(industry_prompt, system="你是一级市场AI产业分析师。")
    result_box("行业分析", industry)

    step(3, "LLM生成财务模型摘要")
    finance_prompt = f"""根据以下数据构建简要财务模型:
营收增速: {target['营收增速']}
毛利率: {target['毛利率']}
ARR: {target['ARR']}
输出: 1)未来3年营收预测 2)盈利预期 3)估值区间(PS倍数法)。"""
    finance = call_llm(finance_prompt, system="你是财务建模专家。")
    result_box("财务模型", finance)

    step(4, "生成投资建议")
    advice_prompt = f"""综合分析:
行业: {industry}
财务: {finance}
给出: 1)投资评级(强烈推荐/推荐/中性/回避)
2)核心逻辑(3点) 3)主要风险(2点)。"""
    advice = call_llm(advice_prompt, system="你是投资决策委员会成员。")
    result_box("投资建议", advice)

    step(5, "验证分析框架完整性")
    ok("投资人视角分析框架验证通过 (行业->财务->建议)")

if __name__ == "__main__":
    run_test("19", "投资人视角", test)
