# コントリビューションガイド

未収録ポケモンの技データ提供を歓迎します。

まず [収録状況ページ](https://ycookiey.github.io/pokemon-champions-data/) で未収録を確認し（重複録画を避けるため）、[ch-data-collector](https://github.com/ycookiey/ch-data-collector) の [録画手順](https://github.com/ycookiey/ch-data-collector/blob/main/docs/recording-guide.md) で動画を撮って技データ `result.json` を出力します。あとは次のいずれかの方法で提出してください。

## 方法1: issue から提出（おすすめ）

リポジトリのクローンや手動でのファイル編集は不要です。

1. [「技データの提出」issue](https://github.com/ycookiey/pokemon-champions-data/issues/new?template=collect.yml) に `result.json` の中身（`{ポケモン名: [技名...]}` の JSON）を貼り付けて送信します。
2. 送信すると内容が検証され、問題なければデータ追加の Pull Request が自動で作成されます。不備があれば issue にその内容がコメントされるので、直して送信し直してください。

## 方法2: 自分で PR を作る

Git の操作に慣れている場合は直接どうぞ。

1. `data/collected.jsonl` に `{"ポケモン名": [技名...]}` の行を追記します（[収録対象一覧](data/pokemon.json) と同じ順に並べると、自動取込の出力と一致して衝突しにくくなります）。
2. Pull Request を作成します。CI（`scripts/validate_collected.py`）が下記の内容を検証します。

## 検証される内容

どちらの方法でも、以下が自動で検証されます。

- **ポケモン名**が[収録対象一覧](data/pokemon.json)の表記と一致すること。ch-data-collector の出力は正規化済みです。フォーム違いは一覧の表記に従います（例: `ライチュウ(アローラ)`, `ロトム(ヒート)`）。
- **技名**がすべて実在すること（OCR 誤読・タイポ・非正規表記を弾きます）。
- 技リストに**重複・空**が無いこと。

なお、技プールが元のフォームと共通のポケモン（メガシンカ等）は収録対象外です。

## ライセンス

提出フォームでの同意、または PR の送信をもって、追加するデータを **CC0 1.0**（パブリックドメイン献納、[data/LICENSE](data/LICENSE)）で提供することに同意したものとみなします。技名・ポケモン名等の原著作権は (株) ポケモン / 任天堂 / ゲームフリーク / クリーチャーズ に帰属します。
