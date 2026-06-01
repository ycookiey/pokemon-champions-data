"""collected.json と母集合 pokemon.json を検証する (CI で PR 時に実行).

検査項目:
  - 母集合 pokemon.json が文字列の配列で、重複名・空/空白のみ・前後空白が無い
  - collected.json が {ポケモン名: [技名...]} のオブジェクトである
  - 各キーが母集合 pokemon.json の名前と完全一致する
    (タイポ・表記揺れ・収集対象外フォームを弾く)
  - 各値が文字列の配列で、技を MIN_MOVES 件以上持つ (空配列を弾く)
  - 技名に空/空白のみ・前後空白が無い
  - 技リストに重複が無い

不正があれば一覧を表示して exit 1 (CI 失敗)。

Usage:
    python scripts/validate_collected.py
"""

from __future__ import annotations

from collections import Counter

import _data


def _reject_duplicate_keys(pairs: list) -> dict:
    """JSON オブジェクトの重複キーを弾く (後勝ちで黙って捨てられるのを防ぐ)."""
    seen: set = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(f"collected.json にキー重複があります: {key!r}")
        seen.add(key)
    return dict(pairs)


def _validate_master(names: object) -> list:
    """母集合 pokemon.json 自身の健全性を検証する (収集側と非対称にしない)."""
    if not isinstance(names, list):
        return ["pokemon.json は配列である必要があります"]
    if not all(isinstance(n, str) for n in names):
        return ["pokemon.json の要素は全て文字列である必要があります"]

    errors: list = []
    blank = sum(1 for n in names if not n.strip())
    if blank:
        errors.append(f"pokemon.json に空または空白のみの名前が {blank} 件あります")
    spaced = sorted(n for n in names if n != n.strip())
    if spaced:
        errors.append(f"pokemon.json に前後空白付きの名前があります: {spaced}")
    dups = sorted(n for n, c in Counter(names).items() if c > 1)
    if dups:
        errors.append(f"pokemon.json に重複名があります: {dups}")
    return errors


def main() -> int:
    # 母集合自体を先に検証する (母集合が壊れていれば収集側の検証は無意味)
    names_list = _data.load_pokemon()
    master_errors = _validate_master(names_list)
    if master_errors:
        print(f"母集合 pokemon.json の検証失敗 ({len(master_errors)} 件):")
        for e in master_errors:
            print(f"  - {e}")
        return 1
    names = set(names_list)

    try:
        collected = _data.load_collected(object_pairs_hook=_reject_duplicate_keys)
    except ValueError as e:
        print(e)
        return 1

    if not isinstance(collected, dict):
        print("collected.json はオブジェクト {ポケモン名: [技名...]} である必要があります")
        return 1

    errors: list = []
    for key, moves in collected.items():
        if key not in names:
            errors.append(
                f"母集合 (data/pokemon.json) に無いポケモン名: {key!r} "
                "— 表記が母集合と一致しているか確認してください"
            )
        if not isinstance(moves, list) or not all(
            isinstance(m, str) for m in moves
        ):
            errors.append(f"{key!r} の技リストは文字列の配列である必要があります")
            continue
        if len(moves) < _data.MIN_MOVES:
            errors.append(
                f"{key!r} の技が {len(moves)} 件しかありません "
                f"— 収集済みは技を {_data.MIN_MOVES} 件以上必要です (空配列は不可)"
            )
            continue
        blank = sum(1 for m in moves if not m.strip())
        if blank:
            errors.append(f"{key!r} に空または空白のみの技名が {blank} 件あります")
        spaced = sorted(m for m in moves if m != m.strip())
        if spaced:
            errors.append(f"{key!r} に前後空白付きの技名があります: {spaced}")
        dups = sorted(m for m, c in Counter(moves).items() if c > 1)
        if dups:
            errors.append(f"{key!r} に重複技があります: {dups}")

    if errors:
        print(f"検証失敗 ({len(errors)} 件):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        f"検証OK: 母集合 {len(names)} 種 / 収集 {len(collected)} 種、"
        "全キーが母集合と一致"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
