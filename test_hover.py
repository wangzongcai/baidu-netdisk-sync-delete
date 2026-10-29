# -*- coding: utf-8 -*-
"""零风险验证：向确认弹窗投递 WM_MOUSEMOVE 到『确定』按钮，看画面是否出现悬停变化。
不点击、不删除。"""
import ctypes
import importlib.util
import sys
import time
from ctypes import wintypes

from PIL import ImageChops, ImageDraw

spec = importlib.util.spec_from_file_location(
    "sd2", r"C:\Users\Administrator\baidu-dupe-clicker\sync_delete_v2.py")
sd2 = importlib.util.module_from_spec(spec)
sys.argv = ["sd2"]
spec.loader.exec_module(sd2)

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

WM_MOUSEMOVE = 0x0200
DLG = 591556
CONFIRM = (291, 146)
CANCEL = (369, 146)


def lparam(x, y):
    return (y << 16) | (x & 0xFFFF)


def cap():
    return sd2.capture(DLG)


base = cap()
base.save(r"C:\Users\Administrator\baidu-dupe-clicker\_hover_base.png")

for tag, pt in (("确定", CONFIRM), ("取消", CANCEL)):
    user32.PostMessageW(DLG, WM_MOUSEMOVE, 0, lparam(*pt))
    time.sleep(0.25)
    im = cap()
    diff = ImageChops.difference(base, im)
    bbox = diff.getbbox()
    print(f"悬停 {tag}{pt} -> 变化区域 bbox={bbox}")

    # 找出差异最明显的点，判断是否落在按钮附近
    if bbox:
        gray = diff.convert("L")
        mx = max(gray.getdata())
        print(f"   最大差异={mx}")
    im.save(rf"C:\Users\Administrator\baidu-dupe-clicker\_hover_{tag}.png")

# 还原
user32.PostMessageW(DLG, WM_MOUSEMOVE, 0, lparam(5, 5))
print("已还原鼠标位置(投递)")
