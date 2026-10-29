# -*- coding: utf-8 -*-
"""按ESC取消网页端确认框，恢复到干净可勾选状态。不删除。"""
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
    # 若有确认框, 点其"取消"按钮(精确)或ESC
    done=False
    # 先尝试点确认框里的"取消"
    try:
        page.evaluate("""() => {
          const dlg=document.querySelector('.deleteDialog, .pan-dialog-wrapper');
          if(!dlg) return;
          for(const n of dlg.querySelectorAll('button,span,div,a')){
            if((n.innerText||'').trim()==='取消'){ n.click(); return; }
          }
        }""")
        done=True
    except Exception as e: print("点取消异常:",e)
    page.wait_for_timeout(300)
    # 再ESC保险
    page.keyboard.press("Escape"); page.wait_for_timeout(200)
    # 检查确认框是否还在
    still=page.evaluate("""() => { const d=document.querySelector('.deleteDialog,.pan-dialog-wrapper'); return d? d.getBoundingClientRect().width>0 : false; }""")
    print("确认框还在?", still)
    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_web_canceled.png")
    print("已截图 _web_canceled.png")
    b.close()