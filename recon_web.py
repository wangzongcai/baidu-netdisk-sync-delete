# -*- coding: utf-8 -*-
"""侦察网页端删除确认框：点‘删除’→等确认框→截图→ESC取消。不点确定,不真删。"""
import time
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222

def main():
    with sync_playwright() as p:
        b=p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx=b.contexts[0]
        page=None
        for pg in ctx.pages:
            if "/disk/clear" in pg.url: page=pg; break
        if not page:
            print("没有清理页, 当前:"); [print(" ",pg.url[:80]) for pg in ctx.pages]; return
        page.bring_to_front(); page.wait_for_timeout(600)
        print("URL:", page.url)

        # 找文本恰为'删除'的可见按钮
        target=None
        loc=page.locator("text=删除")
        for i in range(loc.count()):
            el=loc.nth(i)
            try:
                if (el.inner_text() or "").strip()=="删除" and el.is_visible():
                    target=el; break
            except Exception: pass
        if not target:
            print("未找到‘删除’按钮"); b.close(); return

        t0=time.perf_counter()
        target.click(timeout=4000)
        # 等确认框出现
        found=False
        for _ in range(400):
            found=page.evaluate("""() => {
              const d=[...document.querySelectorAll('[role=dialog],[class*=dialog],[class*=Dialog],[class*=modal],[class*=Modal],[class*=confirm],[class*=Confirm]')];
              for(const e of d){const r=e.getBoundingClientRect(); if(r.width>50&&r.height>30) return true;}
              return /确定|确认删除|删除后|不可恢复|是否删除|删除文件/.test(document.body.innerText||'');
            }""")
            if found: break
            time.sleep(0.005)
        dt=(time.perf_counter()-t0)*1000
        print(f"点删除后 {dt:.1f}ms 检测到确认框: {found}")

        page.wait_for_timeout(300)
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_web_recon.png", full_page=False)
        print("已截图 _web_recon.png")

        # 列出确认框内所有按钮文本及坐标
        btns=page.evaluate("""() => {
          const out=[];
          document.querySelectorAll('button,[role=button],a,span,div').forEach(n=>{
            const r=n.getBoundingClientRect(); if(r.width<=0||r.height<=0) return;
            const t=(n.innerText||'').trim();
            if(t && t.length<=8 && /确定|取消|删除|确认|知道了/.test(t)) out.push({t,x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),w:Math.round(r.width),h:Math.round(r.height)});
          });
          return out;
        }""")
        print("确认框候选按钮:")
        for bt in btns: print(f"  @({bt['x']},{bt['y']}) {bt['w']}x{bt['h']} {bt['t']!r}")

        # 取消：ESC
        page.keyboard.press("Escape")
        time.sleep(0.3)
        print("已ESC取消, 未删除")
        b.close()

if __name__=="__main__": main()