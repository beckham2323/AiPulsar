# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import os
import re
import subprocess
import time
import urllib.parse
from typing import Any, Callable, Dict
import pyautogui
import pyperclip
from core.advanced_skills import AdvancedSkills
from core.digital_twin import PCDigitalTwin
from core.income_finder import LegalIncomeFinder
from core.pc_full_access import PCFullAccess
from core.power_skills import PowerSkills
class SystemController:
    def volume_control(self, action: str) -> str:
        act = action.lower()
        key = "volumemute" if "выкл" in act else ("volumedown" if "тиш" in act or "убав" in act else "volumeup")
        for _ in range(1 if key == "volumemute" else 4):
            pyautogui.press(key)
        return f"Громкость изменена ({action})."
    def window_control(self, action: str) -> str:
        act = action.lower()
        if "сверн" in act: pyautogui.hotkey("win", "d")
        elif "переключ" in act: pyautogui.hotkey("alt", "tab")
        elif "закр" in act: pyautogui.hotkey("alt", "f4")
        return f"Окно: {action}."
    def take_screenshot(self) -> str:
        import datetime, mss
        from PIL import Image
        out = os.path.join(os.path.expanduser("~"), "Desktop", f"Снимок_{datetime.datetime.now().strftime('%H%M%S')}.png")
        with mss.mss() as sct:
            s = sct.grab(sct.monitors[1 if len(sct.monitors) > 1 else 0])
            Image.frombytes("RGB", s.size, s.bgra, "raw", "BGRX").save(out)
        return "Скриншот сохранён на рабочий стол."

from core.virtual_hands import VirtualHands
from core.vision import ScreenVision
from core.web_agent import WebInternetAgent

pyautogui.FAILSAFE = False


