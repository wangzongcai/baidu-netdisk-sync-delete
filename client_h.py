# -*- coding: utf-8 -*-
"""定位客户端可见的『垃圾文件清理』窗口 hwnd=918428，恢复、移到安全位置、截图。"""
import ctypes
from ctypes import wintypes
import time
from PIL import ImageGrab

H=918428
user32=ctypes.windll.user32
user32.SetProcessDPIAware()

user32.ShowWindow(H,9)
user32.SetForegroundWindow(H)
time.sleep(1.2)
r=wintypes.RECT(); user32.GetWindowRect(H,ctypes.byref(r))
print("rect:", r.left,r.top,r.right-r.left,r.bottom-r.top)
img=ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom))
img.save(r"C:\Users\Administrator\baidu-dupe-clicker\_client_now.png")
print("saved _client_now.png size=",img.size)