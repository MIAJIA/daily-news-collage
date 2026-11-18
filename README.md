# daily-news-collage

把一首唱新闻的歌做成撕纸拼贴风格的新闻视频。一个给 Claude Code 用的 skill。

A Claude Code skill that turns a short news-rap song (a Suno `.m4a` with a timed lyrics track) into a torn-paper collage video: a cover page with one card per headline, a timeline with a paper plane, one scene per lyric line, and karaoke-style paper-chip subtitles (English or Chinese).

![2026-11-17 的封面页，也是视频的第一帧](2026-11-17/封面_2026-11-17.jpg)

## 它做什么

```
一首歌（m4a，带逐句歌词时间）
   │
   ├─ 骨架自动出：封面页 · 时间轴和纸飞机 · 撕纸和盖纸转场 · 纸片字幕 · 结尾 · 署名
   └─ 每天要填： 日期 · 每条新闻一张封面卡片 · 每句歌词一幕（标准画面，或者手写一幕）
   ▼
1920×1080 的 mp4，第一帧就是封面图
```

## 怎么用

把这个仓库放进 `~/.claude/skills/daily-news-collage/`，然后对 Claude Code 说「用这首歌做今天的新闻视频」。步骤和规则见 [SKILL.md](SKILL.md) 和 [CLAUDE.md](CLAUDE.md)。

需要 macOS、`ffmpeg`、Python 3 和 Pillow。

## 仓库里没有什么

- 没有图片素材、歌和成片。`2026-11-17/素材来源.tsv` 列出了那一天用到的每张图在维基共享资源上的标题、作者和授权，可以照着下载。
- 没有选开源许可证。

## 封面图里的素材

封面图里的照片来自维基共享资源，作者和授权见 [素材来源.tsv](2026-11-17/素材来源.tsv)（CC BY、CC BY-SA、CC0、BSD）；图里出现的公司标志属于各自的公司，这里只用来指明新闻说的是谁。
