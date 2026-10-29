# -*- coding: utf-8 -*-
"""探明「柚子双删」工具：进程路径、命令行、父进程，并把窗口还原截图。只读。"""
import ctypes
from ctypes import wintypes
import subprocess, os

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# 目标窗口：TkTopLevel '柚子双删'
target_hwnd = 2493982

# 还原并前置
SW_RESTORE = 9
SW_SHOW = 5
user32.ShowWindow(target_hwnd, SW_RESTORE)
user32.SetForegroundWindow(target_hwnd)
import time; time.sleep(1.0)

r = wintypes.RECT()
user32.GetWindowRect(target_hwnd, ctypes.byref(r))
x,y,w,h = r.left, r.top, r.right-r.left, r.bottom-r.top
print(f"柚子双删窗口 rect=({x},{y},{w},{h})")

# 截图
try:
    from PIL import ImageGrab
    img = ImageGrab.grab(bbox=(x,y,x+w,y+h))
    img.save(r"C:\Users\Administrator\baidu-dupe-clicker\_youzi.png")
    print("已截图 _youzi.png")
except Exception as e:
    print("截图失败:", e)

# 用 WMIC/CIM 查进程 13520
try:
    ps = subprocess.check_output(["powershell","-NoProfile","-Command",
        "Get-CimInstance Win32_Process -Filter \"ProcessId=13520\" | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine | Format-List"],
        text=True, encoding="gbk", stderr=subprocess.STDOUT)
    print("=== 进程信息 ===")
    print(ps)
except Exception as e:
    print("查进程失败:", e)