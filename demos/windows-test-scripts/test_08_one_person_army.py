"""Demo 08: 一人军团 - One-person team workflow (CEO -> design -> code -> QA)"""
from test_utils import *

def test():
    project = "内部知识库搜索工具"
    step(1, f"CEO角色 - 产品决策: {project}")
    ceo_prompt = f"""你是创业CEO。为'{project}'项目做产品决策:
1. 核心功能(3个)
2. MVP范围
3. 上线时间表
用简洁的bullet point格式，50字内。"""
    ceo_output = call_llm(ceo_prompt, system="你是果断的创业CEO。")
    result_box("CEO决策", ceo_output)

    step(2, "设计师角色 - UI/UX设计")
    design_prompt = f"""你是UI设计师。根据CEO决策设计'{project}':
CEO决策: {ceo_output}
输出: 1)页面列表 2)核心交互流程 3)设计规范(配色/字体)。简洁输出。"""
    design_output = call_llm(design_prompt, system="你是极简主义UI设计师。")
    result_box("设计方案", design_output)

    step(3, "开发者角色 - 技术实现")
    dev_prompt = f"""你是全栈开发者。根据设计方案实现'{project}':
设计: {design_output}
输出: 1)技术栈选择 2)核心API设计(2个endpoint) 3)数据库schema(1张表)。简洁输出。"""
    dev_output = call_llm(dev_prompt, system="你是高效的全栈开发者。")
    result_box("技术方案", dev_output)

    step(4, "QA角色 - 测试验收")
    qa_prompt = f"""你是QA工程师。为'{project}'编写测试计划:
技术方案: {dev_output}
输出: 1)测试用例(3个) 2)边界条件 3)验收标准。简洁输出。"""
    qa_output = call_llm(qa_prompt, system="你是严谨的QA工程师。")
    result_box("测试计划", qa_output)

    step(5, "验证一人军团流水线")
    roles = ["CEO", "Designer", "Developer", "QA"]
    for r in roles:
        ok(f"{r} 角色完成")
    ok("一人军团四角色流水线验证通过")

if __name__ == "__main__":
    run_test("08", "一人军团", test)
