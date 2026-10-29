# -*- coding: utf-8 -*-
"""只展开「扫描重复文件」旁的下拉箭头，列出选项。绝不触发扫描、不删除。"""
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
        page.bring_to_front()
        page.wait_for_timeout(500)

        # 找到「扫描重复文件」文字节点，看它下方的下拉箭头（通常是同级 svg/i 或 ⬇）
        info = page.evaluate("""() => {
          const all=[...document.querySelectorAll('div,span,a,button,p')];
          let label=null;
          for(const n of all){
            if((n.innerText||'').trim().startsWith('扫描重复文件')){ label=n; break; }
          }
          if(!label) return {found:false};
          const r=label.getBoundingClientRect();
          // 找所在卡片容器
          let card=label;
          for(let i=0;i<5 && card;i++){
            if((card.innerText||'').includes('扫描重复文件') && card.getBoundingClientRect().height>80) break;
            card=card.parentElement;
          }
          return {found:true, x:r.x+r.width/2, y:r.y+r.height/2, w:r.width, h:r.height,
                  cardHtml:(card?card.outerHTML:'').slice(0,1200)};
        }""")
        print("label定位:", {k:info[k] for k in ('found','x','y','w','h') if k in info})
        # 打印卡片 HTML 结构，找下拉控件特征
        if info.get("cardHtml"):
            print("=== 卡片HTML片段 ===")
            print(info["cardHtml"][:1000])

        # 尝试点下拉箭头(若有)：查找文字旁的小箭头元素
        arrow = page.evaluate("""() => {
          const all=[...document.querySelectorAll('div,span,i,svg,a')];
          for(const n of all){
            const t=(n.innerText||'').trim();
            const cls=(n.className&&n.className.baseVal!==undefined)?n.className.baseVal:''+ (n.className||'');
            const r=n.getBoundingClientRect();
            if(r.width<=0) continue;
            // 文字为扫描重复文件且带箭头字符，或 class 含 arrow/dropdown
            if(t==='扫描重复文件' && /arrow|down|drop|caret|chevron/i.test(cls)){
              return {x:r.x+r.width/2,y:r.y+r.height/2,cls};
            }
          }
          return null;
        }""")
        print("下拉箭头定位:", arrow)
        page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_dropdown_before.png")
        print("已截图(未点击扫描)")
        b.close()

if __name__=="__main__": main()