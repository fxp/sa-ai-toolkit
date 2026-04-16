# Enterprise AI Architecture Skills
# 企业AI采用框架 — 通用技能包

这个项目是一套**可复用的AI分享工具包**。
输入任意企业的基本信息，自动生成：
- 定制化Demo选型方案（DEMO总表）
- 完整演示流程手册（RUNBOOK）
- 可执行的CrewAI编排脚本（newco_crew.py）

---

## 快速开始

```bash
# 方式1: 交互式引导建立画像，然后生成
python3.11 generator.py --interactive

# 方式2: 命令行直接指定关键参数
python3.11 generator.py \
  --company "招商银行" \
  --industry "banking-finance" \
  --size "large" \
  --pain-points "A,D,E,G,L" \
  --audience "全行中高层管理者" \
  --minutes 90

# 方式3: 已有画像文件，直接生成
python3.11 generator.py --profile outputs/cmb-bank/profile.json

# 仅预览Demo选型（不写文件）
python3.11 generator.py --profile outputs/cmb-bank/profile.json --preview

# 运行生成的Crew演示
python3.11 outputs/cmb-bank/newco_crew.py --demo
python3.11 outputs/cmb-bank/newco_crew.py --act 4 --demo
python3.11 outputs/cmb-bank/newco_crew.py --list
```

输出目录：`outputs/{company-slug}/`

---

## /enterprise-profile

**触发时机**：用户想为一家新企业生成AI分享方案时

通过5轮问答采集企业画像，最终生成 `profile.json`。

**执行步骤**：

### 第1步：基础定位

问：
> "请告诉我以下信息：
> 1. 企业名称 + 所在行业（例如：招商银行 / 商业银行）
> 2. 员工规模（例如：5万人）
> 3. 本次演示的受众群体（例如：分行行长 + 业务部门负责人）"

### 第2步：痛点识别

展示清单，让用户选3-5个：

```
效率类：
  A. 大量重复性文档处理（报告/合同/工单/工卡）
  B. 跨部门信息同步慢，协作效率低
  C. 会议多但决策慢，方案评审周期长
  D. 员工花大量时间查找内部知识/规程

决策类：
  E. 数据有但难以快速形成洞察，决策依赖经验
  F. 专家资源稀缺，评审排队等待
  G. 风险识别滞后，被动应对多于主动预防

创新类：
  H. 从想法到原型的周期太长
  I. 技术文档/专利/论文阅读消化慢
  J. 遗留系统多，新技术难以融合

质量合规类：
  K. 质量管控依赖人工抽检，漏检率高
  L. 合规/审批工作量大，容易出错
  M. 测试覆盖率低，Bug修复成本高
```

追问："除以上之外，还有什么特别痛的问题？"

### 第3步：关键约束

问：
1. "数据安全要求如何？（不能出内网/不能上云/有等保/军工保密等）"
2. "演示时有没有不能提及的竞对或敏感话题？"
3. "受众的技术背景如何？（全是业务人员 / 有一定技术背景 / 都是工程师）"

### 第4步：演示目标

问：
1. "这次演示最核心的目标是什么？（说服谁做什么决定？）"
2. "演示总时长约多少分钟？希望包含几个可运行的Demo？"

### 第5步：生成画像

调用：`python3.11 generator.py --interactive`，写入 `outputs/{slug}/profile.json`

---

## /enterprise-analyze

**触发时机**：画像收集完成后，输出机会地图和Demo评分

读取 `profile.json`，按行业匹配度 × 痛点相关度 × 演示冲击力三维打分，输出：

- **14个Demo的综合得分排名**
- **推荐的7嵌入+4独立分配方案**
- **必选Demo**（任何企业都不能砍的3个）
- **开场Hook建议**（让全场举手的破冰问题）

调用：`python3.11 generator.py --profile outputs/{slug}/profile.json --step analyze`

---

## /enterprise-design

**触发时机**：分析完成后，定制每个Demo的企业专属场景

