"""Палитра, шрифты и настройка ttk-стилей в минималистичном ключе."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk

# --- палитра -------------------------------------------------------------

BG = "#F4F3F0"
SIDEBAR = "#EEEDE9"
SURFACE = "#FFFFFF"
HOVER = "#F7F6F3"
BORDER = "#E3E1DC"
BORDER_STRONG = "#D4D1C9"
TEXT = "#262625"
MUTED = "#86837B"
FAINT = "#B0ACA3"
ACCENT = "#4C6152"
ACCENT_HOVER = "#3E5044"
SELECT = "#ECEFEA"
DANGER = "#9C5A4D"
POSITIVE = "#4C7A5B"
NEGATIVE = "#A0594A"

# --- шрифты --------------------------------------------------------------

FONT = "Segoe UI"
BODY = (FONT, 10)
BODY_BOLD = (FONT, 10, "bold")
SMALL = (FONT, 9)
TINY = (FONT, 8)
LABEL = (FONT, 8)
TITLE = (FONT, 19, "bold")
DIALOG_TITLE = (FONT, 14, "bold")
VALUE = (FONT, 19, "bold")
APP_TITLE = (FONT, 14, "bold")


def enable_dpi_awareness() -> None:
    """Убирает размытие шрифтов на Windows при масштабировании экрана."""
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:  # noqa: BLE001
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:  # noqa: BLE001
            pass


def apply_theme(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.background", SURFACE)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", SELECT)
    root.option_add("*TCombobox*Listbox.selectForeground", TEXT)
    root.option_add("*TCombobox*Listbox.font", BODY)

    # --- кнопки ----------------------------------------------------------
    style.configure(
        "TButton",
        font=BODY,
        padding=(14, 7),
        background=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=SURFACE,
        darkcolor=SURFACE,
        focuscolor=SURFACE,
        relief="flat",
    )
    style.map(
        "TButton",
        background=[("pressed", SELECT), ("active", HOVER)],
        bordercolor=[("active", BORDER_STRONG), ("focus", BORDER_STRONG)],
        foreground=[("disabled", FAINT)],
    )

    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground="#FFFFFF",
        bordercolor=ACCENT,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        focuscolor=ACCENT,
        padding=(14, 7),
    )
    style.map(
        "Accent.TButton",
        background=[("pressed", ACCENT_HOVER), ("active", ACCENT_HOVER)],
        bordercolor=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)],
        foreground=[("disabled", "#D9DDD7")],
    )

    style.configure(
        "Ghost.TButton",
        background=BG,
        foreground=MUTED,
        bordercolor=BG,
        lightcolor=BG,
        darkcolor=BG,
        focuscolor=BG,
        padding=(10, 6),
    )
    style.map(
        "Ghost.TButton",
        background=[("active", HOVER), ("pressed", SELECT)],
        bordercolor=[("active", HOVER), ("pressed", SELECT)],
        foreground=[("active", TEXT), ("pressed", TEXT)],
    )

    style.configure(
        "SurfaceGhost.TButton",
        background=SURFACE,
        foreground=MUTED,
        bordercolor=SURFACE,
        lightcolor=SURFACE,
        darkcolor=SURFACE,
        focuscolor=SURFACE,
        padding=(10, 6),
    )
    style.map(
        "SurfaceGhost.TButton",
        background=[("active", HOVER), ("pressed", SELECT)],
        bordercolor=[("active", HOVER), ("pressed", SELECT)],
        foreground=[("active", TEXT), ("pressed", TEXT), ("disabled", FAINT)],
    )

    style.configure(
        "DangerGhost.TButton",
        background=BG,
        foreground=MUTED,
        bordercolor=BG,
        lightcolor=BG,
        darkcolor=BG,
        focuscolor=BG,
        padding=(10, 6),
    )
    style.map(
        "DangerGhost.TButton",
        background=[("active", HOVER), ("pressed", SELECT)],
        bordercolor=[("active", HOVER), ("pressed", SELECT)],
        foreground=[("active", DANGER), ("pressed", DANGER), ("disabled", FAINT)],
    )

    style.configure(
        "SurfaceDangerGhost.TButton",
        background=SURFACE,
        foreground=MUTED,
        bordercolor=SURFACE,
        lightcolor=SURFACE,
        darkcolor=SURFACE,
        focuscolor=SURFACE,
        padding=(10, 6),
    )
    style.map(
        "SurfaceDangerGhost.TButton",
        background=[("active", HOVER), ("pressed", SELECT)],
        bordercolor=[("active", HOVER), ("pressed", SELECT)],
        foreground=[("active", DANGER), ("pressed", DANGER), ("disabled", FAINT)],
    )

    style.configure(
        "SidebarGhost.TButton",
        background=SIDEBAR,
        foreground=MUTED,
        bordercolor=SIDEBAR,
        lightcolor=SIDEBAR,
        darkcolor=SIDEBAR,
        focuscolor=SIDEBAR,
        padding=(8, 4),
        font=TINY,
    )
    style.map(
        "SidebarGhost.TButton",
        background=[("active", HOVER), ("pressed", SELECT)],
        bordercolor=[("active", HOVER), ("pressed", SELECT)],
        foreground=[("active", TEXT), ("pressed", TEXT)],
    )

    # --- поля ввода ------------------------------------------------------
    style.configure(
        "TEntry",
        fieldbackground=SURFACE,
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=SURFACE,
        darkcolor=SURFACE,
        insertcolor=TEXT,
        padding=(8, 6),
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", ACCENT)],
        lightcolor=[("focus", ACCENT)],
        darkcolor=[("focus", ACCENT)],
    )

    style.configure(
        "TCombobox",
        fieldbackground=SURFACE,
        background=SURFACE,
        foreground=TEXT,
        arrowcolor=MUTED,
        bordercolor=BORDER,
        lightcolor=SURFACE,
        darkcolor=SURFACE,
        padding=(8, 6),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE), ("disabled", HOVER)],
        foreground=[("readonly", TEXT), ("disabled", FAINT)],
        selectbackground=[("readonly", SURFACE)],
        selectforeground=[("readonly", TEXT)],
        bordercolor=[("focus", ACCENT)],
        arrowcolor=[("active", TEXT)],
    )

    # --- вкладки ---------------------------------------------------------
    style.configure(
        "TNotebook",
        background=BG,
        borderwidth=0,
        tabmargins=(0, 0, 0, 0),
    )
    style.configure(
        "TNotebook.Tab",
        background=BG,
        foreground=MUTED,
        padding=(18, 9),
        borderwidth=0,
        bordercolor=BG,
        lightcolor=BG,
        darkcolor=BG,
        font=BODY,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", SURFACE), ("active", HOVER)],
        foreground=[("selected", TEXT), ("active", TEXT)],
        bordercolor=[("selected", SURFACE), ("active", HOVER)],
        lightcolor=[("selected", SURFACE), ("active", HOVER)],
        darkcolor=[("selected", SURFACE), ("active", HOVER)],
    )

    # --- таблицы ---------------------------------------------------------
    style.configure(
        "Treeview",
        background=SURFACE,
        fieldbackground=SURFACE,
        foreground=TEXT,
        borderwidth=0,
        relief="flat",
        rowheight=30,
        font=BODY,
    )
    style.map(
        "Treeview",
        background=[("selected", SELECT)],
        foreground=[("selected", TEXT)],
    )
    style.configure(
        "Treeview.Heading",
        background=BG,
        foreground=MUTED,
        relief="flat",
        borderwidth=0,
        font=LABEL,
        padding=(8, 8),
    )
    style.map("Treeview.Heading", background=[("active", HOVER)])
    try:
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    except tk.TclError:
        pass

    # --- прокрутка -------------------------------------------------------
    style.configure(
        "Slim.Vertical.TScrollbar",
        background=BORDER_STRONG,
        troughcolor=SURFACE,
        bordercolor=SURFACE,
        lightcolor=BORDER_STRONG,
        darkcolor=BORDER_STRONG,
        arrowcolor=MUTED,
        arrowsize=10,
        width=9,
        relief="flat",
    )
    style.map(
        "Slim.Vertical.TScrollbar",
        background=[("active", FAINT)],
        arrowcolor=[("active", TEXT)],
    )
    style.configure(
        "Sidebar.Vertical.TScrollbar",
        background=BORDER_STRONG,
        troughcolor=SIDEBAR,
        bordercolor=SIDEBAR,
        lightcolor=BORDER_STRONG,
        darkcolor=BORDER_STRONG,
        arrowcolor=MUTED,
        arrowsize=10,
        width=9,
        relief="flat",
    )
    style.map(
        "Sidebar.Vertical.TScrollbar",
        background=[("active", FAINT)],
        arrowcolor=[("active", TEXT)],
    )

    style.configure("TSeparator", background=BORDER)
