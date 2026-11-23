from core.ui_widgets import attach_tab_popup_to_main
# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import tkinter as tk
from core.i18n import get_lang
from core.ui_widgets import RoundedCard, apply_win11_round_corners

_ACTIVE_CTX_MENU = None


class DarkWin11ContextMenu:
    """Чёрное скруглённое контекстное меню в стиле Windows 11 с рамкой #7C4DFF."""

    BG_CARD = "#0D1117"
    BG_HOVER = "#1F242D"
    ACCENT = "#7C4DFF"
    WHITE = "#FFFFFF"
    MUTED = "#8B949E"

    def __init__(self, widget: tk.Widget, readonly: bool = False):
        self.widget = widget
        self.readonly = readonly

    def _close_existing(self):
        global _ACTIVE_CTX_MENU
        if _ACTIVE_CTX_MENU and _ACTIVE_CTX_MENU.winfo_exists():
            try:
                _ACTIVE_CTX_MENU.destroy()
            except Exception:
                pass
        _ACTIVE_CTX_MENU = None

    def show(self, event):
        global _ACTIVE_CTX_MENU
        self._close_existing()
        self.widget.focus_force()

        is_en = get_lang() == "en"
        items = []
        if not self.readonly:
            items.append(("Cut" if is_en else "Вырезать", "Ctrl+X", lambda: _do_cut(self.widget)))
        items.append(("Copy" if is_en else "Копировать", "Ctrl+C", lambda: _do_copy(self.widget)))
        if not self.readonly:
            items.append(("Paste" if is_en else "Вставить", "Ctrl+V", lambda: _do_paste(self.widget)))
            items.append(("Delete" if is_en else "Удалить", "Del", lambda: _do_delete(self.widget)))
        items.append(("SEP", "", None))
        items.append(("Select All" if is_en else "Выделить всё", "Ctrl+A", lambda: _do_select_all(self.widget)))

        row_count = sum(1 for lbl, _, _ in items if lbl != "SEP")
        sep_count = sum(1 for lbl, _, _ in items if lbl == "SEP")
        total_h = row_count * 30 + sep_count * 9 + 14

        popup = tk.Toplevel(self.widget)

        attach_tab_popup_to_main(self.widget if 'self.widget'.strip() else None, popup)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#07090E")
        _ACTIVE_CTX_MENU = popup

        card = RoundedCard(popup, radius=14, border_color="#383838", bg_color=self.BG_CARD, pad=6, width=215, height=total_h)
        card.pack(fill=tk.BOTH, expand=True)
        box = card.inner

        for label, shortcut, cmd in items:
            if label == "SEP":
                tk.Frame(box, bg="#21262D", height=1).pack(fill=tk.X, padx=6, pady=4)
                continue

            row = tk.Frame(box, bg=self.BG_CARD, height=28, cursor="hand2")
            row.pack(fill=tk.X, padx=2, pady=1)
            row.pack_propagate(False)

            lbl_l = tk.Label(row, text=label, bg=self.BG_CARD, fg=self.WHITE, font=("Segoe UI", 9), anchor="w")
            lbl_l.pack(side=tk.LEFT, padx=(10, 4))

            lbl_r = tk.Label(row, text=shortcut, bg=self.BG_CARD, fg=self.MUTED, font=("Consolas", 8), anchor="e")
            lbl_r.pack(side=tk.RIGHT, padx=(4, 10))

            def _on_enter(_e, r=row, l1=lbl_l, l2=lbl_r):
                r.config(bg=self.BG_HOVER)
                l1.config(bg=self.BG_HOVER, fg=self.WHITE)
                l2.config(bg=self.BG_HOVER, fg=self.ACCENT)

            def _on_leave(_e, r=row, l1=lbl_l, l2=lbl_r):
                r.config(bg=self.BG_CARD)
                l1.config(bg=self.BG_CARD, fg=self.WHITE)
                l2.config(bg=self.BG_CARD, fg=self.MUTED)

            def _on_click(_e, action=cmd):
                self._close_existing()
                if action:
                    action()

            for w in (row, lbl_l, lbl_r):
                w.bind("<Enter>", _on_enter)
                w.bind("<Leave>", _on_leave)
                w.bind("<Button-1>", _on_click)

        popup.update_idletasks()
        apply_win11_round_corners(popup)
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        px = min(event.x_root, sw - 225)
        py = min(event.y_root, sh - total_h - 15)
        popup.geometry(f"+{max(4, px)}+{max(4, py)}")
        popup.bind("<FocusOut>", lambda _e: self._close_existing())
        popup.bind("<Escape>", lambda _e: self._close_existing())
        popup.focus_force()


def _do_copy(widget: tk.Widget):
    try:
        sel = widget.selection_get()
        if sel:
            widget.clipboard_clear()
            widget.clipboard_append(sel)
    except Exception:
        pass


def _do_cut(widget: tk.Widget):
    _do_copy(widget)
    _do_delete(widget)


def _do_paste(widget: tk.Widget):
    try:
        txt = widget.clipboard_get()
    except Exception:
        return
    if not txt:
        return
    try:
        if isinstance(widget, tk.Text):
            try:
                widget.delete("sel.first", "sel.last")
            except Exception:
                pass
            widget.insert(tk.INSERT, txt)
        else:
            try:
                widget.delete("sel.first", "sel.last")
            except Exception:
                pass
            widget.insert(tk.INSERT, txt)
    except Exception:
        pass


def _do_delete(widget: tk.Widget):
    try:
        widget.delete("sel.first", "sel.last")
    except Exception:
        pass


def _do_select_all(widget: tk.Widget):
    try:
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
        else:
            widget.select_range(0, tk.END)
            widget.icursor(tk.END)
    except Exception:
        pass


def enable_clipboard_and_menu(widget: tk.Widget, readonly: bool = False):
    """Горячие клавиши Ctrl+C/V/X/A в любой раскладке (RU/EN) и чёрное скруглённое меню ПКМ."""
    menu = DarkWin11ContextMenu(widget, readonly=readonly)
    widget.bind("<Button-1>", lambda _e: widget.focus_force(), add="+")
    widget.bind("<Button-3>", menu.show, add="+")

    def _on_ctrl_key(event):
        if not (event.state & 0x4):
            return None
        code = int(getattr(event, "keycode", 0))
        if code == 67:  # C / С
            _do_copy(widget)
            return "break"
        if code == 86 and not readonly:  # V / М
            _do_paste(widget)
            return "break"
        if code == 88 and not readonly:  # X / Ч
            _do_cut(widget)
            return "break"
        if code == 65:  # A / Ф
            _do_select_all(widget)
            return "break"
        return None

    widget.bind("<KeyPress>", _on_ctrl_key, add="+")

