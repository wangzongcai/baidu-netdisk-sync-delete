# -*- coding: utf-8 -*-
"""探测：在百度网盘页面找「垃圾文件清理 / 重复文件」入口。只读。"""
from playwright.sync_api import sync_playwright
HOST="127.0.0.1"; PORT=9222
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx = b.contexts[0]
    page = None
    for pg in ctx.pages:
        if "pan.baidu.com" in pg.url:
            page = pg; break
    if not page:
        print("no pan page"); b.close(); raise SystemExit
    # 找含关键词的可点击元素文本
    keywords = ["垃圾", "重复", "清理", "工具", "更多"]
    try:
        # 所有可能有文字的节点
        nodes = page.query_selector_all("div, span, a, li, button, span[title], a[title]")
        seen = set()
        for n in nodes:
            try:
                t = (n.inner_text() or "").strip()
                tt = n.get_attribute("title") or ""
                for kw in keywords:
                    if kw in t or kw in tt:
                        if t and t not in seen:
                            seen.add(t)
                            tag = n.evaluate("el => el.tagName")
                            print(f"[{tag}] text={t[:20]!r} title={tt[:30]!r}")
                        break
            except Exception:
                pass
    except Exception as e:
        print("scan err:", e)
    b.close()