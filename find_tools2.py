# -*- coding: utf-8 -*-
"""点击工具菜单后，dump 全部可见短文本，定位清理入口。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx = b.contexts[0]
    page = None
    for pg in ctx.pages:
        if "pan.baidu.com" in pg.url:
            page = pg; break
    if not page:
        print("no pan page"); b.close(); raise SystemExit
    # 再点一次工具，然后 dump 全部可见不长文本
    for sel in ["div[title='工具']", "a:has-text('工具')"]:
        try:
            el = page.locator(sel).first
            if el.count():
                try:
                    el.click(timeout=2500); break
                except Exception: pass
        except Exception: pass
    page.wait_for_timeout(1600)
    try:
        items = page.evaluate("""() => {
          const sel = new Set();
          document.querySelectorAll('div,span,a,li,button,em').forEach(n=>{
            if(!n.offsetParent) return;               // 必须可见
            const t=(n.innerText||'').replace(/\\s+/g,' ').trim();
            if(t && t.length>=2 && t.length<24) sel.add(t);
          });
          return Array.from(sel);
        }""")
        print("=== 工具展开后全部可见短文本 ===")
        for t in items: print("  -", t)
    except Exception as e:
        print("err:", e)
    b.close()