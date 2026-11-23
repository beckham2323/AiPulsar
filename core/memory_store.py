# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import datetime
import json
import os
import re


class AgentMemory:
    """Долговременная нестираемая память Pulsar: помнит все диалоги, команды, факты и предпочтения."""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.history_file = os.path.join(self.models_dir, "memory_log.jsonl")
        self.facts_file = os.path.join(self.models_dir, "memory_facts.json")
        self.facts = self._load_facts()

    def _load_facts(self) -> list:
        if os.path.exists(self.facts_file):
            try:
                with open(self.facts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
        return []

    def _save_facts(self):
        try:
            with open(self.facts_file, "w", encoding="utf-8") as f:
                json.dump(self.facts[-250:], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _append_log(self, kind: str, user_text: str, reply_text: str):
        rec = {
            "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "kind": kind,
            "user": user_text,
            "pulsar": reply_text,
        }
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass

        low = user_text.lower()
        if any(k in low for k in ("запомни", "меня зовут", "мой ", "моя ", "мои ", "я люблю", "я работаю")):
            fact = f"[{rec['ts']}] {user_text.strip()}"
            if fact not in self.facts:
                self.facts.append(fact)
                self._save_facts()

    def remember_command(self, user_text: str, reply_text: str):
        self._append_log("command", user_text, reply_text)

    def remember_chat(self, user_text: str, reply_text: str):
        self._append_log("chat", user_text, reply_text)

    def build_memory_context(self, query: str) -> str:
        lines = []
        if self.facts:
            lines.append("ВАЖНЫЕ ФАКТЫ О ПОЛЬЗОВАТЕЛЕ:")
            for fct in self.facts[-15:]:
                lines.append(f"- {fct}")

        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    recent = f.readlines()[-12:]
                if recent:
                    lines.append("\nНЕДАВНИЕ ДИАЛОГИ:")
                    words = [w for w in re.findall(r"[а-яА-Яa-zA-Z0-9]{4,}", query.lower())]
                    for raw_line in recent:
                        item = json.loads(raw_line)
                        u = item.get("user", "")
                        p = item.get("pulsar", "")
                        if not words or any(w in (u + " " + p).lower() for w in words):
                            lines.append(f"Пользователь: {u} | Pulsar: {p[:180]}")
            except Exception:
                pass
        return "\n".join(lines)

