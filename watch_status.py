# -*- coding: utf-8 -*-
"""只读：一次性查看两端当前状态（不点击、不修改任何东西）。

用法: python watch_status.py
输出: 客户端确认弹窗是否就绪、网页端确认框/已选数量
"""
import sys

sys.path.insert(0, r"C:\Users\Administrator\baidu-dupe-clicker")
import sync_delete_v2 as core


def check_client():
    print("=== 客户端 ===")
    try:
        found = core.find_confirm_dialog()
        if found and found[2]:
            hwnd, rect, cxy, im, scale = found
            print(f"  ✅ 确认弹窗已就绪")
            print(f"     hwnd={hwnd}  rect={rect}  缩放={scale:.3f}")
            print(f"     『确定』客户区坐标={cxy}")
            return True
        print("  ❌ 没找到带『确定/取消』的『系统提示』弹窗")
        mw = core.find_main_window()
        if mw:
            print(f"     客户端主窗口在: hwnd={mw[0]} rect={mw[1]}")
        else:
            print("     连客户端主窗口都没找到（客户端没开？）")
        return False
    except Exception as e:
        print("  检查出错:", e)
        return False


def check_web():
    print("\n=== 网页端 ===")
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print("  playwright 不可用:", e)
        return False

    try:
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://{core.HOST}:{core.PORT}")
            ctx = b.contexts[0]
            page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
            if not page:
                print(f"  ❌ 没有打开清理页（当前页面: {[pg.url[:60] for pg in ctx.pages]}）")
                b.close()
                return False
            info = page.evaluate(r"""() => {
              const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
              const vis = dlg ? dlg.getBoundingClientRect().width>0 : false;
              let btn=null;
              if(vis) dlg.querySelectorAll('button,span,div,a').forEach(n=>{
                const r=n.getBoundingClientRect();
                if(r.width<=0||r.height<=0) return;
                if((n.innerText||'').trim()==='确定'){
                  if(!btn||r.width*r.height<btn.area) btn={x:r.x+r.width/2,y:r.y+r.height/2,area:r.width*r.height};
                }
              });
              const t=(document.body.innerText||'').replace(/\s+/g,' ');
              const m=t.match(/(\d+)个重复文件/), s=t.match(/已选(?:中)?(\d+)个文件/);
              return {dialogVisible:vis, confirm:btn, count:m?m[1]:'?', selected:s?s[1]:'?'};
            }""")
            b.close()

        if info["dialogVisible"] and info["confirm"]:
            print(f"  ✅ 确认框已就绪")
        else:
            print("  ❌ 确认框还没出来（还没点『删除』？）")
        print(f"     重复文件={info['count']}  已选={info['selected']}  确定按钮={info['confirm']}")
        return bool(info["dialogVisible"] and info["confirm"])
    except Exception as e:
        print("  连接失败（Edge 调试端口没开？）:", e)
        return False


if __name__ == "__main__":
    c = check_client()
    w = check_web()
    print("\n" + "=" * 46)
    if c and w:
        print("两端都就绪 → 可以点『② 同步删除』")
    else:
        print("还没准备好：客户端" + ("✓" if c else "✗") + "  网页端" + ("✓" if w else "✗"))
