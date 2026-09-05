#!/usr/bin/env python3
"""
あんこひめの隠れ家 — 静的サイトジェネレーター

使い方:
    .venv\\Scripts\\python.exe build.py            # dist/ に書き出し
    .venv\\Scripts\\python.exe build.py --serve     # ビルドしてローカルプレビュー (http://localhost:8000)

データの流れ:
    data/quotes.json  … 名言160件（No.・本文・人物・カテゴリー・ひめか解説…）
    data/people.json  … 人物ごとの紹介文・所属グループ
    data/site.json    … サイト名・SNSリンク・導線リンクなど
    content/diary/*.md … 日記（1ファイル=1記事、先頭にタイトルと日付）
        ↓ build.py が読み込んで
    dist/             … 完成したHTML一式（そのままCloudflare Pages等に置ける）

方針: 依存を最小に（Jinja2とMarkdownだけ）。1年後も読んで直せる素朴な作りにする。
"""

from __future__ import annotations

import argparse
import calendar as _cal
import hashlib
import html as _html
import json
import re
import shutil
from collections import OrderedDict
from datetime import datetime, timezone
from email.utils import format_datetime
from dataclasses import dataclass, field
from pathlib import Path

import markdown as md
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
DATA = ROOT / "data"
CONTENT = ROOT / "content"
DIST = ROOT / "dist"
STATIC = ROOT / "static"
TEMPLATES = ROOT / "templates"

THEME_SLUGS = {
    "生き方": "ikikata",
    "仕事": "shigoto",
    "挑戦": "chousen",
    "努力": "doryoku",
    "経営": "keiei",
}
THEME_ORDER = ["生き方", "仕事", "挑戦", "努力", "経営"]
GROUP_ORDER = ["経営者・実業家", "スポーツ選手", "歴史上の人物", "海外の名言", "中国古典"]

# 日記タグ → URL用スラッグ（未定義のタグは build 時に警告＋ハッシュで暫定スラッグ）
DIARY_TAG_SLUGS = {
    "猫": "neko", "犬": "inu", "メダカ": "medaka", "鳥": "tori", "動物": "doubutsu",
    "機材": "kizai", "AI": "ai", "音楽": "ongaku", "動画": "douga",
    "SNS": "sns", "サイト制作": "site", "BTS": "bts",
    "韓国ドラマ": "kandrama", "韓ドラ": "kandrama",
    "買い物": "kaimono", "家族": "kazoku", "旦那": "danna",
    "学び": "manabi", "失敗": "shippai", "お金": "okane", "健康": "kenkou",
    "料理": "ryouri", "英語": "eigo", "韓国語": "kankokugo", "日常": "nichijou",
    "あるある": "aruaru", "自虐": "jigyaku",
}
WEEKDAY_JA = ["日", "月", "火", "水", "木", "金", "土"]


def diary_tag_slug(tag: str) -> str:
    s = DIARY_TAG_SLUGS.get(tag)
    if not s:
        s = "t" + hashlib.md5(tag.encode("utf-8")).hexdigest()[:6]
        print(f"  ⚠ 日記タグ '{tag}' の slug 未定義 → 暫定 '{s}'（DIARY_TAG_SLUGS に追加を）")
    return s


def month_calendar(ym: str, posts_by_day: dict) -> dict:
    """ym='2026-08' → テンプレート用の週×日グリッド。"""
    y, m = int(ym[:4]), int(ym[5:7])
    cal = _cal.Calendar(firstweekday=6)  # 日曜はじまり
    weeks = []
    for week in cal.monthdatescalendar(y, m):
        row = []
        for d in week:
            if d.month != m:
                row.append({"day": None})
                continue
            ds = d.isoformat()
            posts = posts_by_day.get(ds, [])
            row.append({
                "day": d.day,
                "date": ds,
                "url": posts[0]["url"] if posts else None,
                "count": len(posts),
            })
        weeks.append(row)
    return {"ym": ym, "label": f"{y}年{m}月", "weeks": weeks}


