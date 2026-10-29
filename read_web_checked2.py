# -*- coding: utf-8 -*-
"""只读：找到网页端带'选中'样式的行，dump其文本。绝不点击。"""
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
    out=page.evaluate(r"""() => {
      const hits=[];
      // 遍历所有元素, 找 className 含 check/selected 且视觉可见的, 取其最近含柚子扩容的文本
      const all=[...document.querySelectorAll('*')];
      for(const n of all){
        const cn = (n.className && (n.className.baseVal!==undefined?n.className.baseVal:n.className)) || '';
        if(typeof cn!=='string') continue;
        if(!/check|selected|active/i.test(cn)) continue;
        if(!/check|selected|active/i.test(cn)) continue;
        const r=n.getBoundingClientRect();
        if(r.width<=0||r.height<=0) continue;
        // 只看像复选框/勾选图标的(尺寸小)
        if(r.width>40||r.height>40) continue;
        // 该元素是否在"选中"态(类名含 checked/selected 而非仅是容器)
        const isChecked=/checked|selected|active/i.test(cn);
        if(!isChecked) continue;
        // 找同行文件名
        let row=n;
        for(let i=0;i<8&&row;i++){ if((row.innerText||'').includes('柚子扩容')) break; row=row.parentElement; }
        const t=(row?row.innerText:'').replace(/\s+/g,' ');
        const m=t.match(/【柚子扩容】[^\s]+/);
        hits.push({cls:cn.slice(0,50), rect:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)], name:m?m[0]:''});
      }
      return hits;
    }""")
    print(f"含 check/selected 的小元素 {len(out)} 个:")
    for h in out: print(f"  cls={h['cls']!r} @{h['rect']} name={h['name']}")
    b.close()