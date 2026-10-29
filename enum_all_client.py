# -*- coding: utf-8 -*-
"""列出所有可见 DuiHostWnd 窗口（不论大小）并逐个 PrintWindow 截图。只读。"""
import ctypes
from ctypes import wintypes

from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.SetProcessDPIAware()


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


def capture(hwnd):
    r = wintypes.RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        return None
    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    ok = user32.PrintWindow(hwnd, mem, 0x2) or user32.PrintWindow(hwnd, mem, 0)
    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = w; bi.bmiHeader.biHeight = -h
    bi.bmiHeader.biPlanes = 1; bi.bmiHeader.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mem); user32.ReleaseDC(hwnd, hdc)
    return img if ok else None


EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
hits = []
def cb(hwnd, _):
    if not user32.IsWindowVisible(hwnd):
        return True
    cls = ctypes.create_unicode_buffer(256); user32.GetClassNameW(hwnd, cls, 256)
    if cls.value != "DuiHostWnd":
        return True
    t = ctypes.create_unicode_buffer(256); user32.GetWindowTextW(hwnd, t, 256)
    r = wintypes.RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
    hits.append((hwnd, t.value, r.left, r.top, r.right - r.left, r.bottom - r.top))
    return True
user32.EnumWindows(EnumProc(cb), 0)

print("所有可见 DuiHostWnd:")
for i, (hwnd, title, L, T, W, H) in enumerate(hits):
    print(f"  [{i}] hwnd={hwnd} title={title!r} rect=({L},{T}) {W}x{H}")
    if 100 <= W and 50 <= H:
        im = capture(hwnd)
        if im:
            p = rf"C:\Users\Administrator\baidu-dupe-clicker\_dlg{i}_{hwnd}.png"
            im.save(p)
            print(f"       -> {p}")
