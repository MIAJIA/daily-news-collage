"""撕纸拼贴风格的通用画图工具：纸纹、网点、白边抠图、手撕照片、渐变字、标签、爆炸贴、时间轴用的纸飞机等。
每天的渲染脚本先设置 collage_lib.SRC（原图文件夹），再调用这里的函数。"""
import math
import os
import random

from PIL import (Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter,
                 ImageFont, ImageOps)

W, H = 1920, 1080
RND = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
BLK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
HEL = "/System/Library/Fonts/Helvetica.ttc"
PURPLE = (88, 60, 165)
PINK = (196, 64, 150)
YELLOW = (255, 214, 60)
NV_GREEN = (118, 185, 0)
TERRA = (204, 110, 80)
RED = (214, 48, 64)
INK = (50, 36, 90)
SRC = None  # 由每天的渲染脚本设置


# ---------- 基础工具 ----------
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease_out(p):
    p = clamp01(p)
    return 1 - (1 - p) ** 3


def ease_in(p):
    p = clamp01(p)
    return p ** 3


def ease_io(p):
    p = clamp01(p)
    return 3 * p * p - 2 * p * p * p


def pop(t, t0, d=0.30):
    """弹出：从 0 放大到略超过 1 再回到 1。"""
    p = (t - t0) / d
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def bounce(p):
    p = clamp01(p)
    n1, d1 = 7.5625, 2.75
    if p < 1 / d1:
        return n1 * p * p
    if p < 2 / d1:
        p -= 1.5 / d1
        return n1 * p * p + 0.75
    if p < 2.5 / d1:
        p -= 2.25 / d1
        return n1 * p * p + 0.9375
    p -= 2.625 / d1
    return n1 * p * p + 0.984375


