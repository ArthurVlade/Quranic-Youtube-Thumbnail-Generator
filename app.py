"""GUI for generating Quranic recitation thumbnails."""

from __future__ import annotations

import os
import sys
import tkinter as tk
import shutil
from dataclasses import replace
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageTk

import i18n
import reciter_store
import settings_store
import win_chrome
from language_picker import ask_language
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
from text_fonts import (
    RECITER_FONTS,
    TITLE_FONTS,
    reciter_font_label,
    title_font_label,
)
from ui_theme import (
    ACCENT,
    ACCENT_HOVER,
    ACCENT_TEXT,
    BG_DARK,
    BG_ELEV,
    BG_INPUT,
    BG_PANEL,
    BORDER,
    CLOSE_HOVER,
    CTRL_HOVER,
    FG_MUTED,
    FG_PRIMARY,
    FONT_HEADING,
    LightGradientBackdrop,
    SegmentedControl,
    SegmentedTabView,
    TITLEBAR_BG,
    TITLEBAR_FG,
    apply_theme,
    get_theme_mode,
    palette,
    set_theme_mode,
    style_listbox,
    toggle_theme_mode,
)

PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 360


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


class ColorPickerRow(ttk.Frame):
    def __init__(
        self,
        master,
        label: str,
        initial: str,
        on_change,
        *,
        i18n_key: str | None = None,
    ) -> None:
        super().__init__(master, style="Panel.TFrame")
        self.on_change = on_change
        self.color_var = tk.StringVar(value=initial)
        lbl = ttk.Label(self, text=label, style="Panel.TLabel", width=16)
        lbl.pack(side="left")
        if i18n_key:
            i18n.bind_widget(lbl, i18n_key)
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
        result = colorchooser.askcolor(color=rgb, title=i18n.t("dialog.choose_color"))
        if result[1]:
            self.color_var.set(result[1])
            self._refresh_swatch()
            self.on_change()

    def rgb(self) -> tuple[int, int, int]:
        return _hex_to_rgb(self.color_var.get())


class BatchExportDialog(tk.Toplevel):
    def __init__(self, master: "ThumbnailApp", build_config, export_scale: int = 2) -> None:
        super().__init__(master)
        self.title(i18n.t("dialog.batch.title"))
        self.geometry("440x300")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.build_config = build_config
        self.export_scale = export_scale

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=i18n.t("dialog.batch.from")).grid(row=0, column=0, sticky="w")
        self.from_var = tk.StringVar(value="1")
        ttk.Spinbox(frame, from_=1, to=114, textvariable=self.from_var, width=8).grid(row=0, column=1, sticky="w", padx=(8, 0))

        ttk.Label(frame, text=i18n.t("dialog.batch.to")).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.to_var = tk.StringVar(value="114")
        ttk.Spinbox(frame, from_=1, to=114, textvariable=self.to_var, width=8).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(frame, text=i18n.t("dialog.batch.folder")).grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.folder_var = tk.StringVar()
        folder_row = ttk.Frame(frame)
        folder_row.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Entry(folder_row, textvariable=self.folder_var, width=28).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text=i18n.t("btn.browse"), command=self._browse).pack(side="left", padx=(8, 0))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.progress_label = ttk.Label(frame, text="", style="Muted.TLabel")
        self.progress_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.export_btn = ttk.Button(buttons, text=i18n.t("dialog.batch.export_all"), style="Accent.TButton", command=self._export)
        self.export_btn.pack(side="left")
        ttk.Button(buttons, text=i18n.t("btn.cancel"), command=self.destroy).pack(side="right")
        self._cancelled = False

    def _browse(self) -> None:
        folder = filedialog.askdirectory(title=i18n.t("dialog.folder.output"))
        if folder:
            self.folder_var.set(folder)

    def _export(self) -> None:
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning(i18n.t("app.title"), i18n.t("dialog.batch.choose_folder"))
            return
        try:
            start = int(self.from_var.get())
            end = int(self.to_var.get())
        except ValueError:
            messagebox.showwarning(i18n.t("app.title"), i18n.t("dialog.batch.invalid_range"))
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
                english_surah=i18n.surah_title(surah.number),
                surah_number=surah.number,
            )
            title = i18n.surah_title(surah.number)
            slug = title.replace(" ", "_").replace("/", "-")
            filename = f"{number:03d}_{slug}.png"
            try:
                save_thumbnail(config, output_dir / filename, self.export_scale)
                saved += 1
            except Exception:
                pass
            self.progress_var.set(idx / total * 100)
            self.progress_label.configure(text=f"{idx}/{total} — {i18n.surah_title(surah.number)}")
            self.update_idletasks()

        messagebox.showinfo(i18n.t("app.title"), i18n.t("msg.batch.exported", count=saved, folder=output_dir))
        self.destroy()


class ReciterManagerDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, on_change) -> None:
        super().__init__(master)
        self.title(i18n.t("dialog.reciter.title"))
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

        reciter_frame = ttk.LabelFrame(frame, text=i18n.t("dialog.reciter.reciters"), padding=8)
        reciter_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        i18n.bind_widget(reciter_frame, "dialog.reciter.reciters")
        self.reciter_list = tk.Listbox(reciter_frame, height=14)
        style_listbox(self.reciter_list)
        self.reciter_list.pack(fill="both", expand=True)
        self.reciter_list.bind("<<ListboxSelect>>", self._on_reciter_select)

        photo_frame = ttk.LabelFrame(frame, text=i18n.t("dialog.reciter.photos"), padding=8)
        photo_frame.grid(row=0, column=1, sticky="nsew")
        i18n.bind_widget(photo_frame, "dialog.reciter.photos")
        self.photo_list = tk.Listbox(photo_frame, height=14)
        style_listbox(self.photo_list)
        self.photo_list.pack(fill="both", expand=True)
        self.photo_list.bind("<<ListboxSelect>>", self._on_photo_select)

        form = ttk.Frame(frame)
        form.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        form.columnconfigure(1, weight=1)

        name_lbl = ttk.Label(form, text=i18n.t("dialog.reciter.name"))
        name_lbl.grid(row=0, column=0, sticky="w")
        i18n.bind_widget(name_lbl, "dialog.reciter.name")
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        photo_lbl = ttk.Label(form, text=i18n.t("dialog.reciter.photo_label"))
        photo_lbl.grid(row=1, column=0, sticky="w", pady=(8, 0))
        i18n.bind_widget(photo_lbl, "dialog.reciter.photo_label")
        self.photo_label_var = tk.StringVar(value=i18n.t("dialog.reciter.portrait"))
        ttk.Entry(form, textvariable=self.photo_label_var, width=40).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        file_lbl = ttk.Label(form, text=i18n.t("dialog.reciter.image_file"))
        file_lbl.grid(row=2, column=0, sticky="w", pady=(8, 0))
        i18n.bind_widget(file_lbl, "dialog.reciter.image_file")
        file_row = ttk.Frame(form)
        file_row.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        self.file_var = tk.StringVar(value=i18n.t("dialog.reciter.no_image"))
        ttk.Label(file_row, textvariable=self.file_var).pack(side="left", fill="x", expand=True)
        browse_btn = ttk.Button(file_row, text=i18n.t("btn.browse"), command=self._browse_photo)
        browse_btn.pack(side="right")
        i18n.bind_widget(browse_btn, "btn.browse")

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        for key, cmd in [
            ("dialog.reciter.add", self._add_reciter),
            ("dialog.reciter.save_name", self._save_reciter_name),
            ("dialog.reciter.add_photo", self._add_photo),
            ("dialog.reciter.remove_photo", self._remove_photo),
            ("dialog.reciter.delete", self._delete_reciter),
        ]:
            btn = ttk.Button(buttons, text=i18n.t(key), command=cmd)
            btn.pack(side="left", padx=(0 if key == "dialog.reciter.add" else 8, 0))
            i18n.bind_widget(btn, key)
        done_btn = ttk.Button(buttons, text=i18n.t("btn.done"), command=self.destroy)
        done_btn.pack(side="right")
        i18n.bind_widget(done_btn, "btn.done")

        self._pending_photo: Path | None = None
        self.reciters: list[reciter_store.Reciter] = []
        self.refresh()

    def refresh(self) -> None:
        self.reciter_list.delete(0, tk.END)
        self.photo_list.delete(0, tk.END)
        self.reciters = reciter_store.load_reciters()
        for reciter in self.reciters:
            count = len(reciter.photos)
            key = "dialog.reciter.photo_one" if count == 1 else "dialog.reciter.photo_many"
            label = i18n.t(key, name=i18n.reciter_name(reciter.id, reciter.name), count=count)
            self.reciter_list.insert(tk.END, label)

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
            suffix = "" if exists else i18n.t("dialog.reciter.missing")
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
            title=i18n.t("dialog.reciter.photo_title"),
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All files", "*.*")],
        )
        if path:
            self._pending_photo = Path(path)
            self.file_var.set(Path(path).name)

    def _add_reciter(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.reciter.enter_name"))
            return
        reciter_store.add_reciter(name)
        self.name_var.set("")
        self.refresh()
        self.on_change()

    def _save_reciter_name(self) -> None:
        if not self.selected_reciter_id:
            messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.reciter.select_first"))
            return
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.reciter.enter_name"))
            return
        reciter_store.update_reciter_name(self.selected_reciter_id, name)
        self.refresh()
        self.on_change()

    def _add_photo(self) -> None:
        if not self.selected_reciter_id:
            messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.reciter.select_for_photos"))
            return
        if not self._pending_photo:
            messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.reciter.choose_image"))
            return
        label = self.photo_label_var.get().strip() or i18n.t("dialog.reciter.portrait")
        reciter_store.add_reciter_photo(self.selected_reciter_id, label, self._pending_photo)
        self._pending_photo = None
        self.file_var.set(i18n.t("dialog.reciter.no_image"))
        self.refresh()
        self._on_reciter_select()
        self.on_change()

    def _remove_photo(self) -> None:
        if not self.selected_reciter_id or not self.selected_photo_id:
            messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.reciter.select_photo_remove"))
            return
        if not messagebox.askyesno(i18n.t("app.title"), i18n.t("msg.reciter.confirm_remove_photo")):
            return
        reciter_store.delete_reciter_photo(self.selected_reciter_id, self.selected_photo_id)
        self.selected_photo_id = None
        self.refresh()
        self._on_reciter_select()
        self.on_change()

    def _delete_reciter(self) -> None:
        if not self.selected_reciter_id:
            messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.reciter.select_to_delete"))
            return
        if not messagebox.askyesno(i18n.t("app.title"), i18n.t("msg.reciter.confirm_delete")):
            return
        reciter_store.delete_reciter(self.selected_reciter_id)
        self.selected_reciter_id = None
        self.selected_photo_id = None
        self.name_var.set("")
        self.file_var.set(i18n.t("dialog.reciter.no_image"))
        self.refresh()
        self.on_change()


class ThumbnailApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(i18n.t("app.title"))
        self.geometry("1280x820+80+40")
        self.minsize(1120, 720)
        self._saved_settings = settings_store.load_settings()
        apply_theme(self, self._saved_settings.get("ui_theme", "dark"))
        self._set_window_icon()

        self.reciters = reciter_store.load_reciters()
        self._reciter_label_to_id: dict[str, str] = {}
        self._bg_segment: SegmentedControl | None = None
        self._tab_view: SegmentedTabView | None = None
        self._scroll_canvases: list[tk.Canvas] = []
        self._tab_keys: list[str] = []
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
        self.english_var = tk.StringVar(value=i18n.surah_title(5) if default else "")
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
        self.status_var = tk.StringVar(value=i18n.t("status.ready"))
        self._language_display = tk.StringVar(value="")
        self._language_was_chosen = bool(self._saved_settings.get("language_chosen", False))

        # Typography sizes (defaults tuned to the cinematic reference look)
        self.svg_height_var = tk.IntVar(value=500)
        self.title_size_var = tk.IntVar(value=52)
        self.reciter_size_var = tk.IntVar(value=44)
        self.badge_size_var = tk.IntVar(value=28)
        self.title_font_var = tk.StringVar()
        self.reciter_font_var = tk.StringVar()
        self._title_font_labels: dict[str, str] = {}
        self._reciter_font_labels: dict[str, str] = {}

        self._syncing_offsets = False

        if self._custom_chrome:
            self._build_titlebar()
        self._light_backdrop = LightGradientBackdrop(self)
        self._light_backdrop.mount()
        self._build_ui()
        self.text_offset_x_var.trace_add("write", lambda *_: self._apply_offset_spinboxes())
        self.text_offset_y_var.trace_add("write", lambda *_: self._apply_offset_spinboxes())
        self._refresh_reciter_options()
        self._refresh_nature_backgrounds()
        self._refresh_banners()
        self._refresh_name_containers()
        self._restore_settings()
        self._apply_ui_theme()
        self._bind_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._ui_ready = True
        self._finalize_custom_shell()
        self.after(100, self.update_preview)

    def _ensure_window_visible(self) -> None:
        """Force the main window on-screen and in front (fixes invisible launch via run.bat)."""
        try:
            self.update_idletasks()
            self.deiconify()
            if str(self.state()) == "iconic":
                self.state("normal")
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            w = max(int(self.winfo_width()), 400)
            h = max(int(self.winfo_height()), 300)
            x = int(self.winfo_x())
            y = int(self.winfo_y())
            off_screen = x + 120 < 0 or y + 120 < 0 or x > sw - 80 or y > sh - 80
            if off_screen:
                x = max(0, (sw - w) // 2)
                y = max(0, (sh - h) // 2)
                self.geometry(f"{w}x{h}+{x}+{y}")
            self.lift()
            self.focus_force()
            self.attributes("-topmost", True)
            self.after(350, lambda: self.attributes("-topmost", False))
        except tk.TclError:
            pass

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
        """Apply borderless Win32 shell after the window is mapped."""
        self.after(1, self._ensure_window_visible)
        if not self._custom_chrome:
            self.after(80, lambda: win_chrome.set_task_manager_title(self, i18n.t("app.title")))
            return

        def _apply_shell() -> None:
            self.update_idletasks()
            win_chrome.apply_borderless_shell(self)
            win_chrome.register_taskbar_hooks(self)
            win_chrome.set_task_manager_title(self, i18n.t("app.title"))
            self._ensure_window_visible()

        self.after(120, _apply_shell)

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

        title = tk.Label(bar, text=i18n.t("app.title"), bg=TITLEBAR_BG, fg=TITLEBAR_FG,
                         font=(FONT_HEADING, 10))
        title.pack(side="left", pady=8)
        self._titlebar_label = title

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
            "title_font": self._current_title_font_id(),
            "reciter_font": self._current_reciter_font_id(),
            "arabic_color": self.arabic_color.color_var.get(),
            "english_color": self.english_color.color_var.get(),
            "reciter_color": self.reciter_color.color_var.get(),
            "badge_text_color": self.badge_text_color.color_var.get(),
            "badge_accent_color": self.badge_accent_color.color_var.get(),
            "reciter_collection": self.reciter_collection_var.get(),
            "language": i18n.get_language(),
            "ui_theme": get_theme_mode(),
            "language_chosen": bool(
                getattr(self, "_language_was_chosen", False)
                or self._saved_settings.get("language_chosen", False)
            ),
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
            if hasattr(self, "title_font_combo"):
                self._set_title_font(s.get("title_font", "cinzel"))
                self._set_reciter_font(s.get("reciter_font", "cormorant_garamond"))
            theme = s.get("ui_theme")
            if theme in {"dark", "light"}:
                set_theme_mode(theme)
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
        self.status_var.set(i18n.t("status.downloading"))

        def on_progress(msg: str) -> None:
            self.after(0, lambda: self.status_var.set(msg))

        def on_done(ok: int, fail: int, err: str = "") -> None:
            def finish():
                if err:
                    self.status_var.set(i18n.t("status.asset_error", error=err))
                elif fail:
                    self.status_var.set(i18n.t("status.assets_partial", ok=ok, fail=fail))
                else:
                    self.status_var.set(i18n.t("status.assets_ready"))
                self._refresh_nature_backgrounds()
                self.update_preview()

            self.after(0, finish)

        start_background_download(on_progress, on_done)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self._light_backdrop.inner, padding=10, style="Gutter.TFrame")
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)
        self._outer = outer

        p = palette()
        self._left_card = tk.Frame(outer, bg=p.border, highlightthickness=0, bd=0)
        self._left_card.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
        left_shell = ttk.Frame(self._left_card, style="Panel.TFrame", padding=0)
        left_shell.pack(fill="both", expand=True, padx=1, pady=1)
        left_shell.configure(width=400)

        header = ttk.Frame(left_shell, style="Panel.TFrame", padding=(12, 12, 12, 4))
        header.pack(fill="x")
        hdr = ttk.Label(header, text=i18n.t("header.settings"), style="Panel.Heading.TLabel")
        hdr.pack(anchor="w")
        i18n.bind_widget(hdr, "header.settings")
        hint = ttk.Label(
            header,
            text=i18n.t("header.hint"),
            style="Panel.Muted.TLabel",
            wraplength=360,
        )
        hint.pack(anchor="w", pady=(4, 0))
        i18n.bind_widget(hint, "header.hint")
        self._build_language_bar(header)

        notebook = SegmentedTabView(left_shell)
        notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._tab_view = notebook
        self._scroll_canvases = notebook.scroll_canvases
        self._tab_keys = [
            "tab.surah", "tab.style", "tab.reciter", "tab.background", "tab.banners", "tab.export",
        ]

        self._build_surah_tab(notebook.add_tab("tab.surah", i18n.t("tab.surah")))
        self._build_style_tab(notebook.add_tab("tab.style", i18n.t("tab.style")))
        self._build_reciter_tab(notebook.add_tab("tab.reciter", i18n.t("tab.reciter")))
        self._build_background_tab(notebook.add_tab("tab.background", i18n.t("tab.background")))
        self._build_layout_tab(notebook.add_tab("tab.banners", i18n.t("tab.banners")))
        self._build_export_tab(notebook.add_tab("tab.export", i18n.t("tab.export")))

        self._preview_card = tk.Frame(outer, bg=p.border, highlightthickness=0, bd=0)
        self._preview_card.grid(row=0, column=1, sticky="nsew")
        preview_frame = ttk.LabelFrame(
            self._preview_card,
            text=i18n.t("preview.frame"),
            style="Dark.TLabelframe",
            padding=8,
        )
        preview_frame.pack(fill="both", expand=True, padx=1, pady=1)
        i18n.bind_widget(preview_frame, "preview.frame")
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

    def _build_language_bar(self, parent) -> None:
        lang_frame = ttk.Frame(parent, style="Panel.TFrame")
        lang_frame.pack(fill="x", pady=(10, 0))

        current_lbl = ttk.Label(lang_frame, text=i18n.t("language.current"), style="Panel.TLabel")
        current_lbl.pack(side="left")
        i18n.bind_widget(current_lbl, "language.current")

        name_lbl = ttk.Label(lang_frame, textvariable=self._language_display, style="Panel.TLabel")
        name_lbl.pack(side="left", padx=(6, 0))

        change_btn = ttk.Button(
            lang_frame,
            text=i18n.t("language.change_btn"),
            command=self._change_language,
        )
        change_btn.pack(side="right")
        i18n.bind_widget(change_btn, "language.change_btn")

        self._theme_btn = ttk.Button(
            lang_frame,
            text=self._theme_button_label(),
            style="Ghost.TButton",
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="right", padx=(0, 8))
        i18n.bind_widget(self._theme_btn, self._theme_button_i18n_key())

        self._language_display.set(self._language_display_name())

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

        self._field(parent, "field.arabic_name", self.arabic_var)
        self._field(parent, "field.english_title", self.english_var)
        self._field(parent, "field.surah_number", self.number_var, width=10, handler=self._on_number_typed)

        surah_hint = ttk.Label(
            parent,
            text=i18n.t("surah.hint"),
            style="Panel.Muted.TLabel",
            wraplength=350,
        )
        surah_hint.pack(anchor="w", pady=(10, 0))
        i18n.bind_widget(surah_hint, "surah.hint")

    def _build_style_tab(self, parent) -> None:
        # ── Colors ──────────────────────────────────────────────────────────
        colors_hdr = ttk.Label(parent, text=i18n.t("style.colors"), style="Panel.Heading.TLabel")
        colors_hdr.pack(anchor="w", pady=(0, 6))
        i18n.bind_widget(colors_hdr, "style.colors")
        self.arabic_color = ColorPickerRow(
            parent, i18n.t("color.arabic"), "#ffffff", self.update_preview, i18n_key="color.arabic",
        )
        self.arabic_color.pack(anchor="w", fill="x", pady=(0, 4))
        self.english_color = ColorPickerRow(
            parent, i18n.t("color.english"), "#ffffff", self.update_preview, i18n_key="color.english",
        )
        self.english_color.pack(anchor="w", fill="x", pady=(0, 4))
        self.reciter_color = ColorPickerRow(
            parent, i18n.t("color.reciter"), "#ffffff", self.update_preview, i18n_key="color.reciter",
        )
        self.reciter_color.pack(anchor="w", fill="x", pady=(0, 4))
        self.badge_text_color = ColorPickerRow(
            parent, i18n.t("color.badge_text"), "#ffffff", self.update_preview, i18n_key="color.badge_text",
        )
        self.badge_text_color.pack(anchor="w", fill="x", pady=(0, 4))
        self.badge_accent_color = ColorPickerRow(
            parent, i18n.t("color.badge_accent"), "#d4af37", self.update_preview, i18n_key="color.badge_accent",
        )
        self.badge_accent_color.pack(anchor="w", fill="x", pady=(0, 4))
        glow = ttk.Checkbutton(
            parent, text=i18n.t("color.soft_glow"), variable=self.text_glow_var, command=self.update_preview,
        )
        glow.pack(anchor="w", pady=(4, 0))
        i18n.bind_widget(glow, "color.soft_glow")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(12, 8))
        self._build_font_section(parent)

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(12, 8))

        # ── Typography sizes ─────────────────────────────────────────────────
        typo_hdr = ttk.Label(parent, text=i18n.t("style.typography"), style="Panel.Heading.TLabel")
        typo_hdr.pack(anchor="w", pady=(0, 8))
        i18n.bind_widget(typo_hdr, "style.typography")
        self._size_row(parent, "size.arabic_svg", self.svg_height_var, 80, 500, 5)
        self._size_row(parent, "size.english_title", self.title_size_var, 20, 90, 2)
        self._size_row(parent, "size.reciter", self.reciter_size_var, 16, 70, 2)
        self._size_row(parent, "size.badge", self.badge_size_var, 14, 52, 2)

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(12, 8))
        container_hdr = ttk.Label(parent, text=i18n.t("style.container"), style="Panel.Heading.TLabel")
        container_hdr.pack(anchor="w", pady=(0, 4))
        i18n.bind_widget(container_hdr, "style.container")
        container_hint = ttk.Label(
            parent,
            text=i18n.t("style.container_hint"),
            style="Panel.Muted.TLabel",
            wraplength=360,
        )
        container_hint.pack(anchor="w", pady=(0, 6))
        i18n.bind_widget(container_hint, "style.container_hint")

        self._container_grid_frame = ttk.Frame(parent, style="Panel.TFrame")
        self._container_grid_frame.pack(fill="x")
        self._container_thumb_refs: list[ImageTk.PhotoImage] = []

        container_scale_row = ttk.Frame(parent, style="Panel.TFrame")
        container_scale_row.pack(fill="x", pady=(6, 0))
        opacity_lbl = ttk.Label(container_scale_row, text=i18n.t("style.container_opacity"), style="Panel.TLabel", width=20)
        opacity_lbl.pack(side="left")
        i18n.bind_widget(opacity_lbl, "style.container_opacity")
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
        height_lbl = ttk.Label(container_height_row, text=i18n.t("style.container_height"), style="Panel.TLabel", width=20)
        height_lbl.pack(side="left")
        i18n.bind_widget(height_lbl, "style.container_height")
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
        width_lbl = ttk.Label(container_width_row, text=i18n.t("style.container_width"), style="Panel.TLabel", width=20)
        width_lbl.pack(side="left")
        i18n.bind_widget(width_lbl, "style.container_width")
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

        preview_hint = ttk.Label(
            parent,
            text=i18n.t("style.container_preview_hint"),
            style="Panel.Muted.TLabel",
            wraplength=360,
        )
        preview_hint.pack(anchor="w", pady=(6, 0))
        i18n.bind_widget(preview_hint, "style.container_preview_hint")

        upload_btn = ttk.Button(parent, text=i18n.t("style.upload_container"), command=self._upload_custom_container)
        upload_btn.pack(anchor="w", pady=(8, 0))
        i18n.bind_widget(upload_btn, "style.upload_container")

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

    def _build_font_section(self, parent) -> None:
        """Title + reciter font pickers — placed near the top of the Style tab."""
        frame = ttk.LabelFrame(parent, text=i18n.t("style.fonts"), padding=8)
        frame.pack(fill="x", pady=(0, 4))
        i18n.bind_widget(frame, "style.fonts")
        self._font_combo_row(
            frame,
            "style.title_font",
            self.title_font_var,
            TITLE_FONTS,
            self._title_font_labels,
            self._on_title_font_changed,
        )
        self._font_combo_row(
            frame,
            "style.reciter_font",
            self.reciter_font_var,
            RECITER_FONTS,
            self._reciter_font_labels,
            self._on_reciter_font_changed,
        )
        fonts_hint = ttk.Label(
            frame,
            text=i18n.t("style.fonts_hint"),
            style="Panel.Muted.TLabel",
            wraplength=340,
        )
        fonts_hint.pack(anchor="w", pady=(4, 0))
        i18n.bind_widget(fonts_hint, "style.fonts_hint")

    def _font_combo_row(
        self,
        parent,
        label_key: str,
        var: tk.StringVar,
        choices: tuple,
        lookup: dict[str, str],
        on_change,
    ) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", pady=(0, 8))
        lbl = ttk.Label(row, text=i18n.t(label_key), style="Panel.TLabel", width=18)
        lbl.pack(side="left", anchor="n")
        i18n.bind_widget(lbl, label_key)
        combo = ttk.Combobox(row, textvariable=var, state="readonly", width=36)
        combo.pack(side="left", fill="x", expand=True, padx=(6, 0))
        labels: list[str] = []
        for choice in choices:
            lookup[choice.label] = choice.id
            labels.append(choice.label)
        combo["values"] = labels
        combo.bind("<<ComboboxSelected>>", on_change)
        if label_key == "style.title_font":
            self.title_font_combo = combo
            if var.get() not in labels:
                default = next((c.label for c in choices if c.id == "cinzel"), labels[0] if labels else "")
                if default:
                    var.set(default)
        else:
            self.reciter_font_combo = combo
            if var.get() not in labels:
                default = next(
                    (c.label for c in choices if c.id == "cormorant_garamond"),
                    labels[0] if labels else "",
                )
                if default:
                    var.set(default)

    def _current_title_font_id(self) -> str:
        label = self.title_font_var.get()
        return self._title_font_labels.get(label, "cinzel")

    def _current_reciter_font_id(self) -> str:
        label = self.reciter_font_var.get()
        return self._reciter_font_labels.get(label, "cormorant_garamond")

    def _set_title_font(self, font_id: str) -> None:
        label = title_font_label(font_id)
        if hasattr(self, "title_font_combo"):
            values = list(self.title_font_combo["values"])
            if label in values:
                self.title_font_var.set(label)

    def _set_reciter_font(self, font_id: str) -> None:
        label = reciter_font_label(font_id)
        if hasattr(self, "reciter_font_combo"):
            values = list(self.reciter_font_combo["values"])
            if label in values:
                self.reciter_font_var.set(label)

    def _on_title_font_changed(self, _event=None) -> None:
        self.schedule_preview()

    def _on_reciter_font_changed(self, _event=None) -> None:
        self.schedule_preview()

    def _size_row(self, parent, label_key: str, var: tk.IntVar, lo: int, hi: int, step: int) -> None:
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", pady=(0, 6))
        lbl = ttk.Label(row, text=i18n.t(label_key), style="Panel.TLabel", width=20)
        lbl.pack(side="left")
        i18n.bind_widget(lbl, label_key)
        val_lbl = ttk.Label(row, textvariable=var, style="Panel.TLabel", width=4)
        val_lbl.pack(side="right")
        ttk.Scale(
            row, from_=lo, to=hi, variable=var, orient="horizontal",
            command=lambda _v: [var.set(round(var.get() / step) * step), self.schedule_preview()],
        ).pack(side="left", fill="x", expand=True, padx=(6, 6))

    def _build_reciter_tab(self, parent) -> None:
        coll_lbl = ttk.Label(parent, text=i18n.t("reciter.collection"), style="Panel.TLabel")
        coll_lbl.pack(anchor="w")
        i18n.bind_widget(coll_lbl, "reciter.collection")
        collection_row = ttk.Frame(parent, style="Panel.TFrame")
        collection_row.pack(fill="x", pady=(4, 8))
        self.reciter_combo = ttk.Combobox(collection_row, textvariable=self.reciter_collection_var, state="readonly", width=24)
        self.reciter_combo.pack(side="left", fill="x", expand=True)
        self.reciter_combo.bind("<<ComboboxSelected>>", self._on_reciter_collection_changed)
        manage_btn = ttk.Button(collection_row, text=i18n.t("reciter.manage"), command=self._open_reciter_manager)
        manage_btn.pack(side="left", padx=(8, 0))
        i18n.bind_widget(manage_btn, "reciter.manage")

        self._field(parent, "reciter.name_on_thumb", self.reciter_display_var)
        photo_lbl = ttk.Label(parent, text=i18n.t("reciter.photo"), style="Panel.TLabel")
        photo_lbl.pack(anchor="w", pady=(8, 0))
        i18n.bind_widget(photo_lbl, "reciter.photo")
        self.reciter_photo_combo = ttk.Combobox(parent, textvariable=self.reciter_photo_var, state="readonly", width=36)
        self.reciter_photo_combo.pack(anchor="w", pady=(4, 0))
        self.reciter_photo_combo.bind("<<ComboboxSelected>>", lambda _e: self.update_preview())

        photo_actions = ttk.Frame(parent, style="Panel.TFrame")
        photo_actions.pack(anchor="w", fill="x", pady=(8, 0))
        add_photo_btn = ttk.Button(photo_actions, text=i18n.t("reciter.add_photo"), command=self._quick_add_reciter_photo)
        add_photo_btn.pack(side="left")
        i18n.bind_widget(add_photo_btn, "reciter.add_photo")
        overlay_chk = ttk.Checkbutton(
            parent,
            text=i18n.t("reciter.show_overlay"),
            variable=self.show_reciter_overlay_var,
            command=self.update_preview,
        )
        overlay_chk.pack(anchor="w", pady=(10, 0))
        i18n.bind_widget(overlay_chk, "reciter.show_overlay")

    def _build_background_tab(self, parent) -> None:
        nature_rb = ttk.Radiobutton(
            parent, text=i18n.t("bg.nature"), variable=self.background_mode, value="nature",
            command=self.update_preview,
        )
        nature_rb.pack(anchor="w")
        i18n.bind_widget(nature_rb, "bg.nature")

        # Category filter — Apple segmented control
        self.bg_category_var = tk.StringVar(value="All")
        cats = ("All", "Forests", "Mountains", "Lakes", "Springs", "Other")
        self._bg_segment = SegmentedControl(
            parent,
            on_select=self._filter_backgrounds,
        )
        self._bg_segment.pack(fill="x", padx=(16, 0), pady=(4, 6))
        self._bg_segment.set_options(
            [(c, i18n.category_name(c)) for c in cats],
            active="All",
        )

        nature_row = ttk.Frame(parent, style="Panel.TFrame")
        nature_row.pack(fill="x", padx=(16, 0), pady=(2, 0))
        self.nature_combo = ttk.Combobox(
            nature_row, textvariable=self.nature_background_var, state="readonly", width=26,
        )
        self.nature_combo.pack(side="left", fill="x", expand=True)
        self.nature_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_nature_selected())

        self._bg_preview_label = tk.Label(nature_row, bd=1, relief="flat", bg=BG_INPUT)
        self._bg_preview_label.pack(side="left", padx=(8, 0))
        self._bg_thumb_ref: ImageTk.PhotoImage | None = None

        ttk.Label(
            parent,
            textvariable=self._bg_count_var if hasattr(self, "_bg_count_var") else tk.StringVar(value=""),
            style="Panel.Muted.TLabel",
        ).pack(anchor="w", padx=(16, 0))
        scenery_btns = ttk.Frame(parent, style="Panel.TFrame")
        scenery_btns.pack(anchor="w", fill="x", padx=(16, 0), pady=(4, 0))
        random_btn = ttk.Button(scenery_btns, text=i18n.t("bg.random"), command=self._random_nature)
        random_btn.pack(side="left")
        i18n.bind_widget(random_btn, "bg.random")
        fetch_btn = ttk.Button(scenery_btns, text=i18n.t("bg.fetch_fresh"), command=self._fetch_fresh_scenery)
        fetch_btn.pack(side="left", padx=(8, 0))
        i18n.bind_widget(fetch_btn, "bg.fetch_fresh")

        reciter_rb = ttk.Radiobutton(
            parent, text=i18n.t("bg.reciter"), variable=self.background_mode, value="reciter",
            command=self.update_preview,
        )
        reciter_rb.pack(anchor="w", pady=(10, 0))
        i18n.bind_widget(reciter_rb, "bg.reciter")
        custom_rb = ttk.Radiobutton(
            parent, text=i18n.t("bg.custom"), variable=self.background_mode, value="custom",
            command=self.update_preview,
        )
        custom_rb.pack(anchor="w", pady=(4, 0))
        i18n.bind_widget(custom_rb, "bg.custom")
        custom_row = ttk.Frame(parent, style="Panel.TFrame")
        custom_row.pack(fill="x", padx=(16, 0), pady=(4, 0))
        ttk.Entry(custom_row, textvariable=self.custom_background_var, width=22).pack(
            side="left", fill="x", expand=True
        )
        browse_bg_btn = ttk.Button(custom_row, text=i18n.t("btn.browse"), command=self._browse_custom_background)
        browse_bg_btn.pack(side="left", padx=(8, 0))
        i18n.bind_widget(browse_bg_btn, "btn.browse")

        overlay_row = ttk.Frame(parent, style="Panel.TFrame")
        overlay_row.pack(fill="x", pady=(14, 0))
        overlay_lbl = ttk.Label(overlay_row, text=i18n.t("bg.overlay"), style="Panel.TLabel")
        overlay_lbl.pack(side="left")
        i18n.bind_widget(overlay_lbl, "bg.overlay")
        ttk.Scale(
            overlay_row, from_=0.25, to=0.75, variable=self.overlay_var, orient="horizontal",
            command=lambda _v: self.schedule_preview(),
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _build_layout_tab(self, parent) -> None:
        banner_hdr = ttk.Label(parent, text=i18n.t("banner.title"), style="Panel.Heading.TLabel")
        banner_hdr.pack(anchor="w")
        i18n.bind_widget(banner_hdr, "banner.title")
        banner_hint = ttk.Label(
            parent,
            text=i18n.t("banner.hint"),
            style="Panel.Muted.TLabel",
            wraplength=360,
        )
        banner_hint.pack(anchor="w", pady=(2, 8))
        i18n.bind_widget(banner_hint, "banner.hint")

        self._banner_grid_frame = ttk.Frame(parent, style="Panel.TFrame")
        self._banner_grid_frame.pack(fill="x")
        self._banner_thumb_refs: list[ImageTk.PhotoImage] = []

        upload_btn = ttk.Button(parent, text=i18n.t("banner.upload"), command=self._upload_custom_banner)
        upload_btn.pack(anchor="w", pady=(8, 0))
        i18n.bind_widget(upload_btn, "banner.upload")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(12, 8))
        size_hdr = ttk.Label(parent, text=i18n.t("banner.size"), style="Panel.Heading.TLabel")
        size_hdr.pack(anchor="w", pady=(0, 4))
        i18n.bind_widget(size_hdr, "banner.size")
        self._size_row(parent, "banner.corner_size", self._banner_size_int_var(), 10, 60, 2)

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(12, 8))
        layout_hdr = ttk.Label(parent, text=i18n.t("layout.offset"), style="Panel.Heading.TLabel")
        layout_hdr.pack(anchor="w")
        i18n.bind_widget(layout_hdr, "layout.offset")

        offset_row = ttk.Frame(parent, style="Panel.TFrame")
        offset_row.pack(anchor="w", fill="x", pady=(6, 0))
        x_lbl = ttk.Label(offset_row, text=i18n.t("layout.x_offset"), style="Panel.TLabel", width=8)
        x_lbl.pack(side="left")
        i18n.bind_widget(x_lbl, "layout.x_offset")
        ttk.Spinbox(offset_row, from_=-520, to=520, textvariable=self.text_offset_x_var, width=7,
                    command=self._apply_offset_spinboxes).pack(side="left")
        y_lbl = ttk.Label(offset_row, text=i18n.t("layout.y_offset"), style="Panel.TLabel", width=8)
        y_lbl.pack(side="left", padx=(10, 0))
        i18n.bind_widget(y_lbl, "layout.y_offset")
        ttk.Spinbox(offset_row, from_=-120, to=420, textvariable=self.text_offset_y_var, width=7,
                    command=self._apply_offset_spinboxes).pack(side="left")

        actions = ttk.Frame(parent, style="Panel.TFrame")
        actions.pack(anchor="w", fill="x", pady=(8, 0))
        for key, cmd, pad in [
            ("layout.reset_all", self._reset_layout, 0),
            ("layout.center", self._center_text, 8),
            ("layout.reset_layers", self._reset_element_layers, 8),
        ]:
            btn = ttk.Button(actions, text=i18n.t(key), command=cmd)
            btn.pack(side="left", padx=(pad, 0))
            i18n.bind_widget(btn, key)

    def _build_export_tab(self, parent) -> None:
        preview_btn = ttk.Button(parent, text=i18n.t("export.update_preview"), command=self.update_preview)
        preview_btn.pack(anchor="w")
        i18n.bind_widget(preview_btn, "export.update_preview")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(10, 8))
        quality_hdr = ttk.Label(parent, text=i18n.t("export.quality"), style="Panel.Heading.TLabel")
        quality_hdr.pack(anchor="w")
        i18n.bind_widget(quality_hdr, "export.quality")
        q_frame = ttk.Frame(parent, style="Panel.TFrame")
        q_frame.pack(anchor="w", pady=(6, 0))
        for label_key, val in [
            ("export.hd", 1), ("export.fhd", 2), ("export.4k", 3),
        ]:
            rb = ttk.Radiobutton(q_frame, text=i18n.t(label_key), variable=self.export_scale_var, value=val)
            rb.pack(anchor="w", pady=2)
            i18n.bind_widget(rb, label_key)
        quality_hint = ttk.Label(
            parent,
            text=i18n.t("export.quality_hint"),
            style="Panel.Muted.TLabel",
            wraplength=350,
        )
        quality_hint.pack(anchor="w", pady=(4, 0))
        i18n.bind_widget(quality_hint, "export.quality_hint")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(10, 8))
        export_btn = ttk.Button(parent, text=i18n.t("export.png"), style="Accent.TButton", command=self.export_thumbnail)
        export_btn.pack(anchor="w")
        i18n.bind_widget(export_btn, "export.png")
        batch_btn = ttk.Button(parent, text=i18n.t("export.batch"), command=self.batch_export)
        batch_btn.pack(anchor="w", pady=(8, 0))
        i18n.bind_widget(batch_btn, "export.batch")
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


    def _field(self, parent, label_key: str, variable: tk.StringVar, width: int = 34, handler=None) -> None:
        lbl = ttk.Label(parent, text=i18n.t(label_key), style="Panel.TLabel")
        lbl.pack(anchor="w", pady=(8, 0))
        i18n.bind_widget(lbl, label_key)
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
                    p = palette()
                    tile_bg = p.bg_input if get_theme_mode() == "light" else (30, 30, 35)
                    bg = Image.new("RGB", img.size, tile_bg)
                    bg.paste(img, mask=img.split()[3])
                    bg.thumbnail((THUMB, THUMB), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(bg)
                else:
                    p = palette()
                    none_rgb = (229, 229, 234) if get_theme_mode() == "light" else (40, 40, 45)
                    line_rgb = (174, 174, 178) if get_theme_mode() == "light" else (80, 80, 80)
                    none_img = Image.new("RGB", (THUMB, THUMB), none_rgb)
                    from PIL import ImageDraw as _ID
                    _ID.Draw(none_img).line([(8, 8), (THUMB - 8, THUMB - 8)], fill=line_rgb, width=2)
                    _ID.Draw(none_img).line([(THUMB - 8, 8), (8, THUMB - 8)], fill=line_rgb, width=2)
                    photo = ImageTk.PhotoImage(none_img)
            except Exception:
                photo = None

            selected = (label == current_label)
            p = palette()
            border_color = ACCENT if selected else p.grid_border

            btn_frame = tk.Frame(cell, bg=border_color, bd=0)
            btn_frame.pack()

            if photo:
                self._banner_thumb_refs.append(photo)
                btn = tk.Label(btn_frame, image=photo, cursor="hand2", bd=0,
                               relief="flat", bg=border_color, padx=2, pady=2)
                btn.pack()
            else:
                p = palette()
                btn = tk.Label(
                    btn_frame,
                    text="?",
                    width=6,
                    height=4,
                    bg=p.bg_input,
                    fg=p.grid_muted,
                    cursor="hand2",
                    bd=0,
                )
                btn.pack()

            btn.bind("<Button-1>", lambda _e, lbl=label: self._select_banner(lbl))

            short = label if len(label) <= 14 else label[:13] + "…"
            lbl_widget = tk.Label(cell, text=short, font=("Segoe UI", 7),
                                  bg=BG_PANEL,
                                  fg=ACCENT if selected else p.grid_muted, wraplength=THUMB, justify="center")
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
            title=i18n.t("dialog.banner.upload_title"),
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
                    p = palette()
                    tile_bg = p.bg_input if get_theme_mode() == "light" else (30, 30, 35)
                    bg = Image.new("RGB", (TW, TH), tile_bg)
                    img.thumbnail((TW - 4, TH - 4), Image.Resampling.LANCZOS)
                    ox = (TW - img.width) // 2
                    oy = (TH - img.height) // 2
                    bg.paste(img, (ox, oy), img)
                    photo = ImageTk.PhotoImage(bg)
                else:
                    p = palette()
                    none_rgb = (229, 229, 234) if get_theme_mode() == "light" else (40, 40, 45)
                    line_rgb = (174, 174, 178) if get_theme_mode() == "light" else (80, 80, 80)
                    text_rgb = (142, 142, 147) if get_theme_mode() == "light" else (120, 120, 120)
                    none_img = Image.new("RGB", (TW, TH), none_rgb)
                    from PIL import ImageDraw as _ID
                    d = _ID.Draw(none_img)
                    d.line([(6, TH // 2), (TW - 6, TH // 2)], fill=line_rgb, width=2)
                    d.text((TW // 2 - 12, TH // 2 - 8), "None", fill=text_rgb)
                    photo = ImageTk.PhotoImage(none_img)
            except Exception:
                photo = None

            selected = label == current
            p = palette()
            border = ACCENT if selected else p.grid_border
            btn_frame = tk.Frame(cell, bg=border, bd=0)
            btn_frame.pack()
            if photo:
                self._container_thumb_refs.append(photo)
                btn = tk.Label(btn_frame, image=photo, cursor="hand2", bd=0, bg=border, padx=2, pady=2)
                btn.pack()
            btn.bind("<Button-1>", lambda _e, lbl=label: self._select_name_container(lbl))
            short = label if len(label) <= 22 else label[:21] + "…"
            tk.Label(cell, text=short, font=("Segoe UI", 7), bg=BG_PANEL,
                     fg=ACCENT if selected else p.grid_muted, wraplength=TW + 20, justify="center").pack()

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
            title=i18n.t("dialog.container.upload_title"),
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
            messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.reciter.select_collection"))
            return
        path = filedialog.askopenfilename(
            title=i18n.t("dialog.reciter.photo_title"),
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
        self.english_var.set(i18n.surah_title(surah.number))
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
        current_id = self._current_reciter_id()
        self._reciter_label_to_id = {}
        labels: list[str] = []
        for reciter in self.reciters:
            label = i18n.reciter_name(reciter.id, reciter.name)
            labels.append(label)
            self._reciter_label_to_id[label] = reciter.id
        self.reciter_combo["values"] = labels
        if current_id:
            match = next((r for r in self.reciters if r.id == current_id), None)
            if match:
                localized = i18n.reciter_name(match.id, match.name)
                self.reciter_collection_var.set(localized)
                self.reciter_display_var.set(localized)
        elif labels:
            self.reciter_collection_var.set(labels[0])
            self.reciter_display_var.set(labels[0])
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
        if self._bg_segment is not None:
            self._bg_segment.set_active(category)
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
        self._bg_count_var.set(
            i18n.t(
                "bg.count_one" if count == 1 else "bg.count",
                count=count,
                category=i18n.category_name(category),
            )
        )
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
        self.status_var.set(i18n.t("status.fetching_fresh"))

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
            self.status_var.set(i18n.t("status.fresh_fail"))
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
        self.status_var.set(i18n.t("status.fresh_ok"))

    def _on_reciter_collection_changed(self, _event=None) -> None:
        reciter = self._selected_reciter()
        if reciter:
            self.reciter_display_var.set(i18n.reciter_name(reciter.id, reciter.name))
        self._refresh_reciter_photos()
        self.update_preview()

    def _current_reciter_id(self) -> str | None:
        label = self.reciter_collection_var.get().strip()
        rid = self._reciter_label_to_id.get(label)
        if rid:
            return rid
        for reciter in self.reciters:
            if reciter.name == label:
                return reciter.id
            if i18n.reciter_name(reciter.id, reciter.name) == label:
                return reciter.id
        return None

    def _open_reciter_manager(self) -> None:
        ReciterManagerDialog(self, on_change=self._on_reciters_changed)

    def _on_reciters_changed(self) -> None:
        self._refresh_reciter_options()
        self.update_preview()

    def _browse_custom_background(self) -> None:
        path = filedialog.askopenfilename(
            title=i18n.t("dialog.folder.background"),
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
        rid = self._current_reciter_id()
        if not rid:
            return None
        return next((r for r in self.reciters if r.id == rid), None)

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
                messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.reciter.add_photos_first"))
            return default_nature_background()
        if mode == "custom":
            custom = self.custom_background_var.get().strip()
            if custom and Path(custom).exists():
                return Path(custom)
            if warn:
                messagebox.showwarning(i18n.t("app.title"), i18n.t("msg.bg.choose_valid"))
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
            title_font=self._current_title_font_id(),
            reciter_font=self._current_reciter_font_id(),
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
            self.status_var.set(i18n.t("status.preview"))
        except Exception as exc:
            self.status_var.set(i18n.t("status.preview_error", error=exc))

    def export_thumbnail(self) -> None:
        number = self._parse_surah_number()
        english = self.english_var.get().strip().replace(" ", "_") or "thumbnail"
        default_name = f"{number:03d}_{english}.png" if number else f"{english}.png"
        output = filedialog.asksaveasfilename(
            title=i18n.t("dialog.save_thumbnail"),
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG image", "*.png")],
        )
        if not output:
            return
        scale = int(self.export_scale_var.get())
        dims = {1: "1280×720", 2: "2560×1440", 3: "3840×2160"}.get(scale, "HD")
        self.status_var.set(i18n.t("status.exporting", dims=dims))
        self.update_idletasks()
        try:
            save_thumbnail(self._build_config(warn=True), Path(output), export_scale=scale)
            self.status_var.set(i18n.t("status.saved", dims=dims, path=output))
            messagebox.showinfo(i18n.t("app.title"), i18n.t("msg.export.saved", dims=dims, path=output))
        except Exception as exc:
            messagebox.showerror(i18n.t("app.title"), i18n.t("msg.export.failed", error=exc))

    def batch_export(self) -> None:
        BatchExportDialog(self, self._build_config, int(self.export_scale_var.get()))

    def _language_display_name(self) -> str:
        for code, name_en, native in i18n.language_choices():
            if code == i18n.get_language():
                return f"{native} ({name_en})"
        return i18n.get_language()

    def _change_language(self) -> None:
        code = ask_language(self, initial=i18n.get_language())
        if not code or code == i18n.get_language():
            return
        self._language_was_chosen = True
        i18n.set_language(code)
        self._apply_language()
        self.update_preview()
        try:
            settings_store.save_settings(self._settings_snapshot())
        except Exception:
            pass

    def _apply_language(self) -> None:
        self.title(i18n.t("app.title"))
        if hasattr(self, "_titlebar_label"):
            self._titlebar_label.configure(text=i18n.t("app.title"))
        if hasattr(self, "_theme_btn"):
            self._theme_btn.configure(text=self._theme_button_label())
            i18n.bind_widget(self._theme_btn, self._theme_button_i18n_key())
        i18n.apply_bindings()
        if hasattr(self, "_tab_view") and self._tab_view and self._tab_keys:
            self._tab_view.refresh_labels(lambda key: i18n.t(key))
        if hasattr(self, "_preview_frame"):
            self._preview_frame.configure(text=i18n.t("preview.frame"))
        self._refresh_surah_combo()
        num = self._parse_surah_number()
        if num:
            self.english_var.set(i18n.surah_title(num))
        self._refresh_reciter_options()
        if hasattr(self, "_bg_segment") and self._bg_segment:
            self._bg_segment.refresh_labels(i18n.category_name)
            self._bg_segment.refresh_theme()
        if hasattr(self, "_language_display"):
            self._language_display.set(self._language_display_name())
        if hasattr(self, "bg_category_var"):
            self._apply_bg_category(self.bg_category_var.get())
        self.status_var.set(i18n.t("status.ready"))

    def _refresh_surah_combo(self) -> None:
        current = self._parse_surah_number()
        self.surah_combo["values"] = [surah_label(s) for s in SURAHS]
        if current:
            surah = get_surah(current)
            if surah:
                self._syncing_surah = True
                self.surah_choice_var.set(surah_label(surah))
                self._syncing_surah = False

    def _theme_button_i18n_key(self) -> str:
        return "theme.switch_light" if get_theme_mode() == "dark" else "theme.switch_dark"

    def _theme_button_label(self) -> str:
        return i18n.t(self._theme_button_i18n_key())

    def _toggle_theme(self) -> None:
        toggle_theme_mode()
        self._apply_ui_theme()
        try:
            settings_store.save_settings(self._settings_snapshot())
        except Exception:
            pass

    def _apply_ui_theme(self) -> None:
        apply_theme(self, get_theme_mode())
        if hasattr(self, "_light_backdrop"):
            self._light_backdrop.refresh()
            self.after(150, self._light_backdrop.refresh)
        if hasattr(self, "_left_card"):
            self._left_card.configure(bg=BORDER)
        if hasattr(self, "_preview_card"):
            self._preview_card.configure(bg=BORDER)
        self._refresh_titlebar_theme()
        if hasattr(self, "_tab_view") and self._tab_view:
            self._tab_view.refresh_theme()
            self._scroll_canvases = self._tab_view.scroll_canvases
        if hasattr(self, "_bg_segment") and self._bg_segment:
            self._bg_segment.refresh_theme()
        if hasattr(self, "preview_canvas"):
            self.preview_canvas.configure(bg=BG_INPUT)
        if hasattr(self, "_bg_preview_label"):
            self._bg_preview_label.configure(bg=BG_INPUT)
        if hasattr(self, "_theme_btn"):
            self._theme_btn.configure(text=self._theme_button_label())
        if hasattr(self, "_banner_grid_frame") and self._banner_grid_frame.winfo_children():
            self._build_banner_grid()
        if hasattr(self, "_container_grid_frame") and self._container_grid_frame.winfo_children():
            self._build_container_grid()

    def _refresh_titlebar_theme(self) -> None:
        if not hasattr(self, "_titlebar"):
            return
        for widget in (self._titlebar, getattr(self, "_tb_controls", None), getattr(self, "_titlebar_label", None)):
            if widget is None:
                continue
            try:
                widget.configure(bg=TITLEBAR_BG)
            except tk.TclError:
                pass
        if hasattr(self, "_titlebar_label"):
            self._titlebar_label.configure(fg=TITLEBAR_FG)
        for btn in (getattr(self, "_tb_min", None), getattr(self, "_tb_max", None), getattr(self, "_tb_close", None)):
            if btn is not None:
                btn.configure(bg=TITLEBAR_BG, fg=FG_MUTED)


def _focus_existing_instance() -> bool:
    """Bring an already-running window to the front."""
    if not sys.platform.startswith("win"):
        return False
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        found: list[int] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def callback(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if "Quran Thumbnail Generator" in buf.value:
                found.append(hwnd)
            return True

        user32.EnumWindows(callback, 0)
        if not found:
            return False
        hwnd = found[0]
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def _acquire_single_instance() -> bool:
    """Return False when another copy is already running (and focus it)."""
    if not sys.platform.startswith("win"):
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, True, "Local\\ArthurVlade.QuranThumbnailGenerator")
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            _focus_existing_instance()
            return False
        return True
    except Exception:
        return True


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


def _write_crash_log() -> None:
    import os
    import traceback

    try:
        log_path = base_dir() / "data" / "crash.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        header = f"cwd={os.getcwd()}\nargv={sys.argv}\n\n"
        log_path.write_text(header + traceback.format_exc(), encoding="utf-8")
    except OSError:
        pass


def _install_excepthook() -> None:
    """Log uncaught errors (including Tk callback failures) to data/crash.log."""
    def _hook(exc_type, exc, tb):
        if exc_type is KeyboardInterrupt:
            sys.__excepthook__(exc_type, exc, tb)
            return
        try:
            import traceback
            log_path = base_dir() / "data" / "crash.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            header = f"cwd={os.getcwd()}\nargv={sys.argv}\n\n"
            log_path.write_text(header + "".join(traceback.format_exception(exc_type, exc, tb)), encoding="utf-8")
        except OSError:
            pass
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook


def main() -> None:
    os.chdir(Path(__file__).resolve().parent)
    _install_excepthook()
    if not _acquire_single_instance():
        return
    _set_app_user_model_id()
    ensure_initialized()
    saved = settings_store.load_settings()
    lang = saved.get("language") or "en"
    i18n.set_language(str(lang))
    app = ThumbnailApp()
    app._language_display.set(app._language_display_name())
    app._maybe_download_first_run_assets()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _write_crash_log()
        raise
