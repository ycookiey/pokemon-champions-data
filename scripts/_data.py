"""data/ の読込と「収録済み」判定を一元化する共通モジュール.

build_coverage.py と validate_collected.py が、同じパス・同じ「収録済み」基準を
参照するための唯一の情報源。収録対象一覧 pokemon.json と収録 collected.json の読込、
および「収録済み = 技を MIN_MOVES 件以上持つ」という判定をここに集約する。

基準を変える (例: 最低技数を上げる) ときはこのファイルだけを直せば、
coverage 生成 (build_coverage) と PR 検証 (validate_collected) の双方に反映される。
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POKEMON_PATH = ROOT / "data" / "pokemon.json"
COLLECTED_PATH = ROOT / "data" / "collected.json"
# 技名マスタ (towakey/pokedex 由来。出自は docs/SOURCES.md、再生成は build_moves.py)。
MOVES_PATH = ROOT / "data" / "moves.json"

# 収録済みと見なす最低技数。空配列 (0技) は「未収録」であり収録済みにしない。
MIN_MOVES = 1


def load_pokemon() -> list:
    """収録対象一覧 pokemon.json を配列のまま読む (順序保持)."""
    return json.loads(POKEMON_PATH.read_text(encoding="utf-8"))


def load_collected(object_pairs_hook=None) -> dict:
    """収録 collected.json を {ポケモン名: [技名...]} として読む."""
    return json.loads(
        COLLECTED_PATH.read_text(encoding="utf-8"),
        object_pairs_hook=object_pairs_hook,
    )


def load_moves() -> list:
    """技名マスタ moves.json を技名の配列として読む (towakey/pokedex 由来)."""
    return json.loads(MOVES_PATH.read_text(encoding="utf-8"))


def is_collected(moves: object) -> bool:
    """収録済み判定: 技を MIN_MOVES 件以上持つ文字列リストか."""
    return isinstance(moves, list) and len(moves) >= MIN_MOVES
