"""Supermarket POS entry point — Desktop application."""
from __future__ import annotations


def main() -> None:
    from supermarket_pos.ui.desktop_app import main as desktop_main
    desktop_main()


if __name__ == "__main__":
    main()