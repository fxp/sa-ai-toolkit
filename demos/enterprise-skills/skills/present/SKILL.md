---
name: present
description: |
  将生成的演示包转换为交付物：PPT、Word文档、学员手册、演示环境启动、彩排模式、会后跟进。用户说"导出PPT"、"生成文档"、"启动演示"、"准备交付"、"彩排"、"会后邮件"时触发。
---

# /present — 演示交付与现场执行

将 `/gen` 生成的Markdown方案转换为可交付的PPT/文档，启动演示环境，支持彩排和会后跟进。

## 定位方案

读取 `outputs/{企业名}/` 目录。如果用户没说企业名，列出所有已生成的企业。

## 操作

### 1. 导出培训PPT
> "把九洲的方案做成PPT"

读取全部文件 → 生成品牌配色PPT：

**PPT结构**：
- P1: 封面（企业名 + "大模型驱动XX行业智能化升级"）
- P2: 今日议程（从03-日程.md）
- P3-P5: 行业趋势（四阶段演进 + 三大重构 + AI角色演进）
- P6-P15: 场景Demo页（每个P0/P1 Demo一页）
  - 左侧：痛点描述（用企业原话）
  - 右侧：AI方案 + 架构图
  - 底部：预期价值（量化）
- P16: 多Agent辩论预告页
- P17: Workshop操作指南页
- P18-P19: 落地路线图（Phase 1/2/3）
- P20: 投入估算 + ROI
- P21: 行动号召（本周三件事）
- P22: Q&A + 联系方式

调用 `anthropic-skills:pptx` 生成 .pptx 文件。

### 2. 导出企业洞察PPT（给领导看的精简版）
> "做一份给董事长看的洞察PPT"

从00-画像.md + 01-痛点.md 提炼：
- P1: 封面
- P2-P3: 企业AI现状评估（已有基础 + 差距）
- P4-P6: Top3痛点场景 + AI解决方案
- P7-P8: 投入产出分析
- P9: 落地路线图
- P10: 行动建议

### 3. 导出Word培训手册
> "生成培训手册Word文档"

合并为一份可打印的Word文档：
- 封面 + 目录
- 企业画像（精简版）
- 每个Demo：场景描述 + 操作步骤 + 台词提示 + 技术要点
- 落地路线图
- Query示例集（从06-query.md精选20条最相关的）

调用 `anthropic-skills:docx` 生成 .docx 文件。

### 4. 导出学员手册
> "生成学员手册" / "打印给学员的资料"

从07-学员手册.md生成可打印的A4格式文档：
- 今日议程（单页）
- 动手实验操作步骤（每个实验一页）
- Query体验清单（精选10条，可现场试）
- 课后资源二维码
- 反馈问卷二维码

### 5. 预运行所有Demo
> "预运行" / "环境检查"

按09-部署清单.md逐项执行：
```bash
# 检查环境
python3 --version
node --version
python3 -c "from zhipuai import ZhipuAI; print('✅ zhipuai OK')"

# 逐个预运行Demo
for f in outputs/{企业名}/demos/*.py; do
    python3 "$f" --auto 2>&1 | tail -1
done
```

输出检查报告：每个Demo ✅/❌ 状态。

### 6. 启动Web演示
> "启动演示" / "打开Org-Uplift"

自动启动有Web组件的展示型Demo：

```bash
# Org-Uplift Game
cd demos/demo-metr-org-uplift && python3 -m http.server 8765 &
open http://localhost:8765/index.html

# MiroFish
open https://666ghj.github.io/mirofish-demo/

# Hypothesis
open https://web.hypothes.is/
```

### 7. 演示彩排
> "帮我彩排九洲的演示"

按03-日程.md顺序，逐Demo：
1. 显示时间段和Demo名称
2. 显示开场台词（从04-台词.md）
3. 显示操作步骤提示
4. 显示过渡话术到下一个Demo
5. 累计计时提醒
6. 标注⭐关键互动环节

### 8. 会后跟进
> "生成九洲的会后邮件" / "写跟进方案"

基于05-行动.md生成：

**跟进邮件**：
- 感谢参加培训
- 核心发现回顾（3条最重要的痛点→方案映射）
- 即时行动建议（本周3件事）
- 下次沟通时间建议
- 附件：学员手册PDF + Query集PDF

**详细跟进方案**（如客户要求）：
- 项目建议书（范围、目标、里程碑、报价）
- 技术方案（架构图、选型建议、部署方案）
- POC计划（2-4周验证方案）

## 快捷组合

| 命令 | 等价操作 |
|------|---------|
| `/present 全套` | PPT + Word + 学员手册 + 预运行 |
| `/present 管理层` | 洞察PPT + 跟进邮件 |
| `/present 交付` | 全套 + 会后方案 |
