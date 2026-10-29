# -*- coding: utf-8 -*-
"""无害探测：光标移到目标点，看该点下是什么窗口、前台是谁。不点击。"""
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()


def info(hwnd):
    if not hwnd:
        return "None"
    cls = ctypes.create_unicode_buffer(256); user32.GetClassNameW(hwnd, cls, 256)
    t = ctypes.create_unicode_buffer(256); user32.GetWindowTextW(hwnd, t, 256)
    r = wintypes.RECT(); user32.GetWindowRect(hwnd, ctypes.byref(r))
    return f"hwnd={hwnd} cls={cls.value!r} title={t.value!r} rect=({r.left},{r.top})-({r.right},{r.bottom})"


TARGET = (3005, 593)
print("前台:", info(user32.GetForegroundWindow()))

old = wintypes.POINT(); user32.GetCursorPos(ctypes.byref(old))
print(f"原光标: ({old.x},{old.y})")

ok = user32.SetCursorPos(*TARGET)
now = wintypes.POINT(); user32.GetCursorPos(ctypes.byref(now))
print(f"SetCursorPos({TARGET}) 返回={ok} 实际=({now.x},{now.y})")

class POINTX(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class RECTX(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


user32.WindowFromPoint.restype = wintypes.HWND
user32.WindowFromPoint.argtypes = [POINTX]
h = user32.WindowFromPoint(POINTX(TARGET[0], TARGET[1]))
print("WindowFromPoint:", info(h))

# 该点所属的顶层窗口
root = h
while root:
    parent = user32.GetParent(root)
    if not parent:
        break
    root = parent
print("顶层窗口:", info(root))

# 用 ChildWindowFromPointEx 逐层下钻，看命中的最小子窗口
cur = root
for _ in range(10):
    if not cur:
        break
    pt = wintypes.POINT(TARGET[0], TARGET[1])
    user32.ScreenToClient(cur, ctypes.byref(pt))
    child = user32.ChildWindowFromPointEx(cur, pt, 0x0001 | 0x0002)  # CWP_SKIPINVISIBLE|CWP_SKIPDISABLED
    if not child or child == cur:
        break
    cur = child
    print("  下钻 ->", info(cur))

user32.SetCursorPos(old.x, old.y)
print("光标已还原")
