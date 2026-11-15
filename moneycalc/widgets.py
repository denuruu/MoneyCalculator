"""Переиспользуемые виджеты: прокручиваемая область, карточка, таблица."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Sequence

from .theme import (
    BODY_BOLD,
    BORDER,
    FAINT,
    FONT,
    MUTED,
    NEGATIVE,
    SELECT,
    SIDEBAR,
    SMALL,
    SURFACE,
    TEXT,
    TINY,
    VALUE,
)


class ScrollableFrame(tk.Frame):
    """Вертикально прокручиваемая область с внутренним фреймом."""

    def __init__(self, parent: tk.Misc, bg: str, scrollbar_style: str = "Slim.Vertical.TScrollbar"):
        super().__init__(parent, bg=bg)
        self._bg = bg
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0, yscrollincrement=20)
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
            style=scrollbar_style,
        )
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.inner.bind("<MouseWheel>", self._on_wheel)

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self._window, width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_inner_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_wheel(self, event: tk.Event) -> str:
        content_height = self.inner.winfo_reqheight()
        if content_height <= self.canvas.winfo_height():
            return "break"
        step = -3 if event.delta > 0 else 3
        self.canvas.yview_scroll(step, "units")
        return "break"

    def bind_wheel_recursive(self) -> None:
        def walk(widget: tk.Misc) -> None:
            widget.bind("<MouseWheel>", self._on_wheel)
            for child in widget.winfo_children():
                walk(child)

        walk(self.inner)


class SummaryCard(tk.Frame):
    """Карточка с заголовком, крупным значением и подписью."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        value: str,
        subtitle: str = "",
        value_color: str = TEXT,
    ):
        super().__init__(
            parent,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
            bd=0,
        )
        inner = tk.Frame(self, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=18, pady=15)

        tk.Label(
            inner,
            text=title.upper(),
            bg=SURFACE,
            fg=MUTED,
            font=TINY,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            inner,
            text=value,
            bg=SURFACE,
            fg=value_color,
            font=VALUE,
            anchor="w",
        ).pack(fill="x", pady=(6, 2))
        if subtitle:
            tk.Label(
                inner,
                text=subtitle,
                bg=SURFACE,
                fg=FAINT,
                font=TINY,
                anchor="w",
            ).pack(fill="x")


class TableTab(tk.Frame):
    """Вкладка со списком записей: панель действий, таблица и итог."""

    def __init__(
        self,
        parent: tk.Misc,
        columns: Sequence[dict],
        *,
        on_add: Callable[[], None],
        on_edit: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        empty_text: str = "",
        add_text: str = "Добавить",
    ):
        super().__init__(parent, bg=SURFACE)
        self._on_edit = on_edit
        self._on_delete = on_delete

        toolbar = tk.Frame(self, bg=SURFACE)
        toolbar.pack(fill="x", pady=(0, 12))
        ttk.Button(toolbar, text=add_text, style="Accent.TButton", command=on_add).pack(side="left")

        self.edit_btn = ttk.Button(
            toolbar,
            text="Изменить",
            style="SurfaceGhost.TButton",
            command=self._edit_selected,
            state="disabled",
        )
        self.edit_btn.pack(side="left", padx=(8, 0))

        self.delete_btn = ttk.Button(
            toolbar,
            text="Удалить",
            style="SurfaceDangerGhost.TButton",
            command=self._delete_selected,
            state="disabled",
        )
        self.delete_btn.pack(side="left", padx=(8, 0))

        footer = tk.Frame(self, bg=SURFACE)
        footer.pack(side="bottom", fill="x", pady=(10, 0))
        self.count_label = tk.Label(footer, text="", bg=SURFACE, fg=MUTED, font=TINY, anchor="w")
        self.count_label.pack(side="left")
        self.total_label = tk.Label(footer, text="", bg=SURFACE, fg=TEXT, font=(FONT, 9, "bold"))
        self.total_label.pack(side="right")

        table_wrap = tk.Frame(self, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        table_wrap.pack(fill="both", expand=True)
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_wrap,
            columns=[column["key"] for column in columns],
            show="headings",
            selectmode="browse",
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            table_wrap,
            orient="vertical",
            command=self.tree.yview,
            style="Slim.Vertical.TScrollbar",
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        for column in columns:
            anchor = column.get("anchor", "w")
            self.tree.heading(
                column["key"],
                text=column["title"],
                anchor=column.get("heading_anchor", anchor),
            )
            self.tree.column(
                column["key"],
                width=column["width"],
                minwidth=column.get("minwidth", 60),
                anchor=anchor,
                stretch=column.get("stretch", False),
            )

        self.tree.tag_configure("negative", foreground=NEGATIVE)

        self.empty_label = tk.Label(
            table_wrap,
            text=empty_text,
            bg=SURFACE,
            fg=FAINT,
            font=SMALL,
            justify="center",
            wraplength=460,
        )

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Delete>", lambda _event: self._delete_selected())

    def set_rows(
        self,
        rows: Sequence[tuple[str, Sequence[str], Sequence[str]]],
        count_text: str = "",
        total_text: str = "",
    ) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for item_id, values, tags in rows:
            self.tree.insert("", "end", iid=item_id, values=tuple(values), tags=tuple(tags))
        self.count_label.configure(text=count_text)
        self.total_label.configure(text=total_text)
        self._update_empty()
        self._on_select()

    def _update_empty(self) -> None:
        if self.tree.get_children():
            self.empty_label.place_forget()
        else:
            self.empty_label.place(relx=0.5, rely=0.45, anchor="center")

    def _selected_id(self) -> Optional[str]:
        selection = self.tree.selection()
        return selection[0] if selection else None

    def _on_select(self, _event: Optional[tk.Event] = None) -> None:
        has_selection = bool(self.tree.selection())
        self.edit_btn.configure(state="normal" if has_selection and self._on_edit else "disabled")
        self.delete_btn.configure(state="normal" if has_selection and self._on_delete else "disabled")

    def _edit_selected(self) -> None:
        item_id = self._selected_id()
        if item_id and self._on_edit:
            self._on_edit(item_id)

    def _delete_selected(self) -> None:
        item_id = self._selected_id()
        if item_id and self._on_delete:
            self._on_delete(item_id)

    def _on_double_click(self, event: tk.Event) -> None:
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        self.tree.selection_set(row_id)
        self._edit_selected()
