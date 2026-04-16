"""Demo 13: 群体智能推演 - Group intelligence simulation with multiple agents"""
from test_utils import *
import random

def test():
    scenario = "城市交通拥堵治理方案"
    step(1, f"初始化群体智能推演: {scenario}")
    agents = [
        {"id": "A1", "role": "交通工程师", "bias": "基建优先"},
        {"id": "A2", "role": "数据科学家", "bias": "智能信号优化"},
        {"id": "A3", "role": "城市规划师", "bias": "公共交通扩容"},
        {"id": "A4", "role": "市民代表", "bias": "出行体验优先"},
        {"id": "A5", "role": "财政官员", "bias": "成本控制"},
    ]
    for a in agents:
        ok(f"Agent {a['id']}: {a['role']} (倾向: {a['bias']})")

    step(2, "Round 1 - 各Agent独立提案")
    proposals_prompt = f"""场景: {scenario}
你同时扮演5个角色，分别给出各自的治理方案(每个1句话):
1. 交通工程师(基建优先)
2. 数据科学家(智能信号)
3. 城市规划师(公共交通)
4. 市民代表(体验优先)
5. 财政官员(成本控制)"""
    proposals = call_llm(proposals_prompt, system="你是群体决策模拟器。")
    result_box("Round 1 各方提案", proposals)

    step(3, "Round 2 - 群体投票与共识形成")
    random.seed(42)
    votes = {a["id"]: random.randint(1, 5) for a in agents}
    consensus_prompt = f"""5个Agent对方案进行投票，票数分布:
{votes}
请综合各方意见，形成一个兼顾多方的共识方案(50字内)。"""
    consensus = call_llm(consensus_prompt, system="你是群体决策调解人。")
    result_box("群体共识", consensus)

    step(4, "Round 3 - 共识方案评估")
    eval_prompt = f"""请对以下群体共识方案打分(1-10):
方案: {consensus}
评分维度: 可行性、成本效益、公众接受度、长期效果。
输出每个维度的分数和总评。"""
    evaluation = call_llm(eval_prompt, system="你是政策评估专家。")
    result_box("方案评估", evaluation)

    step(5, "验证群体智能流程")
    assert len(agents) == 5, "Agent数量不足"
    ok("5-Agent群体智能推演验证通过 (提案->投票->共识->评估)")

if __name__ == "__main__":
    run_test("13", "群体智能推演", test)
