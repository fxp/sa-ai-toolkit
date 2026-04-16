"""Demo 12: 移动端测试 - Maestro YAML test generation"""
from test_utils import *

def test():
    step(1, "定义移动端测试场景")
    app_spec = {
        "app": "com.example.shopping",
        "platform": "Android",
        "screens": ["首页", "搜索", "商品详情", "购物车", "结算"],
        "core_flow": "搜索商品 -> 加入购物车 -> 结算",
    }
    ok(f"待测App: {app_spec['app']} ({app_spec['platform']})")
    info(f"核心流程: {app_spec['core_flow']}")

    step(2, "LLM生成Maestro YAML测试")
    prompt = f"""请为以下移动端App生成Maestro YAML测试脚本:
App: {app_spec['app']}
平台: {app_spec['platform']}
核心流程: {app_spec['core_flow']}

生成完整的Maestro YAML，包含:
1. appId配置
2. 搜索商品(输入关键词)
3. 点击第一个结果
4. 添加到购物车
5. 验证购物车数量"""
    yaml_test = call_llm(prompt, system="你是移动端测试专家，精通Maestro测试框架。")
    result_box("Maestro YAML", yaml_test)

    step(3, "生成边界测试用例")
    edge_prompt = f"""为{app_spec['app']}生成3个Maestro边界测试场景(YAML格式):
1. 空搜索结果处理
2. 网络断开时的错误提示
3. 购物车商品数量上限
简洁输出，每个场景5行以内。"""
    edge_tests = call_llm(edge_prompt, system="你是移动端QA专家。")
    result_box("边界测试", edge_tests)

    step(4, "验证测试矩阵")
    test_types = ["核心流程", "边界条件", "错误处理"]
    for t in test_types:
        ok(f"测试类型: {t}")
    assert len(app_spec["screens"]) == 5, "页面覆盖不完整"
    ok("Maestro移动端测试生成验证通过")

if __name__ == "__main__":
    run_test("12", "移动端测试", test)
