# -*- coding: utf-8 -*-
"""客户端重复文件目录：模拟选中一个文件，看是否出现删除/右键菜单。只读探测，不删除。
注意：客户端是自绘界面，无法读控件文本，只能用截图观察 + 模拟点击/右键。"""
import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

H = 1380056  # 客户端主窗口
# 激活窗口
user32.ShowWindow(H, 9); user32.SetForegroundWindow(H); time.sleep(0.8)

# 取窗口客户区在屏幕上的坐标
class POINT(ctypes.Structure):
    _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
pt=POINT(0,0)
user32.ClientToScreen(H, ctypes.byref(pt))
print("客户区屏幕原点:", pt.x, pt.y)

r=wintypes.RECT(); user32.GetWindowRect(H, ctypes.byref(r))
print("窗口rect:", r.left,r.top,r.right-r.left,r.bottom-r.top)

# 第一个文件图标大约在截图坐标 (394, 290)，但截图是窗口内坐标(相对rect)，
# 而 rect.left=206, top=106。截图里第一个图标中心约 (394, 290) 是相对截图左上(即rect左上)。
# 屏幕坐标 = rect.left + 截图x, rect.top + 截图y
sx = r.left + 394
sy = r.top + 290
print("点击第一个文件图标 屏幕坐标:", sx, sy)

# 左键单击选中
user32.SetCursorPos(sx, sy)
time.sleep(0.3)
MOUSEEVENTF_LEFTDOWN=0x0002; MOUSEEVENTF_LEFTUP=0x0004
user32.mouse_event(MOUSEEVENTF_LEFTDOWN,0,0,0,0)
time.sleep(0.05)
user32.mouse_event(MOUSEEVENTF_LEFTUP,0,0,0,0)
time.sleep(1.0)

# 截图看选中效果
try:
    from PIL import ImageGrab
    ImageGrab.grab(bbox=(r.left,r.top,r.right,r.bottom)).save(r"C:\Users\Administrator\baidu-dupe-clicker\_client_selected.png")
    print("选中后截图 _client_selected.png")
except Exception as e: print("截图失败",e)

# 右键菜单
MOUSEEVENTF_RIGHTDOWN=0x0008; MOUSEEVENTF_RIGHTUP=0x0010
user32.mouse_event(MOUSEEVENTF_RIGHTDOWN,0,0,0,0)
time.sleep(0.05)
user32.mouse_event(MOUSEEVENTF_RIGHTUP,0,0,0,0)
time.sleep(1.2)
try:
    from PIL import ImageGrab
    ImageGrab.grab().save(r"C:\Users\Administrator\baidu-dupe-clicker\_client_rightmenu.png")
    print("右键后全屏截图 _client_rightmenu.png")
except Exception as e: print("截图失败",e)

# 按 ESC 关闭菜单，避免误触
user32.keybd_event(0x1B,0,0,0); user32.keybd_event(0x1B,0,2,0)
print("已按ESC关闭菜单(未做任何删除)")