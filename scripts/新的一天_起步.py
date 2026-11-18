#!/usr/bin/env python3
"""新的一天从这里起步：把这个文件复制到当天文件夹，改名叫「这一天的画面.py」，改带 ← 的地方。

这份起步文件里填的是 2026-11-17 的内容，并且全部用标准画面、全部用自动卡点，
所以它本身就能在 2026-11-17 文件夹里跑通，可以当例子对照着改。

出片：      python3 这一天的画面.py
只看静帧：  python3 这一天的画面.py --stills <输出文件夹> 7.4 11.9 …
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from daily_engine import *  # noqa: E402,F401,F403

day = Day(HERE, os.path.join(HERE, "Wall Street Verse.m4a"),          # ← 当天的音频文件名
          date="NOV 17", weekday="TUESDAY", year=2026, next_date="NOV 18")   # ← 日期
src, cut = day.src, day.cut   # src("x.jpg") 读 素材下载/ 里的原图，cut("x.png") 读 抠图/ 里抠好的图

for _i, (_a, _b, _text) in enumerate(day.lines):   # 先看每句歌词的序号和起止时间
    print("%2d  %5.2f – %5.2f  %s" % (_i, _a, _b, _text), file=sys.stderr)


def span(i, j=None):
    """第 i 句（到第 j 句）歌词的起止时间。"""
    return day.line(i)[0], day.line(i if j is None else j)[1]


# ---------- 一、封面卡片：每条新闻一张（照片 + 抠图 + 一句要点）；第三项是这条新闻的第一句歌词是第几句 ----------  ←
_am = cut("amodei.png")
HEADLINES = [
    ("NVIDIA", card(src("nvidia_hq.jpg"), "NEW CEO + $115.8B", (64, 130, 10), fig=cutout_sprite(cut("kress.png"), 270, stroke=9)), 1),
    ("ANTHROPIC", card(src("nasdaq.jpg"), "IPO: $70 – $78", TERRA, fig=cutout_sprite(_am.crop((0, 0, _am.width, int(_am.height * 0.7))), 250, stroke=9)), 5),
    ("APPLE", card(src("apple_park.jpg"), "SERVICES DOWN", (40, 40, 52), fig=cutout_sprite(src("apple_logo.png").convert("RGBA"), 170, stroke=9), fig_dy=-48, darken=0.8), 9),
    ("JAVA", card(src("oracle_hq.jpg"), "JAVA4SHELL PATCH", (199, 60, 50), fig=cutout_sprite(cut("coffee.png"), 140, stroke=9)), 11),
    ("DEVIN", card(night_bg((620, 600), with_moon=True), "DEVIN BOTS LAUNCH", (60, 70, 190), fig=cutout_sprite(cut("robot.png"), 262, stroke=9)), 13),
]
for _name, _sprite, _first in HEADLINES:
    day.headline(_name, _sprite, arrive=day.line(_first)[0] + 0.25)

# ---------- 二、每句歌词一幕：(第几句, 怎么进场, 画面) ----------  ←
# 标准画面有两种：std_number（大数字）和 std_photo（照片加标签）。
# 想要专门的画面（皇冠落到头上、创可贴贴上去这类），自己写一个 f(t) 返回一张图，写法见 2026-11-17/这一天的画面.py。
SCENES = [
    (1, "tear", lambda a, b: std_photo(day, a, b, src("nvidia_hq.jpg"), title="NVIDIA", figure=cut("kress.png"),
                                       tags=["COLETTE KRESS", "INTERIM CEO"], bg=(206, 228, 172), dots=(70, 140, 20), title_colors=((64, 130, 10), NV_GREEN))),
    (2, "sheet", lambda a, b: std_number(day, a, b, "$115.8B", label="RECORD QUARTERLY REVENUE", tags=["REVENUE DOUBLED"], shout="+103%")),
    (3, "sheet", lambda a, b: std_number(day, a, b, "-2.49%", label="NASDAQ, MONDAY NOV 16", bg=(206, 64, 70), dots=(150, 30, 40),
                                         colors=((140, 16, 30), (230, 60, 70)))),
    (4, "tear", lambda a, b: std_photo(day, a, b, src("gpu_card.png"), title="NVDA", tags=["UP AFTER HOURS", "CLIMBING AGAIN"], shout="BOOM!",
                                       bg=(64, 168, 92), dots=(190, 240, 190), shout_color=(240, 150, 30))),
    (5, "sheet", lambda a, b: std_photo(day, a, b, src("nasdaq.jpg"), title="ANTHROPIC", figure=cut("amodei.png"),
                                        tags=["NASDAQ TICKER: ANT"], bg=(238, 220, 198), dots=TERRA, title_colors=((150, 60, 40), TERRA))),
    (6, "sheet", lambda a, b: std_number(day, a, b, "NOV 18 + 19", label="PRICING, THEN TRADING", tags=["DATES AS REPORTED BY CNBC"],
                                         bg=(238, 220, 198), dots=TERRA, colors=((150, 60, 40), TERRA))),
    (7, "sheet", lambda a, b: std_number(day, a, b, "$70 – $78", label="ANTHROPIC (ANT)", tags=["IPO PRICE RANGE, PER SHARE"],
                                         bg=(238, 220, 198), dots=TERRA, colors=((150, 60, 40), TERRA))),
    (8, "tear", lambda a, b: std_photo(day, a, b, src("wallst_sign.jpg"), tags=["ALL EYES ON WALL STREET"])),
    (9, "sheet", lambda a, b: std_photo(day, a, b, src("apple_park.jpg"), title="APPLE", tags=["iCLOUD", "APPLE PAY"], shout="GONE!")),
    (10, "sheet", lambda a, b: std_number(day, a, b, "FROZEN", label="APP STORE", tags=["REPORTS PEAKED 12:29 PM ET"], shout="HOLD ON!",
                                          bg=(190, 224, 246), dots=(255, 255, 255), colors=((30, 110, 220), (110, 200, 250)))),
    (11, "tear", lambda a, b: std_number(day, a, b, "JAVA4SHELL", label="CVE-2026-114938", tags=["REMOTE CODE EXECUTION"], shout="CRITICAL",
                                         bg=(150, 34, 44), dots=(230, 110, 50), colors=((255, 240, 200), (255, 180, 60)))),
    (12, "sheet", lambda a, b: std_photo(day, a, b, src("oracle_hq.jpg"), title="ORACLE", tags=["PATCH SHIPPED NOV 17", "UPDATE NOW"], shout="ON YOU!",
                                         bg=(240, 232, 214), dots=(199, 60, 50), title_colors=((150, 30, 30), (199, 60, 50)))),
    (13, "sheet", lambda a, b: std_photo(day, a, b, night_bg((900, 580), with_moon=True), title="DEVIN BOTS", figure=cut("robot.png"),
                                         tags=["BY COGNITION", "AGENTS NEVER SLEEP"], bg=(26, 28, 78), dots=(60, 70, 190), title_colors=((90, 200, 255), (170, 120, 255)))),
]
for _k, (_line, _enter, _make) in enumerate(SCENES):
    _a = day.line(_line)[0]
    _b = day.line(SCENES[_k + 1][0])[0] if _k + 1 < len(SCENES) else day.line(-2)[0]   # 这一幕一直演到下一幕开始
    day.scene(_a - 0.12, _make(_a, _b), _enter)

# ---------- 三、字幕 ----------
# 字幕自动上屏。重点词（黄色纸片）不写就自动挑带数字的词和句中大写开头的词；想自己定就列出来：  ←
# day.subtitles(key=["Nvidia", "Kress", "billion", "doubled"])
# 某个词亮得不准，就钉住它的时刻：anchors={第几句: {第几个词: 秒}}
# 要中文字幕版：每句歌词写一条中文，用 | 切成纸片，* 是重点词，@数字 是和英文第几个词同时亮，然后命令行加 --zh：  ←
# day.subtitles(zh=["英伟达！*@0 | 创始人@1 | 走了，*@2 | Kress*@3 | 接过@5 | 王冠*@7", …])

# ---------- 四、封面页和结尾的卡点 ----------
# 不写就用自动估的时刻。听过以后发现不准，再照下面的样子改：
# day.intro(date=1.70, five=3.45, minute=4.75, go=6.25, hey=6.90, build=8.00)
# day.outro(44.00, [("THAT'S THE NEWS!", 44.30), ("THAT'S THE BEAT!", 44.95), ("THAT'S THE DAY!", 45.55)],
#           hey=46.05, tomorrow=46.55, sameway=48.20, plane_leaves=47.4)

if __name__ == "__main__":
    day.run()
