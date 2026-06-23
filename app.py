"""GUI for generating Quranic recitation thumbnails."""

from __future__ import annotations

import sys
import tkinter as tk
import shutil
from dataclasses import replace
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageTk

import reciter_store
import settings_store
import win_chrome
from app_paths import base_dir, ensure_initialized
from preview_canvas import InteractivePreviewCanvas
from surahs import SURAHS, get_surah, surah_label
from thumbnail_generator import (
    ThumbnailConfig,
    default_nature_background,
    generate_thumbnail,
    list_banners,
    list_nature_backgrounds,
    save_thumbnail,
)
from name_containers import list_name_containers
from ui_theme import (
    ACCENT,
    BG_DARK,
    BG_INPUT,
    BG_PANEL,
    CLOSE_HOVER,
    CTRL_HOVER,
    FG_MUTED,
    FG_PRIMARY,
    FONT_HEADING,
    TITLEBAR_BG,
    TITLEBAR_FG,
    apply_theme,
    style_listbox,
)

APP_TITLE = "Quran Thumbnail Generator"
PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 360


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


class ColorPickerRow(ttk.Frame):
    def __init__(self, master, label: str, initial: str, on_change) -> None:
        super().__init__(master, style="Panel.TFrame")
        self.on_change = on_change
        self.color_var = tk.StringVar(value=initial)
        ttk.Label(self, text=label, style="Panel.TLabel", width=16).pack(side="left")
        self.swatch = tk.Label(self, width=3, relief="flat", bd=0, cursor="hand2")
        self.swatch.pack(side="left", padx=(0, 8))
        self.swatch.bind("<Button-1>", lambda _e: self.pick())
        self.value_label = ttk.Label(self, textvariable=self.color_var, style="Panel.TLabel")
        self.value_label.pack(side="left")
        self._refresh_swatch()

    def _refresh_swatch(self) -> None:
        self.swatch.configure(bg=self.color_var.get())

    def pick(self) -> None:
        rgb = _hex_to_rgb(self.color_var.get())
        result = colorchooser.askcolor(color=rgb, title="Choose color")
        if result[1]:
            self.color_var.set(result[1])
            self._refresh_swatch()
            self.on_change()

    def rgb(self) -> tuple[int, int, int]:
        return _hex_to_rgb(self.color_var.get())


