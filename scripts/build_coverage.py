"""収録状況 coverage.json を生成する.

収録対象一覧 (data/pokemon.json = Champions 実装ポケモン名の配列) と収録済み
(data/collected.jsonl = 1 行 = 1 ポケモン {ポケモン名: [技名...]}) を突合し、各ポケモンの収録状況を
site/coverage.json に出力する。GitHub Pages のステータスページがこれを読んで可視化する。

収録キーはポケモン名。技プールが個別に異なるフォーム (地方フォーム等) は
別名で収録対象一覧に含む (技プールがベースと共通のメガ・サイズ違い等は収録対象一覧から除く)。
「収録済み」の基準 (is_collected / MIN_MOVES) は _data.py に集約してある。

Usage:
    python scripts/build_coverage.py
"""

from __future__ import annotations

import json

import _data

OUT_PATH = _data.ROOT / "site" / "coverage.json"


def main() -> int:
    names = _data.load_pokemon()
    collected_moves = _data.load_collected()

    entries = []
    for name in names:
        moves = collected_moves.get(name)
        entries.append(
            {
                "name": name,
                "collected": _data.is_collected(moves),
                "move_count": len(moves) if isinstance(moves, list) else 0,
            }
        )

    total = len(entries)
    done = sum(1 for e in entries if e["collected"])
    coverage = {
        "total": total,
        "collected": done,
        "uncollected": total - done,
        "percent": round(100 * done / total, 1) if total else 0.0,
        "pokemon": entries,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"coverage: {done}/{total} ({coverage['percent']}%) -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
