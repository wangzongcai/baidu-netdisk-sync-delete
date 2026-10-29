# -*- coding: utf-8 -*-
"""BitBlt 抓完整物理桌面并缩放保存，用于定位弹窗真实位置。只读。"""
import ctypes
from ctypes import wintypes

from PIL import Image, ImageDraw

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.SetProcessDPIAware()

vx, vy = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
vw, vh = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)

hdc = user32.GetWindowDC(user32.GetDesktopWindow())
mem = gdi32.CreateCompatibleDC(hdc)
bmp = gdi32.CreateCompatibleBitmap(hdc, vw, vh)
gdi32.SelectObject(mem, bmp)
gdi32.BitBlt(mem, 0, 0, vw, vh, hdc, vx, vy, 0x00CC0020)


class BIH(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BI(ctypes.Structure):
    _fields_ = [("bmiHeader", BIH), ("bmiColors", wintypes.DWORD * 3)]


bi = BI()
bi.bmiHeader.biSize = ctypes.sizeof(BIH)
bi.bmiHeader.biWidth = vw
bi.bmiHeader.biHeight = -vh
bi.bmiHeader.biPlanes = 1
bi.bmiHeader.biBitCount = 32
buf = ctypes.create_string_buffer(vw * vh * 4)
gdi32.GetDIBits(mem, bmp, 0, vh, buf, ctypes.byref(bi), 0)
img = Image.frombuffer("RGBA", (vw, vh), buf, "raw", "BGRA", 0, 1).convert("RGB")

d = ImageDraw.Draw(img)
# 画出 GetWindowRect 报告的弹窗矩形
d.rectangle([2714, 447, 3242, 662], outline=(255, 0, 0), width=3)

small = img.resize((vw // 3, vh // 3), Image.LANCZOS)
small.save(r"C:\Users\Administrator\baidu-dupe-clicker\_phys_small.png")
print(f"物理桌面 {vw}x{vh}，已保存 _phys_small.png（红框=GetWindowRect 报告的弹窗位置）")

gdi32.DeleteObject(bmp)
gdi32.DeleteDC(mem)
user32.ReleaseDC(user32.GetDesktopWindow(), hdc)
