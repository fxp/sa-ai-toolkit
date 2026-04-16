#!/usr/bin/env python3
"""
Demo: 前端自动化测试 — Playwright
演示AI生成的E2E测试脚本自动操控浏览器。

使用方法:
  python3 demo-test.py

依赖:
  pip3 install playwright
  python3 -m playwright install chromium
"""

from playwright.sync_api import sync_playwright, expect
import time


def demo_search_engine_test():
    """演示1: 搜索引擎自动化测试"""
    print("🌐 启动浏览器...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)  # slow_mo让演示可见
        page = browser.new_page()

        # Test 1: 页面加载
        print("\n📋 Test 1: 页面加载测试")
        page.goto("https://www.bing.com")
        print("  ✅ Bing 主页加载成功")

        # Test 2: 搜索功能
        print("\n📋 Test 2: 搜索功能测试")
        search_box = page.locator("#sb_form_q")
        search_box.fill("OpenClaw AI agent framework")
        search_box.press("Enter")
        page.wait_for_load_state("networkidle")
        print("  ✅ 搜索执行成功")

        # Test 3: 结果验证
        print("\n📋 Test 3: 搜索结果验证")
        results = page.locator("#b_results .b_algo")
        count = results.count()
        print(f"  ✅ 找到 {count} 条搜索结果")

        # Test 4: 截图
        print("\n📋 Test 4: 截图保存")
        page.screenshot(path="search-result.png")
        print("  ✅ 截图已保存: search-result.png")

        # Test 5: 响应式测试
        print("\n📋 Test 5: 响应式布局测试 (手机尺寸)")
        page.set_viewport_size({"width": 375, "height": 812})
        time.sleep(1)
        page.screenshot(path="search-result-mobile.png")
        print("  ✅ 手机端截图已保存: search-result-mobile.png")

        time.sleep(2)
        browser.close()

    print("\n" + "=" * 50)
    print("🎉 所有测试通过!")


def demo_custom_site_test(url="https://example.com"):
    """演示2: 自定义网站测试"""
    print(f"🌐 测试网站: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()

        page.goto(url)
        title = page.title()
        print(f"  页面标题: {title}")

        # 检查所有链接
        links = page.locator("a[href]")
        link_count = links.count()
        print(f"  发现 {link_count} 个链接")

        # 检查图片
        images = page.locator("img")
        img_count = images.count()
        print(f"  发现 {img_count} 张图片")

        # 性能指标
        metrics = page.evaluate("""() => {
            const perf = performance.timing;
            return {
                loadTime: perf.loadEventEnd - perf.navigationStart,
                domReady: perf.domContentLoadedEventEnd - perf.navigationStart,
            }
        }""")
        print(f"  DOM Ready: {metrics.get('domReady', 'N/A')}ms")
        print(f"  完全加载: {metrics.get('loadTime', 'N/A')}ms")

        browser.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        demo_custom_site_test(sys.argv[1])
    else:
        demo_search_engine_test()