class HandsExecutor:
    """Единый исполнитель действий «Ока» на компьютере и в интернете."""

    def __init__(self, speak_callback: Callable[[str], None] = None, models_dir: str = "models"):
        self.speak = speak_callback or (lambda text: None)
        self.vision = ScreenVision()
        self.vhands = VirtualHands(self.vision)
        self.web = WebInternetAgent()
        self.sys_ctrl = SystemController()
        self.power = PowerSkills()
        self.adv = AdvancedSkills()
        self.income = LegalIncomeFinder(self.web)
        self.pc = PCFullAccess()
        self.twin = PCDigitalTwin(models_dir=models_dir)

    def execute(self, tool: str, args: Dict[str, Any]) -> str:
        try:
            if tool == "browser_search_tab":
                return self.open_browser_search_tab(str(args.get("query", "")), str(args.get("platform", "yandex")))
            if tool == "find_folder":
                return self.pc.find_folder_everywhere(str(args.get("name", "")), auto_open=True)
            if tool in ("cmd_open", "open_app"):
                target = str(args.get("target") or args.get("name") or "")
                return self.smart_cmd_open(target)
            if tool == "open_settings":
                return self.pc.open_windows_settings(str(args.get("section", "настройки")))
            if tool == "inspect_pc":
                return self.pc.inspect_pc(str(args.get("path", "рабочий стол")))
            if tool == "search_files":
                return self.pc.search_files(str(args.get("query", "")), str(args.get("root", "")), auto_open=bool(args.get("open", True)))
            if tool == "create_folder":
                return self.pc.create_folder(str(args.get("path", "")))
            if tool == "copy_file":
                return self.pc.copy_or_move(str(args.get("src", "")), str(args.get("dst", "")), move=False)
            if tool == "move_file":
                return self.pc.copy_or_move(str(args.get("src", "")), str(args.get("dst", "")), move=True)
            if tool == "rename_file":
                return self.pc.rename_item(str(args.get("path", "")), str(args.get("new_name", "")))
            if tool == "delete_file":
                return self.pc.delete_to_trash(str(args.get("path", "")))
            if tool == "archive_file":
                return self.pc.archive_ops(str(args.get("action", "zip")), str(args.get("src", "")), str(args.get("dst", "")))
            if tool == "read_file":
                return self.pc.read_text_file(str(args.get("path", "")))
            if tool == "pc_shell":
                return self.pc.run_windows_shell(str(args.get("command", "")))
            if tool == "admin_cmd":
                return self.pc.run_admin_shell(str(args.get("command", "")))
            if tool == "sync_clone":
                return self.twin.sync_clone()
            if tool == "inspect_clone":
                return self.twin.inspect_clone_summary()
            if tool == "clone_edit_file":
                return self.twin.edit_via_clone_sandbox(str(args.get("file", "")), str(args.get("find", "")), str(args.get("replace", "")))
            if tool == "clone_rollback":
                return self.twin.rollback_last_backup(str(args.get("file", "")))
            if tool == "web_search":
                return self.web.search_internet(str(args.get("query", "")))
            if tool == "yandex_news":
                return self.web.get_yandex_news(str(args.get("topic", "главные")))
            if tool == "read_webpage":
                return self.web.read_webpage(str(args.get("url", "")))
            if tool == "read_screen":
                return self.vision.read_screen_summary()
            if tool == "click_text":
                return self.vision.click_by_text(str(args.get("text", "")), double_click=bool(args.get("double", False)))
            if tool == "open_visual_folder":
                return self.vhands.open_visual_folder_or_icon(str(args.get("name", "")), on_desktop=bool(args.get("desktop", False)))
            if tool == "mouse_click":
                return self.vhands.click_at(int(args.get("x", 0)), int(args.get("y", 0)), double=bool(args.get("double", False)), right=bool(args.get("right", False)))
            if tool == "scroll_screen":
                return self.vhands.scroll_screen(str(args.get("direction", "вниз")))
            if tool == "type_text":
                pyperclip.copy(str(args.get("text", "")))
                pyautogui.hotkey("ctrl", "v")
                return "Текст введён."
            if tool == "press_key":
                keys = args.get("keys", [])
                if isinstance(keys, list) and keys:
                    pyautogui.hotkey(*[str(k).lower() for k in keys])
                return f"Нажата комбинация {keys}."
            if tool == "volume":
                return self.sys_ctrl.volume_control(str(args.get("action", "громче")))
            if tool == "window":
                return self.sys_ctrl.window_control(str(args.get("action", "свернуть")))
            if tool == "screenshot":
                return self.sys_ctrl.take_screenshot()
            if tool == "browser_open":
                return self.open_browser_search_tab(str(args.get("query", "")), str(args.get("target", "yandex")))
            if tool == "calculate":
                return self.power.safe_calculate(str(args.get("expression", "")))
            if tool == "draw_house_cad":
                return self.adv.draw_house_in_autocad(
                    width_mm=int(args.get("width_mm", 10000)),
                    length_mm=int(args.get("length_mm", 8000)),
                    wall_thick=int(args.get("wall_thick", 400)),
                    title=str(args.get("title", "Проект дома")),
                )
            return f"Неизвестная команда: {tool}"
        except Exception as e:
            return f"Ошибка выполнения ({tool}): {e}"
    def open_browser_search_tab(self, query: str, platform: str = "yandex") -> str:
        """Открывает новую вкладку в браузере и сразу запускает поиск по запросу."""
        q = (query or "").strip(" .!?\"'«»")
        if not q:
            os.startfile("https://ya.ru")
            return "Открыла новую вкладку в браузере."

        encoded = urllib.parse.quote(q)
        plat = (platform or "yandex").lower()
        if "youtube" in plat or "ютуб" in plat:
            url = f"https://youtube.com{encoded}"
            place = "YouTube"
        elif "vk" in plat or "вк" in plat:
            url = f"https://vk.com{encoded}"
            place = "VK Видео"
        else:
            url = f"https://ya.ru{encoded}&lr=75"
            place = "Яндексе"

        os.startfile(url)
        return f"Открыла новую вкладку в браузере и ищу «{q}» в {place}."

    def smart_cmd_open(self, target: str) -> str:
        """Открывает любую программу, папку, файл, сайт или утилиту через скрытую командную строку Windows."""
        raw = (target or "").strip(" .!?\"'«»")
        low = raw.lower()
        if not low:
            return "Не указано, что нужно открыть."

        for prefix in ("пожалуйста", "мне", "папку", "программу", "файл", "сайт", "приложение"):
            low = re.sub(rf"\b{prefix}\b", "", low).strip()
            raw = re.sub(rf"\b{prefix}\b", "", raw, flags=re.I).strip()

        home = os.path.expanduser("~")
        direct_cmd_map = {
            "мой компьютер": "explorer.exe shell:MyComputerFolder",
            "этот компьютер": "explorer.exe shell:MyComputerFolder",
            "проводник": "explorer.exe",
            "рабочий стол": f'explorer.exe "{os.path.join(home, "Desktop")}"',
            "загрузки": f'explorer.exe "{os.path.join(home, "Downloads")}"',
            "документы": f'explorer.exe "{os.path.join(home, "Documents")}"',
            "диск c": 'explorer.exe "C:\\"',
            "диск с": 'explorer.exe "C:\\"',
            "диск d": 'explorer.exe "D:\\"',
            "диск д": 'explorer.exe "D:\\"',
            "браузер": "https://ya.ru",
            "интернет": "https://ya.ru",
            "яндекс": "https://ya.ru",
            "ютуб": "https://youtube.com",
            "youtube": "https://youtube.com",
            "вк": "https://vk.com",
            "вконтакте": "https://vk.com",
            "блокнот": "notepad.exe",
            "калькулятор": "calc.exe",
            "пейнт": "mspaint.exe",
            "paint": "mspaint.exe",
            "диспетчер задач": "taskmgr.exe",
            "панель управления": "control.exe",
            "настройки": "ms-settings:",
            "параметры": "ms-settings:",
            "командная строка": "cmd.exe",
            "терминал": "wt.exe",
            "реестр": "regedit.exe",
            "автокад": "acad.exe",
            "autocad": "acad.exe",
            "ворд": "winword.exe",
            "word": "winword.exe",
            "эксель": "excel.exe",
            "excel": "excel.exe",
            "телеграм": "tg://",
            "telegram": "tg://",
        }

        def _run_hidden_start(arg_str: str):
            subprocess.Popen(
                f'cmd /c start "" {arg_str}',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

        for k, cmd_target in direct_cmd_map.items():
            if k == low or k in low:
                quoted = cmd_target if cmd_target.startswith(("explorer.exe", "http", "tg://", "ms-settings:")) else f'"{cmd_target}"'
                _run_hidden_start(quoted)
                time.sleep(0.5)
                return f"Открыла «{raw or k}»."

        if re.match(r"^(https?://|www\.|[a-z0-9-]+\.(ru|com|org|net|io|рф))", low):
            url = raw if low.startswith("http") else f"https://{raw}"
            _run_hidden_start(f'"{url}"')
            time.sleep(0.5)
            return f"Открыла сайт {url}."

        search_dirs = [
            os.path.join(home, "Desktop"),
            os.path.join(os.environ.get("PUBLIC", r"C:\Users\Public"), "Desktop"),
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), r"Microsoft\Windows\Start Menu\Programs"),
        ]
        for base in search_dirs:
            if not base or not os.path.exists(base):
                continue
            for root, _, files in os.walk(base):
                for fn in files:
                    if low in fn.lower() and fn.lower().endswith((".lnk", ".url", ".exe", ".bat")):
                        full = os.path.join(root, fn)
                        _run_hidden_start(f'"{full}"')
                        time.sleep(0.5)
                        return f"Запустила «{os.path.splitext(fn)}»."

        found_res = self.pc.find_folder_everywhere(raw, auto_open=True)
        if "Нашёл папку" in found_res:
            return found_res

        found_file = self.pc.search_files(raw, auto_open=True)
        if "Нашёл и сразу открыл" in found_file:
            return found_file

        _run_hidden_start(f'"{raw}"')
        time.sleep(0.5)
        return f"Выполнила запуск «{raw}» через командную строку."


