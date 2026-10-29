# -*- coding: utf-8 -*-
"""重置网页端：点『取消』关闭弹窗(不删除) → 点『重新扫描』刷新真实列表。
两者都不涉及删除。"""
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = next((pg for pg in ctx.pages if "/disk/clear" in pg.url), None)
    if not page:
        print("无清理页"); b.close(); raise SystemExit

    # 1) 关弹窗
    r = page.evaluate(r"""() => {
      const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
      if(!dlg) return 'no-dialog';
      let btn=null;
      dlg.querySelectorAll('button,span,div,a').forEach(n=>{
        const r=n.getBoundingClientRect();
        if(r.width<=0||r.height<=0) return;
        if((n.innerText||'').trim()==='取消'){ if(!btn||r.width*r.height<btn.area) btn={x:r.x+r.width/2,y:r.y+r.height/2,area:r.width*r.height}; }
      });
      if(!btn) return 'no-cancel';
      const el=document.elementFromPoint(btn.x,btn.y);
      if(el) el.click();
      return 'clicked-cancel';
    }""")
    print("关闭弹窗:", r)
    page.wait_for_timeout(600)

    # 2) 重新扫描
    r2 = page.evaluate(r"""() => {
      const nodes=[...document.querySelectorAll('button,span,div,a')];
      for(const n of nodes){
        const t=(n.innerText||'').trim();
        if(t === '重新扫描' || t.startsWith('重新扫')){
          const rc=n.getBoundingClientRect();
          if(rc.width>0 && rc.height>0){ n.click(); return 'clicked:'+t; }
        }
      }
      return 'not-found';
    }""")
    print("重新扫描:", r2)

    # 3) 等扫描结束（最多 120 秒）
    last = None
    same = 0
    for i in range(120):
        page.wait_for_timeout(1000)
        st = page.evaluate(r"""() => {
          const t=(document.body.innerText||'').replace(/\s+/g,' ');
          const m=t.match(/(\d+)个重复文件/);
          return {count:m?m[1]:'?', scanning:/扫描中|正在扫描|请稍候/.test(t)};
        }""")
        if st == last:
            same += 1
        else:
            same = 0
            last = st
            print(f"  [{i+1}s] 重复={st['count']} 扫描中={st['scanning']}")
        if not st["scanning"] and same >= 2:
            break

    page.screenshot(path=r"C:\Users\Administrator\baidu-dupe-clicker\_chk_web_reset.png")
    print("已保存 _chk_web_reset.png")
    b.close()
