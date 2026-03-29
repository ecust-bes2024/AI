#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True)
    from PIL import Image

def crop_bottom_whitespace(image_path, threshold=245):
    """裁剪图片底部的空白区域"""
    img = Image.open(image_path)
    pixels = img.load()
    width, height = img.size

    # 从底部向上扫描，找到第一行非空白内容
    for y in range(height - 1, -1, -1):
        # 检查这一行是否有非空白像素
        is_content = False
        for x in range(0, width, 10):  # 每隔10个像素采样，加快速度
            pixel = pixels[x, y]
            # 如果是 RGB，检查是否接近白色/浅灰色背景
            if isinstance(pixel, tuple) and len(pixel) >= 3:
                r, g, b = pixel[:3]
                # 降低阈值，检测浅灰色背景 (#f5f5f5 = 245,245,245)
                if r < threshold or g < threshold or b < threshold:
                    is_content = True
                    break

        if is_content:
            # 找到内容了，裁剪到这里（加一点 padding）
            crop_height = min(y + 40, height)
            cropped = img.crop((0, 0, width, crop_height))

            output_path = Path(image_path).with_stem(Path(image_path).stem + "-cropped")
            cropped.save(output_path)
            print(f"✅ Cropped from {height}px to {crop_height}px")
            print(f"📁 Saved to: {output_path}")
            return

    print("⚠️  No whitespace found to crop")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crop_whitespace.py <image_path>")
        sys.exit(1)

    crop_bottom_whitespace(sys.argv[1])
