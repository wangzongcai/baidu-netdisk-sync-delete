# -*- coding: utf-8 -*-
"""客户端侦察第1步：恢复窗口→点选第一个文件→截图，看『删除』工具栏位置。不删除。"""
import ctypes
from ctypes import wintypes
import time
from PIL import ImageGrab

user32=ctypes.windll.user32
user32.SetProcessDPIAware()
H=1380056
user32.ShowWindow(H,9); user32.SetForegroundWindow(H); time.sleep(0.8)
r=wintypes.RECT(); user32.GetWindowRect(H,ctypes.byref(r))
L,T,W,Hh=r.left,r.top,r.right-r.left,r.bottom-r.top
print(f"窗口 rect=({L},{T},{W},{Hh})")

# 截图当前状态
ImageGrab.grab(bbox=(L,T,L+W,T+Hh)).save(r"C:\Users\Administrator\baidu-dupe-clicker\_client_before_select.png")
print("已截图 _client_before_select.png")

# 点第一个文件图标。之前截图看第一个图标在窗口内约(x=394,y=290)。
# 但窗口尺寸可能变，用相对比例: x≈28%宽, y≈33%高
fx = L + int(W*0.282)
fy = T + int(Hh*0.333)
print("点第一个文件图标:", fx, fy)
user32.SetCursorPos(fx,fy); time.sleep(0.25)
user32.mouse_event(0x0002,0,0,0,0); time.sleep(0.05); user32.mouse_event(0x0004,0,0,0,0)
time.sleep(1.0)
ImageGrab.grab(bbox=(L,T,L+W,T+Hh)).save(r"C:\Users\Administrator\baidu-dupe-clicker\_client_after_select.png")
print("已截图 _client_after_select.png (查看工具栏是否出现删除)")