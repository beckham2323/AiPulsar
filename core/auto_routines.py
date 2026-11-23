# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import datetime
import json
import os
import re
import shutil
import threading
import time
import psutil
from core.i18n import get_lang


class PulsarAutoRoutinesEngine:
    """Автоматизация AiPulsar: авто-триггер игрового режима, расписание Cron-скриптов и сортировка файлов."""

    GAME_PROCESSES = {
        "cs2.exe", "dota2.exe", "gta5.exe", "rdr2.exe", "cyberpunk2077.exe",
        "witcher3.exe", "valorant.exe", "worldoftanks.exe", "tanksblitz.exe",
        "pubg.exe", "apex.exe", "fortniteclient-win64-shipping.exe", "minecraft.exe",
    }

    EXT_FOLDERS = {
        "Документы": (".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"),
        "Таблицы": (".xls", ".xlsx", ".csv"),
        "Картинки": (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"),
        "Архивы": (".zip", ".rar", ".7z", ".tar", ".gz"),
        "Программы": (".exe", ".msi"),
    }

    def __init__(self, models_dir: str = "models", sys_doc=None, run_cmd_cb=None, notify_cb=None):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.cron_file = os.path.join(self.models_dir, "cron_routines.json")
        self.sys_doc = sys_doc
        self.run_cmd_cb = run_cmd_cb
        self.notify_cb = notify_cb
        self._auto_game_active = False
        self._last_fired_min = ""
        self.tasks = self._load_tasks()
        threading.Thread(target=self._routines_loop, daemon=True).start()

    def _load_tasks(self) -> list:
        if os.path.exists(self.cron_file):
            try:
                with open(self.cron_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_tasks(self):
        try:
            with open(self.cron_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def try_schedule_routine(self, text: str) -> str:
        m = re.search(r"(?:каждый\s+день|ежедневно|every\s+day)\s+(?:в|at)\s+(\d{1,2})[:\.\-](\d{2})\s+(.+)", text.strip(), flags=re.I)
        if not m:
            return ""
        hh = max(0, min(23, int(m.group(1))))
        mm = max(0, min(59, int(m.group(2))))
        action = m.group(3).strip(" .!?")
        time_str = f"{hh:02d}:{mm:02d}"
        self.tasks.append({"time": time_str, "action": action})
        self._save_tasks()
        is_en = get_lang() == "en"
        return (
            f"Auto-script scheduled daily at {time_str}: «{action}»."
            if is_en
            else f"Авто-скрипт создан! Каждый день в {time_str} буду выполнять: «{action}»."
        )

    def organize_folder(self, target: str = "desktop") -> str:
        is_en = get_lang() == "en"
        base_dir = os.path.join(os.path.expanduser("~"), "Downloads" if target == "downloads" else "Desktop")
        if not os.path.isdir(base_dir):
            return "Folder not found." if is_en else "Папка не найдена."

        moved = 0
        for entry in os.scandir(base_dir):
            if not entry.is_file(follow_symlinks=False):
                continue
            low = entry.name.lower()
            if low.endswith((".lnk", ".url", ".ini")):
                continue
            dest_sub = None
            for folder_name, exts in self.EXT_FOLDERS.items():
                if low.endswith(exts):
                    dest_sub = folder_name
                    break
            if dest_sub:
                target_dir = os.path.join(base_dir, dest_sub)
                os.makedirs(target_dir, exist_ok=True)
                dest_path = os.path.join(target_dir, entry.name)
                if os.path.exists(dest_path):
                    stem, ext = os.path.splitext(entry.name)
                    dest_path = os.path.join(target_dir, f"{stem}_{int(time.time())}{ext}")
                try:
                    shutil.move(entry.path, dest_path)
                    moved += 1
                except Exception:
                    pass

        label = "Загрузки" if target == "downloads" else "Рабочем столе"
        if is_en:
            return f"Sorted {moved} files into neat folders."
        return f"Навёл порядок на {label}: разложено файлов по папкам — {moved}."

    def _routines_loop(self):
        while True:
            time.sleep(8.0)
            try:
                # 1. Авто-триггер игрового режима при запуске/закрытии игры
                running_exes = {(p.info.get("name") or "").lower() for p in psutil.process_iter(["name"])}
                game_running = bool(running_exes & self.GAME_PROCESSES)

                if game_running and not self._auto_game_active:
                    self._auto_game_active = True
                    if self.sys_doc and not self.sys_doc.dnd_mode:
                        self.sys_doc.toggle_dnd(True)
                        if self.notify_cb:
                            self.notify_cb("AiPulsar", "🎮 Обнаружен запуск игры — автоматически включён режим тишины «Не беспpulsarить».")
                elif not game_running and self._auto_game_active:
                    self._auto_game_active = False
                    if self.sys_doc and self.sys_doc.dnd_mode:
                        msg = self.sys_doc.toggle_dnd(False)
                        if self.notify_cb:
                            self.notify_cb("AiPulsar", f"🎮 Игра закрыта — {msg}")

                # 2. Выполнение авто-скриптов по расписанию (HH:MM)
                now_hm = datetime.datetime.now().strftime("%H:%M")
                if now_hm != self._last_fired_min:
                    due = [t for t in self.tasks if t.get("time") == now_hm]
                    if due:
                        self._last_fired_min = now_hm
                        for item in due:
                            act = item.get("action", "")
                            if act and self.run_cmd_cb:
                                if self.notify_cb:
                                    self.notify_cb("AiPulsar", f"⚡ Авто-скрипт ({now_hm}): выполняю «{act}»")
                                threading.Thread(target=self.run_cmd_cb, args=(act,), daemon=True).start()
            except Exception:
                pass
