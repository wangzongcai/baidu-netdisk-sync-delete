# -*- coding: utf-8 -*-
"""只读：查看清理页当前的勾选数量、确认框状态，不点击任何东西。"""
import sys

sys.path.insert(0, r"C:\Users\Administrator\baidu-dupe-clicker")
import sync_delete_v2 as core

try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    print("playwright 不可用:", e)
    raise SystemExit

with sync_playwright() as p:
    try:
        b = p.chromium.connect_over_cdp(f"http://{core.HOST}:{core.PORT}")
    except Exception as e:
        print("连不上 Edge 调试端口（Edge 没开？）:", e)
        raise SystemExit
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("当前没有清理页，打开的页面是:")
        for pg in ctx.pages:
            print("   ", pg.url[:100])
        b.close()
        raise SystemExit

    info = page.evaluate(r"""() => {
      const t=(document.body.innerText||'').replace(/\s+/g,' ');
      const m=t.match(/(\d+)个重复文件/);
      const s=t.match(/已选(?:中)?(\d+)个文件/);
      const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
      const vis = dlg ? dlg.getBoundingClientRect().width>0 : false;
      // 勾选框/行有多少个
      let checked = 0;
      document.querySelectorAll('input[type=checkbox]').forEach(n=>{ if(n.checked) checked++; });
      return {count:m?m[1]:'?', selected:s?s[1]:'?', dialog:vis, checkedBoxes:checked};
    }""")
    print("重复文件数 =", info["count"])
    print("已选 =", info["selected"])
    print("确认框可见 =", info["dialog"])
    print("勾选框数量 =", info["checkedBoxes"])
    print("页面标题 =", page.title())
    b.close()
