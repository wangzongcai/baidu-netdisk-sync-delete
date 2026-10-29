# -*- coding: utf-8 -*-
"""尝试进入「重复文件/垃圾文件清理」：先点左侧『重复文件』，失败则尝试直达 URL。不做删除。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx = b.contexts[0]
    page = None
    for pg in ctx.pages:
        if "pan.baidu.com" in pg.url:
            page = pg; break
    if not page:
        print("no pan page"); b.close(); raise SystemExit
    print("当前:", page.url)

    # 尝试1: 点击左侧「重复文件」
    clicked = None
    for sel in ["text=重复文件", "div:has-text('重复文件') >> nth=0"]:
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible():
                el.click(timeout=3000)
                clicked = sel; break
        except Exception: pass
    if clicked:
        print("点击了:", clicked)
        page.wait_for_timeout(2000)
    print("点击后 url:", page.url)
    try:
        t = page.title()
    except Exception: t=""
    print("标题:", t)
    b.close()