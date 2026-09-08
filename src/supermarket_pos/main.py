"""Supermarket POS entry point — launches the web UI."""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Supermarket POS")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="Auto-reload on code changes")
    args = parser.parse_args(argv)

    import uvicorn
    from supermarket_pos.api.app import create_app

    app = create_app()
    print(f"\n  Supermarket POS running at http://{args.host}:{args.port}\n")
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()