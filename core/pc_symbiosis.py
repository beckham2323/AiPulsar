# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import ctypes
import datetime
import os
import re
import shutil
import stat
import subprocess
import sys
from typing import Tuple

try:
    import winreg
except Exception:
    winreg = None


def ensure_admin_and_privileges():
    """Запрашивает права Администратора Windows (UAC) и активирует системные привилегии ядра для полного доступа."""
    if os.name != "nt":
        return
    try:
        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        is_admin = False

    if not is_admin and getattr(sys, "frozen", False):
        try:
            params = " ".join(f'"{a}"' for a in sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, os.path.dirname(sys.executable), 1)
            sys.exit(0)
        except Exception:
            pass

    # Активация привилегий SeDebugPrivilege, SeBackupPrivilege, SeRestorePrivilege, SeTakeOwnershipPrivilege
    priv_names = [
        "SeDebugPrivilege",
        "SeBackupPrivilege",
        "SeRestorePrivilege",
        "SeTakeOwnershipPrivilege",
        "SeSystemEnvironmentPrivilege",
    ]
    try:
        advapi32 = ctypes.windll.advapi32
        kernel32 = ctypes.windll.kernel32
        h_token = ctypes.c_void_p()
        if advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0028, ctypes.byref(h_token)):
            for p_name in priv_names:
                luid = ctypes.c_int64()
                if advapi32.LookupPrivilegeValueW(None, p_name, ctypes.byref(luid)):
                    tp = (ctypes.c_uint32 * 4)(1, luid.value & 0xFFFFFFFF, (luid.value >> 32) & 0xFFFFFFFF, 0x00000002)
                    advapi32.AdjustTokenPrivileges(h_token, False, ctypes.byref(tp), 0, None, None)
            kernel32.CloseHandle(h_token)
    except Exception:
        pass


