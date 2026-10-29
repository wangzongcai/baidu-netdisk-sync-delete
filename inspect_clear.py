# -*- coding: utf-8 -*-
"""进入 /disk/clear 页，扫描其分类、扫描/删除/确定按钮，截图。不删除。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222

def main():
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx=b.contexts[0]
        page=None
        for pg in ctx.pages:
            if "/disk/clear" in pg.url:
                page=pg; break
        if not page:
            print("未找到 /disk/clear 页面"); return
        page.bring_to_front()
        page.wait_for_timeout(3500)
        print("url:", page.url)
        try: print("title:", page.title())
        except Exception: pass

        JS="""() => {
          const out=[];
          const seen=new Set();
          document.querySelectorAll('a,div,span,li,button,p,em,strong').forEach(n=>{
            const r=n.getBoundingClientRect();
            if(r.width<=0||r.height<=0) return;
            const t=(n.innerText||'').replace(/\\s+/g,' ').trim();
            if(t && t.length>=2 && t.length<40 && !seen.has(t)){ seen.add(t); out.push(t); }
          });
          return out;
        }"""
        items=page.evaluate(JS)
        print(f"=== 可见文本 {len(items)} 条 ===")
        for t in items: print("  -", t)

        # 列出所有可见 button 及其文本
        print("=== 可见按钮 ===")
        btns=page.evaluate("""() => {
          const out=[];
          document.querySelectorAll('button,[role=button],a.btn,.btn,span.btn').forEach(n=>{
            const r=n.getBoundingClientRect();
            if(r.width<=0||r.height<=0) return;
            const t=(n.innerText||'').trim();
            if(t) out.push(t);
          });
          return out;
        }""")
        for t in btns: print("  [btn]", t)

        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_clear.png", full_page=False)
        print("screenshot saved")
        b.close()

if __name__=="__main__": main()