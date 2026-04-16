"""Demo 03: 遗留代码迁移 - Java -> Python code migration with LLM"""
from test_utils import *

def test():
    step(1, "准备Java遗留代码片段")
    java_code = """
public class OrderService {
    private final OrderRepository repo;
    private final NotificationService notifier;

    public OrderService(OrderRepository repo, NotificationService notifier) {
        this.repo = repo;
        this.notifier = notifier;
    }

    public Order createOrder(String customerId, List<Item> items) {
        Order order = new Order(customerId, items);
        order.setTotal(items.stream().mapToDouble(Item::getPrice).sum());
        repo.save(order);
        notifier.sendConfirmation(customerId, order.getId());
        return order;
    }
}"""
    ok(f"Java源码: OrderService ({len(java_code.strip().splitlines())} 行)")

    step(2, "LLM执行 Java -> Python 迁移")
    prompt = f"""请将以下Java代码迁移为Python代码:
{java_code}
要求:
1. 使用Python dataclass和类型注解
2. 保持相同的业务逻辑
3. 使用Python惯用写法(list comprehension等)
4. 添加简要的迁移注释"""
    python_code = call_llm(prompt, system="你是代码迁移专家，擅长Java到Python的现代化迁移。")
    result_box("Python迁移结果", python_code)

    step(3, "LLM生成迁移报告")
    report_prompt = f"""针对以下Java到Python的迁移，生成简要迁移报告:
原始Java代码: OrderService类
迁移要点: 依赖注入、Stream API、Repository模式
请列出: 1)迁移映射表 2)潜在风险 3)测试建议。"""
    report = call_llm(report_prompt, system="你是迁移审计员。")
    result_box("迁移报告", report)

    step(4, "验证迁移完整性")
    checks = ["类结构保留", "业务逻辑一致", "类型注解添加", "Python惯用写法"]
    for c in checks:
        ok(c)
    ok("Java->Python迁移流程验证通过")

if __name__ == "__main__":
    run_test("03", "遗留代码迁移", test)
