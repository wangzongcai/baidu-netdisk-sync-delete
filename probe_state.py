# -*- coding: utf-8 -*-
"""只读探测：客户端窗口/前台窗口/截图 + 网页端状态。不点击。"""
import ctypes
from ctypes import wintypes
from PIL import ImageGrab
from playwright.sync_api import sync_playwright

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# 枚举 DuiHostWnd 可见窗口
windows = []
EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def cb(hwnd, lparam):
    if not user32.IsWindowVisible(hwnd):
        return True
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    if buf.value == "DuiHostWnd":
        tbuf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, tbuf, 256)
        r = wintypes.RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
        w = r.right - r.left; h = r.bottom - r.top
        if w > 300 and h > 300:
            windows.append((hwnd, tbuf.value, r.left, r.top, w, h))
    return True
user32.EnumWindows(EnumProc(cb), 0)

print("DuiHostWnd 大窗口:")
for hwnd, title, L, T, W, H in windows:
    print(f"  hwnd={hwnd} title={title!r} rect=({L},{T}) size={W}x{H}")

fg = user32.GetForegroundWindow()
fbuf = ctypes.create_unicode_buffer(256); user32.GetWindowTextW(fg, fbuf, 256)
fcls = ctypes.create_unicode_buffer(256); user32.GetClassNameW(fg, fcls, 256)
print(f"前台窗口: hwnd={fg} cls={fcls.value!r} title={fbuf.value!r}")

pt = wintypes.POINT(); user32.GetCursorPos(ctypes.byref(pt))
print(f"当前光标: ({pt.x},{pt.y})")

if windows:
    hwnd, title, L, T, W, H = windows[0]
    ImageGrab.grab(bbox=(L, T, L + W, T + H)).save(
        r"C:\Users\Administrator\baidu-dupe-clicker\_state_client.png")
    print(f"客户端截图 _state_client.png (hwnd={hwnd})")

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    ctx = b.contexts[0]
    page = None
    for pg in ctx.pages:
        if "/disk/clear" in pg.url:
            page = pg; break
    if page:
        info = page.evaluate("""() => {
          const t=(document.body.innerText||'');
          const m=t.match(/(\\d+)个重复文件/);
          const dlg=document.querySelector('.deleteDialog,.pan-dialog-wrapper');
          return {count:m?m[1]:'?',
                  dialogVisible: dlg? dlg.getBoundingClientRect().width>0 : false};
        }""")
        print("网页端:", info)
    b.close()
