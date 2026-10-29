# -*- coding: utf-8 -*-
"""验证 PostMessage 投递点击是否被客户端接受。
默认点『取消』(安全，不删除)，看弹窗是否关闭。可指定 --confirm 点确定(会真删)。"""
import ctypes
import sys
import time

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0200, 0x0201, 0x0202
MK_LBUTTON = 0x0001

DLG = 591556
CONFIRM = (291, 146)
CANCEL = (369, 146)


def lparam(x, y):
    return (y << 16) | (x & 0xFFFF)


def is_visible(hwnd):
    return bool(user32.IsWindowVisible(hwnd))


def post_click(hwnd, x, y, wait=0.6):
    user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lparam(x, y))
    time.sleep(0.02)
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam(x, y))
    time.sleep(0.02)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam(x, y))
    time.sleep(wait)
    return is_visible(hwnd)


def send_click(hwnd, x, y, wait=0.6):
    user32.SendMessageW(hwnd, WM_MOUSEMOVE, 0, lparam(x, y))
    user32.SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam(x, y))
    user32.SendMessageW(hwnd, WM_LBUTTONUP, 0, lparam(x, y))
    time.sleep(wait)
    return is_visible(hwnd)


if not is_visible(DLG):
    print("弹窗不可见，无法测试")
    raise SystemExit

tgt = CONFIRM if "--confirm" in sys.argv else CANCEL
name = "确定" if "--confirm" in sys.argv else "取消"
print(f"目标: {name} @ {tgt}   (弹窗当前可见)")

t0 = time.perf_counter()
still = post_click(DLG, *tgt)
print(f"PostMessage 后 弹窗仍可见={still}  用时 {(time.perf_counter()-t0)*1000:.0f} ms")

if still:
    print("PostMessage 无效，试 SendMessage …")
    t0 = time.perf_counter()
    still2 = send_click(DLG, *tgt)
    print(f"SendMessage 后 弹窗仍可见={still2}  用时 {(time.perf_counter()-t0)*1000:.0f} ms")
    if not still2:
        print(">>> SendMessage 有效")
else:
    print(">>> PostMessage 有效")
