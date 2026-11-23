# -*- coding: utf-8 -*-
import json
import math
import os
import re
import struct
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from core.ui_widgets import attach_tab_popup_to_main


def _is_clean_text(s: str) -> bool:
    if not s or "\ufffd" in s:
        return False
    return bool(re.fullmatch(r"[А-Яа-яЁёA-Za-z0-9\s\(\)\[\]\.,_\-\+/]+", s.strip()))


def _get_exact_windows_audio_devices() -> tuple:
    mics = []
    speakers = []
    try:
        ps_cmd = (
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            "Get-PnpDevice -Class AudioEndpoint -Status OK -ErrorAction SilentlyContinue | "
            "ForEach-Object { $_.InstanceId + '|' + $_.FriendlyName }"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5,
            creationflags=0x08000000,
        )
        for line in (proc.stdout or "").splitlines():
            if "|" not in line:
                continue
            inst_id, fname = line.split("|", 1)
            fname = fname.strip()
            if not fname or not _is_clean_text(fname):
                continue
            if "{0.0.1." in inst_id and fname not in mics:
                mics.append(fname)
            elif "{0.0.0." in inst_id and fname not in speakers:
                speakers.append(fname)
    except Exception:
        pass

    mics.insert(0, "Микрофон по умолчанию (Windows)")
    speakers.insert(0, "Динамики по умолчанию (Windows)")
    return mics, speakers


