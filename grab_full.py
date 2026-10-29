# -*- coding: utf-8 -*-
"""抓整个虚拟桌面(含副屏)，确认坐标系。只读。"""
import ctypes
from PIL import ImageGrab

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

vg = (user32.GetSystemMetrics(76), user32.GetSystemMetrics(77),
      user32.GetSystemMetrics(78), user32.GetSystemMetrics(79))
print("SM_ virtual screen:", vg)

im = ImageGrab.grab(all_screens=True)
print("grab(all_screens) 尺寸:", im.size)
im.save(r"C:\Users\Administrator\baidu-dupe-clicker\_full_desktop.png")

# 缩一张便于查看
small = im.resize((im.width // 3, im.height // 3), 1)
small.save(r"C:\Users\Administrator\baidu-dupe-clicker\_full_desktop_small.png")
print("已保存 _full_desktop.png / _full_desktop_small.png")
