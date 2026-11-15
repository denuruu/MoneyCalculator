"""Чтение и атомарная запись данных в локальный текстовый файл (JSON)."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

from .models import Store


class StorageError(Exception):
    """Файл данных не удалось прочитать."""


def default_data_path() -> Path:
    override = os.environ.get("MONEYCALC_DATA")
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home())
        return base / "MoneyCalculator" / "data.json"

    return Path.home() / ".local" / "share" / "MoneyCalculator" / "data.json"


def load(path: Path) -> Store:
    if not path.exists():
        return Store()

    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text) if text.strip() else {}
        if not isinstance(data, dict):
            raise ValueError("корневой элемент должен быть объектом")
        return Store.from_dict(data)
    except Exception as exc:  # noqa: BLE001 - любая ошибка чтения важна пользователю
        backup: Path | None = None
        try:
            backup = path.with_name(
                f"{path.stem}.corrupt-{time.strftime('%Y%m%d-%H%M%S')}{path.suffix}"
            )
            shutil.copy2(path, backup)
        except Exception:  # noqa: BLE001
            backup = None

        message = f"Не удалось прочитать файл данных:\n{path}\n\n{exc}"
        if backup is not None:
            message += f"\n\nСоздана резервная копия:\n{backup}"
        raise StorageError(message) from exc


def save(store: Store, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(store.to_dict(), ensure_ascii=False, indent=2) + "\n"

    temp_path = path.with_name(path.name + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)
