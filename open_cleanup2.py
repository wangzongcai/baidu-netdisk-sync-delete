# -*- coding: utf-8 -*-
"""点击「垃圾文件清理」卡片本身（含标题文字的最近可点父节点），并检测新页面/新frame。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222

def main():
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = b.contexts[0]
        page=None
        for pg in ctx.pages:
            if "pan.baidu.com" in pg.url: page=pg; break
        if not page: print("no pan page"); return
        page.bring_to_front()
        pages_before = len(ctx.pages)

        frame=None
        for f in page.frames:
            if "aitools" in f.url: frame=f; break
        if not frame: print("no aitools frame"); return

        # 找标题为「垃圾文件清理」的元素，向上找到真正可点击的卡片容器
        box = frame.evaluate("""() => {
          // 精确匹配标题文本
          const all=[...document.querySelectorAll('div,span,p,em,a')];
          let label=null;
          for(const n of all){
            if((n.innerText||'').trim()==='垃圾文件清理' && n.getBoundingClientRect().width>0){ label=n; break; }
          }
          if(!label) return null;
          // 向上找含描述文本或体积较大的卡片容器
          let el=label;
          for(let i=0;i<6 && el;i++){
            const r=el.getBoundingClientRect();
            const txt=(el.innerText||'');
            if(r.height>=50 && /智能清理|释放/.test(txt)) break;
            el=el.parentElement;
          }
          if(!el) el=label;
          const r=el.getBoundingClientRect();
          return {x:r.x+r.width/2, y:r.y+r.height/2, w:r.width, h:r.height};
        }""")
        print("卡片位置:", box)
        if not box:
            print("未定位到卡片"); return
        # 用坐标点击卡片中心
        frame.click("body", position={"x": box["x"], "y": box["y"]}, timeout=4000)
        print("已点击卡片中心")
        page.wait_for_timeout(3500)

        print("新标签页数量变化:", pages_before, "->", len(ctx.pages))
        for i, pg in enumerate(ctx.pages):
            try: t=pg.title()
            except Exception: t=""
            print(f"  page[{i}]: {t[:30]!r} | {pg.url[:90]}")

        # 目标页(无论新旧)扫描清理界面
        for pg in ctx.pages:
            if "pan.baidu.com" not in pg.url: continue
            print("=== frames of", pg.url[:60])
            for f in pg.frames:
                if set(f.url): print("   f:", f.url[:100])
        # 截图
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_cleanup2.png")
        print("screenshot saved")
        b.close()

if __name__=="__main__": main()