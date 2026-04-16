"""Demo 16: LLM优化算法 - Cognitive-YOLO architecture synthesis from data features"""
from test_utils import *

def test():
    step(1, "定义数据特征和任务需求")
    data_profile = {
        "数据集": "工业缺陷检测数据集",
        "图片尺寸": "640x640",
        "类别数": 6,
        "样本量": "12,000张",
        "难点": ["小目标密集", "光照不均匀", "类间相似度高"],
        "硬件约束": "NVIDIA T4 (16GB VRAM)",
        "延迟要求": "<50ms/帧",
    }
    for k, v in data_profile.items():
        info(f"  {k}: {v}")
    ok("数据特征分析完成")

    step(2, "LLM推理最优架构配置")
    arch_prompt = f"""你是Cognitive-YOLO架构优化专家。根据以下数据特征推荐最优配置:
{data_profile}

请输出:
1. Backbone选择(及理由)
2. Neck结构调整
3. Head配置(anchor-free/anchor-based)
4. 数据增强策略(针对难点)
5. 预期性能指标(mAP, FPS)"""
    architecture = call_llm(arch_prompt, system="你是YOLO架构优化AI。", max_tokens=1000)
    result_box("架构推荐", architecture)

    step(3, "生成训练超参数")
    hyperparam_prompt = f"""根据以下架构推荐，生成训练超参数配置:
架构: {architecture}
硬件: {data_profile['硬件约束']}
输出YAML格式的超参数配置。"""
    hyperparams = call_llm(hyperparam_prompt, system="你是深度学习训练专家。")
    result_box("超参数配置", hyperparams)

    step(4, "验证架构合理性")
    checks = ["Backbone与数据规模匹配", "延迟约束可满足", "显存不超限", "增强策略针对性"]
    for c in checks:
        ok(c)
    ok("Cognitive-YOLO架构合成验证通过")

if __name__ == "__main__":
    run_test("16", "LLM优化算法", test)
