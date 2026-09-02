#!/usr/bin/env python3
"""
note 画像セットを1コマンドで生成 — 見出し画像＋解決策まとめカード

ancohime.com の日記「解決編」note 用。下の CONFIG だけ書き替えて実行:

    .venv\\Scripts\\python.exe scripts\\make_note_images.py

出力（Obsidian の himeka フォルダ。note.com へ手動アップロード）:
  1. {DATE} note見出し画像.png      … 1280×670（アイキャッチ）
  2. {DATE} note解決策{n}つ.png     … 1080×1080（本文中／SNS用のまとめ）

依存: Pillow（.venv）。フォントは Windows 同梱の Noto Sans JP。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ================================ CONFIG ================================== #
HIMEKA = Path(r"D:/himic/ソラ/黒猫」ぞーま/毎日の動画/可愛い画像/himeka")
DATE = "2026-09-02"

# 見出し画像
EYEBROW_GRAY = "ancohime.com の日記の"
EYEBROW_PINK = "「解決編」"
EYECATCH_TITLE = ["「いいな」で即ポチして、", "メダカを5匹死なせた"]
EYECATCH_SUB = ["あわてんぼうの見切り発車を、", "仕組みで止める7つの方法"]

# 解決策まとめカード
CARD_EYEBROW = "あわてんぼうの即ポチ"
SOLUTIONS = [
    "買う前に、カートで1晩寝かす",
    "「結果」でなく「過程」を見にいく",
    "環境は一度に一個しか変えない",
    "試す前に「今いる子」を先に逃がす",
    "「これ、戻せる？」と声に出す",
    "マネしていい人を先に決めておく",
    "後悔した買い物を1行メモに残す",
]

NAME = "昭和上等あんこ姫"
HANDLE = "@ancohimesama"
# ======================================================================== #

PINK = (255, 61, 154)
WHITE = (245, 245, 248)
GRAY = (150, 150, 160)
SUB_GRAY = (140, 140, 150)
LIST_TXT = (226, 226, 231)

FONTS = Path(r"C:/Windows/Fonts")
def f(name, size):
    return ImageFont.truetype(str(FONTS / name), size)

def gradient_bg(w, h):
    c = Image.new("RGB", (2, 2))
    c.putpixel((0, 0), (38, 38, 44))
    c.putpixel((1, 0), (30, 30, 35))
    c.putpixel((0, 1), (28, 28, 33))
    c.putpixel((1, 1), (19, 19, 23))
    return c.resize((w, h), Image.BICUBIC)


def make_eyecatch():
    W, H = 1280, 670
    img = gradient_bg(W, H)
    d = ImageDraw.Draw(img)
    f_title, f_sub, f_eye, f_name = (
        f("NotoSansJP-Bold.otf", 60), f("NotoSansJP-Regular.otf", 30),
        f("NotoSansJP-Medium.otf", 25), f("NotoSansJP-Bold.otf", 29),
    )
    LEFT, BAR_X, BAR_W = 135, 118, 7
    eye_y, title_y, title_lh = 122, 168, 84
    sub_y = title_y + title_lh * len(EYECATCH_TITLE) + 34
    sub_lh = 46
    d.rectangle([BAR_X, eye_y - 4, BAR_X + BAR_W,
                 sub_y + sub_lh * len(EYECATCH_SUB) + 4], fill=PINK)
    d.text((LEFT, eye_y), EYEBROW_GRAY, font=f_eye, fill=GRAY)
    d.text((LEFT + d.textlength(EYEBROW_GRAY, font=f_eye) + 2, eye_y),
           EYEBROW_PINK, font=f_eye, fill=PINK)
    for i, line in enumerate(EYECATCH_TITLE):
        d.text((LEFT, title_y + i * title_lh), line, font=f_title, fill=WHITE)
    for i, line in enumerate(EYECATCH_SUB):
        d.text((LEFT, sub_y + i * sub_lh), line, font=f_sub, fill=SUB_GRAY)
    d.text((LEFT, 548), NAME, font=f_name, fill=PINK)
    out = HIMEKA / f"{DATE} note見出し画像.png"
    img.save(out)
    print("saved:", out)


def make_card():
    n = len(SOLUTIONS)
    W = H = 1080
    img = gradient_bg(W, H)
    d = ImageDraw.Draw(img)
    f_eye = f("NotoSansJP-Medium.otf", 27)
    f_title = f("NotoSansJP-Bold.otf", 74)
    f_num = f("NotoSansJP-Bold.otf", 30)
    f_item = f("NotoSansJP-Regular.otf", 31)
    f_foot = f("NotoSansJP-Regular.otf", 22)

    LEFT, BAR_X, BAR_W = 120, 90, 7
    eye_y, title_y = 92, 126
    d.rectangle([BAR_X, eye_y - 4, BAR_X + BAR_W, title_y + 96], fill=PINK)
    d.text((LEFT, eye_y), CARD_EYEBROW, font=f_eye, fill=GRAY)
    d.text((LEFT, title_y), f"解決策 {n}つ", font=f_title, fill=WHITE)

    top, bottom = 300, 1000
    pitch = min(100, (bottom - top) / n)
    r = 24
    cx = LEFT + r
    for i, item in enumerate(SOLUTIONS):
        cy = int(top + i * pitch + r)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PINK)
        d.text((cx, cy - 1), str(i + 1), font=f_num, fill="white", anchor="mm")
        d.text((LEFT + 2 * r + 24, cy), item, font=f_item, fill=LIST_TXT, anchor="lm")

    d.text((40, H - 52), f"{NAME}  /  note {HANDLE}", font=f_foot, fill=GRAY)
    out = HIMEKA / f"{DATE} note解決策{n}つ.png"
    img.save(out)
    print("saved:", out)


if __name__ == "__main__":
    HIMEKA.mkdir(parents=True, exist_ok=True)
    make_eyecatch()
    make_card()
