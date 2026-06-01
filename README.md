# pokemon-champions-data

ポケモンチャンピオンズの技データを**動画から収集して蓄積する**コミュニティデータリポジトリ。収集ツールは [ch-data-collector](https://github.com/ycookiey/ch-data-collector)（別リポジトリ・公開準備中）。

## データ収集状況

GitHub Pages で公開（収集済み / 未収集を一覧・検索・フィルタ）:
**https://ycookiey.github.io/pokemon-champions-data/**

`data/collected.json` が更新されると、CI が収集状況を再生成して Pages を更新する。**録画前にこのページで未収集のポケモンを確認**すれば、重複録画を避けられる。

## 貢献方法

未収集ポケモンの技データ収集を歓迎します。手順・JSON形式・ポケモン名の表記ルールは [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## 構成

```
data/pokemon.json          母集合 = Champions 実装ポケモン名 (210種)
data/collected.json        収集済み技データ {ポケモン名: [技名...]}
scripts/build_coverage.py  collected vs 母集合 → site/coverage.json 生成
site/index.html            ステータスページ (coverage.json を可視化)
.github/workflows/         CI: collected 変更 → coverage 再生成 → Pages deploy
```

母集合は、メガシンカ・サイズ違い等の「技プールがベースと共通のフォーム」を除き、個別に技プールが異なるポケモンのみを収集対象とする。

## ライセンスと権利

- コード（`scripts/` `site/` `.github/`）は **MIT**（[LICENSE](LICENSE)）。
- データ（`data/`）は **CC0 1.0**（[data/LICENSE](data/LICENSE)）でパブリックドメインに献納。利用時に本リポジトリへのリンク・クレジットをいただけると嬉しいです（任意）。
- ポケモンの技名・ポケモン名等の原著作権は (株) ポケモン / 任天堂 / ゲームフリーク / クリーチャーズ に帰属します。本リポジトリはゲームをプレイして観測した事実情報の構造化データのみを対象とし、ゲーム本体のアセットは含みません。
