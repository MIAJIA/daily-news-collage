"""每日新闻拼贴视频的骨架：每天不变的部分都在这里。

一天的文件（例：2026-11-17/这一天的画面.py）只需要做三件事：
  1. day = Day(当天文件夹, 音频, date="NOV 17", weekday="TUESDAY", year=2026, next_date="NOV 18")
  2. 每条新闻登记一张封面卡片：day.headline("NVIDIA", 卡片, arrive=那条新闻第一句歌词的时刻)
  3. 每句歌词登记一幕：day.scene(开始时刻, 画面函数, enter="sheet" 或 "tear")
     画面函数可以用这里的标准画面（std_number、std_photo），也可以自己写一个 f(t) -> 图片。
最后 day.run() 出片；命令行加 --stills <文件夹> <秒> <秒> … 只导出静帧检查。

骨架自动负责：读音频里的逐句歌词时间、封面页（视频第 0 帧就是完整的封面图）、底部时间轴和纸飞机、
纸片字幕（每个词一张小纸片，唱到哪个词哪个词变色并跳一下，重点词是黄色，用 day.subtitles(key=[…]) 指定；
在 day.subtitles(zh=[…]) 里每句写一条中文，命令行加 --zh 就出中文字幕版）、
撕纸和盖纸两种转场、结尾（卡片回场 + 明天见）、底部署名（读 素材来源.tsv）、纸纹、配音频导出 mp4、
导出封面图并把它存成视频文件的封面。
"""
import bisect
import glob
import math
import os
import random
import re
import struct
import subprocess
import sys

import collage_lib as L
from collage_lib import *  # noqa: F401,F403

FPS = 24
CARD_ROT = [-3, 2, -2, 3, -2, 2]
CARD_Y = 592
BAR_Y = 1006
SUB_Y = 866    # 字幕那一行纸片的中心高度


def zh_font():
    """中文字幕用的字体：优先圆体（和英文的圆头粗体最接近），没有就用冬青黑体。返回 (文件, 第几款)。"""
    for p in sorted(glob.glob("/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/Yuanti.ttc")):
        for idx in range(8):
            try:
                if ImageFont.truetype(p, 20, index=idx).getname() == ("Yuanti SC", "Bold"):
                    return p, idx
            except Exception:
                break
    return "/System/Library/Fonts/Hiragino Sans GB.ttc", 2


def _out(cmd):
    return subprocess.run(cmd, capture_output=True).stdout


def _sec(s):
    h, m, rest = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))


