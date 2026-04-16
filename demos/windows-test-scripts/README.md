# Windows 环境测试脚本

> 本目录包含所有 enterprise-ai skill 中 23 个 Demo 的 Windows 环境测试脚本。
> 每个脚本可在 Windows 10/11 + Python 3.11+ 环境下独立运行。

## 前置要求

```powershell
# 1. Python 3.11+
python --version

# 2. 安装通用依赖
pip install requests rich

# 3. 设置 BigModel API Key（用于 LLM 调用的 Demo）
set BIGMODEL_API_KEY=your_key_here
```

## 脚本列表

| 脚本 | Demo | 说明 | 需要GPU |
|------|------|------|---------|
| `test_01_tool_orchestration.py` | MCP工具编排 | 模拟多工具调用链 | 否 |
| `test_02_knowledge_base.py` | Karpathy知识库 | 三文件夹知识管理流程 | 否 |
| `test_03_legacy_migration.py` | 遗留代码迁移 | 代码转换模拟 | 否 |
| `test_04_executive_dashboard.py` | CEO看板 | 多数据源聚合模拟 | 否 |
| `test_05_ai_supervisor.py` | AI监督员 | 质量审查流程模拟 | 否 |
| `test_06_smart_reading.py` | 智能阅读标注 | 文档分析+标注 | 否 |
| `test_07_multi_agent_debate.py` | 多Agent辩论 | 多角色辩论模拟 | 否 |
| `test_08_one_person_army.py` | 一人军团 | 全栈任务自动化 | 否 |
| `test_09_auto_research.py` | AutoResearch | 自动科研管线 | 否 |
| `test_10_ppt_generation.py` | PPT生成 | 品牌PPT生成流程 | 否 |
| `test_11_frontend_testing.py` | 前端自动化测试 | Playwright测试生成 | 否 |
| `test_12_mobile_testing.py` | 移动端测试 | Maestro YAML生成 | 否 |
| `test_13_group_intelligence.py` | 群体智能推演 | 多Agent博弈模拟 | 否 |
| `test_14_ralph_loop.py` | Ralph自主迭代 | 自主反思改进循环 | 否 |
| `test_15_roleplay_training.py` | AI角色扮演培训 | 客服/管理场景训练 | 否 |
| `test_16_llm_algorithm.py` | LLM优化算法 | Cognitive-YOLO流程 | 否 |
| `test_17_circuit_synth.py` | LLM写PCB | Circuit-Synth流程 | 否 |
| `test_18_ontology_mfg.py` | Ontology制造 | 知识图谱+根因分析 | 否 |
| `test_19_investment.py` | 投资人视角 | AI工业股分析 | 否 |
| `test_20_autonomous_agent.py` | 自主Agent | 持续工作循环模拟 | 否 |
| `test_21_tools_showcase.py` | AI工具巡礼 | 7工具能力矩阵 | 否 |
| `test_22_org_uplift.py` | Org-Uplift推演 | METR游戏自动模拟 | 否 |
| `test_23_sam3_industrial.py` | SAM3工业质检 | 视觉+声纹质检流程 | 可选 |

## 运行方式

```powershell
# 运行单个测试
python test_01_tool_orchestration.py

# 运行所有测试
python run_all_tests.py

# 运行所有测试（跳过需要GPU的）
python run_all_tests.py --skip-gpu
```