# --------------------------------------------------------------------------- #
# データ読み込み
# --------------------------------------------------------------------------- #
@dataclass
class Quote:
    no: int
    quote: str
    attribution: str            # 「――松下幸之助（経営の神様・パナソニック創業者）」の（）内など
    person: str
    group: str
    categories: list[str]
    commentary: str             # ひめか：… の中身
    en: str = ""                # 海外名言の原文（無ければ空）
    note: str = ""              # ※諸説あり などの注記
    youtube: str = ""

    @property
    def slug(self) -> str:
        return f"{self.no:03d}"

    @property
    def url(self) -> str:
        return f"/meigen/q/{self.slug}/"


@dataclass
class Person:
    slug: str
    name: str
    group: str
    bio: str
    quote_nos: list[int] = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"/meigen/person/{self.slug}/"


def load_quotes() -> list[Quote]:
    raw = json.loads((DATA / "quotes.json").read_text(encoding="utf-8"))
    out = []
    for r in raw:
        out.append(
            Quote(
                no=int(r["no"]),
                quote=r["quote"].strip(),
                attribution=r.get("attribution", "").strip(),
                person=r["person"].strip(),
                group=r.get("group", "").strip(),
                categories=list(r.get("categories", [])),
                commentary=r.get("commentary", "").strip(),
                en=r.get("en", "").strip(),
                note=r.get("note", "").strip(),
                youtube=r.get("youtube", "").strip(),
            )
        )
    out.sort(key=lambda q: q.no)
    return out


def load_people(quotes: list[Quote]) -> list[Person]:
    meta = json.loads((DATA / "people.json").read_text(encoding="utf-8"))
    # 出現順に人物を採番（URLは person/p01 形式）
    order: list[str] = []
    for q in quotes:
        if q.person not in order:
            order.append(q.person)
    people = []
    for i, name in enumerate(order, start=1):
        m = meta.get(name, {})
        p = Person(
            slug=m.get("slug") or f"p{i:02d}",
            name=name,
            group=m.get("group") or next((q.group for q in quotes if q.person == name), ""),
            bio=m.get("bio", "").strip(),
            quote_nos=[q.no for q in quotes if q.person == name],
        )
        people.append(p)
    return people


def load_site() -> dict:
    return json.loads((DATA / "site.json").read_text(encoding="utf-8"))


def load_kaiwai() -> dict:
    p = DATA / "kaiwai.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def load_works() -> dict:
    p = DATA / "works.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def load_kotowaza() -> dict:
    p = DATA / "kotowaza.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def load_tanka() -> dict:
    p = DATA / "tanka.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def load_diary() -> list[dict]:
    entries = []
    for f in sorted(CONTENT.glob("diary/*.md"), reverse=True):
        text = f.read_text(encoding="utf-8")
        fm, body = _split_front_matter(text)
        d = fm.get("date", "")
        html = md.markdown(body, extensions=["extra"])
        excerpt = _strip_tags(html)
        if len(excerpt) > 110:
            excerpt = excerpt[:110].rstrip() + "…"
        # 見出し画像：front matter の image: 優先、無ければ本文の最初の画像。
        # 本文先頭の画像を見出しに使う場合は本文からは外す（二重表示を防ぐ）。
        hero = fm.get("image", "").strip()
        body_html = html
        if not hero:
            first = _first_img(html)
            if first:
                hero = first
                body_html = re.sub(
                    r"^\s*<p>\s*<img[^>]*>\s*</p>\s*", "", html, count=1
                )
        entries.append(
            {
                "slug": f.stem,
                "title": fm.get("title", f.stem),
                "date": d,
                "year": d[:4],
                "month": d[:7],  # "2026-08"
                "tags": [t.strip() for t in fm.get("tags", "").split(",") if t.strip()],
                "youtube": fm.get("youtube", ""),
                "note": fm.get("note", ""),  # 「解決編」note記事のURL（任意）
                "html": html,          # RSS用（画像込み）
                "body_html": body_html,  # ページ本文用（見出し画像を除いたもの）
                "excerpt": excerpt,
                "image": hero,         # 見出し画像 & OGP画像
                "url": f"/diary/{f.stem}/",
            }
        )
    entries.sort(key=lambda e: (e["date"], e["slug"]), reverse=True)
    return entries


def _strip_tags(html_text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html_text)).strip()


def _first_img(html_text: str) -> str:
    m = re.search(r'<img[^>]+src="([^"]+)"', html_text)
    return m.group(1) if m else ""


