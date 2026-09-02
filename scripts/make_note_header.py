#!/usr/bin/env python3
"""
note 見出し画像（アイキャッチ）生成 — 1280×670

ancohime.com の日記「解決編」note 用。下の CONFIG を書き替えて実行するだけ。

    .venv\\Scripts\\python.exe scripts\\make_note_header.py

依存: Pillow（.venv に入っている）。フォントは Windows 同梱の Noto Sans JP。
出力先は Obsidian の himeka フォルダ（note.com に手動アップロードするため、
サイトの dist には含めない）。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- CONFIG ----
OUT = Path(r"D:/himic/ソラ/黒猫」ぞーま/毎日の動画/可愛い画像/himeka/2026-09-02 note見出し画像.png")

EYEBROW_GRAY = "ancohime.com の日記の"
EYEBROW_PINK = "「解決編」"
TITLE = [
    "「いいな」で即ポチして、",
    "メダカを5匹死なせた",
]
SUBTITLE = [
    "あわてんぼうの見切り発車を、",
    "仕組みで止める7つの方法",
]
NAME = "昭和上等あんこ姫"
# --------------------------------------------------------------------------- #

W, H = 1280, 670
PINK = (255, 61, 154)
WHITE = (245, 245, 248)
GRAY = (150, 150, 160)
SUB_GRAY = (140, 140, 150)

FONTS = Path(r"C:/Windows/Fonts")
def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)

f_title = font("NotoSansJP-Bold.otf", 60)
f_sub = font("NotoSansJP-Regular.otf", 30)
f_eye = font("NotoSansJP-Medium.otf", 25)
f_name = font("NotoSansJP-Bold.otf", 29)

# --- 背景：4隅グラデ（左上が明るく、右下が暗い） ---
corners = Image.new("RGB", (2, 2))
corners.putpixel((0, 0), (38, 38, 44))   # TL
corners.putpixel((1, 0), (30, 30, 35))   # TR
corners.putpixel((0, 1), (28, 28, 33))   # BL
corners.putpixel((1, 1), (19, 19, 23))   # BR
img = corners.resize((W, H), Image.BICUBIC)
d = ImageDraw.Draw(img)

LEFT = 135            # テキスト左端
BAR_X = 118          # ピンクの縦バー
BAR_W = 7

# --- 位置 ---
eye_y = 122
title_y = 168
title_lh = 84
sub_y = title_y + title_lh * len(TITLE) + 34
sub_lh = 46
name_y = 548

# --- 縦バー（見出し〜サブタイトルの高さ） ---
bar_top = eye_y - 4
bar_bottom = sub_y + sub_lh * len(SUBTITLE) + 4
d.rectangle([BAR_X, bar_top, BAR_X + BAR_W, bar_bottom], fill=PINK)

# --- eyebrow（前半グレー＋「解決編」ピンク） ---
d.text((LEFT, eye_y), EYEBROW_GRAY, font=f_eye, fill=GRAY)
gw = d.textlength(EYEBROW_GRAY, font=f_eye)
d.text((LEFT + gw + 2, eye_y), EYEBROW_PINK, font=f_eye, fill=PINK)

# --- title ---
for i, line in enumerate(TITLE):
    d.text((LEFT, title_y + i * title_lh), line, font=f_title, fill=WHITE)

# --- subtitle ---
for i, line in enumerate(SUBTITLE):
    d.text((LEFT, sub_y + i * sub_lh), line, font=f_sub, fill=SUB_GRAY)

# --- name ---
d.text((LEFT, name_y), NAME, font=f_name, fill=PINK)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print("saved:", OUT)
