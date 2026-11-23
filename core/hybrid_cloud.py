# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import json
import socket
import urllib.request
from core.i18n import get_lang
from core.license_manager import AiPulsarLicenseManager


class HybridCloudBrain:
    """Облачный гибридный сплит через защищённый шлюз VESKOR (ваш личный API-ключ хранится только на сервере)."""

    CLOUD_GATEWAY_URL = "https://veskor-dev.ru/chat"

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.lic = AiPulsarLicenseManager(models_dir=models_dir)

    def has_internet(self) -> bool:
        try:
            with socket.create_connection(("8.8.8.8", 53), timeout=0.8):
                return True
        except Exception:
            return False

    def is_online_split_active(self) -> bool:
        st = self.lic.get_status()
        return bool(st.get("is_pro")) and self.has_internet()

    def enhance_with_cloud(self, user_prompt: str, local_context: str = "", web_context: str = "") -> str:
        st = self.lic.get_status()
        if not st.get("is_pro") or not self.has_internet():
            return ""
        try:
            body = json.dumps({
                "token": st["token"],
                "hwid": st["hwid"],
                "lang": get_lang(),
                "prompt": user_prompt,
                "local_context": local_context,
                "web_context": web_context,
            }).encode("utf-8")
            req = urllib.request.Request(
                self.CLOUD_GATEWAY_URL,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "PulsarClient/1.0"},
            )
            with urllib.request.urlopen(req, timeout=22) as r:
                data = json.loads(r.read().decode("utf-8"))
                return str(data.get("reply", "")).strip()
        except Exception:
            return ""
