# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import json
import os
import re


class PulsarMacrosManager:
    """Голосовые макросы и сценарии одной фразой ('Режим работы', 'Режим кино', 'Игровой режим' и пользовательские)."""

    DEFAULT_MACROS = {
        "режим работы": [
            {"tool": "cmd_open", "args": {"target": "документы"}},
            {"tool": "cmd_open", "args": {"target": "браузер"}},
        ],
        "режим кино": [
            {"tool": "window", "args": {"action": "свернуть"}},
            {"tool": "volume", "args": {"action": "громче"}},
            {"tool": "fullscreen_on", "args": {}},
        ],
        "игровой режим": [
            {"tool": "window", "args": {"action": "свернуть"}},
            {"tool": "hide_to_tray", "args": {}},
        ],
    }

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.db_path = os.path.join(self.models_dir, "macros.json")
        self.macros = self._load()

    def _load(self) -> dict:
        data = dict(self.DEFAULT_MACROS)
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    custom = json.load(f)
                    if isinstance(custom, dict):
                        data.update(custom)
            except Exception:
                pass
        return data

    def _save(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.macros, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def try_learn_macro(self, text: str) -> str:
        m = re.match(r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:запомни|создай)\s+(?:сценарий|макрос|режим)\s+([^:]+):\s*(.+)$", text.strip(), flags=re.I)
        if not m:
            return ""
        name = m.group(1).strip().lower()
        raw_actions = [a.strip() for a in re.split(r"\bи\b|,", m.group(2)) if a.strip()]
        steps = [{"tool": "cmd_open", "args": {"target": act}} for act in raw_actions]
        if name and steps:
            self.macros[name] = steps
            self._save()
            return f"Запомнил сценарий «{name}» ({len(steps)} действий). Просто скажи «{name}» для запуска."
        return ""

    def match_macro(self, text: str) -> tuple:
        low = text.lower().strip(" .!?")
        for name, steps in self.macros.items():
            if name in low:
                return name, steps
        return "", []

