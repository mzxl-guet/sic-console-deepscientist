# -*- coding: utf-8 -*-
"""
生成「信通智研台」主视觉素材：
1. hero-signal.png   —— 桂林喀斯特山峦剪影 + 示波器波形 + 频谱柱（透明底）
2. fog-cool.png      —— 冷色水汽（用于叠加雾层）
3. seal-sic.png      —— 朱红印章「信通智研」
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)

W, H = 1830, 1000
rng = np.random.default_rng(20261017)

CYAN = (0, 190, 196)


def hex2rgb(c):
    return tuple(int(c[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


def make_peaks(xs, n, hmin, hmax, wmin, wmax, seed):
    """若干高斯峰叠加，得到喀斯特山峦起伏"""
    r = np.random.default_rng(seed)
    y = np.zeros_like(xs, dtype=float)
    for _ in range(n):
        cx = r.uniform(-0.05, 1.05) * W
        h = r.uniform(hmin, hmax)
        w = r.uniform(wmin, wmax)
        y = np.maximum(y, h * np.exp(-((xs - cx) ** 2) / (2 * w ** 2)))
    y += 12 * np.sin(xs / 260.0 + seed) + 6 * np.sin(xs / 97.0 + seed * 2)
    return np.clip(y, 0, None)


def blend_layer(canvas, curve_y, base_y, top_rgb, bot_rgb, alpha, grain=0.05):
    """标准 over 合成（straight alpha），水彩式上下渐隐"""
    ys = np.arange(H)[:, None]
    mask = ys >= curve_y[None, :]

    denom = np.maximum(base_y - curve_y, 1.0)[None, :]
    t = np.clip((ys - curve_y[None, :]) / denom, 0, 1)

    # 竖直方向的浓淡：山脊处淡入 -> 中段最浓 -> 山脚渐隐
    profile = np.sin(np.pi * np.power(t, 0.75)) ** 0.75
    sa = np.clip(alpha * profile * mask, 0, 1)
    from scipy.ndimage import gaussian_filter
    sa = gaussian_filter(sa, sigma=1.6)
    sa = np.clip(sa * (1.0 + rng.normal(0, grain, size=(H, W))), 0, 1)

    src = (np.array(top_rgb)[None, None, :] * (1 - t[..., None])
           + np.array(bot_rgb)[None, None, :] * t[..., None])

    da = canvas[..., 3:4]
    oa = sa[..., None] + da * (1 - sa[..., None])
    safe = np.maximum(oa, 1e-6)
    canvas[..., :3] = (src * sa[..., None] + canvas[..., :3] * da * (1 - sa[..., None])) / safe
    canvas[..., 3:4] = oa
    return canvas


def draw_glow(img, draw_fn, widths, alphas, color):
    for w, al in zip(widths, alphas):
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_fn(ImageDraw.Draw(layer), color + (int(255 * al),), w)
        layer = layer.filter(ImageFilter.GaussianBlur(max(w / 2.5, 0.4)))
        img.alpha_composite(layer)


def main():
    xs = np.arange(W, dtype=float)

    # ---------- 底：极淡工程网格 ----------
    canvas = np.zeros((H, W, 4), dtype=float)
    grid_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid_layer)
    for x in range(0, W, 61):
        gd.line([(x, 0), (x, H)], fill=(120, 170, 205, 26), width=1)
    for y in range(0, H, 61):
        gd.line([(0, y), (W, y)], fill=(120, 170, 205, 26), width=1)
    ga = np.array(grid_layer, dtype=float) / 255.0
    # 把网格作为最底层
    canvas[..., :3] = ga[..., :3]
    canvas[..., 3] = ga[..., 3]

    # ---------- 四层山峦 ----------
    layers = [
        dict(n=6, hmin=210, hmax=320, wmin=60, wmax=120, base=760, a=0.40,
             top=hex2rgb("#D5E4F0"), bot=hex2rgb("#A9C9DF"), seed=3),
        dict(n=7, hmin=270, hmax=410, wmin=54, wmax=108, base=820, a=0.50,
             top=hex2rgb("#A6C6DD"), bot=hex2rgb("#6E9DBF"), seed=11),
        dict(n=8, hmin=320, hmax=490, wmin=48, wmax=96, base=880, a=0.62,
             top=hex2rgb("#63A0C4"), bot=hex2rgb("#2E6790"), seed=29),
        dict(n=6, hmin=210, hmax=330, wmin=70, wmax=130, base=1000, a=0.80,
             top=hex2rgb("#3C7CA3"), bot=hex2rgb("#12405F"), seed=47),
    ]
    for L in layers:
        h = make_peaks(xs, L["n"], L["hmin"], L["hmax"], L["wmin"], L["wmax"], L["seed"])
        canvas = blend_layer(canvas, L["base"] - h, L["base"], L["top"], L["bot"], L["a"])

    img = Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8), "RGBA")

    # ---------- 山脊高光 ----------
    for L in layers[-2:]:
        h = make_peaks(xs, L["n"], L["hmin"], L["hmax"], L["wmin"], L["wmax"], L["seed"])
        curve = L["base"] - h
        pts = [(float(x), float(curve[int(x)])) for x in range(0, W, 4)]

        def fn(d, c, w, pts=pts):
            d.line(pts, fill=c, width=w, joint="curve")

        draw_glow(img, fn, [6, 2], [0.13, 0.42], (232, 245, 253))

    # ---------- 示波器波形 ----------
    t = np.linspace(0, 1, W)
    env = 0.5 + 0.5 * np.sin(2 * np.pi * t * 0.75 + 0.4) ** 2
    wave = (np.sin(2 * np.pi * t * 3.2) * 0.60
            + np.sin(2 * np.pi * t * 7.6 + 1.1) * 0.25
            + np.sin(2 * np.pi * t * 13.1 + 2.2) * 0.12)
    wy = 585 - wave * env * 92
    wpts = [(float(x), float(wy[i])) for i, x in enumerate(range(W))]

    def wfn(d, c, w):
        d.line(wpts, fill=c, width=w, joint="curve")

    draw_glow(img, wfn, [28, 11, 3], [0.05, 0.12, 0.9], CYAN)

    # 采样点
    dot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dot)
    for x in range(95, W, 158):
        yy = wy[x]
        dd.ellipse([x - 7, yy - 7, x + 7, yy + 7], outline=CYAN + (130,), width=2)
        dd.ellipse([x - 3.5, yy - 3.5, x + 3.5, yy + 3.5], fill=(255, 255, 255, 240))
    img.alpha_composite(dot.filter(ImageFilter.GaussianBlur(0.4)))

    # ---------- 底部频谱柱 ----------
    spec = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spec)
    bars = 76
    bw = W / bars
    for i in range(bars):
        r = np.random.default_rng(1000 + i)
        amp = (np.exp(-((i / bars - 0.5) ** 2) / 0.10) * 0.7 + 0.3) * r.uniform(45, 150)
        x0, x1 = i * bw + 3, (i + 1) * bw - 3
        top = H - amp
        sd.rectangle([x0, top, x1, H], fill=(0, 176, 196, 54))
        sd.rectangle([x0, top, x1, top + 2.5], fill=(0, 190, 196, 130))
    img.alpha_composite(spec.filter(ImageFilter.GaussianBlur(0.3)))

    # ---------- 天线辐射弧 ----------
    ax, ay = 1205, 285
    arcs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arcs)
    for r, a in [(42, 100), (74, 66), (108, 42), (142, 24)]:
        ad.arc([ax - r, ay - r, ax + r, ay + r], start=200, end=340,
               fill=CYAN + (a,), width=2)
    ad.ellipse([ax - 4.5, ay - 4.5, ax + 4.5, ay + 4.5], fill=(255, 255, 255, 235))
    img.alpha_composite(arcs.filter(ImageFilter.GaussianBlur(0.4)))

    # ---------- 边缘羽化：避免出现矩形硬边，融进纸面 ----------
    X = np.arange(W)[None, :].astype(float)
    Y = np.arange(H)[:, None].astype(float)
    fx = np.clip(np.minimum(X, W - 1 - X) / 120.0, 0, 1)
    fy = np.clip(np.minimum(Y, H - 1 - Y) / 90.0, 0, 1)
    fade = np.minimum(fx, fy) ** 0.7
    arr = np.array(img, dtype=float)
    arr[..., 3] = arr[..., 3] * fade
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")

    img.save(os.path.join(OUT, "hero-signal.png"))
    print("hero-signal.png", img.size)

    # ---------- 冷色水汽 ----------
    yy, xx = np.mgrid[0:H, 0:W]
    rgb = np.ones((H, W, 3))
    alpha = np.zeros((H, W))
    for cx, cy, r, a in [(420, 470, 640, 0.55), (1280, 400, 680, 0.50),
                         (900, 760, 800, 0.45), (1650, 700, 470, 0.35)]:
        d = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.45) ** 2) / r
        bump = np.clip(1 - d, 0, 1) ** 1.7
        rgb[..., 0] = np.minimum(rgb[..., 0], 1 - (1 - 0.84) * bump)
        rgb[..., 1] = np.minimum(rgb[..., 1], 1 - (1 - 0.92) * bump)
        rgb[..., 2] = np.minimum(rgb[..., 2], 1 - (1 - 0.99) * bump)
        alpha = np.maximum(alpha, bump * a)
    fog = np.dstack([rgb, alpha])
    Image.fromarray((np.clip(fog, 0, 1) * 255).astype(np.uint8), "RGBA").save(
        os.path.join(OUT, "fog-cool.png"))
    print("fog-cool.png")

    # ---------- 印章 ----------
    S = 4
    sw, sh = 240 * S, 180 * S
    seal = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seal)
    RED = (176, 58, 46, 235)
    sd.rectangle([14 * S, 14 * S, sw - 14 * S, sh - 14 * S], outline=RED, width=int(7 * S))
    sd.rectangle([27 * S, 27 * S, sw - 27 * S, sh - 27 * S], outline=RED, width=int(1.5 * S))
    font = ImageFont.truetype(r"C:\Windows\Fonts\STKAITI.TTF", int(52 * S))
    for i, ch in enumerate(["信", "通", "智", "研"]):
        col, row = i % 2, i // 2
        sd.text((sw * (0.30 + 0.42 * col), sh * (0.30 + 0.42 * row)),
                ch, font=font, fill=RED, anchor="mm")
    seal = seal.resize((240, 180), Image.LANCZOS)
    arr = np.array(seal)
    n = rng.normal(0, 1, arr.shape[:2])
    arr[..., 3] = np.clip(arr[..., 3].astype(float) * (1 - 0.22 * (n > 1.2)), 0, 255).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(os.path.join(OUT, "seal-sic.png"))
    print("seal-sic.png")


if __name__ == "__main__":
    main()
