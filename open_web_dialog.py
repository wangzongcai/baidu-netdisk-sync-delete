# -*- coding: utf-8 -*-
"""点击网页端『删除』按钮，把确认框调出来（不删除）。"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("无清理页"); b.close(); raise SystemExit

    btn = page.evaluate(r"""() => {
      let best=null;
      document.querySelectorAll('button,span,div,a').forEach(n=>{
        const t=(n.innerText||'').trim();
        if(t!=='删除') return;
        const r=n.getBoundingClientRect();
        if(r.width<=0||r.height<=0) return;
        if(!best||r.width*r.height<best.area)
          best={x:r.x+r.width/2,y:r.y+r.height/2,area:r.width*r.height};
      });
      return best;
    }""")
    print("删除按钮:", btn)
    if not btn:
        print("未找到删除按钮"); b.close(); raise SystemExit

    cdp = ctx.new_cdp_session(page)
    cdp.send("Input.dispatchMouseEvent", {"type":"mousePressed","x":btn["x"],"y":btn["y"],"button":"left","clickCount":1})
    cdp.send("Input.dispatchMouseEvent", {"type":"mouseReleased","x":btn["x"],"y":btn["y"],"button":"left","clickCount":1})
    page.wait_for_timeout(900)

    info = page.evaluate(r"""() => {
      const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
      const vis=dlg?dlg.getBoundingClientRect().width>0:false;
      const t=(document.body.innerText||'').replace(/\s+/g,' ');
      const s=t.match(/已选(\d+)个文件/);
      return {dialogVisible:vis, selected:s?s[1]:'?'};
    }""")
    print("网页端:", info)
    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_chk_web_dialog.png")
    print("已保存 _chk_web_dialog.png")
    b.close()
