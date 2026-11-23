# -*- coding: utf-8 -*-
import ctypes
import tkinter as tk

WIN11_BG = "#202020"
WIN11_CARD = "#2B2B2B"
WIN11_FIELD = "#1F1F1F"
WIN11_BORDER = "#383838"
WIN11_BTN = "#323232"
WIN11_BTN_HOVER = "#3D3D3D"
WIN11_ACCENT = "#0078D4"
WIN11_ACCENT_LIGHT = "#60CDFF"
WIN11_DANGER = "#C42B1C"
WIN11_TEXT = "#FFFFFF"
WIN11_TEXT_SEC = "#A6A6A6"


def apply_win11_window_style(win: tk.Misc):
    """Применяет нативную тёмную шапку Windows 11, скруглённые углы (DWMWCP_ROUND) и фон #202020."""
    try:
        win.configure(bg=WIN11_BG)
    except Exception:
        pass
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
        dwmapi = ctypes.windll.dwmapi
        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        dark = ctypes.c_int(1)
        dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))
        # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
        corner = ctypes.c_int(2)
        dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(corner), ctypes.sizeof(corner))
        # DWMWA_BORDER_COLOR = 34 (#383838)
        border_col = ctypes.c_int(0x00383838)
        dwmapi.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(border_col), ctypes.sizeof(border_col))
    except Exception:
        pass
