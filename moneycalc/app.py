"""Главное окно приложения Money Calculator."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional

from . import storage
from .dialogs import CategoryDialog, ExpenseDialog, IncomeDialog, ParticipantDialog, SessionDialog
from .formatting import (
    format_date,
    format_money,
    participants_label,
    plural,
    records_label,
)
from .models import Category, Expense, Income, Participant, Session, Store
from .theme import (
    ACCENT,
    BG,
    BODY_BOLD,
    BORDER,
    FAINT,
    FONT,
    MUTED,
    NEGATIVE,
    POSITIVE,
    SIDEBAR,
    SMALL,
    SURFACE,
    TEXT,
    TINY,
    TITLE,
    apply_theme,
)
from .widgets import ScrollableFrame, SummaryCard, TableTab

INCOME_COLUMNS = [
    {"key": "date", "title": "Дата", "width": 92},
    {"key": "participant", "title": "Участник", "width": 150},
    {"key": "source", "title": "Источник", "width": 230, "stretch": True},
    {"key": "amount", "title": "Сумма", "width": 130, "anchor": "e", "heading_anchor": "e"},
    {"key": "note", "title": "Комментарий", "width": 280, "stretch": True},
]

EXPENSE_COLUMNS = [
    {"key": "date", "title": "Дата", "width": 92},
    {"key": "participant", "title": "Участник", "width": 140},
    {"key": "category", "title": "Вид", "width": 150},
    {"key": "type", "title": "Тип", "width": 160},
    {"key": "amount", "title": "Сумма", "width": 120, "anchor": "e", "heading_anchor": "e"},
    {"key": "note", "title": "Комментарий", "width": 240, "stretch": True},
]

PARTICIPANT_COLUMNS = [
    {"key": "name", "title": "Участник", "width": 170},
    {"key": "income", "title": "Доходы", "width": 130, "anchor": "e", "heading_anchor": "e"},
    {"key": "expense", "title": "Расходы", "width": 130, "anchor": "e", "heading_anchor": "e"},
    {"key": "balance", "title": "Баланс", "width": 130, "anchor": "e", "heading_anchor": "e"},
    {"key": "note", "title": "Заметка", "width": 260, "stretch": True},
]

CATEGORY_COLUMNS = [
    {"key": "name", "title": "Вид расходов", "width": 190},
    {"key": "types", "title": "Типы", "width": 380, "stretch": True},
    {"key": "count", "title": "Записей", "width": 90, "anchor": "e", "heading_anchor": "e"},
    {"key": "total", "title": "Сумма", "width": 140, "anchor": "e", "heading_anchor": "e"},
]


def _period_text(session: Session) -> str:
    if session.start_date and session.end_date:
        return f"{format_date(session.start_date)} — {format_date(session.end_date)}"
    if session.start_date:
        return f"с {format_date(session.start_date)}"
    if session.end_date:
        return f"до {format_date(session.end_date)}"
    return "Период не задан"


class MoneyApp(tk.Tk):
    def __init__(self, data_path: Optional[Path] = None):
        super().__init__()
        self.data_path = Path(data_path) if data_path else storage.default_data_path()
        self._load_error: Optional[str] = None

        try:
            self.store = storage.load(self.data_path)
        except storage.StorageError as exc:
            self.store = Store()
            self._load_error = str(exc)

        self.current_session_id: Optional[str] = (
            self.store.sessions[0].id if self.store.sessions else None
        )
        self._tab_index = 0
        self._saved_text = tk.StringVar(value="Данные загружены")

        self._build_window()
        self.refresh()

        if self._load_error:
            self.after(200, self._show_load_error)

    # --- построение окна -------------------------------------------------

    def _build_window(self) -> None:
        self.title("Money Calculator")
        self.configure(bg=BG)
        self.minsize(1000, 660)
        apply_theme(self)

        self._build_status_bar()

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        sidebar = tk.Frame(main, bg=SIDEBAR, width=272)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self._build_sidebar(sidebar)

        self.content = tk.Frame(main, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self.update_idletasks()
        width, height = 1180, 780
        x = max((self.winfo_screenwidth() - width) // 2, 0)
        y = max((self.winfo_screenheight() - height) // 2 - 20, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_status_bar(self) -> None:
        bar = tk.Frame(self, bg=BG, height=30)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        separator = tk.Frame(self, bg=BORDER, height=1)
        separator.pack(side="bottom", fill="x")

        tk.Label(
            bar,
            text=f"Данные: {self.data_path}",
            bg=BG,
            fg=MUTED,
            font=TINY,
            anchor="w",
        ).pack(side="left", padx=(20, 10))

        link = tk.Label(
            bar,
            text="Открыть папку",
            bg=BG,
            fg=MUTED,
            font=(FONT, 8, "underline"),
            cursor="hand2",
        )
        link.pack(side="right", padx=(0, 20))
        link.bind("<Button-1>", lambda _event: self._open_data_folder())

        tk.Label(
            bar,
            textvariable=self._saved_text,
            bg=BG,
            fg=FAINT,
            font=TINY,
        ).pack(side="right", padx=(0, 16))

    def _build_sidebar(self, sidebar: tk.Frame) -> None:
        top = tk.Frame(sidebar, bg=SIDEBAR)
        top.pack(fill="x", padx=20, pady=(22, 18))
        tk.Label(top, text="Money Calculator", bg=SIDEBAR, fg=TEXT, font=(FONT, 14, "bold")).pack(
            anchor="w"
        )
        tk.Label(top, text="доходы и расходы", bg=SIDEBAR, fg=MUTED, font=TINY).pack(
            anchor="w", pady=(2, 0)
        )

        footer = tk.Frame(sidebar, bg=SIDEBAR)
        footer.pack(side="bottom", fill="x", padx=20, pady=(10, 14))
        tk.Label(
            footer,
            text="Локальное хранение · JSON",
            bg=SIDEBAR,
            fg=FAINT,
            font=TINY,
            anchor="w",
        ).pack(fill="x")

        header = tk.Frame(sidebar, bg=SIDEBAR)
        header.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(header, text="СЕССИИ", bg=SIDEBAR, fg=MUTED, font=(FONT, 8, "bold")).pack(
            side="left"
        )
        ttk.Button(
            header,
            text="+ Новая",
            style="SidebarGhost.TButton",
            command=self._add_session,
        ).pack(side="right")

        self.session_scroll = ScrollableFrame(
            sidebar, SIDEBAR, scrollbar_style="Sidebar.Vertical.TScrollbar"
        )
        self.session_scroll.pack(fill="both", expand=True, padx=(8, 4))

    # --- обновление ------------------------------------------------------

    @property
    def current_session(self) -> Optional[Session]:
        if not self.current_session_id:
            return None
        for session in self.store.sessions:
            if session.id == self.current_session_id:
                return session
        return None

    def refresh(self) -> None:
        if self.current_session_id is not None and not any(
            session.id == self.current_session_id for session in self.store.sessions
        ):
            self.current_session_id = None
        if self.current_session_id is None and self.store.sessions:
            self.current_session_id = self.store.sessions[0].id

        self._rebuild_session_list()
        self._rebuild_content()
        self._update_title()

    def _update_title(self) -> None:
        session = self.current_session
        self.title(f"Money Calculator — {session.name}" if session else "Money Calculator")

    def _rebuild_session_list(self) -> None:
        inner = self.session_scroll.inner
        for child in inner.winfo_children():
            child.destroy()

        if not self.store.sessions:
            tk.Label(inner, text="Нет сессий", bg=SIDEBAR, fg=FAINT, font=SMALL).pack(pady=24)
        else:
            for session in self.store.sessions:
                self._make_session_card(inner, session)

        self.session_scroll.bind_wheel_recursive()
        self.after_idle(self._update_session_scrollregion)

    def _update_session_scrollregion(self) -> None:
        try:
            self.session_scroll.canvas.configure(
                scrollregion=self.session_scroll.canvas.bbox("all")
            )
        except tk.TclError:
            pass

    def _make_session_card(self, parent: tk.Misc, session: Session) -> None:
        selected = session.id == self.current_session_id
        card = tk.Frame(
            parent,
            bg=SURFACE,
            highlightthickness=1,
            highlightbackground=ACCENT if selected else BORDER,
            bd=0,
            cursor="hand2",
        )
        card.pack(fill="x", padx=8, pady=4)

        body = tk.Frame(card, bg=SURFACE, cursor="hand2")
        body.pack(fill="x", padx=14, pady=10)

        name = tk.Label(
            body,
            text=session.name,
            bg=SURFACE,
            fg=TEXT,
            font=BODY_BOLD,
            anchor="w",
            justify="left",
            wraplength=200,
            cursor="hand2",
        )
        name.pack(fill="x")

        balance_color = NEGATIVE if session.balance < 0 else MUTED
        subtitle = tk.Label(
            body,
            text=f"Баланс {format_money(session.balance, session.currency)}",
            bg=SURFACE,
            fg=balance_color,
            font=TINY,
            anchor="w",
            cursor="hand2",
        )
        subtitle.pack(fill="x", pady=(3, 0))

        for widget in (card, body, name, subtitle):
            widget.bind("<Button-1>", lambda _event, sid=session.id: self._select_session(sid))

    def _select_session(self, session_id: str) -> None:
        if session_id == self.current_session_id:
            return
        self.current_session_id = session_id
        self._tab_index = 0
        self.refresh()

    # --- содержимое ------------------------------------------------------

    def _rebuild_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

        session = self.current_session
        if session is None:
            self._build_empty_content()
            return

        wrapper = tk.Frame(self.content, bg=BG)
        wrapper.pack(fill="both", expand=True, padx=28, pady=(24, 18))

        self._build_header(wrapper, session)
        self._build_cards(wrapper, session)

        notebook = ttk.Notebook(wrapper)
        notebook.pack(fill="both", expand=True, pady=(16, 0))
        self._build_income_tab(notebook, session)
        self._build_expense_tab(notebook, session)
        self._build_participant_tab(notebook, session)
        self._build_category_tab(notebook, session)

        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        index = min(self._tab_index, len(notebook.tabs()) - 1)
        if index >= 0:
            notebook.select(index)

    def _on_tab_changed(self, event: tk.Event) -> None:
        notebook = event.widget
        try:
            self._tab_index = notebook.index("current")
        except tk.TclError:
            pass

    def _build_empty_content(self) -> None:
        holder = tk.Frame(self.content, bg=BG)
        holder.place(relx=0.5, rely=0.46, anchor="center")

        tk.Label(
            holder,
            text="Пока нет ни одной сессии",
            bg=BG,
            fg=TEXT,
            font=(FONT, 17, "bold"),
        ).pack()
        tk.Label(
            holder,
            text="Сессия — это отдельный расчёт: месяц, поездка или проект.\n"
            "Создайте первую, чтобы начать вести доходы и расходы.",
            bg=BG,
            fg=MUTED,
            font=SMALL,
            justify="center",
        ).pack(pady=(8, 20))
        ttk.Button(
            holder,
            text="Создать сессию",
            style="Accent.TButton",
            command=self._add_session,
        ).pack()

    def _build_header(self, parent: tk.Misc, session: Session) -> None:
        header = tk.Frame(parent, bg=BG)
        header.pack(fill="x")

        left = tk.Frame(header, bg=BG)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(
            left,
            text=session.name,
            bg=BG,
            fg=TEXT,
            font=TITLE,
            anchor="w",
            justify="left",
            wraplength=720,
        ).pack(fill="x")

        meta = "   ·   ".join(
            [
                _period_text(session),
                f"Валюта: {session.currency}",
                participants_label(len(session.participants)),
            ]
        )
        tk.Label(left, text=meta, bg=BG, fg=MUTED, font=SMALL, anchor="w").pack(
            fill="x", pady=(5, 0)
        )

        if session.note:
            tk.Label(
                left,
                text=session.note,
                bg=BG,
                fg=MUTED,
                font=SMALL,
                anchor="w",
                justify="left",
                wraplength=720,
            ).pack(fill="x", pady=(6, 0))

        actions = tk.Frame(header, bg=BG)
        actions.pack(side="right", anchor="n", padx=(16, 0))
        ttk.Button(
            actions,
            text="Изменить",
            style="Ghost.TButton",
            command=self._edit_session,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            actions,
            text="Удалить",
            style="DangerGhost.TButton",
            command=self._delete_session,
        ).pack(side="left")

    def _build_cards(self, parent: tk.Misc, session: Session) -> None:
        cards = tk.Frame(parent, bg=BG)
        cards.pack(fill="x", pady=(18, 0))
        for index in range(3):
            cards.columnconfigure(index, weight=1, uniform="summary")

        balance = session.balance
        if balance > 0:
            balance_color = POSITIVE
        elif balance < 0:
            balance_color = NEGATIVE
        else:
            balance_color = TEXT

        definitions = [
            (
                "Доходы",
                format_money(session.total_income, session.currency),
                records_label(len(session.incomes)),
                TEXT,
            ),
            (
                "Расходы",
                format_money(session.total_expense, session.currency),
                records_label(len(session.expenses)),
                TEXT,
            ),
            (
                "Баланс",
                format_money(balance, session.currency),
                "доходы минус расходы",
                balance_color,
            ),
        ]

        for index, (title, value, subtitle, color) in enumerate(definitions):
            card = SummaryCard(cards, title, value, subtitle, color)
            card.grid(
                row=0,
                column=index,
                sticky="nsew",
                padx=(0, 12) if index < 2 else 0,
            )

    # --- вкладки ---------------------------------------------------------

    def _add_tab(self, notebook: ttk.Notebook, title: str) -> tk.Frame:
        tab = tk.Frame(notebook, bg=SURFACE)
        notebook.add(tab, text=title)
        return tab

    def _build_income_tab(self, notebook: ttk.Notebook, session: Session) -> None:
        tab = self._add_tab(notebook, "Доходы")
        table = TableTab(
            tab,
            INCOME_COLUMNS,
            on_add=self._add_income,
            on_edit=self._edit_income,
            on_delete=self._delete_income,
            empty_text="Доходов пока нет. Добавьте первую запись.",
        )
        table.pack(fill="both", expand=True, padx=16, pady=16)

        rows = []
        for record in sorted(session.incomes, key=lambda item: item.date or "", reverse=True):
            rows.append(
                (
                    record.id,
                    (
                        format_date(record.date),
                        session.participant_name(record.participant_id),
                        record.source or "—",
                        format_money(record.amount, session.currency),
                        record.note or "",
                    ),
                    (),
                )
            )
        table.set_rows(
            rows,
            records_label(len(rows)),
            f"Итого: {format_money(session.total_income, session.currency)}",
        )

    def _build_expense_tab(self, notebook: ttk.Notebook, session: Session) -> None:
        tab = self._add_tab(notebook, "Расходы")
        table = TableTab(
            tab,
            EXPENSE_COLUMNS,
            on_add=self._add_expense,
            on_edit=self._edit_expense,
            on_delete=self._delete_expense,
            empty_text="Расходов пока нет. Добавьте первую запись.",
        )
        table.pack(fill="both", expand=True, padx=16, pady=16)

        rows = []
        for record in sorted(session.expenses, key=lambda item: item.date or "", reverse=True):
            rows.append(
                (
                    record.id,
                    (
                        format_date(record.date),
                        session.participant_name(record.participant_id),
                        session.category_name(record.category_id),
                        record.type or "—",
                        format_money(record.amount, session.currency),
                        record.note or "",
                    ),
                    (),
                )
            )
        table.set_rows(
            rows,
            records_label(len(rows)),
            f"Итого: {format_money(session.total_expense, session.currency)}",
        )

    def _build_participant_tab(self, notebook: ttk.Notebook, session: Session) -> None:
        tab = self._add_tab(notebook, "Участники")
        table = TableTab(
            tab,
            PARTICIPANT_COLUMNS,
            on_add=self._add_participant,
            on_edit=self._edit_participant,
            on_delete=self._delete_participant,
            empty_text="Участников пока нет. Добавьте людей, чтобы считать доходы по каждому.",
            add_text="Добавить участника",
        )
        table.pack(fill="both", expand=True, padx=16, pady=16)

        rows = []
        for participant in session.participants:
            income, expense = session.participant_totals(participant.id)
            balance = round(income - expense, 2)
            tags = ("negative",) if balance < 0 else ()
            rows.append(
                (
                    participant.id,
                    (
                        participant.name,
                        format_money(income, session.currency),
                        format_money(expense, session.currency),
                        format_money(balance, session.currency),
                        participant.note or "",
                    ),
                    tags,
                )
            )
        table.set_rows(
            rows,
            participants_label(len(rows)),
            f"Баланс: {format_money(session.balance, session.currency)}",
        )

    def _build_category_tab(self, notebook: ttk.Notebook, session: Session) -> None:
        tab = self._add_tab(notebook, "Категории")
        table = TableTab(
            tab,
            CATEGORY_COLUMNS,
            on_add=self._add_category,
            on_edit=self._edit_category,
            on_delete=self._delete_category,
            empty_text="Видов расходов пока нет. Добавьте первый вид и его типы.",
            add_text="Добавить вид",
        )
        table.pack(fill="both", expand=True, padx=16, pady=16)

        rows = []
        for category in sorted(session.categories, key=lambda item: item.name.casefold()):
            count, total = session.category_stats(category.id)
            rows.append(
                (
                    category.id,
                    (
                        category.name,
                        ", ".join(category.types) if category.types else "—",
                        str(count),
                        format_money(total, session.currency),
                    ),
                    (),
                )
            )
        table.set_rows(
            rows,
            f"{len(rows)} {plural(len(rows), 'вид', 'вида', 'видов')}",
            f"Всего расходов: {format_money(session.total_expense, session.currency)}",
        )

    # --- сессии ----------------------------------------------------------

    def _add_session(self) -> None:
        data = SessionDialog(self).show()
        if data is None:
            return
        session = Session.create(**data)
        self.store.sessions.append(session)
        self.current_session_id = session.id
        self._tab_index = 0
        self._commit()

    def _edit_session(self) -> None:
        session = self.current_session
        if session is None:
            return
        data = SessionDialog(self, session).show()
        if data is None:
            return
        for key, value in data.items():
            setattr(session, key, value)
        self._commit()

    def _delete_session(self) -> None:
        session = self.current_session
        if session is None:
            return
        if not messagebox.askyesno(
            "Удалить сессию",
            f"Удалить сессию «{session.name}» вместе со всеми участниками, "
            "доходами и расходами?",
            parent=self,
        ):
            return

        index = self.store.sessions.index(session)
        self.store.sessions.remove(session)
        if self.store.sessions:
            self.current_session_id = self.store.sessions[
                min(index, len(self.store.sessions) - 1)
            ].id
        else:
            self.current_session_id = None
        self._tab_index = 0
        self._commit()

    # --- доходы ----------------------------------------------------------

    def _add_income(self) -> None:
        session = self.current_session
        if session is None:
            return
        data = IncomeDialog(self, session).show()
        if data is None:
            return
        session.incomes.append(Income.create(**data))
        self._commit()

    def _edit_income(self, income_id: str) -> None:
        session = self.current_session
        if session is None:
            return
        record = next((item for item in session.incomes if item.id == income_id), None)
        if record is None:
            return
        data = IncomeDialog(self, session, record).show()
        if data is None:
            return
        for key, value in data.items():
            setattr(record, key, value)
        self._commit()

    def _delete_income(self, income_id: str) -> None:
        session = self.current_session
        if session is None:
            return
        record = next((item for item in session.incomes if item.id == income_id), None)
        if record is None:
            return
        if not messagebox.askyesno(
            "Удалить доход",
            f"Удалить доход на {format_money(record.amount, session.currency)}?",
            parent=self,
        ):
            return
        session.incomes.remove(record)
        self._commit()

    # --- расходы ---------------------------------------------------------

    def _add_expense(self) -> None:
        session = self.current_session
        if session is None:
            return
        data = ExpenseDialog(self, session).show()
        if data is None:
            return
        session.expenses.append(Expense.create(**data))
        self._commit()

    def _edit_expense(self, expense_id: str) -> None:
        session = self.current_session
        if session is None:
            return
        record = next((item for item in session.expenses if item.id == expense_id), None)
        if record is None:
            return
        data = ExpenseDialog(self, session, record).show()
        if data is None:
            return
        for key, value in data.items():
            setattr(record, key, value)
        self._commit()

    def _delete_expense(self, expense_id: str) -> None:
        session = self.current_session
        if session is None:
            return
        record = next((item for item in session.expenses if item.id == expense_id), None)
        if record is None:
            return
        if not messagebox.askyesno(
            "Удалить расход",
            f"Удалить расход на {format_money(record.amount, session.currency)}?",
            parent=self,
        ):
            return
        session.expenses.remove(record)
        self._commit()

    # --- участники -------------------------------------------------------

    def _add_participant(self) -> None:
        session = self.current_session
        if session is None:
            return
        data = ParticipantDialog(
            self, other_names=[participant.name for participant in session.participants]
        ).show()
        if data is None:
            return
        session.participants.append(Participant.create(**data))
        self._commit()

    def _edit_participant(self, participant_id: str) -> None:
        session = self.current_session
        if session is None:
            return
        participant = next(
            (item for item in session.participants if item.id == participant_id), None
        )
        if participant is None:
            return
        others = [
            item.name for item in session.participants if item.id != participant.id
        ]
        data = ParticipantDialog(self, participant, others).show()
        if data is None:
            return
        for key, value in data.items():
            setattr(participant, key, value)
        self._commit()

    def _delete_participant(self, participant_id: str) -> None:
        session = self.current_session
        if session is None:
            return
        participant = next(
            (item for item in session.participants if item.id == participant_id), None
        )
        if participant is None:
            return

        related = [
            record
            for record in session.incomes + session.expenses
            if record.participant_id == participant.id
        ]
        message = f"Удалить участника «{participant.name}»?"
        if related:
            message += (
                f"\n\nС участником связано {records_label(len(related))}. "
                "Они останутся, но будут без участника."
            )
        if not messagebox.askyesno("Удалить участника", message, parent=self):
            return

        for record in session.incomes + session.expenses:
            if record.participant_id == participant.id:
                record.participant_id = None
        session.participants.remove(participant)
        self._commit()

    # --- категории -------------------------------------------------------

    def _add_category(self) -> None:
        session = self.current_session
        if session is None:
            return
        data = CategoryDialog(
            self, other_names=[category.name for category in session.categories]
        ).show()
        if data is None:
            return
        session.categories.append(Category.create(**data))
        self._commit()

    def _edit_category(self, category_id: str) -> None:
        session = self.current_session
        if session is None:
            return
        category = next(
            (item for item in session.categories if item.id == category_id), None
        )
        if category is None:
            return
        others = [item.name for item in session.categories if item.id != category.id]
        data = CategoryDialog(self, category, others).show()
        if data is None:
            return
        for key, value in data.items():
            setattr(category, key, value)
        self._commit()

    def _delete_category(self, category_id: str) -> None:
        session = self.current_session
        if session is None:
            return
        category = next(
            (item for item in session.categories if item.id == category_id), None
        )
        if category is None:
            return

        count, _total = session.category_stats(category.id)
        if count:
            messagebox.showwarning(
                "Нельзя удалить",
                f"К виду «{category.name}» привязано {records_label(count)}. "
                "Сначала переназначьте или удалите эти расходы.",
                parent=self,
            )
            return

        if not messagebox.askyesno(
            "Удалить вид расходов",
            f"Удалить вид расходов «{category.name}»?",
            parent=self,
        ):
            return
        session.categories.remove(category)
        self._commit()

    # --- служебное -------------------------------------------------------

    def _commit(self) -> None:
        try:
            storage.save(self.store, self.data_path)
            self._saved_text.set("Сохранено в " + time.strftime("%H:%M:%S"))
        except Exception as exc:  # noqa: BLE001
            self._saved_text.set("Не сохранено")
            messagebox.showerror(
                "Ошибка сохранения",
                f"Не удалось сохранить данные:\n{exc}",
                parent=self,
            )
        self.refresh()

    def _show_load_error(self) -> None:
        messagebox.showwarning(
            "Файл данных",
            f"{self._load_error}\n\nПриложение запущено с пустыми данными.",
            parent=self,
        )

    def _open_data_folder(self) -> None:
        try:
            folder = self.data_path.parent
            folder.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Не удалось открыть папку", str(exc), parent=self)
