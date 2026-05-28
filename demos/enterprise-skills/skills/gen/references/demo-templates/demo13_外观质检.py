#!/usr/bin/env python3
"""
Demo ⑬ — 外观质检 AI 助手（九洲质检场景）
=========================================
场景来源：九洲技术负责人原话 —
  "我们产品外观检测现在是人眼去判断"
  "油漆上面的瑕疵，转运过程中的碰伤"
  "两个检验员的标准可能不一样"
  "外观的要求非常高"
  "放大摄像机拍出来然后靠人看"

功能：
  1. 模拟：上传产品照片 → AI 识别缺陷
  2. 用 GLM-4V 多模态模型分析缺陷类型和严重程度
  3. 对照经验库判定是否合格
  4. 生成质检报告

  注：本 Demo 用文本模拟图片描述（无需真实图片），
      展示 AI 质检的完整工作流程和判断逻辑。
      实际部署时接入 GLM-4V 或 SAM 3 处理真实图片。

用法：
  python3 demo13_外观质检.py
  python3 demo13_外观质检.py --auto
  python3 demo13_外观质检.py --case 1    # 指定案例
"""

import os
import sys
import json
import time
import argparse

try:
    from zhipuai import ZhipuAI
except ImportError:
    print("❌ 请安装依赖：pip install zhipuai")
    sys.exit(1)

ZHIPU_API_KEY = os.getenv("BIGMODEL_API_KEY", "1790d449b46d437bbc8b101815048d64.lEMGH4tememSXbvH")
if not ZHIPU_API_KEY:
    print("❌ 请设置 BIGMODEL_API_KEY 环境变量")
    sys.exit(1)

client = ZhipuAI(api_key=ZHIPU_API_KEY)
MODEL = "glm-4-plus"

# ── 经验库（实际场景从数据库/知识库加载） ──
EXPERIENCE_DB = {
    "油漆瑕疵": {
        "描述": "喷漆表面出现气泡、流挂、橘皮、色差等缺陷",
        "判定标准": {
            "合格": "肉眼距离50cm不可见的微小瑕疵",
            "轻微不合格": "单点瑕疵面积<2mm²，数量≤3处/面",
            "严重不合格": "单点瑕疵面积≥2mm²，或数量>3处/面，或色差ΔE>3",
        },
        "常见原因": ["喷涂环境湿度过高", "底材处理不彻底", "漆料配比错误", "固化温度不足"],
    },
    "碰伤": {
        "描述": "运输或装配过程中造成的机械损伤",
        "判定标准": {
            "合格": "无可见碰伤",
            "轻微不合格": "碰伤深度<0.1mm，不影响功能和安全",
            "严重不合格": "碰伤深度≥0.1mm，或影响电气间隙/爬电距离",
        },
        "常见原因": ["运输防护不足", "装配工具不当", "搬运操作不规范"],
    },
    "焊接缺陷": {
        "描述": "焊接部位出现气孔、裂纹、未熔合等问题",
        "判定标准": {
            "合格": "焊缝均匀、无可见缺陷、表面光滑",
            "轻微不合格": "单个气孔直径<1mm，焊缝轻微不均匀",
            "严重不合格": "裂纹、未熔合、气孔直径≥1mm",
        },
        "常见原因": ["焊接参数不当", "焊材受潮", "焊接速度过快"],
    },
    "装配缺陷": {
        "描述": "零部件装配位置偏差、间隙不均、紧固件松动",
        "判定标准": {
            "合格": "装配间隙均匀，偏差在公差范围内",
            "轻微不合格": "间隙偏差0.5-1mm，不影响功能",
            "严重不合格": "间隙偏差>1mm，或紧固件未到位",
        },
        "常见原因": ["零件尺寸偏差", "装配顺序错误", "工装夹具磨损"],
    },
}

