#!/usr/bin/env python3
"""
共有用プレビュー生成  →  preview.html（1ファイル完結・データ埋め込み・クライアント側ルーティング）

用途: さくらがローカルサーバを立てなくても、Artifact のURLでサイト全体をクリックして確認できるようにする。
本番の静的サイト（build.py / dist/）とは別物。あくまで確認用のSPA。

再生成: .venv\\Scripts\\python.exe scripts\\make_preview.py
"""
import json
import re
from pathlib import Path

import markdown as md

ROOT = Path(__file__).parent.parent
quotes = json.loads((ROOT / "data" / "quotes.json").read_text(encoding="utf-8"))
site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
people_meta = json.loads((ROOT / "data" / "people.json").read_text(encoding="utf-8"))

# 人物を出現順に採番（build.py と同じ規則）
order = []
for q in quotes:
    if q["person"] not in order:
        order.append(q["person"])
people = []
for i, name in enumerate(order, start=1):
    m = people_meta.get(name, {})
    people.append({
        "slug": m.get("slug") or f"p{i:02d}",
        "name": name,
        "group": m.get("group") or next(q["group"] for q in quotes if q["person"] == name),
        "bio": m.get("bio", ""),
        "nos": [q["no"] for q in quotes if q["person"] == name],
    })

diary = []
for f in sorted((ROOT / "content" / "diary").glob("*.md"), reverse=True):
    text = f.read_text(encoding="utf-8")
    fm = {}
    body = text
    if text.startswith("---"):
        _, fmt, body = text.split("---", 2)
        for line in fmt.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    diary.append({
        "slug": f.stem,
        "title": fm.get("title", f.stem),
        "date": fm.get("date", ""),
        "youtube": fm.get("youtube", ""),
        "html": md.markdown(body.strip(), extensions=["extra"]),
    })

DATA = {
    "site": site,
    "quotes": quotes,
    "people": people,
    "diary": diary,
    "themes": [
        {"name": "生き方", "slug": "ikikata"},
        {"name": "仕事", "slug": "shigoto"},
        {"name": "挑戦", "slug": "chousen"},
        {"name": "努力", "slug": "doryoku"},
        {"name": "経営", "slug": "keiei"},
    ],
    "groups": ["経営者・実業家", "スポーツ選手", "歴史上の人物", "海外の名言"],
}

