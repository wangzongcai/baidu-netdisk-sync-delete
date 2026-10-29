# -*- coding: utf-8 -*-
"""物理屏幕 BitBlt 截图，并在候选点上画标记，肉眼确认哪个才是『确定』。只读。"""
import ctypes
from ctypes import wintypes

from PIL import Image, ImageDraw

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.SetProcessDPIAware()

vx, vy = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
vw, vh = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
print(f"物理虚拟桌面 ({vx},{vy}) {vw}x{vh}")

hwnd = user32.GetDesktopWindow()
hdc = user32.GetWindowDC(hwnd)
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
print("物理截图尺寸:", img.size)

A = (3005, 593)          # 按窗口内偏移直接算
B = (3078, 630)          # 偏移 * 1.25
d = ImageDraw.Draw(img)
for (x, y), color, tag in ((A, (255, 0, 0), "A"), (B, (0, 200, 0), "B")):
    d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=color, width=2)
    d.line([x - 16, y, x + 16, y], fill=color, width=1)
    d.line([x, y - 16, x, y + 16], fill=color, width=1)

crop = img.crop((2600, 380, 3400, 760))
crop = crop.resize((crop.width * 2, crop.height * 2), Image.LANCZOS)
crop.save(r"C:\Users\Administrator\baidu-dupe-clicker\_marks.png")
print("已保存 _marks.png (红=A, 绿=B)")

gdi32.DeleteObject(bmp)
gdi32.DeleteDC(mem)
user32.ReleaseDC(hwnd, hdc)
