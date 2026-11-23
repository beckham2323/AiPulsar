# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import json
import os

_LANG_CACHE = None


def get_lang(models_dir: str = "models") -> str:
    global _LANG_CACHE
    if _LANG_CACHE in ("ru", "en"):
        return _LANG_CACHE
    cfg_path = os.path.join(models_dir, "app_lang.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                val = str(json.load(f).get("lang", "ru")).strip().lower()
                if val in ("ru", "en"):
                    _LANG_CACHE = val
                    return val
        except Exception:
            pass
    _LANG_CACHE = "ru"
    return "ru"


def set_lang(lang: str, models_dir: str = "models"):
    global _LANG_CACHE
    val = "en" if str(lang).strip().lower().startswith("en") else "ru"
    _LANG_CACHE = val
    os.makedirs(models_dir, exist_ok=True)
    try:
        with open(os.path.join(models_dir, "app_lang.json"), "w", encoding="utf-8") as f:
            json.dump({"lang": val}, f, indent=2)
    except Exception:
        pass


STRINGS = {
    "ru": {
        "voice_header": "Голосовое управление ПК с AiPulsar",
        "chat_header": "AiPulsar",
        "send_btn": "ОТПРАВИТЬ ↵",
        "you_prefix": "ВЫ ▸ ",
        "settings_title": "НАСТРОЙКИ PULSAR",
        "mic_level": "УРОВЕНЬ МИКРОФОНА",
        "mic_in": "МИКРОФОН (ВВОД)",
        "out_sp": "КОЛОНКИ / НАУШНИКИ (ВЫВОД)",
        "lang_lbl": "ЯЗЫК / LANGUAGE (ПЕРЕЗАПУСК)",
        "hotkeys_title": "ГОРЯЧИЕ КЛАВИШИ PULSAR",
        "check_upd": "⟳ ПРОВЕРИТЬ ОБНОВЛЕНИЯ",
        "checking_upd": "Проверяю наличие обновлений...",
        "hotkeys": [
            ("Ctrl + Alt + P", "Показать / свернуть окно Pulsar"),
            ("Enter", "Отправить команду или сообщение"),
            ("Ctrl + V / C / A", "Вставка, копирование и выделение"),
            ("Клик по пульсару", "Развернуть пульсар на весь экран"),
            ("Esc", "Выйти из полноэкранного режима"),
            ("Кнопка ✕", "Свернуть в трей (работа в фоне)"),
        ],
    },
    "en": {
        "voice_header": "Голосовое управление ПК с AiPulsar",
        "chat_header": "AiPulsar",
        "send_btn": "SEND ↵",
        "you_prefix": "YOU ▸ ",
        "settings_title": "PULSAR SETTINGS",
        "mic_level": "MICROPHONE LEVEL",
        "mic_in": "MICROPHONE (INPUT)",
        "out_sp": "SPEAKERS / HEADPHONES (OUTPUT)",
        "lang_lbl": "LANGUAGE (RESTART TO APPLY)",
        "hotkeys_title": "PULSAR HOTKEYS",
        "check_upd": "⟳ CHECK FOR UPDATES",
        "checking_upd": "Checking for updates...",
        "hotkeys": [
            ("Ctrl + Alt + P", "Show / hide Pulsar window"),
            ("Enter", "Send command or chat message"),
            ("Ctrl + V / C / A", "Paste, copy and select all"),
            ("Click Pulsar", "Toggle fullscreen pulsar mode"),
            ("Esc", "Exit fullscreen mode"),
            ("Button ✕", "Minimize to tray (background mode)"),
        ],
    },
}


def tr(key: str):
    lang = get_lang()
    return STRINGS.get(lang, STRINGS["ru"]).get(key, STRINGS["ru"].get(key, key))

