# -*- coding: utf-8 -*-
"""探测版：连已登录 Edge，找百度网盘页面，列出可点击的删除/确定相关元素。不删除任何东西。"""
import sys
from playwright.sync_api import sync_playwright

HOST = "127.0.0.1"
PORT = 9222

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        print("已连接浏览器:", browser.version)
        ctx = browser.contexts[0] if browser.contexts else None
        print("contexts:", len(browser.contexts))
        pages = context_pages(ctx)
        for pg in pages:
            url = pg.url
            try:
                title = pg.title()
            except Exception:
                title = ""
            print(f"- page: {title[:40]!r} | {url[:80]}")
        # 找百度网盘(网盘/pan.baidu.com)页面
        target = None
        for pg in context_pages(ctx):
            if "pan.baidu.com" in pg.url:
                target = pg
                break
        if not target:
            print("未找到 pan.baidu.com 页面，请在该 Edge 中登录并打开百度网盘(清理重复文件页)。")
            return
        try:
            t = target.title()
        except Exception:
            t = ""
        print("定位到百度网盘页面，标题:", t)
        # 列出按钮
        btns = target.query_selector_all("button, [role=button], .btn, .button")
        print(f"找到 {len(btns)} 个按钮类元素:")
        for b in btns[:40]:
            txt = (b.inner_text() or "").strip().replace("\n", " ")
            if txt:
                print("   -", repr(txt[:30]))
        browser.close()

def context_pages(ctx):
    return ctx.pages if ctx else []

if __name__ == "__main__":
    main()