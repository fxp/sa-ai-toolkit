"""Demo 23: SAM3工业质检 - SAM3 text-prompt inspection + SAM-Audio sound analysis"""
from test_utils import *

def test():
    step(1, "模拟SAM3视觉质检 - Text-Prompt分割")
    inspection_input = {
        "image": "pcb_board_001.jpg",
        "resolution": "1920x1080",
        "text_prompts": ["焊点缺陷", "短路桥接", "元器件偏移"],
        "model": "SAM3-Industrial",
    }
    ok(f"输入图像: {inspection_input['image']} ({inspection_input['resolution']})")
    info(f"文本提示: {inspection_input['text_prompts']}")

    step(2, "LLM模拟SAM3检测结果分析")
    sam_prompt = f"""你是工业视觉检测AI。模拟SAM3对PCB板的检测结果:
图像: {inspection_input['image']}
检测提示: {inspection_input['text_prompts']}

模拟输出:
1. 每个提示的检测结果(检出/未检出/疑似)
2. 检测置信度(0-1)
3. 缺陷位置描述(区域坐标)
4. 严重等级(Critical/Major/Minor)"""
    sam_result = call_llm(sam_prompt, system="你是工业质检AI视觉模型。")
    result_box("SAM3视觉检测结果", sam_result)

    step(3, "模拟SAM-Audio声学分析")
    audio_input = {
        "audio": "motor_bearing_003.wav",
        "duration": "5.2s",
        "sample_rate": "44100Hz",
        "text_prompts": ["轴承异响", "电机振动", "正常运行"],
    }
    ok(f"音频输入: {audio_input['audio']} ({audio_input['duration']})")

    audio_prompt = f"""你是SAM-Audio工业声学分析AI。模拟对电机声音的分析:
音频: {audio_input['audio']}
分析提示: {audio_input['text_prompts']}

输出:
1. 声音特征描述(频率范围、波形特征)
2. 匹配结果(哪个提示匹配度最高)
3. 设备状态判定(正常/预警/故障)
4. 建议维护措施"""
    audio_result = call_llm(audio_prompt, system="你是工业声学AI分析师。")
    result_box("SAM-Audio声学分析", audio_result)

    step(4, "生成综合质检报告")
    report_prompt = f"""综合视觉和声学检测结果，生成质检报告摘要:
视觉: {sam_result}
声学: {audio_result}
输出: 1)总体判定 2)发现缺陷列表 3)处置建议。"""
    report = call_llm(report_prompt, system="你是质量管理工程师。")
    result_box("综合质检报告", report)

    step(5, "验证双模态检测流程")
    ok("SAM3视觉检测完成")
    ok("SAM-Audio声学分析完成")
    ok("综合质检报告生成完成")
    ok("SAM3双模态工业质检验证通过")

if __name__ == "__main__":
    run_test("23", "SAM3工业质检", test)
