#!/usr/bin/env python3
"""自动获取 HTML 页面高度并截图"""
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.sync_api import sync_playwright

def screenshot_html(html_path, output_path, width=800):
    """自动获取页面高度并截图"""
    html_path = Path(html_path).resolve()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': width, 'height': 600})

        # 加载页面
        page.goto(f'file://{html_path}')

        # 获取实际内容高度
        height = page.evaluate('document.body.scrollHeight')

        # 设置视口为实际高度
        page.set_viewport_size({'width': width, 'height': height})

        # 截图
        page.screenshot(path=output_path)

        browser.close()

        print(f"✅ Screenshot saved: {width}x{height}px")
        print(f"📁 {output_path}")

        return height

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auto_screenshot.py <html_file> [output_file] [width]")
        sys.exit(1)

    html_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 800

    screenshot_html(html_file, output_file, width)
