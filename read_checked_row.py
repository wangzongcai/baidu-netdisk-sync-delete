# -*- coding: utf-8 -*-
"""只读：定位网页端被勾选的行并输出文件名（多种判定方式兜底）。"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("无清理页"); b.close(); raise SystemExit
    out = page.evaluate(r"""() => {
      const res = {byClass: [], byBg: []};
      const nameOf = (n) => {
        const t=(n.innerText||'').replace(/\s+/g,' ');
        const m=t.match(/【柚子扩容】[^\s]+/);
        return m?m[0]:null;
      };
      // 方式1: class 含 checked 的可见小元素
      document.querySelectorAll('*').forEach(n=>{
        const cn = (n.className && (n.className.baseVal!==undefined?n.className.baseVal:n.className)) || '';
        if(typeof cn!=='string' || !/check/i.test(cn)) return;
        const r=n.getBoundingClientRect();
        if(r.width<=0||r.height<=0) return;
        // 往上找行
        let row=n;
        for(let i=0;i<10&&row;i++){ if(nameOf(row)) break; row=row.parentElement; }
        if(!row) return;
        res.byClass.push({cls:cn.slice(0,60), w:Math.round(r.width), h:Math.round(r.height),
                          x:Math.round(r.x), y:Math.round(r.y), name:nameOf(row)});
      });
      // 方式2: 背景非白的行
      document.querySelectorAll('*').forEach(n=>{
        const nm = nameOf(n);
        if(!nm) return;
        const r=n.getBoundingClientRect();
        if(r.width<300||r.height<20||r.height>60) return;
        const bg=getComputedStyle(n).backgroundColor;
        if(bg && bg!=='rgba(0, 0, 0, 0)' && bg!=='rgb(255, 255, 255)' && !/255, 255, 255/.test(bg))
          res.byBg.push({bg, name:nm, y:Math.round(r.y)});
      });
      return res;
    }""")
    print("== class 含 check 的元素 ==")
    for x in out["byClass"][:12]:
        print(" ", x)
    print("== 背景非白且含文件名的行 ==")
    seen = set()
    for x in out["byBg"][:12]:
        if x["name"] in seen:
            continue
        seen.add(x["name"])
        print(" ", x)
    b.close()
