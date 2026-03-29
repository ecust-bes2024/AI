#!/usr/bin/env python3
"""从 Chrome 提取飞书 Cookie"""
import json
from pathlib import Path
from pycookiecheat import chrome_cookies

def extract_feishu_cookie():
    """从 Chrome 提取飞书 Cookie"""
    try:
        # 获取飞书的所有 Cookie
        cookies = chrome_cookies('https://www.feishu.cn')

        # 转换为 Cookie 字符串格式
        cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])

        print(f"✅ 成功提取 {len(cookies)} 个 Cookie 字段")
        print(f"\nCookie 字符串长度: {len(cookie_str)} 字符")

        # 保存到配置文件
        config_dir = Path.home() / '.config' / 'lark-cli'
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / 'config.json'

        config = {'cookie': cookie_str}
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Cookie 已保存到: {config_file}")
        return cookie_str

    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return None

if __name__ == '__main__':
    extract_feishu_cookie()
