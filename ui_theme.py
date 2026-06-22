"""Dark UI theme for the thumbnail generator."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

BG_DARK = "#0d1117"
BG_PANEL = "#1a1d23"
BG_INPUT = "#252a33"
FG_PRIMARY = "#e6edf3"
FG_MUTED = "#9da7b3"
ACCENT = "#6e8efb"
ACCENT_HOVER = "#8aa4ff"
BORDER = "#30363d"


def apply_theme(root: tk.Tk) -> ttk.Style:
    root.configure(bg=BG_DARK)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG_DARK, foreground=FG_PRIMARY, fieldbackground=BG_INPUT, bordercolor=BORDER)
    style.configure("TFrame", background=BG_DARK)
    style.configure("Panel.TFrame", background=BG_PANEL)
    style.configure("TLabel", background=BG_DARK, foreground=FG_PRIMARY)
    style.configure("Panel.TLabel", background=BG_PANEL, foreground=FG_PRIMARY)
    style.configure("Muted.TLabel", background=BG_DARK, foreground=FG_MUTED)
    style.configure("Panel.Muted.TLabel", background=BG_PANEL, foreground=FG_MUTED)
    style.configure("Heading.TLabel", background=BG_DARK, foreground=FG_PRIMARY, font=("Segoe UI", 11, "bold"))
    style.configure("Panel.Heading.TLabel", background=BG_PANEL, foreground=FG_PRIMARY, font=("Segoe UI", 11, "bold"))
    style.configure("TLabelframe", background=BG_DARK, foreground=FG_PRIMARY, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=BG_DARK, foreground=FG_PRIMARY)
    style.configure("Panel.TLabelframe", background=BG_PANEL, foreground=FG_PRIMARY, bordercolor=BORDER)
    style.configure("Panel.TLabelframe.Label", background=BG_PANEL, foreground=FG_PRIMARY)

    style.configure(
        "TEntry",
        fieldbackground=BG_INPUT,
        foreground=FG_PRIMARY,
        insertcolor=FG_PRIMARY,
        bordercolor=BORDER,
    )
    style.configure(
        "TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_INPUT,
        foreground=FG_PRIMARY,
        arrowcolor=FG_PRIMARY,
        bordercolor=BORDER,
    )
    style.map("TCombobox", fieldbackground=[("readonly", BG_INPUT)], foreground=[("readonly", FG_PRIMARY)])

    style.configure("TButton", background=BG_PANEL, foreground=FG_PRIMARY, bordercolor=BORDER, padding=(10, 6))
    style.map("TButton", background=[("active", ACCENT)], foreground=[("active", FG_PRIMARY)])

    style.configure("Accent.TButton", background=ACCENT, foreground=FG_PRIMARY, bordercolor=ACCENT, padding=(10, 6))
    style.map("Accent.TButton", background=[("active", ACCENT_HOVER)])

    style.configure("TRadiobutton", background=BG_DARK, foreground=FG_PRIMARY)
    style.map("TRadiobutton", background=[("active", BG_DARK)])
    style.configure("TCheckbutton", background=BG_DARK, foreground=FG_PRIMARY)
    style.map("TCheckbutton", background=[("active", BG_DARK)])
    style.configure("TScale", background=BG_DARK, troughcolor=BG_INPUT)
    style.configure("Vertical.TScrollbar", background=BG_PANEL, troughcolor=BG_DARK, bordercolor=BORDER)
    style.configure("Horizontal.TScrollbar", background=BG_PANEL, troughcolor=BG_DARK, bordercolor=BORDER)

    style.configure("Dark.TLabelframe", background=BG_PANEL, foreground=FG_PRIMARY, bordercolor=BORDER)
    style.configure("Dark.TLabelframe.Label", background=BG_PANEL, foreground=FG_PRIMARY)

    style.configure("TNotebook", background=BG_PANEL, bordercolor=BORDER)
    style.configure("TNotebook.Tab", background=BG_INPUT, foreground=FG_MUTED, padding=(12, 6))
    style.map("TNotebook.Tab", background=[("selected", BG_PANEL)], foreground=[("selected", FG_PRIMARY)])

    return style


def style_listbox(listbox: tk.Listbox) -> None:
    listbox.configure(
        bg=BG_INPUT,
        fg=FG_PRIMARY,
        selectbackground=ACCENT,
        selectforeground=FG_PRIMARY,
        highlightthickness=1,
        highlightbackground=BORDER,
        relief="flat",
        borderwidth=0,
    )


def style_text(widget: tk.Text) -> None:
    widget.configure(
        bg=BG_INPUT,
        fg=FG_PRIMARY,
        insertbackground=FG_PRIMARY,
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
    )
