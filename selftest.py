# -*- coding: utf-8 -*-
"""打包后自检：确认 playwright 驱动能在 exe 环境里启动。

只启动/关闭 playwright 驱动，不连浏览器、不点任何东西。
"""
import os
import sys

print("Python:", sys.version)
print("frozen:", getattr(sys, "frozen", False))
print("exe目录:", os.path.dirname(os.path.abspath(sys.executable)))

try:
    from playwright.sync_api import sync_playwright
    print("[1/3] 导入 playwright 成功")
except Exception as e:
    print("[1/3] 导入失败:", e)
    sys.exit(1)

try:
    p = sync_playwright().start()
    print("[2/3] playwright 驱动启动成功")
    try:
        print("      chromium 路径:", p.chromium.executable_path)
    except Exception as e:
        print("      (chromium 路径不可用，正常，我们连系统 Edge):", e)
    p.stop()
    print("[3/3] 驱动正常关闭")
except Exception as e:
    import traceback
    print("[2/3] 驱动启动失败:", e)
    traceback.print_exc()
    sys.exit(2)

try:
    import sync_delete_v2 as core
    print("[附加] 核心模块导入成功, 截图目录 =", core.IMG_DIR)
    print("       Edge 位置 =", core.find_edge_exe())
except Exception as e:
    print("[附加] 核心模块导入失败:", e)
    sys.exit(3)

print("\n全部通过")
