# -*- coding: utf-8 -*-
"""预置网页端到确认框：选中第1个文件042(2)→点删除→等确认框→输出确定按钮位置。不点确定。"""
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
        if not page: print("no clear page"); return
        page.bring_to_front(); page.wait_for_timeout(500)
        print("URL:", page.url)

        # 先清空已选：点"取消选择"
        try:
            cs=page.locator("text=取消选择").first
            if cs.count() and cs.is_visible(): cs.click(timeout=2000); page.wait_for_timeout(400); print("已清空选择")
        except Exception: pass

        # 选中第1行的复选框。找复选框: input[type=checkbox] 或 .checkbox
        got=page.evaluate("""() => {
          // 返回第1个数据行复选框的页面坐标
          const rows=[...document.querySelectorAll('[class*=row],[class*=Row],tr,li')];
          const cbs=[...document.querySelectorAll('input[type=checkbox], [class*=checkbox], [class*=Checkbox]')];
          const vis=cbs.filter(n=>{const r=n.getBoundingClientRect();return r.width>0&&r.height>0&&r.width<40;});
          if(!vis.length) return null;
          const n=vis[0]; const r=n.getBoundingClientRect();
          return {x:r.x+r.width/2, y:r.y+r.height/2, count:vis.length};
        }""")
        print("复选框:", got)
        if not got: print("未找到复选框"); b.close(); return
        page.mouse.click(got["x"], got["y"])
        page.wait_for_timeout(600)

        # 截图看选中
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_web_armed_sel.png")

        # 点"删除"
        target=None
        loc=page.locator("text=删除")
        for i in range(loc.count()):
            el=loc.nth(i)
            try:
                if (el.inner_text() or "").strip()=="删除" and el.is_visible():
                    target=el; break
            except Exception: pass
        if not target: print("未找到删除按钮"); b.close(); return
        target.click(timeout=4000)
        # 等确认框
        ok=False
        for _ in range(400):
            ok=page.evaluate("""() => /删除后|释放|确定/.test(document.body.innerText||'') && [...document.querySelectorAll('button,span,div')].some(n=>{const r=n.getBoundingClientRect();return r.width>0&&r.height>0&&(n.innerText||'').trim()==='确定';})""")
            if ok: break
            time.sleep(0.005)
        print("确认框就绪:", ok)

        # 找"确定"按钮位置(精确: 最小的那个'确定'文本节点)
        btn=page.evaluate("""() => {
          let best=null;
          document.querySelectorAll('button,span,div,a').forEach(n=>{
            const r=n.getBoundingClientRect(); if(r.width<=0||r.height<=0) return;
            if((n.innerText||'').trim()==='确定'){
              if(!best || r.width*r.height < best.area) best={x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height,area:r.width*r.height};
            }
          });
          return best;
        }""")
        print("网页端确定按钮:", btn)
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_web_armed_dialog.png")
        print("已预置到确认框, 未点确定")
        b.close()

if __name__=="__main__": main()