# -*- coding: utf-8 -*-
"""读取物理(DPI感知)显示器布局 + 客户端窗口是否完整在屏内。只读。"""
import ctypes
from ctypes import wintypes
from PIL import ImageGrab

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

vx = user32.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
vy = user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
vw = user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
vh = user32.GetSystemMetrics(79)   # SM_CYVIRTUALSCREEN
print(f"物理虚拟桌面: ({vx},{vy}) {vw}x{vh}  右边界={vx+vw} 下边界={vy+vh}")

monitors = []
MonitorEnum = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC,
                                 ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
def cb(hmon, hdc, lprect, lp):
    r = lprect.contents
    monitors.append((r.left, r.top, r.right, r.bottom))
    return True
user32.EnumDisplayMonitors(0, 0, MonitorEnum(cb), 0)
for i, m in enumerate(monitors):
    print(f"显示器{i}: ({m[0]},{m[1]}) - ({m[2]},{m[3]})  {m[2]-m[0]}x{m[3]-m[1]}")

# 客户端窗口
EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
wins = []
def cb2(hwnd, _):
    if not user32.IsWindowVisible(hwnd):
        return True
    cls = ctypes.create_unicode_buffer(256); user32.GetClassNameW(hwnd, cls, 256)
    if cls.value != "DuiHostWnd":
        return True
    r = wintypes.RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
    if r.right - r.left > 600 and r.bottom - r.top > 400:
        t = ctypes.create_unicode_buffer(256); user32.GetWindowTextW(hwnd, t, 256)
        wins.append((hwnd, t.value, r.left, r.top, r.right, r.bottom))
    return True
user32.EnumWindows(EnumProc(cb2), 0)

for hwnd, title, l, t, rr, bb in wins:
    ok = l >= vx and t >= vy and rr <= vx + vw and bb <= vy + vh
    print(f"客户端 hwnd={hwnd} {title!r} rect=({l},{t})-({rr},{bb}) 完整在屏内={ok}")
    btn = (l + 829, t + 483)
    inb = vx <= btn[0] < vx + vw and vy <= btn[1] < vy + vh
    print(f"  确定按钮@{btn} 在屏内={inb}")
    try:
        ImageGrab.grab(bbox=(l, t, rr, bb), all_screens=True).save(
            r"C:\Users\Administrator\baidu-dupe-clicker\_dry_client_all.png")
        print("  已保存 _dry_client_all.png (all_screens)")
    except Exception as e:
        print("  截图失败:", e)
