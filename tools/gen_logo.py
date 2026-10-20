# -*- coding: utf-8 -*-
"""一次性生成图标：芯片外框 + 1.5 周期信号波
产出深色/浅色两套，覆盖页头 logo 与浏览器标签页图标
"""
import os
import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)

NAVY = (11, 74, 143)
CYAN = (0, 190, 196)
MINT = (61, 214, 192)

VB_W, VB_H = 790, 670
CHIP = (132, 118, 526, 434, 92, 38)
WAVE_X0, WAVE_X1 = 208, 582
WAVE_Y, WAVE_A, WAVE_CYC, WAVE_W = 335, 84, 1.5, 38

xs = np.linspace(WAVE_X0, WAVE_X1, 300)
t = (xs - WAVE_X0) / (WAVE_X1 - WAVE_X0)
ys = WAVE_Y - np.sin(t * np.pi * 2 * WAVE_CYC) * WAVE_A

PIN_X = (232, 378, 524)
PIN_Y = (242, 394)


def wave_path():
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in zip(xs, ys))


def write_svg(path, ink_a, ink_b):
    x, y, w, h, r, sw = CHIP
    pins = []
    for px in PIN_X:
        pins.append(f'<rect x="{px}" y="66" width="34" height="54" rx="14"/>')
        pins.append(f'<rect x="{px}" y="550" width="34" height="54" rx="14"/>')
    for py in PIN_Y:
        pins.append(f'<rect x="78" y="{py}" width="56" height="34" rx="14"/>')
        pins.append(f'<rect x="656" y="{py}" width="56" height="34" rx="14"/>')
    pin_svg = "\n    ".join(pins)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{VB_W}" height="{VB_H}" viewBox="0 0 {VB_W} {VB_H}" role="img" aria-label="信通智研台">
  <defs>
    <linearGradient id="sicInk" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{ink_a}"/><stop offset="1" stop-color="{ink_b}"/>
    </linearGradient>
    <linearGradient id="sicWave" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#00BEC4"/><stop offset="1" stop-color="#3DD6C0"/>
    </linearGradient>
  </defs>
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}"
        fill="none" stroke="url(#sicInk)" stroke-width="{sw}"/>
  <g fill="url(#sicInk)">
    {pin_svg}
  </g>
  <path d="{wave_path()}" fill="none" stroke="url(#sicWave)" stroke-width="{WAVE_W}"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
'''
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def band(px, py, width):
    dx, dy = np.gradient(px), np.gradient(py)
    n = np.hypot(dx, dy)
    nx, ny = -dy / n, dx / n
    hw = width / 2.0
    top = list(zip(px + nx * hw, py + ny * hw))
    bot = list(zip(px - nx * hw, py - ny * hw))[::-1]
    return top + bot


def write_png(path, size, ink):
    S = 4
    W = size * S
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = W / float(VB_W)
    OY = (W - VB_H * k) / 2.0

    def T(box):
        return [box[0] * k, box[1] * k + OY, box[2] * k, box[3] * k + OY]

    x, y, w, h, r, sw = CHIP
    d.rounded_rectangle(T([x, y, x + w, y + h]), radius=r * k,
                        outline=ink, width=int(sw * k))
    for px in PIN_X:
        d.rounded_rectangle(T([px, 66, px + 34, 120]), radius=14 * k, fill=ink)
        d.rounded_rectangle(T([px, 550, px + 34, 604]), radius=14 * k, fill=ink)
    for py in PIN_Y:
        d.rounded_rectangle(T([78, py, 134, py + 34]), radius=14 * k, fill=ink)
        d.rounded_rectangle(T([656, py, 712, py + 34]), radius=14 * k, fill=ink)

    mid = len(xs) // 2
    for sl, col in ((slice(0, mid + 1), CYAN), (slice(mid, None), MINT)):
        poly = band(xs[sl], ys[sl], WAVE_W)
        d.polygon([(px * k, py * k + OY) for px, py in poly], fill=col)
    for px, py, col in ((xs[0], ys[0], CYAN), (xs[-1], ys[-1], MINT)):
        rr = WAVE_W / 2.0
        d.ellipse(T([px - rr, py - rr, px + rr, py + rr]), fill=col)

    im.resize((size, size), Image.LANCZOS).save(path)


if __name__ == "__main__":
    # 浅色（亮色顶栏）
    write_svg(os.path.join(OUT, "logo.svg"), "#0B4A8F", "#0A2338")
    write_png(os.path.join(OUT, "logo-small.png"), 200, NAVY)
    write_png(os.path.join(OUT, "logo.png"), 512, NAVY)
    # 深色（暗色顶栏）
    write_svg(os.path.join(OUT, "logo-inverted.svg"), "#E8F2FA", "#BFD8EA")
    write_png(os.path.join(OUT, "logo-small-inverted.png"), 200, (232, 242, 250))
    write_png(os.path.join(OUT, "logo-inverted.png"), 512, (232, 242, 250))
    # 浏览器标签页图标
    write_png(os.path.join(OUT, "favicon-200.png"), 200, NAVY)
    write_png(os.path.join(OUT, "favicon-512.png"), 512, NAVY)
    print("图标生成完成")
