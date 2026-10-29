# -*- coding: utf-8 -*-
"""精确定位百度网盘客户端主窗口(最大可见DuiHostWnd)，恢复并截图。"""
import ctypes
from ctypes import wintypes
import time
from PIL import ImageGrab

user32=ctypes.windll.user32
user32.SetProcessDPIAware()
EnumWindows=user32.EnumWindows
EnumWindowsProc=ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
def txt(h):
    n=user32.GetWindowTextLengthW(h); b=ctypes.create_unicode_buffer(n+1); user32.GetWindowTextW(h,b,n+1); return b.value
def cls(h):
    b=ctypes.create_unicode_buffer(256); user32.GetClassNameW(h,b,256); return b.value

cands=[]
def cb(h,l):
    pid=wintypes.DWORD(); user32.GetWindowThreadProcessId(h,ctypes.byref(pid))
    if pid.value==10652:
        c=cls(h); t=txt(h)
        r=wintypes.RECT(); user32.GetWindowRect(h,ctypes.byref(r))
        w=r.right-r.left; hh=r.bottom-r.top
        if c=="DuiHostWnd" and w>300 and hh>300:
            cands.append((w*hh, h, c, t, (r.left,r.top,w,hh), user32.IsWindowVisible(h)))
    return True
EnumWindows(EnumWindowsProc(cb),0)
cands.sort(reverse=True)
print("候选主窗口(按面积降序):")
for a in cands: print("  ",a)

if cands:
    area,h,c,t,rect,vis=cands[0]
    print(f"选中最大窗口 hwnd={h} rect={rect} vis={vis}")
    user32.ShowWindow(h,9)
    # 移到可控位置: 左上角(50,50)，避免超出屏幕
    SWP_NOSIZE=0x0001
    user32.SetWindowPos(h,0,50,50,0,0,SWP_NOSIZE)
    user32.SetForegroundWindow(h)
    time.sleep(1.2)
    r=wintypes.RECT(); user32.GetWindowRect(h,ctypes.byref(r))
    print("移动后 rect:", r.left,r.top,r.right-r.left,r.bottom-r.top)
    ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom)).save(r"C:\Users\Administrator\baidu-dupe-clicker\_client_now.png")
    print("已截图 _client_now.png, hwnd=",h)