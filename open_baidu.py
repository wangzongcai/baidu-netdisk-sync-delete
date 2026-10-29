# -*- coding: utf-8 -*-
"""在调试实例中打开百度网盘登录页/主页。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx = b.contexts[0]
    pages = ctx.pages
    page = pages[0] if pages else ctx.new_page()
    page.goto("https://pan.baidu.com/", timeout=40000)
    page.wait_for_timeout(2000)
    print("已导航到:", page.url)
    try:
        print("标题:", page.title())
    except Exception:
        pass
    b.close()