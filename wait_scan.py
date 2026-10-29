# -*- coding: utf-8 -*-
"""等待扫描重复文件完成，抓取结果界面、删除/确定按钮。仅观察，不点击删除。"""
import time
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
JS="""() => {
  const out=[]; const seen=new Set();
  document.querySelectorAll('a,div,span,li,button,p,em,strong').forEach(n=>{
    const r=n.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    const t=(n.innerText||'').replace(/\\s+/g,' ').trim();
    if(t && t.length>=1 && t.length<48 && !seen.has(t)){ seen.add(t); out.push(t); }
  });
  return out;
}"""

def main():
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx=b.contexts[0]
        page=None
        for pg in ctx.pages:
            if "/disk/clear" in pg.url: page=pg; break
        if not page: print("no clear page"); return
        page.bring_to_front()

        last=""
        for i in range(60):  # 最多等 120 秒
            items=page.evaluate(JS)
            blob=" | ".join(items)
            scanning = ("停止扫描" in blob) or ("扫描中" in blob)
            if i % 4 == 0:
                print(f"[{(i+1)*2}s] 扫描中... 当前文本数={len(items)}")
            if not scanning and i > 1:
                print(f"扫描完成! 用时约 {(i+1)*2}s")
                break
            time.sleep(2)

        items=page.evaluate(JS)
        print(f"=== 结果界面可见文本 {len(items)} 条 ===")
        for t in items: print("  -", t)
        # 按钮
        print("=== 按钮类 ===")
        btns=page.evaluate("""() => {
          const out=[]; document.querySelectorAll('button,[role=button],a.btn,.btn,span.btn,div.btn').forEach(n=>{
            const r=n.getBoundingClientRect(); if(r.width<=0||r.height<=0) return;
            const t=(n.innerText||'').trim(); if(t) out.push(t);
          }); return [...new Set(out)];
        }""")
        for t in btns: print("  [btn]", t)
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_dupes_done.png", full_page=True)
        print("screenshot saved")
        b.close()

if __name__=="__main__": main()