"""Точка входа приложения Money Calculator."""

from __future__ import annotations

import argparse
from pathlib import Path

from moneycalc.app import MoneyApp
from moneycalc.theme import enable_dpi_awareness


def main() -> None:
    parser = argparse.ArgumentParser(description="Money Calculator — учёт доходов и расходов")
    parser.add_argument(
        "--data",
        type=Path,
        default=None,
        help="путь к файлу данных (по умолчанию — %APPDATA%\\MoneyCalculator\\data.json)",
    )
    args = parser.parse_args()

    enable_dpi_awareness()
    app = MoneyApp(args.data)
    app.mainloop()


if __name__ == "__main__":
    main()
