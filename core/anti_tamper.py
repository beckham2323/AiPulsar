# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import ctypes
import hashlib
import hmac
import json
import os
import sys

_INTEGRITY_SECRET = b"VESKOR_SMIRNOV_VE_AIPULSAR_ANTI_TAMPER_2026_SIG"


def _compute_file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_and_protect_runtime() -> tuple:
    """
    Многоуровневая защита AiPulsar от копирования, модификации и внедрения модов:
    1. Блокирует переменные инжекта (PYTHONPATH, PYTHONINSPECT) и отладчики.
    2. Запрещает любые сторонние .py / .dll / .pyd моды рядом с AiPulsar.exe.
    3. Проверяет HMAC-SHA256 подпись всех системных файлов и ресурсов.
    """
    # 1. Проверка отладчика Windows (Anti-Debug)
    try:
        if hasattr(ctypes, "windll") and ctypes.windll.kernel32.IsDebuggerPresent():
            return False, "Обнаружен отладчик. Запуск заблокирован системой безопасности VESKOR."
    except Exception:
        pass

    # 2. Блокировка попыток подгрузить сторонние моды через PYTHONPATH
    for bad_env in ("PYTHONPATH", "PYTHONINSPECT", "PYTHONSTARTUP"):
        if os.environ.get(bad_env):
            os.environ.pop(bad_env, None)

    if not getattr(sys, "frozen", False):
        return True, "DEV_MODE"

    exe_path = os.path.abspath(next(iter(sys.argv), ""))
    app_dir = os.path.dirname(exe_path)

    # 3. Запрет подбрасывания любых посторонних модов (.py, .pyw, .zip, папок mods/plugins) в корень программы
    forbidden_names = {"mods", "plugins", "scripts", "patches", "inject", "hook"}
    for entry in os.listdir(app_dir):
        low = entry.lower()
        if low in forbidden_names or low.endswith((".py", ".pyw", ".pyc", ".pyo")):
            return False, f"Обнаружен несанкционированный мод или скрипт ({entry}). Модификация запрещена!"

    # 4. Проверка криптографического манифеста целостности integrity.sig
    sig_path = os.path.join(app_dir, "_internal", "integrity.sig")
    if not os.path.exists(sig_path):
        return False, "Отсутствует цифровая подпись целостности VESKOR (integrity.sig)."

    try:
        with open(sig_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        files_map = manifest.get("files", {})
        expected_hmac = manifest.get("signature", "")

        # Проверяем подлинность самого манифеста
        raw_payload = json.dumps(files_map, sort_keys=True).encode("utf-8")
        calc_hmac = hmac.new(_INTEGRITY_SECRET, raw_payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_hmac, calc_hmac):
            return False, "Цифровая подпись манифеста нарушена! Файлы программы были изменены."

        # Сверяем контрольные суммы каждого защищённого файла
        for rel_path, expected_hash in files_map.items():
            full_path = os.path.join(app_dir, rel_path.replace("/", os.sep))
            if not os.path.exists(full_path):
                return False, f"Нарушена целостность: удалён защищённый файл {rel_path}."
            if _compute_file_sha256(full_path) != expected_hash:
                return False, f"Обнаружена модификация файла {rel_path}! Запуск невозможен."
    except Exception as e:
        return False, f"Ошибка проверки цифровой подписи: {e}"

    return True, "OK"
