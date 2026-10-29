# -*- coding: utf-8 -*-
"""直接导航到垃圾文件清理页，然后不操作，交给用户手动选目录扫描。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx=b.contexts[0]
    # 用现有 pan 页面导航
    page=None
    for pg in ctx.pages:
        if "pan.baidu.com" in pg.url:
            page=pg; break
    if not page:
        page=ctx.new_page()
    page.goto("https://pan.baidu.com/disk/clear?orginal=web_tool", timeout=40000)
    page.wait_for_timeout(2500)
    page.bring_to_front()
    print("已导航到清理页:", page.url)
    try: print("标题:", page.title())
    except Exception: pass
    b.close()