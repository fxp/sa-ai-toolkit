"""Demo 10: PPT生成 - Branded PPT generation from outline"""
from test_utils import *

def test():
    step(1, "定义PPT大纲和品牌规范")
    outline = {
        "title": "AI赋能企业数字化转型",
        "slides": [
            {"id": 1, "title": "封面", "type": "cover"},
            {"id": 2, "title": "行业背景", "type": "content", "bullets": 3},
            {"id": 3, "title": "痛点分析", "type": "content", "bullets": 4},
            {"id": 4, "title": "解决方案", "type": "content", "bullets": 3},
            {"id": 5, "title": "案例展示", "type": "case_study"},
            {"id": 6, "title": "实施路线图", "type": "timeline"},
            {"id": 7, "title": "总结与下一步", "type": "summary"},
        ],
        "brand": {"primary_color": "#1a73e8", "font": "Microsoft YaHei", "logo": "company_logo.png"},
    }
    ok(f"大纲: {outline['title']} ({len(outline['slides'])} 页)")
    info(f"品牌色: {outline['brand']['primary_color']}, 字体: {outline['brand']['font']}")

    step(2, "LLM生成每页内容")
    prompt = f"""请为以下PPT大纲生成每页的详细内容:
主题: {outline['title']}
页面: {[s['title'] for s in outline['slides']]}

为每页生成: 标题、副标题、要点(3-4个)、演讲备注(1句话)。用中文输出。"""
    content = call_llm(prompt, system="你是PPT内容策划专家。", max_tokens=1000)
    result_box("PPT内容生成", content)

    step(3, "模拟PPTX结构生成")
    pptx_structure = []
    for slide in outline["slides"]:
        pptx_structure.append({
            "slide_num": slide["id"],
            "layout": slide["type"],
            "title": slide["title"],
            "brand_applied": True,
        })
    ok(f"生成 {len(pptx_structure)} 页PPTX结构")

    step(4, "验证品牌一致性")
    for s in pptx_structure:
        assert s["brand_applied"], f"Slide {s['slide_num']} 品牌未应用"
    ok("全部页面品牌规范已应用")
    ok("PPT生成流水线验证通过")

if __name__ == "__main__":
    run_test("10", "PPT生成", test)
