# -*- coding: utf-8 -*-
"""只读：确认网页端当前勾选的是哪个文件（关闭确认框前先读）。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx=b.contexts[0]
    page=None
    for pg in ctx.pages:
        if "/disk/clear" in pg.url: page=pg; break
    if not page: print("no clear page"); b.close(); raise SystemExit
    page.wait_for_timeout(300)
    # 找被勾选(checked)的行及其文件名
    sel=page.evaluate("""() => {
      const out=[];
      // 找所有 checkbox 元素
      document.querySelectorAll('input[type=checkbox],[class*=checkbox],[class*=Checkbox]').forEach(cb=>{
        let checked=false;
        if(cb.tagName==='INPUT') checked=cb.checked;
        else checked=/checked|selected|active/i.test(cb.className) || cb.getAttribute('aria-checked')==='true';
        if(checked){
          // 向上找行，取行内文件名
          let row=cb;
          for(let i=0;i<6 && row;i++){ if((row.innerText||'').includes('柚子扩容')) break; row=row.parentElement; }
          const txt=(row?row.innerText:'').replace(/\\s+/g,' ');
          const m=txt.match(/【柚子扩容】[^\\s]+/);
          out.push(m?m[0]:txt.slice(0,60));
        }
      });
      return [...new Set(out)];
    }""")
    print("网页端已勾选的文件:", sel)
    b.close()