class Day:
    def __init__(self, folder, audio, date, weekday, year, next_date, bg=(214, 203, 234)):
        self.folder, self.audio = os.path.abspath(folder), audio
        self.date, self.weekday, self.year, self.next_date = date, weekday, year, next_date
        self.srcdir, self.cutdir = os.path.join(self.folder, "素材下载"), os.path.join(self.folder, "抠图")
        L.SRC = self.srcdir
        self.dur = float(_out(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio]).decode().strip())
        self.lines, self.sections = self._lyrics()
        self.onsets = self._onsets()
        self.heads, self.scenes = [], []
        self.bg = paper(bg)
        h = halftone((255, 255, 255), 40, 520, alpha=130, grow_down=True)
        self.bg.paste(h, (0, 0), h)
        self._clouds = [cloud(760, 330, 1), cloud(560, 250, 2), cloud(430, 190, 3)]
        a, b = self.lines[0][0], self.lines[0][1]
        self.t_intro = dict(date=a + 0.18, five=a + 1.9, minute=a + 3.2, go=a + 4.7, hey=a + 5.4, build=b - 1.6)
        self.t_outro = None
        self.sub_cfg = dict(key=None, anchors={}, on=True, zh=None, lang="en")
        self.t_end = self.sections.get("End", self.dur - 3.3) + 0.06
        self.ready = False

    # ---------- 读音频 ----------
    def _lyrics(self):
        """音频自带的字幕轨 → 每句歌词的 (开始, 结束, 文字)，以及 [Verse 1] 这类段落标记的时刻。"""
        txt = _out(["ffmpeg", "-v", "error", "-i", self.audio, "-map", "0:s:0", "-f", "srt", "-"]).decode("utf-8", "replace")
        lines, sections = [], {}
        for block in txt.strip().split("\n\n"):
            rows = [r for r in block.split("\n") if r.strip()]
            if len(rows) < 3 or "-->" not in rows[1]:
                continue
            a, b = [_sec(x.strip()) for x in rows[1].split("-->")]
            text = " ".join(rows[2:]).strip()
            if text.startswith("["):
                sections[text.strip("[]").split(" - ")[0]] = a
            else:
                lines.append((a, b, text))
        if not lines:
            raise SystemExit("这个音频里没有逐句字幕轨，需要手工给每句歌词的时间。")
        return lines, sections

    def _onsets(self):
        """量音量突然变大的时刻（鼓点、重音），给画面卡点用。"""
        raw = _out(["ffmpeg", "-v", "error", "-i", self.audio, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"])
        n = len(raw) // 2
        s = struct.unpack("<%dh" % n, raw[:2 * n])
        env = [math.sqrt(sum(x * x for x in s[i:i + 80]) / 80) for i in range(0, n - 80, 80)]
        return [(i / 100, env[i] - env[i - 1]) for i in range(1, len(env)) if env[i] > env[i - 1]]

    def beats(self, a, b, n, gap=0.30):
        """在 a 到 b 秒之间挑 n 个最强的重音时刻；不够就平均补。"""
        cand = sorted([(v, t) for t, v in self.onsets if a + 0.02 <= t <= b - 0.15], reverse=True)
        picked = []
        for v, t in cand:
            if all(abs(t - p) >= gap for p in picked):
                picked.append(t)
            if len(picked) == n:
                break
        k = 0
        while len(picked) < n:
            picked.append(a + (b - a) * (k + 0.5) / n)
            k += 1
        return sorted(picked)

    def line(self, i):
        return self.lines[i]

    def src(self, name):
        return Image.open(os.path.join(self.srcdir, name))

    def cut(self, name):
        return Image.open(os.path.join(self.cutdir, name))

    # ---------- 登记 ----------
    def headline(self, name, card_sprite, arrive):
        """一条新闻：时间轴上的名字、封面卡片、纸飞机到达它的时刻。"""
        self.heads.append((name, card_sprite, arrive))

    def scene(self, start, fn, enter="sheet", dur=0.24):
        self.scenes.append((start, fn, enter, dur))

    def intro(self, **times):
        """封面页上各样东西弹出的时刻：date、five、minute、go、hey、build（开始推近的时刻）。"""
        self.t_intro.update(times)

    def outro(self, start, shouts, hey, tomorrow, sameway, plane_leaves, tomorrow_text="TOMORROW: A NEW VERSE", sameway_text="THE SAME WAY"):
        """结尾：start 开始撕入；shouts 是 [(文字, 时刻)]，最多三条。"""
        self.t_outro = dict(start=start, shouts=shouts, hey=hey, tomorrow=tomorrow, sameway=sameway, leave=plane_leaves,
                            tomorrow_text=tomorrow_text, sameway_text=sameway_text)

    def subtitles(self, key=None, anchors=None, on=True, zh=None, lang="en"):
        """字幕。key：重点词的列表（不给就自动挑带数字的词和句中大写开头的词）。
        anchors：{第几句: {第几个词: 时刻}}，听过以后发现某个词亮得不准，就在这里钉住它的时刻。
        zh：中文字幕，每句歌词一条，写法是用 | 把一句切成几张纸片；纸片末尾加 * 表示重点词，
            加 @数字 表示它和英文歌词的第几个词同时亮。例："英伟达！*@0 | 创始人@1 | 走了，*@2"。
        lang："en" 出英文字幕，"zh" 出中文字幕；命令行加 --zh 也会切到中文并另存一个文件。"""
        self.sub_cfg = dict(key=key, anchors=anchors or {}, on=on, zh=zh, lang=lang)

    def clouds(self, c, t, t0=0.0, y=0):
        drift = (t - t0) * 9
        place(c, "cloud3", self._clouds[2], 1640 - drift * 0.6, 150 + y)
        place(c, "cloud1", self._clouds[0], 1280 - drift, 360 + y)
        place(c, "cloud2", self._clouds[1], 260 + drift * 0.8, 210 + y)

    # ---------- 骨架用的纸片 ----------
    def _prepare(self):
        if self.ready:
            return
        if self.t_outro is None:
            a, b, _ = self.lines[-2]
            c0, _, _ = self.lines[-1]
            bt = self.beats(a, b, 3)
            self.outro(a - 0.16, [("THAT'S THE NEWS!", bt[0]), ("THAT'S THE BEAT!", bt[1]), ("THAT'S THE DAY!", bt[2])],
                       hey=b - 0.5, tomorrow=c0, sameway=c0 + 1.65, plane_leaves=c0 + 0.85)
        n = len(self.heads)
        self.ticks = [960] if n == 1 else [220 + (W - 440) * i / (n - 1) for i in range(n)]
        self.card_scale = 1.08 if n <= 5 else 0.92
        self.arrive = [h[2] for h in self.heads]
        S = self.S = {}
        S["date"] = gradient_text(self.date, 210, PURPLE, PINK, stroke=14)
        S["weekday"] = tag("%s  %d" % (self.weekday, self.year), 36)
        S["five"] = tag("%d HEADLINES" % n, 60, fg=(255, 255, 255), bg=PURPLE, outline=(255, 255, 255))
        S["minute"] = tag("1 MINUTE", 60, fg=(60, 40, 110), bg=YELLOW, outline=(255, 255, 255))
        S["go"] = burst("GO!", 130, fill=(240, 80, 70), fg=(255, 255, 255))
        S["hey"] = bubble("HEY!", 76)
        cols = [((255, 255, 255), PURPLE), ((255, 255, 255), PINK), ((60, 40, 110), YELLOW)]
        for k, (text, _) in enumerate(self.t_outro["shouts"][:3]):
            S["shout%d" % k] = tag(text, 58, fg=cols[k][0], bg=cols[k][1], outline=(255, 255, 255))
        S["tomorrow"] = gradient_text(self.t_outro["tomorrow_text"], 104, PURPLE, PINK, stroke=12)
        S["sameway"] = tag(self.t_outro["sameway_text"], 54, fg=(255, 255, 255), bg=PURPLE, outline=(255, 255, 255))
        self.bg_end = paper((250, 246, 240))
        he = halftone((200, 186, 232), 560, 1080, alpha=120, grow_down=True)
        self.bg_end.paste(he, (0, 0), he)
        S["seeyou"] = gradient_text("SEE YOU TOMORROW", 150, PURPLE, PINK, stroke=14)
        S["everyday"] = tag("%d HEADLINES, 1 MINUTE, EVERY DAY" % n, 46)
        S["next"] = tag("NEXT: %s" % self.next_date, 46, fg=(60, 40, 110), bg=YELLOW, outline=(255, 255, 255))
        # 时间轴
        self.bar_x0, self.bar_x1, m = 110, 1810, 30
        w, h = self.bar_x1 - self.bar_x0 + 2 * m, 70 + 2 * m
        face = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(face)
        y = m + 46
        d.rounded_rectangle([m, y - 11, w - m, y + 11], radius=11, fill=PURPLE + (255,))
        for cx in (m + 8, w - m - 8):
            d.ellipse([cx - 17, y - 17, cx + 17, y + 17], fill=PURPLE + (255,))
            d.ellipse([cx - 6, y - 6, cx + 6, y + 6], fill=(255, 255, 255, 255))
        for tx in self.ticks:
            x = tx - self.bar_x0 + m
            d.rounded_rectangle([x - 6, y - 30, x + 6, y], radius=6, fill=PURPLE + (255,))
        hard = face.split()[3]
        dil = hard.filter(ImageFilter.GaussianBlur(4)).point(lambda x: 255 if x > 20 else 0)
        S["bar"], self.bar_m = with_edge(face, rough(dil, amp=8, cell=18, blur=1.5)), m
        for i, (name, _, _) in enumerate(self.heads):
            S["tag_dim%d" % i] = tag(name, 30, fg=(150, 135, 200))
            S["tag_lit%d" % i] = tag(name, 34, fg=(255, 255, 255), bg=PURPLE, outline=(255, 255, 255))
        S["plane"] = paper_plane()
        S["credit"] = self._credit()
        self._build_subs()
        self.grain = Image.effect_noise((W, H), 9).convert("RGB")
        self.white = Image.new("RGB", (W, H), (255, 255, 255))
        rnd = random.Random(7)   # 撕开用的锯齿线
        pts, y = [(0, 0)], -30
        while y <= H + 30:
            pts.append((960 + rnd.uniform(-52, 52), y))
            y += rnd.uniform(18, 42)
        pts.append((0, H + 30))
        tl = Image.new("L", (W, H), 0)
        ImageDraw.Draw(tl).polygon(pts, fill=255)
        tr = ImageChops.invert(tl)
        self.tear = (tl, tr, ImageChops.lighter(tl, ImageChops.offset(tl, 16, 0)), ImageChops.lighter(tr, ImageChops.offset(tr, -16, 0)))
        rnd = random.Random(11)  # 盖纸用的左边缘
        pts, y = [], -30
        while y <= H + 30:
            pts.append((34 + rnd.uniform(-24, 24), y))
            y += rnd.uniform(16, 38)
        pts += [(W, H + 30), (W, -30)]
        self.sheet = Image.new("L", (W, H), 0)
        ImageDraw.Draw(self.sheet).polygon(pts, fill=255)
        segs = [(0.0, self._cover, None, 0)] + sorted(self.scenes, key=lambda s: s[0])
        segs += [(self.t_outro["start"], self._outro, "tear", 0.34), (self.t_end, self._endcard, "sheet", 0.50)]
        self.segs = segs
        self.ready = True

    def _chip(self, text, size, fg, bg, font=None):
        f = ImageFont.truetype(font[0], size, index=font[1]) if font else ImageFont.truetype(RND, size)
        bb = f.getbbox(text)
        padx, pady, m = int(size * 0.34), int(size * 0.26), 16
        w, h = bb[2] - bb[0] + 2 * padx + 2 * m, bb[3] - bb[1] + 2 * pady + 2 * m
        face = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(face)
        d.rounded_rectangle([m, m, w - m, h - m], radius=9, fill=bg + (255,))
        d.text((m + padx - bb[0], m + pady - bb[1]), text, font=f, fill=fg + (255,))
        edge = Image.new("L", (w, h), 0)
        ImageDraw.Draw(edge).rounded_rectangle([m - 5, m - 5, w - m + 5, h - m + 5], radius=12, fill=255)
        return with_edge(face, rough(edge, amp=10, cell=12, blur=1.5))

    def _build_subs(self):
        """每句歌词 → 一行小纸片（每个词一张），并估出每个词开始唱的时刻。"""
        cfg = self.sub_cfg
        norm = lambda w: re.sub(r"[^a-z0-9'-]", "", w.lower())
        keys = None if cfg["key"] is None else set(norm(k) for k in cfg["key"])
        self.subs = []
        for li, (a, b, text) in enumerate(self.lines):
            toks = text.split()
            wts = []
            for tk in toks:
                if not any(ch.isalnum() for ch in tk):
                    wts.append(0.6)          # 破折号、省略号：算一小段停顿
                else:
                    parts = [x for x in re.split(r"-", tk) if x]
                    wts.append(sum(max(1, len(re.findall(r"[aeiouy]+", x.lower()))) for x in parts))
            end = b if li + 1 >= len(self.lines) else self.lines[li + 1][0]
            t0, t1 = a + 0.05, a + (min(b, end) - a) * 0.92
            anc = dict(cfg["anchors"].get(li, {}))
            anc.setdefault(0, t0)
            pts = sorted(anc.items()) + [(len(toks), t1)]
            times = [0.0] * len(toks)
            for (i0, ta), (i1, tb) in zip(pts, pts[1:]):
                tot = sum(wts[i0:i1]) or 1
                acc = 0.0
                for i in range(i0, i1):
                    times[i] = ta + (tb - ta) * acc / tot
                    acc += wts[i]
            rnd = random.Random(100 + li)
            chips, x = [], 0
            zh = cfg["zh"][li] if cfg["lang"] == "zh" and cfg["zh"] and li < len(cfg["zh"]) and cfg["zh"][li] else None
            if zh:
                font = zh_font()
                items = []
                for part in zh.split("|"):
                    part = part.strip()
                    m = re.search(r"@(\d+)$", part)
                    idx = int(m.group(1)) if m else None
                    part = part[:m.start()] if m else part
                    is_key = part.endswith("*")
                    items.append([part.rstrip("*").strip().rstrip("，"), idx, is_key])   # 纸片末尾的逗号去掉，纸片之间本来就有间隔
                ptimes = [times[min(it[1], len(times) - 1)] if it[1] is not None else None for it in items]
                if ptimes[0] is None:
                    ptimes[0] = t0
                known = [(k, v) for k, v in enumerate(ptimes) if v is not None] + [(len(items), t1)]
                for (k0, ta), (k1, tb) in zip(known, known[1:]):   # 没钉的纸片按字数在前后两张之间摊开
                    tot = sum(len(items[k][0]) for k in range(k0, k1)) or 1
                    acc = 0
                    for k in range(k0, k1):
                        ptimes[k] = ta + (tb - ta) * acc / tot
                        acc += len(items[k][0])
                for (txt, _, is_key), tt in zip(items, ptimes):
                    size = 58 if is_key else 50
                    plain = self._chip(txt, size, INK, (255, 255, 255), font)
                    sung = self._chip(txt, size, (60, 40, 110), YELLOW, font) if is_key else self._chip(txt, size, (255, 255, 255), PURPLE, font)
                    chips.append(dict(plain=plain, sung=sung, t=tt, x=x + plain.width / 2, rot=rnd.uniform(-2.5, 2.5), key=is_key))
                    x += plain.width - 22
            for i, tk in enumerate(toks if not zh else []):
                if not any(ch.isalnum() for ch in tk):
                    continue
                if keys is None:
                    is_key = any(ch.isdigit() for ch in tk) or (i > 0 and tk[:1].isupper() and tk.lower() not in ("i", "i'm")) or tk.count("-") >= 1
                else:
                    is_key = norm(tk) in keys
                size = 60 if is_key else 52
                plain = self._chip(tk, size, INK, (255, 255, 255))
                sung = self._chip(tk, size, (60, 40, 110), YELLOW) if is_key else self._chip(tk, size, (255, 255, 255), PURPLE)
                chips.append(dict(plain=plain, sung=sung, t=times[i], x=x + plain.width / 2, rot=rnd.uniform(-2.5, 2.5), key=is_key))
                x += plain.width - 22
            total = x + 22
            sc = min(1.0, 1780 / total)
            for ch in chips:
                ch["x"] = 960 + (ch["x"] - total / 2) * sc
            self.subs.append(dict(a=a, end=end, chips=chips, sc=sc))
        strong = sorted(v for _, v in self.onsets)
        cutv = strong[int(len(strong) * 0.80)] if strong else 0
        self.hits = [t for t, v in self.onsets if v >= cutv]

    def _subs(self, c, t):
        if not self.sub_cfg["on"]:
            return
        for li, sub in enumerate(self.subs):
            if not (sub["a"] - 0.14 <= t < sub["end"] - 0.14):
                continue
            k = bisect.bisect_right(self.hits, t) - 1
            beat = max(0.0, 1 - (t - self.hits[k]) / 0.14) if k >= 0 else 0.0   # 跟着鼓点轻轻跳
            chips = sub["chips"]
            for j, ch in enumerate(chips):
                s = sub["sc"] * pop(t, sub["a"] - 0.14 + 0.025 * j, 0.20)
                done = t >= ch["t"]
                nxt = chips[j + 1]["t"] if j + 1 < len(chips) else sub["end"]
                bump = max(0.0, 1 - (t - ch["t"]) / 0.28) if done else 0.0      # 刚唱到的词跳一下
                y = SUB_Y - 5 * beat - (16 if ch["key"] else 10) * bump
                rot = ch["rot"] + (6 * bump * (1 if j % 2 else -1) if done and t < nxt else 0)
                place(c, "sub%d_%d%s" % (li, j, "s" if done else "p"), ch["sung"] if done else ch["plain"], ch["x"], y,
                      s * (1 + (0.26 if ch["key"] else 0.16) * bump), rot)

    def _credit(self):
        """底部署名：读 素材来源.tsv 里的作者和授权。"""
        authors, lics = [], []
        p = os.path.join(self.folder, "素材来源.tsv")
        if os.path.exists(p):
            for ln in open(p, encoding="utf-8").read().splitlines()[1:]:
                f = ln.split("\t")
                if len(f) >= 4:
                    if f[3] not in authors:
                        authors.append(f[3])
                    lic = f[2].rsplit(" ", 1)[0] if f[2][-1:].isdigit() else f[2]
                    if lic not in lics and lic != "Public domain":
                        lics.append(lic)
        text = "Photos via Wikimedia Commons: " + ", ".join(authors) + " (" + " / ".join(lics) + "). Logos belong to their owners."
        font = ImageFont.truetype(HEL, 13)
        words, rows, cur = text.split(" "), [], ""
        for wd in words:
            if font.getbbox(cur + " " + wd)[2] > W * 0.5 and cur:
                rows.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        rows.append(cur)
        rows = rows[-3:]
        im = Image.new("RGBA", (W, 15 * len(rows) + 6), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for k, r in enumerate(rows):
            w = font.getbbox(r)[2]
            d.text((W - w - 13, 3 + k * 15), r, font=font, fill=(20, 15, 40, 150))
            d.text((W - w - 14, 2 + k * 15), r, font=font, fill=(255, 255, 255, 215))
        return im

    # ---------- 每天不变的三幕 ----------
    def _cards(self, c, t, scale_fn):
        for i, (_, sp, _) in enumerate(self.heads):
            place(c, "card%d" % i, sp, self.ticks[i], CARD_Y, self.card_scale * scale_fn(i), CARD_ROT[i % 6], t)

    def _cover(self, t):
        """第 0 秒就是完整的封面图；唱到谁，谁跳一下。"""
        S, T = self.S, self.t_intro
        pulse = lambda t0, amp=0.22, d=0.22: 1 + amp * max(0.0, 1 - abs(t - t0) / d)
        c = self.bg.copy()
        self.clouds(c, t)
        place(c, "date", S["date"], 960, 150, pulse(T["date"], 0.16), -2, t)
        place(c, "weekday", S["weekday"], 1400, 262, pulse(T["date"] + 0.45), 3, t)
        for i, (_, sp, _) in enumerate(self.heads):   # 卡片一直轻轻晃；唱到 "headlines" 时一张接一张跳起来
            hop = max(0.0, 1 - abs(t - (T["five"] + 0.16 + 0.14 * i)) / 0.16)
            place(c, "card%d" % i, sp, self.ticks[i], CARD_Y - 26 * hop + 4 * math.sin(t * 2.2 + i),
                  self.card_scale * (1 + 0.08 * hop), CARD_ROT[i % 6] + 1.2 * math.sin(t * 1.7 + i * 2), t)
        place(c, "five", S["five"], 520, 322, pulse(T["five"]), -4, t)
        place(c, "minute", S["minute"], 1150, 330, pulse(T["minute"]), 4, t)
        place(c, "go", S["go"], 1750, 150, pulse(T["go"], 0.30), 8 + 6 * math.sin(t * 9), t)
        place(c, "hey", S["hey"], 220, 140, pulse(T["hey"], 0.30), 6, t)
        if t > T["build"]:   # 鼓点渐强：整张画慢慢推近并且抖
            p = clamp01((t - T["build"]) / 1.6)
            z = 1 + 0.07 * ease_in(p)
            r = random.Random(int(t * 12))
            big = c.resize((int(W * z), int(H * z)), Image.BILINEAR)
            x0 = max(0, min(big.width - W, int((big.width - W) / 2 + r.uniform(-1, 1) * 7 * p)))
            y0 = max(0, min(big.height - H, int((big.height - H) / 2 + r.uniform(-1, 1) * 7 * p)))
            c = big.crop((x0, y0, x0 + W, y0 + H))
        return c

    def _outro(self, t):
        S, T = self.S, self.t_outro
        c = self.bg.copy()
        self.clouds(c, t, T["start"])
        self._cards(c, t, lambda i: pop(t, T["start"] + 0.06 + 0.07 * i, 0.26))
        if t < T["tomorrow"] + 0.2:
            h = hide(t, T["tomorrow"])
            spots = [(430, 150, -4), (960, 270, 2), (1490, 150, 4)]
            for k, (_, tk) in enumerate(T["shouts"][:3]):
                place(c, "shout%d" % k, S["shout%d" % k], spots[k][0], spots[k][1], pop(t, tk) * h, spots[k][2], t)
            place(c, "hey", S["hey"], 960, 110, pop(t, T["hey"], 0.22) * h, 6, t)
        place(c, "tomorrow", S["tomorrow"], 960, 150, pop(t, T["tomorrow"] + 0.20, 0.30), -1, t)
        place(c, "sameway", S["sameway"], 960, 300, pop(t, T["sameway"]), 2, t)
        return c

    def _endcard(self, t):
        S = self.S
        c = self.bg_end.copy()
        self.clouds(c, t, self.t_end - 0.45, y=20)
        place(c, "seeyou", S["seeyou"], 960, 430, pop(t, self.t_end + 0.45, 0.32), -2, t)
        place(c, "everyday", S["everyday"], 960, 640, pop(t, self.t_end + 0.80), 1, t)
        place(c, "next", S["next"], 960, 770, pop(t, self.t_end + 1.10), -2, t)
        place(c, "plane_big", S["plane"], -200 + (t - self.t_end) * 620, 900 - 40 * math.sin(t * 3), 1.8, 8 * math.sin(t * 3 + 1))
        return c

    def _timeline(self, c, t):
        S, T = self.S, self.t_intro
        bar = S["bar"]
        c.paste(bar, (self.bar_x0 - self.bar_m, BAR_Y - self.bar_m - 46), bar)
        for i, tx in enumerate(self.ticks):
            s = 1 + 0.25 * max(0.0, 1 - abs(t - (T["five"] + 0.16 + 0.14 * i)) / 0.14)
            lit = t >= self.arrive[i]
            if lit:
                s = 1 + 0.35 * max(0, 1 - (t - self.arrive[i]) / 0.3)
            place(c, "tag%d%s" % (i, "L" if lit else "D"), S[("tag_lit%d" if lit else "tag_dim%d") % i], tx, BAR_Y - 62, s, 0)
        xs = [self.bar_x0 + 10] + self.ticks
        px, hop = xs[0], 0.0
        for k, ta in enumerate(self.arrive):
            t0 = T["build"] if k == 0 else ta - 0.9
            if t >= ta:
                px, hop = xs[k + 1], 0.0
            elif t > t0:
                p = ease_io((t - t0) / (ta - t0))
                px, hop = xs[k] + (xs[k + 1] - xs[k]) * p, math.sin(math.pi * p)
        leave = self.t_outro["leave"]
        if t > leave:   # 结尾：纸飞机飞出时间轴
            p = ease_in((t - leave) / 1.9)
            px, hop = xs[-1] + (W + 300 - xs[-1]) * p, min(1.0, p * 3)
        py = BAR_Y + 4 + 4 * math.sin(t * 5) - 26 * hop
        place(c, "plane", S["plane"], px - 34, py, 0.72, 5 * math.sin(t * 3) + 10 * hop, t)

    # ---------- 合成一帧 ----------
    def frame(self, t):
        self._prepare()
        i = max(k for k, s in enumerate(self.segs) if s[0] <= t)
        t0, fn, tr, dur = self.segs[i]
        is_end = i == len(self.segs) - 1
        if tr and t < t0 + dur:
            prev, cur = self.segs[i - 1][1](t), fn(t)
            if is_end:
                self._timeline(prev, t)
                self._subs(prev, t)
            p = (t - t0) / dur
            if tr == "tear":   # 上一幕从中间撕成两半
                c = cur
                off = int(ease_in(p) * 1150) + 6
                c.paste(self.white, (-off, 0), self.tear[2])
                c.paste(prev, (-off, 0), self.tear[0])
                c.paste(self.white, (off, 0), self.tear[3])
                c.paste(prev, (off, 0), self.tear[1])
            else:              # 新的一幕像一张纸从右边盖进来
                c = prev
                off = int((1 - ease_out(p)) * W)
                c.paste(self.white, (off - 18, 0), self.sheet)
                c.paste(cur, (off, 0), self.sheet)
        else:
            c = fn(t)
        if not is_end:
            self._timeline(c, t)
            self._subs(c, t)
        cr = self.S["credit"]
        c.paste(cr, (0, H - cr.height), cr)
        c = ImageChops.overlay(c, self.grain)
        if t > self.dur - 0.5:
            c = Image.blend(c, self.white, clamp01((t - (self.dur - 0.5)) / 0.5))
        return c

    def run(self, argv=None, name=None):
        argv = list(sys.argv[1:] if argv is None else argv)
        suffix = ""
        if "--zh" in argv:   # 中文字幕版：另存一个文件，不覆盖英文字幕版
            argv.remove("--zh")
            if not self.sub_cfg.get("zh"):
                raise SystemExit("这一天还没有写中文字幕：在 day.subtitles(zh=[…]) 里每句歌词写一条。")
            self.sub_cfg["lang"], suffix = "zh", "_中文字幕"
        self._prepare()
        if argv and argv[0] == "--stills":
            os.makedirs(argv[1], exist_ok=True)
            for s in argv[2:]:
                self.frame(float(s)).save(os.path.join(argv[1], "t%05.2f.jpg" % float(s)), quality=88)
            return
        day = os.path.basename(self.folder)
        base = name or "每日新闻_%s.mp4" % day
        out = os.path.join(self.folder, base[:-4] + suffix + ".mp4")
        cover = os.path.join(self.folder, "封面_%s.jpg" % day)
        self.frame(0.0).save(cover, quality=92)   # 视频的第 0 帧就是这张封面
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
               "-i", "-", "-i", self.audio, "-i", cover, "-map", "0:v", "-map", "1:a", "-map", "2:v", "-t", str(self.dur),
               "-af", "afade=t=out:st=%.2f:d=1.0" % (self.dur - 1.0),
               "-c:v:0", "libx264", "-preset:v:0", "medium", "-crf:v:0", "19", "-pix_fmt:v:0", "yuv420p",
               "-c:v:1", "mjpeg", "-disposition:v:1", "attached_pic",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        n = int(self.dur * FPS)
        for i in range(n):
            p.stdin.write(self.frame(i / FPS).tobytes())
            if i % 240 == 0:
                print("  %d / %d 帧" % (i, n), file=sys.stderr)
        p.stdin.close()
        p.wait()
        print("写好了：", out, file=sys.stderr)


# ---------- 标准画面：大多数歌词句子用这两种就够 ----------
def _bg(color, dots):
    bg = paper(color)
    h = halftone(dots, 420, 1080, alpha=105, grow_down=True)
    bg.paste(h, (0, 0), h)
    return bg


_N = [0]


def _key():
    _N[0] += 1
    return "std%d_" % _N[0]


def std_number(day, a, b, number, label=None, tags=(), shout=None, bg=(44, 92, 196), dots=(120, 170, 255),
               colors=((255, 232, 90), (255, 150, 40))):
    """「大数字」：一个大数字居中，上面一行说明，下面最多三个标签，可选一个爆炸贴。
    例：std_number(day, 12.3, 14.8, "$115.8B", label="RECORD QUARTERLY REVENUE", tags=["REVENUE DOUBLED"], shout="+103%")"""
    k, back = _key(), _bg(bg, dots)
    size = max(150, min(260, int(1800 / max(4, len(number)))))
    num = gradient_text(number, size, colors[0], colors[1], stroke=18)
    lab = tag(label, 50) if label else None
    tg = [tag(x, 58, fg=(255, 255, 255), bg=PURPLE, outline=(255, 255, 255)) for x in tags[:3]]
    sh = burst(shout, 160, fill=YELLOW, fg=(60, 40, 110), size=int(min(84, 2.4 * 160 / max(4, len(shout))))) if shout else None
    bt = day.beats(a, b, 1 + len(tg) + (1 if sh else 0))
    spots = [(560, 620, -3), (1300, 640, 3), (940, 760, -2)]

    def fn(t):
        c = back.copy()
        if lab:
            place(c, k + "lab", lab, 960, 120, pop(t, a + 0.10), -2, t)
        place(c, k + "num", num, 960, 350, pop(t, bt[0], 0.30), -2, t)
        for i, sp in enumerate(tg):
            place(c, k + "tag%d" % i, sp, spots[i][0], spots[i][1], pop(t, bt[1 + i]), spots[i][2], t)
        if sh:
            place(c, k + "sh", sh, 1690, 210, pop(t, bt[-1], 0.24), 8 + 6 * math.sin(t * 9), t)
        return c
    return fn


def std_photo(day, a, b, photo, title=None, figure=None, tags=(), shout=None, bg=(226, 228, 232), dots=(150, 150, 165),
              title_colors=(PURPLE, PINK), shout_color=RED):
    """「照片加标签」：左边一张手撕大照片，右边可选一个抠图人物，上面标题，最多三个标签，可选一个爆炸贴。
    例：std_photo(day, 36.6, 39.2, day.src("oracle_hq.jpg"), title="ORACLE", tags=["PATCH SHIPPED NOV 17", "UPDATE NOW"], shout="ON YOU!")"""
    k, back = _key(), _bg(bg, dots)
    ph = torn_photo(photo, 900, 580, border=20)
    ti = gradient_text(title, max(110, min(200, int(1500 / max(4, len(title))))), title_colors[0], title_colors[1], stroke=14, font=BLK) if title else None
    fg = cutout_sprite(figure, 640) if figure is not None else None
    tg = [tag(x, 56, fg=(60, 40, 110), bg=YELLOW if i == 0 else (255, 255, 255), outline=(255, 255, 255)) for i, x in enumerate(tags[:3])]
    sh = burst(shout, 170, fill=shout_color, fg=(255, 255, 255), size=int(min(84, 2.4 * 170 / max(4, len(shout))))) if shout else None
    bt = day.beats(a, b, len(tg) + (1 if sh else 0) + 1)
    spots = [(1400, 290, 4), (1430, 430, -3), (1420, 570, 2)] if fg is None else [(640, 770, 2), (1000, 330, -3), (1000, 480, 3)]

    def fn(t):
        c = back.copy()
        place(c, k + "ph", ph, 620, 500, pop(t, a + 0.06, 0.28), -2, t)
        if ti:
            place(c, k + "ti", ti, 640, 130, pop(t, a + 0.02), -2, t)
        if fg:
            place(c, k + "fg", fg, 1420, 600, pop(t, bt[0], 0.28), 0, t)
        for i, sp in enumerate(tg):
            place(c, k + "tag%d" % i, sp, spots[i][0], spots[i][1], pop(t, bt[1 + i] if 1 + i < len(bt) else bt[-1]), spots[i][2], t)
        if sh:
            place(c, k + "sh", sh, 1540, 690 if fg is None else 230, pop(t, bt[-1], 0.22), 8 + 6 * math.sin(t * 10), t)
        return c
    return fn
