#!/usr/bin/env python3
"""2026-11-17 这一天的画面：五张封面卡片 + 每句歌词一幕。骨架（封面页、时间轴、转场、结尾）在 scripts/daily_engine.py。

出片：      python3 这一天的画面.py
只看静帧：  python3 这一天的画面.py --stills <输出文件夹> 7.4 11.9 …
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from daily_engine import *  # noqa: E402,F401,F403

day = Day(HERE, os.path.join(HERE, "Wall Street Verse.m4a"), date="NOV 17", weekday="TUESDAY", year=2026, next_date="NOV 18")
src, cut = day.src, day.cut
BG1, clouds = day.bg, day.clouds   # "所有人盯着华尔街"那一幕借用封面页的底和云


# ---------- 歌词时间点（秒）：来自音频自带的字幕轨 + 量出来的鼓点 ----------
T_DATE, T_FIVE, T_MINUTE, T_GO, T_HEY, T_BUILD = 1.70, 3.45, 4.75, 6.25, 6.90, 8.00
T_NV, BEAT = 9.86, 0.485
T_GONE, T_KRESS, T_CROWN = T_NV + BEAT, T_NV + 2 * BEAT, T_NV + 3 * BEAT
T_REV, T_DOUBLE, T_NOTDOWN = 12.33, 13.44, 14.23
T_MON, T_BELL, T_BOOM = 14.80, 16.78, 17.25
T_ANT, T_A, T_N, T_T = 19.41, 20.35, 20.85, 21.33
T_PRICE, T_THU = 21.89, 23.15
T_RANGE, T_EYES = 24.30, 26.74
T_APPLE, T_DARK, T_ICLOUD, T_PAY, T_GONE2 = 29.24, 29.90, 30.25, 30.60, 31.20
T_STORE, T_JAVA, T_CRIT, T_ORACLE, T_YOU = 31.57, 34.26, 35.30, 36.62, 38.60
T_DEVIN, T_NIGHT, T_OUT, T_TOM, T_END = 39.24, 41.64, 44.16, 46.55, 49.45

print("准备素材……", file=sys.stderr)
SP = {}
SP["cloud1"], SP["cloud2"], SP["cloud3"] = cloud(760, 330, 1), cloud(560, 250, 2), cloud(430, 190, 3)
kress_cut = cut("kress.png")
_am = cut("amodei.png")
amodei_cut = _am.crop((0, 0, _am.width, int(_am.height * 0.70)))
_nq = src("nasdaq.jpg")
nasdaq_img = _nq.crop((int(_nq.width * 0.26), int(_nq.height * 0.60), int(_nq.width * 0.82), int(_nq.height * 0.90)))
apple_logo = src("apple_logo.png").convert("RGBA")
robot_cut = cut("robot.png")

# 封面页上的五张新闻卡片：一张手撕照片 + 压在上面的抠图 + 一句要点
SP["card0"] = card(src("nvidia_hq.jpg"), "NEW CEO + $115.8B", (64, 130, 10), fig=cutout_sprite(kress_cut, 270, stroke=9), fig_dx=34,
                   extra=[(crown(96).rotate(9, expand=True, resample=Image.BICUBIC), 6, -268)])
SP["card1"] = card(nasdaq_img, "IPO: $70 – $78", TERRA, fig=cutout_sprite(amodei_cut, 250, stroke=9), fig_dx=-58, centering=(0.75, 0.5),
                   extra=[(strip_with(src("anthropic_logo.png"), 230, 54), 44, -262)])
SP["card2"] = card(src("apple_park.jpg"), "SERVICES DOWN", (40, 40, 52), fig=cutout_sprite(apple_logo, 170, stroke=9), fig_dy=-48, darken=0.8,
                   extra=[(xmark(90), 62, -70)])
SP["card3"] = card(src("oracle_hq.jpg"), "JAVA4SHELL PATCH", (199, 60, 50), fig=cutout_sprite(cut("coffee.png"), 140, stroke=9), fig_dx=52,
                   extra=[(cutout_sprite(src("duke.png"), 190, stroke=8), -92, -92)])
SP["card4"] = card(night_bg((620, 600), with_moon=True), "DEVIN BOTS LAUNCH", (60, 70, 190), fig=cutout_sprite(robot_cut, 262, stroke=9))

# Nvidia 换帅
BG2 = paper((206, 228, 172))
_h2 = halftone((70, 140, 20), 0, 520, alpha=95, grow_down=False)
BG2.paste(_h2, (0, 0), _h2)
SP["hq"] = torn_photo(src("nvidia_hq.jpg"), 1180, 700, border=20)
SP["sign"] = cutout_sprite(cut("nvidia_sign.png"), 620)
SP["nvidia"] = gradient_text("NVIDIA", 210, (64, 130, 10), NV_GREEN, stroke=14, font=BLK)
_hu = cut("huang.png")
SP["huang"], SP["huang_gray"] = cutout_sprite(_hu, 740), cutout_sprite(_hu, 740, gray=True)
SP["huang_name"] = tag("JENSEN HUANG, FOUNDER", 38)
SP["resigned"] = tag("RESIGNED NOV 12", 54, fg=(255, 255, 255), bg=RED, outline=(255, 255, 255))
SP["kress"] = cutout_sprite(kress_cut, 760, color=1.2)
SP["kress_name"] = tag("COLETTE KRESS", 44)
SP["interim"] = tag("INTERIM CEO", 62, fg=(60, 40, 110), bg=YELLOW, outline=(255, 255, 255))
SP["crown"] = crown(230)

# Nvidia 收入
BG3 = paper((44, 92, 196))
_h3 = halftone((120, 170, 255), 380, 1080, alpha=120, grow_down=True)
BG3.paste(_h3, (0, 0), _h3)
SP["rev"] = gradient_text("$115.8B", 300, (255, 232, 90), (255, 150, 40), stroke=18)
SP["record"] = tag("RECORD QUARTERLY REVENUE", 50)
SP["chip1"] = torn_photo(src("gpu_card.png"), 330, 330)
SP["chip2"] = torn_photo(src("gpu_chip.jpg"), 300, 230)
BAR_BASE, BAR1_H, BAR2_H = 780, 170, 345   # 57.0 : 115.8 的高度比
SP["bar1"], SP["bar2"] = torn_rect(170, BAR1_H, (232, 226, 240)), torn_rect(190, BAR2_H, NV_GREEN)
SP["bar1_val"] = tag("$57.0B", 40)
SP["bar2_val"] = tag("$115.8B", 46, fg=(255, 255, 255), bg=(64, 130, 10), outline=(255, 255, 255))
SP["bar1_lab"], SP["bar2_lab"] = tag("Q3 LAST YEAR", 30), tag("Q3 THIS YEAR", 30)
SP["x2"] = burst("+103%", 150, fill=YELLOW, fg=(60, 40, 110), size=76)
SP["doubled"] = tag("REVENUE DOUBLED", 66, fg=(255, 255, 255), bg=PURPLE, outline=(255, 255, 255))
SP["notdown"] = bubble("NOT DOWN!", 70)

# 周一纳斯达克下跌，盘后回升
BG_RED = paper((206, 64, 70))
_hr = halftone((150, 30, 40), 400, 1080, alpha=120, grow_down=True)
BG_RED.paste(_hr, (0, 0), _hr)
SP["nasdaq_big"] = torn_photo(nasdaq_img, 760, 480, border=20)
SP["monday"] = tag("MONDAY, NOV 16", 60, fg=RED)
SP["pct"] = gradient_text("-2.49%", 210, (140, 16, 30), (230, 60, 70), stroke=18)
SP["composite"] = tag("NASDAQ COMPOSITE", 50, fg=RED)
SP["down"] = arrow(False, (120, 14, 28))
SP["bell"] = bell(230)
SP["afterbell"] = tag("AFTER THE BELL...", 50, fg=(60, 40, 110), bg=YELLOW, outline=(255, 255, 255))
BG_GRN = paper((64, 168, 92))
_hg = halftone((190, 240, 190), 0, 560, alpha=110, grow_down=False)
BG_GRN.paste(_hg, (0, 0), _hg)
SP["boom"] = burst("BOOM!", 200, fill=YELLOW, fg=RED, size=92)
SP["up"] = arrow(True, (255, 255, 255), w=280, h=460)
SP["nvda_up"] = tag("NVDA UP AFTER HOURS", 64, fg=(40, 120, 50))
SP["climb"] = tag("CLIMBING AGAIN", 60, fg=(60, 40, 110), bg=YELLOW, outline=(255, 255, 255))
SP["sign_s"] = cutout_sprite(cut("nvidia_sign.png"), 470)

# Anthropic 上市
BG_ANT = paper((238, 220, 198))
_ha = halftone(TERRA, 0, 460, alpha=90, grow_down=False)
BG_ANT.paste(_ha, (0, 0), _ha)
BG_ANT2 = paper((238, 220, 198))
_ha2 = halftone(TERRA, 560, 1080, alpha=90, grow_down=True)
BG_ANT2.paste(_ha2, (0, 0), _ha2)
SP["ant_logo"] = strip_with(src("anthropic_logo.png"), 860, 140)
SP["ant_logo_s"] = strip_with(src("anthropic_logo.png"), 430, 76)
SP["amodei"] = cutout_sprite(amodei_cut, 640)
SP["amodei_name"] = tag("DARIO AMODEI, CEO", 38)
SP["nasdaq_mid"] = torn_photo(nasdaq_img, 560, 400, border=18)
SP["tA"], SP["tN"], SP["tT"] = tile("A", TERRA), tile("N", TERRA), tile("T", TERRA)
SP["ticker"] = tag("NASDAQ TICKER", 50, fg=TERRA)
SP["pricetag"] = pricetag()
SP["cal18"] = calendar("WED", "18", "PRICING", TERRA)
SP["cal19"] = calendar("THU", "19", "TRADING", PURPLE)
SP["nov2026"] = tag("NOVEMBER 2026", 54, fg=TERRA)
SP["cnbc"] = tag("DATES AS REPORTED BY CNBC", 34, fg=(120, 100, 90))
SP["yousee"] = bubble("YOU'LL SEE!", 62)
SP["range"] = gradient_text("$70 – $78", 300, (150, 60, 40), TERRA, stroke=18)
SP["range_bar"] = torn_rect(1000, 54, TERRA)
SP["r70"], SP["r78"] = tag("$70", 56, fg=TERRA), tag("$78", 56, fg=TERRA)
SP["pershare"] = tag("IPO PRICE RANGE, PER SHARE", 54, fg=(255, 255, 255), bg=TERRA, outline=(255, 255, 255))
SP["ant_tag"] = tag("ANTHROPIC (ANT)", 54, fg=TERRA)
SP["skyline"] = skyline_sprite()
SP["water"] = water_strip()
SP["wallst"] = torn_photo(src("wallst_sign.jpg").crop((600, 380, 1500, 1020)), 600, 420, border=18)
SP["nyse"] = torn_photo(src("nyse2.jpg"), 360, 450, centering=(0.72, 0.30))
SP["eye_a"], SP["eye_b"], SP["eye_c"] = eye(95), eye(70, iris=(110, 70, 40)), eye(120, iris=(60, 150, 110))
SP["alleyes"] = tag("ALL EYES ON WALL STREET", 64, fg=(255, 255, 255), bg=PURPLE, outline=(255, 255, 255))
EYES = [(250, 190, "eye_a"), (640, 150, "eye_b"), (1330, 170, "eye_c"), (1700, 260, "eye_a"), (1560, 540, "eye_b"),
        (1790, 720, "eye_c"), (120, 500, "eye_b"), (640, 760, "eye_a"), (1300, 800, "eye_b")]

# Apple 服务中断
BG_GRAY = paper((226, 228, 232))
_hy = halftone((150, 150, 165), 0, 500, alpha=90, grow_down=False)
BG_GRAY.paste(_hy, (0, 0), _hy)
SP["park"] = torn_photo(src("apple_park.jpg"), 980, 640, border=20)
SP["apple"] = cutout_sprite(apple_logo, 360)
SP["nov17"] = tag("TUESDAY, NOV 17", 50)
SP["icloud"] = tag("iCLOUD", 80)
SP["applepay"] = tag("APPLE PAY", 80)
SP["x"] = xmark(150)
SP["gone"] = burst("GONE!", 190, fill=RED, fg=(255, 255, 255), size=84)
BLACK = Image.new("RGB", (W, H), (8, 8, 20))
BG_ICE = paper((190, 224, 246))
_hi = halftone((255, 255, 255), 300, 1080, alpha=140, grow_down=True)
BG_ICE.paste(_hi, (0, 0), _hi)
SP["phone"] = phone()
SP["ice"] = icicles()
SP["frozen"] = gradient_text("FROZEN", 240, (30, 110, 220), (110, 200, 250), stroke=18, font=BLK)
SP["clock"] = clock()
SP["peak"] = tag("OUTAGE REPORTS PEAKED 12:29 PM ET", 40)
SP["holdon"] = bubble("HOLD ON!", 66)
SNOW = [(random.Random(40 + i).uniform(0, W), random.Random(80 + i).uniform(31.4, 33.6), random.Random(120 + i).uniform(120, 260),
         random.Random(160 + i).uniform(8, 18)) for i in range(46)]

# Java4Shell
BG_JAVA = paper((150, 34, 44))
_hj = halftone((230, 110, 50), 420, 1080, alpha=110, grow_down=True)
BG_JAVA.paste(_hj, (0, 0), _hj)
SP["j4s"] = gradient_text("JAVA4SHELL", 200, (255, 240, 200), (255, 180, 60), stroke=16, font=BLK)
SP["coffee"] = cutout_sprite(cut("coffee.png"), 380)
SP["duke"] = cutout_sprite(src("duke.png"), 440)
SP["critical"] = burst("CRITICAL", 220, fill=YELLOW, fg=RED, size=70)
SP["cve"] = tag("CVE-2026-114938", 48, fg=RED)
SP["rce"] = tag("REMOTE CODE EXECUTION", 46, fg=RED)
BG_ORA = paper((240, 232, 214))
_ho = halftone((199, 60, 50), 0, 440, alpha=80, grow_down=False)
BG_ORA.paste(_ho, (0, 0), _ho)
SP["ora_logo"] = strip_with(src("oracle_logo.png"), 600, 120)
SP["ora_hq"] = torn_photo(src("oracle_hq.jpg"), 900, 580, border=20)
SP["bandaid"] = bandaid()
SP["shipped"] = tag("PATCH SHIPPED NOV 17", 54, fg=(255, 255, 255), bg=(199, 60, 50), outline=(255, 255, 255))
SP["update"] = tag("UPDATE NOW", 88, fg=(60, 40, 110), bg=YELLOW, outline=(255, 255, 255))
SP["onyou"] = burst("ON YOU!", 200, fill=RED, fg=(255, 255, 255), size=72)

# Devin Bots
BG_NIGHT = night_bg((W, H))
SP["moon"] = moon(120)
SP["devin"] = gradient_text("DEVIN BOTS", 200, (90, 200, 255), (170, 120, 255), stroke=16, font=BLK)
SP["cognition"] = tag("BY COGNITION", 50)
SP["robot0"] = cutout_sprite(robot_cut, 520)
SP["robot1"] = cutout_sprite(ImageOps.mirror(robot_cut), 430)
SP["robot2"] = cutout_sprite(robot_cut, 350)
SP["neversleep"] = tag("AGENTS NEVER SLEEP", 58, fg=(60, 40, 110), bg=YELLOW, outline=(255, 255, 255))
SP["allnight"] = tag("SHIPPING CODE ALL NIGHT", 58, fg=(255, 255, 255), bg=(60, 70, 190), outline=(255, 255, 255))
for _i in range(6):
    SP["code%d" % _i] = code_card(_i)
SP["sheep"], SP["fence"] = sheep(), fence()
SP["zzz"] = gradient_text("Zzz", 110, (255, 255, 255), (200, 210, 255), stroke=8)
SP["count"] = tag("HUMANS COUNT SHEEP", 46)
ROBOTS = [("robot0", 360, 520, 39.55), ("robot1", 800, 430, 39.95), ("robot2", 1190, 350, 40.35)]

CONFETTI = []
_r = random.Random(3)
for _ in range(80):
    CONFETTI.append((_r.uniform(0, W), _r.uniform(12.35, 13.6), _r.uniform(260, 560), _r.uniform(0, 6.28),
                     _r.choice([(255, 214, 60), (240, 80, 70), (255, 255, 255), (118, 185, 0), (196, 64, 150)]), _r.uniform(10, 20)))


# ---------- 每句歌词的那一幕 ----------
def nv_ceo(t):
    c = BG2.copy()
    place(c, "cloud2b", SP["cloud2"], 1560 - (t - 9.5) * 10, 120)
    place(c, "hq", SP["hq"], 1040, 470, 0.9 + 0.1 * ease_out((t - 9.55) / 0.4), 2, t)
    place(c, "sign", SP["sign"], 250, 620, pop(t, T_NV + 0.05), -3, t)
    place(c, "nvidia", SP["nvidia"], 640, 150, pop(t, T_NV, 0.26), -3, t)
    te = clamp01((t - (T_GONE + 0.12)) / 0.55)   # 唱到 "Founder's gone"：变灰、向下滑出画面
    hx, hy, hrot = 760 - 160 * ease_in(te), 610 + 1000 * ease_in(te), 18 * ease_in(te)
    place(c, "huang", SP["huang_gray"] if t >= T_GONE else SP["huang"], hx, hy, pop(t, T_NV, 0.28), hrot, t)
    place(c, "huang_name", SP["huang_name"], hx, hy + 170, pop(t, T_NV + 0.12) if te < 1 else 0, hrot - 2, t)
    place(c, "resigned", SP["resigned"], hx + 10, hy + 60, pop(t, T_GONE, 0.22) if te < 1 else 0, hrot - 8, t)
    kx, ky = 1340, 590
    place(c, "kress", SP["kress"], kx, ky, pop(t, T_KRESS, 0.30), 0, t)
    if t >= T_CROWN - 0.24:   # 皇冠落到头上
        cy = ky - 388 - (1 - bounce((t - (T_CROWN - 0.24)) / 0.42)) * 520
        place(c, "crown", SP["crown"], kx - 86, cy, 1, 9, t)
    place(c, "interim", SP["interim"], 1640, 380, pop(t, T_CROWN + 0.12), -6, t)
    place(c, "kress_name", SP["kress_name"], kx + 10, 770, pop(t, T_KRESS + 0.2), 2, t)
    return c


def nv_rev(t):
    c = BG3.copy()
    place(c, "cloud3c", SP["cloud3"], 250 - (t - 12) * 12, 520)
    place(c, "record", SP["record"], 620, 100, pop(t, T_REV + 0.14), -2, t)
    place(c, "chip1", SP["chip1"], 270, 690, pop(t, T_REV + 0.45), -9, t)
    place(c, "chip2", SP["chip2"], 570, 740, pop(t, T_REV + 0.70), 7, t)
    for key, x, full, t0 in (("bar1", 1440, BAR1_H, T_REV + 0.45), ("bar2", 1670, BAR2_H, T_REV + 0.70)):
        g = ease_out((t - t0) / 0.5)
        if g > 0.02:
            im = SP[key]
            vis = max(8, int(im.height * g))
            part = im.crop((0, 0, im.width, vis))
            c.paste(part, (int(x - im.width / 2), int(BAR_BASE - vis + 46)), part)
        place(c, key + "_val", SP[key + "_val"], x, BAR_BASE - full * g - 30, pop(t, t0 + 0.35), 0, t)
        place(c, key + "_lab", SP[key + "_lab"], x, BAR_BASE + 28, pop(t, t0 + 0.1), 0, t)
    place(c, "rev", SP["rev"], 760, 320, pop(t, T_REV, 0.30), -2, t)
    place(c, "doubled", SP["doubled"], 900, 560, pop(t, T_DOUBLE), -3, t)
    place(c, "x2", SP["x2"], 1100, 740, pop(t, T_DOUBLE + 0.2, 0.26), 8 + 5 * math.sin(t * 8), t)
    place(c, "notdown", SP["notdown"], 1640, 230, pop(t, T_NOTDOWN, 0.24), 6, t)
    d = ImageDraw.Draw(c)
    for x, t0, v, ph, col, s in CONFETTI:
        y = -20 + (t - t0) * v
        if t < t0 or y > H + 20:
            continue
        a = ph + t * 5
        xx = x + 30 * math.sin(a * 0.7)
        dx, dy = s * math.cos(a), s * math.sin(a)
        ex, ey = -dy * 0.45, dx * 0.45
        d.polygon([(xx - dx - ex, y - dy - ey), (xx + dx - ex, y + dy - ey), (xx + dx + ex, y + dy + ey), (xx - dx + ex, y - dy + ey)], fill=col)
    return c


def nasdaq_red(t):
    c = BG_RED.copy()
    place(c, "nasdaq_big", SP["nasdaq_big"], 470, 420, pop(t, T_MON - 0.05), -3, t)
    place(c, "monday", SP["monday"], 1300, 130, pop(t, T_MON + 0.05), 2, t)
    place(c, "pct", SP["pct"], 1300, 340, pop(t, T_MON + 0.50, 0.28), -2, t)
    place(c, "composite", SP["composite"], 1250, 540, pop(t, T_MON + 1.15), -2, t)
    dy = (1 - bounce((t - 15.55) / 0.45)) * 900
    if t > 15.55:
        place(c, "down", SP["down"], 1740, 650 - dy, 1, 0, t)
    if t >= T_BELL:
        swing = 16 * math.sin((t - T_BELL) * 16) * max(0, 1 - (t - T_BELL) / 0.9)
        place(c, "bell", SP["bell"], 760, 760, pop(t, T_BELL, 0.24), swing, t)
        place(c, "afterbell", SP["afterbell"], 1180, 770, pop(t, T_BELL + 0.12), -3, t)
    return c


def nasdaq_green(t):
    c = BG_GRN.copy()
    place(c, "cloud2g", SP["cloud2"], 1500 - (t - 17) * 12, 150)
    place(c, "boom", SP["boom"], 430, 330, pop(t, T_BOOM, 0.24), 8 + 6 * math.sin(t * 10), t)
    place(c, "sign_s", SP["sign_s"], 860, 690, pop(t, T_BOOM + 0.15), 3, t)
    rise = (1 - ease_out((t - (T_BOOM + 0.2)) / 0.6)) * 900
    place(c, "up", SP["up"], 1560, 560 + rise - 14 * math.sin(t * 4), 1, 0, t)
    place(c, "nvda_up", SP["nvda_up"], 1060, 220, pop(t, T_BOOM + 0.40), -2, t)
    place(c, "climb", SP["climb"], 1120, 420, pop(t, 18.40), 3, t)
    place(c, "chip1g", SP["chip1"], 380, 720, pop(t, T_BOOM + 0.55), -8, t)
    return c


def ant_ticker(t):
    c = BG_ANT.copy()
    place(c, "ant_logo", SP["ant_logo"], 700, 140, pop(t, T_ANT - 0.02, 0.28), -2, t)
    place(c, "nasdaq_mid", SP["nasdaq_mid"], 1560, 430, pop(t, T_ANT + 0.30), 3, t)
    place(c, "amodei", SP["amodei"], 330, 600, pop(t, T_ANT + 0.15), 0, t)
    place(c, "amodei_name", SP["amodei_name"], 340, 760, pop(t, T_ANT + 0.40), -2, t)
    for key, x, t0, rot in (("tA", 800, T_A, -5), ("tN", 985, T_N, 3), ("tT", 1170, T_T, -4)):
        place(c, key, SP[key], x, 470, pop(t, t0, 0.24), rot, t)
    place(c, "ticker", SP["ticker"], 985, 680, pop(t, T_T + 0.22), 2, t)
    return c


def ant_dates(t):
    c = BG_ANT2.copy()
    place(c, "ant_logo_s", SP["ant_logo_s"], 290, 100, 1, -2, t)
    place(c, "nov2026", SP["nov2026"], 1050, 170, pop(t, T_PRICE + 0.05), 2, t)
    place(c, "pricetag", SP["pricetag"], 400, 440, pop(t, T_PRICE + 0.08), -12 + 8 * math.sin(t * 6), t)
    place(c, "cal18", SP["cal18"], 860, 480, pop(t, T_PRICE + 0.40), -4, t)
    place(c, "cal19", SP["cal19"], 1240, 500, pop(t, T_THU), 4, t)
    place(c, "cnbc", SP["cnbc"], 1050, 770, pop(t, T_THU + 0.2), 0, t)
    place(c, "yousee", SP["yousee"], 1630, 300, pop(t, 23.60, 0.24), 6, t)
    return c


def ant_range(t):
    c = BG_ANT.copy()
    place(c, "ant_tag", SP["ant_tag"], 960, 110, pop(t, T_RANGE + 0.02), -2, t)
    place(c, "range", SP["range"], 960, 340, pop(t, T_RANGE + 0.10, 0.30), -2, t)
    g = ease_out((t - 25.20) / 0.55)
    if g > 0.02:
        im = SP["range_bar"]
        part = im.crop((0, 0, max(8, int(im.width * g)), im.height))
        c.paste(part, (int(960 - im.width / 2), int(620 - im.height / 2)), part)
    place(c, "r70", SP["r70"], 440, 620, pop(t, 25.25), -4, t)
    place(c, "r78", SP["r78"], 1480, 620, pop(t, 25.70), 4, t)
    place(c, "pershare", SP["pershare"], 960, 770, pop(t, 25.95), 2, t)
    return c


def ant_eyes(t):
    c = BG1.copy()
    clouds(c, t, 26.5)
    sk = SP["skyline"]
    place(c, "skyline", sk, 960, 872 - sk.height / 2 + 44)
    place(c, "water", SP["water"], 960, 985)
    place(c, "nyse", SP["nyse"], 330, 560, pop(t, T_EYES + 0.10), -5, t)
    place(c, "wallst", SP["wallst"], 980, 430, pop(t, T_EYES + 0.02, 0.28), 3, t)
    for i, (x, y, key) in enumerate(EYES):
        s = pop(t, T_EYES + 0.20 + 0.13 * i, 0.22) * (1 + 0.05 * math.sin(t * 7 + i))
        place(c, "eye%d" % i, SP[key], x, y, s, (i * 37) % 21 - 10, t)
    place(c, "alleyes", SP["alleyes"], 960, 730, pop(t, 28.40, 0.26), -2, t)
    return c


def apple_dark(t):
    c = BG_GRAY.copy()
    place(c, "park", SP["park"], 720, 470, pop(t, T_APPLE - 0.04, 0.28), -2, t)
    place(c, "apple", SP["apple"], 1560, 320, pop(t, T_APPLE + 0.12), 4, t)
    f = 0.66 * ease_io((t - (T_DARK - 0.15)) / 0.3)   # "went dark"：整张画暗下去
    if f > 0.01:
        c = Image.blend(c, BLACK, f)
    place(c, "nov17", SP["nov17"], 330, 110, pop(t, T_APPLE + 0.06), -3, t)
    place(c, "icloud", SP["icloud"], 470, 310, pop(t, T_ICLOUD, 0.22), -5, t)
    place(c, "x1", SP["x"], 740, 300, pop(t, T_ICLOUD + 0.16, 0.18), 6, t)
    place(c, "applepay", SP["applepay"], 860, 580, pop(t, T_PAY, 0.22), 4, t)
    place(c, "x2m", SP["x"], 1200, 575, pop(t, T_PAY + 0.16, 0.18), -8, t)
    place(c, "gone", SP["gone"], 1540, 720, pop(t, T_GONE2, 0.22), 8 + 6 * math.sin(t * 10), t)
    return c


def apple_frozen(t):
    c = BG_ICE.copy()
    place(c, "phone", SP["phone"], 480, 500, pop(t, T_STORE + 0.02, 0.28), -6, t)
    g = ease_out((t - 32.05) / 0.5)
    if g > 0.02:
        im = SP["ice"].rotate(6, resample=Image.BICUBIC, expand=True)
        part = im.crop((0, 0, im.width, max(8, int(im.height * g))))
        c.paste(part, (int(450 - im.width / 2), 150), part)
    place(c, "frozen", SP["frozen"], 1240, 260, pop(t, 32.10, 0.28), -3, t)
    place(c, "clock", SP["clock"], 1020, 600, pop(t, 32.85), -6, t)
    place(c, "peak", SP["peak"], 1340, 770, pop(t, 33.05), -1, t)
    place(c, "holdon", SP["holdon"], 1600, 540, pop(t, 33.65, 0.24), 6, t)
    d = ImageDraw.Draw(c)
    for x, t0, v, s in SNOW:
        y = -20 + (t - t0) * v
        if t < t0 or y > H:
            continue
        xx = x + 20 * math.sin(t * 2 + x)
        for k in range(3):
            a = k * math.pi / 3 + t
            d.line([xx - s * math.cos(a), y - s * math.sin(a), xx + s * math.cos(a), y + s * math.sin(a)], fill=(255, 255, 255), width=4)
    return c


def java_crit(t):
    c = BG_JAVA.copy()
    place(c, "j4s", SP["j4s"], 960, 170, pop(t, T_JAVA + 0.04, 0.28), -2, t)
    place(c, "duke", SP["duke"], 250, 610, pop(t, T_JAVA + 0.34), -6 + 4 * math.sin(t * 6), t)
    place(c, "coffee", SP["coffee"], 700, 650, pop(t, T_JAVA + 0.18), 2, t)
    place(c, "rce", SP["rce"], 1010, 390, pop(t, 35.75), -2, t)
    place(c, "critical", SP["critical"], 1560, 620, pop(t, T_CRIT, 0.22) * (1 + 0.04 * math.sin(t * 14)), -8, t)
    place(c, "cve", SP["cve"], 1090, 760, pop(t, 36.0), 2, t)
    return c


def java_patch(t):
    c = BG_ORA.copy()
    place(c, "ora_logo", SP["ora_logo"], 560, 110, pop(t, T_ORACLE + 0.02), -2, t)
    place(c, "ora_hq", SP["ora_hq"], 620, 500, pop(t, T_ORACLE + 0.08, 0.28), -2, t)
    if t >= 37.15:   # 创可贴"啪"地贴上去
        s = 1 + 1.3 * (1 - ease_out((t - 37.15) / 0.16))
        place(c, "bandaid", SP["bandaid"], 640, 520, s, 18, t)
    place(c, "shipped", SP["shipped"], 640, 760, pop(t, 37.40), 2, t)
    place(c, "update", SP["update"], 1440, 330, pop(t, 38.00, 0.26), 4, t)
    place(c, "onyou", SP["onyou"], 1480, 650, pop(t, T_YOU, 0.22), 8 + 6 * math.sin(t * 10), t)
    return c


def devin(t):
    c = BG_NIGHT.copy()
    place(c, "moon", SP["moon"], 1720, 170, 1, 0)
    place(c, "devin", SP["devin"], 740, 150, pop(t, T_DEVIN + 0.04, 0.30), -2, t)
    place(c, "cognition", SP["cognition"], 1260, 285, pop(t, T_DEVIN + 0.35), 3, t)
    place(c, "fence", SP["fence"], 1560, 760, pop(t, T_NIGHT + 0.5), 0, t)
    for i in range(3):   # 人类在数的羊：从右往左跳过栅栏
        t0 = 42.35 + 0.55 * i
        p = (t - t0) / 1.1
        if 0 < p < 1:
            place(c, "sheep%d" % i, SP["sheep"], 1900 - 660 * p, 690 - 230 * math.sin(math.pi * p), 1, 18 - 36 * p)
    place(c, "count", SP["count"], 1560, 490, pop(t, 42.75), -3, t)
    place(c, "zzz", SP["zzz"], 1800, 370, pop(t, 43.10) * (1 + 0.06 * math.sin(t * 5)), 10, t)
    for key, x, h, t0 in ROBOTS:   # 机器人一个一个落地
        if t >= t0:
            y = 830 - h / 2 - (1 - bounce((t - t0) / 0.45)) * 900
            place(c, key, SP[key], x, y, 1, 3 * math.sin(t * 5 + x), t)
    for i in range(6):   # 整晚往外发的代码
        k = i % 3
        t0 = T_NIGHT + 0.10 + 0.36 * i
        p = (t - t0) / 1.5
        if 0 < p < 1:
            _, x, h, _ = ROBOTS[k]
            place(c, "code%d" % i, SP["code%d" % i], x + 60 * math.sin(p * 4 + i), 830 - h - 40 - 520 * ease_out(p), min(1, p * 5) * (1 - ease_in(p)), -8 + 16 * p)
    if t < T_NIGHT:
        place(c, "neversleep", SP["neversleep"], 980, 400, pop(t, 40.85), -3, t)
    else:
        place(c, "neversleep", SP["neversleep"], 980, 400, hide(t, T_NIGHT), -3, t)
        place(c, "allnight", SP["allnight"], 520, 300, pop(t, T_NIGHT + 0.12), -3, t)
    return c


# ---------- 登记：封面页的时刻、五条新闻、每句歌词的那一幕、结尾 ----------
day.intro(date=T_DATE, five=T_FIVE, minute=T_MINUTE, go=T_GO, hey=T_HEY, build=T_BUILD)
for _i, (_name, _arrive) in enumerate(zip(["NVIDIA", "ANTHROPIC", "APPLE", "JAVA", "DEVIN"], [T_NV, T_ANT, T_APPLE, T_JAVA, T_DEVIN])):
    day.headline(_name, SP["card%d" % _i], _arrive)
for _start, _fn, _enter, _dur in [
        (9.50, nv_ceo, "tear", 0.40), (12.18, nv_rev, "sheet", 0.24), (14.68, nasdaq_red, "sheet", 0.22),
        (17.13, nasdaq_green, "tear", 0.30), (19.22, ant_ticker, "sheet", 0.24), (21.76, ant_dates, "sheet", 0.22),
        (24.16, ant_range, "sheet", 0.22), (26.58, ant_eyes, "tear", 0.32), (29.06, apple_dark, "sheet", 0.24),
        (31.43, apple_frozen, "sheet", 0.22), (34.10, java_crit, "tear", 0.30), (36.48, java_patch, "sheet", 0.22),
        (39.02, devin, "sheet", 0.40)]:
    day.scene(_start, _fn, _enter, _dur)
day.subtitles(
    key=["seventeen", "five", "headlines", "one", "minute", "Nvidia", "gone", "Kress", "crown", "Hundred-fifteen", "billion", "doubled",
         "Monday", "red", "Nasdaq", "boom", "climbing", "Anthropic", "A-N-T", "tomorrow", "Thursday", "Seventy", "seventy-eight",
         "Wall", "Street", "Apple", "dark", "iCloud", "Pay", "Gone", "App", "Store", "frozen", "Java", "Four-Shell", "critical",
         "Oracle", "patch", "you", "Cognition", "Devin", "Bots", "never", "sleep", "sheep", "news", "beat", "day", "Tomorrow", "verse"],
    anchors={0: {0: T_DATE, 3: T_FIVE, 5: T_MINUTE, 7: T_GO, 8: T_HEY},            # November … five … one … go! (Hey!)
             1: {0: T_NV, 1: T_GONE - 0.15, 3: T_KRESS, 7: T_CROWN + 0.25},      # Nvidia! Founder's … Kress … crown
             15: {0: 44.30, 3: 44.95, 6: 45.55, 9: 46.05},                         # That's the news / beat / day / (Hey!)
             16: {0: T_TOM + 0.05, 5: 48.20}},                                    # Tomorrow … the same way
    # 中文字幕：每句歌词一条；| 切纸片，* 是重点词，@数字 是和英文第几个词同时亮
    zh=["十一月十七日*@0 | 五条头条*@3 | 一分钟*@5 | 开始！*@7 | （嘿！）@8",
        "英伟达！*@0 | 创始人@1 | 走了，*@2 | Kress*@3 | 接过@5 | 王冠*@7",
        "$115B*@0 | 营收@3 | 翻倍，*@4 | 不是下跌！@5",
        "周一*@0 | 一片血红，*@2 | 整个@4 | 纳斯达克*@5 | 都在疼@7",
        "收盘之后@1 | ——砰！*@5 | 又@7 | 涨回来了！*@8",
        "Anthropic，*@0 | 股票代码@1 | A-N-T*@2",
        "明天定价，*@0 | 周四*@3 | 开始交易，@4 | 等着看！@5",
        "70*@0 | 到@1 | 78 美元，*@2 | 这就是@3 | 发行文件上的@5 | 区间*@8",
        "全世界的目光@0 | 都盯着@5 | 华尔街！*@7",
        "苹果*@0 | 黑屏了！*@2 | （iCloud！）*@3 | Apple Pay！*@4 | （没了！）*@6",
        "App Store*@0 | 大中午@3 | 卡住不动*@6 | ——撑住！@10",
        "Java4Shell 漏洞，*@0 | 严重级别，*@2 | 9.2 分@3",
        "Oracle*@0 | 发了补丁*@1 | ——接下来@5 | 更新*@7 | 靠你自己！*@8",
        "Cognition*@0 | 发布@1 | Devin Bots，*@2 | 智能体@4 | 从不睡觉*@5",
        "整夜@0 | 都在发代码，*@1 | 人类@6 | 还在数羊*@7",
        "这就是新闻！*@0 | 这就是节拍！*@3 | 这就是今天！*@6 | （嘿！）@9",
        "明天*@0 | 再写@1 | 新的一段*@3 | 还是老样子@5"])
day.outro(44.00, [("THAT'S THE NEWS!", T_OUT + 0.14), ("THAT'S THE BEAT!", 44.95), ("THAT'S THE DAY!", 45.55)],
          hey=46.05, tomorrow=T_TOM, sameway=48.20, plane_leaves=47.4)

if __name__ == "__main__":
    day.run(name="每日新闻_2026-11-17_完整版.mp4")
