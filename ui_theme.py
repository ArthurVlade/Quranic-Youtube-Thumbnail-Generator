"""Modern dark UI theme for the thumbnail generator."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# ── Palette ────────────────────────────────────────────────────────────────
BG_DARK = "#0e1117"      # app background
BG_PANEL = "#161b22"     # control panels
BG_INPUT = "#21262d"     # entries / inputs
BG_ELEV = "#1c2128"      # elevated rows / hover
FG_PRIMARY = "#e6edf3"
FG_MUTED = "#7d8590"
BORDER = "#2a313a"

ACCENT = "#d4af37"        # brand gold
ACCENT_HOVER = "#e6c45a"
ACCENT_TEXT = "#0e1117"   # dark text on gold

# Title bar
TITLEBAR_BG = "#0b0e13"
TITLEBAR_FG = "#e6edf3"
CLOSE_HOVER = "#e5484d"
CTRL_HOVER = "#262c36"

FONT = "Segoe UI"
FONT_HEADING = "Segoe UI Semibold"


def apply_theme(root: tk.Tk) -> ttk.Style:
    root.configure(bg=BG_DARK)

    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG_DARK, foreground=FG_PRIMARY,
                    fieldbackground=BG_INPUT, bordercolor=BORDER,
                    font=(FONT, 9))

    style.configure("TFrame", background=BG_DARK)
    style.configure("Panel.TFrame", background=BG_PANEL)
    style.configure("Titlebar.TFrame", background=TITLEBAR_BG)

    style.configure("TLabel", background=BG_DARK, foreground=FG_PRIMARY)
    style.configure("Panel.TLabel", background=BG_PANEL, foreground=FG_PRIMARY)
    style.configure("Muted.TLabel", background=BG_DARK, foreground=FG_MUTED)
    style.configure("Panel.Muted.TLabel", background=BG_PANEL, foreground=FG_MUTED)
    style.configure("Heading.TLabel", background=BG_DARK, foreground=FG_PRIMARY,
                    font=(FONT_HEADING, 11))
    style.configure("Panel.Heading.TLabel", background=BG_PANEL, foreground=ACCENT,
                    font=(FONT_HEADING, 10))

    style.configure("TLabelframe", background=BG_DARK, foreground=FG_PRIMARY, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=BG_DARK, foreground=FG_MUTED)
    style.configure("Panel.TLabelframe", background=BG_PANEL, foreground=FG_PRIMARY, bordercolor=BORDER)
    style.configure("Panel.TLabelframe.Label", background=BG_PANEL, foreground=FG_PRIMARY)
    style.configure("Dark.TLabelframe", background=BG_PANEL, foreground=FG_PRIMARY, bordercolor=BORDER)
    style.configure("Dark.TLabelframe.Label", background=BG_PANEL, foreground=FG_MUTED, font=(FONT, 8))

    style.configure("TEntry", fieldbackground=BG_INPUT, foreground=FG_PRIMARY,
                    insertcolor=ACCENT, bordercolor=BORDER, borderwidth=1, padding=5)
    style.map("TEntry", bordercolor=[("focus", ACCENT)])

    style.configure("TCombobox", fieldbackground=BG_INPUT, background=BG_INPUT,
                    foreground=FG_PRIMARY, arrowcolor=FG_MUTED, bordercolor=BORDER,
                    borderwidth=1, padding=4)
    style.map("TCombobox",
              fieldbackground=[("readonly", BG_INPUT)],
              foreground=[("readonly", FG_PRIMARY)],
              bordercolor=[("focus", ACCENT)],
              arrowcolor=[("active", ACCENT)])

    style.configure("TSpinbox", fieldbackground=BG_INPUT, foreground=FG_PRIMARY,
                    arrowcolor=FG_MUTED, bordercolor=BORDER, borderwidth=1, padding=3)

    # Buttons — flat, subtle border, gold hover
    style.configure("TButton", background=BG_ELEV, foreground=FG_PRIMARY,
                    bordercolor=BORDER, borderwidth=1, focuscolor=BG_PANEL,
                    padding=(12, 7), relief="flat", font=(FONT, 9))
    style.map("TButton",
              background=[("active", CTRL_HOVER), ("pressed", BG_INPUT)],
              bordercolor=[("active", ACCENT)],
              foreground=[("active", FG_PRIMARY)])

    style.configure("Accent.TButton", background=ACCENT, foreground=ACCENT_TEXT,
                    bordercolor=ACCENT, borderwidth=0, padding=(14, 8),
                    relief="flat", font=(FONT_HEADING, 9))
    style.map("Accent.TButton",
              background=[("active", ACCENT_HOVER), ("pressed", "#c9a430")],
              foreground=[("active", ACCENT_TEXT)])

    style.configure("TRadiobutton", background=BG_PANEL, foreground=FG_PRIMARY,
                    indicatorcolor=BG_INPUT, focuscolor=BG_PANEL)
    style.map("TRadiobutton",
              background=[("active", BG_PANEL)],
              indicatorcolor=[("selected", ACCENT)],
              foreground=[("active", ACCENT)])

    style.configure("TCheckbutton", background=BG_PANEL, foreground=FG_PRIMARY,
                    indicatorcolor=BG_INPUT, focuscolor=BG_PANEL)
    style.map("TCheckbutton",
              background=[("active", BG_PANEL)],
              indicatorcolor=[("selected", ACCENT)],
              foreground=[("active", ACCENT)])

    style.configure("TScale", background=BG_PANEL, troughcolor=BG_INPUT, bordercolor=BG_PANEL)
    style.configure("Horizontal.TScale", background=BG_PANEL, troughcolor=BG_INPUT)

    style.configure("TProgressbar", background=ACCENT, troughcolor=BG_INPUT, bordercolor=BG_INPUT)

    style.configure("Vertical.TScrollbar", background=BG_ELEV, troughcolor=BG_DARK,
                    bordercolor=BG_DARK, arrowcolor=FG_MUTED)
    style.configure("Horizontal.TScrollbar", background=BG_ELEV, troughcolor=BG_DARK,
                    bordercolor=BG_DARK, arrowcolor=FG_MUTED)

    # Notebook tabs — modern pill-ish look
    style.configure("TNotebook", background=BG_PANEL, bordercolor=BG_PANEL, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_PANEL, foreground=FG_MUTED,
                    padding=(14, 8), borderwidth=0, font=(FONT, 9))
    style.map("TNotebook.Tab",
              background=[("selected", BG_ELEV)],
              foreground=[("selected", ACCENT), ("active", FG_PRIMARY)])

    style.configure("TSeparator", background=BORDER)

    return style


def style_listbox(listbox: tk.Listbox) -> None:
    listbox.configure(
        bg=BG_INPUT,
        fg=FG_PRIMARY,
        selectbackground=ACCENT,
        selectforeground=ACCENT_TEXT,
        highlightthickness=1,
        highlightbackground=BORDER,
        relief="flat",
        borderwidth=0,
        font=(FONT, 9),
    )


def style_text(widget: tk.Text) -> None:
    widget.configure(
        bg=BG_INPUT,
        fg=FG_PRIMARY,
        insertbackground=ACCENT,
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
        font=(FONT, 9),
    )
