# -*- coding: utf-8 -*-
"""恢复百度网盘客户端窗口并截图，看它的重复文件清理界面。只读。"""
import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
SW_RESTORE=9

# 客户端进程 pid=10652 的 DuiHostWnd 窗口（之前枚举到）
# 重新枚举该 pid 的所有窗口
EnumWindows=user32.EnumWindows
EnumWindowsProc=ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def txt(h):
    n=user32.GetWindowTextLengthW(h); b=ctypes.create_unicode_buffer(n+1); user32.GetWindowTextW(h,b,n+1); return b.value
def cls(h):
    b=ctypes.create_unicode_buffer(256); user32.GetClassNameW(h,b,256); return b.value

wins=[]
def cb(h,l):
    pid=wintypes.DWORD(); user32.GetWindowThreadProcessId(h,ctypes.byref(pid))
    if pid.value==10652:
        r=wintypes.RECT(); user32.GetWindowRect(h,ctypes.byref(r))
        wins.append((h,txt(h),cls(h),user32.IsWindowVisible(h),(r.left,r.top,r.right-r.left,r.bottom-r.top)))
    return True
EnumWindows(EnumWindowsProc(cb),0)
print("百度客户端(10652)窗口:")
for w in wins: print("  ",w)

# 恢复 DuiHostWnd 且 text 含 '垃圾文件清理' 或 '百度网盘' 的窗口
for h,t,c,v,rect in wins:
    if c=="DuiHostWnd" and t and ("百度网盘" in t or "垃圾" in t):
        print(f"恢复窗口 hwnd={h} text={t}")
        user32.ShowWindow(h, SW_RESTORE)
        user32.SetForegroundWindow(h)
        time.sleep(1.2)
        r=wintypes.RECT(); user32.GetWindowRect(h,ctypes.byref(r))
        x,y,w,hh=r.left,r.top,r.right-r.left,r.bottom-r.top
        print(f"  新rect=({x},{y},{w},{hh})")
        if w>100 and hh>100:
            try:
                from PIL import ImageGrab
                ImageGrab.grab(bbox=(x,y,x+w,y+hh)).save(rf"C:\Users\Administrator\baidu-dupe-clicker\_client_{h}.png")
                print("  截图保存 _client_%d.png"%h)
            except Exception as e: print("  截图失败",e)
        break
else:
    print("未找到可恢复的客户端主窗口")