# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import datetime
import os
import re
import threading
import wave
import mss
import numpy as np
import pyautogui
import pyaudio
from core.i18n import get_lang


class PulsarProExtraFeatures:
    """Pro-модули: голосовой кликер по тексту на экране (OCR) и диктофон совещаний с расшифровкой."""

    def __init__(self, vision, brain):
        self.vision = vision
        self.brain = brain
        self._audio_rec = False
        self._wav_path = ""
        self._audio_thread = None

    def click_text_on_screen(self, command_text: str) -> str:
        is_en = get_lang() == "en"
        target = re.sub(
            r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:нажми|кликни|щёлкни|нажать|кликнуть|click|press|tap)(?:\s+на|\s+по|\s+кнопку|\s+on|\s+button)?[:\s]*",
            "",
            command_text,
            flags=re.I,
        ).strip(" .!?\"'«»")

        if not target:
            return "Specify the text on screen to click." if is_en else "Укажи текст или название кнопки на экране, на которую нужно нажать."

        if not self.vision or not getattr(self.vision, "ocr", None):
            return "Screen OCR engine is unavailable." if is_en else "Модуль экранного зрения временно недоступен."

        try:
            with mss.mss() as sct:
                mon = sct.monitors[1 if len(sct.monitors) > 1 else 0]
                shot = sct.grab(mon)
                img_bgr = np.array(shot)[:, :, :3]
                res, _ = self.vision.ocr(img_bgr)
                low_target = target.lower()

                for item in res or []:
                    if len(item) >= 2:
                        box, text_found = item, str(item)
                        if low_target in text_found.lower():
                            xs = [pt for pt in box]
                            ys = [pt for pt in box]
                            cx = int(mon["left"] + sum(xs) / len(xs))
                            cy = int(mon["top"] + sum(ys) / len(ys))
                            pyautogui.moveTo(cx, cy, duration=0.2)
                            pyautogui.click()
                            return f"Clicked on «{text_found}»." if is_en else f"Нажал на «{text_found}»."

            return f"Text «{target}» not found on screen." if is_en else f"Текст «{target}» не найден на текущем экране."
        except Exception as e:
            return f"Click error: {e}" if is_en else f"Ошибка при поиске элемента на экране: {e}"

    def start_meeting_recorder(self) -> str:
        is_en = get_lang() == "en"
        if self._audio_rec:
            return "Meeting recording is already active." if is_en else "Запись разговора уже идёт. Скажи «Останови запись разговора»."

        out_dir = os.path.join(os.path.expanduser("~"), "Documents", "Pulsar_Meetings" if is_en else "Pulsar_Записи_Встреч")
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._wav_path = os.path.join(out_dir, f"Meeting_{ts}.wav")
        self._audio_rec = True

        def _rec_audio():
            pa = pyaudio.PyAudio()
            stream = None
            frames = []
            try:
                stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
                while self._audio_rec:
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)
            except Exception:
                pass
            finally:
                if stream:
                    stream.stop_stream()
                    stream.close()
                pa.terminate()
                if frames:
                    with wave.open(self._wav_path, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(b"".join(frames))

        self._audio_thread = threading.Thread(target=_rec_audio, daemon=True)
        self._audio_thread.start()
        return "Meeting audio recording started. Say 'Stop meeting recording' to transcribe." if is_en else "Начал запись разговора. Скажи «Останови запись разговора», чтобы получить текстовую расшифровку."

    def stop_and_transcribe_meeting(self) -> str:
        is_en = get_lang() == "en"
        if not self._audio_rec:
            return "No active meeting recording." if is_en else "Сейчас запись разговора не запущена."

        self._audio_rec = False
        if self._audio_thread:
            self._audio_thread.join(timeout=3.0)

        wav_file = self._wav_path
        if not wav_file or not os.path.exists(wav_file):
            return "Audio file was not saved." if is_en else "Не удалось сохранить аудиозапись."

        transcript = ""
        try:
            import speech_recognition as sr
            rec = sr.Recognizer()
            with sr.AudioFile(wav_file) as source:
                audio_data = rec.record(source)
                transcript = rec.recognize_google(audio_data, language="en-US" if is_en else "ru-RU")
        except Exception:
            transcript = ""

        if not transcript:
            return f"Audio saved to {wav_file}, but speech was too quiet to transcribe." if is_en else f"Аудио сохранено ({wav_file}), но речь не удалось чётко распознать."

        txt_out = os.path.splitext(wav_file) + ".txt"
        with open(txt_out, "w", encoding="utf-8") as f:
            f.write(transcript)

        return (
            f"Meeting transcript saved ({os.path.basename(txt_out)}):\n{transcript}"
            if is_en
            else f"Расшифровка разговора сохранена ({os.path.basename(txt_out)}):\n{transcript}"
        )
