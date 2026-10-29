# -*- coding: utf-8 -*-
"""删除后截图两端，确认是否删除成功。"""
import ctypes
from ctypes import wintypes
from PIL import ImageGrab
from playwright.sync_api import sync_playwright

CLIENT_HWND=918458 if False else 918428
user32=ctypes.windll.user32; user32.SetProcessDPIAware()
r=wintypes.RECT(); user32.GetWindowRect(CLIENT_HWND,ctypes.byref(r))
ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom)).save(r"C:\Users\Administrator\baidu-dupe-clicker\_after_client.png")
print("客户端截图 _after_client.png")

with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0]
    page=None
    for pg in ctx.pages:
        if "/disk/clear" in pg.url: page=pg; break
    if page:
        page.wait_for_timeout(500)
        # 读取剩余文件数
        info=page.evaluate("""() => {
          const t=document.body.innerText||'';
          const m=t.match(/(\\d+)个重复文件/);
          const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
          const dvis=dlg?(dlg.getBoundingClientRect().width>0):false;
          return {count:m?m[1]:'?', dialogVisible:dvis, has确认:/确定/.test(t)};
        }""")
        print("网页端:", info)
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_after_web.png")
        print("网页端截图 _after_web.png")
    b.close()