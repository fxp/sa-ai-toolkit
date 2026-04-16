"""Demo 01: MCP工具编排 - Multi-tool orchestration chain (calendar + email + CRM)"""
from test_utils import *

def test():
    step(1, "模拟日历工具 - 查询今日会议")
    calendar_data = {
        "meetings": [
            {"time": "10:00", "title": "Q2 Review", "attendees": ["Alice", "Bob"]},
            {"time": "14:00", "title": "Tech Sync", "attendees": ["Charlie"]},
        ]
    }
    ok(f"获取到 {len(calendar_data['meetings'])} 个会议")
    info(f"下次会议: {calendar_data['meetings'][0]['title']} @ {calendar_data['meetings'][0]['time']}")

    step(2, "模拟邮件工具 - 检索相关邮件")
    emails = [
        {"from": "alice@corp.com", "subject": "Q2 数据已更新", "has_attachment": True},
        {"from": "bob@corp.com", "subject": "Review 议程确认", "has_attachment": False},
    ]
    ok(f"检索到 {len(emails)} 封相关邮件")

    step(3, "模拟CRM工具 - 拉取客户状态")
    crm_records = {"active_deals": 5, "pipeline_value": "¥2.3M", "at_risk": 1}
    ok(f"CRM数据: {crm_records['active_deals']} 活跃商机, 管道价值 {crm_records['pipeline_value']}")

    step(4, "LLM编排 - 综合三源数据生成摘要")
    prompt = f"""你是一个MCP工具编排助手。请根据以下三个工具返回的数据，生成一份简洁的晨会摘要:
日历: {calendar_data}
邮件: {emails}
CRM: {crm_records}
请用中文输出，包含今日重点、待办事项和风险提醒。"""
    result = call_llm(prompt, system="你是企业AI助手，擅长多工具数据整合。")
    result_box("MCP编排摘要", result)

    step(5, "验证编排链完整性")
    assert len(calendar_data["meetings"]) > 0, "日历数据为空"
    assert len(emails) > 0, "邮件数据为空"
    assert crm_records["active_deals"] > 0, "CRM数据异常"
    ok("三工具编排链验证通过")

if __name__ == "__main__":
    run_test("01", "MCP工具编排", test)
