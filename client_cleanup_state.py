# -*- coding: utf-8 -*-
"""把客户端恢复到干净状态：点击空白处取消选择，截图确认。不删除。"""
import ctypes
from ctypes import wintypes
import time
from PIL import ImageGrab

user32=ctypes.windll.user32
user32.SetProcessDPIAware()
H=1380056
user32.ShowWindow(H,9); user32.SetForegroundWindow(H); time.sleep(0.6)
r=wintypes.RECT(); user32.GetWindowRect(H,ctypes.byref(r))
# 点右侧空白区取消选择
sx=r.left+1200; sy=r.top+650
user32.SetCursorPos(sx,sy); time.sleep(0.2)
user32.mouse_event(0x0002,0,0,0,0); time.sleep(0.05); user32.mouse_event(0x0004,0,0,0,0)
time.sleep(0.6)
ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom)).save(r"C:\Users\Administrator\baidu-dupe-clicker\_client_clean.png")
print("已取消选择并截图 _client_clean.png, rect=",(r.left,r.top,r.right-r.left,r.bottom-r.top))