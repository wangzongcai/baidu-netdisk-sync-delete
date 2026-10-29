# -*- coding: utf-8 -*-
"""等待网页端扫描结束(以『停止扫描』消失为准)，然后列出真实行。只读。"""
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("无清理页"); b.close(); raise SystemExit

    t0 = time.time()
    last = ""
    for i in range(240):
        st = page.evaluate(r"""() => {
          const t=(document.body.innerText||'').replace(/\s+/g,' ');
          const m=t.match(/(\d+)个重复文件/);
          const scanning=/停止扫描/.test(t);
          return {count:m?m[1]:'?', scanning, head:t.slice(0,90)};
        }""")
        line = f"重复={st['count']} 扫描中={st['scanning']}"
        if line != last:
            print(f"[{int(time.time()-t0):3d}s] {line}")
            last = line
        if not st["scanning"] and st["count"] != "?":
            break
        time.sleep(1)

    # 列出真实行
    rows = page.evaluate(r"""() => {
      const out=[];
      const all=[...document.querySelectorAll('*')];
      const picked=[];
      for(const n of all){
        const t=n.innerText||'';
        if(!/【柚子扩容】/.test(t) || t.length>200) continue;
        const r=n.getBoundingClientRect();
        if(r.width<300||r.height<20||r.height>60) continue;
        if(picked.some(x=>x.contains(n))) continue;
        picked.push(n);
        const m=t.match(/【柚子扩容】[^\s]+/);
        out.push(m?m[0]:'');
      }
      const tt=(document.body.innerText||'').replace(/\s+/g,' ');
      return {rows:out, selected:(tt.match(/已选(?:中)?(\d+)个文件/)||[])[1]||'0',
              count:(tt.match(/(\d+)个重复文件/)||[])[1]||'?'};
    }""")
    print(f"\n头部: {rows['count']} 个重复文件, 已选 {rows['selected']}")
    for i, r in enumerate(rows["rows"], 1):
        print(f"  第{i:2d}行 {r}")
    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_chk_rescan_done.png")
    print("已保存 _chk_rescan_done.png")
    b.close()
