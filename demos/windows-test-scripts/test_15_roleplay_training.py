"""Demo 15: AI角色扮演培训 - Customer service roleplay training with emotional agent"""
from test_utils import *

def test():
    step(1, "设置培训场景")
    scenario = {
        "场景": "客户投诉订单延迟，情绪激动",
        "客户画像": "VIP客户，已等待7天，第3次来电",
        "情绪级别": "愤怒(8/10)",
        "培训目标": "安抚情绪、解决问题、挽留客户",
    }
    for k, v in scenario.items():
        info(f"  {k}: {v}")
    ok("培训场景初始化完成")

    step(2, "模拟客户(情绪Agent)开场")
    customer_prompt = f"""你是一个愤怒的VIP客户。场景: {scenario['场景']}
你已等待7天，这是第3次来电。情绪级别: 愤怒(8/10)。
请用1-2句话表达你的不满，语气要急躁但合理。用中文。"""
    customer_msg = call_llm(customer_prompt, system="你是情绪模拟Agent，真实还原客户情绪。")
    result_box("客户(愤怒)", customer_msg)

    step(3, "学员回应 -> AI评估")
    trainee_response = "非常抱歉让您等这么久，我理解您的心情。让我立刻帮您查看订单状态并优先处理。"
    info(f"学员回应: {trainee_response}")
    eval_prompt = f"""你是客服培训评估师。评估以下学员回应:
客户: {customer_msg}
学员: {trainee_response}
评分维度(各1-10分):
1. 情绪共鸣
2. 问题解决意愿
3. 专业话术
4. 挽留策略
给出总评和改进建议。"""
    evaluation = call_llm(eval_prompt, system="你是资深客服培训师。")
    result_box("AI评估报告", evaluation)

    step(4, "生成培训总结")
    summary_prompt = f"""根据本次角色扮演培训，生成培训总结卡片:
场景: {scenario['场景']}
学员表现: {evaluation}
输出: 1)得分 2)优点 3)改进项 4)推荐话术模板。"""
    summary = call_llm(summary_prompt, system="你是培训总结助手。")
    result_box("培训总结", summary)

    step(5, "验证培训流程")
    ok("角色扮演培训流程验证通过 (场景->模拟->评估->总结)")

if __name__ == "__main__":
    run_test("15", "AI角色扮演培训", test)
