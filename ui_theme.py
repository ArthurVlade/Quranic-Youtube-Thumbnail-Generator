"""Apple-inspired UI theme — calm surfaces, segmented controls, no press-shrink."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable

FONT = "Segoe UI"
FONT_HEADING = "Segoe UI Semibold"

_current_mode = "dark"


@dataclass(frozen=True)
class Palette:
    bg_dark: str
    bg_panel: str
    bg_input: str
    bg_elev: str
    fg_primary: str
    fg_muted: str
    border: str
    accent: str
    accent_hover: str
    accent_text: str
    titlebar_bg: str
    titlebar_fg: str
    close_hover: str
    ctrl_hover: str
    grid_border: str
    grid_muted: str
    segment_track: str
    segment_active_bg: str
    segment_active_fg: str
    btn_bg: str
    btn_fg: str
    btn_hover: str


# Apple Human Interface — dark
DARK = Palette(
    bg_dark="#1c1c1e",
    bg_panel="#2c2c2e",
    bg_input="#3a3a3c",
    bg_elev="#48484a",
    fg_primary="#ffffff",
    fg_muted="#98989d",
    border="#48484a",
    accent="#0a84ff",
    accent_hover="#409cff",
    accent_text="#ffffff",
    titlebar_bg="#1c1c1e",
    titlebar_fg="#ffffff",
    close_hover="#ff453a",
    ctrl_hover="#3a3a3c",
    grid_border="#48484a",
    grid_muted="#8e8e93",
    segment_track="#3a3a3c",
    segment_active_bg="#636366",
    segment_active_fg="#ffffff",
    btn_bg="#3a3a3c",
    btn_fg="#ffffff",
    btn_hover="#48484a",
)

# Light mode — blue-slate mist (clearly not white; pairs with window gradient)
LIGHT = Palette(
    bg_dark="#a8b8cc",
    bg_panel="#c4d0e0",
    bg_input="#ccd6e4",
    bg_elev="#98a8bc",
    fg_primary="#1e293b",
    fg_muted="#64748b",
    border="#8fa0b8",
    accent="#334155",
    accent_hover="#1e293b",
    accent_text="#eef2f7",
    titlebar_bg="#9aacc4",
    titlebar_fg="#1e293b",
    close_hover="#b91c1c",
    ctrl_hover="#8fa0b8",
    grid_border="#8fa0b8",
    grid_muted="#64748b",
    segment_track="#b0bece",
    segment_active_bg="#d0dae8",
    segment_active_fg="#0f172a",
    btn_bg="#b0bece",
    btn_fg="#1e293b",
    btn_hover="#98a8bc",
)

# Gradient stops for light-mode window backdrop (RGB) — visible top→bottom shift
LIGHT_GRADIENT = {
    "top": (0xB0, 0xBE, 0xD4),
    "upper": (0x9A, 0xAC, 0xC4),
    "mid": (0x88, 0x9C, 0xB4),
    "lower": (0x78, 0x8E, 0xA8),
    "bottom": (0x68, 0x7E, 0x98),
    "wash": (0xC0, 0xCE, 0xE0),
}

LIGHT_CONTENT_INSET = 26

BG_DARK = DARK.bg_dark
BG_PANEL = DARK.bg_panel
BG_INPUT = DARK.bg_input
BG_ELEV = DARK.bg_elev
FG_PRIMARY = DARK.fg_primary
FG_MUTED = DARK.fg_muted
BORDER = DARK.border
ACCENT = DARK.accent
ACCENT_HOVER = DARK.accent_hover
ACCENT_TEXT = DARK.accent_text
TITLEBAR_BG = DARK.titlebar_bg
TITLEBAR_FG = DARK.titlebar_fg
CLOSE_HOVER = DARK.close_hover
CTRL_HOVER = DARK.ctrl_hover


def get_theme_mode() -> str:
    return _current_mode


def palette() -> Palette:
    return DARK if _current_mode == "dark" else LIGHT


def set_theme_mode(mode: str) -> str:
    global _current_mode
    _current_mode = "light" if mode == "light" else "dark"
    _sync_exports()
    return _current_mode


def toggle_theme_mode() -> str:
    return set_theme_mode("light" if _current_mode == "dark" else "dark")


def _sync_exports() -> None:
    global BG_DARK, BG_PANEL, BG_INPUT, BG_ELEV, FG_PRIMARY, FG_MUTED, BORDER
    global ACCENT, ACCENT_HOVER, ACCENT_TEXT, TITLEBAR_BG, TITLEBAR_FG
    global CLOSE_HOVER, CTRL_HOVER
    p = palette()
    BG_DARK = p.bg_dark
    BG_PANEL = p.bg_panel
    BG_INPUT = p.bg_input
    BG_ELEV = p.bg_elev
    FG_PRIMARY = p.fg_primary
    FG_MUTED = p.fg_muted
    BORDER = p.border
    ACCENT = p.accent
    ACCENT_HOVER = p.accent_hover
    ACCENT_TEXT = p.accent_text
    TITLEBAR_BG = p.titlebar_bg
    TITLEBAR_FG = p.titlebar_fg
    CLOSE_HOVER = p.close_hover
    CTRL_HOVER = p.ctrl_hover


def style_segment_button(btn: tk.Button, *, active: bool, compact: bool = False) -> None:
    """Apple segmented-control cell — fixed size; selection = accent text emphasis, no press-shrink."""
    p = palette()
    padx = 8 if compact else 12
    pady = 4 if compact else 6
    size = 8 if compact else 9
    track = p.segment_track
    btn.configure(
        relief="flat",
        bd=0,
        overrelief="flat",
        highlightthickness=0,
        padx=padx,
        pady=pady,
        cursor="hand2",
        bg=track,
        activebackground=track,
    )
    if active:
        btn.configure(
            fg=p.accent,
            font=(FONT, size, "bold"),
            activeforeground=p.accent,
        )
    else:
        btn.configure(
            fg=p.fg_muted,
            font=(FONT, size),
            activeforeground=p.fg_primary,
        )


def apply_theme(root: tk.Misc, mode: str | None = None) -> ttk.Style:
    if mode is not None:
        set_theme_mode(mode)
    p = palette()
    root.configure(bg=p.bg_dark)

    style = ttk.Style(root)
    style.theme_use("clam")

    _flat_btn_maps = [
        ("TButton", p.btn_bg, p.btn_fg, p.btn_hover),
        ("Pill.TButton", p.segment_track, p.fg_muted, p.btn_hover),
        ("Ghost.TButton", p.bg_panel, p.accent, p.ctrl_hover),
    ]

    style.configure(
        ".",
        background=p.bg_dark,
        foreground=p.fg_primary,
        fieldbackground=p.bg_input,
        bordercolor=p.border,
        font=(FONT, 10),
    )

    style.configure("TFrame", background=p.bg_dark)
    style.configure("Gutter.TFrame", background=p.bg_dark)
    style.configure("Panel.TFrame", background=p.bg_panel)
    style.configure("Titlebar.TFrame", background=p.titlebar_bg)

    style.configure("TLabel", background=p.bg_dark, foreground=p.fg_primary)
    style.configure("Panel.TLabel", background=p.bg_panel, foreground=p.fg_primary)
    style.configure("Muted.TLabel", background=p.bg_dark, foreground=p.fg_muted)
    style.configure("Panel.Muted.TLabel", background=p.bg_panel, foreground=p.fg_muted)
    style.configure("Heading.TLabel", background=p.bg_dark, foreground=p.fg_primary, font=(FONT_HEADING, 12))
    style.configure("Panel.Heading.TLabel", background=p.bg_panel, foreground=p.fg_primary, font=(FONT_HEADING, 11))

    style.configure("TLabelframe", background=p.bg_dark, foreground=p.fg_primary, bordercolor=p.border)
    style.configure("TLabelframe.Label", background=p.bg_dark, foreground=p.fg_primary, font=(FONT_HEADING, 10))
    style.configure("Panel.TLabelframe", background=p.bg_panel, foreground=p.fg_primary, bordercolor=p.border)
    style.configure("Panel.TLabelframe.Label", background=p.bg_panel, foreground=p.fg_primary, font=(FONT_HEADING, 10))
    style.configure("Dark.TLabelframe", background=p.bg_panel, foreground=p.fg_primary, bordercolor=p.border)
    style.configure("Dark.TLabelframe.Label", background=p.bg_panel, foreground=p.fg_muted, font=(FONT, 9))

    style.configure(
        "TEntry",
        fieldbackground=p.bg_input,
        foreground=p.fg_primary,
        insertcolor=p.accent,
        bordercolor=p.border,
        borderwidth=1,
        padding=(10, 8),
    )
    style.map("TEntry", bordercolor=[("focus", p.accent)])

    style.configure(
        "TCombobox",
        fieldbackground=p.bg_input,
        background=p.bg_input,
        foreground=p.fg_primary,
        arrowcolor=p.fg_muted,
        bordercolor=p.border,
        borderwidth=1,
        padding=(8, 6),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", p.bg_input)],
        foreground=[("readonly", p.fg_primary)],
        bordercolor=[("focus", p.accent)],
    )

    style.configure(
        "TSpinbox",
        fieldbackground=p.bg_input,
        foreground=p.fg_primary,
        arrowcolor=p.fg_muted,
        bordercolor=p.border,
        borderwidth=1,
        padding=(6, 5),
    )

    for name, bg, fg, hover in _flat_btn_maps:
        style.configure(
            name,
            background=bg,
            foreground=fg,
            bordercolor=bg,
            borderwidth=0,
            focuscolor=bg,
            padding=(14, 8),
            relief="flat",
            font=(FONT, 10),
        )
        style.map(
            name,
            background=[("active", hover), ("pressed", hover), ("disabled", bg)],
            foreground=[("active", fg), ("pressed", fg), ("disabled", p.fg_muted)],
            bordercolor=[("active", hover), ("pressed", hover)],
        )

    style.configure(
        "Accent.TButton",
        background=p.accent,
        foreground=p.accent_text,
        bordercolor=p.accent,
        borderwidth=0,
        focuscolor=p.accent,
        padding=(18, 10),
        relief="flat",
        font=(FONT_HEADING, 10),
    )
    style.map(
        "Accent.TButton",
        background=[("active", p.accent_hover), ("pressed", p.accent_hover), ("disabled", p.accent)],
        foreground=[("active", p.accent_text), ("pressed", p.accent_text)],
    )

    style.configure(
        "TRadiobutton",
        background=p.bg_panel,
        foreground=p.fg_primary,
        indicatorcolor=p.bg_input,
        focuscolor=p.bg_panel,
    )
    style.map(
        "TRadiobutton",
        indicatorcolor=[("selected", p.accent)],
        foreground=[("active", p.fg_primary)],
    )

    style.configure(
        "TCheckbutton",
        background=p.bg_panel,
        foreground=p.fg_primary,
        indicatorcolor=p.bg_input,
        focuscolor=p.bg_panel,
    )
    style.map(
        "TCheckbutton",
        indicatorcolor=[("selected", p.accent)],
        foreground=[("active", p.fg_primary)],
    )
    style.configure(
        "Group.TCheckbutton",
        background=p.bg_dark,
        foreground=p.fg_primary,
        indicatorcolor=p.bg_input,
        focuscolor=p.bg_dark,
    )
    style.map(
        "Group.TCheckbutton",
        indicatorcolor=[("selected", p.accent)],
        foreground=[("active", p.fg_primary)],
    )

    style.configure("ControlBar.TFrame", background=p.bg_input)
    style.configure("ControlBar.TLabel", background=p.bg_input, foreground=p.fg_primary)
    style.configure("ControlBar.Muted.TLabel", background=p.bg_input, foreground=p.fg_muted)

    style.configure(
        "TScale",
        background=p.bg_panel,
        troughcolor=p.bg_elev,
        bordercolor=p.border,
        lightcolor=p.bg_elev,
        darkcolor=p.border,
    )
    style.configure(
        "Horizontal.TScale",
        background=p.bg_panel,
        troughcolor=p.bg_elev,
        bordercolor=p.border,
        lightcolor=p.bg_elev,
        darkcolor=p.border,
    )
    style.configure(
        "ControlBar.Horizontal.TScale",
        background=p.bg_input,
        troughcolor=p.bg_elev,
        bordercolor=p.border,
        lightcolor=p.bg_elev,
        darkcolor=p.border,
    )
    style.map(
        "ControlBar.Horizontal.TScale",
        background=[("active", p.bg_input)],
    )
    style.configure("TProgressbar", background=p.accent, troughcolor=p.bg_input, bordercolor=p.bg_input)

    style.configure(
        "Vertical.TScrollbar",
        background=p.bg_elev,
        troughcolor=p.bg_dark,
        bordercolor=p.bg_dark,
        arrowcolor=p.fg_muted,
    )

    style.configure("TSeparator", background=p.border)
    return style


def style_listbox(listbox: tk.Listbox) -> None:
    p = palette()
    listbox.configure(
        bg=p.bg_input,
        fg=p.fg_primary,
        selectbackground=p.accent,
        selectforeground=p.accent_text,
        highlightthickness=1,
        highlightbackground=p.border,
        relief="flat",
        borderwidth=0,
        font=(FONT, 10),
    )


def style_text(widget: tk.Text) -> None:
    p = palette()
    widget.configure(
        bg=p.bg_input,
        fg=p.fg_primary,
        insertbackground=p.accent,
        relief="flat",
        highlightthickness=1,
        highlightbackground=p.border,
        font=(FONT, 10),
    )


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _lerp_rgb(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (_lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t), _lerp(c1[2], c2[2], t))


def _mix_rgb(c1: tuple[int, int, int], c2: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return _lerp_rgb(c1, c2, max(0.0, min(1.0, amount)))


def _gradient_row_color(t: float) -> tuple[int, int, int]:
    g = LIGHT_GRADIENT
    top, upper, mid, lower, bottom = g["top"], g["upper"], g["mid"], g["lower"], g["bottom"]
    if t < 0.35:
        return _lerp_rgb(top, upper, t / 0.35)
    if t < 0.65:
        return _lerp_rgb(upper, mid, (t - 0.35) / 0.30)
    if t < 0.85:
        return _lerp_rgb(mid, lower, (t - 0.65) / 0.20)
    return _lerp_rgb(lower, bottom, (t - 0.85) / 0.15)


_GRADIENT_CACHE: dict[tuple[int, int], object] = {}
_GRADIENT_CACHE_MAX = 6


def render_light_gradient(width: int, height: int):
    """Band-rendered gradient with cache — fast enough for live theme/resize."""
    from PIL import Image, ImageDraw

    w = max(width, 2)
    h = max(height, 2)
    # Render at reduced height, scale up — gradient is smooth so this is fine
    render_h = max(64, min(h, 256))
    render_w = max(64, min(w, 512))
    key = (render_w, render_h)
    cached = _GRADIENT_CACHE.get(key)
    if cached is None:
        img = Image.new("RGB", (render_w, render_h))
        draw = ImageDraw.Draw(img)
        bands = 40
        band_h = max(1, (render_h + bands - 1) // bands)
        wash = LIGHT_GRADIENT["wash"]
        for b in range(bands):
            y0 = b * band_h
            y1 = min(render_h, y0 + band_h)
            if y0 >= render_h:
                break
            t = ((y0 + y1) / 2) / max(render_h - 1, 1)
            row = _gradient_row_color(t)
            draw.rectangle((0, y0, render_w, y1), fill=row)
            if render_w > 80:
                warm = _mix_rgb(row, wash, 0.10)
                draw.rectangle((render_w * 3 // 5, y0, render_w, y1), fill=warm)
        _GRADIENT_CACHE[key] = img
        if len(_GRADIENT_CACHE) > _GRADIENT_CACHE_MAX:
            _GRADIENT_CACHE.pop(next(iter(_GRADIENT_CACHE)))
        cached = img

    if cached.size == (w, h):
        return cached.copy()
    return cached.resize((w, h), Image.Resampling.BILINEAR)


class LightGradientBackdrop:
    """Full-window backdrop — gradient ring visible around inset content in light mode."""

    def __init__(self, root: tk.Misc) -> None:
        self._root = root
        self._canvas = tk.Canvas(root, highlightthickness=0, bd=0, borderwidth=0)
        self._photo = None
        self._job: str | None = None
        self._paint_key: tuple[int, int, str] | None = None
        self.inner = tk.Frame(self._canvas, highlightthickness=0, bd=0)
        self._win = self._canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self._canvas.bind("<Configure>", self._on_configure, add="+")

    def _inset(self) -> int:
        return LIGHT_CONTENT_INSET if get_theme_mode() == "light" else 0

    def mount(self) -> None:
        self._canvas.pack(fill="both", expand=True)
        self._root.bind("<Map>", self._on_map, add="+")
        self.refresh()

    def _on_map(self, _event=None) -> None:
        self._root.after_idle(self._schedule_paint)

    def refresh(self) -> None:
        p = palette()
        mode = get_theme_mode()
        if mode == "light":
            mid = LIGHT_GRADIENT["mid"]
            self.inner.configure(bg="#%02x%02x%02x" % mid)
            self._canvas.configure(bg="#%02x%02x%02x" % LIGHT_GRADIENT["top"])
        else:
            self.inner.configure(bg=p.bg_dark)
            self._canvas.configure(bg=p.bg_dark)
        self._sync_geometry()
        self._paint_key = None
        self._schedule_paint()

    def _sync_geometry(self) -> None:
        m = self._inset()
        w = max(self._canvas.winfo_width(), 4)
        h = max(self._canvas.winfo_height(), 4)
        self._canvas.coords(self._win, m, m)
        self._canvas.itemconfigure(self._win, width=max(w - 2 * m, 1), height=max(h - 2 * m, 1))

    def _on_configure(self, _event=None) -> None:
        self._sync_geometry()
        self._schedule_paint()

    def _schedule_paint(self) -> None:
        if self._job:
            self._root.after_cancel(self._job)
        self._job = self._root.after(120, self._repaint)

    def _repaint(self) -> None:
        self._job = None
        self._paint()

    def _paint(self) -> None:
        w = self._canvas.winfo_width()
        h = self._canvas.winfo_height()
        if w < 4 or h < 4:
            return
        mode = get_theme_mode()
        key = (w, h, mode)
        if key == self._paint_key and self._photo is not None:
            return

        from PIL import Image, ImageTk

        if mode == "light":
            img = render_light_gradient(w, h)
        else:
            p = palette()
            rgb = tuple(int(p.bg_dark[i : i + 2], 16) for i in (1, 3, 5))
            from PIL import Image
            img = Image.new("RGB", (w, h), rgb)
        self._photo = ImageTk.PhotoImage(img)
        self._paint_key = key
        if self._canvas.find_withtag("gradient"):
            self._canvas.itemconfigure("gradient", image=self._photo)
        else:
            self._canvas.delete("gradient")
            self._canvas.create_image(0, 0, anchor="nw", image=self._photo, tags="gradient")
            self._canvas.tag_lower("gradient")
            self._canvas.tag_raise(self._win)


class SegmentedTabView(ttk.Frame):
    """Apple-style segmented tab bar — selection highlights text, size stays fixed."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, style="Panel.TFrame", **kwargs)
        p = palette()
        self._track = tk.Frame(
            self,
            bg=p.segment_track,
            bd=0,
            highlightthickness=0,
            padx=4,
            pady=4,
        )
        self._track.pack(fill="x", padx=4, pady=(0, 10))
        self._content = ttk.Frame(self, style="Panel.TFrame")
        self._content.pack(fill="both", expand=True)
        self._tabs: list[tuple[str, tk.Button, ttk.Frame, tk.Canvas, ttk.Frame]] = []
        self._active = 0
        self._scroll_canvases: list[tk.Canvas] = []

    @property
    def scroll_canvases(self) -> list[tk.Canvas]:
        return self._scroll_canvases

    def add_tab(self, key: str, label: str) -> ttk.Frame:
        p = palette()
        idx = len(self._tabs)
        btn = tk.Button(
            self._track,
            text=label,
            command=lambda i=idx: self.select(i),
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        btn.pack(side="left", padx=1, pady=3)
        style_segment_button(btn, active=(idx == 0), compact=True)

        container = ttk.Frame(self._content, style="Panel.TFrame")
        canvas = tk.Canvas(container, bg=BG_PANEL, highlightthickness=0, borderwidth=0)
        vbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style="Panel.TFrame", padding=12)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)
        canvas.pack(side="left", fill="both", expand=True)

        def _sync(_e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            need = inner.winfo_reqheight() > canvas.winfo_height()
            if need and not vbar.winfo_ismapped():
                vbar.pack(side="right", fill="y")
            elif not need and vbar.winfo_ismapped():
                vbar.pack_forget()
                canvas.yview_moveto(0)

        inner.bind("<Configure>", _sync)
        canvas.bind("<Configure>", lambda e: (canvas.itemconfigure(win, width=e.width), _sync()))

        def _wheel(e):
            if vbar.winfo_ismapped():
                canvas.yview_scroll(int(-e.delta / 120), "units")

        canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _wheel))
        canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

        self._scroll_canvases.append(canvas)
        self._tabs.append((key, btn, container, canvas, inner))
        container.place(relx=0, rely=0, relwidth=1, relheight=1)
        if idx > 0:
            container.lower()
        return inner

    def select(self, index: int) -> None:
        if index == self._active:
            return
        self._active = index
        _key, _btn, active, _canvas, _inner = self._tabs[index]
        active.lift()
        for i, (_key, btn, _container, _canvas, _inner) in enumerate(self._tabs):
            style_segment_button(btn, active=(i == index), compact=True)

    def refresh_theme(self) -> None:
        p = palette()
        self._track.configure(bg=p.segment_track)
        for canvas in self._scroll_canvases:
            canvas.configure(bg=p.bg_panel)
        for i, (_key, btn, _container, _canvas, _inner) in enumerate(self._tabs):
            style_segment_button(btn, active=(i == self._active), compact=True)

    def refresh_labels(self, label_fn: Callable[[str], str]) -> None:
        for key, btn, _container, _canvas, _inner in self._tabs:
            btn.configure(text=label_fn(key))

    def active_index(self) -> int:
        return self._active


