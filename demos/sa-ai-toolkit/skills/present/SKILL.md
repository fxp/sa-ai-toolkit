---
name: present
description: |
  将生成的演示包转换为交付物：PPT、Word文档、演示环境启动。用户说"导出PPT"、"生成文档"、"启动演示"、"准备交付"、"打开Org-Uplift"时触发。
---

# /present — 演示交付与现场执行

将 `/gen` 生成的Markdown方案转换为可交付的PPT/文档，启动有Web组件的演示环境。

## 操作

### 1. 导出PPT
> "把招商银行的方案做成PPT"

读取 `outputs/{企业名}/` → 生成品牌配色PPT：
- 封面：企业名+AI落地方案
- 每个推荐Demo一页：名称、价值、操作步骤、预期效果
- 日程页：演示时间线
- 行动建议页：本周/本月/本季

调用 `/anthropic-skills:pptx` 生成.pptx文件。

### 2. 导出Word
> "生成培训手册Word文档"

将全部Demo内容合并为一份Word文档：
- 封面+目录
- 企业画像
- 每个Demo：场景+步骤+台词+要点
- 行动建议

调用 `/anthropic-skills:docx` 生成.docx文件。

### 3. 启动Web演示
> "启动演示" / "打开Org-Uplift"

自动启动有Web组件的Demo：

```bash
# Org-Uplift Game
cd demos/demo-metr-org-uplift && python3 -m http.server 8765 &
open http://localhost:8765/index.html

# MiroFish
open https://666ghj.github.io/mirofish-demo/

# Hypothesis
open https://web.hypothes.is/
```

### 4. 演示彩排
> "帮我彩排招商银行的演示"

按02-日程.md的顺序，逐Demo：
1. 显示开场台词（从03-台词.md）
2. 提示操作步骤（从demos/xxx.md）
3. 提示过渡话术到下一个Demo
4. 计时提醒

### 5. 会后跟进
> "生成招行的会后邮件"

基于04-行动.md生成跟进邮件：
- 感谢参加
- 核心发现回顾（3条）
- 行动建议（本周3件事）
- 下次沟通时间建议
