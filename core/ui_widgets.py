
import tkinter as _tk_mod

_GLOBAL_ACTIVE_POPUP = None
_ORIG_TOPLEVEL_INIT = _tk_mod.Toplevel.__init__

def _single_popup_toplevel_init(self, master=None, cnf={}, **kw):
    global _GLOBAL_ACTIVE_POPUP
    try:
        if _GLOBAL_ACTIVE_POPUP is not None and _GLOBAL_ACTIVE_POPUP is not self:
            if _GLOBAL_ACTIVE_POPUP.winfo_exists():
                _GLOBAL_ACTIVE_POPUP.destroy()
    except Exception:
        pass
    _ORIG_TOPLEVEL_INIT(self, master=master, cnf=cnf, **kw)
    _GLOBAL_ACTIVE_POPUP = self
    def _safe_bind_transient():
        try:
            if not self.winfo_exists():
                return
            root_w = (master or _tk_mod._default_root)
            if root_w is not None:
                top_root = root_w.winfo_toplevel()
                if top_root is not self and not self.overrideredirect():
                    self.transient(top_root)
            self.lift()
            self.focus_force()
        except Exception:
            pass
    try:
        self.after(20, _safe_bind_transient)
    except Exception:
        pass

if getattr(_tk_mod.Toplevel.__init__, "__name__", "") != "_single_popup_toplevel_init":
    _tk_mod.Toplevel.__init__ = _single_popup_toplevel_init

# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import ctypes
import tkinter as tk


def apply_win11_round_corners(win: tk.Misc):
    try:
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(DWMWCP_ROUND), ctypes.sizeof(DWMWCP_ROUND)
        )
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        dark = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(dark), ctypes.sizeof(dark)
        )
    except Exception:
        pass


def bind_child_window_to_parent(parent: tk.Misc, child: tk.Toplevel, calc_xy_fn):
    """Жёстко привязывает любое дочернее окно к главному окну приложения (движение, сворачивание и поверх родителя)."""
    try:
        child.transient(parent.winfo_toplevel())
    except Exception:
        pass

    def _sync(_event=None):
        try:
            if not child.winfo_exists():
                return
            nx, ny = calc_xy_fn()
            child.geometry(f"+{int(nx)}+{int(ny)}")
        except Exception:
            pass

    root_top = parent.winfo_toplevel()
    bind_id = root_top.bind("<Configure>", _sync, add="+")

    def _on_destroy(_event=None):
        try:
            root_top.unbind("<Configure>", bind_id)
        except Exception:
            pass

    child.bind("<Destroy>", _on_destroy, add="+")


class RoundedCard(tk.Frame):
    """Строгая нативная панель Windows без ярких рамок (тонкая системная граница 1px #383838)."""

    def __init__(self, parent: tk.Widget, radius: int = 6, border_color: str = "#383838", bg_color: str = "#252526", pad: int = 8, width: int = 0, height: int = 0):
        super().__init__(
            parent,
            bg=bg_color,
            highlightbackground="#383838",
            highlightcolor="#383838",
            highlightthickness=1,
            bd=0,
        )
        if width > 0 and height > 0:
            self.configure(width=width, height=height)
            self.pack_propagate(False)
        self.inner = tk.Frame(self, bg=bg_color)
        self.inner.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)


_ACTIVE_AIPULSAR_POPUP = None



_ACTIVE_TAB_POPUP = None

def attach_tab_popup_to_main(parent, win):
    """Привязывает дочернее окно к главному окну AiPulsar и автоматически закрывает предыдущее открытое окно."""
    global _ACTIVE_TAB_POPUP
    try:
        if _ACTIVE_TAB_POPUP is not None and _ACTIVE_TAB_POPUP is not win:
            if _ACTIVE_TAB_POPUP.winfo_exists():
                _ACTIVE_TAB_POPUP.destroy()
    except Exception:
        pass
    _ACTIVE_TAB_POPUP = win

    if parent is None:
        return
    try:
        root_win = parent.winfo_toplevel()
        win.transient(root_win)

        def _sync_move(event=None):
            try:
                if not win.winfo_exists():
                    return
                if root_win.state() == "iconic":
                    win.withdraw()
                else:
                    if win.state() == "withdrawn":
                        win.deiconify()
                    rx, ry = root_win.winfo_rootx(), root_win.winfo_rooty()
                    rw, rh = root_win.winfo_width(), root_win.winfo_height()
                    ww, wh = win.winfo_width(), win.winfo_height()
                    if ww > 50 and wh > 50:
                        nx = rx + max(20, (rw - ww) // 2)
                        ny = ry + max(20, (rh - wh) // 2)
                        win.geometry(f"+{nx}+{ny}")
            except Exception:
                pass

        bind_id = root_win.bind("<Configure>", _sync_move, add="+")
        unmap_id = root_win.bind("<Unmap>", _sync_move, add="+")
        map_id = root_win.bind("<Map>", _sync_move, add="+")

        def _on_close():
            global _ACTIVE_TAB_POPUP
            try:
                root_win.unbind("<Configure>", bind_id)
                root_win.unbind("<Unmap>", unmap_id)
                root_win.unbind("<Map>", map_id)
            except Exception:
                pass
            if _ACTIVE_TAB_POPUP is win:
                _ACTIVE_TAB_POPUP = None
            try:
                win.destroy()
            except Exception:
                pass

        win.protocol("WM_DELETE_WINDOW", _on_close)
    except Exception:
        pass
