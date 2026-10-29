# -*- coding: utf-8 -*-
"""截取所有可见 DuiHostWnd 窗口（只读）。"""
import ctypes
from ctypes import wintypes
from PIL import ImageGrab

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

found = []
EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def cb(hwnd, lparam):
    if not user32.IsWindowVisible(hwnd):
        return True
    cls = ctypes.create_unicode_buffer(256); user32.GetClassNameW(hwnd, cls, 256)
    if cls.value != "DuiHostWnd":
        return True
    tbuf = ctypes.create_unicode_buffer(256); user32.GetWindowTextW(hwnd, tbuf, 256)
    r = wintypes.RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    if w > 100 and h > 60:
        found.append((hwnd, tbuf.value, r.left, r.top, w, h))
    return True
user32.EnumWindows(EnumProc(cb), 0)

for i, (hwnd, title, L, T, W, H) in enumerate(found):
    p = rf"C:\Users\Administrator\baidu-dupe-clicker\_win{i}_{hwnd}.png"
    ImageGrab.grab(bbox=(L, T, L + W, T + H)).save(p)
    print(f"[{i}] hwnd={hwnd} title={title!r} rect=({L},{T}) size={W}x{H} -> {p}")
