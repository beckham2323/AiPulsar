# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import ast
import operator
import os
import shutil
import threading
import time
import pyperclip
from typing import Callable


class AdvancedSkills:
    """Продвинутые навыки: точные вычисления, буфер обмена, фоновые напоминания и сортировка файлов."""

    EXT_MAP = {
        "Документы": (".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".pptx", ".rtf", ".csv"),
        "Изображения": (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"),
        "Архивы": (".zip", ".rar", ".7z", ".tar", ".gz"),
        "Программы": (".exe", ".msi"),
        "Медиа": (".mp3", ".wav", ".mp4", ".avi", ".mkv"),
    }

    def __init__(self, speak_callback: Callable[[str], None] = None):
        self.speak_callback = speak_callback

    def read_clipboard(self) -> str:
        text = (pyperclip.paste() or "").strip()
        if not text:
            return "Буфер обмена сейчас пуст."
        return f"Содержимое буфера обмена ({len(text)} симв.):\n{text[:3000]}"

    def write_clipboard(self, text: str) -> str:
        pyperclip.copy(text)
        return "Готовый текст скопирован в буфер обмена (можно вставить через Ctrl+V)."

    def calculate_math(self, expression: str) -> str:
        """Безопасный точный математический расчёт без ошибок нейросети."""
        expr = (expression or "").replace(",", ".").replace("^", "**").strip()
        allowed_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def _eval(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            if isinstance(node, ast.BinOp) and type(node.op) in allowed_ops:
                return allowed_ops[type(node.op)](_eval(node.left), _eval(node.right))
            if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_ops:
                return allowed_ops[type(node.op)](_eval(node.operand))
            raise ValueError("Неподдерживаемая операция")

        try:
            tree = ast.parse(expr, mode="eval")
            result = _eval(tree.body)
            formatted = f"{result:.4f}".rstrip("0").rstrip(".") if isinstance(result, float) else str(result)
            return f"Точный результат расчёта ({expr}) = {formatted}"
        except Exception as e:
            return f"Не удалось вычислить выражение «{expression}»: {e}"

    def set_reminder(self, minutes: float, message: str) -> str:
        mins = max(0.1, float(minutes))
        msg = (message or "Пора выполнить запланированное дело").strip()

        def _timer_worker():
            time.sleep(mins * 60)
            alert = f"Напоминание! Вы просили напомнить: {msg}"
            print(f"⏰ {alert}")
            if self.speak_callback:
                self.speak_callback(alert)

        threading.Thread(target=_timer_worker, daemon=True).start()
        return f"Таймер установлен на {mins} мин. Напомню: «{msg}»."

    def organize_folder(self, folder_name: str) -> str:
        key = (folder_name or "").lower().strip()
        target_dir = (
            os.path.join(os.path.expanduser("~"), "Desktop")
            if "рабоч" in key
            else os.path.join(os.path.expanduser("~"), "Downloads")
        )
        if not os.path.exists(target_dir):
            return "Указанная папка не найдена."

        moved = 0
        for item in os.listdir(target_dir):
            full_path = os.path.join(target_dir, item)
            if not os.path.isfile(full_path) or item.endswith(".lnk"):
                continue
            ext = os.path.splitext(item)[1].lower()
            for cat, exts in self.EXT_MAP.items():
                if ext in exts:
                    dest_folder = os.path.join(target_dir, cat)
                    os.makedirs(dest_folder, exist_ok=True)
                    shutil.move(full_path, os.path.join(dest_folder, item))
                    moved += 1
                    break
        return f"Порядок наведён: рассортировано файлов по категориям — {moved} шт."

