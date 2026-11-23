# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import datetime
import json
import os
from typing import Any, Dict, List


class AgentMemory:
    """Постоянная нестираемая память всех шагов и самообучение предугадыванию действий."""

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        base_dir = os.path.dirname(storage_path)
        os.makedirs(base_dir, exist_ok=True)
        # Нестираемый лог всех шагов и действий (дописывается только в конец)
        self.journal_path = os.path.join(base_dir, "permanent_history.jsonl")
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    loaded.setdefault("facts", ["Город пользователя: Владивосток"])
                    loaded.setdefault("macros", {})
                    loaded.setdefault("learned_chains", [])
                    return loaded
            except Exception:
                pass
        return {
            "facts": ["Город пользователя: Владивосток"],
            "macros": {},
            "learned_chains": [],
        }

    def save(self):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def log_permanent_event(self, event_type: str, payload: Dict[str, Any]):
        """Записывает любой шаг, мысль, инструмент или диалог навсегда без удаления."""
        record = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": event_type,
            "data": payload,
        }
        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def learn_action_chain(self, user_command: str, steps_executed: List[Dict[str, Any]]):
        """Запоминает успешную цепочку шагов для логического предугадывания будущих задач."""
        if not steps_executed:
            return
        chain_summary = " -> ".join(f"{s['tool']}({s.get('args', {})})" for s in steps_executed)
        entry = {
            "time": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "goal": user_command.strip(),
            "chain": chain_summary,
        }
        self.data["learned_chains"].append(entry)
        self.save()
        self.log_permanent_event("learned_chain", entry)

    def add_fact(self, fact: str) -> str:
        clean = (fact or "").strip()
        if clean and clean not in self.data["facts"]:
            self.data["facts"].append(clean)
            self.save()
            self.log_permanent_event("fact", {"fact": clean})
        return f"Запомнил навсегда: {clean}"

    def add_macro(self, trigger: str, steps_description: str) -> str:
        key = (trigger or "").lower().strip()
        if not key:
            return "Не указано название макроса."
        self.data["macros"][key] = steps_description.strip()
        self.save()
        self.log_permanent_event("macro", {"trigger": key, "steps": steps_description.strip()})
        return f"Голосовой макрос «{key}» сохранён."

    def _find_relevant_experience(self, current_command: str, limit: int = 5) -> List[str]:
        """Подбирает похожие прошлые цепочки шагов, чтобы предугадать логику новой задачи."""
        chains = self.data.get("learned_chains", [])
        if not chains:
            return []
        words = {w for w in current_command.lower().split() if len(w) > 3}
        scored = []
        for idx, item in enumerate(chains):
            goal_low = item.get("goal", "").lower()
            overlap = sum(1 for w in words if w in goal_low)
            scored.append((overlap, idx, item))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top = [x[2] for x in scored[:limit]]
        return [f"Задача: «{x['goal']}» => Проверенная цепочка шагов: {x['chain']}" for x in top]

    def build_memory_prompt(self, current_command: str = "") -> str:
        facts = self.data.get("facts", [])
        macros = self.data.get("macros", {})
        experience = self._find_relevant_experience(current_command)

        parts = [
            "[ПРАВИЛО ПАМЯТИ И ПРЕДУГАДЫВАНИЯ]: Твоя память постоянна и не стирается. "
            "Опирайся на прошлый опыт выполнения задач, логически предугадывай следующий шаг пользователя "
            "и после выполнения задачи кратко предложи логичное продолжение, если оно уместно."
        ]
        if facts:
            parts.append("ПОСТОЯННЫЕ ФАКТЫ О ПОЛЬЗОВАТЕЛЕ:\n" + "\n".join(f"- {x}" for x in facts))
        if macros:
            parts.append(
                "ГОЛОСОВЫЕ МАКРОСЫ:\n" + "\n".join(f"- «{k}»: {v}" for k, v in macros.items())
            )
        if experience:
            parts.append(
                "ВЫУЧЕННЫЕ ЦЕПОЧКИ ДЕЙСТВИЙ ИЗ ПРОШЛОГО ОПЫТА (используй для предугадывания шагов):\n"
                + "\n".join(f"- {e}" for e in experience)
            )
        return "\n\n".join(parts)