HTML = """<title>昭和上等あんこ姫の隠れ家</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<style>
:root{
  --ground:#f6f1e8; --surface:#fffdf8; --edge:#e2d8c6; --edge-soft:#efe8da;
  --ink:#332e27; --ink-dim:#7b7266; --accent:#b07d24; --accent-line:#c79a45;
  --accent-soft:rgba(176,125,36,.10); --shadow:rgba(60,45,20,.08);
  --serif:"Shippori Mincho", "Hiragino Mincho ProN", "Yu Mincho", serif;
  --sans:"Zen Kaku Gothic New", "Hiragino Sans", "Yu Gothic", Meiryo, sans-serif;
  --wrap:41rem;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#211f1c; --surface:#2b2825; --edge:#423c34; --edge-soft:#332f2a;
    --ink:#ece7df; --ink-dim:#a79e92; --accent:#d9a441; --accent-line:#8a6f3a;
    --accent-soft:rgba(217,164,65,.10); --shadow:rgba(0,0,0,.25);
  }
}
:root[data-theme="dark"]{
  --ground:#211f1c; --surface:#2b2825; --edge:#423c34; --edge-soft:#332f2a;
  --ink:#ece7df; --ink-dim:#a79e92; --accent:#d9a441; --accent-line:#8a6f3a;
  --accent-soft:rgba(217,164,65,.10); --shadow:rgba(0,0,0,.25);
}
*{box-sizing:border-box;}
html{-webkit-text-size-adjust:100%;}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:16.5px;line-height:1.92;word-break:break-word;letter-spacing:.01em;}
.wrap{max-width:var(--wrap);margin:0 auto;padding:0 1.15rem;}
a{color:var(--accent);text-decoration:none;}
a:hover{text-decoration:underline;text-underline-offset:3px;}
@media (prefers-reduced-motion:no-preference){
  main{animation:fade .32s ease;}
  @keyframes fade{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:none;}}
}

header.site{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--ground) 88%,transparent);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--edge);}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;gap:.6rem;
  min-height:3.35rem;}
.brand{font-family:var(--serif);font-weight:700;font-size:1.06rem;color:var(--ink);letter-spacing:.02em;}
.brand:hover{text-decoration:none;color:var(--accent);}
nav.site{display:flex;gap:1.05rem;font-size:.9rem;align-items:center;}
nav.site a{color:var(--ink-dim);}
nav.site a:hover{color:var(--accent);text-decoration:none;}
nav.site a.on{color:var(--ink);}
.themebtn{background:none;border:1px solid var(--edge);color:var(--ink-dim);border-radius:999px;
  width:1.9rem;height:1.9rem;font-size:.85rem;cursor:pointer;line-height:1;}
.themebtn:hover{color:var(--accent);border-color:var(--accent-line);}

.crumb{font-size:.78rem;color:var(--ink-dim);padding:.85rem 0 0;letter-spacing:.02em;}
.crumb a{color:var(--ink-dim);}
.crumb i{opacity:.5;margin:0 .4rem;font-style:normal;}

main{padding:1.3rem 0 3.5rem;min-height:60vh;}
h1{font-family:var(--serif);font-weight:700;font-size:1.62rem;line-height:1.55;margin:.5rem 0 1rem;
  text-wrap:balance;letter-spacing:.02em;}
h2{font-family:var(--serif);font-weight:600;font-size:1.16rem;margin:2.1rem 0 .8rem;letter-spacing:.02em;}
h3{font-size:.86rem;font-weight:700;color:var(--ink-dim);letter-spacing:.08em;margin:1.5rem 0 .6rem;}
.lead{color:var(--ink-dim);margin:0 0 1.5rem;font-size:1rem;}
.eyebrow{font-size:.74rem;letter-spacing:.14em;color:var(--accent);font-weight:700;margin:0 0 .35rem;}
.muted{color:var(--ink-dim);font-size:.86rem;}
.sectitle{border-left:2px solid var(--accent);padding-left:.6rem;}
.more{font-weight:700;font-size:.9rem;display:inline-block;}

/* hero */
.hero{padding:2rem 0 .6rem;text-align:center;}
.hero .mark{font-family:var(--serif);font-size:2.5rem;color:var(--accent);line-height:1;}
.hero h1{font-size:2rem;margin:.6rem 0 .3rem;}
.hero p{color:var(--ink-dim);margin:0;}
.cards{display:grid;gap:.8rem;margin:1.8rem 0 1rem;}
@media(min-width:37rem){.cards{grid-template-columns:repeat(3,1fr);}}
.card{display:block;background:var(--surface);border:1px solid var(--edge);border-radius:14px;
  padding:1.05rem 1.1rem;color:var(--ink);box-shadow:0 1px 2px var(--shadow);}
.card:hover{text-decoration:none;border-color:var(--accent-line);transform:translateY(-1px);
  transition:.15s;}
.card h2{font-family:var(--serif);margin:0 0 .3rem;font-size:1.08rem;}
.card p{margin:0;color:var(--ink-dim);font-size:.86rem;line-height:1.75;}

.qlist{list-style:none;padding:0;margin:0;}
.qlist li{border-bottom:1px solid var(--edge-soft);}
.qlist a{display:block;padding:.82rem 0;color:var(--ink);}
.qlist a:hover{color:var(--accent);text-decoration:none;}
.qno{font-size:.72rem;letter-spacing:.1em;color:var(--accent);margin-right:.6rem;}
.qby{display:block;color:var(--ink-dim);font-size:.8rem;margin-top:.1rem;}

.chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:.5rem 0 1.3rem;}
.chip{display:inline-flex;align-items:center;gap:.4rem;background:var(--surface);
  border:1px solid var(--edge);border-radius:999px;padding:.32rem .8rem;font-size:.87rem;color:var(--ink);}
.chip:hover{text-decoration:none;border-color:var(--accent-line);color:var(--accent);}
.chip b{color:var(--ink-dim);font-weight:400;font-size:.76rem;font-variant-numeric:tabular-nums;}

.qcard{background:var(--surface);border:1px solid var(--edge);border-radius:14px;
  padding:1.15rem 1.2rem;margin:1rem 0;box-shadow:0 1px 2px var(--shadow);}
.qcard blockquote,.qdetail blockquote{margin:0;font-family:var(--serif);font-size:1.08rem;
  line-height:1.9;font-weight:500;}
.qcard .en,.qdetail .en{display:block;font-family:var(--sans);color:var(--ink-dim);font-size:.85rem;
  font-style:italic;margin-bottom:.45rem;line-height:1.7;}
blockquote cite{display:block;font-family:var(--sans);font-style:normal;color:var(--ink-dim);
  font-size:.82rem;margin-top:.55rem;font-weight:400;}
.tag-note{color:#b5654d;font-size:.78rem;}
:root[data-theme="dark"] .tag-note,
:root:not([data-theme="light"]) .tag-note{color:#d69a86;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .tag-note{color:#d69a86;}}
.himeka{font-size:.92rem;margin:.85rem 0 0;padding:.7rem .9rem;background:var(--accent-soft);
  border-left:2px solid var(--accent-line);border-radius:0 8px 8px 0;line-height:1.8;}
.himeka b{color:var(--accent);font-weight:700;}
.qmeta{margin:.65rem 0 0;font-size:.82rem;}

/* quote detail */
.qdetail{position:relative;}
.qdetail .bigmark{position:absolute;top:-.6rem;left:-.3rem;font-family:var(--serif);font-size:5rem;
  color:var(--accent);opacity:.13;line-height:1;pointer-events:none;user-select:none;}
.qdetail blockquote.big{font-size:1.32rem;line-height:1.95;margin:.5rem 0 1.3rem;position:relative;}
.himeka-box{background:var(--surface);border:1px solid var(--edge);border-radius:14px;
  padding:1rem 1.15rem;margin:1.35rem 0;box-shadow:0 1px 2px var(--shadow);}
.himeka-box h2{margin:0 0 .5rem;font-size:.98rem;color:var(--accent);font-family:var(--sans);font-weight:700;}
.himeka-box p{margin:0;line-height:1.85;}
.tagrow{display:flex;flex-wrap:wrap;gap:.45rem;margin:1.15rem 0;}
.tagrow a{background:var(--surface);border:1px solid var(--edge);border-radius:7px;
  padding:.18rem .55rem;font-size:.8rem;color:var(--ink-dim);}
.tagrow a:hover{text-decoration:none;color:var(--accent);border-color:var(--accent-line);}
.watch{font-weight:700;font-size:.9rem;}
.pager{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin:1.7rem 0;
  padding-top:1rem;border-top:1px solid var(--edge);font-size:.87rem;}
.pager .sp{flex:1;}
.pager .nx{text-align:right;}

.entrylist{list-style:none;padding:0;}
.entrylist li{border-bottom:1px solid var(--edge-soft);}
.entrylist a{display:block;padding:.9rem 0;color:var(--ink);}
.entrylist time{display:block;color:var(--ink-dim);font-size:.78rem;}
.entrylist b{font-weight:500;font-family:var(--serif);}
.prose p{margin:1rem 0;}
.prose{line-height:1.9;}

.snslist{list-style:none;padding:0;}
.snslist li{border-bottom:1px solid var(--edge-soft);}
.snslist a{display:flex;align-items:baseline;gap:.7rem;padding:1rem 0;color:var(--ink);}
.snslist a:hover{text-decoration:none;color:var(--accent);}
.snslist .ic{width:1.5rem;text-align:center;}
.snslist .nm{font-weight:500;font-family:var(--serif);}
.snslist .hd{color:var(--ink-dim);font-size:.82rem;}
.linklist{list-style:none;padding:0;}
.linklist li{padding:.55rem 0;border-bottom:1px solid var(--edge-soft);}

footer.site{border-top:1px solid var(--edge);background:var(--surface);padding:1.9rem 0;margin-top:2rem;}
footer.site p{margin:.35rem 0;font-size:.82rem;color:var(--ink-dim);}
footer.site .fl{display:flex;flex-wrap:wrap;gap:.3rem 1rem;}
footer.site .sns{font-size:1.1rem;letter-spacing:.45rem;}
.note-banner{background:var(--accent-soft);border:1px solid var(--accent-line);border-radius:10px;
  padding:.6rem .85rem;font-size:.8rem;color:var(--ink-dim);margin:0 0 1rem;}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px;}
</style>

<header class="site"><div class="wrap">
  <a class="brand" href="#/">昭和上等あんこ姫の隠れ家</a>
  <nav class="site">
    <a href="#/" data-nav="/">ホーム</a>
    <a href="#/meigen" data-nav="/meigen">名言</a>
    <a href="#/diary" data-nav="/diary">日記</a>
    <a href="#/sns" data-nav="/sns">SNS</a>
    <button class="themebtn" id="themebtn" title="表示テーマを切り替え" aria-label="表示テーマを切り替え">◑</button>
  </nav>
</div></header>
<div class="wrap" id="crumb"></div>
<main class="wrap" id="app"></main>
<footer class="site"><div class="wrap">
  <p class="fl" id="foot-links"></p>
  <p class="sns" id="foot-sns"></p>
  <p>&copy; 昭和上等あんこ姫の隠れ家 &nbsp;/&nbsp; これは確認用プレビューです</p>
</div></footer>

<script>
const DATA = __DATA__;
const {site, quotes, people, diary, themes, groups} = DATA;
const byNo = Object.fromEntries(quotes.map(q => [q.no, q]));
const personBySlug = Object.fromEntries(people.map(p => [p.slug, p]));
const personByName = Object.fromEntries(people.map(p => [p.name, p]));
const themeBySlug = Object.fromEntries(themes.map(t => [t.slug, t]));
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pad = n => String(n).padStart(3, '0');

function crumbs(items){
  document.getElementById('crumb').innerHTML = items.length
    ? '<nav class="crumb">' + items.map((it,i) =>
        (it[1] ? `<a href="${it[1]}">${esc(it[0])}</a>` : `<span>${esc(it[0])}</span>`)
        + (i < items.length-1 ? '<i>›</i>' : '')).join('') + '</nav>'
    : '';
}
function qBlock(q, opts={}){
  const linkPerson = opts.personLink !== false;
  const p = personByName[q.person];
  return `<blockquote>${q.en ? `<span class="en">${esc(q.en)}</span>` : ''}「${esc(q.quote)}」
    <cite>― ${linkPerson && p ? `<a href="#/person/${p.slug}">${esc(q.person)}</a>` : esc(q.person)}${q.attribution ? `（${esc(q.attribution)}）` : ''}${q.note ? ` <span class="tag-note">${esc(q.note)}</span>` : ''}</cite></blockquote>`;
}

const views = {
  home(){
    crumbs([]);
    const recent = quotes.slice(-3).reverse();
    return `<section class="hero">
      <div class="mark">姫</div>
      <h1>昭和上等あんこ姫の隠れ家</h1>
      <p>${esc(site.tagline)}</p>
    </section>
    <section class="cards">
      <a class="card" href="#/meigen"><h2>名言</h2><p>心に残った言葉を${quotes.length}個。解説はひめか＆黒猫ゾーマ（名言喫茶）。</p></a>
      <a class="card" href="#/diary"><h2>日記</h2><p>日々のできごと。動画は YouTube「子ども15匹＋旦那1」でも。</p></a>
      <a class="card" href="#/sns"><h2>SNS</h2><p>X・Instagram・TikTok・YouTube。各アカウントへの入り口。</p></a>
    </section>
    <section>
      <h2 class="sectitle">最近ふれた名言</h2>
      <ul class="qlist">${recent.map(q => `<li><a href="#/q/${pad(q.no)}"><span class="qno">No.${pad(q.no)}</span>${esc(q.quote)}<span class="qby">— ${esc(q.person)}</span></a></li>`).join('')}</ul>
      <p style="margin-top:1rem"><a class="more" href="#/meigen/all">すべての名言を読む ›</a></p>
    </section>
    <section>
      <h2 class="sectitle">昭和上等あんこ姫の活動</h2>
      <ul class="linklist">
        <li><a href="${site.funnel.youtube_main}">YouTube「子ども15匹＋旦那1」— 日々の事件と日記</a></li>
        <li><a href="${site.funnel.youtube_meigen}">YouTube「ひめかとゾーマの名言喫茶」</a></li>
        <li><a href="${site.funnel.note}">note — 詳しい体験記・解決編</a></li>
      </ul>
    </section>`;
  },
  meigen(){
    crumbs([['ホーム','#/'],['名言','']]);
    const tcount = t => quotes.filter(q => (q.categories||[]).includes(t.name)).length;
    const pByGroup = {};
    people.forEach(p => (pByGroup[p.group] ||= []).push(p));
    return `<p class="eyebrow">ひめかとゾーマの名言喫茶</p>
      <h1>名言</h1>
      <p class="lead">${quotes.length}個の名言を、人物やテーマからも探せます。気になる入り口からどうぞ。</p>
      <p class="muted">解説は、あんこ姫の連載キャラクター「ひめか」と黒猫「ゾーマ」が担当。</p>
      <p><a class="more" href="#/meigen/all">すべての名言を1ページで読む ›</a></p>
      <section><h2 class="sectitle">テーマから探す</h2><div class="chips">
        ${themes.map(t => `<a class="chip" href="#/theme/${t.slug}">「${t.name}」の名言 <b>${tcount(t)}</b></a>`).join('')}
      </div></section>
      <section><h2 class="sectitle">人物から探す</h2>
        ${groups.filter(g => pByGroup[g]).map(g => `<h3>${esc(g)}</h3><div class="chips">
          ${pByGroup[g].map(p => `<a class="chip" href="#/person/${p.slug}">${esc(p.name)} <b>${p.nos.length}</b></a>`).join('')}
        </div>`).join('')}
      </section>`;
  },
  all(){
    crumbs([['ホーム','#/'],['名言','#/meigen'],['すべての名言','']]);
    return `<h1>すべての名言</h1><p class="lead">あんこ姫が集めた名言に、ひめかとゾーマが解説をつけています。</p>` +
      groups.map(g => {
        const qs = quotes.filter(q => q.group === g);
        if(!qs.length) return '';
        return `<section><h2 class="sectitle">${esc(g)}</h2>` + qs.map(q => `<article class="qcard">
          ${qBlock(q)}
          ${q.commentary ? `<p class="himeka"><b>ひめか</b>：${esc(q.commentary)}</p>` : ''}
          <p class="qmeta"><a href="#/q/${pad(q.no)}">No.${pad(q.no)} の詳細 ›</a></p>
        </article>`).join('') + `</section>`;
      }).join('');
  },
  quote(slug){
    const q = byNo[parseInt(slug,10)];
    if(!q) return views.notfound();
    const p = personByName[q.person];
    crumbs([['ホーム','#/'],['名言','#/meigen'],[q.person, p ? `#/person/${p.slug}` : ''],[`No.${pad(q.no)}`,'']]);
    const prev = byNo[q.no-1], next = byNo[q.no+1];
    const same = quotes.filter(x => x.person === q.person && x.no !== q.no).slice(0,6);
    return `<article class="qdetail">
      <span class="bigmark" aria-hidden="true">「</span>
      <p class="eyebrow">No.${pad(q.no)}</p>
      <blockquote class="big">${q.en ? `<span class="en">${esc(q.en)}</span>` : ''}「${esc(q.quote)}」
        <cite>― ${p ? `<a href="#/person/${p.slug}">${esc(q.person)}</a>` : esc(q.person)}${q.attribution ? `（${esc(q.attribution)}）` : ''}${q.note ? ` <span class="tag-note">${esc(q.note)}</span>` : ''}</cite></blockquote>
      ${q.commentary ? `<div class="himeka-box"><h2>💬 この言葉が伝えていること／今の時代なら？</h2><p><b>ひめか</b>：${esc(q.commentary)}</p></div>` : ''}
      ${(q.categories||[]).length ? `<p class="tagrow">${q.categories.map(c => { const t = themes.find(t=>t.name===c); return `<a href="#/theme/${t?t.slug:''}">#${esc(c)}</a>`; }).join('')}</p>` : ''}
      ${q.youtube ? `<p class="watch"><a href="${q.youtube}">▶ 関連動画（YouTube）</a></p>` : ''}
    </article>
    <nav class="pager">
      ${prev ? `<a href="#/q/${pad(prev.no)}">‹ No.${pad(prev.no)}</a>` : '<span class="sp"></span>'}
      <a href="#/meigen/all">一覧</a>
      ${next ? `<a class="nx" href="#/q/${pad(next.no)}">No.${pad(next.no)} ›</a>` : '<span class="sp"></span>'}
    </nav>
    ${same.length ? `<section><h2 class="sectitle">${esc(q.person)} の名言をもっと</h2>
      <ul class="qlist">${same.map(s => `<li><a href="#/q/${pad(s.no)}"><span class="qno">No.${pad(s.no)}</span>${esc(s.quote)}</a></li>`).join('')}</ul>
      ${p ? `<p style="margin-top:1rem"><a class="more" href="#/person/${p.slug}">${esc(q.person)} の一覧へ ›</a></p>` : ''}
    </section>` : ''}`;
  },
  person(slug){
    const p = personBySlug[slug];
    if(!p) return views.notfound();
    crumbs([['ホーム','#/'],['名言','#/meigen'],['人物から探す','#/meigen'],[p.name,'']]);
    const qs = p.nos.map(n => byNo[n]);
    return `<h1>${esc(p.name)}の名言</h1>
      ${p.bio ? `<p class="lead">${esc(p.bio)}</p>` : `<p class="note-banner">※ この人物の紹介文はこれから追加します（Phase 2）。</p>`}
      <p class="muted">${esc(p.group)}｜${qs.length}件</p>
      ${qs.map(q => `<article class="qcard">${qBlock(q,{personLink:false})}
        ${q.commentary ? `<p class="himeka"><b>ひめか</b>：${esc(q.commentary)}</p>` : ''}
        <p class="qmeta"><a href="#/q/${pad(q.no)}">No.${pad(q.no)} の詳細 ›</a></p></article>`).join('')}`;
  },
  theme(slug){
    const t = themeBySlug[slug];
    if(!t) return views.notfound();
    crumbs([['ホーム','#/'],['名言','#/meigen'],['テーマから探す','#/meigen'],[`「${t.name}」の名言`,'']]);
    const qs = quotes.filter(q => (q.categories||[]).includes(t.name));
    return `<h1>「${esc(t.name)}」の名言</h1><p class="muted">${qs.length}件</p>
      ${qs.map(q => `<article class="qcard">${qBlock(q)}
        ${q.commentary ? `<p class="himeka"><b>ひめか</b>：${esc(q.commentary)}</p>` : ''}
        <p class="qmeta"><a href="#/q/${pad(q.no)}">No.${pad(q.no)} の詳細 ›</a></p></article>`).join('')}`;
  },
  diaryIndex(){
    crumbs([['ホーム','#/'],['日記','']]);
    return `<h1>日記</h1><p class="lead">${esc(site.diary_intro)}</p>
      <ul class="linklist">
        <li><a href="${site.funnel.youtube_main}">日々の動画は YouTube「子ども15匹＋旦那1」でも配信中</a></li>
        <li><a href="${site.funnel.note}">note でも日々のできごとを発信しています</a></li>
      </ul>
      ${diary.length ? `<ul class="entrylist">${diary.map(e => `<li><a href="#/diary/${e.slug}">${e.date ? `<time>${esc(e.date)}</time>` : ''}<b>${esc(e.title)}</b></a></li>`).join('')}</ul>` : '<p class="muted">まだ記事がありません。</p>'}`;
  },
  diaryEntry(slug){
    const e = diary.find(d => d.slug === slug);
    if(!e) return views.notfound();
    crumbs([['ホーム','#/'],['日記','#/diary'],[e.title,'']]);
    return `<article><h1>${esc(e.title)}</h1>${e.date ? `<p class="muted"><time>${esc(e.date)}</time></p>` : ''}
      <div class="prose">${e.html}</div>
      ${e.youtube ? `<p class="watch" style="margin-top:1.2rem"><a href="${e.youtube}">▶ この日の関連動画を見る</a></p>` : ''}</article>
      <nav class="pager"><a href="#/diary">‹ 日記の一覧へ</a></nav>`;
  },
  sns(){
    crumbs([['ホーム','#/'],['SNS','']]);
    return `<h1>SNS</h1><p class="lead">下のリンクから、昭和上等あんこ姫の各SNSに移動できます。</p>
      <ul class="snslist">${site.sns.map(s => `<li><a href="${s.url}"><span class="ic">${s.icon}</span><span class="nm">${esc(s.label)}</span> <span class="hd">${esc(s.handle)}</span></a></li>`).join('')}</ul>
      <p class="muted">今後YouTubeチャンネルが増えたら、このリストに同じ形式で追加していきます。</p>`;
  },
  notfound(){ crumbs([['ホーム','#/']]); return `<h1>ページが見つかりません</h1><p><a class="more" href="#/">ホームに戻る ›</a></p>`; }
};

function route(){
  const h = (location.hash || '#/').slice(1);
  const seg = h.split('/').filter(Boolean);
  let html;
  if(seg.length === 0) html = views.home();
  else if(seg[0] === 'meigen' && seg[1] === 'all') html = views.all();
  else if(seg[0] === 'meigen') html = views.meigen();
  else if(seg[0] === 'q') html = views.quote(seg[1]);
  else if(seg[0] === 'person') html = views.person(seg[1]);
  else if(seg[0] === 'theme') html = views.theme(seg[1]);
  else if(seg[0] === 'diary' && seg[1]) html = views.diaryEntry(seg[1]);
  else if(seg[0] === 'diary') html = views.diaryIndex();
  else if(seg[0] === 'sns') html = views.sns();
  else html = views.notfound();
  const app = document.getElementById('app');
  app.innerHTML = html;
  app.style.animation = 'none'; app.offsetHeight; app.style.animation = '';
  const top = '/' + (seg[0] || '');
  document.querySelectorAll('nav.site a[data-nav]').forEach(a =>
    a.classList.toggle('on', a.dataset.nav === top || (top==='/' && a.dataset.nav==='/')));
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', route);

// footer
document.getElementById('foot-links').innerHTML =
  `<a href="${site.funnel.youtube_main}">YouTube「子ども15匹＋旦那1」</a><a href="${site.funnel.note}">note</a><a href="#/sns">SNS一覧</a>`;
document.getElementById('foot-sns').innerHTML = site.sns.map(s => `<a href="${s.url}" title="${esc(s.name)}">${s.icon}</a>`).join(' ');

// theme toggle
const tb = document.getElementById('themebtn');
const KEY = 'ancohime-theme';
try{ const t = localStorage.getItem(KEY); if(t) document.documentElement.dataset.theme = t; }catch(e){}
tb.addEventListener('click', () => {
  const cur = document.documentElement.dataset.theme;
  const mqDark = window.matchMedia('(prefers-color-scheme:dark)').matches;
  const next = cur === 'dark' ? 'light' : cur === 'light' ? 'dark' : (mqDark ? 'light' : 'dark');
  document.documentElement.dataset.theme = next;
  try{ localStorage.setItem(KEY, next); }catch(e){}
});

route();
</script>
"""

out = HTML.replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
(ROOT / "preview.html").write_text(out, encoding="utf-8")
print(f"✓ preview.html を書き出し（{len(out)//1024} KB）")
