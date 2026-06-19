"""収録状況 coverage.json を生成する.

収録対象一覧 (data/pokemon.json = Champions 実装ポケモン名の配列) と収録済み
(data/collected.jsonl = 1 行 = 1 ポケモン {ポケモン名: [技名...]}) を突合し、各ポケモンの収録状況を
site/coverage.json に出力する。GitHub Pages のステータスページがこれを読んで可視化する。
README のバッジ向けに site/badge.json (shields.io endpoint 形式) も同時に出力する。

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
BADGE_PATH = _data.ROOT / "site" / "badge.json"


def _badge_color(percent: float) -> str:
    if percent >= 80:
        return "1F883D"
    if percent >= 50:
        return "9A6700"
    if percent >= 20:
        return "BC4C00"
    return "CF222E"


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
    percent = round(100 * done / total, 1) if total else 0.0
    coverage = {
        "total": total,
        "collected": done,
        "uncollected": total - done,
        "percent": percent,
        "pokemon": entries,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    badge = {
        "schemaVersion": 1,
        "label": "収録",
        "message": f"{done}/{total} ({percent}%)",
        "color": _badge_color(percent),
    }
    BADGE_PATH.write_text(
        json.dumps(badge, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"coverage: {done}/{total} ({percent}%) -> {OUT_PATH}")
    print(f"badge: {badge['message']} ({badge['color']}) -> {BADGE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
