# -*- coding: utf-8 -*-
"""展开「选择删除项」下拉，列出选项。只展开，不选择、不删除。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222

def main():
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx=b.contexts[0]
        page=None
        for pg in ctx.pages:
            if "/disk/clear" in pg.url: page=pg; break
        if not page: print("no clear page"); return
        page.bring_to_front()
        page.wait_for_timeout(500)

        # 点「选择删除项」
        for sel in ["text=选择删除项", "div:has-text('选择删除项') >> nth=0", "button:has-text('选择删除项')"]:
            try:
                el=page.locator(sel).first
                if el.count() and el.is_visible():
                    el.click(timeout=3000); print("已点开选择删除项:",sel); break
            except Exception as e: print("try:",e)
        page.wait_for_timeout(1200)

        # 扫描所有可见文本(下拉项会出现)
        items=page.evaluate("""() => {
          const out=[]; const seen=new Set();
          document.querySelectorAll('a,div,span,li,button,p,em,strong,label').forEach(n=>{
            const r=n.getBoundingClientRect();
            if(r.width<=0||r.height<=0) return;
            const t=(n.innerText||'').replace(/\\s+/g,' ').trim();
            if(t && t.length>=1 && t.length<40 && !seen.has(t)){ seen.add(t); out.push(t); }
          });
          return out;
        }""")
        print("=== 展开后可见文本 ===")
        for t in items: print("  -", t)
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_select_menu.png")
        print("screenshot saved")
        b.close()

if __name__=="__main__": main()