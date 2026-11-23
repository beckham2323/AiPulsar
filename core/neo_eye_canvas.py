# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import tkinter as tk


class NeoEyeCanvas:
    """Минималистичная заглушка: графическая панель и телеметрия отключены для строгого делового стиля."""

    def __init__(self, parent: tk.Widget):
        self.canvas = tk.Canvas(parent, bg="#0B0E14", highlightthickness=0, bd=0, width=1, height=1)

    def set_large_mode(self, flag: bool, w: int = 0, h: int = 0):
        pass

    def render(self, state: str = "idle"):
        pass
