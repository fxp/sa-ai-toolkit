"""Demo 22: Org-Uplift推演 - METR game (4 rounds, success dice, bottleneck tracking)"""
from test_utils import *
import random

def test():
    step(1, "初始化METR推演参数")
    org = {
        "公司": "中型制造企业(500人)",
        "AI成熟度": "Level 1 (试点阶段)",
        "预算": "¥200万/年",
        "目标": "12个月内达到Level 3 (规模化)",
    }
    bottlenecks = {"人才": 3, "数据": 4, "流程": 2, "文化": 5, "技术": 3}
    for k, v in org.items():
        info(f"  {k}: {v}")
    section("初始瓶颈分数 (1-5, 越高越严重)")
    for k, v in bottlenecks.items():
        info(f"  {k}: {'*' * v} ({v}/5)")
    ok("推演初始化完成")

    random.seed(42)
    for round_num in range(1, 5):
        step(round_num + 1, f"Round {round_num} - 决策与掷骰")
        # Simulate dice roll for success
        dice = random.randint(1, 6)
        threshold = max(bottlenecks.values())
        success = dice >= threshold

        round_prompt = f"""METR推演 Round {round_num}:
组织: {org['公司']}
当前瓶颈: {bottlenecks}
骰子结果: {dice} (阈值: {threshold})
{'成功' if success else '失败'}!

请给出:
1. 本轮采取的AI举措(1句话)
2. 瓶颈变化(哪个维度+/-1)
3. 经验教训(1句话)"""
        round_result = call_llm(round_prompt, system="你是组织变革顾问，擅长METR推演。")
        result_box(f"Round {round_num} ({'PASS' if success else 'FAIL'}, dice={dice})", round_result)

        # Update bottlenecks
        worst = max(bottlenecks, key=bottlenecks.get)
        if success:
            bottlenecks[worst] = max(1, bottlenecks[worst] - 1)
        else:
            random_dim = random.choice(list(bottlenecks.keys()))
            bottlenecks[random_dim] = min(5, bottlenecks[random_dim] + 1)

    section("最终瓶颈状态")
    for k, v in bottlenecks.items():
        info(f"  {k}: {'*' * v} ({v}/5)")
    final_score = sum(bottlenecks.values())
    ok(f"4轮推演完成，总瓶颈分: {final_score}/25")

if __name__ == "__main__":
    run_test("22", "Org-Uplift推演", test)
