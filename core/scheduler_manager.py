# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import datetime
import json
import os
import re
import threading
import time


class PulsarScheduler:
    """Умный планировщик таймеров и голосовых напоминаний с сохранением в нестираемую память."""

    def __init__(self, models_dir: str = "models", trigger_cb=None):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.db_path = os.path.join(self.models_dir, "reminders.json")
        self.trigger_cb = trigger_cb or (lambda msg: None)
        self._tasks = self._load()
        threading.Thread(target=self._loop, daemon=True).start()

    def _load(self) -> list:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self._tasks, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def try_schedule_from_text(self, text: str) -> str:
        """Распознаёт команды вида 'напомни через 10 минут ...', 'таймер на 5 минут', 'напомни в 14:30 ...'."""
        low = text.lower().strip()
        if not any(k in low for k in ("напомни", "таймер", "будильник", "разбуди")):
            return ""

        now = datetime.datetime.now()
        target_dt = None
        note = ""

        # 1. Формат "через X минут / часов / секунд"
        m_rel = re.search(r"через\s+(\d+)\s*(секунд\w*|минут\w*|час\w*)", low)
        if m_rel:
            val = int(m_rel.group(1))
            unit = m_rel.group(2)
            delta = datetime.timedelta(seconds=val) if unit.startswith("сек") else (
                datetime.timedelta(hours=val) if unit.startswith("час") else datetime.timedelta(minutes=val)
            )
            target_dt = now + delta
            note = re.sub(r"^.*?(?:через\s+\d+\s*(?:секунд\w*|минут\w*|час\w*))\s*", "", text, flags=re.I).strip(" .!?")

        # 2. Формат "таймер на X минут"
        if not target_dt:
            m_tmr = re.search(r"таймер\s+(?:на\s+)?(\d+)\s*(секунд\w*|минут\w*|час\w*)", low)
            if m_tmr:
                val = int(m_tmr.group(1))
                unit = m_tmr.group(2)
                delta = datetime.timedelta(seconds=val) if unit.startswith("сек") else (
                    datetime.timedelta(hours=val) if unit.startswith("час") else datetime.timedelta(minutes=val)
                )
                target_dt = now + delta
                note = f"Таймер на {val} {unit}"

        # 3. Формат "в ЧЧ:ММ"
        if not target_dt:
            m_abs = re.search(r"\bв\s+(\d{1,2})[:.\s](\d{2})\b", low)
            if m_abs:
                hh, mm = int(m_abs.group(1)), int(m_abs.group(2))
                if 0 <= hh <= 23 and 0 <= mm <= 59:
                    target_dt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                    if target_dt <= now:
                        target_dt += datetime.timedelta(days=1)
                    note = re.sub(r"^.*?\bв\s+\d{1,2}[:.\s]\d{2}\b\s*", "", text, flags=re.I).strip(" .!?")

        if not target_dt:
            return ""

        clean_note = note or "Напоминание от Pulsar"
        self._tasks.append({"due": target_dt.isoformat(), "text": clean_note})
        self._save()
        return f"Поставил напоминание на {target_dt.strftime('%H:%M:%S')}: «{clean_note}»."

    def _loop(self):
        while True:
            time.sleep(1.0)
            if not self._tasks:
                continue
            now = datetime.datetime.now()
            remaining = []
            fired = []
            for item in self._tasks:
                try:
                    due = datetime.datetime.fromisoformat(item["due"])
                    if now >= due:
                        fired.append(item["text"])
                    else:
                        remaining.append(item)
                except Exception:
                    pass
            if fired:
                self._tasks = remaining
                self._save()
                for msg in fired:
                    self.trigger_cb(msg)

