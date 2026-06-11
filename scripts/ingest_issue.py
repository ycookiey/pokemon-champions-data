"""提出 issue の本文から技データを取込み、collected.jsonl へマージする (Action で実行).

Issue Form (.github/ISSUE_TEMPLATE/collect.yml) に貼られた collector 出力 JSON
({ポケモン名: [技名...]}) を本文から抽出し、収録対象一覧 pokemon.json・技名マスタ
moves.json で検証してから data/collected.jsonl へマージする。検証は PR 検証
(validate_collected.py) と同一の _data.validate_collected_dict を使うので、取込を
通ったデータは PR の CI でも必ず通る (基準のズレによる後段失敗を防ぐ)。

入力:
    環境変数 ISSUE_BODY (issue 本文)。無ければ argv[1] のファイルから読む (ローカル実行用)。
出力:
    成功時のみ data/collected.jsonl を書き換える。判定と人間向けサマリ (PR 本文 / issue
    コメントに使う markdown) を出力ディレクトリ (環境変数 INGEST_OUT、既定 ingest_out/)
    の result.json / summary.md に書く。終了コードは成功 0 / 検証失敗・解析不能 1。

CI はランナー組み込みの python3 (stdlib のみ) で走るため stdlib だけに依存する。

Usage:
    ISSUE_BODY="$(cat result.json)" python scripts/ingest_issue.py
    python scripts/ingest_issue.py result.json
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import _data

# issue 本文中の ```json ... ``` フェンスを最初の 1 個だけ取り出す
# (Issue Form の render: json はこの形で囲む)。言語指定の有無どちらも許容。
_FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


def _extract_json_text(body: str) -> str:
    """issue 本文から JSON テキストを取り出す.

    フェンス付きコードブロックがあればその中身、無ければ本文全体を JSON とみなす
    (フォームを使わず生 JSON を貼った場合・ローカルで result.json を直接渡した場合)。
    """
    m = _FENCE.search(body)
    return (m.group(1) if m else body).strip()


def _reject_duplicate_keys(pairs: list) -> dict:
    """JSON オブジェクトの重複キーを弾く (json.loads 既定の後勝ちで黙って捨てるのを防ぐ).

    bot 生成 PR は validate.yml が走らないため取込時のここがマージ前の唯一の砦。
    同名ポケモンを 2 度貼ると一方が黙って消える事故を防ぐ。
    """
    seen: set = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(f"同じポケモン名が複数あります: {key!r}")
        seen.add(key)
    return dict(pairs)


def _merge(current: dict, incoming: dict, order: list) -> tuple[dict, list, list, list]:
    """incoming を current にマージし、キーを母集合 order の並びに揃えて返す.

    既存と同名は更新 (置換) する。並び順を毎回 order (pokemon.json) に合わせることで、
    master・手動編集・自動取込が単一の正準順に一致し、差分の散らばりとマージ衝突を防ぐ。
    新規・更新・既存と同一 (no-op) の名前リストも返し、PR 本文で「黙って上書きした」
    状態にも「変わらない更新が水増しで載る」状態にもならないようにする。
    技集合が同じで配列順だけ異なるケースは「実質的な更新ではない」ため、現行を保持し
    unchanged 扱いとする (収集ツールの fuzzy match や閾値変更で発見順が揺れたぶんを
    PR 差分に出さないため)。
    """
    new_names = [k for k in incoming if k not in current]
    updated_names = [
        k for k in incoming
        if k in current and set(current[k]) != set(incoming[k])
    ]
    unchanged_names = [
        k for k in incoming
        if k in current and set(current[k]) == set(incoming[k])
    ]
    combined = dict(current)
    # 技集合が同じ (順序差のみ) ケースは current を保持し PR 差分を出さない.
    for k, v in incoming.items():
        if k in current and set(current[k]) == set(v):
            continue
        combined[k] = v
    index = {name: i for i, name in enumerate(order)}
    # 母集合順に並べる。order に無いキーは検証で弾かれるはずだが、念のため末尾へ安定配置。
    ordered = sorted(combined, key=lambda k: (index.get(k, len(order)), k))
    merged = {k: combined[k] for k in ordered}
    return merged, new_names, updated_names, unchanged_names


def _dumps_collected(d: dict) -> str:
    """collected.jsonl を 1 行 1 ポケモン ({名前: [技...]}) で書き出す.

    行が独立するので追加・更新・並べ替えが 1 行単位の差分になり、JSON object の
    「最後の要素だけカンマ無し」に起因する差分ノイズ (末尾が伸びると旧・最終行が
    丸ごと再表示される) も出ない。各行は json.loads で読める。
    """
    return "".join(
        json.dumps({k: v}, ensure_ascii=False) + "\n" for k, v in d.items()
    )


def _write_outputs(out_dir: Path, result: dict, summary_md: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "summary.md").write_text(summary_md, encoding="utf-8")


def main() -> int:
    out_dir = Path(os.environ.get("INGEST_OUT", "ingest_out"))

    body = os.environ.get("ISSUE_BODY")
    if body is None:
        if len(sys.argv) < 2:
            print("ISSUE_BODY 環境変数または引数のファイルパスが必要です", file=sys.stderr)
            return 1
        body = Path(sys.argv[1]).read_text(encoding="utf-8")

    text = _extract_json_text(body)
    try:
        incoming = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError) as e:
        msg = f"JSON として解析できませんでした: {e}"
        print(msg)
        _write_outputs(out_dir, {"ok": False, "errors": [msg]}, f"### 取込失敗\n\n- {msg}\n")
        return 1

    names_list = _data.load_pokemon()
    names = set(names_list)
    known_moves = set(_data.load_moves())
    errors = _data.validate_collected_dict(incoming, names, known_moves)
    if errors:
        print(f"検証失敗 ({len(errors)} 件):")
        for e in errors:
            print(f"  - {e}")
        md = "### 取込失敗 — データを修正して issue を編集してください\n\n" + "".join(
            f"- {e}\n" for e in errors
        )
        _write_outputs(out_dir, {"ok": False, "errors": errors}, md)
        return 1

    current = _data.load_collected()
    merged, new_names, updated_names, unchanged_names = _merge(current, incoming, names_list)
    _data.COLLECTED_PATH.write_text(_dumps_collected(merged), encoding="utf-8")

    lines = [f"- {n} ({len(incoming[n])} 技)" for n in new_names]
    ups = [f"- {n} ({len(incoming[n])} 技) ※既存を更新" for n in updated_names]
    md_parts = ["### 取込成功\n"]
    if new_names:
        md_parts.append(f"\n**新規収録 ({len(new_names)} 件)**\n\n" + "\n".join(lines) + "\n")
    if updated_names:
        md_parts.append(f"\n**更新 (既存を上書き) ({len(updated_names)} 件)**\n\n" + "\n".join(ups) + "\n")
    if unchanged_names:
        md_parts.append(f"\n既存と同一のため更新一覧から除外: {len(unchanged_names)} 件\n")
    summary_md = "".join(md_parts)
    print(summary_md)
    _write_outputs(
        out_dir,
        {"ok": True, "new": new_names, "updated": updated_names, "unchanged": unchanged_names},
        summary_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
