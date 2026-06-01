# pokemon-champions-data

ポケモンチャンピオンズの技データリポジトリ。収集ツールは [ch-data-collector](https://github.com/ycookiey/ch-data-collector)で、画面録画から自動で技を抽出する。（別リポジトリ・公開準備中）

## データ収録状況

GitHub Pages で公開（収録済み / 未収録を一覧・検索・フィルタ）:
**https://ycookiey.github.io/pokemon-champions-data/**

`data/collected.json` が更新されると、CI が収録状況を再生成して Pages を更新する。**録画前にこのページで未収録のポケモンを確認**すれば、重複録画を避けられる。

## コントリビューション

未収録ポケモンの技データ提供を歓迎します。手順・JSON形式・ポケモン名の表記ルールは [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## 構成

```
data/pokemon.json             収録対象 = Champions 実装ポケモン名 (210種)
data/collected.json           収録済み技データ {ポケモン名: [技名...]}
data/moves.json               技名マスタ (towakey/pokedex 由来の全技名。PR 検証に使用)
scripts/build_coverage.py     collected vs 収録対象 → site/coverage.json 生成
scripts/build_moves.py        towakey/pokedex から moves.json を再生成
scripts/validate_collected.py PR 検証 (収録対象一致・形式・技名がマスタに実在)
site/index.html               ステータスページ (coverage.json を可視化)
docs/SOURCES.md               各データの出自・生成方法・ライセンス
.github/workflows/            CI: PR=validate / main マージ=coverage 再生成→Pages deploy
```

収録対象は、個別に技プールが異なるポケモンのみとする。フォームが違うだけで覚える技が共通しているポケモン（メガシンカ・サイズ違い等）は除く。

## ライセンスと権利

- コード（`scripts/` `site/` `.github/`）は **MIT**（[LICENSE](LICENSE)）。
- データ（`data/`）は **CC0 1.0**（[data/LICENSE](data/LICENSE)）でパブリックドメインに献納。利用時に本リポジトリへのリンク・クレジットをいただけると嬉しいです（任意）。
- ポケモンの技名・ポケモン名等の原著作権は (株) ポケモン / 任天堂 / ゲームフリーク / クリーチャーズ に帰属します。本リポジトリはゲームをプレイして観測した事実情報の構造化データのみを対象とし、ゲーム本体のアセットは含みません。
