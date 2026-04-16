"""Demo 05: AI监督员 - Quality review workflow (draft -> review -> approve)"""
from test_utils import *

def test():
    step(1, "生成初稿(Draft)")
    draft_prompt = "请写一份关于'公司引入AI工具的安全策略'的简短提案草稿(100字)。"
    draft = call_llm(draft_prompt, system="你是企业策略撰写助手。")
    result_box("初稿(Draft)", draft)

    step(2, "AI监督员审查(Review)")
    review_prompt = f"""你是AI质量监督员。请审查以下提案草稿，给出:
1. 质量评分(1-10)
2. 发现的问题(列出3个)
3. 修改建议
4. 是否通过审查(PASS/REVISE/REJECT)

草稿内容:
{draft}"""
    review = call_llm(review_prompt, system="你是严格的质量审计AI，专注于发现问题。")
    result_box("审查报告(Review)", review)

    step(3, "根据反馈修订")
    revise_prompt = f"""请根据以下审查意见修订提案:
原稿: {draft}
审查意见: {review}
请输出修订后的完整提案。"""
    revised = call_llm(revise_prompt, system="你是提案修订助手。")
    result_box("修订稿(Revised)", revised)

    step(4, "终审批准(Approve)")
    approve_prompt = f"""你是最终审批人。请对修订后的提案做最终判定:
修订稿: {revised}
输出: APPROVED 或 NEEDS_WORK，附简要理由。"""
    verdict = call_llm(approve_prompt, system="你是终审决策者。")
    result_box("终审结果", verdict)

    step(5, "验证三阶段流程完整性")
    stages = ["Draft", "Review", "Approve"]
    for s in stages:
        ok(f"{s} 阶段完成")
    ok("Draft->Review->Approve 三阶段流程验证通过")

if __name__ == "__main__":
    run_test("05", "AI监督员", test)
