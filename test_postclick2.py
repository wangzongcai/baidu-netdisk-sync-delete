# -*- coding: utf-8 -*-
"""可指定坐标投递点击。用法:
  python test_postclick2.py X Y           # 投递到弹窗客户区坐标
投递后报告弹窗是否消失 + 主窗口是否刷新。"""
import ctypes
import sys
import time

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0200, 0x0201, 0x0202
MK_LBUTTON = 0x0001
DLG = 591556


def lparam(x, y):
    return (y << 16) | (x & 0xFFFF)


x, y = int(sys.argv[1]), int(sys.argv[2])
print(f"弹窗可见={bool(user32.IsWindowVisible(DLG))}  投递点=({x},{y})")

user32.PostMessageW(DLG, WM_MOUSEMOVE, 0, lparam(x, y))
time.sleep(0.02)
user32.PostMessageW(DLG, WM_LBUTTONDOWN, MK_LBUTTON, lparam(x, y))
time.sleep(0.02)
user32.PostMessageW(DLG, WM_LBUTTONUP, 0, lparam(x, y))
time.sleep(0.8)
print("PostMessage 后 弹窗可见=", bool(user32.IsWindowVisible(DLG)))
