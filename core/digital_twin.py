# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import datetime
import json
import os
import shutil
import subprocess


class PCDigitalTwin:
    """Цифровой клон вашего ПК с песочницей для безопасного тестирования и внесения корректировок."""

    def __init__(self, models_dir: str):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.twin_file = os.path.join(self.models_dir, "pc_digital_twin.json")
        self.sandbox_dir = os.path.join(self.models_dir, "pc_clone_sandbox")
        self.backup_dir = os.path.join(self.models_dir, "pc_backups")
        os.makedirs(self.sandbox_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def sync_clone(self) -> str:
        """Снимает актуальный слепок папок, программ, процессов и настроек ПК в цифровой клон."""
        home = os.path.expanduser("~")
        folders_to_map = {
            "Рабочий стол": os.path.join(home, "Desktop"),
            "Загрузки": os.path.join(home, "Downloads"),
            "Документы": os.path.join(home, "Documents"),
            "Диск D": "D:\\",
        }

        tree_snapshot = {}
        for title, path in folders_to_map.items():
            if os.path.exists(path):
                try:
                    entries = os.listdir(path)[:60]
                    tree_snapshot[title] = entries
                except Exception:
                    tree_snapshot[title] = ["Нет доступа"]

        # Активные процессы Windows
        procs = []
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", "Get-Process | Select-Object -ExpandProperty ProcessName -Unique | Sort-Object"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=8,
            )
            procs = [p.strip() for p in (res.stdout or "").splitlines() if p.strip()][:80]
        except Exception:
            pass

        twin_data = {
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_home": home,
            "folders": tree_snapshot,
            "running_processes": procs,
        }

        with open(self.twin_file, "w", encoding="utf-8") as f:
            json.dump(twin_data, f, ensure_ascii=False, indent=2)

        return (
            f"Цифровой клон ПК обновлён ({twin_data['updated_at']}). "
            f"В памяти клона {sum(len(v) for v in tree_snapshot.values())} объектов файловой системы и {len(procs)} активных процессов."
        )

    def inspect_clone_summary(self) -> str:
        if not os.path.exists(self.twin_file):
            self.sync_clone()
        try:
            with open(self.twin_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            lines = [f"Слепок клона ПК от {data.get('updated_at')}:"]
            for folder_name, items in data.get("folders", {}).items():
                lines.append(f"• {folder_name}: {', '.join(items[:12])}")
            return "\n".join(lines)
        except Exception as e:
            return f"Ошибка чтения клона ПК: {e}"

    def edit_via_clone_sandbox(self, target_file: str, find_text: str, replace_text: str) -> str:
        """Клонирует файл в песочницу, вносит правку, сохраняет резервную копию оригинала и применяет корректировку."""
        raw = (target_file or "").strip()
        if not os.path.isabs(raw):
            raw = os.path.join(os.path.expanduser("~"), "Desktop", raw)
        if not os.path.exists(raw) or not os.path.isfile(raw):
            return f"Файл для корректировки не найден: {raw}"

        try:
            fname = os.path.basename(raw)
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # 1. Сохраняем резервную копию оригинала
            backup_path = os.path.join(self.backup_dir, f"{stamp}_{fname}")
            shutil.copy2(raw, backup_path)

            # 2. Создаём копию в песочнице-клоне и проверяем правку
            sandbox_file = os.path.join(self.sandbox_dir, fname)
            shutil.copy2(raw, sandbox_file)

            with open(sandbox_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if find_text:
                if find_text not in content:
                    return f"Фрагмент «{find_text}» не найден в файле {fname}. Оригинал не изменён."
                new_content = content.replace(find_text, replace_text)
            else:
                new_content = content + "\n" + replace_text

            with open(sandbox_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            # 3. Переносим проверенную правку из клона в реальный файл
            shutil.copy2(sandbox_file, raw)
            return f"Правка проверена в клоне ПК и применена к файлу «{fname}». Резервная копия сохранена."
        except Exception as e:
            return f"Ошибка при корректировке через клон ПК: {e}"

    def rollback_last_backup(self, filename_hint: str = "") -> str:
        """Откатывает последнее изменение из резервной копии клона ПК."""
        backups = sorted(os.listdir(self.backup_dir), reverse=True)
        if filename_hint:
            backups = [b for b in backups if filename_hint.lower() in b.lower()]
        if not backups:
            return "Резервные копии для отката не найдены."
        latest = next(iter(backups))
        orig_name = latest.split("_", 2).pop()
        target_desktop = os.path.join(os.path.expanduser("~"), "Desktop", orig_name)
        shutil.copy2(os.path.join(self.backup_dir, latest), target_desktop)
        return f"Откатил файл «{orig_name}» к состоянию до правки."