class AudioSettingsPopup:
    W11_BG = "#202020"
    W11_CARD = "#2B2B2B"
    W11_CARD_BORDER = "#383838"
    W11_CTRL = "#333333"
    W11_CTRL_HOVER = "#3D3D3D"
    W11_TEXT = "#FFFFFF"
    W11_SUBTEXT = "#A6A6A6"
    W11_ACCENT = "#60CDFF"
    W11_ACCENT_BTN = "#0078D4"
    W11_METER_BG = "#1A1A1A"

    def __init__(self, parent: tk.Misc, on_apply: Optional[Callable[[dict], None]] = None, models_dir: str = "models", **kwargs):
        self.parent = parent
        self.on_apply = on_apply
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.cfg_path = os.path.join(self.models_dir, "audio_prefs.json")
        self._win: Optional[tk.Toplevel] = None
        self._meter_running = False

    def _load_cfg(self) -> dict:
        if os.path.exists(self.cfg_path):
            try:
                with open(self.cfg_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cfg(self, data: dict):
        try:
            with open(self.cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def toggle(self):
        if self._win and self._win.winfo_exists():
            self._stop_and_destroy()
            return
        self.show()

    def _stop_and_destroy(self):
        self._meter_running = False
        if self._win and self._win.winfo_exists():
            try:
                self._win.destroy()
            except Exception:
                pass
        self._win = None

    def show(self):
        if self._win and self._win.winfo_exists():
            self._win.lift()
            self._win.focus_force()
            return

        mics, speakers = _get_exact_windows_audio_devices()
        cfg = self._load_cfg()

        win = tk.Toplevel(self.parent)
        self._win = win
        win.title("Параметры аудио — AiPulsar")
        win.configure(bg=self.W11_BG)
        win.geometry("510x420")
        win.resizable(False, False)

        win.option_add("*TCombobox*Listbox.background", self.W11_CARD)
        win.option_add("*TCombobox*Listbox.foreground", self.W11_TEXT)
        win.option_add("*TCombobox*Listbox.selectBackground", self.W11_CTRL_HOVER)
        win.option_add("*TCombobox*Listbox.selectForeground", self.W11_ACCENT)
        win.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))

        style = ttk.Style(win)
        try:
            style.theme_use("clam")
            style.configure("Win11Audio.TCombobox", fieldbackground=self.W11_CTRL, background=self.W11_CTRL, foreground=self.W11_TEXT, selectbackground=self.W11_CTRL, selectforeground=self.W11_TEXT, bordercolor="#484848", lightcolor=self.W11_CTRL, darkcolor=self.W11_CTRL, arrowcolor=self.W11_TEXT, padding=6)
            style.map("Win11Audio.TCombobox", fieldbackground=[("readonly", self.W11_CTRL)], background=[("readonly", self.W11_CTRL), ("active", self.W11_CTRL_HOVER)], foreground=[("readonly", self.W11_TEXT)])
        except Exception:
            pass

        top_bar = tk.Frame(win, bg=self.W11_BG)
        top_bar.pack(fill=tk.X, padx=20, pady=(14, 10))
        tk.Label(top_bar, text="Параметры аудио", bg=self.W11_BG, fg=self.W11_TEXT, font=("Segoe UI Semibold", 14)).pack(anchor="w")

        saved_mic = str(cfg.get("mic_name") or "").strip()
        if not _is_clean_text(saved_mic) or saved_mic not in mics:
            saved_mic = mics[0]
        mic_var = tk.StringVar(value=saved_mic)

        saved_spk = str(cfg.get("spk_name") or "").strip()
        if not _is_clean_text(saved_spk) or saved_spk not in speakers:
            saved_spk = speakers[0]
        spk_var = tk.StringVar(value=saved_spk)

        def _apply_and_save(_event=None):
            new_cfg = {"mic_name": mic_var.get(), "mic_index": None, "spk_name": spk_var.get(), "spk_index": None}
            self._save_cfg(new_cfg)
            if self.on_apply:
                try:
                    self.on_apply(new_cfg)
                except Exception:
                    pass

        out_card = tk.Frame(win, bg=self.W11_CARD, highlightthickness=1, highlightbackground=self.W11_CARD_BORDER)
        out_card.pack(fill=tk.X, padx=20, pady=(0, 8))
        out_inner = tk.Frame(out_card, bg=self.W11_CARD)
        out_inner.pack(fill=tk.X, padx=14, pady=12)
        tk.Label(out_inner, text="🔊  Вывод (динамики / наушники)", bg=self.W11_CARD, fg=self.W11_TEXT, font=("Segoe UI Semibold", 10)).pack(anchor="w")

        spk_cb = ttk.Combobox(out_inner, textvariable=spk_var, values=speakers, state="readonly", style="Win11Audio.TCombobox", font=("Segoe UI", 9))
        spk_cb.pack(fill=tk.X, pady=(6, 8))
        spk_cb.bind("<<ComboboxSelected>>", _apply_and_save)

        spk_meter_row = tk.Frame(out_inner, bg=self.W11_CARD)
        spk_meter_row.pack(fill=tk.X)
        tk.Label(spk_meter_row, text="Индикатор звука:", bg=self.W11_CARD, fg=self.W11_SUBTEXT, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 8))
        spk_canvas = tk.Canvas(spk_meter_row, height=10, bg=self.W11_METER_BG, highlightthickness=1, highlightbackground="#424242")
        spk_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        spk_bar = spk_canvas.create_rectangle(0, 0, 0, 12, fill=self.W11_ACCENT, width=0)

        def _test_speaker_audio():
            def _run_test():
                try:
                    ps_say = "Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Volume = 100; $s.Rate = 1; $s.Speak('Проверка динамиков. Звук работает отлично.');"
                    proc = subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_say], creationflags=0x08000000)
                    step = 0
                    while proc.poll() is None and self._meter_running:
                        step += 1
                        lvl = 0.35 + 0.55 * abs(math.sin(step * 0.45))
                        if win.winfo_exists():
                            w_px = max(1, int(spk_canvas.winfo_width() * lvl))
                            win.after(0, lambda wp=w_px: spk_canvas.coords(spk_bar, 0, 0, wp, 12))
                        time.sleep(0.06)
                except Exception:
                    pass
                finally:
                    if win.winfo_exists():
                        win.after(0, lambda: spk_canvas.coords(spk_bar, 0, 0, 0, 12))
            threading.Thread(target=_run_test, daemon=True).start()

        tk.Button(spk_meter_row, text="▶ Тест звука", command=_test_speaker_audio, bg=self.W11_CTRL, fg=self.W11_TEXT, activebackground=self.W11_CTRL_HOVER, activeforeground=self.W11_TEXT, highlightthickness=1, highlightbackground="#484848", relief=tk.FLAT, font=("Segoe UI", 8), padx=10, pady=2, cursor="hand2").pack(side=tk.RIGHT)

        in_card = tk.Frame(win, bg=self.W11_CARD, highlightthickness=1, highlightbackground=self.W11_CARD_BORDER)
        in_card.pack(fill=tk.X, padx=20, pady=(0, 14))
        in_inner = tk.Frame(in_card, bg=self.W11_CARD)
        in_inner.pack(fill=tk.X, padx=14, pady=12)
        tk.Label(in_inner, text="🎙️  Ввод (микрофон)", bg=self.W11_CARD, fg=self.W11_TEXT, font=("Segoe UI Semibold", 10)).pack(anchor="w")

        mic_cb = ttk.Combobox(in_inner, textvariable=mic_var, values=mics, state="readonly", style="Win11Audio.TCombobox", font=("Segoe UI", 9))
        mic_cb.pack(fill=tk.X, pady=(6, 8))
        mic_cb.bind("<<ComboboxSelected>>", _apply_and_save)

        mic_meter_row = tk.Frame(in_inner, bg=self.W11_CARD)
        mic_meter_row.pack(fill=tk.X)
        tk.Label(mic_meter_row, text="Уровень микрофона:", bg=self.W11_CARD, fg=self.W11_SUBTEXT, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 8))
        mic_canvas = tk.Canvas(mic_meter_row, height=10, bg=self.W11_METER_BG, highlightthickness=1, highlightbackground="#424242")
        mic_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        mic_bar = mic_canvas.create_rectangle(0, 0, 0, 12, fill="#3CCB5A", width=0)
        mic_pct_lbl = tk.Label(mic_meter_row, text="0%", bg=self.W11_CARD, fg=self.W11_SUBTEXT, font=("Segoe UI", 8), width=4, anchor="e")
        mic_pct_lbl.pack(side=tk.RIGHT)

        self._meter_running = True

        def _live_mic_meter_loop():
            pa = None
            stream = None
            try:
                import pyaudio
                pa = pyaudio.PyAudio()
                stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=512)
                while self._meter_running and win.winfo_exists():
                    data = stream.read(512, exception_on_overflow=False)
                    count = len(data) // 2
                    if count > 0:
                        shorts = struct.unpack(f"<{count}h", data)
                        rms = math.sqrt(sum(s * s for s in shorts) / count)
                        norm = min(1.0, rms / 4200.0)
                        pct = int(norm * 100)
                        if win.winfo_exists():
                            w_px = max(0, int(mic_canvas.winfo_width() * norm))
                            bar_col = "#FF5F56" if pct > 88 else ("#60CDFF" if pct > 45 else "#3CCB5A")
                            win.after(0, lambda wp=w_px, p=pct, c=bar_col: (mic_canvas.coords(mic_bar, 0, 0, wp, 12), mic_canvas.itemconfig(mic_bar, fill=c), mic_pct_lbl.config(text=f"{p}%")))
                    time.sleep(0.04)
            except Exception:
                pass
            finally:
                try:
                    if stream:
                        stream.stop_stream()
                        stream.close()
                except Exception:
                    pass
                try:
                    if pa:
                        pa.terminate()
                except Exception:
                    pass

        threading.Thread(target=_live_mic_meter_loop, daemon=True).start()

        footer = tk.Frame(win, bg=self.W11_BG)
        footer.pack(fill=tk.X, padx=20, pady=(0, 14))
        tk.Button(footer, text="🔄 Обновить устройства", command=lambda: (self._stop_and_destroy(), self.show()), bg=self.W11_CTRL, fg=self.W11_TEXT, activebackground=self.W11_CTRL_HOVER, activeforeground=self.W11_TEXT, highlightthickness=1, highlightbackground="#484848", relief=tk.FLAT, font=("Segoe UI", 9), padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT)
        tk.Button(footer, text="Готово", command=lambda: (_apply_and_save(), self._stop_and_destroy()), bg=self.W11_ACCENT_BTN, fg=self.W11_TEXT, activebackground="#106EBE", activeforeground=self.W11_TEXT, relief=tk.FLAT, font=("Segoe UI Semibold", 9), padx=18, pady=6, cursor="hand2").pack(side=tk.RIGHT)

        attach_tab_popup_to_main(self.parent, win)
        win.protocol("WM_DELETE_WINDOW", self._stop_and_destroy)
        win.lift()
        win.focus_force()
