# データの出自

このリポジトリの各データファイルの出自・生成方法・ライセンスを明示する。

## data/moves.json — 技名マスタ

PR 検証 (`scripts/validate_collected.py`) が「`collected.json` の技名が実在する
正規名か」を照合するための、ゲーム内日本語表記の**全技名のソート済み配列**。

| 項目 | 内容 |
|---|---|
| 出典リポジトリ | [towakey/pokedex](https://github.com/towakey/pokedex) |
| ライセンス | MIT |
| 固定 commit | `50ee303b316970bad2dfe47186978860530a7fcf` (2026-05-10) — 正本は build_moves.py の `PINNED_COMMIT` |
| 生成スクリプト | [`scripts/build_moves.py`](../scripts/build_moves.py) |
| 件数 | 960 技 |

towakey/pokedex の全世代 `waza_list.json` を union した、ゲーム内日本語表記の
全技名。技名の照合のみに使うため、型・PP は持たず技名だけを保持する。

### 再生成手順

```
python scripts/build_moves.py
```

固定 commit を一時ディレクトリへ浅く clone して `data/moves.json` を生成する
(後始末まで自動)。既存の clone を使う場合は `python scripts/build_moves.py <dir>`
(`<dir>/pokedex/` が要る)。

towakey/pokedex に技が追加されたら、build_moves.py の `PINNED_COMMIT` を新しい
commit に更新して再生成し、`data/moves.json` と上表の commit を合わせて更新する。
