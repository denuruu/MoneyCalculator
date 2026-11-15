"""Модальные диалоги создания и редактирования записей."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, Optional, Sequence

from .formatting import parse_amount, parse_date, today_iso
from .models import Category, Expense, Income, Participant, Session
from .theme import (
    ACCENT,
    BG,
    BODY,
    BORDER,
    DANGER,
    DIALOG_TITLE,
    FONT,
    MUTED,
    SMALL,
    SURFACE,
    TEXT,
    TINY,
)

NO_PARTICIPANT = "— без участника"
COMMON_SOURCES = ["Зарплата", "Премия", "Фриланс", "Инвестиции", "Подарок", "Прочее"]


def _amount_input(value: float) -> str:
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


class BaseDialog(tk.Toplevel):
    """Базовое модальное окно с формой, ошибкой и кнопками."""

    def __init__(self, parent: tk.Misc, title: str, width: int = 460):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.configure(bg=SURFACE)
        self.resizable(False, False)
        self.transient(parent)
        self.result: Optional[dict] = None
        self._width = width
        self._first_focus: Optional[tk.Widget] = None

        self._build_base(title)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda _event: self._cancel())
        self.bind("<Return>", self._on_return)

    def _build_base(self, title: str) -> None:
        self.container = tk.Frame(self, bg=SURFACE)
        self.container.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(
            self.container,
            text=title,
            bg=SURFACE,
            fg=TEXT,
            font=DIALOG_TITLE,
            anchor="w",
        ).pack(fill="x")

        self.form = tk.Frame(self.container, bg=SURFACE)
        self.form.pack(fill="x", pady=(16, 0))

        self.error_label = tk.Label(
            self.container,
            text=" ",
            bg=SURFACE,
            fg=DANGER,
            font=TINY,
            wraplength=self._width - 48,
            justify="left",
            anchor="w",
        )
        self.error_label.pack(fill="x", pady=(4, 0))

        footer = tk.Frame(self.container, bg=SURFACE)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Button(footer, text="Отмена", style="SurfaceGhost.TButton", command=self._cancel).pack(
            side="right"
        )
        self.save_btn = ttk.Button(
            footer, text="Сохранить", style="Accent.TButton", command=self._save
        )
        self.save_btn.pack(side="right", padx=(0, 8))

    # --- конструкторы полей ---------------------------------------------

    def add_field(self, label: str, factory: Callable[[tk.Misc], tk.Widget]) -> tk.Widget:
        row = tk.Frame(self.form, bg=SURFACE)
        row.pack(fill="x", pady=(0, 12))
        tk.Label(row, text=label, bg=SURFACE, fg=MUTED, font=TINY, anchor="w").pack(
            fill="x", pady=(0, 4)
        )
        widget = factory(row)
        widget.pack(fill="x")
        return widget

    def add_entry(self, label: str, value: str = "") -> tuple[tk.StringVar, ttk.Entry]:
        var = tk.StringVar(value=value)
        entry = self.add_field(label, lambda parent: ttk.Entry(parent, textvariable=var))
        if self._first_focus is None:
            self._first_focus = entry
        return var, entry

    def add_combobox(
        self,
        label: str,
        values: Sequence[str],
        value: str = "",
        *,
        readonly: bool = False,
    ) -> tuple[tk.StringVar, ttk.Combobox]:
        var = tk.StringVar(value=value)
        combo = self.add_field(
            label,
            lambda parent: ttk.Combobox(
                parent,
                textvariable=var,
                values=list(values),
                state="readonly" if readonly else "normal",
            ),
        )
        if self._first_focus is None:
            self._first_focus = combo
        return var, combo

    def add_text(self, label: str, value: str = "", height: int = 3) -> tk.Text:
        def factory(parent: tk.Misc) -> tk.Text:
            widget = tk.Text(
                parent,
                height=height,
                wrap="word",
                bg=SURFACE,
                fg=TEXT,
                insertbackground=TEXT,
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=BORDER,
                highlightcolor=ACCENT,
                font=BODY,
                padx=8,
                pady=6,
            )
            widget.insert("1.0", value)
            return widget

        return self.add_field(label, factory)

    def add_grid_row(self) -> tk.Frame:
        row = tk.Frame(self.form, bg=SURFACE)
        row.pack(fill="x", pady=(0, 12))
        return row

    def field_label(self, parent: tk.Misc, text: str) -> tk.Label:
        return tk.Label(parent, text=text, bg=SURFACE, fg=MUTED, font=TINY, anchor="w")

    def add_amount_and_date(
        self, amount_value: str = "", date_value: str = ""
    ) -> tuple[tk.StringVar, ttk.Entry, tk.StringVar, ttk.Entry]:
        row = self.add_grid_row()
        row.columnconfigure(0, weight=3)
        row.columnconfigure(1, weight=2)

        self.field_label(row, "Сумма").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.field_label(row, "Дата · ГГГГ-ММ-ДД").grid(row=0, column=1, sticky="w")

        amount_var = tk.StringVar(value=amount_value)
        amount_entry = ttk.Entry(row, textvariable=amount_var)
        amount_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        date_var = tk.StringVar(value=date_value)
        date_entry = ttk.Entry(row, textvariable=date_var)
        date_entry.grid(row=1, column=1, sticky="ew")
        return amount_var, amount_entry, date_var, date_entry

    # --- служебное -------------------------------------------------------

    def fail(self, message: str, widget: Optional[tk.Widget] = None) -> None:
        self.error_label.configure(text=message)
        if widget is not None:
            widget.focus_set()

    def clear_error(self) -> None:
        self.error_label.configure(text=" ")

    def _cancel(self) -> None:
        self.result = None
        self.destroy()

    def _on_return(self, event: tk.Event) -> Optional[str]:
        if isinstance(event.widget, (tk.Text, ttk.Combobox)):
            return None
        self._save()
        return "break"

    def _save(self) -> None:  # pragma: no cover - переопределяется наследниками
        raise NotImplementedError

    def show(self) -> Optional[dict]:
        self.update_idletasks()
        parent = self.master
        width = self._width
        height = max(self.winfo_reqheight(), 200)
        try:
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(), parent.winfo_height()
        except tk.TclError:
            px, py, pw, ph = 0, 0, 900, 700

        x = px + max((pw - width) // 2, 0)
        y = py + max((ph - height) // 2, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()
        self.grab_set()
        if self._first_focus is not None:
            self._first_focus.focus_set()
        else:
            self.save_btn.focus_set()
        self.wait_window(self)
        return self.result


class SessionDialog(BaseDialog):
    def __init__(self, parent: tk.Misc, session: Optional[Session] = None):
        title = "Новая сессия" if session is None else "Изменить сессию"
        super().__init__(parent, title, width=480)

        self.name_var, self.name_entry = self.add_entry(
            "Название", session.name if session else ""
        )

        row = self.add_grid_row()
        row.columnconfigure(0, weight=0)
        row.columnconfigure(1, weight=1)
        row.columnconfigure(2, weight=1)

        self.field_label(row, "Валюта").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.field_label(row, "Начало · ГГГГ-ММ-ДД").grid(
            row=0, column=1, sticky="w", padx=(0, 10)
        )
        self.field_label(row, "Окончание · ГГГГ-ММ-ДД").grid(row=0, column=2, sticky="w")

        self.currency_var = tk.StringVar(value=session.currency if session else "₽")
        ttk.Entry(row, textvariable=self.currency_var, width=5).grid(
            row=1, column=0, sticky="ew", padx=(0, 10)
        )

        self.start_var = tk.StringVar(value=session.start_date if session else "")
        self.start_entry = ttk.Entry(row, textvariable=self.start_var)
        self.start_entry.grid(row=1, column=1, sticky="ew", padx=(0, 10))

        self.end_var = tk.StringVar(value=session.end_date if session else "")
        self.end_entry = ttk.Entry(row, textvariable=self.end_var)
        self.end_entry.grid(row=1, column=2, sticky="ew")

        self.note_text = self.add_text("Заметка", session.note if session else "", height=3)

    def _save(self) -> None:
        self.clear_error()
        name = self.name_var.get().strip()
        if not name:
            return self.fail("Укажите название сессии.", self.name_entry)

        try:
            start = parse_date(self.start_var.get())
        except ValueError as exc:
            return self.fail(str(exc), self.start_entry)

        try:
            end = parse_date(self.end_var.get())
        except ValueError as exc:
            return self.fail(str(exc), self.end_entry)

        if start and end and end < start:
            return self.fail("Дата окончания не может быть раньше даты начала.", self.end_entry)

        self.result = {
            "name": name,
            "currency": self.currency_var.get().strip() or "₽",
            "start_date": start,
            "end_date": end,
            "note": self.note_text.get("1.0", "end").strip(),
        }
        self.destroy()


class ParticipantDialog(BaseDialog):
    def __init__(
        self,
        parent: tk.Misc,
        participant: Optional[Participant] = None,
        other_names: Iterable[str] = (),
    ):
        title = "Новый участник" if participant is None else "Изменить участника"
        super().__init__(parent, title, width=420)
        self._other_names = {name.casefold() for name in other_names}

        self.name_var, self.name_entry = self.add_entry(
            "Имя", participant.name if participant else ""
        )
        self.note_text = self.add_text("Заметка", participant.note if participant else "", height=2)

    def _save(self) -> None:
        self.clear_error()
        name = self.name_var.get().strip()
        if not name:
            return self.fail("Укажите имя участника.", self.name_entry)
        if name.casefold() in self._other_names:
            return self.fail("Участник с таким именем уже есть в сессии.", self.name_entry)

        self.result = {
            "name": name,
            "note": self.note_text.get("1.0", "end").strip(),
        }
        self.destroy()


class CategoryDialog(BaseDialog):
    def __init__(
        self,
        parent: tk.Misc,
        category: Optional[Category] = None,
        other_names: Iterable[str] = (),
    ):
        title = "Новый вид расходов" if category is None else "Изменить вид расходов"
        super().__init__(parent, title, width=440)
        self._other_names = {name.casefold() for name in other_names}

        self.name_var, self.name_entry = self.add_entry(
            "Название вида", category.name if category else ""
        )
        self.types_text = self.add_text(
            "Типы · каждый с новой строки",
            "\n".join(category.types) if category else "",
            height=5,
        )

    def _save(self) -> None:
        self.clear_error()
        name = self.name_var.get().strip()
        if not name:
            return self.fail("Укажите название вида расходов.", self.name_entry)
        if name.casefold() in self._other_names:
            return self.fail("Вид расходов с таким названием уже есть.", self.name_entry)

        types: list[str] = []
        seen: set[str] = set()
        for line in self.types_text.get("1.0", "end").splitlines():
            value = line.strip()
            if value and value.casefold() not in seen:
                seen.add(value.casefold())
                types.append(value)

        self.result = {"name": name, "types": types}
        self.destroy()


class IncomeDialog(BaseDialog):
    def __init__(self, parent: tk.Misc, session: Session, income: Optional[Income] = None):
        title = "Новый доход" if income is None else "Изменить доход"
        super().__init__(parent, title, width=460)
        self._participants = list(session.participants)
        self._participant_by_name = {p.name: p.id for p in self._participants}

        names = [p.name for p in self._participants]
        if income is not None:
            initial_participant = (
                session.participant_name(income.participant_id)
                if income.participant_id
                else NO_PARTICIPANT
            )
        else:
            initial_participant = names[0] if names else NO_PARTICIPANT

        self.participant_var, _combo = self.add_combobox(
            "Участник",
            [NO_PARTICIPANT] + names,
            initial_participant,
            readonly=True,
        )
        self.source_var, _source = self.add_combobox(
            "Источник",
            COMMON_SOURCES,
            income.source if income else "",
            readonly=False,
        )

        amount_value = _amount_input(income.amount) if income else ""
        date_value = income.date if income else today_iso()
        self.amount_var, self.amount_entry, self.date_var, self.date_entry = self.add_amount_and_date(
            amount_value, date_value
        )

        self.note_text = self.add_text("Комментарий", income.note if income else "", height=2)

    def _save(self) -> None:
        self.clear_error()
        participant_id = self._participant_by_name.get(self.participant_var.get())

        try:
            amount = parse_amount(self.amount_var.get())
        except ValueError as exc:
            return self.fail(str(exc), self.amount_entry)

        try:
            date_value = parse_date(self.date_var.get())
        except ValueError as exc:
            return self.fail(str(exc), self.date_entry)

        self.result = {
            "participant_id": participant_id,
            "amount": amount,
            "source": self.source_var.get().strip(),
            "date": date_value,
            "note": self.note_text.get("1.0", "end").strip(),
        }
        self.destroy()


class ExpenseDialog(BaseDialog):
    def __init__(self, parent: tk.Misc, session: Session, expense: Optional[Expense] = None):
        title = "Новый расход" if expense is None else "Изменить расход"
        super().__init__(parent, title, width=480)
        self._participants = list(session.participants)
        self._participant_by_name = {p.name: p.id for p in self._participants}
        self._categories = list(session.categories)
        self._category_by_name = {c.name: c for c in self._categories}

        names = [p.name for p in self._participants]
        if expense is not None:
            initial_participant = (
                session.participant_name(expense.participant_id)
                if expense.participant_id
                else NO_PARTICIPANT
            )
        else:
            initial_participant = names[0] if names else NO_PARTICIPANT

        self.participant_var, _combo = self.add_combobox(
            "Участник",
            [NO_PARTICIPANT] + names,
            initial_participant,
            readonly=True,
        )

        category_names = [c.name for c in self._categories]
        initial_category = ""
        if expense is not None and expense.category_id:
            category = session.category(expense.category_id)
            initial_category = category.name if category else ""
        if not initial_category and category_names:
            initial_category = category_names[0]

        self.category_var, self.category_combo = self.add_combobox(
            "Вид расхода",
            category_names,
            initial_category,
            readonly=True,
        )
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_change)

        category = self._category_by_name.get(initial_category)
        type_values = list(category.types) if category else []
        initial_type = expense.type if expense else ""
        self.type_var, self.type_combo = self.add_combobox(
            "Тип расхода",
            type_values,
            initial_type,
            readonly=False,
        )

        amount_value = _amount_input(expense.amount) if expense else ""
        date_value = expense.date if expense else today_iso()
        self.amount_var, self.amount_entry, self.date_var, self.date_entry = self.add_amount_and_date(
            amount_value, date_value
        )

        self.note_text = self.add_text("Комментарий", expense.note if expense else "", height=2)

    def _on_category_change(self, _event: Optional[tk.Event] = None) -> None:
        category = self._category_by_name.get(self.category_var.get())
        values = list(category.types) if category else []
        self.type_combo.configure(values=values)
        current = self.type_var.get().strip()
        if current and current.casefold() not in {value.casefold() for value in values}:
            self.type_var.set("")

    def _save(self) -> None:
        self.clear_error()
        participant_id = self._participant_by_name.get(self.participant_var.get())

        category = self._category_by_name.get(self.category_var.get())
        if category is None:
            return self.fail(
                "Выберите вид расхода. Если список пуст, добавьте вид во вкладке «Категории».",
                self.category_combo,
            )

        type_value = self.type_var.get().strip()
        if not type_value:
            return self.fail("Укажите тип расхода.", self.type_combo)

        try:
            amount = parse_amount(self.amount_var.get())
        except ValueError as exc:
            return self.fail(str(exc), self.amount_entry)

        try:
            date_value = parse_date(self.date_var.get())
        except ValueError as exc:
            return self.fail(str(exc), self.date_entry)

        if type_value.casefold() not in {value.casefold() for value in category.types}:
            category.types.append(type_value)

        self.result = {
            "participant_id": participant_id,
            "category_id": category.id,
            "type": type_value,
            "amount": amount,
            "date": date_value,
            "note": self.note_text.get("1.0", "end").strip(),
        }
        self.destroy()
