# -*- coding: utf-8 -*-
"""在 aipanwebtools frame 里找重复文件/清理入口。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx = b.contexts[0]
    page=None
    for pg in ctx.pages:
        if "pan.baidu.com" in pg.url: page=pg; break
    if not page:
        print("no pan page"); b.close(); raise SystemExit
    frame = None
    for f in page.frames:
        if "aipanwebtools" in f.url:
            frame = f; break
    if not frame:
        print("no aipanwebtools frame"); b.close(); raise SystemExit
    print("frame:", frame.url[:90])
    frame.wait_for_timeout(2000)
    try:
        items = frame.evaluate("""() => {
          const sel=new Set();
          document.querySelectorAll('a,div,span,li,button').forEach(n=>{
            if(!n.offsetParent) return;
            const t=(n.innerText||'').replace(/\\s+/g,' ').trim();
            if(t && t.length>=2 && t.length<34) sel.add(t);
          });
          return Array.from(sel);
        }""")
        print("=== tools frame 可见文本 ===")
        for t in items: print("  -", t)
    except Exception as e: print("err:",e)
    b.close()