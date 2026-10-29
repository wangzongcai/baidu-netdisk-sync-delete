# -*- coding: utf-8 -*-
"""在确认框截图里用深色文字像素聚类，定位『确定』『取消』按钮中心。只读。"""
import sys
from PIL import Image

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Administrator\baidu-dupe-clicker\_dlg2_591556.png"
im = Image.open(path).convert("RGB")
W, H = im.size
px = im.load()
print(f"图像 {W}x{H}")

# 先找白底内容区域（排除透明边形成的纯黑）
def is_text(p):
    r, g, b = p
    return 35 <= max(r, g, b) <= 145

white_x = [x for x in range(W) if sum(1 for y in range(H) if min(px[x, y]) > 200) > H * 0.3]
white_y = [y for y in range(H) if sum(1 for x in range(W) if min(px[x, y]) > 200) > W * 0.3]
wx1, wx2 = (min(white_x), max(white_x)) if white_x else (0, W - 1)
wy1, wy2 = (min(white_y), max(white_y)) if white_y else (0, H - 1)
print(f"白底内容区: x={wx1}..{wx2} y={wy1}..{wy2}")

# 只在下方 45% 找按钮文字
y0 = int(wy1 + (wy2 - wy1) * 0.66)
cols = []
for x in range(wx1, wx2 + 1):
    dark = 0
    for y in range(y0, wy2 + 1):
        if is_text(px[x, y]):
            dark += 1
    cols.append(dark)

# 按列有文字的连续区间聚类（允许小间隙）
groups = []
cur = None
gap = 0
for i, c in enumerate(cols):
    x = wx1 + i
    if c >= 2:
        if cur is None:
            cur = [x, x]
        else:
            cur[1] = x
        gap = 0
    else:
        if cur is not None:
            gap += 1
            if gap > 12:
                groups.append(tuple(cur)); cur = None
if cur:
    groups.append(tuple(cur))

# 每个簇求 y 范围和像素重心
for i, (x1, x2) in enumerate(groups):
    ys = [y for y in range(y0, wy2 + 1) for x in range(x1, x2 + 1)
          if is_text(px[x, y])]
    if not ys:
        continue
    y1, y2 = min(ys), max(ys)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    print(f"文字簇{i}: x={x1}..{x2} y={y1}..{y2} 宽度={x2-x1+1} 中心=({cx},{cy})")
    # 相对右下角偏移
    print(f"    右下角相对偏移 = (W-{cx}, {H}-{cy}) = ({W-cx},{H-cy})")
