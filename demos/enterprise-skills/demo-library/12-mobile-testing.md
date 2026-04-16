---
id: "12"
name: "移动端测试 (Maestro)"
pattern: "test-intelligence"
universal_value: "YAML可读测试脚本：业务人员也能看懂测试在干什么"
scoring_signals: ["M", "K"]
impact_score: 5
offline: true
duration_min: 2
act: 4
mode: "backup"
---

## 核心价值主张

Maestro用YAML写移动端测试流程，像在描述操作步骤一样写测试——产品经理能读懂，开发和QA能维护，AI能自动生成。

## 变量说明

| 占位符 | 说明 | 示例值（金融）| 示例值（制造）| 示例值（航天）|
|--------|------|--------------|--------------|--------------|
| {{App名称}} | 要测试的移动应用 | 手机银行App | 设备巡检App | 维修工单App |
| {{App包名}} | App的package ID | com.bank.mobile | com.factory.patrol | com.maint.orders |
| {{测试流程}} | 要测试的用户旅程 | 登录→查余额→转账→查账单 | 登录→创建巡检→拍照上传→提交 | 登录→查看工单→完成填写→提交 |

## YAML模板

```yaml
appId: {{App包名}}
---
- launchApp
- assertVisible: "登录"
- tapOn: "用户名"
- inputText: "test_user"
- tapOn: "密码"
- inputText: "password123"
- tapOn: "登录"
- assertVisible: "{{测试流程第一个验证点}}"
- takeScreenshot: login_success
```

## 开场触发词

> "这是Maestro给{{App名称}}写的测试脚本——你不需要是工程师也能看懂，因为它就是在描述用户操作步骤。"

## WOW时刻

> 展示AI自动生成了完整的YAML流程，和手写的几乎一样，但节省了30分钟。

## 收尾金句

> "YAML可读测试：业务人员能审，开发人员能改，AI能生成。{{App名称}}的回归测试从'手工1天'变成'自动10分钟'。"
