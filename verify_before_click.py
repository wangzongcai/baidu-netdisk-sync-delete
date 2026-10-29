# -*- coding: utf-8 -*-
"""点击前的只读核对：两端确认框是否在、确定按钮坐标、客户端窗口尺寸。绝不点击。"""
import ctypes
from ctypes import wintypes
from PIL import ImageGrab
from playwright.sync_api import sync_playwright

CLIENT_HWND=918428
user32=ctypes.windll.user32; user32.SetProcessDPIAware()

# --- 客户端 ---
r=wintypes.RECT(); user32.GetWindowRect(CLIENT_HWND,ctypes.byref(r))
L,T,W,Hh=r.left,r.top,r.right-r.left,r.bottom-r.top
print(f"客户端窗口 rect=({L},{T}) 尺寸={W}x{Hh}")
ImageGrab.grab(bbox=(L,T,L+W,T+Hh)).save(r"C:\Users\Administrator\baidu-dupe-clicker\_pre_click_client.png")
print("客户端当前截图 _pre_click_client.png")

# --- 网页端 ---
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx=b.contexts[0]
    page=None
    for pg in ctx.pages:
        if "/disk/clear" in pg.url: page=pg; break
    if not page:
        print("网页端: 未找到清理页"); raise SystemExit
    web=page.evaluate("""() => {
      const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
      const dvis=dlg? (dlg.getBoundingClientRect().width>0):false;
      let best=null;
      if(dlg) dlg.querySelectorAll('button,span,div,a').forEach(n=>{
        const r=n.getBoundingClientRect(); if(r.width<=0||r.height<=0) return;
        if((n.innerText||'').trim()==='确定'){ if(!best||r.width*r.height<best.area) best={x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),area:r.width*r.height}; }
      });
      return {dialogVisible:dvis, confirmBtn:best};
    }""")
    print("网页端: 确认框可见=",web["dialogVisible"]," 确定按钮=",web["confirmBtn"])
    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_pre_click_web.png")
    print("网页端当前截图 _pre_click_web.png")
    b.close()