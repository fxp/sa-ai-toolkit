#!/usr/bin/env python3
"""
Demo 4: Agent + Hypothes.is 自动标注
用AI分析文章内容，自动在Hypothes.is上创建标注。

使用方法:
  1. 设置环境变量: export HYPOTHESIS_API_TOKEN="your_token"
  2. 运行: python annotate-agent.py "https://example.com/article"

依赖:
  pip install requests anthropic
"""

import os
import sys
import json
import requests
from typing import Optional

# ── 配置 ──
HYPOTHESIS_API = "https://api.hypothes.is/api"
HYPOTHESIS_TOKEN = os.getenv("HYPOTHESIS_API_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def fetch_article(url: str) -> str:
    """抓取文章内容（简单实现）"""
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        # 简单提取文本（生产环境应用readability库）
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.texts = []
                self.skip = False
            def handle_starttag(self, tag, attrs):
                if tag in ('script', 'style', 'nav', 'footer', 'header'):
                    self.skip = True
            def handle_endtag(self, tag):
                if tag in ('script', 'style', 'nav', 'footer', 'header'):
                    self.skip = False
            def handle_data(self, data):
                if not self.skip and data.strip():
                    self.texts.append(data.strip())

        parser = TextExtractor()
        parser.feed(resp.text)
        return "\n".join(parser.texts)[:8000]  # 截断到8000字符
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""


def analyze_with_ai(text: str) -> list[dict]:
    """用AI分析文章，提取值得标注的内容"""
    if not ANTHROPIC_API_KEY:
        # 如果没有API Key，返回模拟数据
        return [
            {"quote": text[:100], "tag": "关键数据", "comment": "这是一个重要的数据点", "color": "red"},
            {"quote": text[200:300] if len(text) > 300 else text[:100], "tag": "产品策略", "comment": "值得借鉴的策略", "color": "green"},
        ]

    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""分析以下文章，找出4-6个值得标注的内容。对每个标注，返回JSON数组：

每个元素包含:
- "quote": 原文中值得标注的一句话（必须是原文中的精确文字）
- "tag": 标签类型，从以下选择: "关键数据", "非共识观点", "产品策略", "AI批评"
- "comment": 你的批判性评论（1-2句话）

文章内容:
{text[:5000]}

返回纯JSON数组，不要其他内容。"""
        }]
    )

    try:
        return json.loads(message.content[0].text)
    except:
        return []


def create_annotation(url: str, quote: str, text: str, tags: list[str]) -> Optional[dict]:
    """在Hypothes.is上创建标注"""
    if not HYPOTHESIS_TOKEN:
        print(f"  [模拟] 标注: {quote[:40]}... | 标签: {tags}")
        return {"id": "mock", "text": text}

    headers = {
        "Authorization": f"Bearer {HYPOTHESIS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "uri": url,
        "text": text,
        "tags": tags,
        "target": [{
            "source": url,
            "selector": [{
                "type": "TextQuoteSelector",
                "exact": quote,
            }]
        }]
    }

    resp = requests.post(f"{HYPOTHESIS_API}/annotations", headers=headers, json=payload)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"  Error: {resp.status_code} - {resp.text}")
        return None


TAG_COLORS = {
    "关键数据": "🔴",
    "非共识观点": "🟡",
    "产品策略": "🟢",
    "AI批评": "💬",
}


def main():
    if len(sys.argv) < 2:
        print("用法: python annotate-agent.py <url>")
        print()
        print("环境变量:")
        print("  HYPOTHESIS_API_TOKEN  - Hypothes.is API Token")
        print("  ANTHROPIC_API_KEY     - Anthropic API Key (可选，无则用模拟数据)")
        print()
        print("示例:")
        print("  python annotate-agent.py https://example.com/article")
        return

    url = sys.argv[1]
    print(f"🔍 抓取文章: {url}")
    text = fetch_article(url)
    if not text:
        print("❌ 无法获取文章内容")
        return

    print(f"📄 文章长度: {len(text)} 字符")
    print(f"🤖 AI分析中...")
    insights = analyze_with_ai(text)
    print(f"💡 发现 {len(insights)} 个洞察")
    print()

    for i, insight in enumerate(insights, 1):
        tag = insight.get("tag", "其他")
        emoji = TAG_COLORS.get(tag, "📌")
        quote = insight.get("quote", "")[:60]
        comment = insight.get("comment", "")

        print(f"{emoji} [{i}] {tag}")
        print(f"  引用: \"{quote}...\"")
        print(f"  评论: {comment}")

        result = create_annotation(
            url=url,
            quote=insight.get("quote", ""),
            text=f"**{tag}**: {comment}",
            tags=[tag, "AI-generated", "OpenClaw-demo"],
        )
        if result:
            print(f"  ✅ 标注已创建")
        print()

    print("=" * 60)
    print(f"📊 完成! 共创建 {len(insights)} 个标注")
    if HYPOTHESIS_TOKEN:
        print(f"🔗 查看: https://hypothes.is/search?q=tag:OpenClaw-demo")
    else:
        print("⚠️  模拟模式（未设置 HYPOTHESIS_API_TOKEN）")
        print("    设置后重新运行以创建真实标注")


if __name__ == "__main__":
    main()
