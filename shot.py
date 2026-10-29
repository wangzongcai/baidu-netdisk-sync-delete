# -*- coding: utf-8 -*-
"""截图当前 pan 页面，用于人工确认工具列表外观。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx=b.contexts[0]
    page=None
    for pg in ctx.pages:
        if "pan.baidu.com" in pg.url: page=pg; break
    if not page:
        print("no pan page"); b.close(); raise SystemExit
    page.bring_to_front()
    page.wait_for_timeout(2500)
    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_shot.png")
    print("saved, url:", page.url)
    b.close()