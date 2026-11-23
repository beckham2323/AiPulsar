# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import re
import os
import shutil
import subprocess
import zipfile


class PCFullAccess:
    """Полный доступ к системному поиску Windows, всем папкам/дискам и всем настройкам Windows."""

    SETTINGS_MAP = {
        "звук": "ms-settings:sound",
        "микрофон": "ms-settings:privacy-microphone",
        "наушники": "ms-settings:sound",
        "bluetooth": "ms-settings:bluetooth",
        "блютуз": "ms-settings:bluetooth",
        "wifi": "ms-settings:network-wifi",
        "вайфай": "ms-settings:network-wifi",
        "сеть": "ms-settings:network-status",
        "интернет": "ms-settings:network-status",
        "экран": "ms-settings:display",
        "дисплей": "ms-settings:display",
        "приложения": "ms-settings:appsfeatures",
        "программы": "ms-settings:appsfeatures",
        "автозагрузка": "ms-settings:startupapps",
        "обновления": "ms-settings:windowsupdate",
        "питание": "ms-settings:powersleep",
        "система": "ms-settings:about",
        "о системе": "ms-settings:about",
        "персонализация": "ms-settings:personalization",
        "диспетчер устройств": "devmgmt.msc",
        "диспетчер задач": "taskmgr.exe",
        "панель управления": "control.exe",
        "настройки": "ms-settings:",
        "параметры": "ms-settings:",
    }

    def open_windows_settings(self, section: str = "настройки") -> str:
        key = (section or "настройки").lower().strip()
        target_uri = "ms-settings:"
        matched_name = "Параметры Windows"
        for k, uri in self.SETTINGS_MAP.items():
            if k in key:
                target_uri = uri
                matched_name = k.capitalize()
                break
        try:
            os.startfile(target_uri)
            return f"Открыл раздел настроек Windows: {matched_name}."
        except Exception as e:
            return f"Не удалось открыть настройки ({matched_name}): {e}"

    def _get_all_drives(self) -> list:
        drives = []
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            d = f"{letter}:\\"
            if os.path.exists(d):
                drives.append(d)
        return drives

    def _resolve_path(self, raw_path: str) -> str:
        p = (raw_path or "").strip()
        low = p.lower()
        home = os.path.expanduser("~")
        aliases = {
            "рабочий стол": os.path.join(home, "Desktop"),
            "на рабочий стол": os.path.join(home, "Desktop"),
            "загрузки": os.path.join(home, "Downloads"),
            "в загрузки": os.path.join(home, "Downloads"),
            "документы": os.path.join(home, "Documents"),
            "в документы": os.path.join(home, "Documents"),
            "диск c": "C:\\",
            "диск d": "D:\\",
        }
        if low in aliases:
            return aliases[low]
        if not os.path.isabs(p):
            return os.path.join(home, "Desktop", p)
        return p

    def inspect_pc(self, path_or_alias: str = "") -> str:
        resolved = self._resolve_path(path_or_alias or "рабочий стол")
        if not os.path.exists(resolved):
            return f"Путь не найден: {resolved}"
        try:
            items = os.listdir(resolved)
            dirs = [f"[Папка] {x}" for x in items if os.path.isdir(os.path.join(resolved, x))][:30]
            files = [f"[Файл] {x}" for x in items if os.path.isfile(os.path.join(resolved, x))][:40]
            listing = "\n".join(dirs + files) or "Папка пуста."
            return f"Содержимое {resolved}:\n{listing}"
        except Exception as e:
            return f"Ошибка чтения {resolved}: {e}"

    def search_files(self, query: str, search_root: str = "", auto_open: bool = False) -> str:
        q = (query or "").strip()
        if not q:
            return "Не указано, что именно искать."

        found = []
        safe_q = q.replace("'", "''")
        ps_index = (
            f"$conn = New-Object -ComObject ADODB.Connection; "
            f"$conn.Open('Provider=Search.CollatorDSO;Extended Properties=\"Application=Windows\";'); "
            f"$rs = $conn.Execute(\"SELECT TOP 15 System.ItemPathDisplay FROM SystemIndex WHERE System.FileName LIKE '%{safe_q}%'\"); "
            f"while(-not $rs.EOF){{ $rs.Fields.Item('System.ItemPathDisplay').Value; $rs.MoveNext() }}; "
            f"$conn.Close()"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_index],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=5,
            )
            for line in (res.stdout or "").splitlines():
                p = line.strip()
                if p and os.path.exists(p) and p not in found:
                    found.append(p)
        except Exception:
            pass

        if len(found) < 5:
            q_low = q.lower()
            roots = [self._resolve_path(search_root)] if search_root else self._get_all_drives()
            skip_dirs = {"windows", "program files", "program files (x86)", "$recycle.bin", "appdata", ".venv", ".venv311", "_internal", "programdata"}
            for r in roots:
                if not os.path.exists(r):
                    continue
                for root_dir, dirs, files in os.walk(r):
                    dirs[:] = [d for d in dirs if d.lower() not in skip_dirs]
                    for name in dirs + files:
                        if q_low in name.lower():
                            full = os.path.join(root_dir, name)
                            if full not in found:
                                found.append(full)
                            if len(found) >= 15:
                                break
                    if len(found) >= 15:
                        break
                if len(found) >= 15:
                    break

        if not found:
            return f"Поисковая система Windows не нашла файлов или папок по запросу «{query}»."

        first_item = next(iter(found))
        if auto_open:
            try:
                os.startfile(first_item)
                return f"Нашёл и сразу открыл: {first_item}"
            except Exception:
                pass

        return f"Поисковая система Windows нашла ({len(found)}):\n" + "\n".join(found)
    def create_folder(self, folder_path: str) -> str:
        target = self._resolve_path(folder_path)
        os.makedirs(target, exist_ok=True)
        return f"Папка создана: {target}"

    def copy_or_move(self, src: str, dst: str, move: bool = False) -> str:
        s = self._resolve_path(src)
        d = self._resolve_path(dst)
        if not os.path.exists(s):
            return f"Исходный объект не найден: {s}"
        try:
            if os.path.isdir(d):
                d = os.path.join(d, os.path.basename(s))
            else:
                os.makedirs(os.path.dirname(d), exist_ok=True)
            if move:
                shutil.move(s, d)
                return f"Переместил {os.path.basename(s)} в {d}"
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
            return f"Скопировал {os.path.basename(s)} в {d}"
        except Exception as e:
            return f"Ошибка при операции с файлом: {e}"

    def rename_item(self, old_path: str, new_name: str) -> str:
        s = self._resolve_path(old_path)
        if not os.path.exists(s):
            return f"Объект не найден: {s}"
        clean_new = os.path.basename((new_name or "").strip())
        if not clean_new:
            return "Не указано новое имя."
        dst = os.path.join(os.path.dirname(s), clean_new)
        try:
            os.rename(s, dst)
            return f"Переименовано в {clean_new}"
        except Exception as e:
            return f"Ошибка переименования: {e}"

    def delete_to_trash(self, target_path: str) -> str:
        target = self._resolve_path(target_path)
        if not os.path.exists(target):
            return f"Объект не найден: {target}"
        try:
            ps_script = (
                f'Add-Type -AssemblyName Microsoft.VisualBasic; '
                f'if (Test-Path -LiteralPath "{target}" -PathType Container) {{ '
                f'[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory("{target}", "OnlyErrorDialogs", "SendToRecycleBin") '
                f'}} else {{ '
                f'[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("{target}", "OnlyErrorDialogs", "SendToRecycleBin") }}'
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True,
            )
            return f"Отправил в Корзину: {os.path.basename(target)}"
        except Exception as e:
            return f"Не удалось удалить в Корзину: {e}"

    def archive_ops(self, action: str, source_path: str, dest_path: str = "") -> str:
        src = self._resolve_path(source_path)
        if not os.path.exists(src):
            return f"Путь не найден: {src}"
        act = (action or "zip").lower()
        try:
            if "распак" in act or "unzip" in act:
                out_dir = self._resolve_path(dest_path) if dest_path else os.path.splitext(src)
                os.makedirs(out_dir, exist_ok=True)
                with zipfile.ZipFile(src, "r") as zf:
                    zf.extractall(out_dir)
                return f"Архив распакован в папку: {out_dir}"
            out_zip = self._resolve_path(dest_path) if dest_path else f"{src}.zip"
            if not out_zip.lower().endswith(".zip"):
                out_zip += ".zip"
            base_no_ext = os.path.splitext(out_zip)
            shutil.make_archive(base_no_ext, "zip", src if os.path.isdir(src) else os.path.dirname(src), None if os.path.isdir(src) else os.path.basename(src))
            return f"Создан архив: {out_zip}"
        except Exception as e:
            return f"Ошибка архивации: {e}"

    def read_text_file(self, file_path: str) -> str:
        raw = self._resolve_path(file_path)
        if not os.path.exists(raw):
            return f"Файл не найден: {raw}"
        try:
            with open(raw, "r", encoding="utf-8", errors="ignore") as f:
                return f"Содержимое файла {os.path.basename(raw)}:\n{f.read(3500)}"
        except Exception as e:
            return f"Не удалось прочитать файл: {e}"

    def run_windows_shell(self, command: str) -> str:
        cmd = (command or "").strip()
        if not cmd:
            return "Пустая системная команда."
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=15,
            )
            return (res.stdout or res.stderr or "Команда выполнена.").strip()[:2000]
        except Exception as e:
            return f"Ошибка выполнения команды: {e}"


    def run_admin_shell(self, command: str) -> str:
        """Формирует и выполняет команду в командной строке / PowerShell с правами Администратора."""
        cmd = (command or "").strip()
        if not cmd:
            return "Не указана команда для выполнения от имени Администратора."
        try:
            import ctypes
            import tempfile
            is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
            if is_admin:
                res = subprocess.run(
                    ["cmd.exe", "/c", cmd],
                    capture_output=True, text=True, encoding="cp866", errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW, timeout=20,
                )
                out = (res.stdout or res.stderr or "Команда успешно выполнена от имени Администратора.").strip()
                return out[:2200]

            # Если сам процесс запущен без прав админа — запрашиваем повышение привилегий через RunAs с записью вывода
            log_file = os.path.join(tempfile.gettempdir(), "oko_admin_out.txt")
            if os.path.exists(log_file):
                os.remove(log_file)
            wrapped = f'/c {cmd} > "{log_file}" 2>&1'
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", wrapped, None, 0)
            import time
            for _ in range(25):
                time.sleep(0.4)
                if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                    break
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="cp866", errors="ignore") as f:
                    txt = f.read(2200).strip()
                return txt or "Команда выполнена с правами Администратора."
            return "Команда отправлена на выполнение с правами Администратора."
        except Exception as e:
            return f"Ошибка выполнения от имени Администратора: {e}"


    def find_folder_everywhere(self, folder_name: str, auto_open: bool = True) -> str:
        """Мгновенно ищет папку по названию во всех местах (Рабочий стол, Загрузки, Документы, все диски) и открывает её."""
        raw = (folder_name or "").strip(" .!?\"'«»")
        for prefix in ("папку", "папка", "директорию", "каталог"):
            raw = re.sub(rf"\b{prefix}\b", "", raw, flags=re.I).strip()
        if not raw:
            return "Не указано название папки для поиска."

        q_low = raw.lower()
        home = os.path.expanduser("~")
        priority_roots = [
            os.path.join(home, "Desktop"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Documents"),
        ] + self._get_all_drives()

        matched_dirs = []
        skip_dirs = {
            "windows", "program files", "program files (x86)", "$recycle.bin",
            "appdata", ".venv", ".venv311", "_internal", "programdata", "system volume information",
        }

        # 1. Быстрая проверка верхних уровней в приоритетных местах
        for base in priority_roots:
            if not os.path.exists(base):
                continue
            try:
                for entry in os.listdir(base):
                    full = os.path.join(base, entry)
                    if os.path.isdir(full) and q_low in entry.lower() and full not in matched_dirs:
                        matched_dirs.append(full)
            except Exception:
                pass

        # 2. Запрос к системному индексу Windows Search для папок
        if not matched_dirs:
            safe_q = raw.replace("'", "''")
            ps_idx = (
                f"$conn = New-Object -ComObject ADODB.Connection; "
                f"$conn.Open('Provider=Search.CollatorDSO;Extended Properties=\"Application=Windows\";'); "
                f"$rs = $conn.Execute(\"SELECT TOP 10 System.ItemPathDisplay FROM SystemIndex WHERE System.Kind = 'folder' AND System.FileName LIKE '%{safe_q}%'\"); "
                f"while(-not $rs.EOF){{ $rs.Fields.Item('System.ItemPathDisplay').Value; $rs.MoveNext() }}; "
                f"$conn.Close()"
            )
            try:
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_idx],
                    capture_output=True, text=True, encoding="utf-8", errors="ignore",
                    creationflags=subprocess.CREATE_NO_WINDOW, timeout=4,
                )
                for line in (res.stdout or "").splitlines():
                    p = line.strip()
                    if p and os.path.isdir(p) and p not in matched_dirs:
                        matched_dirs.append(p)
            except Exception:
                pass

        # 3. Глубокий обход всех папок на всех дисках
        if not matched_dirs:
            for base in priority_roots:
                if not os.path.exists(base):
                    continue
                for root_dir, dirs, _ in os.walk(base):
                    dirs[:] = [d for d in dirs if d.lower() not in skip_dirs]
                    for d in dirs:
                        if q_low in d.lower():
                            full = os.path.join(root_dir, d)
                            if full not in matched_dirs:
                                matched_dirs.append(full)
                            if len(matched_dirs) >= 10:
                                break
                    if len(matched_dirs) >= 10:
                        break
                if len(matched_dirs) >= 10:
                    break

        if not matched_dirs:
            return f"Папка «{raw}» не найдена ни на одном диске."

        # Приоритет точному совпадению имени папки
        exact = next((p for p in matched_dirs if os.path.basename(p).lower() == q_low), next(iter(matched_dirs)))
        if auto_open:
            subprocess.Popen(["explorer.exe", exact])
            return f"Нашёл папку «{os.path.basename(exact)}» ({exact}) и сразу открыл её."

        return f"Найдены папки ({len(matched_dirs)}):\n" + "\n".join(matched_dirs)

