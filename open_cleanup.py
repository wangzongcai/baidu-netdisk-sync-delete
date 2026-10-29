# -*- coding: utf-8 -*-
"""在 aitools frame 里点击「垃圾文件清理」，进入该功能页并列出页面内容。不删除。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222

def main():
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = b.contexts[0]
        page=None
        for pg in ctx.pages:
            if "pan.baidu.com" in pg.url: page=pg; break
        if not page: print("no pan page"); return
        page.bring_to_front()

        frame = None
        for f in page.frames:
            if "aitools" in f.url: frame=f; break
        if not frame:
            print("no aitools frame"); return
        print("aitools frame:", frame.url[:90])

        # 点击「垃圾文件清理」卡片
        clicked=False
        for sel in ["text=垃圾文件清理", "div:has-text('垃圾文件清理') >> nth=0"]:
            try:
                el = frame.locator(sel).first
                if el.count():
                    el.click(timeout=4000)
                    clicked=True; print("clicked:", sel); break
            except Exception as e:
                print("click try fail:", e)
        print("clicked?", clicked)
        page.wait_for_timeout(3000)

        # 进入后可能是新页面/新frame，扫描所有清理相关按钮
        print("=== 当前所有 frame ===")
        for f in page.frames:
            if set(f.url):
                print("  -", f.url[:100])

        # 扫描所有 frame 中含关键动作词的文本
        KEY = ["清理","扫描","重复","删除","确定","取消","立即","开始","选择","共","个","释放","空间","文件"]
        JS = """() => {
          const out=new Set();
          document.querySelectorAll('a,div,span,li,button,p,em,strong').forEach(n=>{
            const r=n.getBoundingClientRect();
            if(r.width<=0||r.height<=0) return;
            const t=(n.innerText||'').replace(/\\s+/g,' ').trim();
            if(t && t.length>=2 && t.length<34) out.add(t);
          });
          return Array.from(out);
        }"""
        for f in page.frames:
            try: items=f.evaluate(JS)
            except Exception: continue
            hits=[t for t in items if any(k in t for k in KEY)]
            if hits:
                print(f"--- frame {f.url[:55]} ---")
                for t in hits[:40]: print("   ", t)
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_cleanup.png")
        print("screenshot saved")
        b.close()

if __name__=="__main__": main()