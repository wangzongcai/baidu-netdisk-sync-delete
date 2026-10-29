# -*- coding: utf-8 -*-
"""只读：截图网页端和客户端当前状态，看各自勾选情况。"""
import ctypes
from ctypes import wintypes
import time
from PIL import ImageGrab
from playwright.sync_api import sync_playwright

# 1) 网页端截图
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx=b.contexts[0]
    page=None
    for pg in ctx.pages:
        if "/disk/clear" in pg.url: page=pg; break
    if page:
        page.bring_to_front(); page.wait_for_timeout(400)
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_web_checked.png")
        print("网页端截图 _web_checked.png, url=",page.url)
    b.close()

# 2) 客户端截图 (hwnd 918428)
H=918428
user32=ctypes.windll.user32
user32.SetProcessDPIAware()
r=wintypes.RECT(); user32.GetWindowRect(H,ctypes.byref(r))
print("客户端rect:", r.left,r.top,r.right-r.left,r.bottom-r.top)
if r.right-r.left>100:
    ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom)).save(r"C:\Users\Administrator\baidu-dupe-clicker\_client_checked.png")
    print("客户端截图 _client_checked.png")
