# -*- coding: utf-8 -*-
"""柚子双删：还原窗口、取真实 rect、高分辨率截图；查进程命令行。只读。"""
import ctypes
from ctypes import wintypes
import subprocess, os, time

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# 找所有 TkTopLevel '柚子双删'
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
GetWindowTextW = user32.GetWindowTextW; GetWindowTextLengthW = user32.GetWindowTextLengthW
GetClassNameW = user32.GetClassNameW; IsWindowVisible = user32.IsWindowVisible
GetWindowRect = user32.GetWindowRect

def txt(h):
    n=GetWindowTextLengthW(h); b=ctypes.create_unicode_buffer(n+1); GetWindowTextW(h,b,n+1); return b.value
def cls(h):
    b=ctypes.create_unicode_buffer(256); GetClassNameW(h,b,256); return b.value

found=[]
def cb(h,l):
    t=txt(h)
    if "柚子" in t:
        r=wintypes.RECT(); GetWindowRect(h,ctypes.byref(r))
        found.append((h,t,cls(h),(r.left,r.top,r.right-r.left,r.bottom-r.top),IsWindowVisible(h)))
    return True
EnumWindows(EnumWindowsProc(cb),0)
print("找到柚子窗口:", found)

for h,t,c,rect,vis in found:
    user32.ShowWindow(h,9)  # SW_RESTORE
    user32.SetForegroundWindow(h)
time.sleep(1)

# 重新取 rect
for h,t,c,rect,vis in found:
    r=wintypes.RECT(); GetWindowRect(h,ctypes.byref(r))
    x,y,w,hh=r.left,r.top,r.right-r.left,r.bottom-r.top
    print(f"窗口 hwnd={h} 新rect=({x},{y},{w},{hh})")
    try:
        from PIL import ImageGrab
        img=ImageGrab.grab(bbox=(x,y,x+w,y+hh))
        img.save(rf"C:\Users\Administrator\baidu-dupe-clicker\_youzi_{h}.png")
        print("  截图:", f"_youzi_{h}.png")
    except Exception as e: print("  截图失败:",e)

# 查进程，用 utf-8 宽松
try:
    import json
    p = subprocess.run(["powershell","-NoProfile","-Command",
        "Get-CimInstance Win32_Process | Where-Object {$_.Name -match 'python|pythonw'} | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine | ConvertTo-Json"],
        capture_output=True)
    text = p.stdout.decode('utf-8', errors='replace')
    print("=== python 进程 ===")
    print(text[:3000])
except Exception as e:
    print("查进程失败:",e)