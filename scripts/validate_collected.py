"""collected.json と収録対象一覧 pokemon.json を検証する (CI で PR 時に実行).

検査項目:
  - 収録対象一覧 pokemon.json が文字列の配列で、重複名・空/空白のみ・前後空白が無い
  - 技名マスタ moves.json が文字列の配列で、重複・空/空白のみ・前後空白が無い
  - collected.json が {ポケモン名: [技名...]} のオブジェクトである
  - 各キーが収録対象一覧 pokemon.json の名前と完全一致する
    (タイポ・表記揺れ・収録対象外フォームを弾く)
  - 各値が文字列の配列で、技を MIN_MOVES 件以上持つ (空配列を弾く)
  - 技名に空/空白のみ・前後空白が無い
  - 技リストに重複が無い
  - 各技名が技名マスタ moves.json (towakey/pokedex 由来の全技名) に実在する
    (OCR ゴミ・手編集タイポ・非正規表記を弾く)

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


def _validate_list_master(items: object, label: str) -> list:
    """名前/技名の配列マスタ自身の健全性を検証する (収録側と非対称にしない).

    pokemon.json (収録対象一覧) と moves.json (技名マスタ) は同じ
    「文字列の配列・重複なし・空/空白や前後空白なし」を満たすべきなので共通化する。
    """
    if not isinstance(items, list):
        return [f"{label} は配列である必要があります"]
    if not all(isinstance(n, str) for n in items):
        return [f"{label} の要素は全て文字列である必要があります"]

    errors: list = []
    blank = sum(1 for n in items if not n.strip())
    if blank:
        errors.append(f"{label} に空または空白のみの項目が {blank} 件あります")
    spaced = sorted(n for n in items if n != n.strip())
    if spaced:
        errors.append(f"{label} に前後空白付きの項目があります: {spaced}")
    dups = sorted(n for n, c in Counter(items).items() if c > 1)
    if dups:
        errors.append(f"{label} に重複があります: {dups}")
    return errors


def _validate_moves_no_variants(moves: list) -> list:
    """技名マスタに表記ゆれ (NFKC/スペースで同一になる別表記) が無いか検証する.

    マスタに同一技の別表記が両方あると、collected 側の非正規表記もマスタ照合を
    通ってしまい「非正規表記を弾く」目的が崩れる。build_moves.py が正規表記 1 件に
    集約するので通常は発生しないが、手編集での混入を防ぐ最後の砦。
    """
    if not isinstance(moves, list) or not all(isinstance(m, str) for m in moves):
        return []  # 形式不正は _validate_list_master が報告済み
    groups: dict[str, list] = {}
    for m in moves:
        groups.setdefault(_data.normalize_move_key(m), []).append(m)
    variants = sorted(v for v in groups.values() if len(v) > 1)
    if variants:
        return [
            "技名マスタ moves.json に表記ゆれ (NFKC/スペースで同一になる別表記) "
            f"があります: {variants} — 正規表記 1 件に統一 (build_moves.py で再生成)"
        ]
    return []


def main() -> int:
    # マスタ自体を先に検証する (マスタが壊れていれば収録側の検証は無意味)
    names_list = _data.load_pokemon()
    moves_list = _data.load_moves()
    master_errors = _validate_list_master(names_list, "収録対象一覧 pokemon.json")
    master_errors += _validate_list_master(moves_list, "技名マスタ moves.json")
    master_errors += _validate_moves_no_variants(moves_list)
    if master_errors:
        print(f"マスタの検証失敗 ({len(master_errors)} 件):")
        for e in master_errors:
            print(f"  - {e}")
        return 1
    names = set(names_list)
    known_moves = set(moves_list)

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
                f"収録対象一覧 (data/pokemon.json) に無いポケモン名: {key!r} "
                "— 表記が収録対象一覧と一致しているか確認してください"
            )
        if not isinstance(moves, list) or not all(
            isinstance(m, str) for m in moves
        ):
            errors.append(f"{key!r} の技リストは文字列の配列である必要があります")
            continue
        if len(moves) < _data.MIN_MOVES:
            errors.append(
                f"{key!r} の技が {len(moves)} 件しかありません "
                f"— 収録済みは技を {_data.MIN_MOVES} 件以上必要です (空配列は不可)"
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
        unknown = sorted(set(m for m in moves if m.strip()) - known_moves)
        if unknown:
            errors.append(
                f"{key!r} に技名マスタ (data/moves.json) に無い技名があります: "
                f"{unknown} — OCR 誤読・タイポ・非正規表記の可能性。正規名へ修正してください"
            )

    if errors:
        print(f"検証失敗 ({len(errors)} 件):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        f"検証OK: 収録対象一覧 {len(names)} 種 / 技名マスタ {len(known_moves)} 技 / "
        f"収録 {len(collected)} 種、全キーが収録対象一覧と一致・全技名がマスタに実在"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
