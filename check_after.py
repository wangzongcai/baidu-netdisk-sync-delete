# -*- coding: utf-8 -*-
"""只读：查看删除后两端状态，并把客户端主窗口截图保存供人工核对。"""
import sys

sys.path.insert(0, r"C:\Users\Administrator\baidu-dupe-clicker")
import sync_delete_v2 as core

DIR = r"C:\Users\Administrator\baidu-dupe-clicker"

print("=== 客户端 ===")
found = core.find_confirm_dialog()
if found and found[2]:
    print(f"  确认弹窗仍在: hwnd={found[0]} 缩放={found[4]:.3f}")
else:
    print("  确认弹窗已关闭（正常）")

mw = core.find_main_window()
if mw:
    im = core.capture(mw[0])
    if im:
        p = f"{DIR}\\_after_check_client.png"
        im.save(p)
        print(f"  主窗口截图已保存: {p}  尺寸={im.size}")
    else:
        print("  截图失败")
else:
    print("  未找到客户端主窗口")

print("\n=== 网页端 ===")
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://{core.HOST}:{core.PORT}")
        ctx = b.contexts[0]
        page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
        if not page:
            print("  当前没有清理页，打开过的页面:")
            for pg in ctx.pages:
                print("   ", pg.url[:90])
            b.close()
        else:
            info = page.evaluate(r"""() => {
              const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
              const vis = dlg ? dlg.getBoundingClientRect().width>0 : false;
              const t=(document.body.innerText||'').replace(/\s+/g,' ');
              const m=t.match(/(\d+)个重复文件/), s=t.match(/已选(?:中)?(\d+)个文件/);
              const sp=t.match(/占用空间([\d.]+[A-Z]+)/);
              return {dialogVisible:vis, count:m?m[1]:'?', selected:s?s[1]:'?',
                      space:sp?sp[1]:'?'};
            }""")
            print(f"  确认框={info['dialogVisible']}  重复文件={info['count']}  "
                  f"已选={info['selected']}  占用={info['space']}")
            page.screenshot(path=f"{DIR}\\_after_check_web.png")
            print(f"  网页端截图: {DIR}\\_after_check_web.png")
            b.close()
except Exception as e:
    print("  查询失败:", e)