# ── 模拟质检案例（实际场景从摄像头拍照获取） ──
TEST_CASES = [
    {
        "id": "QC-2026-0415-001",
        "产品": "S13-M-1600/10 油浸式变压器",
        "工序": "总装后外观终检",
        "检验员": "张工",
        "图片描述": (
            "变压器外壳正面照片：整体喷漆为九洲标准灰色（RAL7035）。"
            "在箱体左侧面中部偏下位置，距底部约40cm处，发现一处明显的漆面流挂，"
            "流挂长度约15mm，宽度约3mm，呈水滴状向下延伸。"
            "同一面的右上角有2处微小气泡，每处直径约0.5mm。"
            "铭牌区域字迹清晰，无划伤。"
            "散热器翅片无变形，排列整齐。"
            "顶部储油柜油漆完好，无碰伤。"
        ),
    },
    {
        "id": "QC-2026-0415-002",
        "产品": "ZNBOX-12/630 美式箱变",
        "工序": "喷漆后转运前检查",
        "检验员": "李工",
        "图片描述": (
            "箱变外壳门板照片：门板喷漆为标准绿色（RAL6005）。"
            "门板右下角有一处碰伤，面积约8mm×5mm，漆层脱落露出底材。"
            "碰伤痕迹呈新鲜金属色，判断为近期搬运造成。"
            "门把手区域有轻微擦痕，长约20mm，未露底材。"
            "铰链安装孔位正确，门板开合顺畅。"
            "门板与框架间隙左侧2mm、右侧4mm，明显不均匀。"
        ),
    },
    {
        "id": "QC-2026-0415-003",
        "产品": "GGD2-0.4 低压开关柜",
        "工序": "出厂前终检",
        "检验员": "张工",
        "图片描述": (
            "开关柜前面板照片：面板喷漆为标准灰白色（RAL7035），"
            "整体色泽均匀，无明显色差。"
            "所有指示灯安装到位，标签打印清晰。"
            "铜排连接处螺栓均已拧紧并有标记漆。"
            "柜体与底座连接处焊缝均匀光滑。"
            "门板密封胶条完好，关闭后无明显间隙。"
            "整体外观良好，未发现明显缺陷。"
        ),
    },
]


def stream_print(text: str, delay: float = 0.015):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def print_section(title: str):
    print(f"\n{'━' * 60}")
    print(f"  {title}")
    print(f"{'━' * 60}")


def ai_inspect(case: dict, experience_db: dict) -> str:
    """用 GLM-5.1 模拟视觉质检 AI"""

    exp_text = ""
    for defect_type, info in experience_db.items():
        exp_text += f"\n【{defect_type}】\n"
        for level, desc in info["判定标准"].items():
            exp_text += f"  {level}：{desc}\n"

    prompt = f"""你是一位经验丰富的产品外观质检 AI 系统。

请根据以下检验信息和经验库标准，对产品外观进行判定。

【检验信息】
- 产品：{case['产品']}
- 工序：{case['工序']}
- 图像描述：{case['图片描述']}

【经验库判定标准】
{exp_text}

请输出：
1. 🔍 缺陷识别清单（每个缺陷：类型、位置、尺寸、严重程度）
2. ✅/❌ 总体判定（合格/附条件放行/返工/报废）
3. 📊 与经验库标准的逐项比对
4. 💡 根因分析建议（可能的原因和改进方向）
5. 📋 检验记录（结构化格式，可直接录入系统）

注意：
- 判定必须严格依据经验库标准
- 如果有两个以上轻微不合格，需要评估是否降级为严重
- 给出具体的数值和位置，不要模糊描述
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是工业产品外观质检AI，判定严格依据经验库标准，输出专业简洁。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1200,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(description="外观质检 AI Demo")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--case", type=int, choices=[1, 2, 3], help="指定案例编号")
    args = parser.parse_args()

    print("\n" + "█" * 60)
    print("  🔍 外观质检 AI 助手 Demo")
    print("  场景：产品外观缺陷识别 + 经验库比对 + 自动判定")
    print("  模型：BigModel GLM-5.1（文本模拟图像输入）")
    print("  实际部署：接入 GLM-4V 多模态 + SAM 3 分割")
    print("█" * 60)

    # 选择案例
    if args.case:
        cases = [TEST_CASES[args.case - 1]]
    else:
        cases = TEST_CASES

    print(f"\n📋 经验库已加载：{len(EXPERIENCE_DB)} 类缺陷标准")
    for dt in EXPERIENCE_DB:
        print(f"   📌 {dt}")

    if not args.auto:
        try:
            input("\n按 Enter 开始质检...")
        except EOFError:
            pass

    for idx, case in enumerate(cases):
        print_section(f"质检案例 {idx+1}/{len(cases)} — {case['id']}")
        print(f"  📦 产品：{case['产品']}")
        print(f"  🔧 工序：{case['工序']}")
        print(f"  👤 检验员：{case['检验员']}")
        print(f"\n  📷 图像描述（实际场景由摄像机拍摄）：")
        print(f"  {case['图片描述'][:80]}...")
        print()

        print("  🤖 AI 分析中...\n")
        result = ai_inspect(case, EXPERIENCE_DB)
        stream_print(result, delay=0.01)

        if idx < len(cases) - 1:
            print(f"\n{'─' * 60}")
            if not args.auto:
                try:
                    input("按 Enter 继续下一个案例...")
                except EOFError:
                    pass

    # ── 总结 ──
    print_section("系统总结")

    print("""
