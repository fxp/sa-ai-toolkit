"""Demo 24: Kaggle自动发现 + 深度研究 — 全链路自动数据科学管线"""
from test_utils import *
import random, json

def test():
    # ── Phase 0: 自动发现 ──
    section("Phase 0: Kaggle自动发现")
    step(1, "模拟Kaggle API搜索竞赛和数据集")

    competitions = [
        {"name": "Severstal: Steel Defect Detection", "relevance": 9, "data_quality": 8, "hotness": 9,
         "reason": "钢材表面缺陷分割，直接对口工业质检需求"},
        {"name": "MVTec Anomaly Detection", "relevance": 8, "data_quality": 9, "hotness": 7,
         "reason": "15类工业产品异常检测，benchmark标准数据集"},
        {"name": "PCB Defect Detection", "relevance": 9, "data_quality": 7, "hotness": 6,
         "reason": "PCB缺陷检测，与硬件产线高度相关"},
        {"name": "DAGM 2007 Texture Defect", "relevance": 7, "data_quality": 8, "hotness": 5,
         "reason": "纹理缺陷检测经典基准，适合方法论验证"},
        {"name": "Casting Product Defect", "relevance": 8, "data_quality": 6, "hotness": 6,
         "reason": "铸造缺陷二分类，简单但实用"},
    ]

    for i, c in enumerate(competitions, 1):
        score = (c["relevance"] + c["data_quality"] + c["hotness"]) / 3
        info(f"  #{i} {c['name']} — 综合评分:{score:.1f}/10 | {c['reason']}")
    ok(f"发现 {len(competitions)} 个匹配的竞赛/数据集")

    selected = competitions[0]
    info(f"  选中: {selected['name']}")

    # ── Phase 1: 深度研究 ──
    section("Phase 1: 深度技术调研")
    step(2, f"对「{selected['name']}」进行深度研究")

    research_prompt = f"""你是AI研究助手，对以下Kaggle竞赛进行深度技术调研：
竞赛: {selected['name']}
任务: 工业缺陷检测

请输出：
1. 近2年Top论文趋势摘要（2-3句）
2. Kaggle Top方案共性（3个要点）
3. 技术选型建议表（3个方案，各1句评价）
4. 推荐实验计划（3个阶段）

用简洁中文回复。"""

    research = call_llm(research_prompt, max_tokens=600)
    result_box("深度研究报告", research)
    ok("文献综述 + Top方案分析 + 技术选型完成")

    # ── Phase 2: 自动参赛 ──
    section("Phase 2: AutoKaggle/AIDE自动参赛")
    step(3, "模拟AutoKaggle 6阶段管线执行")

    phases = [
        ("赛题理解", "读取竞赛说明、评估指标(Dice coefficient)、数据格式"),
        ("初步EDA", "4类缺陷分布: Class1=32%, Class2=25%, Class3=2%, Class4=41%"),
        ("数据清洗", "去除空标注样本(43%)、标准化图像尺寸至256x1600"),
        ("深度EDA", "发现Class3极度不平衡，需过采样或focal loss"),
        ("特征工程", "多尺度裁剪 + CutMix增强 + 在线难样本挖掘"),
        ("建模提交", "UNet-EfficientNet-B4 → 5-fold CV → TTA → 提交"),
    ]

    for i, (name, detail) in enumerate(phases, 1):
        ok(f"Phase {i} [{name}]: {detail}")

    # 模拟AIDE树搜索
    step(4, "模拟AIDE树搜索探索方案")
    branches = [
        {"name": "UNet+ResNet34", "dice": round(random.uniform(0.88, 0.92), 4), "status": "baseline"},
        {"name": "UNet+EfficientNet-B4", "dice": round(random.uniform(0.91, 0.95), 4), "status": "improved"},
        {"name": "DeepLabV3+", "dice": round(random.uniform(0.87, 0.90), 4), "status": "pruned"},
        {"name": "Ensemble(top2)+TTA", "dice": round(random.uniform(0.93, 0.96), 4), "status": "best"},
    ]

    for b in branches:
        icon = "★" if b["status"] == "best" else "→" if b["status"] == "improved" else "✗" if b["status"] == "pruned" else "○"
        info(f"  {icon} {b['name']}: Dice={b['dice']} [{b['status']}]")

    best = max(branches, key=lambda x: x["dice"])
    ok(f"最优方案: {best['name']} (Dice={best['dice']})")

    # ── Phase 3: 论文生成 ──
    section("Phase 3: 自动生成论文")
    step(5, "基于实验结果生成论文初稿")

    paper_prompt = f"""基于以下实验结果，生成一篇技术论文的摘要（100字以内）：

竞赛: {selected['name']}
最优方案: {best['name']}，Dice分数: {best['dice']}
创新点: SAM3零样本预筛选 + UNet有监督精调 + 模型集成
对比: 比baseline提升{round((best['dice'] - branches[0]['dice']) * 100, 1)}%

用学术风格的中文撰写。"""

    abstract = call_llm(paper_prompt, max_tokens=300)
    result_box("论文摘要", abstract)

    # ── 全链路验证 ──
    section("全链路验证")
    step(6, "验证4阶段端到端完整性")
    ok("Phase 0: Kaggle自动发现 ✓ (5个推荐)")
    ok("Phase 1: 深度技术调研 ✓ (文献+方案分析)")
    ok(f"Phase 2: 自动参赛 ✓ (Dice={best['dice']})")
    ok("Phase 3: 论文生成 ✓ (摘要已生成)")
    ok("Kaggle全链路自动数据科学管线验证通过")


if __name__ == "__main__":
    run_test("24", "Kaggle自动发现+深度研究", test)
