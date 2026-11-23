# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import datetime
import json
import os
import re
import threading
import time
import webbrowser
import mss
import numpy as np
from core.i18n import get_lang


class PulsarSuperProTools:
    """Супер-функции Pulsar Pro: Машина времени экрана (Recall), Невидимый суфлёр и Генератор сайтов/презентаций."""

    def __init__(self, vision, brain, models_dir: str = "models"):
        self.vision = vision
        self.brain = brain
        self.recall_dir = os.path.join(models_dir, "screen_recall")
        os.makedirs(self.recall_dir, exist_ok=True)
        self.recall_db = os.path.join(self.recall_dir, "recall_index.json")
        self._recall_active = False
        self._last_sig = ""
        self.prompter_active = False

    def start_screen_time_machine(self) -> str:
        is_en = get_lang() == "en"
        if self._recall_active:
            return "Screen Time Machine is already recording." if is_en else "Машина времени экрана уже работает в фоне."
        self._recall_active = True
        threading.Thread(target=self._recall_loop, daemon=True).start()
        return (
            "Screen Time Machine enabled! I now remember everything shown on your screen locally."
            if is_en
            else "Машина времени экрана включена! Теперь я локально запоминаю всё, что появляется на экране."
        )

    def _recall_loop(self):
        while self._recall_active:
            try:
                if self.vision and getattr(self.vision, "ocr", None):
                    with mss.mss() as sct:
                        mon = sct.monitors[1 if len(sct.monitors) > 1 else 0]
                        shot = sct.grab(mon)
                        img = np.array(shot)[:, :, :3]
                        res, _ = self.vision.ocr(img)
                        lines = [str(item) for item in (res or []) if len(item) >= 2]
                        joined = " | ".join(lines)[:3000]
                        sig = joined[:120]
                        if joined and sig != self._last_sig:
                            self._last_sig = sig
                            self._append_recall_record(joined)
            except Exception:
                pass
            time.sleep(10.0)

    def _append_recall_record(self, text_blob: str):
        records = []
        if os.path.exists(self.recall_db):
            try:
                with open(self.recall_db, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                records = []
        now_dt = datetime.datetime.now()
        cutoff = (now_dt - datetime.timedelta(hours=24)).isoformat()
        records = [r for r in records if r.get("ts", "") >= cutoff]
        records.append({"ts": now_dt.isoformat(), "time": now_dt.strftime("%H:%M:%S"), "text": text_blob})
        with open(self.recall_db, "w", encoding="utf-8") as f:
            json.dump(records[-300:], f, ensure_ascii=False)

    def search_screen_time_machine(self, query_text: str) -> str:
        is_en = get_lang() == "en"
        q = re.sub(
            r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:найди в памяти экрана|найди на экране где|что было на экране|машина времени|search screen memory|what was on screen)[:\s]*",
            "",
            query_text,
            flags=re.I,
        ).strip(" .!?")

        if not os.path.exists(self.recall_db):
            return (
                "Screen memory is empty yet. Say 'Enable screen time machine' first."
                if is_en
                else "Память экрана пока пуста. Сначала скажите «Включи машину времени экрана»."
            )

        with open(self.recall_db, "r", encoding="utf-8") as f:
            records = json.load(f)

        words = [w.lower() for w in re.findall(r"[а-яА-Яa-zA-Z0-9]{2,}", q)]
        hits = []
        for rec in reversed(records):
            low_t = rec.get("text", "").lower()
            if any(w in low_t for w in words):
                hits.append(f"[{rec.get('time')}]: {rec.get('text', '')[:380]}")
            if len(hits) >= 3:
                break

        if not hits:
            return f"Nothing matching «{q}» found in today's screen history." if is_en else f"В сегодняшней истории экрана не найдено упоминаний «{q}»."

        ctx = "\n\n".join(hits)
        prompt = (
            f"Based on these screen history captures, briefly answer what was shown for query '{q}':\n\n{ctx}"
            if is_en
            else f"По этим сохранённым снимкам текста с экрана кратко ответь на запрос «{q}» (укажи время):\n\n{ctx}"
        )
        ans = self.brain.ask_free_chat([{"role": "user", "content": prompt}])
        return ans or ctx[:600]

    def toggle_invisible_prompter(self, enable: bool) -> str:
        is_en = get_lang() == "en"
        self.prompter_active = bool(enable)
        if self.prompter_active:
            return (
                "Invisible Call Prompter ON. I will whisper silent hints into chat without speaking aloud."
                if is_en
                else "Невидимый суфлёр включён! Буду бесшумно писать подсказки в чат, не озвучивая их вслух."
            )
        return "Invisible Call Prompter OFF." if is_en else "Невидимый суфлёр выключен."

    def generate_website_or_presentation(self, prompt_text: str) -> str:
        is_en = get_lang() == "en"
        is_pres = any(w in prompt_text.lower() for w in ("презентац", "слайд", "presentation", "slides"))
        topic = re.sub(
            r"^(?:pulsar|пульсар)?[,\s]*(?:создай|сделай|сгенерируй|create|build|generate)\s+(?:сайт|лендинг|презентацию|слайды|website|landing|presentation)(?:\s+для|\s+на\s+тему|\s+про|\s+for|\s+about)?[:\s]*",
            "",
            prompt_text,
            flags=re.I,
        ).strip(" .!?") or "Современный проект"

        ai_prompt = (
            f"Generate a complete, single-file modern dark-themed HTML5 {'presentation with 5 slides (use Left/Right arrow keys)' if is_pres else 'landing page'} about: {topic}. "
            f"Include inline CSS with neon gradients, clean typography, cards, and call-to-action. Return ONLY valid HTML starting with <!DOCTYPE html>."
        )
        html_code = self.brain.ask_free_chat([{"role": "user", "content": ai_prompt}]) or ""
        m = re.search(r"<!DOCTYPE html>.*</html>", html_code, flags=re.S | re.I)
        final_html = m.group(0) if m else (
            f"<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'><title>{topic}</title>"
            f"<style>body{{background:#07090E;color:#fff;font-family:Segoe UI,sans-serif;padding:60px;text-align:center}}"
            f".box{{max-width:780px;margin:auto;background:#0D1117;border:1px solid #7C4DFF;border-radius:20px;padding:40px}}"
            f"h1{{color:#64FFDA;font-size:38px}}p{{font-size:18px;color:#C9D1D9}}</style></head>"
            f"<body><div class='box'><h1>{topic}</h1><p>Создано автоматически за 10 секунд с помощью AiPulsar Pro (VESKOR).</p></div></body></html>"
        )

        desk = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(desk, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "AiPulsar_Presentation" if is_pres else "AiPulsar_Site"
        out_html = os.path.join(desk, f"{prefix}_{ts}.html")
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(final_html)

        webbrowser.open(f"file:///{out_html.replace(os.sep, '/')}")
        return (
            f"Created and opened in browser: {os.path.basename(out_html)}"
            if is_en
            else f"Создал и открыл в браузере: {os.path.basename(out_html)}"
        )
