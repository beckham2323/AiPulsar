# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import time
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05


class VirtualHands:
    """Невидимое управление интерфейсом Windows без перехвата и перемещения курсора пользователя."""

    def __init__(self, vision):
        self.vision = vision

    def _ghost_click(self, x: int, y: int, double: bool = False, right: bool = False):
        orig_x, orig_y = pyautogui.position()
        try:
            if right:
                pyautogui.rightClick(int(x), int(y))
            elif double:
                pyautogui.doubleClick(int(x), int(y))
            else:
                pyautogui.click(int(x), int(y))
        finally:
            pyautogui.moveTo(orig_x, orig_y, duration=0)

    def move_to(self, x: int, y: int) -> str:
        return f"Точка ({x}, {y}) зафиксирована невидимым указателем."

    def click_at(self, x: int, y: int, double: bool = False, right: bool = False) -> str:
        self._ghost_click(x, y, double=double, right=right)
        return f"Невидимый клик выполнен в ({x}, {y})."

    def open_visual_folder_or_icon(self, label: str, on_desktop: bool = False) -> str:
        if on_desktop:
            pyautogui.hotkey("win", "d")
            time.sleep(0.5)

        coords = self.vision.find_text_coords(label)
        if not coords and not on_desktop:
            pyautogui.hotkey("win", "d")
            time.sleep(0.5)
            coords = self.vision.find_text_coords(label)

        if not coords:
            return f"Объект «{label}» на экране не найден."

        found_name, cx, cy = coords
        icon_y = max(20, cy - 22)
        self._ghost_click(cx, icon_y, double=True)
        time.sleep(0.5)
        return f"Невидимым кликом открыл «{found_name}»."

    def scroll_screen(self, direction: str = "вниз", amount: int = 500) -> str:
        clicks = -abs(int(amount)) if "вниз" in direction.lower() else abs(int(amount))
        pyautogui.scroll(clicks)
        return f"Прокрутил экран {direction}."