class BatchExportDialog(tk.Toplevel):
    def __init__(self, master: "ThumbnailApp", build_config, export_scale: int = 2) -> None:
        super().__init__(master)
        self.title("Batch Export")
        self.geometry("440x300")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.build_config = build_config
        self.export_scale = export_scale

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="From surah").grid(row=0, column=0, sticky="w")
        self.from_var = tk.StringVar(value="1")
        ttk.Spinbox(frame, from_=1, to=114, textvariable=self.from_var, width=8).grid(row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Label(frame, text="To surah").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.to_var = tk.StringVar(value="114")
        ttk.Spinbox(frame, from_=1, to=114, textvariable=self.to_var, width=8).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(frame, text="Output folder").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.folder_var = tk.StringVar()
        folder_row = ttk.Frame(frame)
        folder_row.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Entry(folder_row, textvariable=self.folder_var, width=28).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text="Browse...", command=self._browse).pack(side="left", padx=(8, 0))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.progress_label = ttk.Label(frame, text="", style="Muted.TLabel")
        self.progress_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.export_btn = ttk.Button(buttons, text="Export All", style="Accent.TButton", command=self._export)
        self.export_btn.pack(side="left")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        self._cancelled = False

    def _browse(self) -> None:
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.folder_var.set(folder)

    def _export(self) -> None:
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning(APP_TITLE, "Choose an output folder.")
            return
        try:
            start = int(self.from_var.get())
            end = int(self.to_var.get())
        except ValueError:
            messagebox.showwarning(APP_TITLE, "Enter valid surah numbers.")
            return
        if start > end:
            start, end = end, start

        output_dir = Path(folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        saved = 0
        base_config = self.build_config(warn=False)

        numbers = [n for n in range(start, end + 1) if get_surah(n)]
        total = len(numbers)
        self.export_btn.configure(state="disabled")

        for idx, number in enumerate(numbers, 1):
            surah = get_surah(number)
            config = replace(
                base_config,
                arabic_surah=surah.arabic,
                english_surah=surah.english,
                surah_number=surah.number,
            )
            filename = f"{number:03d}_{surah.english.replace('Surah ', '').replace(' ', '_')}.png"
            try:
                save_thumbnail(config, output_dir / filename, self.export_scale)
                saved += 1
            except Exception:
                pass
            self.progress_var.set(idx / total * 100)
            self.progress_label.configure(text=f"{idx}/{total} — {surah.english}")
            self.update_idletasks()

        messagebox.showinfo(APP_TITLE, f"Exported {saved} thumbnails to:\n{output_dir}")
        self.destroy()


class ReciterManagerDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, on_change) -> None:
        super().__init__(master)
        self.title("Manage Reciters & Photo Groups")
        self.geometry("760x480")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.configure(bg=BG_DARK)
        self.on_change = on_change
        self.selected_reciter_id: str | None = None
        self.selected_photo_id: str | None = None

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        reciter_frame = ttk.LabelFrame(frame, text="Reciters", padding=8)
        reciter_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.reciter_list = tk.Listbox(reciter_frame, height=14)
        style_listbox(self.reciter_list)
        self.reciter_list.pack(fill="both", expand=True)
        self.reciter_list.bind("<<ListboxSelect>>", self._on_reciter_select)

        photo_frame = ttk.LabelFrame(frame, text="Photos for Selected Reciter", padding=8)
        photo_frame.grid(row=0, column=1, sticky="nsew")
        self.photo_list = tk.Listbox(photo_frame, height=14)
        style_listbox(self.photo_list)
        self.photo_list.pack(fill="both", expand=True)
        self.photo_list.bind("<<ListboxSelect>>", self._on_photo_select)

        form = ttk.Frame(frame)
        form.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Reciter name").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(form, text="Photo label").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.photo_label_var = tk.StringVar(value="Portrait")
        ttk.Entry(form, textvariable=self.photo_label_var, width=40).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(form, text="Image file").grid(row=2, column=0, sticky="w", pady=(8, 0))
        file_row = ttk.Frame(form)
        file_row.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        self.file_var = tk.StringVar(value="No image selected")
        ttk.Label(file_row, textvariable=self.file_var).pack(side="left", fill="x", expand=True)
        ttk.Button(file_row, text="Browse...", command=self._browse_photo).pack(side="right")

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(buttons, text="Add Reciter", command=self._add_reciter).pack(side="left")
        ttk.Button(buttons, text="Save Name", command=self._save_reciter_name).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Add Photo", command=self._add_photo).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Remove Photo", command=self._remove_photo).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Delete Reciter", command=self._delete_reciter).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Done", command=self.destroy).pack(side="right")

        self._pending_photo: Path | None = None
        self.reciters: list[reciter_store.Reciter] = []
        self.refresh()

    def refresh(self) -> None:
        self.reciter_list.delete(0, tk.END)
        self.photo_list.delete(0, tk.END)
        self.reciters = reciter_store.load_reciters()
        for reciter in self.reciters:
            count = len(reciter.photos)
            self.reciter_list.insert(tk.END, f"{reciter.name} ({count} photo{'s' if count != 1 else ''})")

    def _selected_reciter(self) -> reciter_store.Reciter | None:
        selection = self.reciter_list.curselection()
        if not selection:
            return None
        return self.reciters[selection[0]]

    def _on_reciter_select(self, _event=None) -> None:
        reciter = self._selected_reciter()
        self.photo_list.delete(0, tk.END)
        self.selected_photo_id = None
        if not reciter:
            return
        self.selected_reciter_id = reciter.id
        self.name_var.set(reciter.name)
        for photo in reciter.photos:
            exists = Path(photo.image_path).exists()
            suffix = "" if exists else " [missing]"
            self.photo_list.insert(tk.END, f"{photo.label}{suffix}")

    def _on_photo_select(self, _event=None) -> None:
        reciter = self._selected_reciter()
        selection = self.photo_list.curselection()
        if not reciter or not selection:
            return
        photo = reciter.photos[selection[0]]
        self.selected_photo_id = photo.id
        self.photo_label_var.set(photo.label)
        if Path(photo.image_path).exists():
            self.file_var.set(Path(photo.image_path).name)

    def _browse_photo(self) -> None:
        path = filedialog.askopenfilename(
            title="Select reciter photo",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All files", "*.*")],
        )
        if path:
            self._pending_photo = Path(path)
            self.file_var.set(Path(path).name)

    def _add_reciter(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning(APP_TITLE, "Enter a reciter name.")
            return
        reciter_store.add_reciter(name)
        self.name_var.set("")
        self.refresh()
        self.on_change()

    def _save_reciter_name(self) -> None:
        if not self.selected_reciter_id:
            messagebox.showwarning(APP_TITLE, "Select a reciter first.")
            return
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning(APP_TITLE, "Enter a reciter name.")
            return
        reciter_store.update_reciter_name(self.selected_reciter_id, name)
        self.refresh()
        self.on_change()

    def _add_photo(self) -> None:
        if not self.selected_reciter_id:
            messagebox.showwarning(APP_TITLE, "Select a reciter to attach photos to.")
            return
        if not self._pending_photo:
            messagebox.showwarning(APP_TITLE, "Choose an image file first.")
            return
        label = self.photo_label_var.get().strip() or "Portrait"
        reciter_store.add_reciter_photo(self.selected_reciter_id, label, self._pending_photo)
        self._pending_photo = None
        self.file_var.set("No image selected")
        self.refresh()
        self._on_reciter_select()
        self.on_change()

    def _remove_photo(self) -> None:
        if not self.selected_reciter_id or not self.selected_photo_id:
            messagebox.showwarning(APP_TITLE, "Select a photo to remove.")
            return
        if not messagebox.askyesno(APP_TITLE, "Remove this photo from the reciter group?"):
            return
        reciter_store.delete_reciter_photo(self.selected_reciter_id, self.selected_photo_id)
        self.selected_photo_id = None
        self.refresh()
        self._on_reciter_select()
        self.on_change()

    def _delete_reciter(self) -> None:
        if not self.selected_reciter_id:
            messagebox.showwarning(APP_TITLE, "Select a reciter to delete.")
            return
        if not messagebox.askyesno(APP_TITLE, "Delete this reciter and all of their photos?"):
            return
        reciter_store.delete_reciter(self.selected_reciter_id)
        self.selected_reciter_id = None
        self.selected_photo_id = None
        self.name_var.set("")
        self.file_var.set("No image selected")
        self.refresh()
        self.on_change()


class ThumbnailApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x820+80+40")
        self.minsize(1120, 720)
        apply_theme(self)
        self._set_window_icon()

        self.reciters = reciter_store.load_reciters()
        self._saved_settings = settings_store.load_settings()
        self._syncing_surah = False
        self._preview_job: str | None = None

        # Custom title bar — strip native caption via Win32 (keeps taskbar icon).
        # Set "native_titlebar": true in data/settings.json to force native chrome.
        self._custom_chrome = not self._saved_settings.get("native_titlebar", False)
        self._maximized = False
        self._normal_geometry = "1280x820+80+40"

        default = get_surah(5)
        self.surah_choice_var = tk.StringVar(value=surah_label(default) if default else "")
        self.arabic_var = tk.StringVar(value=default.arabic if default else "")
        self.english_var = tk.StringVar(value=default.english if default else "")
        self.number_var = tk.StringVar(value="5")
        self.banner_var = tk.StringVar(value="None")
        self.text_glow_var = tk.BooleanVar(value=True)
        self.show_reciter_overlay_var = tk.BooleanVar(value=False)
        self.custom_banner_path: Path | None = None
        self.name_container_var = tk.StringVar(value="None")
        self.name_container_width_var = tk.DoubleVar(value=1.0)
        self.name_container_height_var = tk.DoubleVar(value=1.0)
        self.name_container_opacity_var = tk.DoubleVar(value=0.88)
        self.custom_name_container_path: Path | None = None

        self.reciter_collection_var = tk.StringVar()
        self.reciter_display_var = tk.StringVar()
        self.reciter_photo_var = tk.StringVar()
        self.background_mode = tk.StringVar(value="nature")
        self._bg_count_var = tk.StringVar(value="")
        self.export_scale_var = tk.IntVar(value=2)   # 1=HD, 2=FHD, 3=4K
        self.banner_size_var = tk.DoubleVar(value=0.40)
        self.nature_background_var = tk.StringVar()
        self.custom_background_var = tk.StringVar(value="")
        self.overlay_var = tk.DoubleVar(value=0.50)
        self.text_offset_x_var = tk.IntVar(value=0)
        self.text_offset_y_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Ready")

        # Typography sizes (defaults tuned to the cinematic reference look)
        self.svg_height_var = tk.IntVar(value=500)
        self.title_size_var = tk.IntVar(value=52)
        self.reciter_size_var = tk.IntVar(value=44)
        self.badge_size_var = tk.IntVar(value=28)

        self._syncing_offsets = False

        self._build_ui()
        self.text_offset_x_var.trace_add("write", lambda *_: self._apply_offset_spinboxes())
        self.text_offset_y_var.trace_add("write", lambda *_: self._apply_offset_spinboxes())
        self._refresh_reciter_options()
        self._refresh_nature_backgrounds()
        self._refresh_banners()
        self._refresh_name_containers()
        self._restore_settings()
        self._bind_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._ui_ready = True
        self._finalize_custom_shell()
        self.after(100, self.update_preview)

    def _set_window_icon(self) -> None:
        assets = base_dir() / "assets"
        ico_path = assets / "icon.ico"
        png_path = assets / "icon.png"
        if ico_path.exists():
            try:
                self.iconbitmap(default=str(ico_path))
            except tk.TclError:
                pass
        if png_path.exists():
            try:
                self._icon_image = tk.PhotoImage(file=str(png_path))
                self.iconphoto(True, self._icon_image)
            except tk.TclError:
                pass

    def _finalize_custom_shell(self) -> None:
        """Apply borderless Win32 shell once at startup."""
        if not self._custom_chrome:
            return
        self.update_idletasks()
        win_chrome.apply_borderless_shell(self)
        win_chrome.register_taskbar_hooks(self)

    # ── custom title bar ─────────────────────────────────────────────────────

    def _build_titlebar(self) -> None:
        bar = tk.Frame(self, bg=TITLEBAR_BG, height=40)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)
        self._titlebar = bar

        # App icon (small)
        try:
            if getattr(self, "_icon_image", None) is not None:
                factor = max(1, self._icon_image.width() // 22)
                self._tb_icon = self._icon_image.subsample(factor, factor)
                tk.Label(bar, image=self._tb_icon, bg=TITLEBAR_BG).pack(side="left", padx=(12, 8))
        except tk.TclError:
            pass

        title = tk.Label(bar, text=APP_TITLE, bg=TITLEBAR_BG, fg=TITLEBAR_FG,
                         font=(FONT_HEADING, 10))
        title.pack(side="left", pady=8)

        # Window control buttons (right side, inset when maximized on Win11)
        self._tb_controls = tk.Frame(bar, bg=TITLEBAR_BG)
        self._tb_controls.pack(side="right", fill="y")
        self._tb_close = self._tb_button(self._tb_controls, "\u2715", self._on_close, hover=CLOSE_HOVER, hover_fg="#ffffff")
        self._tb_max = self._tb_button(self._tb_controls, "\u25A1", self._toggle_maximize, hover=CTRL_HOVER)
        self._tb_min = self._tb_button(self._tb_controls, "\u2014", self._minimize, hover=CTRL_HOVER)
        self._sync_titlebar_insets()

        # Dragging
        for widget in (bar, title):
            widget.bind("<ButtonPress-1>", self._tb_press)
            widget.bind("<B1-Motion>", self._tb_drag)
            widget.bind("<Double-Button-1>", lambda _e: self._toggle_maximize())

    def _tb_button(self, parent, glyph, command, hover, hover_fg=None):
        btn = tk.Label(parent, text=glyph, bg=TITLEBAR_BG, fg=FG_MUTED,
                       font=("Segoe UI", 11), width=4, height=1, cursor="hand2")
        btn.pack(side="right", fill="y")
        normal_fg = FG_MUTED

        def on_enter(_e):
            btn.configure(bg=hover, fg=hover_fg or FG_PRIMARY)

        def on_leave(_e):
            btn.configure(bg=TITLEBAR_BG, fg=normal_fg)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<ButtonRelease-1>", lambda _e: command())
        return btn

    def _sync_titlebar_insets(self) -> None:
        if not getattr(self, "_tb_controls", None):
            return
        inset = win_chrome.titlebar_control_inset(self._maximized)
        self._tb_controls.pack_configure(padx=(0, inset))
        if getattr(self, "_tb_max", None):
            self._tb_max.configure(text="\u2750" if self._maximized else "\u25A1")

    def _after_window_state_change(self) -> None:
        self.update_idletasks()
        frame = getattr(self, "_preview_frame", None)
        if frame is not None and frame.winfo_width() > 80:
            class _Ev:
                width = frame.winfo_width()
                height = frame.winfo_height()
            self._on_preview_frame_resize(_Ev())

    def _tb_press(self, event) -> None:
        if self._maximized:
            return
        self._drag_origin = (event.x_root, event.y_root)
        self._win_origin = (self.winfo_x(), self.winfo_y())

    def _tb_drag(self, event) -> None:
        if self._maximized or not hasattr(self, "_drag_origin"):
            return
        dx = event.x_root - self._drag_origin[0]
        dy = event.y_root - self._drag_origin[1]
        self.geometry(f"+{self._win_origin[0] + dx}+{self._win_origin[1] + dy}")

    def _minimize(self) -> None:
        win_chrome.minimize_window(self)

    def _toggle_maximize(self) -> None:
        if not self._custom_chrome:
            return
        if self._maximized:
            self.geometry(self._normal_geometry)
            self._maximized = False
        else:
            self._normal_geometry = self.geometry()
            geo = win_chrome.maximize_geometry(self)
            if geo:
                self.geometry(geo)
            else:
                self.geometry(
                    f"{self.winfo_screenwidth()}x{self.winfo_screenheight() - 48}+0+0"
                )
            self._maximized = True
        self._sync_titlebar_insets()
        self.after(50, self._after_window_state_change)

    def _bind_shortcuts(self) -> None:
        self.bind_all("<Control-s>", lambda _e: self.export_thumbnail())
        self.bind_all("<Control-S>", lambda _e: self.export_thumbnail())
        self.bind_all("<Control-r>", lambda _e: self.update_preview())
        self.bind_all("<Control-e>", lambda _e: self.batch_export())
        self.bind_all("<F5>", lambda _e: self.update_preview())

    # ── settings persistence ────────────────────────────────────────────────

    def _settings_snapshot(self) -> dict:
        return {
            "banner": self.banner_var.get(),
            "name_container": self.name_container_var.get(),
            "name_container_width_scale": float(self.name_container_width_var.get()),
            "name_container_height_scale": float(self.name_container_height_var.get()),
            "name_container_opacity": float(self.name_container_opacity_var.get()),
            "text_glow": bool(self.text_glow_var.get()),
            "background_mode": self.background_mode.get(),
            "nature_background": self.nature_background_var.get(),
            "bg_category": getattr(self, "bg_category_var", tk.StringVar(value="All")).get(),
            "export_scale": int(self.export_scale_var.get()),
            "banner_size": float(self.banner_size_var.get()),
            "overlay": float(self.overlay_var.get()),
            "svg_height": int(self.svg_height_var.get()),
            "title_size": int(self.title_size_var.get()),
            "reciter_size": int(self.reciter_size_var.get()),
            "badge_size": int(self.badge_size_var.get()),
            "arabic_color": self.arabic_color.color_var.get(),
            "english_color": self.english_color.color_var.get(),
            "reciter_color": self.reciter_color.color_var.get(),
            "badge_text_color": self.badge_text_color.color_var.get(),
            "badge_accent_color": self.badge_accent_color.color_var.get(),
            "reciter_collection": self.reciter_collection_var.get(),
            "native_titlebar": bool(self._saved_settings.get("native_titlebar", False)),
        }

    def _restore_settings(self) -> None:
        s = self._saved_settings
        if not s:
            return
        try:
            self.text_glow_var.set(bool(s.get("text_glow", True)))
            self.export_scale_var.set(int(s.get("export_scale", 2)))
            self.banner_size_var.set(float(s.get("banner_size", 0.40)))
            if hasattr(self, "_banner_size_int"):
                self._banner_size_int.set(int(self.banner_size_var.get() * 100))
            self.overlay_var.set(float(s.get("overlay", self.overlay_var.get())))
            self.svg_height_var.set(int(s.get("svg_height", self.svg_height_var.get())))
            self.title_size_var.set(int(s.get("title_size", self.title_size_var.get())))
            self.reciter_size_var.set(int(s.get("reciter_size", self.reciter_size_var.get())))
            self.badge_size_var.set(int(s.get("badge_size", self.badge_size_var.get())))
            for picker, key in [
                (self.arabic_color, "arabic_color"),
                (self.english_color, "english_color"),
                (self.reciter_color, "reciter_color"),
                (self.badge_text_color, "badge_text_color"),
                (self.badge_accent_color, "badge_accent_color"),
            ]:
                val = s.get(key)
                if val:
                    picker.color_var.set(val)
                    picker._refresh_swatch()
            banner = s.get("banner")
            if banner and banner in [lbl for _, lbl, _ in getattr(self, "_banner_data", [])]:
                self.banner_var.set(banner)
                self._on_banner_selected()
                self._build_banner_grid()
            container = s.get("name_container")
            if container and container in [lbl for _, lbl, _ in getattr(self, "_container_data", [])]:
                self.name_container_var.set(container)
                self._on_name_container_selected()
                self._build_container_grid()
            width = s.get("name_container_width_scale")
            height = s.get("name_container_height_scale")
            opacity = s.get("name_container_opacity")
            legacy = s.get("name_container_scale")
            if width is not None:
                self.name_container_width_var.set(float(width))
            elif legacy is not None:
                self.name_container_width_var.set(float(legacy))
            if height is not None:
                self.name_container_height_var.set(float(height))
            elif legacy is not None:
                self.name_container_height_var.set(float(legacy))
            if opacity is not None:
                self.name_container_opacity_var.set(float(opacity))
            if hasattr(self, "_container_height_pct") and height is not None:
                self._container_height_pct.set(int(float(height) * 100))
            elif hasattr(self, "_container_height_pct") and legacy is not None:
                self._container_height_pct.set(int(float(legacy) * 100))
            if hasattr(self, "_container_width_pct") and width is not None:
                self._container_width_pct.set(int(float(width) * 100))
            elif hasattr(self, "_container_width_pct") and legacy is not None:
                self._container_width_pct.set(int(float(legacy) * 100))
            if hasattr(self, "_container_opacity_pct") and opacity is not None:
                self._container_opacity_pct.set(int(float(opacity) * 100))
            mode = s.get("background_mode")
            if mode in {"nature", "reciter", "custom"}:
                self.background_mode.set(mode)
            cat = s.get("bg_category")
            if cat and hasattr(self, "bg_category_var"):
                self._filter_backgrounds(cat)
            nature = s.get("nature_background")
            if nature and nature in self.nature_combo["values"]:
                self.nature_background_var.set(nature)
                self._update_bg_preview()
            collection = s.get("reciter_collection")
            if collection and collection in self.reciter_combo["values"]:
                self.reciter_collection_var.set(collection)
                self._on_reciter_collection_changed()
        except (tk.TclError, ValueError, KeyError):
            pass

    def _on_close(self) -> None:
        try:
            settings_store.save_settings(self._settings_snapshot())
        except Exception:
            pass
        self.destroy()

    def _maybe_download_first_run_assets(self) -> None:
        """On installed builds, fetch missing fonts/scenery in the background."""
        from app_paths import is_frozen
        if not is_frozen():
            return
        from first_run_assets import needs_any_download, start_background_download
        if not needs_any_download():
            return
        self.status_var.set("First launch — downloading fonts and scenery library…")

        def on_progress(msg: str) -> None:
            self.after(0, lambda: self.status_var.set(msg))

        def on_done(ok: int, fail: int, err: str = "") -> None:
            def finish():
                if err:
                    self.status_var.set(f"Asset download error: {err}")
                elif fail:
                    self.status_var.set(
                        f"Assets ready ({ok} downloaded, {fail} skipped — check connection)."
                    )
                else:
                    self.status_var.set("Assets ready.")
                self._refresh_nature_backgrounds()
                self.update_preview()

            self.after(0, finish)

        start_background_download(on_progress, on_done)

    def _build_ui(self) -> None:
        if self._custom_chrome:
            self._build_titlebar()

        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        left_shell = ttk.Frame(outer, style="Panel.TFrame", padding=0)
        left_shell.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        left_shell.configure(width=400)

        header = ttk.Frame(left_shell, style="Panel.TFrame", padding=(12, 12, 12, 4))
        header.pack(fill="x")
        ttk.Label(header, text="Thumbnail Settings", style="Panel.Heading.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Use tabs below — drag preview handles or arrow keys to move text.",
            style="Panel.Muted.TLabel",
            wraplength=360,
        ).pack(anchor="w", pady=(4, 0))

        notebook = ttk.Notebook(left_shell)
        notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._build_surah_tab(self._add_scroll_tab(notebook, "Surah"))
        self._build_style_tab(self._add_scroll_tab(notebook, "Style"))
        self._build_reciter_tab(self._add_scroll_tab(notebook, "Reciter"))
        self._build_background_tab(self._add_scroll_tab(notebook, "Background"))
        self._build_layout_tab(self._add_scroll_tab(notebook, "Banners"))
        self._build_export_tab(self._add_scroll_tab(notebook, "Export"))

        preview_frame = ttk.LabelFrame(
            outer,
            text="Preview — colored tabs on left = per-layer handles · drag canvas = move block · double-click = reset · arrows = nudge",
            style="Dark.TLabelframe",
            padding=8,
        )
        preview_frame.grid(row=0, column=1, sticky="nsew")
        preview_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        self._preview_frame = preview_frame
        self.preview_canvas = InteractivePreviewCanvas(
            preview_frame,
            on_layout_change=self._on_canvas_layout_change,
            on_container_resize=self._on_container_resize,
        )
        self.preview_canvas.grid(row=0, column=0)
        preview_frame.bind("<Configure>", self._on_preview_frame_resize)

    def _add_scroll_tab(self, notebook, title: str):
        """Add a notebook tab whose content scrolls, with an auto-hiding scrollbar."""
        container = ttk.Frame(notebook, style="Panel.TFrame")
        canvas = tk.Canvas(container, bg=BG_PANEL, highlightthickness=0, borderwidth=0)
        vbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style="Panel.TFrame", padding=10)
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

        notebook.add(container, text=title)
        return inner

    def _on_preview_frame_resize(self, event) -> None:
        avail_w = event.width - 24
        avail_h = event.height - 44   # leave room for the frame title + padding
        if avail_w < 80 or avail_h < 80:
            return
        w = min(avail_w, int(avail_h * 16 / 9))
        h = int(w * 9 / 16)
        if w == self.preview_canvas.pre_w and h == self.preview_canvas.pre_h:
            return
        self.preview_canvas.set_preview_size(w, h)
        # Re-render at the scale appropriate for the new size (keeps it crisp)
        if getattr(self, "_ui_ready", False):
            self.schedule_preview(180)

    def _build_surah_tab(self, parent) -> None:
        self.surah_combo = ttk.Combobox(
            parent,
            textvariable=self.surah_choice_var,
            values=[surah_label(s) for s in SURAHS],
            state="readonly",
            width=36,
        )
        self.surah_combo.pack(anchor="w", pady=(0, 8))
        self.surah_combo.bind("<<ComboboxSelected>>", self._on_surah_selected)

        self._field(parent, "Arabic name", self.arabic_var)
        self._field(parent, "English title (transliteration)", self.english_var)
        self._field(parent, "Surah number", self.number_var, width=10, handler=self._on_number_typed)

        ttk.Label(
            parent,
            text="Stylized Arabic loads from Amrayn SVG. English title, reciter name, and surah badge render below it.",
            style="Panel.Muted.TLabel",
            wraplength=350,
        ).pack(anchor="w", pady=(10, 0))

    def _build_style_tab(self, parent) -> None:
        # ── Colors ──────────────────────────────────────────────────────────
        ttk.Label(parent, text="Colors", style="Panel.Heading.TLabel").pack(anchor="w", pady=(0, 6))
        self.arabic_color = ColorPickerRow(parent, "Arabic / SVG", "#ffffff", self.update_preview)
        self.arabic_color.pack(anchor="w", fill="x", pady=(0, 4))
        self.english_color = ColorPickerRow(parent, "English title", "#ffffff", self.update_preview)
        self.english_color.pack(anchor="w", fill="x", pady=(0, 4))
        self.reciter_color = ColorPickerRow(parent, "Reciter name", "#ffffff", self.update_preview)
        self.reciter_color.pack(anchor="w", fill="x", pady=(0, 4))
        self.badge_text_color = ColorPickerRow(parent, "Badge number", "#ffffff", self.update_preview)
        self.badge_text_color.pack(anchor="w", fill="x", pady=(0, 4))
        self.badge_accent_color = ColorPickerRow(parent, "Badge accent", "#d4af37", self.update_preview)
        self.badge_accent_color.pack(anchor="w", fill="x", pady=(0, 4))
        ttk.Checkbutton(parent, text="Soft glow", variable=self.text_glow_var, command=self.update_preview).pack(anchor="w", pady=(4, 0))

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(12, 8))

        # ── Typography sizes ─────────────────────────────────────────────────
        ttk.Label(parent, text="Typography sizes", style="Panel.Heading.TLabel").pack(anchor="w", pady=(0, 8))
        self._size_row(parent, "Arabic SVG height", self.svg_height_var, 80, 500, 5)
        self._size_row(parent, "English title (pt)", self.title_size_var, 20, 90, 2)
        self._size_row(parent, "Reciter name (pt)", self.reciter_size_var, 16, 70, 2)
        self._size_row(parent, "Badge number (pt)", self.badge_size_var, 14, 52, 2)

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(12, 8))
        ttk.Label(parent, text="Surah name container", style="Panel.Heading.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(
            parent,
            text="Ornate frame around the Arabic surah name only. English title, reciter, and badge stay below.",
            style="Panel.Muted.TLabel",
            wraplength=360,
        ).pack(anchor="w", pady=(0, 6))

        self._container_grid_frame = ttk.Frame(parent, style="Panel.TFrame")
        self._container_grid_frame.pack(fill="x")
        self._container_thumb_refs: list[ImageTk.PhotoImage] = []

        container_scale_row = ttk.Frame(parent, style="Panel.TFrame")
        container_scale_row.pack(fill="x", pady=(6, 0))
        ttk.Label(container_scale_row, text="Container opacity", style="Panel.TLabel", width=20).pack(side="left")
        self._container_opacity_pct = tk.IntVar(value=88)

        def _container_opacity_update(*_):
            self.name_container_opacity_var.set(self._container_opacity_pct.get() / 100)
            self.schedule_preview()

        self._container_opacity_pct.trace_add("write", _container_opacity_update)
        ttk.Scale(
            container_scale_row, from_=30, to=100, variable=self._container_opacity_pct,
            orient="horizontal",
            command=lambda _v: self.schedule_preview(),
        ).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Label(container_scale_row, textvariable=self._container_opacity_pct, style="Panel.TLabel", width=4).pack(side="right")

        container_height_row = ttk.Frame(parent, style="Panel.TFrame")
        container_height_row.pack(fill="x", pady=(6, 0))
        ttk.Label(container_height_row, text="Container height", style="Panel.TLabel", width=20).pack(side="left")
        self._container_height_pct = tk.IntVar(value=100)

        def _container_height_update(*_):
            self.name_container_height_var.set(self._container_height_pct.get() / 100)
            self.schedule_preview()

        self._container_height_pct.trace_add("write", _container_height_update)
        ttk.Scale(
            container_height_row, from_=70, to=160, variable=self._container_height_pct,
            orient="horizontal",
            command=lambda _v: self.schedule_preview(),
        ).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Label(container_height_row, textvariable=self._container_height_pct, style="Panel.TLabel", width=4).pack(side="right")

        container_width_row = ttk.Frame(parent, style="Panel.TFrame")
        container_width_row.pack(fill="x", pady=(6, 0))
        ttk.Label(container_width_row, text="Container width", style="Panel.TLabel", width=20).pack(side="left")
        self._container_width_pct = tk.IntVar(value=100)

        def _container_width_update(*_):
            self.name_container_width_var.set(self._container_width_pct.get() / 100)
            self.schedule_preview()

        self._container_width_pct.trace_add("write", _container_width_update)
        ttk.Scale(
            container_width_row, from_=70, to=160, variable=self._container_width_pct,
            orient="horizontal",
            command=lambda _v: self.schedule_preview(),
        ).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Label(container_width_row, textvariable=self._container_width_pct, style="Panel.TLabel", width=4).pack(side="right")

        ttk.Label(
            parent,
            text="Hover the frame in preview: ↔ width, ↕ height, ⧉ uniform padding. Arabic SVG size is separate (Typography tab).",
            style="Panel.Muted.TLabel",
            wraplength=360,
        ).pack(anchor="w", pady=(6, 0))

        ttk.Button(parent, text="Upload custom container...", command=self._upload_custom_container).pack(
            anchor="w", pady=(8, 0)
        )

    def _banner_size_int_var(self) -> tk.IntVar:
        """Return an IntVar (percent 10-60) that stays in sync with banner_size_var (0.10-0.60)."""
        if hasattr(self, "_banner_size_int"):
            return self._banner_size_int
        self._banner_size_int = tk.IntVar(value=int(self.banner_size_var.get() * 100))

        def _to_float(*_):
            self.banner_size_var.set(self._banner_size_int.get() / 100)
            self.schedule_preview()

        self._banner_size_int.trace_add("write", _to_float)
        return self._banner_size_int

    def _size_row(self, parent, label: str, var: tk.IntVar, lo: int, hi: int, step: int) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", pady=(0, 6))
        ttk.Label(row, text=label, style="Panel.TLabel", width=20).pack(side="left")
        val_lbl = ttk.Label(row, textvariable=var, style="Panel.TLabel", width=4)
        val_lbl.pack(side="right")
        ttk.Scale(
            row, from_=lo, to=hi, variable=var, orient="horizontal",
            command=lambda _v: [var.set(round(var.get() / step) * step), self.schedule_preview()],
        ).pack(side="left", fill="x", expand=True, padx=(6, 6))

    def _build_reciter_tab(self, parent) -> None:
        ttk.Label(parent, text="Collection (photo group)", style="Panel.TLabel").pack(anchor="w")
        collection_row = ttk.Frame(parent, style="Panel.TFrame")
        collection_row.pack(fill="x", pady=(4, 8))
        self.reciter_combo = ttk.Combobox(collection_row, textvariable=self.reciter_collection_var, state="readonly", width=24)
        self.reciter_combo.pack(side="left", fill="x", expand=True)
        self.reciter_combo.bind("<<ComboboxSelected>>", self._on_reciter_collection_changed)
        ttk.Button(collection_row, text="Manage...", command=self._open_reciter_manager).pack(side="left", padx=(8, 0))

        self._field(parent, "Name on thumbnail", self.reciter_display_var)
        ttk.Label(parent, text="Reciter photo", style="Panel.TLabel").pack(anchor="w", pady=(8, 0))
        self.reciter_photo_combo = ttk.Combobox(parent, textvariable=self.reciter_photo_var, state="readonly", width=36)
        self.reciter_photo_combo.pack(anchor="w", pady=(4, 0))
        self.reciter_photo_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_preview())

        photo_actions = ttk.Frame(parent, style="Panel.TFrame")
        photo_actions.pack(anchor="w", fill="x", pady=(8, 0))
        ttk.Button(photo_actions, text="Add reciter photo...", command=self._quick_add_reciter_photo).pack(side="left")
        ttk.Checkbutton(
            parent,
            text="Show reciter photo on thumbnail (drag gold handle in preview)",
            variable=self.show_reciter_overlay_var,
            command=self.update_preview,
        ).pack(anchor="w", pady=(10, 0))

    def _build_background_tab(self, parent) -> None:
        ttk.Radiobutton(
            parent, text="Nature scenery", variable=self.background_mode, value="nature",
            command=self.update_preview,
        ).pack(anchor="w")

        # Category filter bar
        self.bg_category_var = tk.StringVar(value="All")
        cat_frame = ttk.Frame(parent, style="Panel.TFrame")
        cat_frame.pack(fill="x", padx=(16, 0), pady=(4, 2))
        for cat in ("All", "Forests", "Mountains", "Lakes", "Springs", "Other"):
            tk.Button(
                cat_frame, text=cat, font=("Segoe UI", 8),
                bg="#1e2129", fg="#aaaaaa", activebackground="#d4af37",
                relief="flat", bd=0, padx=6, pady=2, cursor="hand2",
                command=lambda c=cat: self._filter_backgrounds(c),
            ).pack(side="left", padx=(0, 4))

        nature_row = ttk.Frame(parent, style="Panel.TFrame")
        nature_row.pack(fill="x", padx=(16, 0), pady=(2, 0))
        self.nature_combo = ttk.Combobox(
            nature_row, textvariable=self.nature_background_var, state="readonly", width=26,
        )
        self.nature_combo.pack(side="left", fill="x", expand=True)
        self.nature_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_nature_selected())

        self._bg_preview_label = tk.Label(nature_row, bd=1, relief="flat", bg="#1a1d23")
        self._bg_preview_label.pack(side="left", padx=(8, 0))
        self._bg_thumb_ref: ImageTk.PhotoImage | None = None

        ttk.Label(
            parent,
            textvariable=self._bg_count_var if hasattr(self, "_bg_count_var") else tk.StringVar(value=""),
            style="Panel.Muted.TLabel",
        ).pack(anchor="w", padx=(16, 0))
        scenery_btns = ttk.Frame(parent, style="Panel.TFrame")
        scenery_btns.pack(anchor="w", fill="x", padx=(16, 0), pady=(4, 0))
        ttk.Button(scenery_btns, text="Random scenery", command=self._random_nature).pack(side="left")
        ttk.Button(scenery_btns, text="Fetch fresh (online)", command=self._fetch_fresh_scenery).pack(
            side="left", padx=(8, 0)
        )

        ttk.Radiobutton(
            parent, text="Selected reciter photo", variable=self.background_mode, value="reciter",
            command=self.update_preview,
        ).pack(anchor="w", pady=(10, 0))
        ttk.Radiobutton(
            parent, text="Custom image", variable=self.background_mode, value="custom",
            command=self.update_preview,
        ).pack(anchor="w", pady=(4, 0))
        custom_row = ttk.Frame(parent, style="Panel.TFrame")
        custom_row.pack(fill="x", padx=(16, 0), pady=(4, 0))
        ttk.Entry(custom_row, textvariable=self.custom_background_var, width=22).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(custom_row, text="Browse...", command=self._browse_custom_background).pack(
            side="left", padx=(8, 0)
        )

        overlay_row = ttk.Frame(parent, style="Panel.TFrame")
        overlay_row.pack(fill="x", pady=(14, 0))
        ttk.Label(overlay_row, text="Dark overlay", style="Panel.TLabel").pack(side="left")
        ttk.Scale(
            overlay_row, from_=0.25, to=0.75, variable=self.overlay_var, orient="horizontal",
            command=lambda _v: self.schedule_preview(),
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _build_layout_tab(self, parent) -> None:
        ttk.Label(parent, text="Islamic Corner Banners", style="Panel.Heading.TLabel").pack(anchor="w")
        ttk.Label(
            parent,
            text="Click a banner to apply it. Gold = selected. Upload your own PNG with the button below.",
            style="Panel.Muted.TLabel",
            wraplength=360,
        ).pack(anchor="w", pady=(2, 8))

        # Visual banner grid — populated in _refresh_banners
        self._banner_grid_frame = ttk.Frame(parent, style="Panel.TFrame")
        self._banner_grid_frame.pack(fill="x")
        self._banner_thumb_refs: list[ImageTk.PhotoImage] = []  # prevent GC

        ttk.Button(parent, text="Upload custom banner...", command=self._upload_custom_banner).pack(anchor="w", pady=(8, 0))

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(12, 8))
        ttk.Label(parent, text="Banner size", style="Panel.Heading.TLabel").pack(anchor="w", pady=(0, 4))
        self._size_row(parent, "Corner size (% of frame)", self._banner_size_int_var(),
                       10, 60, 2)

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(12, 8))
        ttk.Label(parent, text="Text position fine-tuning", style="Panel.Heading.TLabel").pack(anchor="w")

        offset_row = ttk.Frame(parent, style="Panel.TFrame")
        offset_row.pack(anchor="w", fill="x", pady=(6, 0))
        ttk.Label(offset_row, text="X offset", style="Panel.TLabel", width=8).pack(side="left")
        ttk.Spinbox(offset_row, from_=-520, to=520, textvariable=self.text_offset_x_var, width=7,
                    command=self._apply_offset_spinboxes).pack(side="left")
        ttk.Label(offset_row, text="Y offset", style="Panel.TLabel", width=8).pack(side="left", padx=(10, 0))
        ttk.Spinbox(offset_row, from_=-120, to=420, textvariable=self.text_offset_y_var, width=7,
                    command=self._apply_offset_spinboxes).pack(side="left")

        actions = ttk.Frame(parent, style="Panel.TFrame")
        actions.pack(anchor="w", fill="x", pady=(8, 0))
        ttk.Button(actions, text="Reset all", command=self._reset_layout).pack(side="left")
        ttk.Button(actions, text="Center block", command=self._center_text).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Reset layers", command=self._reset_element_layers).pack(side="left", padx=(8, 0))

    def _build_export_tab(self, parent) -> None:
        ttk.Button(parent, text="Update Preview", command=self.update_preview).pack(anchor="w")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(10, 8))
        ttk.Label(parent, text="Export quality", style="Panel.Heading.TLabel").pack(anchor="w")
        q_frame = ttk.Frame(parent, style="Panel.TFrame")
        q_frame.pack(anchor="w", pady=(6, 0))
        for label, val in [("HD  1280×720", 1), ("Full HD  2560×1440", 2), ("4K  3840×2160", 3)]:
            ttk.Radiobutton(q_frame, text=label, variable=self.export_scale_var, value=val).pack(anchor="w", pady=2)
        ttk.Label(
            parent,
            text="Full HD and 4K render at higher DPI — crisp text, sharp badge edges, smooth banner corners.",
            style="Panel.Muted.TLabel",
            wraplength=350,
        ).pack(anchor="w", pady=(4, 0))

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(10, 8))
        ttk.Button(parent, text="Export PNG", style="Accent.TButton", command=self.export_thumbnail).pack(anchor="w")
        ttk.Button(parent, text="Batch Export...", command=self.batch_export).pack(anchor="w", pady=(8, 0))
        ttk.Label(parent, textvariable=self.status_var, style="Panel.Muted.TLabel", wraplength=350).pack(anchor="w", pady=(16, 0))

    def _on_canvas_layout_change(self) -> None:
        self._sync_offset_vars_from_canvas()
        self.update_preview()

    def _sync_offset_vars_from_canvas(self) -> None:
        self._syncing_offsets = True
        self.text_offset_x_var.set(self.preview_canvas.block_x)
        self.text_offset_y_var.set(self.preview_canvas.block_y)
        self._syncing_offsets = False

    def _apply_offset_spinboxes(self) -> None:
        if self._syncing_offsets:
            return
        try:
            x = int(self.text_offset_x_var.get())
            y = int(self.text_offset_y_var.get())
        except tk.TclError:
            return
        if x == self.preview_canvas.block_x and y == self.preview_canvas.block_y:
            return
        self.preview_canvas.block_x = x
        self.preview_canvas.block_y = y
        self.preview_canvas.clamp_block()
        self._sync_offset_vars_from_canvas()
        self.update_preview()

    def _center_text(self) -> None:
        self.preview_canvas.block_x = 0
        self.preview_canvas.block_y = 0
        self.preview_canvas.clamp_block()
        self._sync_offset_vars_from_canvas()
        self.update_preview()

    def _reset_element_layers(self) -> None:
        pc = self.preview_canvas
        pc.svg_off     = [0, 0]
        pc.title_off   = [0, 0]
        pc.reciter_off = [0, 0]
        pc.badge_off   = [0, 0]
        self.update_preview()


    def _field(self, parent, label: str, variable: tk.StringVar, width: int = 34, handler=None) -> None:
        ttk.Label(parent, text=label, style="Panel.TLabel").pack(anchor="w", pady=(8, 0))
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        entry.pack(anchor="w")
        entry.bind("<KeyRelease>", handler or (lambda _e: self.update_preview()))

    def _refresh_banners(self) -> None:
        banners = list_banners()
        self._banner_data = banners  # (id, label, path)
        self._banner_lookup = {label: banner_id for banner_id, label, _path in banners}

        preferred = "None"
        if self.banner_var.get() not in [lbl for _, lbl, _ in banners]:
            self.banner_var.set(preferred)

        self._build_banner_grid()
        self._on_banner_selected()

    def _build_banner_grid(self) -> None:
        frame = self._banner_grid_frame
        for child in frame.winfo_children():
            child.destroy()
        self._banner_thumb_refs.clear()

        THUMB = 72
        cols = 4
        current_label = self.banner_var.get()

        for idx, (banner_id, label, path) in enumerate(self._banner_data):
            col = idx % cols
            row = idx // cols

            cell = ttk.Frame(frame, style="Panel.TFrame")
            cell.grid(row=row, column=col, padx=4, pady=4)

            # Generate thumbnail
            try:
                if path and path.exists():
                    img = Image.open(path).convert("RGBA")
                    # White bg for transparent PNGs
                    bg = Image.new("RGB", img.size, (30, 30, 35))
                    bg.paste(img, mask=img.split()[3])
                    bg.thumbnail((THUMB, THUMB), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(bg)
                else:
                    # "None" tile — dark grey square
                    none_img = Image.new("RGB", (THUMB, THUMB), (40, 40, 45))
                    from PIL import ImageDraw as _ID
                    _ID.Draw(none_img).line([(8, 8), (THUMB-8, THUMB-8)], fill=(80, 80, 80), width=2)
                    _ID.Draw(none_img).line([(THUMB-8, 8), (8, THUMB-8)], fill=(80, 80, 80), width=2)
                    photo = ImageTk.PhotoImage(none_img)
            except Exception:
                photo = None

            selected = (label == current_label)
            border_color = "#d4af37" if selected else "#333344"

            btn_frame = tk.Frame(cell, bg=border_color, bd=0)
            btn_frame.pack()

            if photo:
                self._banner_thumb_refs.append(photo)
                btn = tk.Label(btn_frame, image=photo, cursor="hand2", bd=0,
                               relief="flat", bg=border_color, padx=2, pady=2)
                btn.pack()
            else:
                btn = tk.Label(btn_frame, text="?", width=6, height=4, bg="#2a2a30",
                               fg="#888", cursor="hand2", bd=0)
                btn.pack()

            btn.bind("<Button-1>", lambda _e, lbl=label: self._select_banner(lbl))

            short = label if len(label) <= 14 else label[:13] + "…"
            lbl_widget = tk.Label(cell, text=short, font=("Segoe UI", 7),
                                  bg=frame.winfo_rgb("Panel.TFrame") if False else "#1a1d23",
                                  fg="#d4af37" if selected else "#888888", wraplength=THUMB, justify="center")
            lbl_widget.pack()

    def _select_banner(self, label: str) -> None:
        self.banner_var.set(label)
        self._on_banner_selected()
        self._build_banner_grid()

    def _on_banner_selected(self, _event=None) -> None:
        label = self.banner_var.get()
        lookup = getattr(self, "_banner_lookup", {})
        banner_id = lookup.get(label, "none")
        if banner_id.startswith("custom_"):
            path = base_dir() / "assets" / "banners" / f"{banner_id}.png"
            self.custom_banner_path = path if path.exists() else None
        else:
            self.custom_banner_path = None
        self.update_preview()

    def _upload_custom_banner(self) -> None:
        path = filedialog.askopenfilename(
            title="Upload corner banner PNG",
            filetypes=[("PNG images", "*.png"), ("All images", "*.jpg *.jpeg *.png *.webp"), ("All files", "*.*")],
        )
        if not path:
            return
        dest_dir = base_dir() / "assets" / "banners"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"custom_{Path(path).stem}.png"
        shutil.copy2(path, dest)
        self.custom_banner_path = dest
        self._refresh_banners()
        label = f"Custom: {Path(path).stem.replace('_', ' ').title()}"
        self.banner_var.set(label)
        self.update_preview()

    def _refresh_name_containers(self) -> None:
        containers = list_name_containers()
        self._container_data = containers
        self._container_lookup = {label: cid for cid, label, _path in containers}
        if self.name_container_var.get() not in [lbl for _, lbl, _ in containers]:
            self.name_container_var.set("None")
        if hasattr(self, "_container_grid_frame"):
            self._build_container_grid()
            self._on_name_container_selected()

    def _build_container_grid(self) -> None:
        frame = self._container_grid_frame
        for child in frame.winfo_children():
            child.destroy()
        self._container_thumb_refs.clear()

        TW, TH = 128, 40
        cols = 2
        current = self.name_container_var.get()

        for idx, (cid, label, path) in enumerate(self._container_data):
            col = idx % cols
            row = idx // cols
            cell = ttk.Frame(frame, style="Panel.TFrame")
            cell.grid(row=row, column=col, padx=4, pady=4, sticky="w")

            try:
                if path and path.exists():
                    img = Image.open(path).convert("RGBA")
                    bg = Image.new("RGB", (TW, TH), (30, 30, 35))
                    img.thumbnail((TW - 4, TH - 4), Image.Resampling.LANCZOS)
                    ox = (TW - img.width) // 2
                    oy = (TH - img.height) // 2
                    bg.paste(img, (ox, oy), img)
                    photo = ImageTk.PhotoImage(bg)
                else:
                    none_img = Image.new("RGB", (TW, TH), (40, 40, 45))
                    from PIL import ImageDraw as _ID
                    d = _ID.Draw(none_img)
                    d.line([(6, TH // 2), (TW - 6, TH // 2)], fill=(80, 80, 80), width=2)
                    d.text((TW // 2 - 12, TH // 2 - 8), "None", fill=(120, 120, 120))
                    photo = ImageTk.PhotoImage(none_img)
            except Exception:
                photo = None

            selected = label == current
            border = "#d4af37" if selected else "#333344"
            btn_frame = tk.Frame(cell, bg=border, bd=0)
            btn_frame.pack()
            if photo:
                self._container_thumb_refs.append(photo)
                btn = tk.Label(btn_frame, image=photo, cursor="hand2", bd=0, bg=border, padx=2, pady=2)
                btn.pack()
            btn.bind("<Button-1>", lambda _e, lbl=label: self._select_name_container(lbl))
            short = label if len(label) <= 22 else label[:21] + "…"
            tk.Label(cell, text=short, font=("Segoe UI", 7), bg="#1a1d23",
                     fg="#d4af37" if selected else "#888888", wraplength=TW + 20, justify="center").pack()

    def _select_name_container(self, label: str) -> None:
        self.name_container_var.set(label)
        self._on_name_container_selected()
        self._build_container_grid()

    def _on_name_container_selected(self, _event=None) -> None:
        label = self.name_container_var.get()
        cid = getattr(self, "_container_lookup", {}).get(label, "none")
        if cid.startswith("custom_"):
            p = base_dir() / "assets" / "name_containers" / f"{cid}.png"
            self.custom_name_container_path = p if p.exists() else None
        else:
            self.custom_name_container_path = None
        self.update_preview()

    def _on_container_resize(self, kind: str, delta: float) -> None:
        lo, hi = 0.55, 1.8
        if kind == "width":
            cur = float(self.name_container_width_var.get())
            self.name_container_width_var.set(max(lo, min(hi, cur + delta)))
            if hasattr(self, "_container_width_pct"):
                self._container_width_pct.set(int(self.name_container_width_var.get() * 100))
        elif kind == "height":
            cur = float(self.name_container_height_var.get())
            self.name_container_height_var.set(max(lo, min(hi, cur + delta)))
            if hasattr(self, "_container_height_pct"):
                self._container_height_pct.set(int(self.name_container_height_var.get() * 100))
        elif kind == "uniform":
            w = max(lo, min(hi, float(self.name_container_width_var.get()) + delta))
            h = max(lo, min(hi, float(self.name_container_height_var.get()) + delta))
            self.name_container_width_var.set(w)
            self.name_container_height_var.set(h)
            if hasattr(self, "_container_width_pct"):
                self._container_width_pct.set(int(w * 100))
            if hasattr(self, "_container_height_pct"):
                self._container_height_pct.set(int(h * 100))
        self.schedule_preview(60)

    def _name_container_id(self) -> str:
        return getattr(self, "_container_lookup", {}).get(self.name_container_var.get(), "none")

    def _upload_custom_container(self) -> None:
        path = filedialog.askopenfilename(
            title="Upload surah name container PNG",
            filetypes=[("PNG images", "*.png"), ("All images", "*.jpg *.jpeg *.png *.webp"), ("All files", "*.*")],
        )
        if not path:
            return
        dest_dir = base_dir() / "assets" / "name_containers"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"custom_{Path(path).stem}.png"
        shutil.copy2(path, dest)
        self.custom_name_container_path = dest
        self._refresh_name_containers()
        self.name_container_var.set(f"Custom: {Path(path).stem.replace('_', ' ').title()}")
        self.update_preview()

    def _quick_add_reciter_photo(self) -> None:
        reciter = self._selected_reciter()
        if not reciter:
            messagebox.showwarning(APP_TITLE, "Select a reciter collection first.")
            return
        path = filedialog.askopenfilename(
            title="Add reciter photo",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        reciter_store.add_reciter_photo(reciter.id, "Portrait", Path(path))
        self._refresh_reciter_photos()
        self.reciter_photo_var.set("Portrait")
        self.show_reciter_overlay_var.set(True)
        self.update_preview()

    def _reset_layout(self) -> None:
        pc = self.preview_canvas
        pc.block_x, pc.block_y = 0, 0
        pc.svg_off     = [0, 0]
        pc.title_off   = [0, 0]
        pc.reciter_off = [0, 0]
        pc.badge_off   = [0, 0]
        pc.reciter_x, pc.reciter_y, pc.reciter_width = 900, 420, 220
        self._sync_offset_vars_from_canvas()
        self.update_preview()

    def _apply_surah(self, surah_number: int) -> None:
        surah = get_surah(surah_number)
        if not surah:
            return
        self._syncing_surah = True
        self.surah_choice_var.set(surah_label(surah))
        self.arabic_var.set(surah.arabic)
        self.english_var.set(surah.english)
        self.number_var.set(str(surah.number))
        self._syncing_surah = False
        self.update_preview()

    def _on_surah_selected(self, _event=None) -> None:
        if self._syncing_surah:
            return
        for surah in SURAHS:
            if surah_label(surah) == self.surah_choice_var.get():
                self._apply_surah(surah.number)
                return

    def _on_number_typed(self, _event=None) -> None:
        if self._syncing_surah:
            return
        raw = self.number_var.get().strip()
        if raw.isdigit() and 1 <= int(raw) <= 114:
            self._apply_surah(int(raw))
        else:
            self.update_preview()

    def _refresh_reciter_options(self) -> None:
        self.reciters = reciter_store.load_reciters()
        names = [reciter.name for reciter in self.reciters]
        self.reciter_combo["values"] = names
        if names and self.reciter_collection_var.get() not in names:
            self.reciter_collection_var.set(names[0])
            self.reciter_display_var.set(names[0])
        self._refresh_reciter_photos()

    def _refresh_reciter_photos(self) -> None:
        reciter = self._selected_reciter()
        if not reciter or not reciter.photos:
            self.reciter_photo_combo["values"] = []
            self.reciter_photo_var.set("")
            return
        labels: list[str] = []
        self._photo_lookup = {}
        for photo in reciter.photos:
            if Path(photo.image_path).exists():
                labels.append(photo.label)
                self._photo_lookup[photo.label] = photo
        self.reciter_photo_combo["values"] = labels
        if labels and self.reciter_photo_var.get() not in labels:
            self.reciter_photo_var.set(labels[0])

    # Map file stem prefixes → display category
    _CATEGORY_PREFIXES = {
        "forest": "Forests",
        "autumn": "Forests",
        "winter": "Forests",
        "mountain": "Mountains",
        "valley": "Mountains",
        "lake": "Lakes",
        "spring": "Springs",
        "waterfall": "Springs",
        "river": "Springs",
        "stream": "Springs",
        "sky": "Other",
        "meadow": "Other",
        "desert": "Other",
        "beach": "Other",
        "canyon": "Other",
        "nature_pine": "Forests",
        "nature_calm_forest": "Forests",
        "nature_forest": "Forests",
        "nature_river_forest": "Forests",
        "nature_mountain": "Mountains",
        "nature_misty_peaks": "Mountains",
        "nature_cloudy_mountains": "Mountains",
        "nature_alpine_meadow": "Mountains",
        "nature_lake": "Lakes",
        "nature_serene_lake": "Lakes",
        "nature_waterfall": "Springs",
        "nature_sunset_valley": "Other",
        "nature_green_hills": "Other",
    }

    def _stem_to_category(self, stem: str) -> str:
        # Exact match first, then prefix match
        cat = self._CATEGORY_PREFIXES.get(stem)
        if cat:
            return cat
        for prefix, cat in self._CATEGORY_PREFIXES.items():
            if stem.startswith(prefix):
                return cat
        return "Other"

    _CAT_PRETTY = {
        "forest": "Forest", "mountain": "Mountain", "lake": "Lake",
        "spring": "Spring", "sky": "Sky", "valley": "Valley",
        "meadow": "Meadow", "desert": "Desert", "beach": "Beach",
        "autumn": "Autumn", "winter": "Winter", "nature": "Nature",
    }

    def _stem_to_label(self, stem: str) -> str:
        for prefix, pretty in self._CAT_PRETTY.items():
            if stem.startswith(prefix + "_"):
                rest = stem[len(prefix) + 1:]
                if rest.isdigit():
                    return f"{pretty} {rest}"
                return f"{rest.replace('_', ' ').title()} ({pretty})"
        return stem.replace("_", " ").title()

    def _refresh_nature_backgrounds(self) -> None:
        images = list_nature_backgrounds()
        if not images:
            images = [default_nature_background()]
        self._all_bg_data: list[tuple[str, str, Path]] = []  # (label, category, path)
        for p in images:
            label = self._stem_to_label(p.stem)
            category = self._stem_to_category(p.stem)
            self._all_bg_data.append((label, category, p))
        self._all_bg_data.sort(key=lambda t: (t[1], t[0]))
        self._apply_bg_category(self.bg_category_var.get() if hasattr(self, "bg_category_var") else "All")

    def _filter_backgrounds(self, category: str) -> None:
        self.bg_category_var.set(category)
        self._apply_bg_category(category)

    def _apply_bg_category(self, category: str) -> None:
        data = self._all_bg_data if hasattr(self, "_all_bg_data") else []
        if category == "All":
            filtered = data
        else:
            filtered = [(lbl, cat, p) for lbl, cat, p in data if cat == category]
        if not filtered and data:
            filtered = data
        labels = [lbl for lbl, _cat, _p in filtered]
        self._nature_lookup = {lbl: p for lbl, _cat, p in filtered}
        self.nature_combo["values"] = labels
        count = len(labels)
        self._bg_count_var.set(f"{count} image{'s' if count != 1 else ''} ({category})")
        if labels and self.nature_background_var.get() not in labels:
            # Prefer a calm mountain scene as the default selection
            pref = next((l for l in labels if l.lower().startswith("mountain")), labels[0])
            self.nature_background_var.set(pref)
        self._update_bg_preview()

    def _on_nature_selected(self) -> None:
        self._update_bg_preview()
        self.background_mode.set("nature")
        self.update_preview()

    def _update_bg_preview(self) -> None:
        lookup = getattr(self, "_nature_lookup", {})
        path = lookup.get(self.nature_background_var.get())
        if not path or not path.exists():
            return
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((80, 46), Image.Resampling.LANCZOS)
            self._bg_thumb_ref = ImageTk.PhotoImage(img)
            self._bg_preview_label.configure(image=self._bg_thumb_ref, width=80, height=46)
        except Exception:
            pass

    def _random_nature(self) -> None:
        import random
        labels = list(getattr(self, "_nature_lookup", {}).keys())
        if labels:
            self.nature_background_var.set(random.choice(labels))
            self.background_mode.set("nature")
            self._update_bg_preview()
            self.update_preview()

    def _fetch_fresh_scenery(self) -> None:
        """Download a brand-new, clean 4K image for guaranteed uniqueness."""
        import random
        import threading
        from urllib.request import Request, urlopen

        from image_quality import is_good_bytes

        category = self.bg_category_var.get() if hasattr(self, "bg_category_var") else "All"
        keyword_map = {
            "Forests": "forest", "Mountains": "mountain", "Lakes": "lake",
            "Springs": "waterfall", "Other": "nature landscape", "All": "nature landscape",
        }
        keyword = keyword_map.get(category, "nature landscape").replace(" ", ",")
        prefix_map = {
            "Forests": "forest", "Mountains": "mountain", "Lakes": "lake",
            "Springs": "spring", "Other": "sky", "All": "mountain",
        }
        prefix = prefix_map.get(category, "mountain")
        seed = random.randint(1, 9_999_999)
        dest = base_dir() / "assets" / "backgrounds" / f"{prefix}_fresh_{seed}.jpg"
        self.status_var.set("Fetching fresh 4K scenery online…")

        def worker():
            # Picsum first (reliable clean 4K), then validated keyword attempts.
            urls = [
                f"https://picsum.photos/seed/fresh{seed}/3840/2160",
                f"https://loremflickr.com/3840/2160/{keyword}?lock={seed}",
                f"https://picsum.photos/seed/fresh{seed + 31}/3840/2160",
            ]
            ok = False
            for url in urls:
                try:
                    req = Request(url, headers={"User-Agent": "QuranThumbnailGenerator/3.0"})
                    with urlopen(req, timeout=40) as resp:
                        data = resp.read()
                    if is_good_bytes(data):
                        dest.write_bytes(data)
                        ok = True
                        break
                except Exception:
                    continue
            self.after(0, lambda: self._on_fresh_fetched(ok, dest))

        threading.Thread(target=worker, daemon=True).start()

    def _on_fresh_fetched(self, ok: bool, dest: Path) -> None:
        if not ok:
            self.status_var.set("Could not fetch fresh scenery — check your connection.")
            return
        self._refresh_nature_backgrounds()
        label = self._stem_to_label(dest.stem)
        if label in self.nature_combo["values"]:
            self.nature_background_var.set(label)
        else:
            self._filter_backgrounds("All")
            self.nature_background_var.set(self._stem_to_label(dest.stem))
        self.background_mode.set("nature")
        self._update_bg_preview()
        self.update_preview()
        self.status_var.set("Fresh scenery added and applied.")

    def _on_reciter_collection_changed(self, _event=None) -> None:
        name = self.reciter_collection_var.get().strip()
        if name:
            self.reciter_display_var.set(name)
        self._refresh_reciter_photos()
        self.update_preview()

    def _open_reciter_manager(self) -> None:
        ReciterManagerDialog(self, on_change=self._on_reciters_changed)

    def _on_reciters_changed(self) -> None:
        self._refresh_reciter_options()
        self.update_preview()

    def _browse_custom_background(self) -> None:
        path = filedialog.askopenfilename(
            title="Select custom background",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All files", "*.*")],
        )
        if path:
            self.custom_background_var.set(path)
            self.background_mode.set("custom")
            self.update_preview()

    def _parse_surah_number(self) -> int:
        raw = self.number_var.get().strip()
        return int(raw) if raw.isdigit() else 0

    def _selected_reciter(self) -> reciter_store.Reciter | None:
        name = self.reciter_collection_var.get().strip()
        return next((r for r in self.reciters if r.name == name), None)

    def _selected_reciter_photo_path(self) -> Path | None:
        reciter = self._selected_reciter()
        if not reciter:
            return None
        photo = getattr(self, "_photo_lookup", {}).get(self.reciter_photo_var.get().strip())
        if photo and Path(photo.image_path).exists():
            return Path(photo.image_path)
        for item in reciter.photos:
            if Path(item.image_path).exists():
                return Path(item.image_path)
        return None

    def _resolve_background(self, warn: bool = False) -> Path:
        mode = self.background_mode.get()
        if mode == "nature":
            lookup = getattr(self, "_nature_lookup", {})
            path = lookup.get(self.nature_background_var.get())
            return path if path and path.exists() else default_nature_background()
        if mode == "reciter":
            path = self._selected_reciter_photo_path()
            if path:
                return path
            if warn:
                messagebox.showwarning(APP_TITLE, "Add photos via Manage... first.")
            return default_nature_background()
        if mode == "custom":
            custom = self.custom_background_var.get().strip()
            if custom and Path(custom).exists():
                return Path(custom)
            if warn:
                messagebox.showwarning(APP_TITLE, "Choose a valid custom background.")
            return default_nature_background()
        return default_nature_background()

    def _banner_id(self) -> str:
        return getattr(self, "_banner_lookup", {}).get(self.banner_var.get(), "none")

    def _build_config(self, warn: bool = False) -> ThumbnailConfig:
        layout = self.preview_canvas.layout_dict()
        overlay_path = self._selected_reciter_photo_path() if self.show_reciter_overlay_var.get() else None
        return ThumbnailConfig(
            arabic_surah=self.arabic_var.get(),
            english_surah=self.english_var.get(),
            reciter_name=self.reciter_display_var.get().strip(),
            surah_number=self._parse_surah_number(),
            background_path=self._resolve_background(warn=warn),
            overlay_opacity=float(self.overlay_var.get()),
            arabic_color=self.arabic_color.rgb(),
            english_color=self.english_color.rgb(),
            reciter_color=self.reciter_color.rgb(),
            badge_text_color=self.badge_text_color.rgb(),
            badge_accent_color=self.badge_accent_color.rgb(),
            banner_id=self._banner_id(),
            banner_custom_path=self.custom_banner_path,
            name_container_id=self._name_container_id(),
            name_container_custom_path=self.custom_name_container_path,
            name_container_width_scale=float(self.name_container_width_var.get()),
            name_container_height_scale=float(self.name_container_height_var.get()),
            name_container_opacity=float(self.name_container_opacity_var.get()),
            text_glow=self.text_glow_var.get(),
            text_offset_x=layout["text_offset_x"],
            text_offset_y=layout["text_offset_y"],
            show_reciter_overlay=self.show_reciter_overlay_var.get() and overlay_path is not None,
            reciter_overlay_path=overlay_path,
            reciter_overlay_x=layout["reciter_overlay_x"],
            reciter_overlay_y=layout["reciter_overlay_y"],
            reciter_overlay_width=layout["reciter_overlay_width"],
            svg_max_height=int(self.svg_height_var.get()),
            title_size=int(self.title_size_var.get()),
            reciter_size=int(self.reciter_size_var.get()),
            badge_size=int(self.badge_size_var.get()),
            svg_offset_x=layout["svg_offset_x"],
            svg_offset_y=layout["svg_offset_y"],
            title_offset_x=layout["title_offset_x"],
            title_offset_y=layout["title_offset_y"],
            reciter_offset_x=layout["reciter_offset_x"],
            reciter_offset_y=layout["reciter_offset_y"],
            badge_offset_x=layout["badge_offset_x"],
            badge_offset_y=layout["badge_offset_y"],
            banner_corner_size=float(self.banner_size_var.get()),
        )

    def schedule_preview(self, delay_ms: int = 120) -> None:
        """Debounced preview refresh — coalesces rapid slider/drag updates."""
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except (ValueError, tk.TclError):
                pass
        self._preview_job = self.after(delay_ms, self._run_scheduled_preview)

    def _run_scheduled_preview(self) -> None:
        self._preview_job = None
        self.update_preview()

    def update_preview(self) -> None:
        try:
            self.preview_canvas.show_reciter = (
                self.show_reciter_overlay_var.get()
                and self._selected_reciter_photo_path() is not None
            )
            self.preview_canvas.update_sizes(
                int(self.svg_height_var.get()),
                int(self.title_size_var.get()),
                int(self.reciter_size_var.get()),
                int(self.badge_size_var.get()),
            )
            layout: dict = {}
            # Render the preview at a high-enough internal scale that it stays
            # crisp at the current display size (matches the export look).
            pw = getattr(self.preview_canvas, "pre_w", 640)
            preview_scale = 1 if pw <= 1180 else (2 if pw <= 2400 else 3)
            image = generate_thumbnail(self._build_config(), _scale=preview_scale, layout_out=layout)
            self.preview_canvas.set_layout(layout)
            self.preview_canvas.show_image(image)
            self.status_var.set(
                "Preview — colored tabs (left) move individual layers · drag canvas = block · arrows = nudge"
            )
        except Exception as exc:
            self.status_var.set(f"Preview error: {exc}")

    def export_thumbnail(self) -> None:
        number = self._parse_surah_number()
        english = self.english_var.get().strip().replace(" ", "_") or "thumbnail"
        default_name = f"{number:03d}_{english}.png" if number else f"{english}.png"
        output = filedialog.asksaveasfilename(
            title="Save thumbnail",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG image", "*.png")],
        )
        if not output:
            return
        scale = int(self.export_scale_var.get())
        dims = {1: "1280×720", 2: "2560×1440", 3: "3840×2160"}.get(scale, "HD")
        self.status_var.set(f"Exporting at {dims}…")
        self.update_idletasks()
        try:
            save_thumbnail(self._build_config(warn=True), Path(output), export_scale=scale)
            self.status_var.set(f"Saved {dims} PNG to {output}")
            messagebox.showinfo(APP_TITLE, f"Thumbnail saved ({dims}):\n{output}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not save thumbnail:\n{exc}")

    def batch_export(self) -> None:
        BatchExportDialog(self, self._build_config, int(self.export_scale_var.get()))


def _set_app_user_model_id() -> None:
    """Tell Windows this is its own app so the taskbar uses our icon, not python's."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "ArthurVlade.QuranThumbnailGenerator"
        )
    except Exception:
        pass


def main() -> None:
    _set_app_user_model_id()
    ensure_initialized()
    app = ThumbnailApp()
    app._maybe_download_first_run_assets()
    app.mainloop()


if __name__ == "__main__":
    main()
