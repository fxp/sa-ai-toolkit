# Methodology — 培训方法论与交付物

> 本目录从 [Enterprise AI Training](../../../../Enterprise%20AI%20Training/) 项目 merge 而来，
> 补充 enterprise-skills 在**培训方法论**和**现场交付物**两个维度的能力。

---

## 与原 enterprise-skills 的关系

| enterprise-skills 原能力 | methodology 补充能力 |
|--------------------------|----------------------|
| Demo 选型（generator.py）| **D-7→D+1 全流程**（生成→定制→交付→会后）|
| 14 个通用 Demo 模板 | **4 个工业垂直 Demo**（标书/一致性/合同/质检，含可运行代码）|
| 行业 JSON 预置（10个）| **12 节点价值链痛点扫描** + **5 层 AI 需求金字塔** |
| narrative.md 4 幕叙事 | **120/60/30 分钟三档日程模板** |
| RUNBOOK.md 操作手册 | **学员手册 / 讲师 Rundown / 部署清单**（独立模板）|
| —— | **D-1 前夜深度对话方法论**（关键差异化）|
| —— | **培训现场 QA Agent**（在 `../qa-agent/`）|
| —— | **Browser-Use 自动化 Query 集** |

---

## 文件清单

### 1. 培训方法论

| 文件 | 内容 | 何时用 |
|------|------|--------|
| `pre-night-interview.md` | 前夜深度对话 90 分钟模板 + 痛点金矿提取技巧 | D-1 给央国企做培训前一晚 |
| `full-workflow-demo.md` | D-7 → D+1 全流程模拟（中航锂电案例）| 第一次带新人执行培训项目时 |
| `training-architecture.md` | 5 层企业 AI 需求金字塔 + 三档日程（120/60/30 分钟）+ 关键话术模板 | 设计培训内容时 |
| `pain-point-framework.md` | 12 节点价值链痛点扫描框架 + 行业变体 | Demo 选型前的痛点诊断 |
| `query-templates.md` | 12 类 Query 骨架（含 Browser-Use 自动化）+ System Prompt 模板 | 培训后给学员的 Query 速查 |

### 2. 工业垂直 Demo 代码（demo-templates-vertical/）

| 文件 | 对应 Demo | 行业 |
|------|----------|------|
| `demo10_标书智能审查.py` | Demo 15 | 制造/军工/工程 |
| `demo11_文档一致性检查.py` | Demo 16 | 制药/制造/航空 |
| `demo12_合同智能审批.py` | Demo 17 | 通用 |
| `demo13_外观质检.py` | Demo 18 | 电子/汽车/重工 |
| `multi_agent_debate.py` | 配合 Demo 07（多Agent辩论）| 通用 |

所有脚本支持：
- `--auto` 无交互运行
- `--case N` 选择案例
- 双引擎架构（规则确定性 + LLM 语义理解）
- `stream_print()` 打字机效果

### 3. 交付物模板（deliverable-templates/）

> 计划中：学员手册 / 讲师 Rundown / 部署清单的空白模板。
> 当前版本可参考 [Enterprise AI Training 的 skills/gen/SKILL.md](../skills/gen/SKILL.md) 中的格式规范。

---

## 与 generator.py 集成路径（建议）

如果要把这些方法论沉淀为可调用的步骤，可以在 `generator.py` 增加：

```bash
# 现有
python3.11 generator.py --profile X --step package

# 建议新增
python3.11 generator.py --profile X --step methodology  # 输出 RUNBOOK + 三档日程 + 学员手册
python3.11 generator.py --profile X --step pre-night    # 生成前夜对话提纲
python3.11 generator.py --profile X --step qa-faq       # 生成会后 FAQ 文档（需配合 ../qa-agent/）
```

---

## Claude Code Skill 形式入口

如果使用 Claude Code，[../skills/](../skills/) 目录提供了三个 slash command：

- `/gen <企业名>` — 一键生成全套培训方案
- `/customize` — 9 种微调操作（术语替换/Demo增删/受众切换…）
- `/present` — 8 种交付操作（PPT/Word/学员手册/彩排/会后跟进）

这是 generator.py CLI 的 LLM-native 替代品，适合不写代码的培训师直接对话使用。

---

## Merge 来源

- 源项目：`Projects/Enterprise AI Training/`
- Merge 日期：2026-04-28
- Merge 决策：单向（Enterprise → OpenClaw），保留两边项目独立
