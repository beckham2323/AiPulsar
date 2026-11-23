# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import base64
import datetime
import hashlib
import os
import re
import threading
import time
import psutil
from PIL import Image
from core.i18n import get_lang

try:
    import winreg
except Exception:
    winreg = None


class PulsarSecurityRadar:
    """Фоновый радар безопасности (FREE): отслеживает доступ сторонних программ к веб-камере и микрофону."""

    def __init__(self, alert_cb=None):
        self.alert_cb = alert_cb
        self._active_cams = set()
        self._running = True
        threading.Thread(target=self._watch_loop, daemon=True).start()

    def _scan_active_devices(self, cap_name: str) -> set:
        found = set()
        if not winreg:
            return found
        base_path = rf"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\{cap_name}\NonPackaged"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base_path) as root_k:
                i = 0
                while True:
                    try:
                        sub_name = winreg.EnumKey(root_k, i)
                        i += 1
                        with winreg.OpenKey(root_k, sub_name) as sk:
                            val, _ = winreg.QueryValueEx(sk, "LastUsedTimeStop")
                            if int(val) == 0:
                                app_exe = os.path.basename(sub_name.replace("#", "\\"))
                                if "pulsar" not in app_exe.lower() and "python" not in app_exe.lower():
                                    found.add(app_exe)
                    except OSError:
                        break
        except Exception:
            pass
        return found

    def get_security_report(self) -> str:
        is_en = get_lang() == "en"
        cams = self._scan_active_devices("webcam")
        mics = self._scan_active_devices("microphone")
        conns = len([c for c in psutil.net_connections(kind="inet") if c.status == "ESTABLISHED"])
        if is_en:
            c_txt = ", ".join(cams) if cams else "none"
            m_txt = ", ".join(mics) if mics else "none"
            return f"Security Radar: Active connections: {conns}. Camera used by: {c_txt}. Mic used by: {m_txt}."
        c_txt = ", ".join(cams) if cams else "никем не используется"
        m_txt = ", ".join(mics) if mics else "никем не используется"
        return f"Радар безопасности: активных сетевых соединений — {conns}. Камера: {c_txt}. Микрофон: {m_txt}."

    def _watch_loop(self):
        while self._running:
            time.sleep(5.0)
            try:
                cams = self._scan_active_devices("webcam")
                new_cams = cams - self._active_cams
                self._active_cams = cams
                if new_cams and self.alert_cb:
                    apps = ", ".join(new_cams)
                    self.alert_cb(f"🛡️ Радар безопасности: программа {apps} только что включила веб-камеру!")
            except Exception:
                pass


class PulsarCryptoVault:
    """Голосовой крипто-сейф в картинке (PRO): незаметно вшивает зашифрованный секрет внутрь PNG-изображения."""

    MAGIC = b"VESKOR_VAULT_V1:"

    @staticmethod
    def _xor_crypt(data: bytes, password: str) -> bytes:
        key = hashlib.sha256(password.encode("utf-8")).digest()
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    @classmethod
    def hide_secret_in_image(cls, secret_text: str, passphrase: str = "VESKOR2026") -> str:
        is_en = get_lang() == "en"
        desk = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(desk, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_img = os.path.join(desk, f"Pulsar_Space_Art_{ts}.png")

        # Генерируем красивую абстрактную космическую картинку 256x256 и вшиваем в младшие биты (LSB) зашифрованный текст
        img = Image.new("RGB", (256, 256), (10, 14, 28))
        px = img.load()
        for y in range(256):
            for x in range(256):
                r = (18 + (x ^ y) // 4) & 0xFE
                g = (22 + (x * y) // 512) & 0xFE
                b = (58 + (x + y) // 3) & 0xFE
                px[x, y] = (r, g, b)

        enc = cls.MAGIC + cls._xor_crypt(secret_text.encode("utf-8"), passphrase)
        b64 = base64.b64encode(enc) + b"\x00"
        bits = "".join(f"{byte:08b}" for byte in b64)

        idx = 0
        for y in range(256):
            for x in range(256):
                if idx >= len(bits):
                    break
                r, g, b = px[x, y]
                r = (r & 0xFE) | int(bits[idx])
                idx += 1
                if idx < len(bits):
                    g = (g & 0xFE) | int(bits[idx])
                    idx += 1
                if idx < len(bits):
                    b = (b & 0xFE) | int(bits[idx])
                    idx += 1
                px[x, y] = (r, g, b)

        img.save(out_img, "PNG")
        return (
            f"Secret encrypted and hidden inside {os.path.basename(out_img)} on Desktop."
            if is_en
            else f"Секрет зашифрован и спрятан внутри картинки {os.path.basename(out_img)} на Рабочем столе."
        )

    @classmethod
    def extract_secret_from_latest_image(cls, passphrase: str = "VESKOR2026") -> str:
        is_en = get_lang() == "en"
        desk = os.path.join(os.path.expanduser("~"), "Desktop")
        candidates = sorted(
            [os.path.join(desk, f) for f in os.listdir(desk) if f.startswith("Pulsar_Space_Art_") and f.endswith(".png")],
            reverse=True,
        ) if os.path.isdir(desk) else []

        if not candidates:
            return "No vault image found on Desktop." if is_en else "На Рабочем столе не найдена картинка-контейнер Pulsar_Space_Art."

        img = Image.open(candidates).convert("RGB")
        px = img.load()
        bits = []
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = px[x, y]
                bits.extend([str(r & 1), str(g & 1), str(b & 1)])

        raw_bytes = bytearray()
        for i in range(0, len(bits) - 7, 8):
            val = int("".join(bits[i : i + 8]), 2)
            if val == 0:
                break
            raw_bytes.append(val)

        try:
            decoded = base64.b64decode(bytes(raw_bytes))
            if not decoded.startswith(cls.MAGIC):
                return "Wrong passphrase or empty vault." if is_en else "Неверная кодовая фраза или секрет не найден."
            plain = cls._xor_crypt(decoded[len(cls.MAGIC) :], passphrase).decode("utf-8")
            return f"Unlocked secret: {plain}" if is_en else f"Расшифрованный секрет из картинки: {plain}"
        except Exception:
            return "Failed to unlock image vault." if is_en else "Не удалось расшифровать секрет из картинки."
