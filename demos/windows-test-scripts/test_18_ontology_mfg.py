"""Demo 18: Ontology制造 - Manufacturing ontology (entities -> relations -> root cause query)"""
from test_utils import *

def test():
    step(1, "定义制造本体实体")
    entities = {
        "设备": ["CNC机床A", "注塑机B", "装配线C"],
        "工艺": ["切削", "注塑", "装配", "检测"],
        "缺陷": ["尺寸偏差", "表面划痕", "装配松动"],
        "参数": ["主轴转速", "模具温度", "扭矩值"],
        "物料": ["铝合金坯料", "ABS塑料粒子", "螺栓M6"],
    }
    total = sum(len(v) for v in entities.values())
    for cat, items in entities.items():
        info(f"  {cat}: {', '.join(items)}")
    ok(f"定义 {len(entities)} 类实体，共 {total} 个节点")

    step(2, "LLM构建关系图谱")
    relation_prompt = f"""你是制造业知识图谱专家。根据以下实体构建关系:
{entities}
输出三元组格式: (实体1, 关系, 实体2)
关系类型: 使用、产生、影响、包含、检测
至少输出8组三元组。"""
    relations = call_llm(relation_prompt, system="你是工业本体建模专家。")
    result_box("关系三元组", relations)

    step(3, "LLM执行根因查询")
    query_prompt = f"""基于制造本体:
实体: {entities}
关系: {relations}

查询: 当检测到"尺寸偏差"缺陷时，可能的根本原因链是什么？
请追溯: 缺陷 -> 工艺 -> 设备 -> 参数，给出完整因果链。"""
    root_cause = call_llm(query_prompt, system="你是制造质量根因分析专家。")
    result_box("根因分析结果", root_cause)

    step(4, "验证本体完整性")
    assert len(entities) == 5, "实体类别不完整"
    assert total >= 15, "实体数量不足"
    ok("制造本体构建与查询验证通过 (实体->关系->根因)")

if __name__ == "__main__":
    run_test("18", "Ontology制造", test)
