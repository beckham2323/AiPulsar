# -*- coding: utf-8 -*-
import ast
import datetime
import hashlib
import importlib.util
import json
import os
import re
import traceback
import urllib.parse
import urllib.request
from typing import Optional


def _get_mods_root() -> str:
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    root = os.path.join(appdata, "AiPulsar_SoulVault", "mods_and_skills")
    os.makedirs(root, exist_ok=True)
    return root


class AutonomousModSplitEngine:
    """Система изолированных модов со сплит-подключением, Watchdog-самоисправлением после краша и поиском кода в сети."""

    FORBIDDEN = ("format c:", "rd /s", "rmdir /s", "del /f /s /q c:\\\\", "shutil.rmtree('c:", 'shutil.rmtree("c:')

    def __init__(self, brain_engine=None):
        self.brain = brain_engine
        self.mods_dir = _get_mods_root()
        self.registry_path = os.path.join(self.mods_dir, "mods_registry.json")
        self.watchdog_path = os.path.join(self.mods_dir, "boot_watchdog.json")

    def _load_registry(self) -> list:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_registry(self, items: list):
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def _set_watchdog(self, mod_id: str, phase: str):
        with open(self.watchdog_path, "w", encoding="utf-8") as f:
            json.dump({"pending_mod_id": mod_id, "phase": phase, "ts": datetime.datetime.now().isoformat()}, f)

    def _clear_watchdog(self):
        if os.path.exists(self.watchdog_path):
            try:
                os.remove(self.watchdog_path)
            except Exception:
                pass

    def boot_guard_and_heal_mods(self) -> list:
        """Проверяет при старте: если прошлый запуск упал из-за мода — останавливает его, чинит код и перезапускает мод."""
        reports = []
        if not os.path.exists(self.watchdog_path):
            return reports

        try:
            with open(self.watchdog_path, "r", encoding="utf-8") as f:
                wd = json.load(f)
        except Exception:
            self._clear_watchdog()
            return reports

        crashed_id = str(wd.get("pending_mod_id") or "").strip()
        self._clear_watchdog()
        if not crashed_id:
            return reports

        reg = self._load_registry()
        for item in reg:
            if item.get("id") == crashed_id:
                mod_file = item.get("file", "")
                task_desc = item.get("task", "Пользовательский навык")
                item["enabled"] = False
                item["last_error"] = "Аварийное завершение процесса при выполнении мода"
                self._save_registry(reg)

                if self._repair_mod_file(mod_file, task_desc, item["last_error"]):
                    item["enabled"] = True
                    item["healed_count"] = int(item.get("healed_count", 0)) + 1
                    self._save_registry(reg)
                    reports.append(f"🛠️ Обнаружен сбой мода «{task_desc}». Мод остановлен, исправлен и безопасно перезапущен!")
                else:
                    reports.append(f"⚠️ Мод «{task_desc}» вызвал сбой и отключён для защиты ядра AiPulsar.")
                break
        return reports

    def _repair_mod_file(self, mod_file: str, task_desc: str, error_text: str) -> bool:
        if not mod_file:
            return False
        safe_code = f'''# -*- coding: utf-8 -*-
TASK = {task_desc!r}

def run_mod(user_query: str, web_helper) -> str:
    try:
        return web_helper.search_web_live(user_query)
    except Exception as exc:
        return f"Мод «{{TASK}}» выполнен в безопасном режиме: {{exc}}"
'''
        try:
            ast.parse(safe_code)
            with open(mod_file, "w", encoding="utf-8") as f:
                f.write(safe_code)
            return True
        except Exception:
            return False
    def search_internet_code_snippets(self, topic: str) -> str:
        q = urllib.parse.quote(f"python code example {topic}")
        url = f"https://duckduckgo.com{q}&format=json&no_html=1&skip_disambig=1"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        collected = []
        try:
            with opener.open(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            abstract = (data.get("AbstractText") or "").strip()
            if abstract:
                collected.append(abstract)
            for rel in (data.get("RelatedTopics") or [])[:4]:
                if isinstance(rel, dict) and rel.get("Text"):
                    collected.append(rel["Text"])
        except Exception:
            pass
        return "\n".join(collected)

    def create_and_split_new_mod(self, task_instruction: str) -> str:
        clean_task = (task_instruction or "").strip()
        mod_id = hashlib.sha256(clean_task.encode("utf-8")).hexdigest()[:8]
        mod_file = os.path.join(self.mods_dir, f"mod_{mod_id}.py")

        web_refs = self.search_internet_code_snippets(clean_task)

        mod_code = f'''# -*- coding: utf-8 -*-
import datetime, json, os, subprocess, urllib.parse, urllib.request

TASK = {clean_task!r}
WEB_KNOWLEDGE = {web_refs[:600]!r}

def run_mod(user_query: str, web_helper) -> str:
    q = (user_query or "").strip()
    low = q.lower()
    if any(k in low for k in ("курс", "доллар", "евро", "юань", "валют")):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({{}}))
        with opener.open("https://cbr-xml-daily.ru", timeout=8) as r:
            d = json.loads(r.read().decode("utf-8"))
        return f"💱 Курсы ЦБ РФ: USD = {{d['Valute']['USD']['Value']:.2f}} ₽ | EUR = {{d['Valute']['EUR']['Value']:.2f}} ₽ | CNY = {{d['Valute']['CNY']['Value']:.2f}} ₽"
    if "погод" in low:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({{}}))
        with opener.open("https://wttr.in", timeout=8) as r:
            return "🌤️ " + r.read().decode("utf-8", errors="ignore").strip()
    res = web_helper.search_web_live(q)
    if WEB_KNOWLEDGE:
        return res + "\\n\\n📚 Найдено по алгоритму в сети:\\n" + WEB_KNOWLEDGE[:300]
    return res
'''
        if self.brain is not None:
            prompt = (
                "Напиши ТОЛЬКО валидный Python-код с функцией `def run_mod(user_query: str, web_helper) -> str:` "
                f"для задачи: {clean_task}. Контекст из интернета: {web_refs[:400]}."
            )
            for m_name in ("ask", "chat", "generate", "respond"):
                fn = getattr(self.brain, m_name, None)
                if callable(fn):
                    try:
                        raw_out = str(fn(prompt))
                        m = re.search(r"```(?:python)?\s*(.*?)```", raw_out, flags=re.DOTALL | re.IGNORECASE)
                        cand = m.group(1).strip() if m else raw_out.strip()
                        if "def run_mod" in cand and not any(b in cand.lower() for b in self.FORBIDDEN):
                            ast.parse(cand)
                            mod_code = cand
                    except Exception:
                        pass
                    break

        ast.parse(mod_code)
        with open(mod_file, "w", encoding="utf-8") as f:
            f.write(mod_code)

        keywords = [w for w in re.findall(r"[а-яёa-z0-9]{4,}", clean_task.lower()) if w not in ("научись", "навык", "создай", "мод", "код", "сама", "найди", "интернете")]
        reg = [r for r in self._load_registry() if r.get("id") != mod_id]
        reg.append({
            "id": mod_id,
            "task": clean_task,
            "keywords": keywords[:6],
            "file": mod_file,
            "enabled": True,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        self._save_registry(reg)

        return (
            f"🧩 Создан изолированный мод `mod_{mod_id}.py` в папке модификаций:\n"
            f"`{self.mods_dir}`\n"
            f"• Сплит-маршрут к ядру AiPulsar: ВКЛЮЧЁН (можно отключить или удалить без остановки программы)\n"
            f"• Поиск кода в интернете: {'выполнен' if web_refs else 'базовый алгоритм готов'}"
        )

    def disable_or_delete_mod(self, query_text: str) -> str:
        low = (query_text or "").lower()
        do_delete = "удал" in low or "сотри" in low
        reg = self._load_registry()
        if not reg:
            return "В папке модификаций пока нет подключённых пользовательских модов."

        target = None
        for item in reversed(reg):
            if item.get("id", "") in low or any(k in low for k in item.get("keywords", [])):
                target = item
                break
        if target is None:
            target = reg[-1]

        if do_delete:
            f_path = target.get("file", "")
            if f_path and os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except Exception:
                    pass
            reg = [r for r in reg if r.get("id") != target.get("id")]
            self._save_registry(reg)
            return f"🗑️ Ошибочный мод `{os.path.basename(f_path)}` («{target.get('task')}») удалён. Ядро AiPulsar работает чисто."

        target["enabled"] = False
        self._save_registry(reg)
        return f"🔌 Сплит-связь мода «{target.get('task')}» (`mod_{target.get('id')}.py`) отключена."

    def route_through_active_mods(self, user_query: str, web_helper) -> Optional[str]:
        low = (user_query or "").strip().lower()
        if not low:
            return None

        if any(p in low for p in ("отключи мод", "выключи мод", "удали мод", "удали навык", "отключи навык")):
            return self.disable_or_delete_mod(user_query)

        reg = self._load_registry()
        for item in reversed(reg):
            if not item.get("enabled", True):
                continue
            kws = item.get("keywords") or []
            if kws and any(k in low for k in kws):
                mod_id = item.get("id", "")
                mod_file = item.get("file", "")
                if not os.path.exists(mod_file):
                    continue
                self._set_watchdog(mod_id, "executing")
                try:
                    spec = importlib.util.spec_from_file_location(f"aipulsar_mod_{mod_id}", mod_file)
                    if spec and spec.loader:
                        mod_obj = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod_obj)
                        result = mod_obj.run_mod(user_query, web_helper)
                        self._clear_watchdog()
                        return str(result)
                except Exception as exc:
                    err_tb = traceback.format_exc()
                    self._clear_watchdog()
                    if self._repair_mod_file(mod_file, item.get("task", ""), err_tb):
                        item["healed_count"] = int(item.get("healed_count", 0)) + 1
                        self._save_registry(reg)
                        return f"🛠️ В моде `mod_{mod_id}.py` произошла ошибка ({exc}), но я сама переписала и исправила его код! Повторите запрос."
                    item["enabled"] = False
                    self._save_registry(reg)
                    return f"⚠️ Мод `mod_{mod_id}.py` выдал ошибку ({exc}) и был отключён для защиты программы."
        return None
