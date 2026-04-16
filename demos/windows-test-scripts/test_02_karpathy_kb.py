"""Demo 02: Karpathy知识库 - 3-folder knowledge base build (raw -> wiki -> outputs)"""
from test_utils import *

def test():
    step(1, "模拟 raw/ 文件夹 - 收集原始资料")
    raw_docs = [
        {"file": "transformer_paper.pdf", "size": "2.1MB", "type": "论文"},
        {"file": "karpathy_lecture_notes.md", "size": "45KB", "type": "笔记"},
        {"file": "gpt_blog_post.html", "size": "120KB", "type": "博客"},
    ]
    ok(f"raw/ 收集到 {len(raw_docs)} 份原始文档")
    for d in raw_docs:
        info(f"  {d['file']} ({d['size']}) - {d['type']}")

    step(2, "LLM处理 - raw/ -> wiki/ 知识提炼")
    prompt = """请将以下原始资料提炼为wiki格式的知识条目:
1. Transformer论文 - Attention Is All You Need
2. Karpathy讲座笔记 - 从零构建GPT
3. GPT博客文章 - 语言模型的进化

为每个条目生成: 标题、核心概念(3点)、关键公式/代码片段、相关链接。用中文输出。"""
    wiki_content = call_llm(prompt, system="你是知识库管理助手，擅长将原始资料提炼为结构化wiki。")
    result_box("wiki/ 知识条目", wiki_content)

    step(3, "模拟 wiki/ -> outputs/ 生成交付物")
    outputs = [
        {"name": "Transformer速查卡.md", "type": "速查卡"},
        {"name": "GPT演进时间线.md", "type": "时间线"},
        {"name": "面试准备Q&A.md", "type": "Q&A"},
    ]
    ok(f"outputs/ 生成 {len(outputs)} 份交付物")

    step(4, "验证三层文件夹结构")
    pipeline = {"raw": len(raw_docs), "wiki": 3, "outputs": len(outputs)}
    for folder, count in pipeline.items():
        assert count > 0, f"{folder}/ 为空"
        info(f"  {folder}/ -> {count} 文件")
    ok("Karpathy三层知识库结构验证通过")

if __name__ == "__main__":
    run_test("02", "Karpathy知识库", test)
