# あんこひめの隠れ家 — 静的サイト

ancohime.com を MuuMuu Sites から、自前の静的サイトへ移行するためのプロジェクト。
中身は Notion から抜き出したデータ（`data/`）＋日記の Markdown（`content/`）。
`build.py` が HTML 一式（`dist/`）を生成する。ホスティングは Cloudflare Pages を想定。

## なぜ移行したか
MuuMuu Sites（GMOペパボ・無料）には次の限界があり、ancohime.com を「本拠地」にするには不十分だった:
- ページ間のリンク（「戻る」など）が全部 notion.so に飛んでしまう（インラインリンクは内部リンクに変換されない仕様）
- 「Made with MuuMuu Sites」バッジが消せない（有料プランなし）
- ナビゲーション・デザインをほぼいじれない

この静的サイトなら: 内部リンク・パンくず・ナビが普通に動く／バッジなし／デザイン自由／ホスティング無料。

## セットアップ
```
python -m venv .venv
.venv\Scripts\python.exe -m pip install jinja2 markdown
```

## 使い方
```
.venv\Scripts\python.exe scripts\make_quotes.py   # data/quotes.json を再生成
.venv\Scripts\python.exe build.py                 # dist/ に書き出し
.venv\Scripts\python.exe build.py --serve         # ビルドしてプレビュー (http://localhost:8000)
```

## フォルダ
| 場所 | 中身 |
|---|---|
| `data/quotes.json` | 名言168件（No.・本文・人物・肩書き・カテゴリー・ひめか解説・英語原文・注記） |
| `data/people.json` | 人物ごとの紹介文（bio）。空でも動く。Phase 2 で各人物ページから移植 |
| `data/site.json` | サイト名・SNSリンク・YouTube/noteへの導線 |
| `content/diary/*.md` | 日記。1ファイル=1記事。ファイル名 `YYYY-MM-DD-なにか.md` |
| `templates/*.html` | Jinja2 テンプレート |
| `static/` | CSS・画像（そのまま dist/static/ にコピーされる） |
| `scripts/make_quotes.py` | Notion由来データを quotes.json に組み立てる（出典コメント付き） |
| `dist/` | 生成物。Git 管理しない |

## 生成されるページ（248ページ）
- `/` トップ
- `/meigen/` 名言トップ（テーマ・人物から探す）
- `/meigen/all/` すべての名言（1ページ）
- `/meigen/q/001/` … `/168/` 個別の名言
- `/meigen/person/p01/` … 人物別（68人）
- `/meigen/theme/ikikata|shigoto|chousen|doryoku|keiei/` テーマ別
- `/diary/`, `/diary/<slug>/` 日記
- `/sns/` SNS一覧
- `/404.html`

## 未完了（Phase 2 以降）
- 人物68人の紹介文（bio）を各 Notion 人物ページから移植（今は松下幸之助のみ）
- No.161〜168 は Notion DB 未登録（「名言を読む」にのみ存在）。カテゴリー未設定
- 「長嶋茂雄」表記ゆれ（人物一覧ページでは「長島茂雄」）→ 正しい「長嶋」に統一済み
- テーマページの導入文、名言トップの説明文の微調整
- デプロイ（Cloudflare Pages）＋ ancohime.com の DNS 切り替え
- 旧 MuuMuu Sites の URL からのリダイレクト方針
