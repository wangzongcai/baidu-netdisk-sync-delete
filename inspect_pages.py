# -*- coding: utf-8 -*-
"""诊断：列出所有 pan 页面及其所有 frame URL，并找含垃圾文件清理的 frame。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx=b.contexts[0]
    print("总页面:", len(ctx.pages))
    target_frame=None
    for i,pg in enumerate(ctx.pages):
        try: t=pg.title()
        except Exception: t=""
        print(f"page[{i}]: {t[:30]!r} | {pg.url[:100]}")
        if "pan.baidu.com" in pg.url:
            for f in pg.frames:
                if set(f.url):
                    print("    frame:", f.url[:110])
                try:
                    txt=f.evaluate("()=>{let s='';document.querySelectorAll('div,span').forEach(n=>{const r=n.getBoundingClientRect();if(r.width>0&&r.height>0){const t=(n.innerText||'').trim();if(t.length>=4&&t.length<40)s+=t+'\\n';}});return s;}")
                except Exception:
                    txt=""
                if txt and "垃圾文件清理" in txt:
                    target_frame=f
                    print("    >>> 该 frame 含『垃圾文件清理』")
    print("目标 frame:", target_frame.url[:80] if target_frame else None)
    b.close()