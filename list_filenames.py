# -*- coding: utf-8 -*-
"""读取网页端当前重复文件列表的文件名(按行序)，用于和客户端对齐。只读。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx=b.contexts[0]
    page=None
    for pg in ctx.pages:
        if "/disk/clear" in pg.url: page=pg; break
    if not page: print("no clear page"); b.close(); raise SystemExit
    page.wait_for_timeout(500)
    print("URL:", page.url)
    # 抓所有含【柚子扩容】的文件名行
    names=page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('div,span,a').forEach(n=>{
        const r=n.getBoundingClientRect(); if(r.width<=0||r.height<=0) return;
        const t=(n.innerText||'').trim();
        if(t.startsWith('【柚子扩容】') && t.length>10 && t.length<80) {
          // 去重(父容器可能重复)
          if(!out.includes(t)) out.push(t);
        }
      });
      return out;
    }""")
    print(f"网页端重复文件名 ({len(names)}):")
    for i,nm in enumerate(names): print(f"  {i+1}. {nm}")
    b.close()