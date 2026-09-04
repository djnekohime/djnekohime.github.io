#!/usr/bin/env python3
"""
note 画像セット＋Instagram 解決編リール素材を1コマンドで生成

ancohime.com の日記「解決編」note／リール用。下の CONFIG だけ書き替えて実行:

    .venv\\Scripts\\python.exe scripts\\make_note_images.py

出力（Obsidian の himeka フォルダ。note.com / Instagram へ手動アップロード）:
  1. {DATE} note見出し画像.png          … 1280×670（アイキャッチ）
  2. {DATE} note解決策{n}つ.png         … 1080×1080（本文中／SNS用のまとめ）
  3. {DATE} リール/01_hook.png 〜 09_close.png … 1080×1920（9:16 リールのスライド）

依存: Pillow（.venv）。フォントは Windows 同梱の Noto Sans JP。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ================================ CONFIG ================================== #
HIMEKA = Path(r"D:/himic/ソラ/黒猫」ぞーま/毎日の動画/可愛い画像/himeka")
DATE = "2026-09-04"

# 見出し画像
EYEBROW_GRAY = "ancohime.com の日記の"
EYEBROW_PINK = "「解決編」"
EYECATCH_TITLE = ["メダカの飼い方を、ぜんぶ", "AIの言いなりにしてたら"]
EYECATCH_SUB = ["AIの即答を信じすぎない", "ための7つの方法"]

# 解決策まとめカード ＋ リールのテロップ（共通で使う）
CARD_EYEBROW = "AIとの付き合い方"
SOLUTIONS = [
    "「それ、何を前提にした答え？」と聞き返す",
    "疑うのは生き物・お金・体・戻せないことだけ",
    "二択で聞かず「どういう時にいる／いらん？」",
    "聞く前に「今なにで回ってるか」を1行書く",
    "「捨てる・やめる」の指示は1日寝かせる",
    "大事な質問は言い方を変えて2回聞く",
    "いやな予感がしたら、答えを待たず先に避難",
]

# Instagram 解決編リール（9:16）
REEL_EYEBROW = "解決編リール"
REEL_HOOK = ["メダカの水槽が、", "また", "真っ白になった"]
REEL_HOOK_SUB = "飼い方をぜんぶAIに聞いてた"
REEL_PROGRESS_LABEL = "AIの即答を信じすぎない7つの方法"
REEL_CLOSE = ["AIをやめる話やない。", "「何を前提にした答え？」を", "1個 聞き返すだけ"]
REEL_CLOSE_CTA = "▶ フル解説は note（プロフのリンク）"
REEL_CLOSE_SUB = "この日の日記 → ancohime.com"

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


def wrap(d, text, font, max_w):
    """日本語向け・文字単位の折り返し。'\n' は強制改行。"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if d.textlength(cur + ch, font=font) <= max_w or not cur:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


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


def make_reel():
    """9:16 のリール用スライド。01=Hook / 02..=テロップ7枚 / 09=締め。"""
    W, H = 1080, 1920
    n = len(SOLUTIONS)
    outdir = HIMEKA / f"{DATE} リール"
    outdir.mkdir(parents=True, exist_ok=True)

    f_eye = f("NotoSansJP-Medium.otf", 34)
    f_hook = f("NotoSansJP-Bold.otf", 96)
    f_hooksub = f("NotoSansJP-Regular.otf", 40)
    f_prog = f("NotoSansJP-Medium.otf", 34)
    f_num = f("NotoSansJP-Bold.otf", 78)
    f_tip = f("NotoSansJP-Bold.otf", 68)
    f_close = f("NotoSansJP-Bold.otf", 84)
    f_cta = f("NotoSansJP-Medium.otf", 40)
    f_sub = f("NotoSansJP-Regular.otf", 34)
    f_name = f("NotoSansJP-Bold.otf", 34)
    f_foot = f("NotoSansJP-Regular.otf", 26)

    LEFT, BAR_X, BAR_W = 120, 88, 8
    MAXW = W - LEFT - 90

    # --- 01 Hook ---
    img = gradient_bg(W, H)
    d = ImageDraw.Draw(img)
    top = 430
    d.rectangle([BAR_X, top - 8, BAR_X + BAR_W, top + 40 + 130 * len(REEL_HOOK) + 30],
                fill=PINK)
    d.text((LEFT, top), REEL_EYEBROW, font=f_eye, fill=PINK)
    y = top + 74
    for line in REEL_HOOK:
        d.text((LEFT, y), line, font=f_hook, fill=WHITE)
        y += 130
    d.text((LEFT, y + 24), REEL_HOOK_SUB, font=f_hooksub, fill=SUB_GRAY)
    d.text((LEFT, H - 150), NAME, font=f_name, fill=PINK)
    p = outdir / "01_hook.png"
    img.save(p)
    print("saved:", p)

    # --- 02..08 テロップ ---
    for i, item in enumerate(SOLUTIONS):
        img = gradient_bg(W, H)
        d = ImageDraw.Draw(img)
        d.text((LEFT, 250), REEL_PROGRESS_LABEL, font=f_prog, fill=GRAY)
        d.text((LEFT, 300), f"{i + 1} / {n}", font=f_prog, fill=PINK)

        r = 66
        cx, cy = LEFT + r, 640
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PINK)
        d.text((cx, cy - 2), str(i + 1), font=f_num, fill="white", anchor="mm")

        lines = wrap(d, item, f_tip, MAXW)
        ty = cy + r + 70
        for ln in lines:
            d.text((LEFT, ty), ln, font=f_tip, fill=WHITE)
            ty += 92

        d.text((LEFT, H - 130), f"{NAME}  /  note {HANDLE}", font=f_foot, fill=GRAY)
        p = outdir / f"{i + 2:02d}_tip{i + 1}.png"
        img.save(p)
        print("saved:", p)

    # --- 09 締め ---
    img = gradient_bg(W, H)
    d = ImageDraw.Draw(img)
    top = 470
    d.rectangle([BAR_X, top - 8, BAR_X + BAR_W, top + 118 * len(REEL_CLOSE) + 8],
                fill=PINK)
    y = top
    for line in REEL_CLOSE:
        d.text((LEFT, y), line, font=f_close, fill=WHITE)
        y += 118
    d.text((LEFT, y + 60), REEL_CLOSE_CTA, font=f_cta, fill=PINK)
    d.text((LEFT, y + 130), REEL_CLOSE_SUB, font=f_sub, fill=SUB_GRAY)
    d.text((LEFT, H - 150), NAME, font=f_name, fill=PINK)
    p = outdir / f"{n + 2:02d}_close.png"
    img.save(p)
    print("saved:", p)


if __name__ == "__main__":
    HIMEKA.mkdir(parents=True, exist_ok=True)
    make_eyecatch()
    make_card()
    make_reel()
