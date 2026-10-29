# -*- coding: utf-8 -*-
"""用 CDP 真实鼠标事件点击网页端『重新扫描』，并等待扫描完成。不删除任何文件。"""
import time
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
        if(!t.startsWith('重新扫')) return;
        const r=n.getBoundingClientRect();
        if(r.width<=0||r.height<=0) return;
        if(!best || r.width*r.height<best.area)
          best={x:r.x+r.width/2, y:r.y+r.height/2, area:r.width*r.height, text:t,
                rect:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};
      });
      return best;
    }""")
    print("重新扫描按钮:", btn)
    if not btn:
        print("没找到按钮"); b.close(); raise SystemExit

    vp = page.viewport_size
    print("视口:", vp)

    cdp = ctx.new_cdp_session(page)
    cdp.send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": btn["x"], "y": btn["y"]})
    cdp.send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": btn["x"], "y": btn["y"],
                                          "button": "left", "clickCount": 1})
    cdp.send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": btn["x"], "y": btn["y"],
                                          "button": "left", "clickCount": 1})
    print("已点击")
    page.wait_for_timeout(1500)

    for i in range(60):
        st = page.evaluate(r"""() => {
          const t=(document.body.innerText||'').replace(/\s+/g,' ');
          const m=t.match(/(\d+)个重复文件/);
          return {count:m?m[1]:'?', scanning:/扫描中|正在扫描|请稍候|扫描进度/.test(t),
                  body:t.slice(0,160)};
        }""")
        print(f"[{i}] 重复={st['count']} 扫描中={st['scanning']}")
        if i % 5 == 0:
            print("   ", st["body"][:120])
        page.wait_for_timeout(1000)
        if not st["scanning"] and i > 2:
            break

    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_chk_rescan.png")
    print("已保存 _chk_rescan.png")
    b.close()