def rough(mask, amp=26, cell=24, blur=3):
    """把蒙版的边缘变成手撕、手剪那样不规则的边。"""
    w, h = mask.size
    n = Image.effect_noise((max(2, w // cell), max(2, h // cell)), amp).resize((w, h), Image.BICUBIC)
    d = mask.filter(ImageFilter.GaussianBlur(blur))
    v = ImageChops.add(d, n, 1, -128)
    return v.point(lambda x: 255 if x > 127 else 0).filter(ImageFilter.GaussianBlur(0.9))


def paper(color, size=(W, H)):
    base = Image.new("RGB", size, color)
    fine = Image.effect_noise(size, 20).convert("RGB")
    blot = Image.effect_noise((size[0] // 48 + 2, size[1] // 48 + 2), 6).resize(size, Image.BICUBIC).convert("RGB")
    return ImageChops.overlay(ImageChops.overlay(base, fine), blot)


def halftone(color, y0, y1, cell=30, rmax=11, grow_down=True, alpha=120, x0=0, x1=W):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    row = 0
    y = y0
    while y < y1:
        f = (y - y0) / max(1, (y1 - y0))
        if not grow_down:
            f = 1 - f
        r = rmax * f
        off = cell / 2 if row % 2 else 0
        x = x0 - cell + off
        while x < x1 + cell:
            if r > 0.8:
                d.ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))
            x += cell
        y += cell * 0.86
        row += 1
    return layer


def with_edge(img, edge_mask, shadow=True):
    """给一块东西垫上白色纸边和淡淡的投影。"""
    size = img.size
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    if shadow:
        sh = ImageChops.offset(edge_mask, 9, 11).filter(ImageFilter.GaussianBlur(8)).point(lambda x: int(x * 0.38))
        s = Image.new("RGBA", size, (25, 15, 55, 0))
        s.putalpha(sh)
        out = Image.alpha_composite(out, s)
    white = Image.new("RGBA", size, (255, 255, 255, 0))
    white.putalpha(edge_mask)
    out = Image.alpha_composite(out, white)
    return Image.alpha_composite(out, img)


def cutout_sprite(im, height, stroke=15, gray=False, color=1.15, contrast=1.08):
    """抠好的主体 → 带白色粗边的拼贴小人。"""
    im = im.convert("RGBA")
    bbox = im.split()[3].getbbox()
    if bbox:
        im = im.crop(bbox)
    w = max(1, int(im.width * height / im.height))
    im = im.resize((w, height), Image.LANCZOS)
    a = im.split()[3]
    rgb = im.convert("RGB")
    if gray:
        rgb = ImageOps.grayscale(rgb).convert("RGB")
        rgb = ImageEnhance.Contrast(rgb).enhance(1.1)
    else:
        rgb = ImageEnhance.Color(rgb).enhance(color)
        rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    im = rgb.convert("RGBA")
    im.putalpha(a)
    pad = stroke + 30
    size = (w + 2 * pad, height + 2 * pad)
    src = Image.new("RGBA", size, (0, 0, 0, 0))
    src.paste(im, (pad, pad))
    hard = src.split()[3].point(lambda x: 255 if x > 90 else 0)
    dil = hard.filter(ImageFilter.GaussianBlur(stroke * 0.55)).point(lambda x: 255 if x > 14 else 0)
    edge = rough(dil, amp=22, cell=30, blur=3)
    return with_edge(src, edge)


def torn_photo(im, w, h, border=16, centering=(0.5, 0.5)):
    """方形照片 → 四边手撕、带白边的纸片。"""
    im = ImageOps.fit(im.convert("RGB"), (w, h), Image.LANCZOS, centering=centering)
    im = ImageEnhance.Color(im).enhance(1.15)
    pad = border + 30
    size = (w + 2 * pad, h + 2 * pad)
    inner = Image.new("L", size, 0)
    ImageDraw.Draw(inner).rectangle([pad, pad, pad + w, pad + h], fill=255)
    inner = rough(inner, amp=16, cell=18, blur=2)
    outer = Image.new("L", size, 0)
    ImageDraw.Draw(outer).rectangle([pad - border, pad - border, pad + w + border, pad + h + border], fill=255)
    outer = rough(outer, amp=34, cell=16, blur=3)
    src = Image.new("RGBA", size, (0, 0, 0, 0))
    ph = Image.new("RGBA", size, (0, 0, 0, 0))
    ph.paste(im, (pad, pad))
    src.paste(ph, (0, 0), inner)
    return with_edge(src, outer)


def torn_rect(w, h, color, border=10):
    return torn_photo(paper(color, (w, h)), w, h, border=border)


def gradient_text(text, size, c1, c2, stroke=12, font=RND):
    f = ImageFont.truetype(font, size)
    bb = f.getbbox(text, stroke_width=stroke)
    m = 34
    w, h = bb[2] - bb[0] + 2 * m, bb[3] - bb[1] + 2 * m
    org = (m - bb[0], m - bb[1])
    under = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(under).text(org, text, font=f, fill=(255, 255, 255, 255), stroke_width=stroke, stroke_fill=(255, 255, 255, 255))
    edge = under.split()[3]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text(org, text, font=f, fill=255)
    g = Image.linear_gradient("L").rotate(90).resize((w, h))
    grad = ImageOps.colorize(g, c2, c1).convert("RGBA")
    face = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    face.paste(grad, (0, 0), mask)
    return with_edge(face, edge)


def tag(text, size=34, fg=PURPLE, bg=(255, 255, 255), outline=(200, 186, 232), font=RND, padx=None):
    f = ImageFont.truetype(font, size)
    bb = f.getbbox(text)
    padx = padx if padx is not None else int(size * 0.55)
    pady = int(size * 0.32)
    m = 22
    w, h = bb[2] - bb[0] + 2 * padx + 2 * m, bb[3] - bb[1] + 2 * pady + 2 * m
    face = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(face)
    box = [m, m, w - m, h - m]
    d.rounded_rectangle(box, radius=(h - 2 * m) // 2, fill=bg + (255,), outline=outline + (255,), width=max(3, size // 10))
    d.text((m + padx - bb[0], m + pady - bb[1]), text, font=f, fill=fg + (255,))
    edge = Image.new("L", (w, h), 0)
    ImageDraw.Draw(edge).rounded_rectangle([m - 5, m - 5, w - m + 5, h - m + 5], radius=(h - 2 * m) // 2 + 5, fill=255)
    return with_edge(face, rough(edge, amp=10, cell=14, blur=1.5))


def burst(text, r, fill=YELLOW, fg=PURPLE, spikes=16, size=None):
    m = 40
    S = 2 * r + 2 * m
    c = S / 2
    pts = []
    for i in range(spikes * 2):
        ang = math.pi * i / spikes
        rr = r if i % 2 == 0 else r * 0.74
        pts.append((c + rr * math.cos(ang), c + rr * math.sin(ang)))
    face = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(face)
    d.polygon(pts, fill=fill + (255,))
    f = ImageFont.truetype(BLK, size or int(r * 0.52))
    bb = f.getbbox(text)
    d.text((c - (bb[2] + bb[0]) / 2, c - (bb[3] + bb[1]) / 2), text, font=f, fill=fg + (255,))
    hard = face.split()[3]
    dil = hard.filter(ImageFilter.GaussianBlur(7)).point(lambda x: 255 if x > 14 else 0)
    return with_edge(face, rough(dil, amp=12, cell=22, blur=2))


def bubble(text, size=92):
    f = ImageFont.truetype(BLK, size)
    bb = f.getbbox(text)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    m = 36
    w, h = tw + 150 + 2 * m, th + 130 + 2 * m
    face = Image.new("RGBA", (w, h + 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(face)
    d.polygon([(w * 0.60, h - m - 30), (w * 0.78, h + 40), (w * 0.74, h - m - 40)], fill=(255, 255, 255, 255), outline=(40, 30, 70, 255))
    d.ellipse([m, m, w - m, h - m], fill=(255, 255, 255, 255), outline=(40, 30, 70, 255), width=7)
    d.polygon([(w * 0.615, h - m - 34), (w * 0.775, h + 30), (w * 0.735, h - m - 44)], fill=(255, 255, 255, 255))
    g = Image.linear_gradient("L").resize((tw + 20, th + 20))
    grad = ImageOps.colorize(g, (255, 196, 40), (240, 80, 60)).convert("RGBA")
    tm = Image.new("L", (tw + 20, th + 20), 0)
    ImageDraw.Draw(tm).text((10 - bb[0], 10 - bb[1]), text, font=f, fill=255)
    face.paste(grad, (int((w - tw) / 2) - 10, int((h - th) / 2) - 10), tm)
    hard = face.split()[3]
    dil = hard.filter(ImageFilter.GaussianBlur(6)).point(lambda x: 255 if x > 14 else 0)
    return with_edge(face, rough(dil, amp=10, cell=22, blur=2))


def crown(w=210):
    h = int(w * 0.62)
    m = 30
    face = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    d = ImageDraw.Draw(face)
    pts = [(0, h), (0, h * 0.28), (w * 0.22, h * 0.62), (w * 0.36, h * 0.05), (w * 0.5, h * 0.55),
           (w * 0.64, h * 0.05), (w * 0.78, h * 0.62), (w, h * 0.28), (w, h)]
    d.polygon([(m + x, m + y) for x, y in pts], fill=(250, 200, 40, 255))
    d.rectangle([m, m + h * 0.80, m + w, m + h], fill=(232, 160, 30, 255))
    for i, col in enumerate([(220, 50, 70), (60, 110, 220), (220, 50, 70)]):
        cx = m + w * (0.25 + 0.25 * i)
        d.ellipse([cx - 11, m + h * 0.90 - 11, cx + 11, m + h * 0.90 + 11], fill=col + (255,))
    grain = Image.effect_noise(face.size, 18).convert("RGB")
    rgb = ImageChops.overlay(face.convert("RGB"), grain).convert("RGBA")
    rgb.putalpha(face.split()[3])
    hard = rgb.split()[3]
    dil = hard.filter(ImageFilter.GaussianBlur(6)).point(lambda x: 255 if x > 14 else 0)
    return with_edge(rgb, rough(dil, amp=10, cell=20, blur=2))


def paper_plane():
    """用报纸折的纸飞机，头朝右。"""
    m = 26
    w, h = 170, 104
    face = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    d = ImageDraw.Draw(face)
    P = lambda x, y: (m + x, m + y)
    top = [P(0, 6), P(170, 46), P(52, 54)]
    low = [P(52, 54), P(170, 46), P(26, 100)]
    keel = [P(52, 54), P(170, 46), P(70, 84)]
    d.polygon(low, fill=(226, 224, 232, 255))
    d.polygon(keel, fill=(186, 184, 200, 255))
    d.polygon(top, fill=(250, 250, 250, 255))
    d.polygon([P(0, 6), P(60, 20), P(40, 30), P(8, 14)], fill=(214, 48, 64, 255))  # 报头的红条
    for i in range(5):  # 报纸上的字行
        y = 26 + i * 5
        d.line([P(30 + i * 9, y + i * 1.5), P(120 + i * 6, y + 12 + i * 3.2)], fill=(120, 120, 140, 255), width=2)
    for i in range(4):
        d.line([P(48 + i * 4, 62 + i * 8), P(120 - i * 12, 58 + i * 7)], fill=(150, 150, 165, 255), width=2)
    hard = face.split()[3]
    dil = hard.filter(ImageFilter.GaussianBlur(4)).point(lambda x: 255 if x > 20 else 0)
    return with_edge(face, rough(dil, amp=8, cell=16, blur=1.5))


def cloud(w, h, seed):
    rnd = random.Random(seed)
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    base = h * 0.78
    d.rounded_rectangle([w * 0.08, base - h * 0.22, w * 0.92, base], radius=int(h * 0.11), fill=255)
    for i in range(8):
        cx = w * (0.16 + 0.68 * i / 7) + rnd.uniform(-w * 0.03, w * 0.03)
        k = 1 - abs(i - 3.5) / 5.5
        r = h * (0.16 + 0.26 * k) * rnd.uniform(0.85, 1.15)
        cy = base - h * 0.16 - r * 0.55
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    m = rough(m, amp=14, cell=26, blur=4)
    shade = Image.linear_gradient("L").resize((w, h))
    body = ImageOps.colorize(shade, (255, 255, 255), (226, 222, 240)).convert("RGB")
    body = ImageChops.overlay(body, Image.effect_noise((w, h), 16).convert("RGB")).convert("RGBA")
    body.putalpha(m)
    return body


def skyline_sprite(width=1340):
    """从黄昏的下曼哈顿全景里，沿着楼顶把天空剪掉。"""
    im = Image.open(os.path.join(SRC, "skyline.jpg")).convert("RGB")
    iw, ih = im.size
    crop = im.crop((0, int(ih * 0.36), int(iw * 0.72), int(ih * 0.872)))
    h = int(crop.height * width / crop.width)
    crop = crop.resize((width, h), Image.LANCZOS)
    edges = ImageOps.grayscale(crop).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.5))
    px = edges.load()
    mask = Image.new("L", (width, h), 0)
    md = ImageDraw.Draw(mask)
    tops = []
    for x in range(width):
        top = h - 14
        for y in range(6, h - 14) if 8 < x < width - 8 else ():
            if px[x, y] > 16:
                top = y
                break
        tops.append(top)
    sm = []
    for x in range(width):  # 用相邻几列的最小值，避免细尖顶被漏掉后出现缺口
        lo = max(0, x - 2)
        sm.append(min(tops[lo:x + 3]))
    for x in range(width):
        md.line([(x, max(0, sm[x] - 3)), (x, h)], fill=255)
    crop = ImageEnhance.Brightness(crop).enhance(1.35)
    crop = ImageEnhance.Color(crop).enhance(1.25)
    rgba = crop.convert("RGBA")
    rgba.putalpha(mask)
    pad = 44
    src = Image.new("RGBA", (width + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    src.paste(rgba, (pad, pad))
    hard = src.split()[3]
    dil = hard.filter(ImageFilter.GaussianBlur(5)).point(lambda x: 255 if x > 14 else 0)
    return with_edge(src, rough(dil, amp=8, cell=22, blur=1.5), shadow=False)


def water_strip():
    im = Image.open(os.path.join(SRC, "skyline.jpg")).convert("RGB")
    iw, ih = im.size
    crop = im.crop((0, int(ih * 0.885), iw, ih))
    crop = ImageEnhance.Brightness(crop).enhance(1.7)
    crop = ImageEnhance.Color(crop).enhance(1.2)
    return torn_photo(crop, W + 60, 250, border=12)


# ---------- 画面摆放 ----------
CACHE = {}


def place(canvas, key, img, cx, cy, scale=1.0, rot=0.0, t=None):
    if scale <= 0.03:
        return
    if t is not None:  # 每秒 8 次的轻微抖动，像手工逐格拍的纸片
        r = random.Random("%s-%d" % (key, int(t * 8)))
        cx += r.uniform(-1.6, 1.6)
        cy += r.uniform(-1.6, 1.6)
        rot += r.uniform(-0.5, 0.5)
    k = (key, round(scale, 2), round(rot * 2) / 2)
    im = CACHE.get(k)
    if im is None:
        im = img
        if abs(k[1] - 1) > 0.005:
            im = im.resize((max(1, int(im.width * k[1])), max(1, int(im.height * k[1]))), Image.LANCZOS)
        if abs(k[2]) > 0.05:
            im = im.rotate(k[2], resample=Image.BICUBIC, expand=True)
        if len(CACHE) > 500:
            CACHE.clear()
        CACHE[k] = im
    canvas.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


# ---------- 现成的纸片：箭头、铃铛、日历、眼睛、手机、时钟、创可贴、月亮、羊、新闻卡片等 ----------
def comp(c, sp, x, y):
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
    layer.paste(sp, (int(x), int(y)))
    return Image.alpha_composite(c, layer)


def shape(w, h, fn, stroke=7, m=30, shadow=True):
    face = Image.new("RGBA", (w + 2 * m, h + 2 * m), (0, 0, 0, 0))
    fn(ImageDraw.Draw(face), m)
    g = Image.effect_noise(face.size, 14).convert("RGB")
    rgb = ImageChops.overlay(face.convert("RGB"), g).convert("RGBA")
    rgb.putalpha(face.split()[3])
    hard = rgb.split()[3]
    dil = hard.filter(ImageFilter.GaussianBlur(stroke * 0.6)).point(lambda x: 255 if x > 16 else 0)
    return with_edge(rgb, rough(dil, amp=9, cell=20, blur=2), shadow=shadow)


def ctext(d, cx, cy, text, font, size, fill):
    f = ImageFont.truetype(font, size)
    bb = f.getbbox(text)
    d.text((cx - (bb[0] + bb[2]) / 2, cy - (bb[1] + bb[3]) / 2), text, font=f, fill=fill)


def arrow(up, color, w=240, h=400):
    def fn(d, m):
        pts = [(w / 2, 0), (w, h * 0.42), (w * 0.68, h * 0.42), (w * 0.68, h), (w * 0.32, h), (w * 0.32, h * 0.42), (0, h * 0.42)]
        if not up:
            pts = [(x, h - y) for x, y in pts]
        d.polygon([(m + x, m + y) for x, y in pts], fill=color + (255,))
    return shape(w, h, fn)


def bell(s=220):
    def fn(d, m):
        d.ellipse([m + s * 0.42, m, m + s * 0.58, m + s * 0.16], fill=(214, 150, 20, 255))
        d.pieslice([m + s * 0.15, m + s * 0.08, m + s * 0.85, m + s * 1.1], 180, 360, fill=(250, 200, 40, 255))
        d.rectangle([m + s * 0.15, m + s * 0.58, m + s * 0.85, m + s * 0.76], fill=(250, 200, 40, 255))
        d.rounded_rectangle([m + s * 0.04, m + s * 0.72, m + s * 0.96, m + s * 0.86], radius=int(s * 0.07), fill=(232, 170, 30, 255))
        d.ellipse([m + s * 0.40, m + s * 0.82, m + s * 0.60, m + s * 1.0], fill=(200, 120, 20, 255))
    return shape(s, s, fn)


def calendar(weekday, num, label, color):
    w, h = 300, 350

    def fn(d, m):
        d.rounded_rectangle([m, m, m + w, m + h], radius=26, fill=(255, 255, 255, 255))
        d.rounded_rectangle([m, m, m + w, m + 92], radius=26, fill=color + (255,))
        d.rectangle([m, m + 50, m + w, m + 92], fill=color + (255,))
        ctext(d, m + w / 2, m + 46, weekday, BLK, 44, (255, 255, 255, 255))
        ctext(d, m + w / 2, m + 185, num, BLK, 150, INK + (255,))
        ctext(d, m + w / 2, m + 305, label, RND, 40, color + (255,))
        for x in (m + 70, m + w - 70):
            d.ellipse([x - 12, m - 14, x + 12, m + 18], fill=(60, 50, 80, 255))
    return shape(w, h, fn)


def pricetag():
    w, h = 260, 170

    def fn(d, m):
        d.polygon([(m, m + h / 2), (m + 70, m), (m + w, m), (m + w, m + h), (m + 70, m + h)], fill=(240, 120, 60, 255))
        d.ellipse([m + 38, m + h / 2 - 16, m + 70, m + h / 2 + 16], fill=(255, 255, 255, 255))
        ctext(d, m + 165, m + h / 2, "$ ?", BLK, 84, (255, 255, 255, 255))
    return shape(w, h, fn)


def eye(r=90, iris=(70, 130, 220)):
    w, h = int(2 * r), int(1.3 * r)

    def fn(d, m):
        d.ellipse([m, m, m + w, m + h], fill=(255, 255, 255, 255), outline=(40, 30, 70, 255), width=7)
        ir = h * 0.42
        cx, cy = m + w / 2, m + h / 2
        d.ellipse([cx - ir, cy - ir, cx + ir, cy + ir], fill=iris + (255,))
        d.ellipse([cx - ir * 0.5, cy - ir * 0.5, cx + ir * 0.5, cy + ir * 0.5], fill=(20, 15, 30, 255))
        d.ellipse([cx + ir * 0.15, cy - ir * 0.6, cx + ir * 0.5, cy - ir * 0.25], fill=(255, 255, 255, 255))
    return shape(w, h, fn, stroke=5)


def phone():
    w, h = 340, 640

    def fn(d, m):
        d.rounded_rectangle([m, m, m + w, m + h], radius=50, fill=(28, 28, 40, 255))
        d.rounded_rectangle([m + 16, m + 16, m + w - 16, m + h - 16], radius=38, fill=(206, 228, 250, 255))
        d.rounded_rectangle([m + w / 2 - 50, m + 26, m + w / 2 + 50, m + 50], radius=12, fill=(28, 28, 40, 255))
        d.rounded_rectangle([m + 90, m + 170, m + 250, m + 330], radius=38, fill=(20, 120, 250, 255))
        ctext(d, m + 170, m + 250, "A", BLK, 120, (255, 255, 255, 255))
        ctext(d, m + 170, m + 380, "App Store", RND, 44, (40, 40, 70, 255))
        for i in range(8):  # 转不动的进度圈
            a = i * math.pi / 4
            v = 120 + i * 14
            d.ellipse([m + 170 + 44 * math.cos(a) - 9, m + 490 + 44 * math.sin(a) - 9,
                       m + 170 + 44 * math.cos(a) + 9, m + 490 + 44 * math.sin(a) + 9], fill=(v, v, v, 255))
    return shape(w, h, fn)


def icicles(w=420, h=190):
    def fn(d, m):
        rnd = random.Random(5)
        pts = [(m, m), (m + w, m)]
        x = w
        while x > 0:
            step = rnd.uniform(26, 48)
            ln = rnd.uniform(0.35, 1.0) * h
            pts.append((m + x, m + 40))
            pts.append((m + x - step / 2, m + 40 + ln))
            x -= step
        pts.append((m, m + 40))
        d.polygon(pts, fill=(214, 240, 255, 255))
        d.rectangle([m, m, m + w, m + 46], fill=(236, 248, 255, 255))
    return shape(w, h + 40, fn, stroke=5)


def clock(r=130):
    def fn(d, m):
        c = m + r
        d.ellipse([m, m, m + 2 * r, m + 2 * r], fill=(255, 255, 255, 255), outline=INK + (255,), width=12)
        for i in range(12):
            a = i * math.pi / 6
            d.line([c + (r - 30) * math.sin(a), c - (r - 30) * math.cos(a), c + (r - 16) * math.sin(a), c - (r - 16) * math.cos(a)], fill=INK + (255,), width=6)
        ah = (12 + 29 / 60) / 12 * 2 * math.pi
        am = 29 / 60 * 2 * math.pi
        d.line([c, c, c + r * 0.5 * math.sin(ah), c - r * 0.5 * math.cos(ah)], fill=INK + (255,), width=12)
        d.line([c, c, c + r * 0.78 * math.sin(am), c - r * 0.78 * math.cos(am)], fill=RED + (255,), width=8)
        d.ellipse([c - 10, c - 10, c + 10, c + 10], fill=INK + (255,))
    return shape(2 * r, 2 * r, fn)


def bandaid(w=440, h=130):
    def fn(d, m):
        d.rounded_rectangle([m, m, m + w, m + h], radius=h // 2, fill=(236, 196, 150, 255))
        d.rectangle([m + w * 0.36, m + 10, m + w * 0.64, m + h - 10], fill=(248, 222, 188, 255))
        for i in range(3):
            for j in range(3):
                x, y = m + w * 0.44 + i * w * 0.06, m + h * 0.3 + j * h * 0.2
                d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(214, 170, 128, 255))
    return shape(w, h, fn)


def moon(r=120):
    def fn(d, m):
        d.ellipse([m, m, m + 2 * r, m + 2 * r], fill=(250, 236, 170, 255))
        for cx, cy, cr in ((0.6, 0.5, 0.2), (1.2, 0.7, 0.14), (0.9, 1.3, 0.25), (1.45, 1.25, 0.1)):
            d.ellipse([m + r * cx - r * cr, m + r * cy - r * cr, m + r * cx + r * cr, m + r * cy + r * cr], fill=(232, 212, 140, 255))
    return shape(2 * r, 2 * r, fn)


def sheep():
    w, h = 240, 180

    def fn(d, m):
        for x in (70, 100, 150, 180):
            d.rounded_rectangle([m + x - 7, m + 110, m + x + 7, m + 178], radius=6, fill=(40, 36, 50, 255))
        rnd = random.Random(9)
        for _ in range(14):
            cx, cy, r = m + 60 + rnd.uniform(0, 130), m + 50 + rnd.uniform(0, 60), rnd.uniform(30, 44)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(252, 252, 250, 255))
        d.ellipse([m + 2, m + 40, m + 70, m + 100], fill=(40, 36, 50, 255))   # 头朝左
        d.ellipse([m + 18, m + 56, m + 30, m + 68], fill=(255, 255, 255, 255))
        d.ellipse([m + 48, m + 30, m + 78, m + 52], fill=(40, 36, 50, 255))
    return shape(w, h, fn, stroke=6)


def fence():
    w, h = 230, 170

    def fn(d, m):
        for x in (20, 105, 190):
            d.rounded_rectangle([m + x, m, m + x + 24, m + h], radius=8, fill=(170, 110, 60, 255))
        for y in (40, 100):
            d.rounded_rectangle([m, m + y, m + w, m + y + 22], radius=8, fill=(196, 134, 78, 255))
    return shape(w, h, fn)


def code_card(seed):
    w, h = 230, 120

    def fn(d, m):
        rnd = random.Random(seed)
        d.rounded_rectangle([m, m, m + w, m + h], radius=18, fill=(255, 255, 255, 255))
        d.ellipse([m + 14, m + 14, m + 54, m + 54], fill=(60, 180, 90, 255))
        d.line([m + 24, m + 35, m + 32, m + 44, m + 45, m + 25], fill=(255, 255, 255, 255), width=7)
        ctext(d, m + 140, m + 34, "MERGED", BLK, 30, (60, 180, 90, 255))
        for j in range(2):
            x = m + 20
            for _ in range(3):
                ln = rnd.uniform(30, 70)
                d.rounded_rectangle([x, m + 70 + j * 22, x + ln, m + 82 + j * 22], radius=6,
                                    fill=rnd.choice([(120, 110, 220), (240, 150, 60), (90, 170, 230)]) + (255,))
                x += ln + 10
    return shape(w, h, fn, stroke=5)


def tile(ch, color):
    w, h = 170, 200

    def fn(d, m):
        d.rounded_rectangle([m, m, m + w, m + h], radius=26, fill=color + (255,))
        ctext(d, m + w / 2, m + h / 2, ch, BLK, 150, (255, 255, 255, 255))
    return shape(w, h, fn)


def xmark(s=130):
    def fn(d, m):
        d.line([m + 10, m + 10, m + s - 10, m + s - 10], fill=(220, 40, 50, 255), width=30)
        d.line([m + s - 10, m + 10, m + 10, m + s - 10], fill=(220, 40, 50, 255), width=30)
    return shape(s, s, fn, stroke=6)


def strip_with(img, w, h, bg=(255, 255, 255)):
    s = torn_rect(w, h, bg, border=8)
    im = img.convert("RGBA")
    bb = im.split()[3].getbbox()
    if bb:
        im = im.crop(bb)
    sc = min((w - 60) / im.width, (h - 36) / im.height)
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    return comp(s, im, (s.width - im.width) / 2, (s.height - im.height) / 2)


def night_bg(size, with_moon=False):
    bg = paper((26, 28, 78), size)
    d = ImageDraw.Draw(bg)
    rnd = random.Random(21)
    for _ in range(int(size[0] * size[1] / 9000)):
        x, y, r = rnd.uniform(0, size[0]), rnd.uniform(0, size[1] * 0.8), rnd.uniform(1.2, 3.4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 220))
    if with_moon:
        d.ellipse([size[0] * 0.62, size[1] * 0.08, size[0] * 0.62 + 150, size[1] * 0.08 + 150], fill=(250, 236, 170))
    return bg


def card(bg, caption, cap_bg, fig=None, fig_dx=0, fig_dy=0, centering=(0.5, 0.5), extra=(), darken=1.0):
    """封面页上的新闻卡片：一张手撕照片 + 压在上面的抠图 + 一句要点。"""
    if darken != 1.0:
        bg = ImageEnhance.Brightness(bg.convert("RGB")).enhance(darken)
    photo = torn_photo(bg, 310, 300, border=14, centering=centering)
    cap = tag(caption, 30, fg=(255, 255, 255), bg=cap_bg, outline=(255, 255, 255))
    cw, ch = max(photo.width + 40, cap.width + 10), photo.height + 110
    c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    c = comp(c, photo, (cw - photo.width) / 2, 30)
    base_y = 30 + photo.height - 44
    if fig is not None:
        c = comp(c, fig, cw / 2 - fig.width / 2 + fig_dx, base_y - fig.height + 30 + fig_dy)
    for sp, dx, dy in extra:
        c = comp(c, sp, cw / 2 - sp.width / 2 + dx, base_y - sp.height / 2 + dy)
    return comp(c, cap, cw / 2 - cap.width / 2, base_y - 10)


def hide(t, t_out, d=0.18):
    """到 t_out 时缩小消失，之前返回 1。"""
    return 1 - ease_in((t - t_out) / d)
