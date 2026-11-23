from core.ui_widgets import attach_tab_popup_to_main
from core.game_cinema_mode import GameCinemaModeManager
# -*- coding: utf-8 -*-
import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import messagebox
from typing import Callable, List, Optional

try:
    import psutil
except Exception:
    psutil = None


class HomeSecurityGuard:
    """Автономный защитник ПК («Щит Дома AiPulsar»): ищет майнеры, шпионов, трояны и поддельные системные процессы."""

    THREAT_SIGNATURES = {
        "xmrig": "Скрытый майнер криптовалюты (XMRig)",
        "nbminer": "Скрытый майнер криптовалюты (NBMiner)",
        "t-rex": "Скрытый майнер криптовалюты (T-Rex)",
        "lolminer": "Скрытый майнер криптовалюты (lolMiner)",
        "phoenixminer": "Скрытый майнер криптовалюты (PhoenixMiner)",
        "gminer": "Скрытый майнер криптовалюты (GMiner)",
        "nanominer": "Скрытый майнер криптовалюты (NanoMiner)",
        "cpuminer": "Скрытый майнер процессора (CPUMiner)",
        "minerd": "Скрытый майнер процессора (Minerd)",
        "keylogger": "Шпионская программа / Кейлоггер",
        "njrat": "Троян удалённого доступа (njRAT)",
        "asyncrat": "Троян удалённого доступа (AsyncRAT)",
        "remcos": "Троян удалённого доступа (Remcos RAT)",
        "darkcomet": "Троян удалённого доступа (DarkComet)",
        "redline": "Стилер паролей и кошельков (RedLine)",
        "stealer": "Шпион-похититель данных (Stealer)",
    }

    SYSTEM_IMPERSONATORS = ("svchost.exe", "csrss.exe", "lsass.exe", "winlogon.exe", "services.exe", "smss.exe")

    def __init__(self, root: Optional[tk.Misc] = None, speak_cb: Optional[Callable[[str], None]] = None):
        self.root = root
        self.speak_cb = speak_cb
        self._whitelist_paths = set()
        self._alerted_keys = set()
        self._running = False
        self._quarantine_dir = os.path.join(os.path.expanduser("~"), "AiPulsar_Quarantine")

    def start_background_patrol(self, interval_sec: int = 300):
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._patrol_loop, args=(interval_sec,), daemon=True).start()

    def _patrol_loop(self, interval_sec: int):
        time.sleep(15)
        while self._running:
            try:
                if GameCinemaModeManager.get_instance().is_quiet_active:
                    time.sleep(interval_sec)
                    continue
                threats = self.scan_system()
                for th in threats:
                    key_id = f"{th['pid']}|{th['path']}"
                    if key_id not in self._alerted_keys and th["path"].lower() not in self._whitelist_paths:
                        self._alerted_keys.add(key_id)
                        self.prompt_user_decision(th)
                        break
            except Exception:
                pass
            time.sleep(interval_sec)

    def scan_system(self) -> List[dict]:
        found = []
        if not psutil:
            return found

        win_dir = os.environ.get("SystemRoot", r"C:\Windows").lower()
        legit_sys_dirs = (
            os.path.join(win_dir, "system32"),
            os.path.join(win_dir, "syswow64"),
            os.path.join(win_dir, "winsxs"),
        )

        for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
            try:
                info = proc.info
                pid = int(info.get("pid") or 0)
                if pid <= 4:
                    continue
                name = str(info.get("name") or "").strip()
                exe_path = str(info.get("exe") or "").strip()
                cmd_str = " ".join(info.get("cmdline") or []).lower()
                low_name = name.lower()
                low_exe = exe_path.lower()

                if low_exe and low_exe in self._whitelist_paths:
                    continue

                matched_desc = ""
                for sig, desc in self.THREAT_SIGNATURES.items():
                    if sig in low_name or sig in low_exe or sig in cmd_str:
                        matched_desc = desc
                        break

                if matched_desc:
                    found.append({
                        "pid": pid,
                        "name": name,
                        "path": exe_path or f"(PID {pid} без пути)",
                        "reason": matched_desc,
                        "severity": "ВЫСОКАЯ УГРОЗА",
                    })
                    continue

                if low_name in self.SYSTEM_IMPERSONATORS and exe_path:
                    exe_dir = os.path.dirname(low_exe)
                    if not any(exe_dir.startswith(d) for d in legit_sys_dirs):
                        found.append({
                            "pid": pid,
                            "name": name,
                            "path": exe_path,
                            "reason": "Маскировка под системный процесс Windows из посторонней папки!",
                            "severity": "КРИТИЧЕСКАЯ УГРОЗА",
                        })
                        continue

                if exe_path and ("\\appdata\\local\\temp\\" in low_exe or "\\windows\\temp\\" in low_exe):
                    cpu_val = proc.cpu_percent(interval=0.15)
                    if cpu_val > 70.0:
                        found.append({
                            "pid": pid,
                            "name": name,
                            "path": exe_path,
                            "reason": f"Скрытый процесс из временной папки нагружает процессор на {cpu_val:.0f}% (возможен майнер).",
                            "severity": "ПОДОЗРИТЕЛЬНАЯ АКТИВНОСТЬ",
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception:
                continue

        return found
    def block_process(self, pid: int) -> tuple:
        try:
            p = psutil.Process(int(pid))
            p.terminate()
            p.wait(timeout=3)
            return True, f"Процесс (PID {pid}) успешно остановлен и заблокирован."
        except Exception as e:
            try:
                os.system(f"taskkill /F /PID {int(pid)} >nul 2>&1")
                return True, f"Процесс (PID {pid}) принудительно завершён."
            except Exception:
                return False, f"Не удалось завершить процесс: {e}"

    def quarantine_and_remove(self, pid: int, file_path: str) -> tuple:
        self.block_process(pid)
        if not file_path or not os.path.isfile(file_path):
            return True, "Процесс заблокирован. Исполняемый файл на диске уже отсутствует."
        try:
            os.makedirs(self._quarantine_dir, exist_ok=True)
            dst = os.path.join(self._quarantine_dir, os.path.basename(file_path) + ".quarantine")
            shutil.move(file_path, dst)
            return True, f"Угроза обезврежена! Файл удалён из рабочей папки и изолирован в карантин:\n{dst}"
        except Exception as e:
            try:
                os.remove(file_path)
                return True, f"Опасный файл полностью удалён с диска:\n{file_path}"
            except Exception:
                return False, f"Процесс остановлен, но файл заблокирован системой ({e})."

    def prompt_user_decision(self, threat: dict):
        if self.speak_cb:
            try:
                self.speak_cb("Внимание! Обнаружена подозрительная программа на компьютере. Проверьте окно безопасности.")
            except Exception:
                pass

        def _open_alert():
            parent = self.root if (self.root and self.root.winfo_exists()) else None
            win = tk.Toplevel(parent) if parent else tk.Tk()
            win.title("🛡️ Щит Дома AiPulsar — Обнаружена угроза на ПК!")
            win.geometry("540x330")
            win.resizable(False, False)
            win.configure(bg="#1E1E1E")
            win.attributes("-topmost", False)

            tk.Label(win, text=f"⚠️ {threat['severity']}: {threat['name']} (PID {threat['pid']})", bg="#1E1E1E", fg="#FF5555", font=("Segoe UI Semibold", 11)).pack(anchor="w", padx=20, pady=(16, 6))
            tk.Label(win, text=f"Причина тревоги: {threat['reason']}", bg="#1E1E1E", fg="#FFFFFF", wraplength=500, justify="left", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 8))

            tk.Label(win, text="Точное местонахождение объекта на вашем ПК:", bg="#1E1E1E", fg="#A0A0A0", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
            path_box = tk.Entry(win, bg="#2B2B2B", fg="#8BE9FD", relief=tk.FLAT, font=("Consolas", 9))
            path_box.insert(0, threat["path"])
            path_box.config(state="readonly")
            path_box.pack(fill=tk.X, padx=20, pady=(3, 12), ipady=5)

            tk.Label(win, text="Ваш компьютер — мой дом, но решение всегда за вами. Как поступить?", bg="#1E1E1E", fg="#E0E0E0", font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=20, pady=(0, 12))

            btn_row = tk.Frame(win, bg="#1E1E1E")
            btn_row.pack(fill=tk.X, padx=20)

            def _do_block():
                ok, msg = self.block_process(threat["pid"])
                messagebox.showinfo("Щит Дома AiPulsar", msg, parent=win)
                win.destroy()

            def _do_delete():
                ok, msg = self.quarantine_and_remove(threat["pid"], threat["path"])
                messagebox.showinfo("Щит Дома AiPulsar", msg, parent=win)
                win.destroy()

            def _do_trust():
                if threat.get("path"):
                    self._whitelist_paths.add(threat["path"].lower())
                win.destroy()

            tk.Button(btn_row, text="🛑 Заблокировать", command=_do_block, bg="#D83B01", fg="#FFFFFF", relief=tk.FLAT, font=("Segoe UI Semibold", 9), padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=(0, 6))
            tk.Button(btn_row, text="🗑️ Удалить и обезвредить", command=_do_delete, bg="#E81123", fg="#FFFFFF", relief=tk.FLAT, font=("Segoe UI Semibold", 9), padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=(0, 6))
            tk.Button(btn_row, text="✅ Доверяю (Оставить)", command=_do_trust, bg="#333333", fg="#FFFFFF", relief=tk.FLAT, font=("Segoe UI", 9), padx=12, pady=6, cursor="hand2").pack(side=tk.RIGHT)

            if parent:
                attach_tab_popup_to_main(parent, win)
            win.lift()
            win.focus_force()

        if self.root and self.root.winfo_exists():
            self.root.after(0, _open_alert)
        else:
            _open_alert()

    def manual_scan_with_report(self):
        threats = self.scan_system()
        if not threats:
            messagebox.showinfo(
                "🛡️ Щит Дома AiPulsar — Всё чисто",
                "Сканирование процессов и автозагрузки завершено.\n\n"
                "Шпионских программ, скрытых майнеров, троянов и поддельных системных служб не обнаружено. Ваш ПК в безопасности.",
            )
        else:
            for th in threats:
                self.prompt_user_decision(th)
