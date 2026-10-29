# -*- coding: utf-8 -*-
"""用 PrintWindow(PW_RENDERFULLCONTENT) 抓客户端窗口内容，不受遮挡/副屏影响。只读。"""
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
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)

    # PW_RENDERFULLCONTENT=0x2 对 DWM 合成窗口最可靠
    ok = user32.PrintWindow(hwnd, mem, 0x2)
    if not ok:
        ok = user32.PrintWindow(hwnd, mem, 0)

    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h        # 负数 = 自上而下
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    bi.bmiHeader.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0)

    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")

    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    return ok, img


for hwnd in (918428,):
    ok, im = capture(hwnd)
    print(f"hwnd={hwnd} PrintWindow成功={bool(ok)} 尺寸={im.size}")
    im.save(rf"C:\Users\Administrator\baidu-dupe-clicker\_pw_{hwnd}.png")
    # 左上角像素，判断是否全黑
    print("  左上像素:", im.getpixel((5, 5)), " 中心像素:", im.getpixel((im.width // 2, im.height // 2)))
