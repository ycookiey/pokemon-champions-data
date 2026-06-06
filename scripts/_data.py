"""data/ の読込と「収録済み」判定を一元化する共通モジュール.

build_coverage.py と validate_collected.py が、同じパス・同じ「収録済み」基準を
参照するための唯一の情報源。収録対象一覧 pokemon.json と収録 collected.jsonl の読込、
および「収録済み = 技を MIN_MOVES 件以上持つ」という判定をここに集約する。

基準を変える (例: 最低技数を上げる) ときはこのファイルだけを直せば、
coverage 生成 (build_coverage) と PR 検証 (validate_collected) の双方に反映される。
"""

from __future__ import annotations

import json
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POKEMON_PATH = ROOT / "data" / "pokemon.json"
# 収録データは 1 行 1 ポケモン ({名前: [技...]})。行が独立するので追加・削除・
# 並べ替えが 1 行差分になり、末尾要素のカンマ揺れによる差分ノイズが出ない。
COLLECTED_PATH = ROOT / "data" / "collected.jsonl"
# 技名マスタ (towakey/pokedex 由来。出自は docs/SOURCES.md、再生成は build_moves.py)。
MOVES_PATH = ROOT / "data" / "moves.json"

# 収録済みと見なす最低技数。空配列 (0技) は「未収録」であり収録済みにしない。
MIN_MOVES = 1


def load_pokemon() -> list:
    """収録対象一覧 pokemon.json を配列のまま読む (順序保持)."""
    return json.loads(POKEMON_PATH.read_text(encoding="utf-8"))


def _reject_dup_pairs(pairs: list) -> dict:
    """1 行の JSON オブジェクト内の重複キーを弾く (json 既定の後勝ちで黙って捨てるのを防ぐ)."""
    seen: set = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(f"同じポケモン名が複数あります: {key!r}")
        seen.add(key)
    return dict(pairs)


def load_collected() -> dict:
    """収録 collected.jsonl を {ポケモン名: [技名...]} として読む (1 行 1 ポケモン).

    各行は {名前: [技...]} の単一オブジェクト。行内・行間どちらの重複キーも ValueError
    で弾く (後勝ちで黙って欠落するのを防ぐ)。空行は無視する。
    """
    collected: dict = {}
    for lineno, raw in enumerate(
        COLLECTED_PATH.read_text(encoding="utf-8").splitlines(), 1
    ):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line, object_pairs_hook=_reject_dup_pairs)
        except json.JSONDecodeError as e:
            raise ValueError(f"collected.jsonl の {lineno} 行目が不正な JSON です: {e}")
        for key, value in obj.items():
            if key in collected:
                raise ValueError(
                    f"collected.jsonl にキー重複があります: {key!r} ({lineno} 行目)"
                )
            collected[key] = value
    return collected


def load_moves() -> list:
    """技名マスタ moves.json を技名の配列として読む (towakey/pokedex 由来)."""
    return json.loads(MOVES_PATH.read_text(encoding="utf-8"))


def normalize_move_key(name: str) -> str:
    """技名の表記ゆれ吸収キー (同一技の世代間表記ゆれを同一視する).

    towakey/pokedex は複数世代を収録するため、同じ技が世代により全角/半角
    (`１０まんボルト`↔`10まんボルト`)・スペース有無 (`クロスポイズン`↔`クロス ポイズン`)
    で揺れる。これらを潰したキーで「実質同一の技」を判定する。マスタは群ごとに
    正規表記 1 件へ集約し、collected 側の非正規表記はこのキーで弾く。

    ひらがな↔カタカナのカナ種の違い (`ねこにこばん`↔`ネコにこばん`) は、別の正規
    表記として両方残す (公式綴りが世代で変わった事例であり、誤って別技を併合する
    リスクも避ける)。
    """
    s = unicodedata.normalize("NFKC", name)
    return s.replace(" ", "").replace("　", "")


def is_collected(moves: object) -> bool:
    """収録済み判定: 技を MIN_MOVES 件以上持つ文字列リストか."""
    return isinstance(moves, list) and len(moves) >= MIN_MOVES


def validate_collected_dict(
    collected: object, names: set, known_moves: set
) -> list:
    """{ポケモン名: [技名...]} を収録対象一覧・技名マスタで検証しエラー文字列の配列を返す.

    PR 検証 (validate_collected.py) と issue 取込 (ingest_issue.py) が同一基準で
    検証するための唯一の情報源。基準がズレると「取込は通過したが PR マージ時の
    validate で落ちる」不整合が起きるため共有する。CI はランナー組み込みの python3
    (stdlib のみ) で走るので、ここも stdlib だけに保つ。

    検査: オブジェクト形式 / 各キーが収録対象一覧に実在 / 値が文字列配列 /
    技を MIN_MOVES 件以上持つ / 空・前後空白なし / 重複なし / 技名がマスタに実在。
    """
    if not isinstance(collected, dict):
        return ["{ポケモン名: [技名...]} のオブジェクトである必要があります"]

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
        if len(moves) < MIN_MOVES:
            errors.append(
                f"{key!r} の技が {len(moves)} 件しかありません "
                f"— 収録済みは技を {MIN_MOVES} 件以上必要です (空配列は不可)"
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
    return errors
