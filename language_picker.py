"""Language selection dialog for first launch and in-app changes."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import i18n
from ui_theme import BG_DARK, BG_PANEL, FG_PRIMARY, FONT_HEADING, apply_theme


class LanguagePickerDialog(tk.Toplevel):
    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str | None = None,
        prompt: str | None = None,
        initial: str | None = None,
        required: bool = False,
    ) -> None:
        super().__init__(master)
        self.result: str | None = initial or i18n.get_language()
        self._required = required
        self.title(title or i18n.t("language.title"))
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.minsize(520, 420)
        self.transient(master)
        self.grab_set()

        if prompt is None:
            prompt = i18n.t("language.prompt")

        frame = ttk.Frame(self, padding=16, style="Panel.TFrame")
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=prompt, style="Panel.Heading.TLabel", wraplength=480).pack(anchor="w")

        search_row = ttk.Frame(frame, style="Panel.TFrame")
        search_row.pack(fill="x", pady=(12, 8))
        ttk.Label(search_row, text=i18n.t("language.search"), style="Panel.TLabel").pack(side="left")
        self._search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self._search_var, width=32)
        search_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)
        self._search_var.trace_add("write", lambda *_: self._filter_list())

        list_frame = ttk.Frame(frame, style="Panel.TFrame")
        list_frame.pack(fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical")
        self._list = tk.Listbox(
            list_frame,
            activestyle="none",
            bg=BG_PANEL,
            fg=FG_PRIMARY,
            selectbackground="#d4af37",
            selectforeground="#111111",
            highlightthickness=0,
            borderwidth=0,
            font=("Segoe UI", 10),
            yscrollcommand=scroll.set,
        )
        scroll.config(command=self._list.yview)
        self._list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self._choices: list[tuple[str, str, str]] = i18n.language_choices()
        self._display_to_code: dict[str, str] = {}
        self._populate(self._choices)

        if initial:
            for idx, (code, _en, native) in enumerate(self._choices):
                if code == initial:
                    self._list.selection_set(idx)
                    self._list.see(idx)
                    break

        self._list.bind("<Double-Button-1>", lambda _e: self._confirm())
        self._list.bind("<Return>", lambda _e: self._confirm())

        buttons = ttk.Frame(frame, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text=i18n.t("language.continue_btn"), style="Accent.TButton", command=self._confirm).pack(side="right")
        if not required:
            ttk.Button(buttons, text=i18n.t("btn.cancel"), command=self._cancel).pack(side="right", padx=(0, 8))

        self.geometry("560x480")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        search_entry.focus_set()
        self._present()

    def _present(self) -> None:
        """Ensure the dialog is visible and centered (fixes hidden first-run picker on Windows)."""
        self.update_idletasks()
        w, h = 560, 480
        x = max(0, (self.winfo_screenwidth() - w) // 2)
        y = max(0, (self.winfo_screenheight() - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(250, lambda: self.attributes("-topmost", False))
        if self._list.size() and not self._list.curselection():
            self._list.selection_set(0)
            self._list.see(0)

    def _populate(self, choices: list[tuple[str, str, str]]) -> None:
        self._list.delete(0, tk.END)
        self._display_to_code.clear()
        for code, name_en, native in choices:
            label = f"{native}  ({name_en})"
            self._display_to_code[label] = code
            self._list.insert(tk.END, label)

    def _filter_list(self) -> None:
        q = self._search_var.get().strip().lower()
        if not q:
            self._populate(self._choices)
            return
        filtered = [
            item for item in self._choices
            if q in item[0].lower() or q in item[1].lower() or q in item[2].lower()
        ]
        self._populate(filtered)

    def _confirm(self) -> None:
        sel = self._list.curselection()
        if not sel:
            return
        label = self._list.get(sel[0])
        self.result = self._display_to_code.get(label)
        if self.result:
            self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()

    def _on_close(self) -> None:
        if self._required:
            return
        self._cancel()


def ask_language(
    master: tk.Misc,
    *,
    initial: str | None = None,
    required: bool = False,
    title: str | None = None,
    prompt: str | None = None,
) -> str | None:
    if not i18n.language_codes() or i18n.language_codes() == ["en"]:
        i18n.set_language("en")
        return "en"
    dlg = LanguagePickerDialog(
        master,
        initial=initial,
        required=required,
        title=title,
        prompt=prompt,
    )
    master.wait_window(dlg)
    return dlg.result


def pick_startup_language() -> str:
    """Blocking first-run language picker using a standalone window."""
    root = tk.Tk()
    apply_theme(root)
    i18n.set_language("en")
    root.withdraw()
    code = ask_language(root, required=True, initial="en")
    try:
        root.destroy()
    except tk.TclError:
        pass
    return code or "en"
