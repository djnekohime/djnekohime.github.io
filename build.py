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
import json
import re
import shutil
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
GROUP_ORDER = ["経営者・実業家", "スポーツ選手", "歴史上の人物", "海外の名言"]


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


def load_diary() -> list[dict]:
    entries = []
    for f in sorted(CONTENT.glob("diary/*.md"), reverse=True):
        text = f.read_text(encoding="utf-8")
        fm, body = _split_front_matter(text)
        entries.append(
            {
                "slug": f.stem,
                "title": fm.get("title", f.stem),
                "date": fm.get("date", ""),
                "youtube": fm.get("youtube", ""),
                "html": md.markdown(body, extensions=["extra"]),
                "url": f"/diary/{f.stem}/",
            }
        )
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


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


def build(serve: bool = False) -> None:
    quotes = load_quotes()
    people = load_people(quotes)
    site = load_site()
    diary = load_diary()
    env = make_env()

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

    # --- トップ ---
    write("/index.html", env.get_template("home.html").render(
        **ctx_base,
        recent_quotes=quotes[-3:][::-1],
        total_quotes=len(quotes),
        total_people=len(people),
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
    write("/diary/index.html", env.get_template("diary_index.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("日記", None)],
        entries=diary,
    ))
    tmpl_d = env.get_template("diary_entry.html")
    for e in diary:
        write(e["url"], tmpl_d.render(
            **ctx_base,
            breadcrumbs=[("ホーム", "/"), ("日記", "/diary/"), (e["title"], None)],
            entry=e,
        ))

    # --- SNS ---
    write("/sns/index.html", env.get_template("sns.html").render(
        **ctx_base,
        breadcrumbs=[("ホーム", "/"), ("SNS", None)],
    ))

    # --- 404 ---
    write("/404.html", env.get_template("404.html").render(**ctx_base, breadcrumbs=[]))

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