class SegmentedControl(tk.Frame):
    """Horizontal segmented filter (e.g. background categories)."""

    def __init__(self, master, on_select: Callable[[str], None], **kwargs) -> None:
        p = palette()
        super().__init__(master, bg=p.segment_track, bd=0, highlightthickness=0, **kwargs)
        self._on_select = on_select
        self._buttons: dict[str, tk.Button] = {}
        self._active = ""

    def set_options(self, options: list[tuple[str, str]], *, active: str) -> None:
        for child in self.winfo_children():
            child.destroy()
        self._buttons.clear()
        self._active = active
        for value, label in options:
            btn = tk.Button(
                self,
                text=label,
                relief="flat",
                bd=0,
                highlightthickness=0,
                command=lambda v=value: self._select(v),
            )
            btn.pack(side="left", padx=1, pady=3)
            self._buttons[value] = btn
        self.refresh_theme()

    def _select(self, value: str) -> None:
        self._active = value
        self.refresh_theme()
        self._on_select(value)

    def set_active(self, value: str) -> None:
        """Update selection visuals without firing on_select."""
        self._active = value
        if self._buttons:
            self.refresh_theme()

    def refresh_theme(self) -> None:
        p = palette()
        self.configure(bg=p.segment_track)
        for value, btn in self._buttons.items():
            style_segment_button(btn, active=(value == self._active), compact=True)

    def refresh_labels(self, label_fn: Callable[[str], str]) -> None:
        for value, btn in self._buttons.items():
            btn.configure(text=label_fn(value))
