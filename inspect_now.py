# -*- coding: utf-8 -*-
"""只读：截图网页端当前状态，检测是否有删除确认框及其"确定"位置。绝不点击。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx=b.contexts[0]
    page=None
    for pg in ctx.pages:
        if "/disk/clear" in pg.url: page=pg; break
    if not page: print("no clear page"); b.close(); raise SystemExit
    page.wait_for_timeout(400)
    print("URL:", page.url)
    info=page.evaluate("""() => {
      const dlg=document.querySelector('.pan-dialog-wrapper.deleteDialog, .deleteDialog');
      let dstate=null;
      if(dlg){const r=dlg.getBoundingClientRect(); dstate={visible:r.width>0&&r.height>0, rect:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)], text:(dlg.innerText||'').replace(/\\s+/g,' ').trim().slice(0,120)};}
      let best=null;
      document.querySelectorAll('button,span,div,a').forEach(n=>{
        const r=n.getBoundingClientRect(); if(r.width<=0||r.height<=0) return;
        if((n.innerText||'').trim()==='确定'){ if(!best||r.width*r.height<best.area) best={x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height),area:r.width*r.height}; }
      });
      return {dialog:dstate, confirmBtn:best, bodyHasConfirm:/确定/.test(document.body.innerText||'')};
    }""")
    print("对话框:", info["dialog"])
    print("确定按钮:", info["confirmBtn"])
    print("body含确定:", info["bodyHasConfirm"])
    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_web_state_now.png")
    print("截图 _web_state_now.png")
    b.close()