# 🧠 NewCo一天 — CrewAI 多Agent编排引擎

## 为什么用CrewAI？

| 对比项 | Dify/n8n | Paperclip | **CrewAI** |
|--------|----------|-----------|------------|
| Agent类型 | Workflow节点 | 多Agent公司 | **异构Agent编排** |
| MCP支持 | ❌/有限 | ❌ | ✅ 原生 |
| 可视化 | ✅ | ✅ | ✅ (Studio) |
| 代码自由度 | 低 | 中 | **高** |
| 适合场景 | 固定Workflow | 模拟公司 | **混合编排** |
| 社区 | 中 | 小 | **46k Stars** |

**CrewAI的核心优势**：能编排**异构Agent**——不只是LLM对话，还能串联Python脚本、浏览器操作、CLI工具、MCP服务。正好匹配我们14个不同技术栈的Demo。

---

## 架构设计

```
                    ┌─────────────────────────────┐
                    │     CrewAI Orchestrator      │
                    │    (newco_crew.py)           │
                    └──────────┬──────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
    │   Act 1-3     │ │    Act 4      │ │   输出层      │
    │  嵌入式Agent  │ │  独立Agent    │ │               │
    │               │ │               │ │  Markdown     │
    │  A1 MCP架构师 │ │  D1 战略辩论  │ │  HTML看板     │
    │  A2 Loop设计  │ │  D2 OPC开发   │ │  PPT文件      │
    │  B1 迁移专家  │ │  D3 自动科研  │ │  知识库wiki/  │
    │  B2 知识工程  │ │  D4 PPT设计   │ │  测试报告     │
    │  C1 CEO看板   │ │               │ │               │
    │  C2 监督员    │ │  (可选备选)   │ │               │
    │  C3 PM阅读    │ │  Playwright   │ │               │
    │               │ │  Maestro      │ │               │
    │               │ │  MiroFish     │ │               │
    └───────────────┘ └───────────────┘ └───────────────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │     LLM 路由层              │
                    │  OpenRouter / BigModel GLM  │
                    │  (可切换任意模型)            │
                    └─────────────────────────────┘
```

## 10个Agent · 11个Task · 4幕叙事

```
Act 1 技术          Act 2 行业          Act 3 工作          Act 4 行动
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│ MCP架构师  │───▶│ 迁移专家   │───▶│ CEO顾问    │───▶│ 战略辩论   │
│ (工具编排) │    │ (COBOL)    │    │ (看板设计) │    │ (Paperclip)│
├────────────┤    ├────────────┤    ├────────────┤    ├────────────┤
│ MCP架构师  │    │ 知识工程师 │    │ AI监督员   │    │ OPC开发    │
│ (Ralph)    │    │ (Karpathy) │    │ (红袖标)   │    │ (GStack)   │
└────────────┘    └────────────┘    ├────────────┤    ├────────────┤
                                    │ PM阅读器   │    │ 自动科研   │
                                    │ (Hypothes) │    │(AutoRes)   │
                                    └────────────┘    ├────────────┤
                                                      │ PPT设计师  │
                                                      │ (压轴🎤)   │
                                                      └────────────┘
     2 Tasks           2 Tasks          3 Tasks           4 Tasks
```

## 快速开始

```bash
# 安装依赖
pip install crewai 'crewai[tools]'

# 设置API Key（二选一）
export OPENROUTER_API_KEY="sk-or-v1-xxx"
export BIGMODEL_API_KEY="xxx.xxx"

# 运行全部（约5-10分钟）
python newco_crew.py

# 只跑某一幕（演示时用）
python newco_crew.py --act 1   # 技术
python newco_crew.py --act 2   # 行业
python newco_crew.py --act 3   # 工作
python newco_crew.py --act 4   # 行动

# 演示模式（输出简化，每个Agent 100字以内）
python newco_crew.py --demo

# 无CrewAI时自动降级为模拟模式（直接调BigModel API）
```

## 演示场景

### 场景A：分享时作为"总控"
在分享Act 4时，直接运行：
```bash
python newco_crew.py --act 4 --demo
```
观众看到4个Agent依次输出战略辩论→MVP规划→科研方案→PPT大纲。

### 场景B：作为"NewCo一天"的完整叙事
在分享收尾时，展示完整流程跑一遍的结果：
```bash
python newco_crew.py
```
10个Agent接力完成一天的工作，证明PPT里说的"Agent-Native组织"不是概念。

### 场景C：证明"异构Agent编排"
展示CrewAI如何串联不同技术栈的Agent——有的调LLM，有的跑Python脚本，有的操作浏览器。
```python
# 未来扩展：加入MCP Tool
from crewai_tools import MCPServerAdapter
mcp_tools = MCPServerAdapter(server_url="http://localhost:18789")
agent = Agent(tools=[mcp_tools], ...)
```

## 与PPT的对应关系

| PPT论点 | CrewAI中的Agent | 输出物 |
|---------|----------------|--------|
| S11 MCP范式转变 | MCP架构师 | 工具编排方案 |
| S13 Ralph Loop | MCP架构师 | 自主迭代示例 |
| S21 COBOL事件 | 迁移专家 | 迁移成本对比 |
| S23 护城河 | 知识工程师 | 知识库构建方案 |
| S26 管理效率 | CEO顾问 | 实时看板设计 |
| S29 红袖标 | AI监督员 | 人力结构方案 |
| S30 自动化设计力 | PM阅读器 | 阅读工作流 |
| S31 决策层 | 战略辩论 | 3轮辩论记录 |
| S32 专家悖论 | 自动科研/OPC | 研究方案/MVP |
| S34 桶vs棍 | PPT设计师 | 汇报大纲 |
