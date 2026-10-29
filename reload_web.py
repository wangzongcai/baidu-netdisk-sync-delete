# -*- coding: utf-8 -*-
"""刷新网页端清理页，读取真实的剩余行。只读(不删除)。"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("无清理页"); b.close(); raise SystemExit

    page.reload()
    page.wait_for_timeout(3000)

    for i in range(20):
        st = page.evaluate(r"""() => {
          const t=(document.body.innerText||'').replace(/\s+/g,' ');
          const m=t.match(/(\d+)个重复文件/);
          const names=[...document.querySelectorAll('*')].map(n=>{
            const s=(n.innerText||'');
            if(s.length>0 && s.length<120){
              const mm=s.match(/【柚子扩容】[^\s]+/);
              return mm?mm[0]:null;
            }
            return null;
          }).filter(Boolean);
          return {count:m?m[1]:'?', rows:[...new Set(names)], selected:(t.match(/已选(\d+)个文件/)||[])[1]||'0',
                  scanning:/扫描中|正在扫描|请稍候/.test(t)};
        }""")
        print(f"[{i+1}] 重复={st['count']} 已选={st['selected']} 扫描中={st['scanning']} 行数={len(st['rows'])}")
        for r in st["rows"]:
            print("   ", r)
        if not st["scanning"] and st["count"] != "?":
            break
        page.wait_for_timeout(2000)

    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_chk_web_reload.png")
    print("已保存 _chk_web_reload.png")
    b.close()
