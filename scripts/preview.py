"""収録状況ページをローカルでプレビューする.

site/coverage.json を生成 (build_coverage.py) してから site/ を HTTP 配信する。
ブラウザの fetch は file:// では動かないため、本番 (GitHub Pages) と同じく
HTTP 経由で配信して本番パリティを保つ。coverage.json は gitignore 対象。

Usage:
    python scripts/preview.py            # http://localhost:8000/ で配信
    python scripts/preview.py --port 9000
    python scripts/preview.py --no-open  # ブラウザを自動で開かない
"""

from __future__ import annotations

import argparse
import errno
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# scripts/ を import パス先頭に入れ、起動法 (python scripts/preview.py /
# python -m scripts.preview / 別 cwd) に依らず兄弟モジュールを解決する。
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _data
import build_coverage

SITE_DIR = _data.ROOT / "site"


def main() -> int:
    parser = argparse.ArgumentParser(description="収録状況ページをローカル配信する")
    parser.add_argument("--port", type=int, default=8000, help="待ち受けポート (既定: 8000)")
    parser.add_argument("--no-open", action="store_true", help="ブラウザを自動で開かない")
    args = parser.parse_args()

    # 本番デプロイと同じく coverage.json を生成してから配信する
    build_coverage.main()

    handler = partial(SimpleHTTPRequestHandler, directory=str(SITE_DIR))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            print(f"ポート {args.port} は使用中です。--port で別のポートを指定してください。")
            return 1
        raise

    url = f"http://localhost:{args.port}/"
    print(f"\nserving {SITE_DIR} at {url}  (Ctrl+C で停止)")

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
