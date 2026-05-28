# Demo 代码模板

> 以下模板已在九洲电器培训中实战验证。
> 生成新企业方案时，复制模板并替换企业数据。

## 模板文件位置

九洲培训项目目录（作为参考模板源）：
```
/Users/xiaopingfeng/Library/Mobile Documents/iCloud~md~obsidian/Documents/Projects/Enterprise AI Training/output/
```

## 可直接复用的模板

| Demo | 模板文件 | 需要替换的内容 |
|------|---------|-------------|
| A1 | demo_验证脚本.py (实验1部分) | 业务问题、产品名、参数 |
| B1 | demo10_标书智能审查.py | SAMPLE_BID_DOCUMENT数据、证书类型、技术参数 |
| B2 | demo11_文档一致性检查.py | PROJECT_DOCS数据、文档类型、参数字段 |
| B3 | demo12_合同智能审批.py | SAMPLE_CONTRACT文本、APPROVAL_RULES规则 |
| D1 | demo13_外观质检.py | EXPERIENCE_DB经验库、TEST_CASES测试案例 |
| E1 | demo_多Agent辩论.py | 辩论议题、Agent角色、事件选项 |

## 模板代码共同特征

每个模板脚本遵循统一架构：

```python
#!/usr/bin/env python3
"""
Demo — {名称}
场景：{一句话描述}
模型：BigModel GLM-5.1
用法：
  python3 {filename}.py              # 交互式运行
  python3 {filename}.py --auto       # 自动演示
"""

import os, sys, json, time, argparse
from zhipuai import ZhipuAI

ZHIPU_API_KEY = os.getenv("BIGMODEL_API_KEY", "{fallback_key}")
client = ZhipuAI(api_key=ZHIPU_API_KEY)
MODEL = "glm-4-plus"

# ── 企业数据（替换区） ──
# 这里放该企业的模拟数据

def stream_print(text, delay=0.015):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

def print_section(title):
    print(f"\n{'━'*60}\n  {title}\n{'━'*60}")

# ── 规则引擎 ──
def rule_check(...):
    """硬性规则检查（毫秒级，100%准确）"""
    ...

# ── AI 引擎 ──
def ai_review(...):
    """AI语义审查（秒级，模糊判断）"""
    prompt = f"..."
    response = client.chat.completions.create(
        model=MODEL,
        messages=[...],
        max_tokens=...,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()

    # 开场
    print("\n" + "█"*60)
    print("  🔍 {Demo名称}")
    print("█"*60)

    # Step 1: 规则引擎
    print_section("Step 1 — 规则引擎检查")
    ...

    # Step 2: AI审查
    print_section("Step 2 — AI语义审查")
    ...

    # Step 3: 总结 + 技术揭秘
    print_section("总结")
    print("技术揭秘：...")

if __name__ == "__main__":
    main()
```

## 替换指南

生成新企业Demo时，按以下顺序替换：

1. **文件头docstring**：替换Demo名称、场景描述、用法命令
2. **企业数据区**：替换产品名/型号/参数/部门名/标准号
3. **规则引擎函数**：替换检查规则（日期字段、数值阈值、必填项）
4. **AI Prompt**：替换行业角色设定、检查维度、输出要求
5. **开场/总结文案**：替换为该企业的术语和痛点描述
6. **技术揭秘段落**：替换为该行业的落地方案