┌──────────────────────────────────────────────────────┐
│           🔍 外观质检 AI 系统架构                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────┐   ┌──────────┐   ┌──────────┐          │
│  │ 工业相机 │ → │ SAM 3    │ → │ 缺陷分割  │         │
│  │ 标准光源 │   │ 零样本   │   │ 定位标注  │         │
│  └────────┘   └──────────┘   └────┬─────┘          │
│                                    │                 │
│                              ┌─────▼──────┐         │
│                              │ GLM-4V/5.1  │         │
│                              │ 缺陷分类+   │         │
│                              │ 严重度评估   │         │
│                              └─────┬──────┘         │
│                                    │                 │
│                    ┌───────────────▼──────────────┐ │
│                    │         经验库比对             │ │
│                    │ 缺陷类型 × 判定标准 → 合格/返工 │ │
│                    └───────────────┬──────────────┘ │
│                                    │                 │
│                    ┌───────────────▼──────────────┐ │
│                    │    自动生成质检报告 + 工单     │ │
│                    └─────────────────────────────┘ │
├──────────────────────────────────────────────────────┤
│  💡 解决九洲的三个痛点：                               │
│  ① 两个检验员标准不一致 → AI 统一判定标准              │
│  ② 人眼看一圈得一个小时 → AI 秒级检测                 │
│  ③ 经验库靠人维护 → AI 自动积累+更新                  │
├──────────────────────────────────────────────────────┤
│  🛣️ 落地路径：                                        │
│  Phase 1: 本 Demo（文本模拟） → 验证逻辑               │
│  Phase 2: 接入真实产品照片 → GLM-4V 多模态              │
│  Phase 3: 部署 SAM 3 → 实时视频流质检                  │
│  Phase 4: 对接 MES → 自动拦截不合格品                   │
└──────────────────────────────────────────────────────┘
""")

    print("─" * 60)
    print("🔍 技术揭秘")
    print("─" * 40)
    print("• 本 Demo 用文本描述模拟图像输入（无需真实图片）")
    print("• 实际部署方案：")
    print("  → 工业相机（标准光源、色温控制）→ 九洲已有！")
    print("  → SAM 3 零样本分割（不需要标注数据）")
    print("  → GLM-4V 多模态理解缺陷语义")
    print("  → 经验库：从人工维护 → AI 自动更新")
    print("• 关键优势：")
    print("  → 判定标准统一（不再依赖检验员个人经验）")
    print("  → 7×24 不疲劳（人眼看久了会漏检）")
    print("  → 可追溯（每张照片+每次判定都有记录）")
    print("─" * 60)
    print("\n✅ 演示完成！")


if __name__ == "__main__":
    main()
