# -*- coding: utf-8 -*-
"""用 playwright 精确定位 deleteDialog 里的『取消』按钮并点击。不删除。"""
import time
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx=b.contexts[0]
    page=None
    for pg in ctx.pages:
        if "/disk/clear" in pg.url: page=pg; break
    if not page: print("no clear page"); b.close(); raise SystemExit
    page.bring_to_front(); page.wait_for_timeout(300)

    # 在 .deleteDialog 内找文字恰为"取消"的元素点击
    clicked=False
    try:
        dlg=page.locator(".deleteDialog").first
        if dlg.count()==0: dlg=page.locator(".pan-dialog-wrapper").first
        cancel=dlg.locator("text=取消").first
        if cancel.count():
            cancel.click(timeout=3000)
            clicked=True
            print("点了 .deleteDialog 内的取消")
    except Exception as e:
        print("locator取消失败:",e)
    page.wait_for_timeout(400)
    still=page.evaluate("""() => { const d=document.querySelector('.deleteDialog,.pan-dialog-wrapper'); return d? (d.getBoundingClientRect().width>0) : false; }""")
    print("确认框还在?", still)
    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_web_canceled2.png")
    b.close()