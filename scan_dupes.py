# -*- coding: utf-8 -*-
"""点击「扫描重复文件」，进入扫描/结果界面，扫描按钮与删除/确定控件。仅扫描不删除。"""
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

        # 点击「扫描重复文件」（点文字节点）
        clicked=False
        for sel in ["text=扫描重复文件", "div:has-text('扫描重复文件') >> nth=0"]:
            try:
                el=page.locator(sel).first
                if el.count():
                    el.click(timeout=4000)
                    clicked=True; print("clicked:",sel); break
            except Exception as e: print("try fail:",e)
        print("clicked?",clicked)
        page.wait_for_timeout(3000)

        # 扫描后 dump 可见文本与按钮
        JS="""() => {
          const out=[];
          const seen=new Set();
          document.querySelectorAll('a,div,span,li,button,p,em,strong').forEach(n=>{
            const r=n.getBoundingClientRect();
            if(r.width<=0||r.height<=0) return;
            const t=(n.innerText||'').replace(/\\s+/g,' ').trim();
            if(t && t.length>=2 && t.length<44 && !seen.has(t)){ seen.add(t); out.push(t); }
          });
          return out;
        }"""
        items=page.evaluate(JS)
        print(f"=== 扫描后可见文本 {len(items)} 条 ===")
        for t in items: print("  -", t)
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_dupes.png")
        print("screenshot saved")
        b.close()

if __name__=="__main__": main()