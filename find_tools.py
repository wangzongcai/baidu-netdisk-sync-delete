# -*- coding: utf-8 -*-
"""点击「工具」菜单，列出其下的清理类入口。只读导航，不删除。"""
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

    # 点击文本为「工具」的可点击元素
    clicked = False
    for sel in ["a:has-text('工具')", "div:has-text('工具')", "li:has-text('工具')"]:
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible():
                el.click(timeout=3000)
                clicked = True
                print("clicked:", sel)
                break
        except Exception:
            continue
    page.wait_for_timeout(1500)
    # 列出当前可见的含清理/垃圾关键词的文本
    try:
        texts = page.evaluate("""() => {
          const out = new Set();
          const nodes = document.querySelectorAll('div,span,a,li,button');
          for (const n of nodes) {
            const t = (n.innerText||'').trim();
            if (t && t.length<40 && /垃圾|清理|回收|重复|去重|整理/.test(t)) out.add(t);
          }
          return Array.from(out).slice(0,40);
        }""")
        print("清理类关键词可见文本:")
        for t in texts: print("  -", t)
    except Exception as e:
        print("scan err:", e)
    b.close()