# -*- coding: utf-8 -*-
"""只读：查询网页端当前剩余数量与列表。"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("无清理页"); b.close(); raise SystemExit
    page.wait_for_timeout(1200)
    out = page.evaluate(r"""() => {
      const t=(document.body.innerText||'').replace(/\s+/g,' ');
      const m=t.match(/(\d+)个重复文件/);
      const rows=[];
      const picked=[];
      for(const n of document.querySelectorAll('*')){
        const s=n.innerText||'';
        if(!/【柚子扩容】/.test(s) || s.length>200) continue;
        const r=n.getBoundingClientRect();
        if(r.width<300||r.height<20||r.height>60) continue;
        if(picked.some(x=>x.contains(n))) continue;
        picked.push(n);
        const mm=s.match(/【柚子扩容】[^\s]+/);
        rows.push(mm?mm[0]:'');
      }
      return {count:m?m[1]:'?', rows, head:t.slice(0,100)};
    }""")
    print("网页端:", out["count"], "个重复文件")
    print("头部:", out["head"])
    for i, r in enumerate(out["rows"], 1):
        print(f"  第{i}行 {r}")
    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_chk_web_final.png")
    b.close()
