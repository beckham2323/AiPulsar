# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import collections
import math
import pathlib
import queue
import struct
import threading
import time

try:
    import speech_recognition as sr
except FileNotFoundError as _e:
    _missing = pathlib.Path(str(_e.filename or ""))
    if _missing.name == "version.txt":
        _missing.parent.mkdir(parents=True, exist_ok=True)
        _missing.write_text("3.14.0\n", encoding="utf-8")
    import speech_recognition as sr

try:
    import pyaudio
except Exception:
    pyaudio = None

try:
    import sounddevice as sd
except Exception:
    sd = None

from core.i18n import get_lang


def _fix_win_device_name(raw_name: str) -> str:
    s = str(raw_name or "").strip()
    if not s:
        return "Микрофон Windows"
    for src_enc in ("latin1", "cp1252"):
        try:
            fixed = s.encode(src_enc).decode("cp1251")
            if any("А" <= ch <= "я" or ch in "Ёё" for ch in fixed):
                return fixed.strip()
        except Exception:
            pass
    return s


def get_windows_audio_devices() -> tuple:
    mics = []
    mic_map = {}
    outs = []
    out_map = {}

    sd_names = {}
    if sd is not None:
        try:
            for i, dev in enumerate(sd.query_devices()):
                sd_names[i] = _fix_win_device_name(dev.get("name", ""))
        except Exception:
            pass

    if pyaudio is not None:
        pa = None
        try:
            pa = pyaudio.PyAudio()
            host_info = pa.get_default_host_api_info()
            host_idx = host_info.get("index", 0)
            for idx in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(idx)
                if info.get("hostApi") != host_idx:
                    continue
                clean = sd_names.get(idx) or _fix_win_device_name(info.get("name", ""))
                low = clean.lower()
                if any(skip in low for skip in ("mapper", "переназнач", "первичный", "primary")):
                    continue
                if int(info.get("maxInputChannels", 0)) > 0:
                    lbl = f"[{idx}] {clean}"
                    if lbl not in mic_map:
                        mic_map[lbl] = idx
                        mics.append(lbl)
                if int(info.get("maxOutputChannels", 0)) > 0:
                    lbl = f"[{idx}] {clean}"
                    if lbl not in out_map:
                        out_map[lbl] = idx
                        outs.append(lbl)
        except Exception:
            pass
        finally:
            if pa:
                try:
                    pa.terminate()
                except Exception:
                    pass

    if not mics:
        mics = ["[Default] Системный микрофон Windows"]
        mic_map[mics] = None
    if not outs:
        outs = ["[Default] Системные динамики Windows"]
        out_map[outs] = None

    return mics, mic_map, outs, out_map


class VoiceEars:
    """Стабильный голосовой модуль AiPulsar с постоянным аудиопотpulsarм (без разрывов и переподключений)."""

    RATE = 16000
    CHUNK = 1024

    def __init__(self, level_cb=None, devices_cb=None):
        self.level_cb = level_cb
        self.devices_cb = devices_cb
        self.muted = False
        self.device_index = None
        self._restart_stream = False
        self._label_to_idx = {}
        self._smooth_lvl = 0.0
        self._phrases_q = queue.Queue(maxsize=8)
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 320

        self.refresh_devices()
        threading.Thread(target=self._continuous_stream_worker, daemon=True).start()

    def refresh_devices(self):
        items, mic_map, _, _ = get_windows_audio_devices()
        self._label_to_idx = mic_map
        active_lbl = items
        self.device_index = self._label_to_idx.get(active_lbl)
        if self.devices_cb:
            try:
                self.devices_cb(items, active_lbl)
            except Exception:
                pass

    def select_device_by_label(self, label: str):
        if label in self._label_to_idx:
            new_idx = self._label_to_idx[label]
            if new_idx != self.device_index:
                self.device_index = new_idx
                self._restart_stream = True

    def _calc_rms(self, raw_bytes: bytes) -> float:
        count = len(raw_bytes) // 2
        if count <= 0:
            return 0.0
        shorts = struct.unpack(f"<{count}h", raw_bytes[: count * 2])
        return math.sqrt(sum(s * s for s in shorts) / count)

    def _continuous_stream_worker(self):
        """Держит поток микрофона открытым постоянно и выделяет фразы без переподключения устройства."""
        while True:
            if pyaudio is None:
                time.sleep(1.0)
                continue

            pa = None
            stream = None
            self._restart_stream = False
            try:
                pa = pyaudio.PyAudio()
                open_kwargs = {
                    "format": pyaudio.paInt16,
                    "channels": 1,
                    "rate": self.RATE,
                    "input": True,
                    "frames_per_buffer": self.CHUNK,
                }
                if self.device_index is not None:
                    open_kwargs["input_device_index"] = int(self.device_index)

                stream = pa.open(**open_kwargs)
                pre_buffer = collections.deque(maxlen=10)
                speech_frames = []
                in_speech = False
                silent_chunks = 0
                max_silent_chunks = int((self.RATE / self.CHUNK) * 0.85)
                max_phrase_chunks = int((self.RATE / self.CHUNK) * 12.0)

                while not self._restart_stream:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    if self.muted:
                        in_speech = False
                        speech_frames.clear()
                        if self.level_cb and self._smooth_lvl > 0.01:
                            self._smooth_lvl = 0.0
                            self.level_cb(0.0)
                        continue

                    rms = self._calc_rms(data)
                    target_lvl = min(1.0, rms / 3200.0)
                    self._smooth_lvl = self._smooth_lvl * 0.65 + target_lvl * 0.35
                    if self.level_cb:
                        self.level_cb(self._smooth_lvl)

                    if rms > self.recognizer.energy_threshold:
                        if not in_speech:
                            in_speech = True
                            speech_frames.extend(pre_buffer)
                        speech_frames.append(data)
                        silent_chunks = 0
                    else:
                        if in_speech:
                            speech_frames.append(data)
                            silent_chunks += 1
                            if silent_chunks >= max_silent_chunks or len(speech_frames) >= max_phrase_chunks:
                                pcm_blob = b"".join(speech_frames)
                                speech_frames.clear()
                                in_speech = False
                                silent_chunks = 0
                                if not self._phrases_q.full():
                                    self._phrases_q.put(pcm_blob)
                        else:
                            pre_buffer.append(data)
            except Exception:
                # Если конкретный индекс недоступен — плавно переходим на системный микрофон Windows по умолчанию
                if self.device_index is not None:
                    self.device_index = None
                time.sleep(0.5)
            finally:
                if stream is not None:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except Exception:
                        pass
                if pa is not None:
                    try:
                        pa.terminate()
                    except Exception:
                        pass

    def listen_phrase(self, silence_duration: float = 0.85) -> str:
        try:
            pcm_blob = self._phrases_q.get(timeout=0.5)
        except queue.Empty:
            return ""

        if self.muted or not pcm_blob:
            return ""

        try:
            audio = sr.AudioData(pcm_blob, self.RATE, 2)
            lang_code = "en-US" if get_lang() == "en" else "ru-RU"
            text = self.recognizer.recognize_google(audio, language=lang_code)
            return (text or "").strip()
        except Exception:
            return ""
