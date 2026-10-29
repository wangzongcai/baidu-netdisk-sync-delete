# -*- coding: utf-8 -*-
"""只读：截取网页端清理页(含勾选行)。"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if page:
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_chk_web.png")
        print("已保存 _chk_web.png")
    b.close()
