# -*- coding: utf-8 -*-
"""验证网络事件捕获链路（只读、无副作用）：
在页面里发一个无害请求，确认 page.on('request') + page.wait_for_timeout 能正常收到事件。"""
import time
from playwright.sync_api import sync_playwright

HOST, PORT = "127.0.0.1", 9222
events = []

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(f"http://{HOST}:{PORT}")
    ctx = b.contexts[0]
    page = None
    for pg in ctx.pages:
        if "/disk/clear" in pg.url:
            page = pg; break
    if not page:
        print("未找到清理页"); b.close(); raise SystemExit

    page.on("request", lambda r: events.append(("req", time.perf_counter_ns(), r.method, r.url)))
    page.on("response", lambda r: events.append(("resp", time.perf_counter_ns(), r.status, r.url)))

    t0 = time.perf_counter_ns()
    # 无害请求：拉当前页面自身的 HTML（同域、只读）
    page.evaluate("""() => fetch('/disk/clear?from=verify', {cache:'no-store'}).then(r=>r.status).catch(e=>'err')""")
    # 关键：用 wait_for_timeout 驱动 Playwright 事件循环
    page.wait_for_timeout(800)
    t1 = time.perf_counter_ns()

    print(f"800ms 内捕获事件 {len(events)} 条，耗时 {(t1-t0)/1e6:.0f} ms")
    for kind, ts, a, u in events[:12]:
        print(f"  {kind:4s} +{(ts-t0)/1e6:8.2f}ms {a} {u[:110]}")

    b.close()

print("结论:", "捕获链路正常" if events else "仍是 0 条 —— 需要改用 CDP 会话方案")
