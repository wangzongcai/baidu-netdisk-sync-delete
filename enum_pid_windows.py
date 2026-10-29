# -*- coding: utf-8 -*-
"""列出 PID 13520 的所有顶层窗口及大小。"""
import ctypes
from ctypes import wintypes
user32=ctypes.windll.user32
user32.SetProcessDPIAware()
EnumWindows=user32.EnumWindows
EnumWindowsProc=ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
GetWindowTextW=user32.GetWindowTextW; GetWindowTextLengthW=user32.GetWindowTextLengthW
GetClassNameW=user32.GetClassNameW; IsWindowVisible=user32.IsWindowVisible
GetWindowRect=user32.GetWindowRect; GetWindowThreadProcessId=user32.GetWindowThreadProcessId

def txt(h):
    n=GetWindowTextLengthW(h); b=ctypes.create_unicode_buffer(n+1); GetWindowTextW(h,b,n+1); return b.value
def cls(h):
    b=ctypes.create_unicode_buffer(256); GetClassNameW(h,b,256); return b.value

rows=[]
def cb(h,l):
    pid=wintypes.DWORD(); GetWindowThreadProcessId(h,ctypes.byref(pid))
    if pid.value==13520:
        r=wintypes.RECT(); GetWindowRect(h,ctypes.byref(r))
        rows.append((h,txt(h),cls(h),IsWindowVisible(h),(r.left,r.top,r.right-r.left,r.bottom-r.top)))
    return True
EnumWindows(EnumWindowsProc(cb),0)
print(f"PID 13520 共 {len(rows)} 个顶层窗口:")
for h,t,c,v,rect in rows:
    print(f"  hwnd={h} vis={v} class={c} rect={rect} text={t!r}")