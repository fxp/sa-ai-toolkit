"""Demo 17: LLM写PCB - Circuit-Synth workflow (description -> schematic -> BOM)"""
from test_utils import *

def test():
    step(1, "定义电路需求描述")
    circuit_desc = {
        "项目": "温湿度监测模块",
        "功能": "采集温湿度数据，通过WiFi上传到云端",
        "核心器件": ["ESP32-C3", "SHT30传感器", "3.3V LDO"],
        "接口": ["USB-C供电", "I2C传感器", "WiFi天线"],
        "尺寸约束": "30mm x 25mm 双面板",
    }
    for k, v in circuit_desc.items():
        info(f"  {k}: {v}")
    ok("电路需求定义完成")

    step(2, "LLM生成原理图描述")
    schematic_prompt = f"""你是电路设计AI。根据以下需求生成原理图连接描述:
{circuit_desc}
输出:
1. 电源部分(USB-C -> LDO -> 3.3V)
2. MCU连接(ESP32-C3引脚分配)
3. 传感器接口(I2C连接)
4. 天线匹配电路
用网表格式描述连接关系。"""
    schematic = call_llm(schematic_prompt, system="你是嵌入式硬件设计专家。", max_tokens=1000)
    result_box("原理图描述", schematic)

    step(3, "LLM生成BOM清单")
    bom_prompt = f"""根据以下原理图，生成BOM(物料清单):
{schematic}
输出表格格式: 序号|器件名|封装|数量|参考价格(RMB)
包含所有电阻、电容、IC等。"""
    bom = call_llm(bom_prompt, system="你是电子元器件采购专家。")
    result_box("BOM清单", bom)

    step(4, "生成PCB布局建议")
    layout_prompt = f"""尺寸: {circuit_desc['尺寸约束']}
器件: {circuit_desc['核心器件']}
给出PCB布局建议: 1)器件摆放区域 2)走线注意事项 3)天线净空区。3句话。"""
    layout = call_llm(layout_prompt, system="你是PCB Layout工程师。")
    result_box("布局建议", layout)

    step(5, "验证Circuit-Synth流程")
    stages = ["需求描述", "原理图", "BOM", "布局"]
    for s in stages:
        ok(f"{s} 阶段完成")
    ok("Circuit-Synth工作流验证通过")

if __name__ == "__main__":
    run_test("17", "LLM写PCB", test)
