# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import time
import mss
import numpy as np
import pyautogui
from PIL import Image
from rapidocr_onnxruntime import RapidOCR


class ScreenVision:
    """Компьютерное зрение экрана: распознавание всех значков и кнопок + клик мышью без рук."""

    def __init__(self):
        self._ocr = None

    @property
    def ocr(self):
        if self._ocr is None:
            self._ocr = RapidOCR()
        return self._ocr

    def _capture_screen(self) -> np.ndarray:
        with mss.mss() as sct:
            idx = 1 if len(sct.monitors) > 1 else 0
            shot = sct.grab(sct.monitors[idx])
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            return np.array(img)

    def read_screen_summary(self) -> str:
        frame = self._capture_screen()
        result, _ = self.ocr(frame)
        if not result:
            return "На экране не обнаружено читаемого текста или значков."

        lines = []
        for item in result[:55]:
            box, text, score = item[0], str(item[1]), float(item[2])
            if score >= 0.55 and text.strip():
                cx = int(sum(p[0] for p in box) / 4)
                cy = int(sum(p[1] for p in box) / 4)
                lines.append(f"«{text.strip()}» (x={cx}, y={cy})")

        return "Вижу на экране следующие значки и надписи:\n" + "\n".join(lines[:40])

    def click_by_text(self, target_text: str, double_click: bool = False) -> str:
        target = (target_text or "").lower().strip()
        if not target:
            return "Не указан текст значка для нажатия."

        frame = self._capture_screen()
        result, _ = self.ocr(frame)
        if not result:
            return "Не удалось распознать элементы на экране."

        for item in result:
            box, text, score = item[0], str(item[1]), float(item[2])
            if score >= 0.50 and target in text.lower():
                cx = int(sum(p[0] for p in box) / 4)
                cy = int(sum(p[1] for p in box) / 4)
                pyautogui.moveTo(cx, cy, duration=0.25)
                if double_click:
                    pyautogui.doubleClick()
                else:
                    pyautogui.click()
                return f"Нажал на значок «{text.strip()}» в точке ({cx}, {cy})."

        return f"Значок с надписью «{target_text}» на экране не найден."

    def click_desktop_icon(self, icon_name: str) -> str:
        """Сворачивает окна (Win+D), находит значок на Рабочем столе глазами и открывает его двойным кликом."""
        pyautogui.hotkey("win", "d")
        time.sleep(0.7)
        res = self.click_by_text(icon_name, double_click=True)
        return res

