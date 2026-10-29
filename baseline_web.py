# -*- coding: utf-8 -*-
"""网页端基线：测「点击删除按钮 → 弹出确认框」的界面响应延时。只测弹框，绝点确定。"""
import time
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222

def find_clear_page(ctx):
    for pg in ctx.pages:
        if "/disk/clear" in pg.url: return pg
    return None

def main():
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx=b.contexts[0]
        page=find_clear_page(ctx)
        if not page:
            print("未找到清理页, 当前页面:"); [print("  ",pg.url[:80]) for pg in ctx.pages]; return
        page.bring_to_front(); page.wait_for_timeout(800)
        print("当前URL:", page.url)

        # 判断是否在结果页(list)
        if "/list" not in page.url:
            print("不在扫描结果页, 需先扫描。请手动扫描或让我导航。")
            b.close(); return

        # 记录点前时间，点击「删除」按钮(顶部)，等确认框出现
        # 用 locator 精确匹配「删除」按钮(非"选择删除项")
        target=None
        for sel in ["button:has-text('删除')", "div:has-text('删除')", "text=删除"]:
            try:
                loc=page.locator(sel)
                n=loc.count()
                if n==0: continue
                # 找文本恰为'删除'且可见的元素
                for i in range(n):
                    el=loc.nth(i)
                    try:
                        t=(el.inner_text() or "").strip()
                    except Exception:
                        t=""
                    if t=="删除" and el.is_visible():
                        target=el; break
                if target: break
            except Exception:
                continue
        if not target:
            print("未找到『删除』按钮"); b.close(); return

        t0=time.perf_counter()
        target.click(timeout=4000)
        # 轮询：确认框/弹窗出现（查找"确定"/"取消"/"删除后"等）
        t_popup=None
        for _ in range(300):  # 最多3秒
            try:
                has = page.evaluate("""() => {
                  const txt=(document.body.innerText||'');
                  const dialogs=[...document.querySelectorAll('[role=dialog],.dialog,.modal,.popup,.confirm,[class*=dialog],[class*=confirm]')];
                  for(const d of dialogs){ const r=d.getBoundingClientRect(); if(r.width>0&&r.height>0) return true; }
                  return /确定|确认删除|删除后不可恢复|是否删除/.test(txt);
                }""")
            except Exception:
                has=False
            if has:
                t_popup=time.perf_counter(); break
            time.sleep(0.005)
        if t_popup:
            print(f"删除→确认框出现: {(t_popup-t0)*1000:.1f} ms")
        else:
            print("3秒内未检测到确认框")

        # 截图看确认框
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_web_confirm.png")
        print("已截图 _web_confirm.png")
        # ---- 不点确定，按 ESC 取消 ----
        page.keyboard.press("Escape")
        print("已按ESC取消(未删除任何文件)")
        b.close()

if __name__=="__main__": main()