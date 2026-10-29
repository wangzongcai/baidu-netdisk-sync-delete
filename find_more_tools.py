# -*- coding: utf-8 -*-
"""点击左侧「更多工具」，遍历所有 frame 用 rect 可见性扫描清理类入口。不删除任何东西。"""
from playwright.sync_api import sync_playwright

HOST="127.0.0.1"; PORT=9222

JS_SCAN = """
() => {
  const out = new Set();
  const nodes = document.querySelectorAll('a,div,span,li,button,p,em,strong');
  for (const n of nodes) {
    const r = n.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;      // 用 rect 判断可见
    const t = (n.innerText || '').replace(/\\s+/g, ' ').trim();
    if (t && t.length >= 2 && t.length < 34) out.add(t);
  }
  return Array.from(out);
}
"""

def main():
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
        ctx = b.contexts[0]
        page = None
        for pg in ctx.pages:
            if "pan.baidu.com" in pg.url:
                page = pg; break
        if not page:
            print("no pan page"); return
        page.bring_to_front()
        page.wait_for_timeout(500)

        # 点左侧「更多工具」
        clicked = None
        for sel in ["text=更多工具", "div:has-text('更多工具')", "li:has-text('更多工具')"]:
            try:
                el = page.locator(sel).first
                if el.count():
                    box = el.bounding_box()
                    if box and box["width"] > 0:
                        el.click(timeout=3000)
                        clicked = sel
                        break
            except Exception:
                continue
        print("点击结果:", clicked)
        page.wait_for_timeout(2500)

        print("=== 各 frame 扫描 (含关键词) ===")
        for f in page.frames:
            try:
                items = f.evaluate(JS_SCAN)
            except Exception:
                continue
            hits = [t for t in items if any(k in t for k in ["垃圾","清理","重复","去重","整理","扫描","备份"])]
            if hits:
                print(f"[frame {f.url[:60]}]")
                for t in hits:
                    print("   -", t)
        # 主页面全量(短文本)便于看整体
        try:
            main_items = page.main_frame.evaluate(JS_SCAN)
            print("=== 主 frame 全部可见短文本 ===")
            for t in main_items:
                print("  -", t)
        except Exception as e:
            print("main scan err:", e)
        b.close()

if __name__ == "__main__":
    main()