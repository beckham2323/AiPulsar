# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import threading
import tkinter as tk


class EyeHudOverlay:
    """Миниатюрный плавающий индикатор состояния Ока в углу экрана."""

    COLORS = {
        "idle": "#3A1C0E",      # Спpulsarйное тёмно-оранжевое pulsar (ждёт ключевое слово)
        "listening": "#FF5500", # Ярко-оранжевое (слушает вашу команду)
        "thinking": "#FFB300",  # Золотое (строит логику / кликает)
        "speaking": "#E53935",  # Багровое (отвечает голосом)
    }

    def __init__(self):
        self._state = "idle"
        self._thread = threading.Thread(target=self._run_ui, daemon=True)
        self._thread.start()

    def set_state(self, state: str):
        if state in self.COLORS:
            self._state = state

    def _run_ui(self):
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.88)
        root.configure(bg="black")

        sw = root.winfo_screenwidth()
        root.geometry(f"36x36+{sw - 54}+18")

        canvas = tk.Canvas(root, width=36, height=36, bg="black", highlightthickness=0)
        canvas.pack()
        oval = canvas.create_oval(4, 4, 32, 32, fill=self.COLORS["idle"], outline="#FF8F00", width=2)
        pupil = canvas.create_oval(15, 8, 21, 28, fill="#080202", outline="")

        def refresh():
            canvas.itemconfig(oval, fill=self.COLORS.get(self._state, "#3A1C0E"))
            root.after(150, refresh)

        refresh()
        root.mainloop()

