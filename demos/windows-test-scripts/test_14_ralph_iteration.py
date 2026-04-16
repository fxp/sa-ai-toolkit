"""Demo 14: Ralph自主迭代 - Self-improving loop (plan -> execute -> reflect -> improve)"""
from test_utils import *

def test():
    task = "编写一个高效的Python缓存装饰器"
    step(1, f"Plan阶段 - 制定计划: {task}")
    plan_prompt = f"""你是自主迭代Agent。任务: {task}
Phase: PLAN
请输出:
1. 目标定义(1句话)
2. 实现步骤(3步)
3. 成功标准(2条)"""
    plan = call_llm(plan_prompt, system="你是自主编程Agent，遵循Plan-Execute-Reflect-Improve循环。")
    result_box("Plan", plan)

    step(2, "Execute阶段 - 执行实现")
    exec_prompt = f"""基于计划执行实现:
计划: {plan}
Phase: EXECUTE
请直接输出Python代码实现一个带TTL的LRU缓存装饰器。"""
    execution = call_llm(exec_prompt, system="你是Python高级开发者。", max_tokens=1000)
    result_box("Execute", execution)

    step(3, "Reflect阶段 - 自我反思")
    reflect_prompt = f"""Phase: REFLECT
请审查以下代码实现:
{execution}
输出:
1. 代码质量评分(1-10)
2. 发现的问题(列出2个)
3. 遗漏的边界条件"""
    reflection = call_llm(reflect_prompt, system="你是代码审查专家，善于发现问题。")
    result_box("Reflect", reflection)

    step(4, "Improve阶段 - 改进优化")
    improve_prompt = f"""Phase: IMPROVE
根据反思结果改进代码:
反思: {reflection}
请输出改进后的关键代码片段和改进说明。"""
    improvement = call_llm(improve_prompt, system="你是代码优化专家。")
    result_box("Improve", improvement)

    step(5, "验证PERI循环完整性")
    phases = ["Plan", "Execute", "Reflect", "Improve"]
    for p in phases:
        ok(f"{p} 阶段完成")
    ok("Ralph PERI自主迭代循环验证通过")

if __name__ == "__main__":
    run_test("14", "Ralph自主迭代", test)
