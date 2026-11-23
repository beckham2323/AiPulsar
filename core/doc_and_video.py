# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import datetime
import json
import os
import re
import subprocess
import threading
import time
import cv2
import docx
import mss
import numpy as np
import openpyxl


class PulsarDocAndVideoTools:
    """Генератор готовых Word (.docx) и Excel (.xlsx) документов по описанию + фоновая запись видео с экрана в .mp4."""

    def __init__(self, brain):
        self.brain = brain
        self._recording = False
        self._rec_path = ""
        self._rec_thread = None

    def create_office_document(self, command_text: str) -> str:
        low = command_text.lower()
        is_excel = any(w in low for w in ("excel", "эксель", "таблиц"))
        topic = re.sub(
            r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:создай|сделай|сгенерируй|напиши)\s+(?:файл\s+|документ\s+|таблицу\s+)?(?:word|ворд|excel|эксель)?\s*(?:с|про|на тему|по)?\s*",
            "",
            command_text,
            flags=re.I,
        ).strip(" .!?") or "Новый документ"

        out_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Pulsar_Документы")
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", topic)[:40].strip() or "Документ"

        if is_excel:
            out_xlsx = os.path.join(out_dir, f"{safe_title}_{ts}.xlsx")
            prompt = (
                f"Составь структуру таблицы Excel на русском языке по теме: «{topic}».\n"
                "Верни ответ СТРОГО в виде JSON-массива строк (список списков), где первая строка — заголовки столбцов, а следующие 8–15 строк — реалистичные заполненные данные. Никакого лишнего текста вокруг JSON."
            )
            raw = self.brain.ask_free_chat([{"role": "user", "content": prompt}])
            rows = []
            m = re.search(r"\[.*\]", raw, flags=re.S)
            if m:
                try:
                    rows = json.loads(m.group(0))
                except Exception:
                    rows = []
            if not rows or not isinstance(rows, list):
                rows = [["№", "Наименование", "Количество", "Примечание"], ["1", topic, "1", "Создано в Pulsar"]]

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Данные"
            for r in rows:
                if isinstance(r, list):
                    ws.append([str(c) for c in r])
            wb.save(out_xlsx)
            os.startfile(out_xlsx)
            return f"Создал Excel-таблицу «{os.path.basename(out_xlsx)}» на Рабочем столе и сразу открыл её."

        # Генерация документа Word (.docx)
        out_docx = os.path.join(out_dir, f"{safe_title}_{ts}.docx")
        prompt = (
            f"Напиши готовый, грамотно структурированный документ на чистом русском языке на тему: «{topic}».\n"
            "Разбей текст на заголовок и логические абзацы без Markdown-символов звёздочек и решёток."
        )
        content = self.brain.ask_free_chat([{"role": "user", "content": prompt}])
        clean_content = re.sub(r"[#*`]", "", content or topic).strip()

        doc = docx.Document()
        doc.add_heading(topic.capitalize(), level=1)
        for para in clean_content.splitlines():
            p = para.strip()
            if p:
                doc.add_paragraph(p)
        doc.save(out_docx)
        os.startfile(out_docx)
        return f"Создал Word-документ «{os.path.basename(out_docx)}» на Рабочем столе и сразу открыл его."

    def start_screen_recording(self) -> str:
        if self._recording:
            return "Запись экрана уже идёт. Скажи «Останови запись экрана», чтобы сохранить видео."

        vid_dir = os.path.join(os.path.expanduser("~"), "Videos", "Pulsar_Записи")
        os.makedirs(vid_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._rec_path = os.path.join(vid_dir, f"Запись_экрана_{ts}.mp4")
        self._recording = True

        def _record_loop():
            try:
                with mss.mss() as sct:
                    mon = sct.monitors[1 if len(sct.monitors) > 1 else 0]
                    w, h = int(mon["width"]), int(mon["height"])
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    writer = cv2.VideoWriter(self._rec_path, fourcc, 15.0, (w, h))
                    while self._recording:
                        t0 = time.time()
                        shot = sct.grab(mon)
                        frame = np.array(shot)[:, :, :3]
                        writer.write(frame)
                        dt = time.time() - t0
                        if dt < 0.065:
                            time.sleep(0.065 - dt)
                    writer.release()
            except Exception:
                self._recording = False

        self._rec_thread = threading.Thread(target=_record_loop, daemon=True)
        self._rec_thread.start()
        return "Начал запись экрана в видеофайл. Чтобы завершить, скажи «Останови запись экрана»."

    def stop_screen_recording(self) -> str:
        if not self._recording:
            return "Сейчас запись экрана не запущена."
        self._recording = False
        if self._rec_thread:
            self._rec_thread.join(timeout=3.0)
        saved = self._rec_path
        if saved and os.path.exists(saved):
            subprocess.Popen(["explorer.exe", f'/select,"{saved}"'])
            return f"Запись экрана остановлена и сохранена: {saved}"
        return "Запись экрана остановлена."


