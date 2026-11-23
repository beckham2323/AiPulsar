# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import ctypes
import datetime
import json
import os
import re
import threading
import time
import psutil
from core.i18n import get_lang


class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def _get_idle_seconds() -> float:
    try:
        lii = _LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            return max(0.0, millis / 1000.0)
    except Exception:
        pass
    return 0.0


class PulsarAutoEvolutionEngine:
    """Фоновый движок самообучения AiPulsar: учится на привычках, запоминает правила и индексирует файлы в простое."""

    TRACKED_APPS = {
        "chrome.exe": "браузер Chrome",
        "yandex.exe": "Яндекс Браузер",
        "msedge.exe": "браузер Edge",
        "telegram.exe": "Telegram",
        "winword.exe": "Word",
        "excel.exe": "Excel",
        "code.exe": "VS Code",
        "1cv8.exe": "1С",
    }

    def __init__(self, models_dir: str = "models", notify_cb=None):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.db_path = os.path.join(self.models_dir, "evolution_brain.json")
        self.notify_cb = notify_cb
        self.enabled = True
        self._suggested_today = False
        self.data = self._load()
        threading.Thread(target=self._evolution_loop, daemon=True).start()

    def _load(self) -> dict:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"rules": [], "app_stats": {}, "indexed_files": []}

    def _save(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def try_learn_user_rule(self, text: str) -> str:
        low = (text or "").strip().lower()
        if any(low.startswith(p) for p in ("запомни:", "запомни правило:", "запомни что ", "выучи правило:", "remember rule:", "remember that ")):
            rule_txt = re.sub(r"^(?:запомни правило|запомни что|запомни|выучи правило|remember rule|remember that)[:\s]*", "", text.strip(), flags=re.I).strip()
            if rule_txt and rule_txt not in self.data["rules"]:
                self.data["rules"].append(rule_txt)
                self.data["rules"] = self.data["rules"][-50:]
                self._save()
            is_en = get_lang() == "en"
            return f"Learned and saved to long-term memory: «{rule_txt}»." if is_en else f"Запомнил в долговременную память: «{rule_txt}». Готово."
        return ""

    def get_learned_context(self) -> str:
        rules = self.data.get("rules", [])
        if not rules:
            return ""
        joined = "; ".join(rules[-12:])
        return f"\n[ВЫУЧЕННЫЕ ПРАВИЛА ПОЛЬЗОВАТЕЛЯ]: {joined}\n"

    def get_evolution_summary(self) -> str:
        is_en = get_lang() == "en"
        r_cnt = len(self.data.get("rules", []))
        f_cnt = len(self.data.get("indexed_files", []))
        top_apps = sorted(self.data.get("app_stats", {}).items(), key=lambda x: x[1], reverse=True)[:3]
        apps_str = ", ".join(self.TRACKED_APPS.get(k, k) for k, _ in top_apps) or ("пока собираю статистику" if not is_en else "collecting data")
        if is_en:
            return f"Self-Evolution status: {r_cnt} personal rules learned, {f_cnt} documents indexed in idle time. Top apps: {apps_str}."
        return f"Статус самообучения: выучено личных правил — {r_cnt}, проиндексировано документов в простое — {f_cnt}. Частые программы: {apps_str}."

    def _scan_idle_documents(self):
        scan_dirs = [
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.expanduser("~"), "Documents"),
        ]
        known = set(self.data.get("indexed_files", []))
        added = 0
        for d in scan_dirs:
            if not os.path.isdir(d):
                continue
            for fn in os.listdir(d):
                if fn.lower().endswith((".txt", ".docx", ".pdf", ".xlsx")) and fn not in known:
                    known.add(fn)
                    added += 1
                    if added >= 10:
                        break
        if added > 0:
            self.data["indexed_files"] = list(known)[-200:]
            self._save()

    def _evolution_loop(self):
        while True:
            time.sleep(60.0)
            if not self.enabled:
                continue
            try:
                # 1. Фиксируем привычки использования рабочих программ
                seen_now = set()
                for proc in psutil.process_iter(["name"]):
                    pname = (proc.info.get("name") or "").lower()
                    if pname in self.TRACKED_APPS and pname not in seen_now:
                        seen_now.add(pname)
                        stats = self.data.setdefault("app_stats", {})
                        stats[pname] = int(stats.get(pname, 0)) + 1
                self._save()

                # 2. Если пользователь отошёл от ПК более чем на 5 минут (простой) — индексируем новые файлы и формируем полезную подсказку
                idle_sec = _get_idle_seconds()
                if idle_sec >= 300:
                    self._scan_idle_documents()
                    if not self._suggested_today and len(self.data.get("app_stats", {})) >= 2 and self.notify_cb:
                        self._suggested_today = True
                        top2 = sorted(self.data["app_stats"].items(), key=lambda x: x[1], reverse=True)[:2]
                        names = " и ".join(self.TRACKED_APPS.get(k, k) for k, _ in top2)
                        self.notify_cb(
                            "AiPulsar",
                            f"🧠 Самообучение в простое: я заметил, что вы чаще всего используете {names}. "
                            f"Скажите «Запомни сценарий Рабочий старт: открой {names}», чтобы запускать их одной фразой!"
                        )
            except Exception:
                pass
