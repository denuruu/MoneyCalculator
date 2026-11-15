"""Форматирование и разбор денежных сумм, дат и числительных."""

from __future__ import annotations

import math
from datetime import date, datetime

_DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%Y.%m.%d")


def format_money(value: float | int, currency: str = "₽") -> str:
    """1234.5 -> '1 234,50 ₽'; 30000 -> '30 000 ₽'."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    if not math.isfinite(number):
        number = 0.0
    sign = "−" if number < 0 else ""
    text = f"{abs(number):,.2f}".replace(",", " ").replace(".", ",")
    if text.endswith(",00"):
        text = text[:-3]
    return f"{sign}{text} {currency}".strip()


def parse_amount(text: str) -> float:
    """Разбирает сумму, принимая пробелы, запятую и знак валюты."""
    raw = str(text or "").strip()
    for junk in ("\u00a0", "\u202f", " ", "₽", "руб.", "руб"):
        raw = raw.replace(junk, "")
    raw = raw.replace(",", ".")
    if not raw:
        raise ValueError("Введите сумму.")
    try:
        number = float(raw)
    except ValueError as exc:
        raise ValueError("Сумма должна быть числом, например 12 500,50.") from exc
    if not math.isfinite(number):
        raise ValueError("Сумма должна быть числом.")
    if number <= 0:
        raise ValueError("Сумма должна быть больше нуля.")
    return round(number, 2)


def format_date(iso_date: str) -> str:
    if not iso_date:
        return "—"
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return iso_date


def parse_date(text: str) -> str:
    """Возвращает дату в ISO-формате. Пустая строка допустима."""
    raw = str(text or "").strip()
    if not raw:
        return ""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД, например 2026-11-09.")


def today_iso() -> str:
    return date.today().strftime("%Y-%m-%d")


def plural(number: int, one: str, few: str, many: str) -> str:
    number = abs(int(number))
    if number % 10 == 1 and number % 100 != 11:
        return one
    if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        return few
    return many


def records_label(number: int) -> str:
    return f"{number} {plural(number, 'запись', 'записи', 'записей')}"


def participants_label(number: int) -> str:
    return f"{number} {plural(number, 'участник', 'участника', 'участников')}"
