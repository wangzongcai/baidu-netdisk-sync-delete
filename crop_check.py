# -*- coding: utf-8 -*-
"""裁剪网页端截图，放大前两行区域，确认勾选行文件名。"""
from PIL import Image
im=Image.open(r"C:\Users\Administrator\baidu-dupe-clicker\_web_checked.png")
# 截图里第1行约 y=290, 第2行 y=350. 裁剪 x:0-400, y:260-380
crop=im.crop((0,255,760,385))
crop=crop.resize((crop.width*2, crop.height*2), Image.LANCZOS)
crop.save(r"C:\Users\Administrator\baidu-dupe-clicker\_web_rows_zoom.png")
print("saved zoom", crop.size)