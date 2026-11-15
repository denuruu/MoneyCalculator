"""Модель данных приложения и сериализация в обычные словари."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

DEFAULT_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Жильё", ["Аренда", "Коммунальные услуги", "Ремонт"]),
    ("Продукты", ["Супермаркет", "Рынок", "Доставка"]),
    ("Транспорт", ["Топливо", "Общественный транспорт", "Такси", "Обслуживание"]),
    ("Здоровье", ["Аптека", "Врачи", "Страхование"]),
    ("Быт", ["Хозтовары", "Техника", "Подписки"]),
    ("Развлечения", ["Кафе и рестораны", "Кино", "Поездки"]),
    ("Прочее", []),
]


def new_id() -> str:
    return uuid4().hex


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return default
    return str(value)


def _amount(value: Any) -> float:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result


@dataclass
class Participant:
    id: str
    name: str
    note: str = ""

    @classmethod
    def create(cls, name: str, note: str = "") -> "Participant":
        return cls(new_id(), name.strip(), note.strip())

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Participant":
        return cls(
            str(data.get("id") or new_id()),
            _text(data.get("name"), "Без имени") or "Без имени",
            _text(data.get("note")),
        )


@dataclass
class Category:
    id: str
    name: str
    types: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, types: Optional[list[str]] = None) -> "Category":
        return cls(new_id(), name.strip(), _unique([t.strip() for t in (types or [])]))

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "types": list(self.types)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Category":
        raw_types = data.get("types")
        types = [str(t).strip() for t in raw_types] if isinstance(raw_types, list) else []
        return cls(
            str(data.get("id") or new_id()),
            _text(data.get("name"), "Без названия") or "Без названия",
            _unique([t for t in types if t]),
        )


@dataclass
class Income:
    id: str
    participant_id: Optional[str]
    amount: float
    source: str = ""
    date: str = ""
    note: str = ""

    @classmethod
    def create(
        cls,
        participant_id: Optional[str],
        amount: float,
        source: str = "",
        date: str = "",
        note: str = "",
    ) -> "Income":
        return cls(new_id(), participant_id, round(float(amount), 2), source.strip(), date, note.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "participant_id": self.participant_id,
            "amount": self.amount,
            "source": self.source,
            "date": self.date,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Income":
        participant_id = data.get("participant_id")
        return cls(
            str(data.get("id") or new_id()),
            str(participant_id) if participant_id else None,
            _amount(data.get("amount")),
            _text(data.get("source")),
            _text(data.get("date")),
            _text(data.get("note")),
        )


@dataclass
class Expense:
    id: str
    participant_id: Optional[str]
    category_id: Optional[str]
    type: str
    amount: float
    date: str = ""
    note: str = ""

    @classmethod
    def create(
        cls,
        participant_id: Optional[str],
        category_id: Optional[str],
        type: str,
        amount: float,
        date: str = "",
        note: str = "",
    ) -> "Expense":
        return cls(
            new_id(),
            participant_id,
            category_id,
            type.strip(),
            round(float(amount), 2),
            date,
            note.strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "participant_id": self.participant_id,
            "category_id": self.category_id,
            "type": self.type,
            "amount": self.amount,
            "date": self.date,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Expense":
        participant_id = data.get("participant_id")
        category_id = data.get("category_id")
        return cls(
            str(data.get("id") or new_id()),
            str(participant_id) if participant_id else None,
            str(category_id) if category_id else None,
            _text(data.get("type")),
            _amount(data.get("amount")),
            _text(data.get("date")),
            _text(data.get("note")),
        )


@dataclass
class Session:
    id: str
    name: str
    currency: str = "₽"
    start_date: str = ""
    end_date: str = ""
    note: str = ""
    participants: list[Participant] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    incomes: list[Income] = field(default_factory=list)
    expenses: list[Expense] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        name: str,
        currency: str = "₽",
        start_date: str = "",
        end_date: str = "",
        note: str = "",
    ) -> "Session":
        session = cls(
            new_id(),
            name.strip(),
            currency.strip() or "₽",
            start_date,
            end_date,
            note.strip(),
        )
        session.categories = [Category.create(cat_name, types) for cat_name, types in DEFAULT_CATEGORIES]
        return session

    # --- справочники -----------------------------------------------------

    def participant(self, participant_id: Optional[str]) -> Optional[Participant]:
        if not participant_id:
            return None
        for participant in self.participants:
            if participant.id == participant_id:
                return participant
        return None

    def category(self, category_id: Optional[str]) -> Optional[Category]:
        if not category_id:
            return None
        for category in self.categories:
            if category.id == category_id:
                return category
        return None

    def participant_name(self, participant_id: Optional[str]) -> str:
        participant = self.participant(participant_id)
        return participant.name if participant else "—"

    def category_name(self, category_id: Optional[str]) -> str:
        category = self.category(category_id)
        return category.name if category else "—"

    # --- расчёты ---------------------------------------------------------

    @property
    def total_income(self) -> float:
        return round(sum(record.amount for record in self.incomes), 2)

    @property
    def total_expense(self) -> float:
        return round(sum(record.amount for record in self.expenses), 2)

    @property
    def balance(self) -> float:
        return round(self.total_income - self.total_expense, 2)

    def participant_totals(self, participant_id: str) -> tuple[float, float]:
        income = sum(r.amount for r in self.incomes if r.participant_id == participant_id)
        expense = sum(r.amount for r in self.expenses if r.participant_id == participant_id)
        return round(income, 2), round(expense, 2)

    def category_stats(self, category_id: str) -> tuple[int, float]:
        records = [r for r in self.expenses if r.category_id == category_id]
        return len(records), round(sum(r.amount for r in records), 2)

    # --- сериализация ----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "currency": self.currency,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "note": self.note,
            "participants": [p.to_dict() for p in self.participants],
            "categories": [c.to_dict() for c in self.categories],
            "incomes": [i.to_dict() for i in self.incomes],
            "expenses": [e.to_dict() for e in self.expenses],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        def items(key: str) -> list[dict[str, Any]]:
            value = data.get(key)
            return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

        return cls(
            str(data.get("id") or new_id()),
            _text(data.get("name"), "Без названия") or "Без названия",
            _text(data.get("currency"), "₽") or "₽",
            _text(data.get("start_date")),
            _text(data.get("end_date")),
            _text(data.get("note")),
            [Participant.from_dict(item) for item in items("participants")],
            [Category.from_dict(item) for item in items("categories")],
            [Income.from_dict(item) for item in items("incomes")],
            [Expense.from_dict(item) for item in items("expenses")],
        )


@dataclass
class Store:
    sessions: list[Session] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"version": 1, "sessions": [session.to_dict() for session in self.sessions]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Store":
        raw_sessions = data.get("sessions") if isinstance(data, dict) else None
        sessions = []
        if isinstance(raw_sessions, list):
            sessions = [Session.from_dict(item) for item in raw_sessions if isinstance(item, dict)]
        return cls(sessions)
