#!/usr/bin/env python3
from PIL import Image

# 打开图片
img = Image.open('claude-mem-poster.png')

# 获取图片尺寸
width, height = img.size
print(f"Original size: {width}x{height}")

# 从下往上扫描，找到最后一个非空白行
# 定义空白阈值（灰色背景 #f5f5f5 的 RGB 值约为 245,245,245）
def is_blank_row(img, y, threshold=240):
    """检查某一行是否为空白（接近 #f5f5f5）"""
    for x in range(width):
        pixel = img.getpixel((x, y))
        # 如果是 RGB 或 RGBA
        if isinstance(pixel, tuple):
            r, g, b = pixel[:3]
            # 如果任何像素不是接近空白色，则不是空白行
            if r < threshold or g < threshold or b < threshold:
                return False
    return True

# 从下往上找到第一个非空白行
last_content_y = height - 1
for y in range(height - 1, 0, -1):
    if not is_blank_row(img, y):
        last_content_y = y
        break

# 添加一些底部边距（40px）
crop_height = min(last_content_y + 40, height)

print(f"Content ends at: {last_content_y}px")
print(f"Cropping to: {width}x{crop_height}")

# 裁剪图片
cropped = img.crop((0, 0, width, crop_height))

# 保存
cropped.save('claude-mem-poster-cropped.png')
print(f"✅ Cropped poster saved: claude-mem-poster-cropped.png")
