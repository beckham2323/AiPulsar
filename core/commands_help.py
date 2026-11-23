from core.ui_widgets import attach_tab_popup_to_main
# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import threading
import tkinter as tk
from core.i18n import get_lang
from core.ui_widgets import RoundedCard, apply_win11_round_corners, bind_child_window_to_parent


class CommandsCheatsheetDialog:
    """Интерактивная шпаргалка голосовых и текстовых команд (клик по команде сразу запускает её)."""

    ACCENT = "#7C4DFF"
    BG_ROOT = "#07090E"
    BG_CARD = "#0D1117"
    BG_ITEM = "#161B22"
    BG_HOVER = "#21262D"

    def __init__(self, root: tk.Widget, on_run_command=None):
        self.root = root
        self.on_run_command = on_run_command
        self._win = None

    def toggle(self):
        if self._win and self._win.winfo_exists():
            self._win.destroy()
            self._win = None
            return
        self.show()

    def show(self):
        is_en = get_lang() == "en"
        win = tk.Toplevel(self.root)
        attach_tab_popup_to_main(self.root if 'self.root'.strip() else None, win)
        win.title("AiPulsar — Commands Cheatsheet" if is_en else "AiPulsar — Шпаргалка команд")
        win.configure(bg=self.BG_ROOT)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        self._win = win

        outer = RoundedCard(win, radius=18, border_color="#383838", bg_color=self.BG_CARD, pad=12, width=830, height=755)
        outer.pack(fill=tk.BOTH, expand=True)
        box = outer.inner

        hdr = tk.Frame(box, bg=self.BG_CARD)
        hdr.pack(fill=tk.X, padx=4, pady=(2, 6))
        title = "?  INTERACTIVE COMMANDS (CLICK ANY TO RUN)" if is_en else "?  ШПАРГАЛКА КОМАНД AIPULSAR (НАЖМИТЕ НА ЛЮБУЮ ДЛЯ ЗАПУСКА)"
        tk.Label(hdr, text=title, bg=self.BG_CARD, fg="#FFFFFF", font=("Segoe UI Semibold", 10)).pack(side=tk.LEFT)
        tk.Button(hdr, text="✕", command=win.destroy, bg=self.BG_CARD, fg="#FFFFFF", activebackground="#1F242D", activeforeground=self.ACCENT, relief=tk.FLAT, font=("Segoe UI Semibold", 10), padx=6, cursor="hand2").pack(side=tk.RIGHT)

        groups = [
            (
                "🖥  УПРАВЛЕНИЕ WINDOWS, ЗАЩИТА И СИСТЕМА (FREE + PRO)" if not is_en else "🖥  WINDOWS, SECURITY & SYSTEM (FREE + PRO)",
                [
                    ("📂 Открой мой компьютер", "Открывает Проводник Windows"),
                    ("🩺 Как чувствует себя компьютер?", "Проверяет загрузку CPU, памяти и место на диске"),
                    ("🧹 Очисти память и временные файлы", "Удаляет мусор Temp и очищает корзину"), ("🗂️ Наведи порядок на Рабочем столе", "Раскладывает файлы по папкам, не трогая ярлыки"),
                    ("🛡️ Проверь безопасность и камеру", "Пульсар-радар проверяет доступ к камере, микрофону и сети"),
                    ("⏰ Напомни через 15 минут проверить почту", "Ставит голосовой таймер-напоминание"),
                    ("🎮 Я играю", "Включает режим тишины «Не беспpulsarить»"), ("🧠 Запомни: мой рабочий проект называется Альфа", "Записывает личное правило в долговременную память"), ("📈 Чему ты научился?", "Показывает статистику самообучения и выученных привычек"),
                ],
            ),
            (
                "✦  УНИКАЛЬНЫЕ СУПЕР-ФИШКИ И ДОКУМЕНТЫ (AIPULSAR PRO)" if not is_en else "✦  SUPER PRO FEATURES & DOCUMENTS (AIPULSAR PRO)",
                [
                    ("🕰️ Включи машину времени экрана", "Запоминает всё, что было на экране за 24 часа (Recall)"),
                    ("🔍 Найди в памяти экрана номер договора", "Мгновенно находит закрытые вкладки, цифры и текст"),
                    ("🎧 Включи суфлёра", "Бесшумно подсказывает ответы в чат во время созвонов"),
                    ("🌐 Создай сайт для кофейни", "Генерирует готовый HTML5-сайт или презентацию за 10 сек"),
                    ("📱 Подключи телефон", "Открывает QR-код Квантового моста (тачпад и телепорт файлов)"),
                    ("🔐 Спрячь секрет в картинку: пароль 1234", "Шифрует секрет внутри PNG-картинки на Рабочем столе"),
                    ("📊 Создай таблицу Excel расходов за месяц", "Генерирует готовый .xlsx или Word (.docx) документ"),
                    ("🖱️ Нажми на кнопку Пуск", "Находит слово на экране через OCR и кликает мышью"), ("⚡ Каждый день в 09:00 открой мой компьютер", "Создаёт автономный авто-скрипт по расписанию"),
                ],
            ),
        ]

        for grp_title, items in groups:
            tk.Label(box, text=grp_title, bg=self.BG_CARD, fg=self.ACCENT, font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=6, pady=(6, 3))
            for cmd_display, desc in items:
                clean_phrase = cmd_display.split(" ", 1)[-1]
                row = tk.Frame(box, bg=self.BG_ITEM, height=28, cursor="hand2")
                row.pack(fill=tk.X, padx=6, pady=2)
                row.pack_propagate(False)

                l_cmd = tk.Label(row, text=f"▸  {cmd_display}", bg=self.BG_ITEM, fg="#FFFFFF", font=("Segoe UI Semibold", 9), anchor="w")
                l_cmd.pack(side=tk.LEFT, padx=(10, 6))

                l_desc = tk.Label(row, text=desc, bg=self.BG_ITEM, fg="#8B949E", font=("Segoe UI", 8), anchor="e")
                l_desc.pack(side=tk.RIGHT, padx=(6, 10))

                def _on_enter(_e, r=row, w1=l_cmd, w2=l_desc):
                    r.config(bg=self.BG_HOVER)
                    w1.config(bg=self.BG_HOVER, fg="#64FFDA")
                    w2.config(bg=self.BG_HOVER, fg="#FFFFFF")

                def _on_leave(_e, r=row, w1=l_cmd, w2=l_desc):
                    r.config(bg=self.BG_ITEM)
                    w1.config(bg=self.BG_ITEM, fg="#FFFFFF")
                    w2.config(bg=self.BG_ITEM, fg="#8B949E")

                def _run(_e, phrase=clean_phrase):
                    win.destroy()
                    if self.on_run_command:
                        threading.Thread(target=self.on_run_command, args=(phrase,), daemon=True).start()

                for w in (row, l_cmd, l_desc):
                    w.bind("<Enter>", _on_enter)
                    w.bind("<Leave>", _on_leave)
                    w.bind("<Button-1>", _run)

        win.update_idletasks()
        apply_win11_round_corners(win)

        def _calc_xy():
            rw = self.root.winfo_width() or 1260
            rh = self.root.winfo_height() or 740
            nx = self.root.winfo_rootx() + (rw - win.winfo_reqwidth()) // 2
            ny = self.root.winfo_rooty() + (rh - win.winfo_reqheight()) // 2
            return (max(16, nx), max(16, ny))

        ix, iy = _calc_xy()
        win.geometry(f"+{ix}+{iy}")
        bind_child_window_to_parent(self.root, win, _calc_xy)
        win.lift()
        win.focus_force()



