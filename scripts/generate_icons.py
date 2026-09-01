"""Generates the 'Us' app icon set: a simple white heart mark on a warm
coral-to-plum diagonal gradient, at the sizes/purposes required by the PWA
manifest. Run once during setup - the output PNGs are committed as static
assets, this script doesn't need to run again unless the mark changes."""

import math
import os

from PIL import Image, ImageDraw

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static", "icons")
os.makedirs(OUT_DIR, exist_ok=True)

COLOR_START = (233, 99, 111)   # #E9636F
COLOR_END = (122, 33, 64)      # #7A2140


def gradient_square(size):
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            r = int(COLOR_START[0] + (COLOR_END[0] - COLOR_START[0]) * t)
            g = int(COLOR_START[1] + (COLOR_END[1] - COLOR_START[1]) * t)
            b = int(COLOR_START[2] + (COLOR_END[2] - COLOR_START[2]) * t)
            px[x, y] = (r, g, b)
    return img


def heart_path(cx, cy, scale):
    """Returns a list of (x, y) points approximating a heart, using the
    classic parametric heart curve, centered at (cx, cy)."""
    points = []
    steps = 200
    for i in range(steps + 1):
        t = math.pi * 2 * i / steps
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        points.append((cx + x * scale, cy + y * scale))
    return points


def make_icon(size, maskable=False, out_name=None):
    img = gradient_square(size)
    draw = ImageDraw.Draw(img)

    # Maskable icons need extra "safe zone" padding (~20%) since OSes crop
    # them into circles/squircles; regular icons can use more of the canvas.
    safe_fraction = 0.62 if maskable else 0.82
    scale = (size * safe_fraction) / 32.0  # heart curve spans roughly 32 units wide

    cx, cy = size / 2, size / 2 + size * 0.03
    pts = heart_path(cx, cy, scale)
    draw.polygon(pts, fill=(255, 255, 255, 255))

    path = os.path.join(OUT_DIR, out_name)
    img.save(path, "PNG")
    print("wrote", path)


def make_favicon(size=32):
    img = gradient_square(size)
    draw = ImageDraw.Draw(img)
    scale = (size * 0.8) / 32.0
    cx, cy = size / 2, size / 2 + size * 0.03
    pts = heart_path(cx, cy, scale)
    draw.polygon(pts, fill=(255, 255, 255, 255))
    img.save(os.path.join(OUT_DIR, "favicon-32.png"), "PNG")
    print("wrote favicon-32.png")


if __name__ == "__main__":
    make_icon(192, maskable=False, out_name="icon-192.png")
    make_icon(512, maskable=False, out_name="icon-512.png")
    make_icon(192, maskable=True, out_name="icon-192-maskable.png")
    make_icon(512, maskable=True, out_name="icon-512-maskable.png")
    make_icon(180, maskable=False, out_name="apple-touch-icon.png")
    make_favicon(32)
