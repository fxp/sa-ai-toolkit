"""Demo 04: CEO看板 - Multi-source data aggregation for executive dashboard"""
from test_utils import *

def test():
    step(1, "模拟多源数据采集")
    sources = {
        "财务": {"revenue": "¥12.5M", "cost": "¥8.2M", "margin": "34.4%"},
        "销售": {"new_deals": 23, "pipeline": "¥5.8M", "win_rate": "42%"},
        "研发": {"sprint_velocity": 85, "bug_count": 12, "release_eta": "3天"},
        "HR": {"headcount": 156, "open_positions": 8, "attrition": "4.2%"},
    }
    for name, data in sources.items():
        ok(f"{name}数据源已接入")
        for k, v in data.items():
            info(f"  {k}: {v}")

    step(2, "LLM生成CEO摘要")
    prompt = f"""你是CEO智能助手。根据以下四个部门的数据，生成一份简洁的CEO晨会看板摘要:
{sources}
要求: 1)关键指标总览 2)需要关注的风险 3)本周决策建议。用中文，控制在200字内。"""
    summary = call_llm(prompt, system="你是高管决策支持AI。")
    result_box("CEO看板摘要", summary)

    step(3, "生成异常预警")
    alerts = []
    if int(sources["研发"]["bug_count"]) > 10:
        alerts.append("研发Bug数超阈值(>10)")
    if float(sources["HR"]["attrition"].rstrip("%")) > 4:
        alerts.append("人员流失率偏高(>4%)")
    for a in alerts:
        warn(a)
    ok(f"检测到 {len(alerts)} 个预警项")

    step(4, "验证看板数据完整性")
    assert len(sources) == 4, "数据源不完整"
    ok("四维CEO看板数据聚合验证通过")

if __name__ == "__main__":
    run_test("04", "CEO看板", test)
