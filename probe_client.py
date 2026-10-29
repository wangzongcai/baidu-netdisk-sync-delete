# -*- coding: utf-8 -*-
"""探测百度网盘客户端窗口：枚举顶层窗口，找到 DuiHostWnd 主窗口，截图。只读。"""
import ctypes
from ctypes import wintypes
import os

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# 枚举顶层窗口
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetClassNameW = user32.GetClassNameW
IsWindowVisible = user32.IsWindowVisible
GetWindowRect = user32.GetWindowRect
GetWindowThreadProcessId = user32.GetWindowThreadProcessId

def get_text(hwnd):
    n = GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n+1)
    GetWindowTextW(hwnd, buf, n+1)
    return buf.value

def get_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    GetClassNameW(hwnd, buf, 256)
    return buf.value

results = []
def cb(hwnd, lParam):
    if not IsWindowVisible(hwnd):
        return True
    cls = get_class(hwnd)
    txt = get_text(hwnd)
    pid = wintypes.DWORD()
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    r = wintypes.RECT()
    GetWindowRect(hwnd, ctypes.byref(r))
    w = r.right - r.left
    h = r.bottom - r.top
    if w > 0 and h > 0:
        results.append((hwnd, pid.value, cls, txt, (r.left, r.top, w, h)))
    return True

cb_fn = EnumWindowsProc(cb)
EnumWindows(cb_fn, 0)

# 找出与百度网盘进程相关的窗口
import subprocess, json
# 获取百度网盘进程 PID 集合
try:
    out = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq BaiduNetdisk.exe", "/FO", "CSV", "/NH"], text=True, encoding="gbk")
    baidu_pids = set()
    for line in out.strip().splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 2 and parts[1].isdigit():
            baidu_pids.add(int(parts[1]))
except Exception as e:
    baidu_pids = set()
    print("tasklist err:", e)

print("百度网盘 PID:", baidu_pids)
print("=== 所有可见窗口 ===")
for hwnd, pid, cls, txt, rect in results:
    mark = "  <== BAIDU" if pid in baidu_pids else ""
    if txt or cls.startswith("DuiHost"):
        print(f"hwnd={hwnd} pid={pid} class={cls} rect={rect} text={txt!r}{mark}")

# 截图客户端主窗口
target = None
for hwnd, pid, cls, txt, rect in results:
    if pid in baidu_pids and rect[2] > 300 and rect[3] > 200:
        target = (hwnd, rect)
        break
if target:
    hwnd, (x, y, w, h) = target
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
        img.save(r"C:\Users\Administrator\baidu-dupe-clicker\_client.png")
        print(f"客户端截图已保存, 区域=({x},{y},{w},{h})")
    except Exception as e:
        print("截图失败:", e)
else:
    print("未找到百度网盘客户端主窗口")