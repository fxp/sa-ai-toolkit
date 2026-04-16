---
id: "11"
name: "前端自动化测试 (Playwright)"
pattern: "test-intelligence"
universal_value: "AI不光写代码，还测代码——开发→测试一体化"
scoring_signals: ["M", "K", "H"]
impact_score: 5
offline: true
duration_min: 2
act: 4
mode: "backup"
---

## 核心价值主张

Playwright让AI控制真实浏览器做UI测试，测试脚本用Python写，可读性高，CI/CD集成容易。和一人军团组合，展示AI从"开发"到"验收"的全覆盖。

## 变量说明

| 占位符 | 说明 | 示例值（金融）| 示例值（制造）| 示例值（航天）|
|--------|------|--------------|--------------|--------------|
| {{测试场景}} | 要测试的业务流程 | 贷款申请表单填写→提交→结果页 | 工单创建→审批→完成流程 | 任务申请→审批→执行反馈 |
| {{测试网站}} | 演示时测试的URL | 内部OA系统/公开演示站 | ERP演示环境 | 任务管理系统/示例站 |
| {{关键断言}} | 最重要的测试验证点 | 提交后出现"申请编号"，无报错弹窗 | 审批完成后状态变为"已批准" | 任务创建后出现任务ID |

## 演示指令

```python
# Playwright测试脚本
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("{{测试网站}}")
    
    # 测试{{测试场景}}
    page.fill("#field1", "测试数据")
    page.click("#submit")
    page.wait_for_selector(".success-message")
    
    # 断言：{{关键断言}}
    assert page.title() != ""
    print(f"✅ 标题: {page.title()}")
    print(f"✅ 性能: TTFB:{perf}ms")
```

## 开场触发词

> "写完代码谁来测？传统方式：QA手工点。AI方式：AI控制浏览器自动点，还出报告——"

## WOW时刻

> 浏览器在演示者面前自动打开、填写、点击、截图，全程无人操作。

## 收尾金句

> "AI写了代码，AI测了代码，AI出了报告——开发到验收一条龙。{{测试场景}}从'人工1小时'变成'自动3分钟'。"