class PulsarPCSymbiosis:
    """Полный системный симбиоз с ПК: управление всеми файлами, дисками, реестром, службами и настройками Windows."""

    HIVE_MAP = {
        "HKCU": winreg.HKEY_CURRENT_USER if winreg else None,
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER if winreg else None,
        "HKLM": winreg.HKEY_LOCAL_MACHINE if winreg else None,
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE if winreg else None,
        "HKCR": winreg.HKEY_CLASSES_ROOT if winreg else None,
        "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT if winreg else None,
        "HKU": winreg.HKEY_USERS if winreg else None,
        "HKEY_USERS": winreg.HKEY_USERS if winreg else None,
    }

    @staticmethod
    def list_all_drives() -> list:
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            root = f"{letter}:\\"
            if os.path.exists(root):
                drives.append(root)
        return drives

    @classmethod
    def find_anywhere_on_pc(cls, query: str, max_results: int = 20) -> str:
        q = query.strip().lower()
        if not q:
            return "Укажите имя файла или папки для поиска по всему компьютеру."
        found = []
        skip_dirs = {"$recycle.bin", "system volume information", "winsxs", "node_modules", ".venv", ".venv311"}
        for drive in cls.list_all_drives():
            for root_dir, dirs, files in os.walk(drive, topdown=True):
                dirs[:] = [d for d in dirs if d.lower() not in skip_dirs]
                for name in dirs + files:
                    if q in name.lower():
                        found.append(os.path.join(root_dir, name))
                        if len(found) >= max_results:
                            return "Найдено по всему ПК (первые 20):\n" + "\n".join(found)
        if not found:
            return f"По запросу «{query}» на дисках ПК ничего не найдено."
        return f"Найдено на ПК ({len(found)}):\n" + "\n".join(found)

    @staticmethod
    def force_delete_path(target_path: str) -> str:
        p = target_path.strip().strip('"')
        if not os.path.exists(p):
            return f"Путь не найден: {p}"
        def _onerror(func, path, _exc):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception:
                pass
        try:
            if os.path.isdir(p):
                shutil.rmtree(p, onerror=_onerror)
            else:
                os.chmod(p, stat.S_IWRITE)
                os.remove(p)
            return f"Удалено с ПК: {p}"
        except Exception as e:
            return f"Не удалось удалить {p}: {e}"

    @staticmethod
    def create_folder_or_file(target_path: str, content: str = "") -> str:
        p = target_path.strip().strip('"')
        try:
            if content or os.path.splitext(p)[1]:
                parent = os.path.dirname(p)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Файл создан и записан: {p}"
            os.makedirs(p, exist_ok=True)
            return f"Папка создана: {p}"
        except Exception as e:
            return f"Ошибка создания {p}: {e}"
    @classmethod
    def _parse_reg_path(cls, full_path: str):
        clean = full_path.strip().strip('"')
        parts = clean.split("\\", 1)
        if len(parts) < 2:
            return None, ""
        hive = cls.HIVE_MAP.get(parts[0].upper())
        return hive, parts[1]

    @classmethod
    def registry_read(cls, reg_path: str, value_name: str = "") -> str:
        if not winreg:
            return "Модуль реестра Windows недоступен."
        hive, subkey = cls._parse_reg_path(reg_path)
        if not hive or not subkey:
            return "Укажите полный путь ветки реестра (например: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run)."
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as rk:
                if value_name:
                    val, vtype = winreg.QueryValueEx(rk, value_name)
                    return f"Реестр [{reg_path}] -> {value_name} = {val} (тип {vtype})"
                items = []
                idx = 0
                while True:
                    try:
                        n, v, _ = winreg.EnumValue(rk, idx)
                        items.append(f"  • {n or '(По умолчанию)'} = {v}")
                        idx += 1
                    except OSError:
                        break
                subkeys = []
                s_idx = 0
                while True:
                    try:
                        subkeys.append(f"  [Раздел] {winreg.EnumKey(rk, s_idx)}")
                        s_idx += 1
                    except OSError:
                        break
                out = subkeys + items
                return f"Содержимое ветки [{reg_path}]:\n" + ("\n".join(out[:40]) if out else "  (Раздел пуст)")
        except Exception as e:
            return f"Ошибка чтения реестра [{reg_path}]: {e}"

    @classmethod
    def registry_write(cls, reg_path: str, value_name: str, value_data, is_dword: bool = False) -> str:
        if not winreg:
            return "Модуль реестра Windows недоступен."
        hive, subkey = cls._parse_reg_path(reg_path)
        if not hive or not subkey:
            return "Некорректный путь ветки реестра."
        try:
            # Автоматический бэкап ветки перед изменением
            os.makedirs("models/reg_backups", exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            bkp_file = os.path.abspath(f"models/reg_backups/backup_{ts}.reg")
            subprocess.run(["reg", "export", reg_path, bkp_file, "/y"], creationflags=0x08000000, capture_output=True)

            with winreg.CreateKeyEx(hive, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as rk:
                if is_dword:
                    winreg.SetValueEx(rk, value_name, 0, winreg.REG_DWORD, int(value_data))
                else:
                    winreg.SetValueEx(rk, value_name, 0, winreg.REG_SZ, str(value_data))
            return f"Параметр реестра сохранён: [{reg_path}] {value_name} = {value_data} (бэкап: {bkp_file})"
        except Exception as e:
            return f"Ошибка записи в реестр [{reg_path}]: {e}"

    @classmethod
    def registry_delete_value(cls, reg_path: str, value_name: str) -> str:
        if not winreg:
            return "Модуль реестра Windows недоступен."
        hive, subkey = cls._parse_reg_path(reg_path)
        if not hive or not subkey:
            return "Некорректный путь ветки реестра."
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as rk:
                winreg.DeleteValue(rk, value_name)
            return f"Параметр «{value_name}» удалён из [{reg_path}]."
        except Exception as e:
            return f"Ошибка удаления из реестра: {e}"

    @classmethod
    def try_handle_system_command(cls, text: str) -> Tuple[bool, str]:
        """Распознаёт и исполняет прямые команды управления файлами, дисками, реестром и настройками ПК."""
        raw = text.strip()
        low = raw.lower()

        # 1. Глобальный поиск по всем дискам ПК
        m_find = re.match(r"^(?:найди на пк|найти на пк|поиск по всему пк|найди файл|найди папку)\s+(.+)$", raw, re.IGNORECASE)
        if m_find:
            return True, cls.find_anywhere_on_pc(m_find.group(1))

        # 2. Создание папки или файла по любому пути
        m_mk = re.match(r"^(?:создай папку|создать папку|создай файл|создать файл)\s+([a-zA-Z]:\\[^\r\n]+)$", raw, re.IGNORECASE)
        if m_mk:
            return True, cls.create_folder_or_file(m_mk.group(1))

        # 3. Удаление любого файла или папки по пути
        m_del = re.match(r"^(?:удали файл|удали папку|удалить файл|удалить папку)\s+([a-zA-Z]:\\[^\r\n]+)$", raw, re.IGNORECASE)
        if m_del:
            return True, cls.force_delete_path(m_del.group(1))

        # 4. Чтение ветки реестра
        m_reg_r = re.match(r"^(?:прочитай реестр|покажи реестр|реестр)\s+(HK[A-Z_]+\\[^\s]+)(?:\s+([^\s]+))?$", raw, re.IGNORECASE)
        if m_reg_r:
            return True, cls.registry_read(m_reg_r.group(1), m_reg_r.group(2) or "")

        # 5. Запись в реестр: "запиши в реестр HKCU\... Имя = Значение"
        m_reg_w = re.match(r"^(?:запиши в реестр|измени реестр)\s+(HK[A-Z_]+\\[^\s]+)\s+([^\s=]+)\s*=\s*(.+)$", raw, re.IGNORECASE)
        if m_reg_w:
            val_str = m_reg_w.group(3).strip().strip('"')
            is_num = val_str.isdigit()
            return True, cls.registry_write(m_reg_w.group(1), m_reg_w.group(2), int(val_str) if is_num else val_str, is_dword=is_num)

        # 6. Список всех дисков и томов ПК
        if any(k in low for k in ("список дисков", "все диски пк", "какие диски есть")):
            return True, "Подключённые диски и разделы ПК: " + ", ".join(cls.list_all_drives())

        return False, ""