def _split_front_matter(text: str) -> tuple[dict, str]:
    """先頭の --- で囲まれた key: value ブロックを取り出す簡易パーサ。"""
    if text.startswith("---"):
        _, fm_text, body = text.split("---", 2)
        fm = {}
        for line in fm_text.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
        return fm, body.strip()
    return {}, text.strip()


# --------------------------------------------------------------------------- #
# レンダリング
# --------------------------------------------------------------------------- #
def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["nl2p"] = lambda s: "".join(
        f"<p>{line}</p>" for line in str(s).split("\n") if line.strip()
    )
    return env


def write(path_from_dist: str, html: str) -> None:
    out = DIST / path_from_dist.lstrip("/")
    if out.suffix != ".html":
        out = out / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def write_raw(path_from_dist: str, text: str) -> None:
    """拡張子をそのまま使ってファイルを書き出す（rss.xml など）。"""
    out = DIST / path_from_dist.lstrip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def build_diary_rss(diary: list[dict], site: dict) -> str:
    base = f"https://{site.get('domain', 'example.com')}"
    items = []
    for e in diary[:20]:
        try:
            dt = datetime.strptime(e["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            dt = datetime.now(timezone.utc)
        link = base + e["url"]
        desc = _html.escape(re.sub(r"<[^>]+>", "", e["html"]).strip()[:500])
        items.append(
            "    <item>\n"
            f"      <title>{_html.escape(e['title'])}</title>\n"
            f"      <link>{link}</link>\n"
            f"      <guid isPermaLink=\"true\">{link}</guid>\n"
            f"      <pubDate>{format_datetime(dt)}</pubDate>\n"
            f"      <description>{desc}</description>\n"
            "    </item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n  <channel>\n'
        f"    <title>{_html.escape(site.get('title',''))} — 日記</title>\n"
        f"    <link>{base}/diary/</link>\n"
        f"    <description>{_html.escape(site.get('description',''))}</description>\n"
        "    <language>ja</language>\n"
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )


def build(serve: bool = False) -> None:
    quotes = load_quotes()
    people = load_people(quotes)
    site = load_site()
    diary = load_diary()
    kotowaza = load_kotowaza()
    tanka = load_tanka()
    env = make_env()
    base = f"https://{site.get('domain', 'example.com')}"

    by_no = {q.no: q for q in quotes}
    people_by_name = {p.name: p for p in people}

    # グループ別
    groups = {g: [q for q in quotes if q.group == g] for g in GROUP_ORDER}
    groups = {g: v for g, v in groups.items() if v}

    # テーマ別
    themes = []
    for name in THEME_ORDER:
        qs = [q for q in quotes if name in q.categories]
        if qs:
            themes.append({"name": name, "slug": THEME_SLUGS[name], "quotes": qs})

    # 人物をグループ順に
    people_by_group = {}
    for p in people:
        people_by_group.setdefault(p.group, []).append(p)
    people_by_group = {
        g: people_by_group[g] for g in GROUP_ORDER if g in people_by_group
    }

    ctx_base = dict(site=site, nav_diary=diary)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    # 静的ファイル
    if STATIC.exists():
        shutil.copytree(STATIC, DIST / "static")

    # サイトルート直下に置くファイル（ads.txt など）
    for name in ("ads.txt", "robots.txt", "favicon.ico"):
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, DIST / name)

    # --- トップ ---
    write("/index.html", env.get_template("home.html").render(
        **ctx_base,
        recent_quotes=quotes[-3:][::-1],
        total_quotes=len(quotes),
        total_people=len(people),
        total_kotowaza=sum(len(c["items"]) for c in kotowaza.get("cats", [])),
        diary_recent=diary[:3],
    ))

    # --- 名言トップ ---
    write("/meigen/index.html", env.get_template("meigen_index.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("名言", None)],
        total_quotes=len(quotes),
        groups=groups,
        themes=themes,
        people_by_group=people_by_group,
        recent_quotes=quotes[-6:][::-1],
    ))

    # --- 名言を読む（全件・グループ別） ---
    write("/meigen/all/index.html", env.get_template("meigen_all.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("名言", "/meigen/"), ("すべての名言", None)],
        groups=groups,
    ))

    # --- 個別の名言 ---
    tmpl_q = env.get_template("quote.html")
    for q in quotes:
        person = people_by_name.get(q.person)
        same_person = [x for x in quotes if x.person == q.person and x.no != q.no]
        write(q.url, tmpl_q.render(
            **ctx_base,
            breadcrumbs=[
                ("ホーム", "/"), ("名言", "/meigen/"),
                (q.person, person.url if person else None),
                (f"No.{q.slug}", None),
            ],
            q=q, person=person,
            prev=by_no.get(q.no - 1), next=by_no.get(q.no + 1),
            same_person=same_person[:6],
            theme_slugs=THEME_SLUGS,
        ))

    # --- 人物別 ---
    tmpl_p = env.get_template("person.html")
    for p in people:
        write(p.url, tmpl_p.render(
            **ctx_base,
            breadcrumbs=[
                ("ホーム", "/"), ("名言", "/meigen/"),
                ("人物から探す", "/meigen/#people"), (p.name, None),
            ],
            person=p,
            quotes=[by_no[n] for n in p.quote_nos],
        ))

    # --- テーマ別 ---
    tmpl_t = env.get_template("theme.html")
    for t in themes:
        write(f"/meigen/theme/{t['slug']}/", tmpl_t.render(
            **ctx_base,
            breadcrumbs=[
                ("ホーム", "/"), ("名言", "/meigen/"),
                ("テーマから探す", "/meigen/#themes"), (f"「{t['name']}」の名言", None),
            ],
            theme=t,
        ))

    # --- 日記 ---
    # 年月グループ（diary は日付降順）
    by_month: "OrderedDict[str, list[dict]]" = OrderedDict()
    for e in diary:
        by_month.setdefault(e["month"], []).append(e)
    months = [
        {"ym": ym, "label": f"{ym[:4]}年{int(ym[5:7])}月", "count": len(es), "entries": es}
        for ym, es in by_month.items()
    ]
    posts_by_day: dict[str, list[dict]] = {}
    for e in diary:
        posts_by_day.setdefault(e["date"], []).append(e)

    # タグ集計 & タグ→URL
    diary_tags: "OrderedDict[str, list[dict]]" = OrderedDict()
    for e in diary:
        for t in e["tags"]:
            diary_tags.setdefault(t, []).append(e)
    tag_url = {t: f"/diary/tag/{diary_tag_slug(t)}/" for t in diary_tags}

    # トップに出す最近分（30件前後まで、残りは月別アーカイブへ）
    recent_groups, shown = [], 0
    for mo in months:
        if shown >= 30 and recent_groups:
            break
        recent_groups.append({"label": mo["label"], "entries": mo["entries"]})
        shown += len(mo["entries"])
    has_more = shown < len(diary)

    write("/diary/index.html", env.get_template("diary_index.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("日記", None)],
        months=months,
        cal=month_calendar(months[0]["ym"], posts_by_day) if months else None,
        recent_groups=recent_groups,
        has_more=has_more,
        weekday_ja=WEEKDAY_JA,
        tag_url=tag_url,
        tanka_poems=tanka.get("poems", []),
    ))

    tmpl_d = env.get_template("diary_entry.html")
    for i, e in enumerate(diary):
        newer = diary[i - 1] if i > 0 else None
        older = diary[i + 1] if i < len(diary) - 1 else None
        og_img = e["image"]
        if og_img.startswith("/"):
            og_img = base + og_img
        write(e["url"], tmpl_d.render(
            **ctx_base,
            breadcrumbs=[("ホーム", "/"), ("日記", "/diary/"), (e["title"], None)],
            entry=e, older=older, newer=newer, tag_url=tag_url,
            og_type="article", og_title=e["title"], og_description=e["excerpt"],
            og_image=(og_img or None), og_url=base + e["url"],
        ))

    # 月別アーカイブ
    tmpl_dm = env.get_template("diary_month.html")
    for mo in months:
        write(f"/diary/{mo['ym']}/", tmpl_dm.render(
            **ctx_base,
            breadcrumbs=[("ホーム", "/"), ("日記", "/diary/"), (mo["label"], None)],
            month=mo,
            cal=month_calendar(mo["ym"], posts_by_day),
            weekday_ja=WEEKDAY_JA,
            tag_url=tag_url,
        ))

    # 日記タグページ
    tmpl_dt = env.get_template("diary_tag.html")
    for t, es in diary_tags.items():
        write(f"/diary/tag/{diary_tag_slug(t)}/", tmpl_dt.render(
            **ctx_base,
            breadcrumbs=[("ホーム", "/"), ("日記", "/diary/"), (f"#{t}", None)],
            tag=t, entries=es, tag_url=tag_url,
        ))

    # 日記RSS
    write_raw("/diary/rss.xml", build_diary_rss(diary, site))

    # --- ことわざ ---
    if kotowaza.get("cats"):
        kw_all = [it for c in kotowaza["cats"] for it in c["items"]]
        kw_total = len(kw_all)
        write("/kotowaza/index.html", env.get_template("kotowaza_index.html").render(
            **ctx_base,
            breadcrumbs=[("ホーム", "/"), ("ことわざ", None)],
            intro=kotowaza.get("intro", ""),
            cats=kotowaza["cats"],
            total=kw_total,
            og_title="ことわざ", og_description=kotowaza.get("intro", ""),
            og_url=base + "/kotowaza/",
        ))
        # 五十音順
        _k2h = str.maketrans({chr(c): chr(c - 0x60) for c in range(0x30A1, 0x30F7)})
        GYOU = [
            ("あ", "あいうえおぁぃぅぇぉゔ"), ("か", "かきくけこがぎぐげご"),
            ("さ", "さしすせそざじずぜぞ"), ("た", "たちつてとだぢづでどっ"),
            ("な", "なにぬねの"), ("は", "はひふへほばびぶべぼぱぴぷぺぽ"),
            ("ま", "まみむめも"), ("や", "やゆよゃゅょ"),
            ("ら", "らりるれろ"), ("わ", "わをんゐゑ"),
        ]
        def _kkey(it):
            return (it.get("kana", "") or it.get("text", "")).translate(_k2h)
        def _gyou(it):
            c = (_kkey(it) or "わ")[0]
            for lbl, chars in GYOU:
                if c in chars:
                    return lbl
            return "わ"
        kw_sorted = sorted(kw_all, key=_kkey)
        gyou_list = []
        for lbl, _chars in GYOU:
            items = [it for it in kw_sorted if _gyou(it) == lbl]
            if items:
                gyou_list.append({"label": lbl, "items": items})
        write("/kotowaza/aiueo/index.html", env.get_template("kotowaza_aiueo.html").render(
            **ctx_base,
            breadcrumbs=[("ホーム", "/"), ("ことわざ", "/kotowaza/"), ("五十音順", None)],
            gyou_list=gyou_list, total=kw_total,
            og_title="ことわざ 五十音順", og_description=kotowaza.get("intro", ""),
            og_url=base + "/kotowaza/aiueo/",
        ))

    # --- 短歌コーナー（日記の一部） ---
    write("/tanka/index.html", env.get_template("tanka_index.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("日記", "/diary/"), ("短歌コーナー", None)],
        intro=tanka.get("intro", ""),
        poems=tanka.get("poems", []),
        og_title="短歌コーナー", og_description=tanka.get("intro", ""),
        og_url=base + "/tanka/",
    ))

    # --- SNS ---
    write("/sns/index.html", env.get_template("sns.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("SNS", None)],
    ))

    # --- リンク集（LINE リッチメニュー等からの着地ページ） ---
    write("/links/index.html", env.get_template("links.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("リンク集", None)],
    ))

    # --- 法務ページ（このサイトについて／プライバシーポリシー／お問い合わせ） ---
    write("/about/index.html", env.get_template("about.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("このサイトについて", None)],
    ))
    write("/privacy/index.html", env.get_template("privacy.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("プライバシーポリシー", None)],
    ))
    write("/contact/index.html", env.get_template("contact.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("お問い合わせ", None)],
    ))

    # --- 作品（LINEスタンプ・音楽など） ---
    works = load_works()
    if works:
        write("/works/index.html", env.get_template("works_index.html").render(
            **ctx_base,
            breadcrumbs=[("ホーム", "/"), ("作品", None)],
            works=works,
        ))
        stamp_tmpl = env.get_template("works_stamp.html")
        for cat in works.get("categories", []):
            for w in cat.get("works", []):
                if cat["slug"] == "line-stamps":
                    write(f"/works/{cat['slug']}/{w['slug']}/", stamp_tmpl.render(
                        **ctx_base,
                        breadcrumbs=[
                            ("ホーム", "/"), ("作品", "/works/"),
                            (cat["name"], "/works/"), (w["title"], None),
                        ],
                        cat=cat, w=w,
                    ))

    # --- 界隈語録 ---
    kaiwai = load_kaiwai()
    if kaiwai:
        presenter = kaiwai["presenter"]
        cats = kaiwai["categories"]
        allk = kaiwai["kaiwai"]
        cat_by_slug = {c["slug"]: c for c in cats}
        by_cat: dict[str, list] = {}
        for k in allk:
            by_cat.setdefault(k["category"], []).append(k)

        write("/kaiwai/index.html", env.get_template("kaiwai_index.html").render(
            **ctx_base,
            breadcrumbs=[("ホーム", "/"), ("界隈語録", None)],
            presenter=presenter, categories=cats, by_cat=by_cat,
        ))

        tmpl_kc = env.get_template("kaiwai_category.html")
        for c in cats:
            ks = by_cat.get(c["slug"], [])
            if not ks:
                continue
            write(f"/kaiwai/{c['slug']}/", tmpl_kc.render(
                **ctx_base,
                breadcrumbs=[("ホーム", "/"), ("界隈語録", "/kaiwai/"), (c["name"], None)],
                category=c, kaiwai_list=ks, presenter=presenter,
            ))

        tmpl_kk = env.get_template("kaiwai_kaiwai.html")
        tmpl_kg = env.get_template("kaiwai_goroku.html")
        for k in allk:
            cat = cat_by_slug.get(k["category"], {"slug": k["category"], "name": k["category"]})
            gor = k["goroku"]
            write(f"/kaiwai/{k['slug']}/", tmpl_kk.render(
                **ctx_base,
                breadcrumbs=[("ホーム", "/"), ("界隈語録", "/kaiwai/"),
                             (cat["name"], f"/kaiwai/{cat['slug']}/"), (k["name"], None)],
                kaiwai=k, category=cat, presenter=presenter,
            ))
            for i, g in enumerate(gor, start=1):
                write(f"/kaiwai/{k['slug']}/{i}/", tmpl_kg.render(
                    **ctx_base,
                    breadcrumbs=[("ホーム", "/"), ("界隈語録", "/kaiwai/"),
                                 (cat["name"], f"/kaiwai/{cat['slug']}/"),
                                 (k["name"], f"/kaiwai/{k['slug']}/"), (g["title"], None)],
                    kaiwai=k, category=cat, g=g, num=i, total=len(gor),
                    prev=(gor[i - 2] if i > 1 else None),
                    prev_url=(f"/kaiwai/{k['slug']}/{i - 1}/" if i > 1 else None),
                    next=(gor[i] if i < len(gor) else None),
                    next_url=(f"/kaiwai/{k['slug']}/{i + 1}/" if i < len(gor) else None),
                    presenter=presenter,
                ))

    # --- 404 ---
    write("/404.html", env.get_template("404.html").render(**ctx_base, breadcrumbs=[]))

    # --- sitemap.xml ---
    base = f"https://{site.get('domain', 'example.com')}"
    locs = []
    for f in sorted(DIST.rglob("*.html")):
        rel = f.relative_to(DIST).as_posix()
        if rel == "404.html":
            continue
        path = rel[:-len("index.html")] if rel.endswith("index.html") else rel
        locs.append(f"  <url><loc>{base}/{path}</loc></url>")
    write_raw("/sitemap.xml",
              '<?xml version="1.0" encoding="UTF-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
              + "\n".join(locs) + "\n</urlset>\n")

    pages = sum(1 for _ in DIST.rglob("*.html"))
    print(f"[OK] ビルド完了: {pages} ページ / 出力先 {DIST}")

    if serve:
        _serve()


def _serve(port: int = 8000) -> None:
    import functools
    import http.server
    import socketserver

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"プレビュー: http://localhost:{port}  (Ctrl+C で停止)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n停止しました。")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="ビルド後にローカルプレビューを起動")
    args = ap.parse_args()
    build(serve=args.serve)
