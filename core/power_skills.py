# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import os
import subprocess
from pathlib import Path


class PowerSkills:
    """Поиск локальных файлов, системные папки и управление режимами работы ассистента."""

    FOLDERS_MAP = {
        "загрузки": os.path.join(os.path.expanduser("~"), "Downloads"),
        "документы": os.path.join(os.path.expanduser("~"), "Documents"),
        "рабочий стол": os.path.join(os.path.expanduser("~"), "Desktop"),
        "изображения": os.path.join(os.path.expanduser("~"), "Pictures"),
        "музыка": os.path.join(os.path.expanduser("~"), "Music"),
    }

    def find_and_open(self, query: str) -> str:
        q = (query or "").lower().strip()
        if not q:
            return "Не указано имя файла или папки."

        for name, path in self.FOLDERS_MAP.items():
            if name in q and os.path.exists(path):
                os.startfile(path)
                return f"Открыл папку «{name}»."

        search_roots = [
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.expanduser("~"), "Documents"),
            os.path.join(os.path.expanduser("~"), "Downloads"),
            "D:\\",
        ]
        for root_dir in search_roots:
            if not os.path.exists(root_dir):
                continue
            for dirpath, dirnames, filenames in os.walk(root_dir):
                # Пропускаем системные и скрытые папки для высpulsarй скорости
                dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("Windows", "Program Files", "Program Files (x86)", "$RECYCLE.BIN", "System Volume Information", ".venv")]
                for fn in filenames:
                    if q in fn.lower():
                        full_path = os.path.join(dirpath, fn)
                        os.startfile(full_path)
                        return f"Нашёл и открыл файл: {fn}"

        return f"Файл или папка «{query}» не найдены."

