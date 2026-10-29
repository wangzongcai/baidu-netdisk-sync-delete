# -*- coding: utf-8 -*-
"""读取弹窗的窗口/客户区矩形与 DPI。只读。"""
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

DLG = 591556
r = wintypes.RECT(); user32.GetWindowRect(DLG, ctypes.byref(r))
print(f"窗口矩形: ({r.left},{r.top})-({r.right},{r.bottom})  {r.right-r.left}x{r.bottom-r.top}")

c = wintypes.RECT(); user32.GetClientRect(DLG, ctypes.byref(c))
print(f"客户区: {c.right-c.left}x{c.bottom-c.top}")

# 客户区左上角在屏幕上的位置
pt = wintypes.POINT(0, 0)
user32.ClientToScreen(DLG, ctypes.byref(pt))
print(f"客户区原点(屏幕): ({pt.x},{pt.y})")

try:
    dpi = ctypes.windll.user32.GetDpiForWindow(DLG)
    print("GetDpiForWindow =", dpi, " 缩放 =", dpi / 96)
except Exception as e:
    print("GetDpiForWindow 不可用:", e)

# 该窗口的样式
ex = user32.GetWindowLongW(DLG, -20)   # GWL_EXSTYLE
st = user32.GetWindowLongW(DLG, -16)   # GWL_STYLE
print(f"EXSTYLE=0x{ex & 0xFFFFFFFF:08X}  WS_EX_LAYERED={bool(ex & 0x80000)}  "
      f"WS_EX_TRANSPARENT={bool(ex & 0x20)}  WS_EX_TOPMOST={bool(ex & 0x8)}")
print(f"STYLE=0x{st & 0xFFFFFFFF:08X}  WS_VISIBLE={bool(st & 0x10000000)}  "
      f"WS_CHILD={bool(st & 0x40000000)}  WS_POPUP={bool(st & 0x80000000)}")
