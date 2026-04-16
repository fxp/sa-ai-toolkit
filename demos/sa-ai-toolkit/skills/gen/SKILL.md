---
name: gen
description: |
  输入企业名称，一键生成全套AI落地演示方案。搜索企业信息→识别行业→评分选Demo→逐Demo填充行业定制内容→输出完整演示包。用户说企业名称、"生成方案"、"准备演示"、"做Demo"时触发。
---

# /gen — 企业AI演示方案一键生成

输入一家企业名称，输出一套可直接用于现场培训的完整演示包。

## 输入

企业名称（如"招商银行"、"宁德时代"、"华为云"）。

## 输出

```
outputs/{企业名}/
├── 00-画像.md        企业基本信息、行业、产品线、痛点、竞品
├── 01-选型.md        20个Demo的评分排序（标注必选/推荐/不适用）
├── 02-日程.md        120分钟版+60分钟版演示日程
├── 03-台词.md        每个Demo的开场白（用企业真实术语）
├── 04-行动.md        本周/本月/本季落地路线图+KPI
└── demos/            每个Demo的定制化演示内容
    ├── ceo-board.md
    ├── roleplay.md
    ├── finrobot.md
    └── ... (16-20个)
```

## 工作流

### Step 1: 搜索企业信息
用Web搜索采集：行业、营收、员工数、技术栈、AI现状、竞品。
如果搜不到关键信息，直接问用户。

### Step 2: 评分选Demo
基于行业和痛点，对20个Demo评分排序。

Demo池（按类别）：

**战略**: ceo-board(多Agent董事会), mirofish(群体智能), finrobot(AI行研)
**知识**: karpathy-kb(知识库), hypothesis(阅读标注)
**培训**: roleplay(角色扮演场景训练)
**研发**: gstack(一人公司), cognitive-yolo(LLM优化算法), sam3(视觉+声纹质检), circuit-synth(PCB电路), autoresearch(自动科研), kaggle-pipeline(Kaggle竞赛)
**交付**: ppt-gen(品牌PPT), ontology-mfg(知识图谱)
**质量**: maestro(移动测试), playwright(浏览器测试)
**体验**: ai-tools(工具巡礼), org-uplift(组织推演), autonomous-agent(自主Agent), skill-governance(Skill治理)

行业→Demo跳过规则：
- 银行/金融 → 跳过 circuit-synth, sam3, cognitive-yolo
- 制造业 → 全部适用
- 科技/软件 → 跳过 circuit-synth（除非做硬件）
- 医疗 → 跳过 circuit-synth, maestro

### Step 3: 逐Demo生成定制内容
每个Demo文件包含：
1. **标题** — 用企业真实业务场景命名
2. **场景描述** — 用企业产品名/流程名/术语
3. **演示步骤** — 可直接操作的Step 1/2/3
4. **预期效果** — 观众会看到什么
5. **要点** — 培训师的说话提示

**关键规则**：
- 用真实术语：不说"你的产品"，说"招行App"
- 用真实数据：不说"某个指标"，说"2025年营收3375亿"
- 不适用的Demo标注"跳过"而非删除

### Step 4: 生成配套文件
- 日程表：120分钟版（开场→冲击→深度→体验→行动）+ 60分钟缩略版
- 开场台词：每个Demo一段，用企业场景引入
- 行动建议：本周/本月/本季，含具体KPI
