# -*- coding: utf-8 -*-
"""只读：截客户端主窗口，用于人工核对当前重复文件数量。"""
import sys

sys.path.insert(0, r"C:\Users\Administrator\baidu-dupe-clicker")
import sync_delete_v2 as core

m = core.find_main_window()
if not m:
    print("没找到客户端主窗口")
    sys.exit(1)

im = core.capture(m[0])
if im is None:
    print("抓图失败")
    sys.exit(2)

out = r"C:\Users\Administrator\baidu-dupe-clicker\_now_client.png"
im.save(out)
print(f"已保存 {out}  尺寸={im.size}  hwnd={m[0]}")
