"""Demo 07: 多Agent辩论 - Multi-agent debate (3 agents argue a topic)"""
from test_utils import *

def test():
    topic = "企业应该全面拥抱AI还是谨慎试点？"
    step(1, f"设定辩题: {topic}")
    agents = {
        "激进派(Agent A)": "你坚定支持全面拥抱AI，认为速度决定生死。",
        "保守派(Agent B)": "你主张谨慎试点，认为风险控制优先。",
        "中立派(Agent C)": "你是理性中立方，综合双方观点给出平衡建议。",
    }
    for name, role in agents.items():
        ok(f"{name} 已就位")

    step(2, "第一轮: 各方开场陈述")
    statements = {}
    for name, role in agents.items():
        prompt = f"辩题: {topic}\n请用3-4句话阐述你的核心立场。"
        resp = call_llm(prompt, system=role)
        statements[name] = resp
        result_box(f"{name} 开场", resp)

    step(3, "第二轮: 交叉质询")
    debate_context = "\n".join([f"{k}: {v}" for k, v in statements.items()])
    rebuttal_prompt = f"""辩题: {topic}
各方立场:
{debate_context}

你是激进派，请针对保守派的观点提出2个尖锐质疑。"""
    rebuttal = call_llm(rebuttal_prompt, system=agents["激进派(Agent A)"])
    result_box("交叉质询", rebuttal)

    step(4, "第三轮: 中立方总结裁决")
    judge_prompt = f"""辩题: {topic}
各方论述:
{debate_context}

请作为中立裁判，给出:
1. 双方最有力论点各1个
2. 最终建议(50字内)
3. 推荐策略(激进/保守/混合)"""
    verdict = call_llm(judge_prompt, system=agents["中立派(Agent C)"])
    result_box("中立方裁决", verdict)

    step(5, "验证辩论流程")
    assert len(statements) == 3, "辩手数量不足"
    ok("三Agent辩论流程验证通过 (开场->质询->裁决)")

if __name__ == "__main__":
    run_test("07", "多Agent辩论", test)
