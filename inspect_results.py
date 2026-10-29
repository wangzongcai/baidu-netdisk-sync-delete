# -*- coding: utf-8 -*-
"""扫描结果后：定位重复文件列表、选择项、删除/确定按钮。仅观察，不点击删除。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222

JS="""() => {
  const out=[]; const seen=new Set();
  document.querySelectorAll('a,div,span,li,button,p,em,strong,label').forEach(n=>{
    const r=n.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    const t=(n.innerText||'').replace(/\\s+/g,' ').trim();
    if(t && t.length>=1 && t.length<50 && !seen.has(t)){ seen.add(t); out.push(t); }
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
        if not page:
            print("no clear page; pages:");
            for pg in ctx.pages: print("  ",pg.url[:80])
            return
        page.bring_to_front()
        page.wait_for_timeout(800)
        print("url:", page.url)
        items=page.evaluate(JS)
        print(f"=== 可见文本 {len(items)} 条 ===")
        for t in items: print("  -", t)

        print("=== 按钮/可点元素(带坐标) ===")
        btns=page.evaluate("""() => {
          const out=[];
          document.querySelectorAll('button,[role=button],a.btn,.btn,span.btn,div.btn,a,li,span[class*=btn]').forEach(n=>{
            const r=n.getBoundingClientRect();
            if(r.width<=0||r.height<=0) return;
            const t=(n.innerText||'').trim().replace(/\\s+/g,' ');
            if(t && t.length<30) out.push({t, x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2), w:Math.round(r.width), h:Math.round(r.height)});
          });
          return out;
        }""")
        for bt in btns: print(f"  [{bt['w']}x{bt['h']}] @({bt['x']},{bt['y']}) {bt['t']!r}")
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_results.png", full_page=True)
        print("screenshot saved")
        b.close()

if __name__=="__main__": main()