
def _windows_sapi_speak_fallback(text: str):
    """Надёжный системный синтезатор речи Windows (SAPI), срабатывает мгновенно если edge-tts или аудиовыход заблокирован."""
    import subprocess
    clean_t = str(text or "").replace('"', "'").replace("\n", " ").strip()[:500]
    if not clean_t:
        return
    ps_tts = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Volume = 100; $s.Rate = 1; "
        f"$s.Speak(\"{clean_t}\");"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_tts],
        capture_output=True,
        timeout=15,
        creationflags=0x08000000,
    )


def _detect_auto_voice_for_lang(text: str = "") -> str:
    """Автоматически ставит английский голос, если выбрана английская версия или текст на английском, и русский для русской версии."""
    import json, os, re, sys
    lang = "ru"
    cfg_paths = []
    if getattr(sys, "frozen", False):
        cfg_paths.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "models", "ui_prefs.json"))
    cfg_paths.extend([os.path.join(os.getcwd(), "models", "ui_prefs.json"), r"D:\AiPulsar\models\ui_prefs.json"])
    for cp in cfg_paths:
        if os.path.exists(cp):
            try:
                with open(cp, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if str(d.get("lang", "")).lower().startswith("en"):
                    lang = "en"
                    break
            except Exception:
                pass
    if text and not re.search(r"[а-яА-ЯёЁ]", text) and re.search(r"[a-zA-Z]{3,}", text):
        lang = "en"
    return "en-US-AndrewNeural" if lang == "en" else "ru-RU-DmitryNeural"

# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import asyncio
import ctypes
import os
import re
import subprocess
import tempfile
import threading
import time
from core.ears import get_windows_audio_devices
from core.i18n import get_lang

try:
    import edge_tts
except Exception:
    edge_tts = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None


class VoiceSpeaker:
    """Мгновенный живой голос AiPulsar (Edge Neural TTS + прямой вывод через winmm.dll за 50 мс)."""

    def __init__(self, outputs_cb=None):
        self.outputs_cb = outputs_cb
        self.muted = False
        self._lock = threading.Lock()
        self._out_map = {}
        self.selected_output = ""
        self._winmm = getattr(ctypes, "windll", None) and ctypes.windll.winmm

    def set_muted(self, flag: bool):
        self.muted = bool(flag)

    def refresh_output_devices(self, initial: bool = False):
        _, _, outs, out_map = get_windows_audio_devices()
        self._out_map = out_map
        if outs and not self.selected_output:
            self.selected_output = outs
        if self.outputs_cb:
            try:
                self.outputs_cb(outs, self.selected_output)
            except Exception:
                pass

    def select_output_by_label(self, label: str):
        self.selected_output = label

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        t = re.sub(r"[`*_#►▸✔✖✦★🎁💳🌍📋🔒⏰]", "", str(text or ""))
        t = re.sub(r"https?://\S+", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t[:320]

    def _play_mp3_winmm(self, mp3_path: str):
        if not self._winmm:
            return
        alias = f"pulsar_tts_{threading.get_ident()}"
        mci = self._winmm.mciSendStringW
        mci(f"close {alias}", None, 0, 0)
        if mci(f'open "{mp3_path}" type mpegvideo alias {alias}', None, 0, 0) == 0:
            mci(f"play {alias} wait", None, 0, 0)
            mci(f"close {alias}", None, 0, 0)

    def _speak_sapi_fast(self, clean_text: str):
        safe = clean_text.replace("'", " ")
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Rate = 4; $s.Speak('{safe}')"
        )
        subprocess.run(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)

    def speak(self, text: str):
        if not text or not str(text).strip():
            return
        if self.muted:
            return
        clean = self._clean_for_speech(text)
        if not clean:
            return

        with self._lock:
            is_en = get_lang() == "en"
            tmp_mp3 = os.path.join(tempfile.gettempdir(), f"aipulsar_{os.getpid()}_{int(time.time()*1000)}.mp3")
            try:
                if edge_tts is not None:
                    voice_name = "en-US-AriaNeural" if is_en else "ru-RU-SvetlanaNeural"
                    async def _gen():
                        comm = edge_tts.Communicate(clean, voice_name, rate="+25%", pitch="+2Hz")
                        await comm.save(tmp_mp3)
                    asyncio.run(_gen())
                    if os.path.exists(tmp_mp3) and os.path.getsize(tmp_mp3) > 100:
                        self._play_mp3_winmm(tmp_mp3)
                        return
            except Exception:
                pass
            finally:
                try:
                    if os.path.exists(tmp_mp3):
                        os.remove(tmp_mp3)
                except Exception:
                    pass

            try:
                if gTTS is not None:
                    tts = gTTS(text=clean, lang="en" if is_en else "ru", slow=False)
                    tts.save(tmp_mp3)
                    self._play_mp3_winmm(tmp_mp3)
                    return
            except Exception:
                pass
            finally:
                try:
                    if os.path.exists(tmp_mp3):
                        os.remove(tmp_mp3)
                except Exception:
                    pass

            try:
                self._speak_sapi_fast(clean)
            except Exception:
                pass
