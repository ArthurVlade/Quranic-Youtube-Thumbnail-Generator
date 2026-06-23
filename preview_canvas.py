"""Interactive preview canvas — per-element drag handles + global block drag."""

from __future__ import annotations

import tkinter as tk
from typing import Literal

from PIL import Image, ImageTk

from ui_theme import BG_INPUT

PREVIEW_W = 640
PREVIEW_H = 360
OUTPUT_W  = 1280
OUTPUT_H  = 720

TEXT_OFFSET_X_MIN, TEXT_OFFSET_X_MAX = -520, 520
TEXT_OFFSET_Y_MIN, TEXT_OFFSET_Y_MAX = -120, 420

# One handle per text layer + global block handle
ELEMENT_HANDLES: list[tuple[str, str, str]] = [
    ("svg",     "#5b9cf6", "SVG"),      # blue
    ("title",   "#ffe566", "Title"),    # yellow
    ("reciter", "#6be5a0", "Reciter"),  # green
    ("badge",   "#ffd166", "Badge"),    # gold
]

DragTarget = Literal["block", "svg", "title", "reciter", "badge", "reciter_photo"]


_SNAP_THRESHOLD_PX = 14   # output pixels: snap element X to center when within this range


class InteractivePreviewCanvas(tk.Canvas):
    HANDLE_W = 28
    HANDLE_H = 40

    def __init__(self, master, on_layout_change) -> None:
        super().__init__(
            master,
            width=PREVIEW_W,
            height=PREVIEW_H,
            bg=BG_INPUT,
            highlightthickness=0,
            cursor="fleur",
        )
        self.on_layout_change = on_layout_change
        self.pre_w = PREVIEW_W
        self.pre_h = PREVIEW_H
        self.scale = self.pre_w / OUTPUT_W
        self._photo: ImageTk.PhotoImage | None = None
        self._source_image: Image.Image | None = None
        self._drag_target: DragTarget | None = None
        self._drag_start: tuple[int, int] | None = None

        # Global block offset (moves all elements together)
        self.block_x = 0
        self.block_y = 0

        # Per-element independent offsets
        self.svg_off     = [0, 0]
        self.title_off   = [0, 0]
        self.reciter_off = [0, 0]
        self.badge_off   = [0, 0]

        # Reciter photo overlay
        self.reciter_x     = 900
        self.reciter_y     = 420
        self.reciter_width = 220
        self.show_reciter  = False

        # Sizes (kept in sync from app.py) for approximate Y calculation
        self._svg_h      = 280
        self._title_size = 52
        self._rec_size   = 44
        self._badge_size = 28

        # Accurate element centres (output px) supplied by the renderer per frame.
        self._layout: dict = {}

        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<B1-Motion>",       self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Double-Button-1>", self._on_double_click)
        self.bind("<KeyPress>",        self._on_key)
        self.configure(takefocus=True)

    # ── external API ──────────────────────────────────────────────────────────

    def update_sizes(self, svg_h: int, title_size: int, rec_size: int, badge_size: int) -> None:
        self._svg_h      = svg_h
        self._title_size = title_size
        self._rec_size   = rec_size
        self._badge_size = badge_size

    def set_layout(self, layout: dict) -> None:
        """Receive accurate element centre Ys (output px) from the renderer."""
        self._layout = layout or {}

    def set_preview_size(self, w: int, h: int) -> None:
        """Resize the preview (keeps 16:9) and re-render the current frame."""
        w = max(PREVIEW_W, int(w))
        h = max(PREVIEW_H, int(h))
        if w == self.pre_w and h == self.pre_h:
            return
        self.pre_w, self.pre_h = w, h
        self.scale = self.pre_w / OUTPUT_W
        self.configure(width=self.pre_w, height=self.pre_h)
        if self._source_image is not None:
            self.show_image(self._source_image)

    def clamp_block(self) -> None:
        self.block_x = max(TEXT_OFFSET_X_MIN, min(TEXT_OFFSET_X_MAX, self.block_x))
        self.block_y = max(TEXT_OFFSET_Y_MIN, min(TEXT_OFFSET_Y_MAX, self.block_y))

    def layout_dict(self) -> dict:
        return {
            "text_offset_x":      self.block_x,
            "text_offset_y":      self.block_y,
            "svg_offset_x":       self.svg_off[0],
            "svg_offset_y":       self.svg_off[1],
            "title_offset_x":     self.title_off[0],
            "title_offset_y":     self.title_off[1],
            "reciter_offset_x":   self.reciter_off[0],
            "reciter_offset_y":   self.reciter_off[1],
            "badge_offset_x":     self.badge_off[0],
            "badge_offset_y":     self.badge_off[1],
            "reciter_overlay_x":  self.reciter_x,
            "reciter_overlay_y":  self.reciter_y,
            "reciter_overlay_width": self.reciter_width,
            "show_reciter_overlay":  self.show_reciter,
        }

    # ── coordinate helpers ────────────────────────────────────────────────────

    def _out_to_pre(self, x: float, y: float) -> tuple[int, int]:
        return int(x * self.scale), int(y * self.scale)

    def _delta_to_out(self, dx: int, dy: int) -> tuple[int, int]:
        return int(dx / self.scale), int(dy / self.scale)

    def _element_natural_ys(self) -> dict[str, int]:
        """Natural stack Y positions in output pixels (mirrors compute_element_ys)."""
        base_y = int(OUTPUT_H * 0.12) + self.block_y
        GAP_SVG   = 36
        GAP_TITLE = 28
        GAP_REC   = 40
        svg_y   = base_y
        title_y = svg_y   + self._svg_h      + GAP_SVG
        rec_y   = title_y + self._title_size  + GAP_TITLE
        badge_y = rec_y   + self._rec_size    + GAP_REC
        return {"svg": svg_y, "title": title_y, "reciter": rec_y, "badge": badge_y}

    def _element_handle_positions(self) -> dict[str, tuple[int, int]]:
        """Preview-space centre of each element."""
        cx = OUTPUT_W // 2 + self.block_x
        if self._layout:
            L = self._layout
            return {
                "svg":     self._out_to_pre(cx + self.svg_off[0],     L.get("svg", 0)     + self.svg_off[1]),
                "title":   self._out_to_pre(cx + self.title_off[0],   L.get("title", 0)   + self.title_off[1]),
                "reciter": self._out_to_pre(cx + self.reciter_off[0], L.get("reciter", 0) + self.reciter_off[1]),
                "badge":   self._out_to_pre(cx + self.badge_off[0],   L.get("badge", 0)   + self.badge_off[1]),
            }
        # Fallback approximation when no layout has been supplied yet
        nat = self._element_natural_ys()
        return {
            "svg":     self._out_to_pre(cx + self.svg_off[0],     nat["svg"]     + self._svg_h // 2      + self.svg_off[1]),
            "title":   self._out_to_pre(cx + self.title_off[0],   nat["title"]   + self._title_size // 2 + self.title_off[1]),
            "reciter": self._out_to_pre(cx + self.reciter_off[0], nat["reciter"] + self._rec_size // 2   + self.reciter_off[1]),
            "badge":   self._out_to_pre(cx + self.badge_off[0],   nat["badge"]   + self._badge_size      + self.badge_off[1]),
        }

    def _reciter_rect(self) -> tuple[int, int, int, int]:
        rx, ry = self._out_to_pre(self.reciter_x, self.reciter_y)
        rw = max(24, int(self.reciter_width * self.scale))
        rh = int(rw * 0.75)
        return rx - rw // 2, ry - rh // 2, rx + rw // 2, ry + rh // 2

    # ── drawing ───────────────────────────────────────────────────────────────

    def show_image(self, image: Image.Image) -> None:
        self._source_image = image
        preview = image.resize((self.pre_w, self.pre_h), Image.Resampling.LANCZOS)
        self._photo = ImageTk.PhotoImage(preview)
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self._photo, tags=("bg",))
        self._draw_guides()
        self._draw_handles()

    def _draw_guides(self) -> None:
        cx = self.pre_w // 2
        near_center = abs(self.block_x) <= 12
        line_color = "#d4af37" if near_center else "#666666"
        line_w = 2 if near_center else 1
        self.create_line(cx, 0, cx, self.pre_h, fill=line_color, dash=(4, 6), width=line_w, tags=("guide",))
        if near_center:
            self.create_text(cx + 5, 8, text="centered", fill="#d4af37", font=("Segoe UI", 7), anchor="nw", tags=("guide",))
        for frac in (1/3, 2/3):
            y = int(self.pre_h * frac)
            self.create_line(0, y, self.pre_w, y, fill="#333333", dash=(2, 8), width=1, tags=("guide",))

    def _draw_handles(self) -> None:
        positions = self._element_handle_positions()
        HW, HH = self.HANDLE_W, self.HANDLE_H

        for key, color, label in ELEMENT_HANDLES:
            cx, cy = positions[key]
            cy = max(HH // 2 + 2, min(self.pre_h - HH // 2 - 2, cy))
            x1, y1, x2, y2 = 2, cy - HH // 2, HW + 2, cy + HH // 2
            # Highlight the active drag target
            outline = "#ffffff" if self._drag_target == key else ""
            self.create_rectangle(x1, y1, x2, y2, fill=color, outline=outline, width=1,
                                  tags=("handle", f"h_{key}"))
            # 3-char label inside tab
            short = label[:3]
            self.create_text(x1 + (x2 - x1) // 2, (y1 + y2) // 2,
                             text=short, fill="#000000",
                             font=("Segoe UI", 7, "bold"), tags=("handle",))

        # Reciter photo handle (dashed box)
        if self.show_reciter:
            x1, y1, x2, y2 = self._reciter_rect()
            x1c = max(2, min(self.pre_w - 2, x1))
            y1c = max(2, min(self.pre_h - 2, y1))
            x2c = max(2, min(self.pre_w - 2, x2))
            y2c = max(2, min(self.pre_h - 2, y2))
            self.create_rectangle(x1c, y1c, x2c, y2c,
                                  outline="#ffd166", width=2, dash=(6, 3),
                                  tags=("handle", "h_reciter_photo"))

    def _draw_handles_only(self) -> None:
        self.delete("guide")
        self.delete("handle")
        self._draw_guides()
        self._draw_handles()

    # ── hit testing ───────────────────────────────────────────────────────────

    def _hit_element_tab(self, x: int, y: int) -> DragTarget | None:
        positions = self._element_handle_positions()
        HW, HH = self.HANDLE_W + 6, self.HANDLE_H // 2 + 4
        for key, _color, _label in ELEMENT_HANDLES:
            _cx, cy = positions[key]
            cy = max(HH, min(self.pre_h - HH, cy))
            if 0 <= x <= HW + 8 and abs(y - cy) <= HH:
                return key  # type: ignore[return-value]
        return None

    def _hit_reciter_photo(self, x: int, y: int) -> bool:
        if not self.show_reciter:
            return False
        x1, y1, x2, y2 = self._reciter_rect()
        pad = 10
        return x1 - pad <= x <= x2 + pad and y1 - pad <= y <= y2 + pad

    # ── event handlers ────────────────────────────────────────────────────────

    def _on_press(self, event) -> None:
        self.focus_set()
        tab = self._hit_element_tab(event.x, event.y)
        if tab:
            self._drag_target = tab
        elif self._hit_reciter_photo(event.x, event.y):
            self._drag_target = "reciter_photo"
        else:
            self._drag_target = "block"
        self._drag_start = (event.x, event.y)

    def _snap_element_x(self, off: list[int]) -> None:
        """Snap element X offset to centre-line if within threshold."""
        if abs(off[0]) <= _SNAP_THRESHOLD_PX:
            off[0] = 0

    def _on_drag(self, event) -> None:
        if not self._drag_start:
            return
        dx, dy = event.x - self._drag_start[0], event.y - self._drag_start[1]
        odx, ody = self._delta_to_out(dx, dy)
        t = self._drag_target

        if t == "block":
            self.block_x += odx
            self.block_y += ody
            self.clamp_block()
        elif t == "svg":
            self.svg_off[0] += odx;     self.svg_off[1] += ody
            self._snap_element_x(self.svg_off)
        elif t == "title":
            self.title_off[0] += odx;   self.title_off[1] += ody
            self._snap_element_x(self.title_off)
        elif t == "reciter":
            self.reciter_off[0] += odx; self.reciter_off[1] += ody
            self._snap_element_x(self.reciter_off)
        elif t == "badge":
            self.badge_off[0] += odx;   self.badge_off[1] += ody
            self._snap_element_x(self.badge_off)
        elif t == "reciter_photo":
            self.reciter_x = max(80, min(OUTPUT_W - 80, self.reciter_x + odx))
            self.reciter_y = max(80, min(OUTPUT_H - 80, self.reciter_y + ody))

        self._drag_start = (event.x, event.y)
        self._draw_handles_only()
        self._draw_drag_info()

    def _draw_drag_info(self) -> None:
        """Overlay showing which element is moving and its offset."""
        self.delete("draginfo")
        t = self._drag_target
        if not t or t == "reciter_photo":
            return
        if t == "block":
            msg = f"Block  x={self.block_x:+}  y={self.block_y:+}"
        else:
            off = {"svg": self.svg_off, "title": self.title_off,
                   "reciter": self.reciter_off, "badge": self.badge_off}[t]
            snap = "  ·  centered" if off[0] == 0 else ""
            msg = f"{t.upper()}  x={off[0]:+}  y={off[1]:+}{snap}"
        self.create_rectangle(self.pre_w - 5, self.pre_h - 22, self.pre_w - 5, self.pre_h - 5,
                              fill="#00000080", outline="", tags=("draginfo",))
        self.create_text(self.pre_w // 2, self.pre_h - 10, text=msg,
                         fill="#d4af37", font=("Segoe UI", 8), anchor="s", tags=("draginfo",))

    def _on_release(self, _event) -> None:
        self.delete("draginfo")
        if self._drag_target:
            self.on_layout_change()
        self._drag_target = None
        self._drag_start  = None

    def _on_double_click(self, event) -> None:
        tab = self._hit_element_tab(event.x, event.y)
        if tab == "svg":
            self.svg_off = [0, 0]
        elif tab == "title":
            self.title_off = [0, 0]
        elif tab == "reciter":
            self.reciter_off = [0, 0]
        elif tab == "badge":
            self.badge_off = [0, 0]
        elif self._hit_reciter_photo(event.x, event.y):
            self.reciter_x, self.reciter_y = 900, 420
        else:
            self.block_x, self.block_y = 0, 0
            self.clamp_block()
        self._draw_handles_only()
        self.on_layout_change()

    def _on_key(self, event) -> None:
        step = 10 if event.state & 0x0001 else 4
        moved = False
        if event.keysym == "Left":
            self.block_x -= step; moved = True
        elif event.keysym == "Right":
            self.block_x += step; moved = True
        elif event.keysym == "Up":
            self.block_y -= step; moved = True
        elif event.keysym == "Down":
            self.block_y += step; moved = True
        if moved:
            self.clamp_block()
            self._draw_handles_only()
            self.on_layout_change()
