"""Windows-specific helpers for a borderless (custom title bar) Tk window.

Strips the native caption from the Win32 shell HWND (parent of winfo_id) while
keeping WS_EX_APPWINDOW so the app stays on the taskbar. Styles are applied
once — repeated SetWindowPos/ShowWindow calls were leaving orphan system-menu
controls on the desktop.
"""

from __future__ import annotations

import sys
from pathlib import Path

_IS_WIN = sys.platform.startswith("win")

_GWL_STYLE = -16
_GWL_EXSTYLE = -20
_WS_CAPTION = 0x00C00000
_WS_THICKFRAME = 0x00040000
_WS_SYSMENU = 0x00080000
_WS_MINIMIZEBOX = 0x00020000
_WS_MAXIMIZEBOX = 0x00010000
_WS_EX_APPWINDOW = 0x00040000
_WS_EX_TOOLWINDOW = 0x00000080
_SW_MINIMIZE = 6
_SPI_GETWORKAREA = 0x0030
_SWP_NOMOVE = 0x0002
_SWP_NOSIZE = 0x0001
_SWP_NOZORDER = 0x0004
_SWP_FRAMECHANGED = 0x0020
_WM_SETICON = 0x0080
_ICON_SMALL = 0
_ICON_BIG = 1
_IMAGE_ICON = 1
_LR_LOADFROMFILE = 0x0010
_STRIP_STYLE = _WS_CAPTION | _WS_THICKFRAME | _WS_SYSMENU | _WS_MINIMIZEBOX | _WS_MAXIMIZEBOX


def _user32():
    import ctypes
    return ctypes.windll.user32


def _get_set_window_long():
    import ctypes
    user32 = _user32()
    if ctypes.sizeof(ctypes.c_void_p) == 8:
        return user32.GetWindowLongPtrW, user32.SetWindowLongPtrW
    return user32.GetWindowLongW, user32.SetWindowLongW


def shell_hwnd(root) -> int:
    """Return the Win32 shell HWND that owns the taskbar button for a Tk root."""
    if not _IS_WIN:
        return 0
    try:
        root.update_idletasks()
        wid = int(root.winfo_id())
        if not wid:
            return 0
        parent = int(_user32().GetParent(wid))
        return parent if parent else wid
    except Exception:
        return 0


def _icon_path() -> Path | None:
    try:
        from app_paths import base_dir
        ico = base_dir() / "assets" / "icon.ico"
        return ico if ico.exists() else None
    except Exception:
        return None


def _apply_hwnd_icon(hwnd: int, ico_path: Path) -> None:
    if not _IS_WIN or not hwnd or not ico_path.exists():
        return
    try:
        user32 = _user32()
        for size, slot in ((32, _ICON_BIG), (16, _ICON_SMALL)):
            hicon = user32.LoadImageW(
                None,
                str(ico_path),
                _IMAGE_ICON,
                size,
                size,
                _LR_LOADFROMFILE,
            )
            if hicon:
                user32.SendMessageW(hwnd, _WM_SETICON, slot, hicon)
    except Exception:
        pass


def _purge_system_menu(hwnd: int) -> None:
    """Reset the system menu after stripping WS_SYSMENU (avoids orphan Close controls)."""
    if not hwnd:
        return
    try:
        _user32().GetSystemMenu(hwnd, True)
    except Exception:
        pass


def apply_borderless_shell(root, *, force: bool = False) -> None:
    """Remove native title bar while keeping a normal taskbar presence."""
    if not _IS_WIN:
        return
    if getattr(root, "_win_shell_applied", False) and not force:
        return
    try:
        hwnd = shell_hwnd(root)
        if not hwnd:
            return

        get_long, set_long = _get_set_window_long()
        user32 = _user32()

        style = get_long(hwnd, _GWL_STYLE)
        style &= ~_STRIP_STYLE
        set_long(hwnd, _GWL_STYLE, style)
        _purge_system_menu(hwnd)

        exstyle = get_long(hwnd, _GWL_EXSTYLE)
        exstyle = (exstyle & ~_WS_EX_TOOLWINDOW) | _WS_EX_APPWINDOW
        set_long(hwnd, _GWL_EXSTYLE, exstyle)

        user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOZORDER | _SWP_FRAMECHANGED,
        )

        title = root.title() or "Quran Thumbnail Generator"
        user32.SetWindowTextW(hwnd, title)

        ico = _icon_path()
        if ico:
            _apply_hwnd_icon(hwnd, ico)

        root._win_shell_applied = True  # type: ignore[attr-defined]
    except Exception:
        pass


def enable_taskbar_icon(root) -> None:
    apply_borderless_shell(root, force=True)


def register_taskbar_hooks(root) -> None:
    """Re-apply shell styles after restore from minimize (not on first show)."""
    if not _IS_WIN:
        return

    root._win_shell_map_count = 0  # type: ignore[attr-defined]

    def _on_map(event) -> None:
        if event.widget is not root:
            return
        root._win_shell_map_count = getattr(root, "_win_shell_map_count", 0) + 1  # type: ignore[attr-defined]
        if root._win_shell_map_count < 2:  # type: ignore[attr-defined]
            return
        job = getattr(root, "_win_shell_map_job", None)
        if job:
            try:
                root.after_cancel(job)
            except Exception:
                pass

        def _reapply() -> None:
            root._win_shell_applied = False  # type: ignore[attr-defined]
            apply_borderless_shell(root, force=True)

        root._win_shell_map_job = root.after(120, _reapply)  # type: ignore[attr-defined]

    root.bind("<Map>", _on_map, add="+")


def minimize_window(root) -> None:
    if not _IS_WIN:
        try:
            root.iconify()
        except Exception:
            pass
        return
    try:
        _user32().ShowWindow(shell_hwnd(root), _SW_MINIMIZE)
    except Exception:
        try:
            root.iconify()
        except Exception:
            pass


def get_work_area() -> tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) of the screen excluding the taskbar."""
    if not _IS_WIN:
        return None
    try:
        import ctypes
        from ctypes import wintypes
        rect = wintypes.RECT()
        _user32().SystemParametersInfoW(_SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
        return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        return None


def titlebar_control_inset(maximized: bool) -> int:
    """Right padding so custom window controls stay visible when maximized."""
    if not maximized or not _IS_WIN:
        return 0
    return 14


def maximize_geometry(root) -> str | None:
    """Return a geometry string that fills the monitor work area."""
    area = get_work_area()
    if not area:
        return None
    left, top, right, bottom = area
    return f"{right - left}x{bottom - top}+{left}+{top}"
