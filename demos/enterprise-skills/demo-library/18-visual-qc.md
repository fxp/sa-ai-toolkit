---
id: "18"
name: "外观质检"
pattern: "quality-gate-vision"
universal_value: "视觉缺陷分类 0.3 秒/张，比抽检漏检率低 10 倍"
scoring_signals: ["K", "A"]
impact_score: 7
offline: true
duration_min: 3
act: 2
mode: "embedded"
vertical: "manufacturing|electronics|automotive"
source_code: "../methodology/demo-templates-vertical/demo13_外观质检.py"
---

## 核心价值主张

人工抽检靠经验、易疲劳、夜班漏检率飙升。AI 视觉模型对划痕/凹陷/色差/装配错位等做毫秒级分类，且每个判定有可视化热力图，质量员从"看"升级到"复核+决策"。

## 通用演示指令（待替换）

```
对这批 {{产品}} 的图像做缺陷检测：
- 分类：{{缺陷类型清单}}
- 输出每张图：缺陷类型 / 置信度 / 位置 / 严重度
- 按 {{分类维度}} 统计趋势（产线/班次/物料批次）
- 给出 Top3 根因假设
```

## 变量说明

| 占位符 | 电子制造 | 汽车 | 重工 |
|--------|---------|------|------|
| {{产品}} | PCB/SMT 板 | 车身/内饰件 | 变压器套管 |
| {{缺陷类型}} | 短路/虚焊/翘起 | 漆面/凹陷/装配 | 裂纹/绝缘/形变 |
| {{分类维度}} | 产线×班次 | 物料批次×车型 | 工艺参数×季节 |

## 开场触发词

> "你们外观质检靠抽检，5% 抽样率——剩下 95% 出了问题，是客户帮你发现的。"

## 落地路径

| Phase | 时长 | 内容 |
|-------|------|------|
| 1 | 0-3月 | 离线 Demo + 单条产线试点 |
| 2 | 3-6月 | 在线检测 + MES 联动 |
| 3 | 6-18月 | 全产线 + 主动预警（参数偏移预测）|

## 配套代码

`methodology/demo-templates-vertical/demo13_外观质检.py`
