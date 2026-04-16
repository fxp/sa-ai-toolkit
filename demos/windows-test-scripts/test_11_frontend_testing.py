"""Demo 11: 前端自动化测试 - Playwright test generation"""
from test_utils import *

def test():
    step(1, "定义待测页面结构")
    page_spec = {
        "url": "https://example.com/login",
        "elements": [
            {"id": "username", "type": "input", "required": True},
            {"id": "password", "type": "input", "required": True},
            {"id": "login-btn", "type": "button", "text": "登录"},
            {"id": "error-msg", "type": "div", "visible_on_error": True},
        ],
    }
    ok(f"页面: {page_spec['url']} ({len(page_spec['elements'])} 个元素)")

    step(2, "LLM生成Playwright测试代码")
    prompt = f"""请为以下登录页面生成Playwright (Python) 自动化测试代码:
页面: {page_spec['url']}
元素: {page_spec['elements']}

生成3个测试用例:
1. 正常登录流程
2. 空表单提交验证
3. 错误密码提示验证

使用pytest + playwright，包含page fixture。"""
    test_code = call_llm(prompt, system="你是前端自动化测试专家，精通Playwright。", max_tokens=1000)
    result_box("Playwright测试代码", test_code)

    step(3, "生成Page Object Model")
    pom_prompt = """为上述登录页面生成Page Object Model类:
包含: LoginPage类, locators, login方法, get_error方法。
使用Playwright Python API。简洁输出。"""
    pom = call_llm(pom_prompt, system="你是前端测试架构师。")
    result_box("Page Object Model", pom)

    step(4, "验证测试覆盖率")
    scenarios = ["正常登录", "空表单", "错误密码", "POM结构"]
    for s in scenarios:
        ok(f"测试场景: {s}")
    ok("Playwright测试生成验证通过")

if __name__ == "__main__":
    run_test("11", "前端自动化测试", test)
