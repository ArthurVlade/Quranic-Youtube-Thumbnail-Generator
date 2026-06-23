"""Windows-specific helpers for a borderless (custom title bar) Tk window.

Keeps a borderless window visible in the taskbar and supports real
minimize/restore via the Win32 API. All functions degrade gracefully on
non-Windows platforms or if the calls fail.
"""

from __future__ import annotations

import sys

_IS_WIN = sys.platform.startswith("win")

# Win32 constants
_GWL_EXSTYLE = -20
_WS_EX_APPWINDOW = 0x00040000
_WS_EX_TOOLWINDOW = 0x00000080
_SW_MINIMIZE = 6
_SPI_GETWORKAREA = 0x0030


def _hwnd(root) -> int:
    import ctypes
    # For an overrideredirect Tk toplevel, winfo_id() is the window HWND itself.
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    return hwnd or root.winfo_id()


def enable_taskbar_icon(root) -> None:
    """Make a borderless window appear in the taskbar with our own icon."""
    if not _IS_WIN:
        return
    try:
        import ctypes
        hwnd = _hwnd(root)
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
        style = (style & ~_WS_EX_TOOLWINDOW) | _WS_EX_APPWINDOW
        user32.SetWindowLongW(hwnd, _GWL_EXSTYLE, style)
        # Re-assert the window so the new style takes effect.
        root.withdraw()
        root.after(10, root.deiconify)
    except Exception:
        pass


def minimize_window(root) -> None:
    if not _IS_WIN:
        try:
            root.iconify()
        except Exception:
            pass
        return
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(_hwnd(root), _SW_MINIMIZE)
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
        ctypes.windll.user32.SystemParametersInfoW(_SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
        return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        return None
