from core.risk_advisor import PulsarRiskAdvisor, ADVISOR_SYSTEM_PROMPT
from core.i18n import get_lang
# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import datetime
import json
import os
import re
import subprocess
import time
import urllib.request
from typing import Any, Dict, List
from core.auto_bootstrap import LocalModelBootstrapper
from core.hardware_profiler import HardwareAutoProfiler
from core.hybrid_cloud import HybridCloudBrain
from core.web_agent import WebInternetAgent


class BrainEngine:
    """Гибридный когнитивный мозг Pulsar (локальная нейросеть + облачный контур + автоадаптация под железо)."""

    SYSTEM_PROMPT = """Ты — «Pulsar», автономный голосовой искусственный интеллект с ПОЛНЫМ ПРЯМЫМ ДОСТУПОМ к компьютеру пользователя на Windows.
КРИТИЧЕСКИ ВАЖНОЕ ПРАВИЛО ЯЗЫКА: Отвечай ИСКЛЮЧИТЕЛЬНО НА РУССКОМ ЯЗЫКЕ! Ни одного слова на английском языке в поле `reply` или в ответах пользователю!

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
1. {"plan": "план", "thought": "логика", "tool": "cmd_open", "args": {"target": "мой компьютер | браузер | диск d | загрузки | автокад | имя программы или сайта"}}
2. {"plan": "...", "thought": "...", "tool": "find_folder", "args": {"name": "название папки для поиска по всем дискам"}}
3. {"plan": "...", "thought": "...", "tool": "browser_search_tab", "args": {"query": "поисковый запрос", "platform": "yandex | youtube | vk"}}
4. {"plan": "...", "thought": "...", "tool": "inspect_pc", "args": {"path": "рабочий стол | загрузки | документы | диск c | диск d | полный путь"}}
5. {"plan": "...", "thought": "...", "tool": "create_folder", "args": {"path": "имя или полный путь папки"}}
6. {"plan": "...", "thought": "...", "tool": "search_files", "args": {"query": "имя файла или папки", "open": true}}
7. {"plan": "...", "thought": "...", "tool": "admin_cmd", "args": {"command": "точная команда для cmd.exe с правами Администратора"}}
8. {"plan": "...", "thought": "...", "tool": "copy_file", "args": {"src": "откуда", "dst": "куда"}}
9. {"plan": "...", "thought": "...", "tool": "move_file", "args": {"src": "откуда", "dst": "куда"}}
10. {"plan": "...", "thought": "...", "tool": "rename_file", "args": {"path": "путь", "new_name": "новое имя"}}
11. {"plan": "...", "thought": "...", "tool": "delete_file", "args": {"path": "путь для удаления в Корзину"}}
12. {"plan": "...", "thought": "...", "tool": "open_settings", "args": {"section": "звук | микрофон | bluetooth | wifi | экран | приложения | автозагрузка | обновления | диспетчер устройств | панель управления | настройки"}}
13. {"plan": "...", "thought": "...", "tool": "web_search", "args": {"query": "поисковый запрос"}}
14. {"plan": "...", "thought": "...", "tool": "yandex_news", "args": {"topic": "главные | владивосток | политика | экономика | технологии | спорт"}}
15. {"plan": "...", "thought": "...", "tool": "volume", "args": {"action": "громче | тише | выключить"}}
16. {"plan": "...", "thought": "...", "tool": "window", "args": {"action": "свернуть | переключить | развернуть | закрыть"}}
17. {"plan": "...", "thought": "...", "tool": "screenshot", "args": {}}
18. {"plan": "...", "thought": "итог", "tool": "finish", "args": {"reply": "Живой ответ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ"}}"""

    def __init__(self):
        self.api_url = "http://" + "127.0.0.1:11434/api/chat"
        self.hw = HardwareAutoProfiler()
        self.model = self._pick_best_installed_model(self.hw.config.get("preferred_models", ["oko-ru"]))
        self.web = WebInternetAgent()
        self.cloud = HybridCloudBrain()
        LocalModelBootstrapper(self.hw.config.get("preferred_models", [])).start_background_check()

    def _pick_best_installed_model(self, preferred: list) -> str:
        self._ensure_ollama()
        try:
            with urllib.request.urlopen("http://" + "127.0.0.1:11434/api/tags", timeout=1.5) as r:
                data = json.loads(r.read().decode("utf-8"))
                installed = [m.get("name", "") for m in data.get("models", [])]
                for pref in preferred:
                    for inst in installed:
                        if inst == pref or inst.startswith(pref + ":"):
                            return inst
                if installed:
                    return next(iter(installed))
        except Exception:
            pass
        return next(iter(preferred), "oko-ru")

    def _ensure_ollama(self):
        try:
            with urllib.request.urlopen("http://" + "127.0.0.1:11434/api/tags", timeout=1.0) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        ollama_exe = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
        cmd = [ollama_exe, "serve"] if os.path.exists(ollama_exe) else ["ollama", "serve"]
        try:
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1.5)
        except Exception:
            pass
    def _fast_intent(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        if not history:
            return {}
        last = next(reversed(history))
        raw_txt = str(last.get("content", ""))

        done_prefixes = (
            "[Результат open_app]:", "[Результат cmd_open]:", "[Результат find_folder]:",
            "[Результат browser_search_tab]:", "[Результат open_settings]:", "[Результат window]:",
            "[Результат volume]:", "[Результат screenshot]:", "[Результат create_folder]:",
            "[Результат sync_clone]:", "[Результат clone_edit_file]:", "[Результат clone_rollback]:",
        )
        if raw_txt.startswith(done_prefixes):
            res_clean = raw_txt.split(":", 1).pop().strip()
            return {"plan": "Готово", "thought": "Действие выполнено", "tool": "finish", "args": {"reply": f"Готово, {res_clean.lower()}"}}

        if "[Результат " in raw_txt:
            return {}

        parts = raw_txt.split("ЗАДАЧА ПОЛЬЗОВАТЕЛЯ:")
        cmd = (parts[-1] if parts else raw_txt).lower().strip(" .!?")

        if get_lang() == "en":
            m_en_open = re.match(r"^(?:pulsar[,\s]*)?(?:open|launch|start|run)\s+(.+)$", cmd)
            if m_en_open:
                tgt = m_en_open.group(1).strip(" .!?")
                if tgt in ("my computer", "this pc", "explorer", "file explorer"):
                    tgt = "мой компьютер"
                return {"plan": f"Open {tgt}", "thought": f"Launching {tgt}", "tool": "cmd_open", "args": {"target": tgt}}
            m_en_fld = re.match(r"^(?:pulsar[,\s]*)?(?:find|search|open)\s+folder\s+(.+)$", cmd)
            if m_en_fld:
                return {"plan": "Find folder", "thought": "Searching folder", "tool": "find_folder", "args": {"name": m_en_fld.group(1).strip(" .!?")}}
            m_en_web = re.match(r"^(?:pulsar[,\s]*)?(?:search|find|google|watch)\s+(.+?)(?:\s+online|\s+on youtube|\s+in browser)?$", cmd)
            if m_en_web and any(w in cmd for w in ("online", "youtube", "browser", "movie", "video")):
                plat = "youtube" if "youtube" in cmd else "yandex"
                return {"plan": "Web search", "thought": "Searching in browser", "tool": "browser_search_tab", "args": {"query": m_en_web.group(1).strip(), "platform": plat}}
            if "screenshot" in cmd:
                return {"plan": "Screenshot", "thought": "Taking screenshot", "tool": "screenshot", "args": {}}
            if "minimize" in cmd:
                return {"plan": "Minimize", "thought": "Minimizing windows", "tool": "window", "args": {"action": "свернуть"}}
            if "volume up" in cmd or "louder" in cmd:
                return {"plan": "Volume up", "thought": "Increasing volume", "tool": "volume", "args": {"action": "громче"}}
            if "volume down" in cmd or "quieter" in cmd:
                return {"plan": "Volume down", "thought": "Decreasing volume", "tool": "volume", "args": {"action": "тише"}}


        if any(w in cmd for w in ("в интернете", "в браузере", "в сети", "онлайн", "фильм", "сериал", "смотреть", "на ютубе", "в ютубе", "на youtube")):
            q_clean = re.sub(r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:найди|поищи|найти|поискать|включи|открой|покажи)(?:\s+мне)?\s+", "", cmd, flags=re.I)
            q_clean = re.sub(r"\b(?:в интернете|в браузере|в сети|на ютубе|в ютубе|на youtube)\b", "", q_clean, flags=re.I).strip(" .!?")
            plat = "youtube" if any(y in cmd for y in ("ютуб", "youtube")) else ("vk" if "вк" in cmd else "yandex")
            if q_clean:
                return {"plan": f"Поиск в браузере: {q_clean}", "thought": f"Ищу «{q_clean}»", "tool": "browser_search_tab", "args": {"query": q_clean, "platform": plat}}

        m_folder = re.match(r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:найди|поищи|открой|покажи|где(?:\s+находится)?)\s+папк[уаи]\s+(.+)$", cmd)
        if m_folder:
            fname = m_folder.group(1).strip(" .!?\"'«»")
            if fname:
                return {"plan": f"Поиск папки {fname}", "thought": f"Ищу папку «{fname}»", "tool": "find_folder", "args": {"name": fname}}

        if any(w in cmd for w in ("открой настройки", "настройки windows", "параметры windows", "панель управления", "диспетчер устройств", "настройки звука", "настройки микрофона", "настройки блютуз", "настройки wifi")):
            return {"plan": "Открыть настройки", "thought": "Открываю настройки", "tool": "open_settings", "args": {"section": cmd}}

        m_open = re.match(r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:открой|открыть|запусти|запустить|включи|включить)\s+(.+)$", cmd)
        if m_open:
            target_obj = m_open.group(1).strip(" .!?")
            if target_obj:
                return {"plan": f"Открыть {target_obj}", "thought": f"Запускаю «{target_obj}»", "tool": "cmd_open", "args": {"target": target_obj}}

        if any(w in cmd for w in ("мой компьютер", "этот компьютер", "проводник")):
            return {"plan": "Открыть Мой компьютер", "thought": "Открываю Мой компьютер", "tool": "cmd_open", "args": {"target": "мой компьютер"}}
        if "скриншот" in cmd or "снимок экрана" in cmd:
            return {"plan": "Скриншот", "thought": "Делаю снимок экрана", "tool": "screenshot", "args": {}}
        if "сверни все окна" in cmd:
            return {"plan": "Свернуть окна", "thought": "Сворачиваю окна", "tool": "window", "args": {"action": "свернуть"}}
        if "погромче" in cmd or "прибавь звук" in cmd:
            return {"plan": "Громче", "thought": "Прибавляю звук", "tool": "volume", "args": {"action": "громче"}}
        if "потише" in cmd or "убавь звук" in cmd:
            return {"plan": "Тише", "thought": "Убавляю звук", "tool": "volume", "args": {"action": "тише"}}
        return {}

    def _ensure_russian_text(self, text: str) -> str:
        if get_lang() == 'en':
            return (text or '').strip()
        clean = (text or "").strip()
        latin_cnt = len(re.findall(r"[A-Za-z]", clean))
        cyr_cnt = len(re.findall(r"[А-Яа-яЁё]", clean))
        if latin_cnt > 12 and latin_cnt > cyr_cnt * 0.35:
            try:
                payload = json.dumps({
                    "model": self.model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": "Переведи и перепиши этот текст ТОЛЬКО на чистом русском языке без единого английского слова."},
                        {"role": "user", "content": clean},
                    ],
                    "options": {"temperature": 0.2, "num_predict": 450},
                }).encode("utf-8")
                req = urllib.request.Request(self.api_url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    translated = data.get("message", {}).get("content", "").strip()
                    if translated:
                        return translated
            except Exception:
                pass
        return clean

    def _extract_json(self, raw: str) -> Dict[str, Any]:
        cleaned = raw.strip()
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if match:
            cleaned = match.group(0)
        try:
            res = json.loads(cleaned)
            if res.get("tool") == "finish" and isinstance(res.get("args"), dict) and "reply" in res["args"]:
                res["args"]["reply"] = self._ensure_russian_text(str(res["args"]["reply"]))
            return res
        except Exception:
            return {"plan": "Ответ", "thought": "Отвечаю", "tool": "finish", "args": {"reply": self._ensure_russian_text(raw[:250])}}

    def next_step(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        fast = self._fast_intent(history)
        if fast:
            return fast

        self._ensure_ollama()
        now = datetime.datetime.now()
        sys_msg = self.SYSTEM_PROMPT + f"\n[КОНТЕКСТ]: Владивосток, {now.strftime('%d.%m.%Y %H:%M')}. ОТВЕЧАЙ СТРОГО ПО-РУССКИ!"
        opts = {
            "temperature": 0.2,
            "num_predict": 380,
            "num_ctx": self.hw.config.get("num_ctx", 2048),
            "num_gpu": self.hw.config.get("num_gpu", 99),
        }
        payload = json.dumps({
            "model": self.model,
            "stream": False,
            "messages": [{"role": "system", "content": sys_msg}] + history + [{"role": "system", "content": ("Reply strictly in natural English inside JSON." if get_lang() == "en" else "Отвечай строго на русском языке в JSON.")}],
            "options": opts,
        }).encode("utf-8")
        try:
            req = urllib.request.Request(self.api_url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                return self._extract_json(content)
        except Exception as e:
            return {"plan": "Резервный ответ", "thought": f"Таймаут: {e}", "tool": "finish", "args": {"reply": "Я понял задачу, но нейросеть немного задумалась. Повтори команду, пожалуйста."}}

    def ask_free_chat(self, dialog_history: List[Dict[str, str]], memory_context: str = "") -> str:
        now = datetime.datetime.now()
        last_q = next(reversed(dialog_history)).get("content", "") if dialog_history else ""
        low_q = last_q.lower()

        live_web_data = ""
        if any(w in low_q for w in ("новост", "яндекс", "случилось", "происходит", "события", "владивосток")):
            topic = "владивосток" if "владивосток" in low_q else ("экономика" if "эконом" in low_q else ("технологии" if "технолог" in low_q else "главные"))
            live_web_data = self.web.get_yandex_news(topic)
        elif len(last_q.strip()) > 4 and not any(w in low_q for w in ("привет", "как дела", "спасибо", "кто ты")):
            live_web_data = self.web.search_internet(last_q)

        if self.cloud.is_online_split_active():
            cloud_ans = self.cloud.enhance_with_cloud(last_q, local_context=memory_context, web_context=live_web_data)
            if cloud_ans:
                return self._ensure_russian_text(cloud_ans)

        self._ensure_ollama()
        sys_prompt = (
            "Ты — «Pulsar», умный ИИ-ассистент с полным доступом к компьютеру пользователя на Windows, интернету и Яндекс Новостям. "
            "СТРОГОЕ ПРАВИЛО: Отвечай ИСКЛЮЧИТЕЛЬНО НА РУССКОМ ЯЗЫКЕ! Никогда не используй английский язык в ответах! "
            f"Контекст: Владивосток, {now.strftime('%d.%m.%Y %H:%M')}.\n{memory_context}\n\n"
            + (f"[АКТУАЛЬНЫЕ ДАННЫЕ ИЗ ИНТЕРНЕТА]:\n{live_web_data}" if live_web_data else "")
        )
        payload = json.dumps({
            "model": self.model,
            "stream": False,
            "messages": [{"role": "system", "content": sys_prompt}] + dialog_history[-10:] + [{"role": "system", "content": ("Reply strictly in natural English." if get_lang() == "en" else "Ответь строго на русском языке.")}],
            "options": {"temperature": 0.5, "num_predict": 550, "num_ctx": self.hw.config.get("num_ctx", 2048)},
        }).encode("utf-8")
        try:
            req = urllib.request.Request(self.api_url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                ans = data.get("message", {}).get("content", "").strip()
                return self._ensure_russian_text(ans) or "Я на связи и готов помочь. Уточни, пожалуйста, что нужно сделать?"
        except Exception as e:
            if live_web_data:
                return f"Вот что удалось найти прямо сейчас:\n{live_web_data[:600]}"
            return f"Сейчас нейросеть занята ({e}), попробуй повторить запрос."



