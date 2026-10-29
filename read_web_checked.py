# -*- coding: utf-8 -*-
"""只读：dump 网页端第一行DOM结构，找出勾选标记与文件名，确认勾的是哪个文件。绝不点击。"""
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
    info=page.evaluate(r"""() => {
      // 找到所有包含【柚子扩容】的"行"元素(取最内层且含复选框的)
      const res=[];
      const all=[...document.querySelectorAll('div,li,tr')];
      for(const n of all){
        const t=(n.innerText||'').replace(/\s+/g,' ').trim();
        if(!t.includes('柚子扩容')) continue;
        // 只取"行"级: 高度在20~60, 宽度>500
        const r=n.getBoundingClientRect();
        if(r.height<20||r.height>70||r.width<600) continue;
        // 找该行内的复选框元素(span/i/svg/div with checkbox class)
        const cbEls=[...n.querySelectorAll('*')].filter(x=>/checkbox|check|u-check|selected|checked/i.test(x.className && (x.className.baseVal||x.className)||''));
        const cbInfo=cbEls.map(x=>({cls:(x.className&&(x.className.baseVal||x.className))||'', tag:x.tagName, checked:/checked|selected/i.test((x.className&&(x.className.baseVal||x.className))||'')||x.getAttribute('aria-checked')==='true'}));
        const m=t.match(/【柚子扩容】[^\s]+/);
        res.push({name:m?m[0]:t.slice(0,50), rect:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)], cbs:cbInfo});
      }
      // 去重按rect
      const seen=new Set(); const out=[];
      for(const x of res){ const k=x.rect.join(','); if(!seen.has(k)){seen.add(k); out.push(x);} }
      return out;
    }""")
    print(f"找到 {len(info)} 行:")
    for i,x in enumerate(info):
        cbs=", ".join(f"{c['tag']}:{c['cls'][:40]}({'✓' if c['checked'] else ' '})" for c in x["cbs"][:3])
        print(f"  [{i}] {x['name']}")
        print(f"      rect={x['rect']}  cbs=[{cbs}]")
    b.close()