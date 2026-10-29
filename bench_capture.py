# -*- coding: utf-8 -*-
"""测量 PrintWindow 抓主窗口的耗时，判断能否用于高频轮询。只读。"""
import importlib.util
import statistics
import sys
import time

spec = importlib.util.spec_from_file_location(
    "sd2", r"C:\Users\Administrator\baidu-dupe-clicker\sync_delete_v2.py")
sd2 = importlib.util.module_from_spec(spec)
sys.argv = ["sd2"]
spec.loader.exec_module(sd2)

mw = sd2.find_main_window()
print("主窗口:", mw)
hwnd = mw[0]

times = []
for _ in range(15):
    t0 = time.perf_counter_ns()
    im = sd2.capture(hwnd)
    times.append((time.perf_counter_ns() - t0) / 1e6)

print(f"PrintWindow 整窗(1125x813) 耗时: 最小 {min(times):.1f} 中位 {statistics.median(times):.1f} 最大 {max(times):.1f} ms")

# 只比较顶部计数区域(裁剪后约 640x95)的开销
im = sd2.capture(hwnd)
times2 = []
for _ in range(30):
    t0 = time.perf_counter_ns()
    im2 = sd2.capture(hwnd)
    h = hash(im2.crop((60, 45, 700, 140)).tobytes())
    times2.append((time.perf_counter_ns() - t0) / 1e6)
print(f"含裁剪+hash: 最小 {min(times2):.1f} 中位 {statistics.median(times2):.1f} 最大 {max(times2):.1f} ms")
