# -*- coding: utf-8 -*-
"""验证屏幕坐标是否与 GetWindowRect 一致：直接 BitBlt 该窗口矩形。只读。"""
import ctypes
import importlib.util
import sys
import time
from ctypes import wintypes

from PIL import Image

spec = importlib.util.spec_from_file_location(
    "sd2", r"C:\Users\Administrator\baidu-dupe-clicker\sync_delete_v2.py")
sd2 = importlib.util.module_from_spec(spec)
sys.argv = ["sd2"]
spec.loader.exec_module(sd2)

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.SetProcessDPIAware()


class BIH(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BI(ctypes.Structure):
    _fields_ = [("bmiHeader", BIH), ("bmiColors", wintypes.DWORD * 3)]


def grab(x, y, w, h):
    hdc = user32.GetDC(0)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    gdi32.BitBlt(mem, 0, 0, w, h, hdc, x, y, 0x00CC0020)
    bi = BI()
    bi.bmiHeader.biSize = ctypes.sizeof(BIH)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bi), 0)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    gdi32.DeleteObject(bmp); gdi32.DeleteDC(mem); user32.ReleaseDC(0, hdc)
    return img


mw = sd2.find_main_window()
hwnd, (L, T, R, B) = mw
print(f"窗口矩形 ({L},{T})-({R},{B})")
img = grab(L, T, R - L, B - T)
img.save(r"C:\Users\Administrator\baidu-dupe-clicker\_screengrab_rect.png")
print("已保存 _screengrab_rect.png")

# 速度测试：带偏移，只抓顶部区域
times = []
for _ in range(30):
    t0 = time.perf_counter_ns()
    im = grab(L, T, 700, 120)
    times.append((time.perf_counter_ns() - t0) / 1e6)
times.sort()
print(f"屏幕抓 700x120 耗时: 最小 {times[0]:.2f} 中位 {times[len(times)//2]:.2f} "
      f"P90 {times[int(len(times)*0.9)]:.2f} ms")
