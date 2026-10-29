# -*- coding: utf-8 -*-
"""列出网盘工具列表页里的所有工具入口文本。"""
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
    print("url:", page.url)
    page.wait_for_timeout(1500)
    try:
        items = page.evaluate("""() => {
          const sel=new Set();
          document.querySelectorAll('a,div,span,li,button').forEach(n=>{
            if(!n.offsetParent) return;
            const t=(n.innerText||'').replace(/\\s+/g,' ').trim();
            if(t && t.length>=2 && t.length<30) sel.add(t);
          });
          return Array.from(sel);
        }""")
        print("=== 工具列表页全部可见文本 ===")
        for t in items: print("  -", t)
    except Exception as e: print("err:",e)
    b.close()