# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import os
import datetime
import os
import subprocess
import time
import urllib.parse
import webbrowser
import mss
import pyautogui
from PIL import Image


class SystemAndBrowserControl:
    """Управление громкостью, окнами, скриншотами, питанием ПК и браузером без рук."""

    SITES_MAP = {
        "youtube": "https://youtube.com",
        "ютуб": "https://youtube.com",
        "яндекс": "https://ya.ru",
        "погода": "https://yandex.ru",
        "почта": "https://yandex.ru",
        "вк": "https://vk.com",
        "вконтакте": "https://vk.com",
        "госуслуги": "https://gosuslugi.ru",
    }

    def volume_control(self, action: str) -> str:
        act = (action or "").lower().strip()
        if "выкл" in act or "mute" in act or "тиш" in act:
            pyautogui.press("volumemute")
            return "Звук переключён (без звука / включён)."
        if "громч" in act or "прибав" in act or "up" in act:
            for _ in range(5):
                pyautogui.press("volumeup")
            return "Громкость увеличена."
        if "тише" in act or "убав" in act or "down" in act:
            for _ in range(5):
                pyautogui.press("volumedown")
            return "Громкость уменьшена."
        return "Команда громкости выполнена."

    def window_control(self, action: str) -> str:
        act = (action or "").lower().strip()
        if "сверн" in act:
            pyautogui.hotkey("win", "d")
            return "Все окна свёрнуты."
        if "переключ" in act or "след" in act:
            pyautogui.hotkey("alt", "tab")
            return "Переключил активное окно."
        if "закр" in act:
            pyautogui.hotkey("alt", "f4")
            return "Активное окно закрыто."
        if "разверн" in act or "весь экран" in act:
            pyautogui.hotkey("win", "up")
            return "Окно развёрнуто на весь экран."
        return "Управление окном выполнено."

    def take_screenshot(self) -> str:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop", "Скриншоты_Pulsar")
        os.makedirs(desktop, exist_ok=True)
        fname = datetime.datetime.now().strftime("screen_%Y-%m-%d_%H-%M-%S.png")
        full_path = os.path.join(desktop, fname)
        with mss.mss() as sct:
            shot = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
            img.save(full_path)
        return f"Скриншот сохранён: {full_path}"

    def browser_open_or_search(self, target: str, search_query: str = "") -> str:
        key = (target or "").lower().strip()
        q = (search_query or "").strip()

        if ("youtube" in key or "ютуб" in key) and q:
            url = f"https://youtube.com/results?search_query={urllib.parse.quote(q)}"
            os.startfile(url)
            return f"Открыл YouTube с поиском: «{q}»."

        if q:
            url = f"https://ya.ru{urllib.parse.quote(q)}"
            os.startfile(url)
            return f"Открыл поиск Яндекса по запросу: «{q}»."

        url = self.SITES_MAP.get(key)
        if not url:
            url = target if target.startswith("http") else f"https://ya.ru{urllib.parse.quote(target)}"
        os.startfile(url)
        return f"Открыл в браузере: {url}"

    def power_control(self, action: str, minutes: int = 0) -> str:
        act = (action or "").lower().strip()
        if "отмен" in act:
            subprocess.run(["shutdown", "/a"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
            return "Таймер выключения отменён."
        if "выкл" in act:
            sec = max(60, int(minutes) * 60)
            subprocess.run(["shutdown", "/s", "/t", str(sec)], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
            return f"Компьютер выключится через {max(1, int(minutes))} мин."
        if "перезагр" in act:
            subprocess.run(["shutdown", "/r", "/t", "30"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
            return "Компьютер перезагрузится через 30 секунд."
        return "Команда питания выполнена."



