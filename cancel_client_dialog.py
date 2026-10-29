# -*- coding: utf-8 -*-
"""点客户端确认框的『取消』按钮，关闭弹窗。不删除。"""
import ctypes
from ctypes import wintypes
import time
from PIL import ImageGrab

H=918428
user32=ctypes.windll.user32
user32.SetProcessDPIAware()
r=wintypes.RECT(); user32.GetWindowRect(H,ctypes.byref(r))
L,T=r.left,r.top
# 取消按钮中心：截图坐标(755,484) => 屏幕
cssx=L+755; ssy=T+484
print("点取消 屏幕坐标:", cssx, ssy)
user32.SetCursorPos(cssx,ssy); time.sleep(0.2)
user32.mouse_event(0x0002,0,0,0,0); time.sleep(0.05); user32.mouse_event(0x0004,0,0,0,0)
time.sleep(0.8)
ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom)).save(r"C:\Users\Administrator\baidu-dupe-clicker\_client_canceled.png")
print("已点取消并截图 _client_canceled.png")