# -*- coding: utf-8 -*-
"""只读：读取网页端已勾选文件名 + 客户端主窗口截图(供人工核对)。不点击。"""
import re
from playwright.sync_api import sync_playwright
import importlib.util, sys

# 复用 sync_delete_v2 的窗口抓取
spec = importlib.util.spec_from_file_location(
    "sd2", r"C:\Users\Administrator\baidu-dupe-clicker\sync_delete_v2.py")
sd2 = importlib.util.module_from_spec(spec)
sys.argv = ["sd2"]           # 防止其 main 被触发
spec.loader.exec_module(sd2)

mw = sd2.find_main_window()
if mw:
    im = sd2.capture(mw[0])
    if im:
        im.save(r"C:\Users\Administrator\baidu-dupe-clicker\_chk_client.png")
        print(f"客户端主窗口截图 _chk_client.png {im.size}")
        # 顶部已选行数文字区域留给人看，不做 OCR

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("无清理页"); b.close(); raise SystemExit
    out = page.evaluate(r"""() => {
      const rows=[...document.querySelectorAll('tr,li,div')].filter(n=>{
        const t=(n.innerText||'');
        return t.includes('柚子扩容') && t.length<120;
      });
      const picked=[];
      for(const n of rows){
        const cls = (n.className||'')+'';
        let checked=false;
        // 看是否含表示勾选的子元素
        n.querySelectorAll('input,span,i,em,b').forEach(c=>{
          const cc=((c.className&&(c.className.baseVal!==undefined?c.className.baseVal:c.className))||'')+'';
          if(/checked/i.test(cc)) checked=true;
          if(c.tagName==='INPUT' && c.checked) checked=true;
        });
        // 背景高亮行
        const bg = getComputedStyle(n).backgroundColor;
        const txt=(n.innerText||'').replace(/\s+/g,' ');
        const m=txt.match(/【柚子扩容】[^\s]+/);
        if((checked || (bg && bg!=='rgba(0, 0, 0, 0)' && bg!=='rgb(255, 255, 255)')) && m)
          picked.push({name:m[0], checked, bg});
      }
      const txt=(document.body.innerText||'').replace(/\s+/g,' ');
      const s=txt.match(/已选(\d+)个文件/);
      return {selected:s?s[1]:'?', picked:picked.slice(0,6)};
    }""")
    print("网页端 已选:", out["selected"])
    for x in out["picked"]:
        print("  ", x)
    b.close()
