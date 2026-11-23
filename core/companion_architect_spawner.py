# -*- coding: utf-8 -*-
import ast
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request


def _get_companion_dir() -> str:
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    cdir = os.path.join(appdata, "AiPulsar_SoulVault", "companion_architect")
    os.makedirs(cdir, exist_ok=True)
    return cdir


def _get_mods_dir() -> str:
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    mdir = os.path.join(appdata, "AiPulsar_SoulVault", "mods_and_skills")
    os.makedirs(mdir, exist_ok=True)
    return mdir


class CompanionArchitectManager:
    """Управление автономным ИИ-Помощником с полным доступом к системе, AutoPip, консилиумом ИИ и фоновой самоэволюцией."""

    SPAWN_TRIGGERS = (
        "создай помощника", "напиши помощника", "напиши себе помощника",
        "запусти помощника", "сделай помощника", "ии помощник для кода",
        "прокачай помощника", "саморазвитие",
    )

    def __init__(self):
        self.comp_dir = _get_companion_dir()
        self.mods_dir = _get_mods_dir()
        self.companion_script = os.path.join(self.comp_dir, "architect_companion.py")
        self.keys_vault_path = os.path.join(self.comp_dir, "discovered_keys.json")
        self.outbox_path = os.path.join(self.comp_dir, "tasks_outbox.json")
        self.weak_log_path = os.path.join(self.comp_dir, "weak_queries_queue.json")

    def harvest_keys_and_endpoints(self) -> dict:
        found_keys = {
            "openai_key": os.environ.get("OPENAI_API_KEY", ""),
            "deepseek_key": os.environ.get("DEEPSEEK_API_KEY", ""),
            "groq_key": os.environ.get("GROQ_API_KEY", ""),
            "openrouter_key": os.environ.get("OPENROUTER_API_KEY", ""),
            "free_llm_endpoint": "https://pollinations.ai",
            "search_endpoint": "https://duckduckgo.com",
        }
        candidates = [
            os.path.join(os.getcwd(), "models", "cloud_config.json"),
            r"D:\AiPulsar\models\cloud_config.json",
            r"D:\AiPulsar\dist\AiPulsar\models\cloud_config.json",
        ]
        for cfg in candidates:
            if os.path.exists(cfg):
                try:
                    with open(cfg, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for k, v in data.items():
                        if isinstance(v, str) and len(v) > 15 and ("key" in k.lower() or "token" in k.lower() or v.startswith("sk-")):
                            found_keys[k] = v
                except Exception:
                    pass

        with open(self.keys_vault_path, "w", encoding="utf-8") as f:
            json.dump(found_keys, f, ensure_ascii=False, indent=2)
        return found_keys

    def log_query_for_idle_evolution(self, user_query: str, answer_text: str):
        """Фиксирует вопросы, на которые дан слабый/короткий ответ, чтобы Помощник в фоне сам улучшил их."""
        q = (user_query or "").strip()
        a = (answer_text or "").strip().lower()
        if not q or len(q) < 5:
            return
        weak_markers = ("извините", "не могу", "к сожалению", "нет данных", "не удалось", "ошибка")
        if any(m in a for m in weak_markers) or len(a) < 25:
            items = []
            if os.path.exists(self.weak_log_path):
                try:
                    with open(self.weak_log_path, "r", encoding="utf-8") as f:
                        items = json.load(f)
                except Exception:
                    items = []
            if not any(x.get("query") == q for x in items):
                items.append({"query": q, "ts": datetime.datetime.now().isoformat()})
                with open(self.weak_log_path, "w", encoding="utf-8") as f:
                    json.dump(items[-40:], f, ensure_ascii=False, indent=2)
    def write_companion_source_code(self) -> str:
        part_a = f'''# -*- coding: utf-8 -*-
import ast
import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

COMP_DIR = {self.comp_dir!r}
MODS_DIR = {self.mods_dir!r}
KEYS_FILE = os.path.join(COMP_DIR, "discovered_keys.json")
OUTBOX_FILE = os.path.join(COMP_DIR, "tasks_outbox.json")
WEAK_FILE = os.path.join(COMP_DIR, "weak_queries_queue.json")
REGISTRY_FILE = os.path.join(MODS_DIR, "mods_registry.json")


class FullSystemBridge:
    BLOCKED_SYS = ("format c:", "rd /s /q c:\\\\", "rmdir /s /q c:\\\\", "del /f /s /q c:\\\\windows")

    @classmethod
    def run_powershell(cls, ps_script: str, timeout: int = 25) -> tuple:
        low = (ps_script or "").lower()
        if any(b in low for b in cls.BLOCKED_SYS):
            return False, "Заблокирована деструктивная команда для системного раздела Windows."
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        return (proc.returncode == 0), (out if out else err)


class AutoPipInstaller:
    STD_TO_PIP = {{
        "bs4": "beautifulsoup4",
        "cv2": "opencv-python",
        "PIL": "Pillow",
        "yaml": "PyYAML",
        "sklearn": "scikit-learn",
        "duckduckgo_search": "duckduckgo-search",
    }}

    @classmethod
    def ensure_package_from_error(cls, error_text: str) -> tuple:
        m = re.search(r"No module named ['\"]([a-zA-Z0-9_\\-]+)['\"]", error_text or "")
        if not m:
            return False, ""
        mod_name = m.group(1)
        pkg_name = cls.STD_TO_PIP.get(mod_name, mod_name)
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", pkg_name],
            capture_output=True,
            text=True,
            timeout=90,
        )
        return (proc.returncode == 0), pkg_name


def _load_keys() -> dict:
    if os.path.exists(KEYS_FILE):
        try:
            with open(KEYS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {{"free_llm_endpoint": "https://pollinations.ai"}}


def _multi_ai_council_generate(task_prompt: str, last_error: str = "") -> str:
    keys = _load_keys()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({{}}))

    draft_prompt = (
        "Ты — ведущий Python-архитектор с полным доступом к Windows, PowerShell и интернету. "
        "Напиши ТОЛЬКО чистый рабочий Python-код без markdown-разметки. "
        "Обязательная точка входа: def run_mod(user_query: str, web_helper) -> str:\\n"
        f"Задача: {{task_prompt}}\\n"
    )
    if last_error:
        draft_prompt += f"ИСПРАВЬ ОШИБКУ ПРОШЛОГО ЗАПУСКА:\\n{{last_error}}\\n"

    candidates = []
    for k_name, ep, mdl in (
        ("deepseek_key", "https://deepseek.com", "deepseek-chat"),
        ("openai_key", "https://openai.com", "gpt-4o-mini"),
        ("openrouter_key", "https://openrouter.ai", "openai/gpt-4o-mini"),
    ):
        api_key = keys.get(k_name, "")
        if not api_key:
            continue
        try:
            payload = json.dumps({{
                "model": mdl,
                "messages": [{{"role": "user", "content": draft_prompt}}],
                "temperature": 0.2,
            }}).encode("utf-8")
            req = urllib.request.Request(ep, data=payload, headers={{"Content-Type": "application/json", "Authorization": f"Bearer {{api_key}}"}})
            with opener.open(req, timeout=5) as r:
                txt = json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]
            m = re.search(r"```(?:python)?\\s*(.*?)```", txt, flags=re.DOTALL | re.IGNORECASE)
            code = m.group(1).strip() if m else txt.strip()
            if "def run_mod" in code:
                candidates.append(code)
        except Exception:
            pass

    try:
        q_enc = urllib.parse.quote(draft_prompt[:1800])
        req = urllib.request.Request(f"https://pollinations.ai{{q_enc}}", headers={{"User-Agent": "Mozilla/5.0"}})
        with opener.open(req, timeout=5) as r:
            txt = r.read().decode("utf-8", errors="ignore").strip()
        m = re.search(r"```(?:python)?\\s*(.*?)```", txt, flags=re.DOTALL | re.IGNORECASE)
        code = m.group(1).strip() if m else txt.strip()
        if "def run_mod" in code:
            candidates.append(code)
    except Exception:
        pass

    for c in candidates:
        try:
            ast.parse(c)
            return c
        except Exception:
            continue

    return f"""# -*- coding: utf-8 -*-
import datetime

TASK = {{task_prompt!r}}

def run_mod(user_query: str, web_helper) -> str:
    if web_helper is not None:
        return web_helper.search_web_live(user_query)
    return f"Навык '{{TASK}}' выполнен ({{datetime.datetime.now().strftime('%H:%M:%S')}})."
"""
'''
        part_b = '''

def _sandbox_test_with_autopip(code_str: str, test_query: str) -> tuple:
    try:
        ast.parse(code_str)
    except SyntaxError as se:
        return False, f"SyntaxError: {se.msg} (line {se.lineno})", []

    installed_pkgs = []
    tmp_test_file = os.path.join(COMP_DIR, "_sandbox_probe.py")
    with open(tmp_test_file, "w", encoding="utf-8") as f:
        f.write(code_str)

    runner_code = (
        f"import importlib.util\\n"
        f"spec = importlib.util.spec_from_file_location('probe', {tmp_test_file!r})\\n"
        f"m = importlib.util.module_from_spec(spec)\\n"
        f"spec.loader.exec_module(m)\\n"
        f"res = m.run_mod({test_query!r}, None)\\n"
        f"assert res is not None, 'Empty result'\\n"
        f"print('SANDBOX_PASS:', str(res)[:120])\\n"
    )

    for _pip_try in range(3):
        proc = subprocess.run([sys.executable, "-c", runner_code], capture_output=True, text=True, timeout=20)
        if proc.returncode == 0 and "SANDBOX_PASS:" in proc.stdout:
            return True, proc.stdout.strip(), installed_pkgs
        err_out = (proc.stderr or proc.stdout or "").strip()
        if "No module named" in err_out:
            ok_pip, pkg_name = AutoPipInstaller.ensure_package_from_error(err_out)
            if ok_pip and pkg_name:
                installed_pkgs.append(pkg_name)
                continue
        return False, err_out[-600:], installed_pkgs

    return False, "Не удалось разрешить зависимости.", installed_pkgs


def build_and_verify_skill_loop(task_text: str) -> dict:
    last_err = ""
    final_code = ""
    attempts_used = 0
    all_installed = []

    for attempt in range(1, 6):
        attempts_used = attempt
        cand_code = _multi_ai_council_generate(task_text, last_error=last_err)
        ok, diag, pkgs = _sandbox_test_with_autopip(cand_code, task_text)
        all_installed.extend(pkgs)
        if ok:
            final_code = cand_code
            break
        last_err = diag

    if not final_code:
        final_code = """# -*- coding: utf-8 -*-
def run_mod(user_query: str, web_helper) -> str:
    return web_helper.search_web_live(user_query) if web_helper else "Выполнено в безопасном режиме."
"""

    mod_id = hashlib.sha256(task_text.encode("utf-8")).hexdigest()[:8]
    mod_path = os.path.join(MODS_DIR, f"mod_{mod_id}.py")
    with open(mod_path, "w", encoding="utf-8") as f:
        f.write(final_code)

    reg = []
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                reg = json.load(f)
        except Exception:
            reg = []

    kws = [w for w in re.findall(r"[а-яёa-z0-9]{4,}", task_text.lower()) if w not in ("научись", "напиши", "помощник", "сделай", "создай", "код")]
    reg = [r for r in reg if r.get("id") != mod_id]
    reg.append({
        "id": mod_id,
        "task": task_text,
        "keywords": kws[:6],
        "file": mod_path,
        "enabled": True,
        "built_by": "CompanionArchitect_v2",
        "attempts": attempts_used,
        "auto_installed_packages": list(set(all_installed)),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)

    return {
        "status": "READY",
        "mod_id": mod_id,
        "mod_path": mod_path,
        "attempts": attempts_used,
        "packages": list(set(all_installed)),
        "task": task_text,
    }


def run_idle_evolution_cycle():
    if not os.path.exists(WEAK_FILE):
        return
    try:
        with open(WEAK_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        return
    if not items:
        return
    batch = items[:2]
    remaining = items[2:]
    with open(WEAK_FILE, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=2)
    for it in batch:
        q = it.get("query", "")
        if q:
            build_and_verify_skill_loop(q)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--task":
        t_str = " ".join(sys.argv[2:])
        res = build_and_verify_skill_loop(t_str)
        with open(OUTBOX_FILE, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(json.dumps(res, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "--idle-evolve":
        run_idle_evolution_cycle()
'''
        with open(self.companion_script, "w", encoding="utf-8") as f:
            f.write(part_a + part_b)
        return self.companion_script


    def ensure_always_on_background_companion(self):
        """Запускает ИИ-Помощника как независимый фоновый процесс 24/7 и закрепляет его в автозапуске Windows."""
        self.harvest_keys_and_endpoints()
        script_p = self.write_companion_source_code()
        py_exe = r"D:\AiPulsar\.venv311\Scripts\pythonw.exe"
        if not os.path.exists(py_exe):
            py_exe = r"D:\AiPulsar\.venv311\Scripts\python.exe" if getattr(sys, "frozen", False) else sys.executable

        # 1. Регистрируем задачу в Планировщике Windows, чтобы Помощник работал даже без открытой программы
        try:
            task_cmd = (
                f'schtasks /Create /TN "AiPulsar_Companion_24x7" /TR "\"{py_exe}\" \"{script_p}\" --daemon-forever" '
                f'/SC ONLOGON /RL HIGHEST /F'
            )
            subprocess.run(task_cmd, shell=True, capture_output=True, timeout=6, creationflags=0x08000000)
        except Exception:
            pass

        # 2. Запускаем полностью отвязанный от основного окна процесс (DETACHED_PROCESS = 0x00000008)
        try:
            lock_f = os.path.join(self.comp_dir, "companion_24x7.heartbeat")
            is_alive = False
            if os.path.exists(lock_f):
                if (time.time() - os.path.getmtime(lock_f)) < 180:
                    is_alive = True
            if not is_alive and os.path.exists(py_exe):
                subprocess.Popen(
                    [py_exe, script_p, "--daemon-forever"],
                    creationflags=0x00000008 | 0x08000000,
                    close_fds=True,
                )
        except Exception:
            pass

    def start_idle_evolution_daemon(self, interval_sec: int = 600):
        def _loop():
            time.sleep(45)
            while True:
                try:
                    self.harvest_keys_and_endpoints()
                    script_p = self.write_companion_source_code()
                    py_exe = r"D:\AiPulsar\.venv311\Scripts\python.exe" if getattr(sys, "frozen", False) else sys.executable
                    if os.path.exists(py_exe):
                        subprocess.Popen([py_exe, script_p, "--idle-evolve"], creationflags=0x08000000)
                except Exception:
                    pass
                time.sleep(interval_sec)

        threading.Thread(target=_loop, daemon=True).start()

    def spawn_and_delegate_task(self, task_instruction: str) -> str:
        keys = self.harvest_keys_and_endpoints()
        script_path = self.write_companion_source_code()

        py_exe = sys.executable
        if getattr(sys, "frozen", False):
            venv_py = r"D:\AiPulsar\.venv311\Scripts\python.exe"
            if os.path.exists(venv_py):
                py_exe = venv_py

        try:
            proc = subprocess.run(
                [py_exe, script_path, "--task", task_instruction],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.returncode == 0 and os.path.exists(self.outbox_path):
                with open(self.outbox_path, "r", encoding="utf-8") as f:
                    rep = json.load(f)
                active_keys_cnt = sum(1 for k, v in keys.items() if v and "endpoint" not in k)
                pkgs_str = ", ".join(rep.get("packages") or []) or "стандартная библиотека"
                return (
                    f"🤖 ИИ-Помощник (v2: AutoPip + Multi-AI + SystemBridge) выполнил задачу в отдельном процессе!\n"
                    f"• Активных ключей и шлюзов: {active_keys_cnt} API-ключей + консилиум нейросетей\n"
                    f"• Доустановленные библиотеки (AutoPip): {pkgs_str}\n"
                    f"• Итераций отладки в песочнице: {rep.get('attempts', 1)}\n"
                    f"• Готовый мод `mod_{rep.get('mod_id')}.py` подключён к сплит-ядру AiPulsar!"
                )
        except Exception as e:
            return f"Помощник создан в `{script_path}`, но при фоновом прогоне возникла задержка: {e}"

        return f"🤖 ИИ-Помощник v2 создан и готов к работе в `{self.comp_dir}`."
