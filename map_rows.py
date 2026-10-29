# -*- coding: utf-8 -*-
"""读取网页端每一行的文件名 + 可能的 fs_id(从属性/React props 里挖)。只读。"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("无清理页"); b.close(); raise SystemExit

    out = page.evaluate(r"""() => {
      const res = [];
      // 找到包含文件名的行容器（高度 40~60、宽度较大）
      const all = [...document.querySelectorAll('*')];
      const rows = [];
      for(const n of all){
        const t = n.innerText || '';
        if(!/【柚子扩容】/.test(t) || t.length > 200) continue;
        const r = n.getBoundingClientRect();
        if(r.width < 300 || r.height < 20 || r.height > 60) continue;
        // 只要最内层的行
        if(rows.some(x => x.contains(n))) continue;
        rows.push(n);
      }
      for(const n of rows){
        const m = (n.innerText||'').match(/【柚子扩容】[^\s]+/);
        // 挖属性里的长数字
        let ids = [];
        let cur = n;
        for(let d=0; d<4 && cur; d++){
          for(const a of cur.attributes || []){
            const mm = (a.value||'').match(/\b\d{12,20}\b/g);
            if(mm) ids.push(...mm.map(x=>a.name+'='+x));
          }
          // React fiber
          for(const k of Object.keys(cur)){
            if(k.startsWith('__reactProps') || k.startsWith('__reactFiber')){
              try{
                let o = cur[k];
                const seen = new Set();
                const walk = (v, depth) => {
                  if(!v || depth>4 || typeof v!=='object' || seen.has(v)) return;
                  seen.add(v);
                  for(const kk of Object.keys(v)){
                    const val = v[kk];
                    if(typeof val === 'string' && /^\d{12,20}$/.test(val)) ids.push(kk+'='+val);
                    else if(typeof val === 'number' && String(val).length>=12) ids.push(kk+'='+val);
                    else if(typeof val === 'object') walk(val, depth+1);
                  }
                };
                walk(o, 0);
              }catch(e){}
            }
          }
          cur = cur.parentElement;
        }
        res.push({name: m?m[0]:'', ids: [...new Set(ids)].slice(0,8)});
      }
      return res;
    }""")
    for i, r in enumerate(out, 1):
        print(f"第{i:2d}行 {r['name']}")
        if r["ids"]:
            print(f"        {r['ids']}")
    b.close()
