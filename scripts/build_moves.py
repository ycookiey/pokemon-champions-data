"""towakey/pokedex (MIT) の waza_list.json から技名マスタ data/moves.json を生成する.

PR 検証 (validate_collected.py) が「collected.jsonl の技名が実在する正規名か」を
照合するための技名一覧を作る。公開リポジトリ towakey/pokedex の各世代
`waza_list.json` を union した、ゲーム内日本語表記の**全技名のソート済み配列**。

このリポジトリは技名の照合しか行わないため type/pp は持たず、名前だけを出力する
(技マスタの完全版 = id/type/pp 付きは収集ツール側 ch-data-collector が保持)。

出自・ライセンスは docs/SOURCES.md に記載。固定 commit はこのファイルの
PINNED_COMMIT が正本 (SOURCES.md はこれを転記する)。

Usage:
    python scripts/build_moves.py          # 固定 commit を clone して生成 (推奨)
    python scripts/build_moves.py <dir>    # 既存の pokedex clone を使う (オフライン)

<dir> は `pokedex/` ディレクトリを含む clone のルート。
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

import _data

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "moves.json"
POKEDEX_URL = "https://github.com/towakey/pokedex"
# docs/SOURCES.md の固定 commit はこの値を転記すること (ここが正本)。
PINNED_COMMIT = "d89793ca662e0f85c41d5306028b5418c78f30de"

# towakey/pokedex の世代ディレクトリを古い順に並べる。同一技の世代間表記ゆれ
# (全角/半角・スペース有無) は最新世代の綴りを正規とする (Champions は最新作
# Scarlet_Violet に最も近いため)。GEN_ORDER 外の未知世代は最古扱い (-1)。
GEN_ORDER = [
    "Red_Green_Blue_Pikachu",
    "Gold_Silver_Crystal",
    "Ruby_Sapphire_Emerald",
    "FireRed_LeafGreen",
    "Diamond_Pearl_Platinum",
    "HeartGold_SoulSilver",
    "Black_White",
    "Black2_White2",
    "X_Y",
    "OmegaRuby_AlphaSapphire",
    "Sun_Moon",
    "UltraSun_UltraMoon",
    "Sword_Shield",
    "LegendsArceus",
    "Scarlet_Violet",
    "LegendsZA",
]


def _gen_rank(gen: str) -> int:
    return GEN_ORDER.index(gen) if gen in GEN_ORDER else -1


def _force_rmtree(path: Path) -> None:
    """読み取り専用の .git オブジェクトごと temp clone を消す (Windows 対策)."""

    def on_error(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    # Python 3.12+ は onexc、それ以前は onerror。両対応。
    try:
        import shutil

        shutil.rmtree(path, onexc=lambda f, p, e: on_error(f, p, e))
    except TypeError:
        import shutil

        shutil.rmtree(path, onerror=on_error)


def _clone_pinned(dest: Path) -> None:
    """固定 commit だけを浅く取得する (reachable SHA fetch)."""
    subprocess.run(["git", "init", "-q", str(dest)], check=True)
    git = ["git", "-C", str(dest)]
    subprocess.run([*git, "remote", "add", "origin", POKEDEX_URL], check=True)
    subprocess.run(
        [*git, "fetch", "-q", "--depth", "1", "origin", PINNED_COMMIT], check=True
    )
    subprocess.run([*git, "checkout", "-q", "--detach", "FETCH_HEAD"], check=True)


def build(src_root: Path) -> int:
    src = src_root / "pokedex"
    if not src.exists():
        print(f"pokedex dir not found: {src}")
        return 2

    # 全世代の waza_list.json を走査し、各技名が登場する最新世代の順位を記録する。
    # 文字列値しか持たないスキーマ違いのキー (フィールド名の紛れ込み) は dict 情報の
    # 有無で除外する。
    best_rank: dict[str, int] = {}
    for waza_list_path in sorted(src.glob("*/waza_list.json")):
        rank = _gen_rank(waza_list_path.parent.name)
        wl = json.loads(waza_list_path.read_text(encoding="utf-8")).get(
            "waza_list", {}
        )
        for _game, moves in wl.items():
            if not isinstance(moves, dict):
                continue
            for name, info in moves.items():
                if isinstance(info, dict) and info:
                    if rank > best_rank.get(name, -2):
                        best_rank[name] = rank

    # 表記ゆれキーで群化し、各群から正規表記 1 件を選ぶ。最新世代を優先し、同順位は
    # NFKC 正規形・スペース無しを優先 (安定した決定的選択)。
    def _pick_key(name: str) -> tuple:
        nfkc = unicodedata.normalize("NFKC", name)
        return (
            best_rank[name],            # 新しい世代ほど優先
            nfkc == name,               # 既に NFKC 正規形なら優先
            " " not in name and "　" not in name,  # スペース無しを優先
            name,
        )

    groups: dict[str, str] = {}
    collapsed: dict[str, list[str]] = {}
    for name in best_rank:
        k = _data.normalize_move_key(name)
        collapsed.setdefault(k, []).append(name)
        if k not in groups or _pick_key(name) > _pick_key(groups[k]):
            groups[k] = name

    # 集約された (= 複数表記を 1 件に潰した) 群を可視化する。
    for k, variants in sorted(collapsed.items()):
        if len(variants) > 1:
            chosen = groups[k]
            dropped = sorted(v for v in variants if v != chosen)
            print(f"  表記ゆれ集約: {chosen!r} ← {dropped}")

    moves_out = sorted(groups.values())
    OUT_PATH.write_text(
        json.dumps(moves_out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"全技名 {len(moves_out)} 件を {OUT_PATH} に書き出した")
    return 0


def main() -> int:
    # 既存 clone のパスが渡されればそれを使う (オフライン/開発用)。
    if len(sys.argv) >= 2:
        return build(Path(sys.argv[1]))

    # 引数なし: 固定 commit を temp に clone して生成し、後始末する。
    tmp = Path(tempfile.mkdtemp(prefix="pokedex-"))
    try:
        print(f"clone {POKEDEX_URL}@{PINNED_COMMIT[:10]} ...")
        _clone_pinned(tmp)
        return build(tmp)
    finally:
        _force_rmtree(tmp)


if __name__ == "__main__":
    raise SystemExit(main())