对每个选中的Demo，改写：
- 角色名称（CEO→行长/总工/旅长...）
- 场景设定（用企业实际系统/数字/流程）
- 演示触发词（精准触碰企业已选痛点）
- 台词脚本（可直接朗读）
- 收尾金句（锚定PPT论点）

调用：`python3.11 generator.py --profile outputs/{slug}/profile.json --step design`

---

## /enterprise-package

**触发时机**：设计完成后，生成完整交付物

写入 `outputs/{slug}/`：
- `DEMO总表.md` — 按4幕排列的完整Demo方案
- `RUNBOOK.md` — 每个Demo的逐步操作手册
- `newco_crew.py` — 可直接运行的CrewAI编排脚本
- `narrative.md` — 4幕叙事大纲 + 过渡台词
- `score_report.md` — Demo评分明细

调用：`python3.11 generator.py --profile outputs/{slug}/profile.json --step package`

---

## /enterprise-run

**触发时机**：包生成后，现场运行演示

```bash
python3.11 outputs/{slug}/newco_crew.py --list      # 查看所有工具
python3.11 outputs/{slug}/newco_crew.py --demo       # 全幕演示
python3.11 outputs/{slug}/newco_crew.py --act 4      # 仅Act 4
python3.11 outputs/{slug}/newco_crew.py --run-tool kb # 单工具测试
```

---

## Demo库 (14个模板)

每个模板位于 `demo-library/` 目录，包含：
- `pattern`：AI能力模式（工具编排/知识萃取/质量看门/决策放大/内容生成）
- `universal_value`：与行业无关的核心价值主张
- `hooks`：需要填充的变量（`{{角色}}` `{{系统}}` `{{场景}}` `{{数字}}`）
- `scoring_signals`：哪些痛点代码匹配此Demo

| ID  | Demo名称 | AI模式 | 核心价值 |
|-----|---------|--------|---------|
| 01  | MCP工具编排 | 工具路由 | 一句话跨N个系统 |
| 02  | Karpathy知识库 | 知识萃取 | 企业知识永不流失 |
| 03  | 遗留代码迁移 | 代码智能 | 迁移成本降万倍 |
| 04  | 指挥/CEO看板 | 决策支持 | 实时感知全局 |
| 05  | AI监督员 | 质量看门 | AI+人协同新范式 |
| 06  | 智能阅读标注 | 文档智能 | 阅读效率×10 |
| 07  | 多Agent辩论 | 多智能体 | 决策前提前吵架 |
| 08  | 一人军团 | 个人放大 | 一人=一个团队 |
| 09  | AutoResearch | 自主研究 | 文献到论文全自动 |
| 10  | PPT生成 | 内容生成 | 4小时→3分钟 |
| 11  | 前端自动化测试 | 测试智能 | AI不光写还测 |
| 12  | 移动端自动化测试 | 测试智能 | YAML可读测试 |
| 13  | 群体智能推演 | 涌现智能 | 不确定对抗模拟 |
| 14  | Ralph自主迭代 | 自主执行 | 零人工介入完成任务 |

---

## 行业预置库 (10个行业)

`industry-patterns/` 目录为以下行业预制了所有Demo变量：

| 文件 | 行业 | 特色场景 |
|------|------|---------|
| banking-finance.json | 商业银行/金融 | 贷款审批/合规/风控 |
| manufacturing.json | 制造业 | 工艺管理/质检/维修 |
| aerospace-defense.json | 航空航天/军工 | 任务规划/技术文档/装备保障 |
| healthcare.json | 医疗/医药 | 临床数据/病历/合规 |
| retail-ecommerce.json | 零售/电商 | 导购/客服/供应链 |
| consulting-research.json | 咨询/研究机构 | 行研/报告/知识库 |
| logistics.json | 物流/供应链 | 调度/追踪/预测 |
| real-estate.json | 地产/建筑 | 项目管理/合同/报审 |
| energy.json | 能源/公用事业 | 运维/安全/调度 |
| tech-software.json | 科技/软件 | 开发提效/文档/测试 |
