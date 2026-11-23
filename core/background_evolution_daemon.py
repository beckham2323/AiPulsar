# -*- coding: utf-8 -*-
import os, subprocess, sys, time, winreg, psutil

def _is_daemon_running(pid_file: str) -> bool:
    if not os.path.exists(pid_file):
        return False
    try:
        pid = int(open(pid_file, "r", encoding="utf-8").read().strip())
        if psutil.pid_exists(pid):
            p = psutil.Process(pid)
            if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                return True
    except Exception:
        pass
    return False

def register_daemon_autostart(models_dir: str = "models"):
    try:
        exe_path = os.path.abspath(sys.executable)
        if getattr(sys, "frozen", False):
            cmd = f'"{exe_path}" --daemon-helper-tester'
        else:
            main_py = os.path.abspath("main.py")
            cmd = f'"{exe_path}" "{main_py}" --daemon-helper-tester'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "AiPulsarBackgroundBrain", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
    except Exception:
        pass

def ensure_background_daemon_started(models_dir: str = "models"):
    os.makedirs(models_dir, exist_ok=True)
    pid_file = os.path.join(models_dir, "daemon_ht.pid")
    register_daemon_autostart(models_dir)
    if _is_daemon_running(pid_file):
        return
    flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    if getattr(sys, "frozen", False):
        args = [sys.executable, "--daemon-helper-tester"]
    else:
        args = [sys.executable, os.path.abspath("main.py"), "--daemon-helper-tester"]
    subprocess.Popen(args, creationflags=flags, close_fds=True, cwd=os.getcwd())

def run_daemon_forever(models_dir: str = "models"):
    os.makedirs(models_dir, exist_ok=True)
    pid_file = os.path.join(models_dir, "daemon_ht.pid")
    if _is_daemon_running(pid_file):
        return
    with open(pid_file, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    from core.auto_evolution import PulsarAutoEvolutionEngine
    eng = PulsarAutoEvolutionEngine(models_dir=models_dir, notify_cb=None)
    eng.enabled = True
    while True:
        try:
            eng.run_helper_and_tester_cycle()
        except Exception:
            pass
        time.sleep(900.0)
