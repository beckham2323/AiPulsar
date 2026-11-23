def _get_persistent_hardware_id() -> str:
    """Вычисляет неизменный HWID по физическим ID материнской платы, процессора и BIOS (переживает переустановку Windows)."""
    import hashlib, subprocess
    parts = []
    cmds = [
        ["wmic", "csproduct", "get", "uuid"],
        ["wmic", "cpu", "get", "processorid"],
        ["wmic", "bios", "get", "serialnumber"],
    ]
    for cmd in cmds:
        try:
            out = subprocess.check_output(cmd, creationflags=0x08000000, timeout=3).decode("utf-8", errors="ignore")
            lines = [ln.strip() for ln in out.splitlines() if ln.strip() and ln.strip().lower() not in ("uuid", "processorid", "serialnumber")]
            if lines:
                parts.append(lines)
        except Exception:
            pass
    if not parts:
        try:
            ps = "Get-CimInstance Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"
            uid = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], creationflags=0x08000000, timeout=3).decode("utf-8", errors="ignore").strip()
            if uid:
                parts.append(uid)
        except Exception:
            pass
    raw_hw = "|".join(parts) if parts else "FALLBACK-HW-AIPULSAR"
    return "AP-" + hashlib.sha256(raw_hw.encode("utf-8")).hexdigest()[:16].upper()

# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import datetime
import hashlib
import hmac
import json
import os
import subprocess
import urllib.request
import uuid

try:
    import winreg
except Exception:
    winreg = None


class AiPulsarLicenseManager:
    """Управление лицензией: вечный FREE, одноразовый 3-дневный TRIAL на 1 ПК и вечный PRO по зашифрованному промpulsarду."""

    _SIGN_SECRET = b"VESKOR_SMIRNOV_VE_PULSAR_2026_PUBLIC_VERIFY"
    _PROMO_HASH = "7b7c0889d7b5be8c2b742bcf772bdea829d54fd7bdaa6fab202bfb3a59777d78"
    TRIAL_DAYS = 3
    LICENSE_API_URL = "https://veskor-dev.ru"

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.lic_path = os.path.join(self.models_dir, "pulsar_pro.lic")
        self.hwid = self._compute_hwid()
        self._sys_guard_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Microsoft", "Windows", "VESKOR_Cache")
        self._sys_guard_file = os.path.join(self._sys_guard_dir, "hw_trial_lock.dat")

    def _compute_hwid(self) -> str:
        return _get_persistent_hardware_id()
        raw_id = str(uuid.getnode())
        try:
            res = subprocess.run(
                ["wmic", "csproduct", "get", "uuid"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=2
            )
            lines = [x.strip() for x in (res.stdout or "").splitlines() if x.strip() and "UUID" not in x.upper()]
            if lines:
                raw_id = lines
        except Exception:
            pass
        digest = hashlib.sha256(f"VESKOR_HW:{raw_id}".encode("utf-8")).hexdigest().upper()
        return f"VESK-{digest[:4]}-{digest[4:8]}-{digest[8:12]}"

    def _trial_lock_token(self) -> str:
        return hashlib.sha256(f"TRIAL_LOCK_2026:{self.hwid}".encode("utf-8")).hexdigest()

    def is_trial_used(self) -> bool:
        expected = self._trial_lock_token()
        if winreg:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\VESKOR\Pulsar") as k:
                    val, _ = winreg.QueryValueEx(k, "TrialFingerprint")
                    if str(val) == expected:
                        return True
            except Exception:
                pass
        try:
            if os.path.exists(self._sys_guard_file):
                with open(self._sys_guard_file, "r", encoding="utf-8") as f:
                    if expected in f.read():
                        return True
        except Exception:
            pass
        return False

    def _mark_trial_used_forever(self):
        token = self._trial_lock_token()
        if winreg:
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\VESKOR\Pulsar") as k:
                    winreg.SetValueEx(k, "TrialFingerprint", 0, winreg.REG_SZ, token)
            except Exception:
                pass
        try:
            os.makedirs(self._sys_guard_dir, exist_ok=True)
            with open(self._sys_guard_file, "a", encoding="utf-8") as f:
                f.write(token + "\n")
        except Exception:
            pass

    def start_3day_trial(self) -> tuple:
        if self.is_trial_used():
            return False, "Пробный период 3 дня на этом устройстве уже был использован."
        now_dt = datetime.datetime.now()
        exp_dt = now_dt + datetime.timedelta(days=self.TRIAL_DAYS)
        self._mark_trial_used_forever()
        with open(self.lic_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "license_key": "TRIAL_3D",
                    "token": "TRIAL_ACTIVE",
                    "hwid": self.hwid,
                    "tier": "TRIAL",
                    "expires_at": exp_dt.isoformat(),
                },
                f,
                indent=2,
            )
        return True, f"Пробная версия Pro на 3 дня активирована до {exp_dt.strftime('%d.%m.%Y %H:%M')}!"
    def check_remote_activation(self) -> tuple:
        try:
            payload = json.dumps({"hwid": self.hwid}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.LICENSE_API_URL}/check-device",
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "PulsarClient/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read().decode("utf-8"))
                if data.get("ok") and data.get("license_key"):
                    key = str(data["license_key"]).strip().upper()
                    days = int(data.get("days", 365))
                    exp_dt = datetime.datetime.now() + datetime.timedelta(days=days)
                    with open(self.lic_path, "w", encoding="utf-8") as f:
                        json.dump({"license_key": key, "token": key, "hwid": self.hwid, "tier": "PRO", "expires_at": exp_dt.isoformat()}, f, indent=2)
                    return True, "Оплата подтверждена! Версия Pulsar Pro активирована."
        except Exception:
            pass
        return False, ""

    def deactivate_license(self) -> str:
        if os.path.exists(self.lic_path):
            try:
                os.remove(self.lic_path)
            except Exception:
                pass
        return "Лицензия на этом ПК деактивирована."

    def activate_key(self, license_key: str) -> tuple:
        raw_input = (license_key or "").strip()

        entered_hash = hashlib.sha256(f"VESKOR_MASTER_PROMO_SALT_2026:{raw_input}".encode("utf-8")).hexdigest()
        if hmac.compare_digest(entered_hash, self._PROMO_HASH):
            with open(self.lic_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "license_key": "MASTER_LIFETIME",
                        "token": "LIFETIME_VERIFIED",
                        "hwid": self.hwid,
                        "tier": "PRO",
                        "lifetime": True,
                    },
                    f,
                    indent=2,
                )
            return True, "Пожизненная версия Pulsar Pro активирована навсегда!"

        key = raw_input.upper()
        if not (key.startswith("VESK-PRO-") or key.startswith("VESK-MON-") or key.startswith("VESK-YR-")):
            return False, "Неверный код активации."

        days = 30 if key.startswith("VESK-MON-") else 365
        exp_dt = datetime.datetime.now() + datetime.timedelta(days=days)

        try:
            payload = json.dumps({"license_key": key, "hwid": self.hwid}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.LICENSE_API_URL}/activate",
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "PulsarClient/1.0"},
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
                if data.get("ok"):
                    token = str(data.get("activation_token", key))
                    with open(self.lic_path, "w", encoding="utf-8") as f:
                        json.dump({"license_key": key, "token": token, "hwid": self.hwid, "tier": "PRO", "expires_at": exp_dt.isoformat()}, f, indent=2)
                    return True, f"Pulsar Pro активирован на {days} дн.!"
                return False, str(data.get("error", "Ключ недействителен."))
        except Exception:
            pass

        parts = key.split("-")
        if len(parts) == 5:
            body = f"{parts}-{parts}"
            sig = parts
            expected = hmac.new(self._SIGN_SECRET, f"{self.hwid}:{body}".encode("utf-8"), hashlib.sha256).hexdigest()[:8].upper()
            if hmac.compare_digest(sig, expected):
                with open(self.lic_path, "w", encoding="utf-8") as f:
                    json.dump({"license_key": key, "token": key, "hwid": self.hwid, "tier": "PRO", "expires_at": exp_dt.isoformat()}, f, indent=2)
                return True, f"Pulsar Pro активирован на {days} дн.!"

        return False, "Не удалось подтвердить ключ. Проверьте правильность ввода."

    @staticmethod
    def _format_remaining(delta: datetime.timedelta) -> str:
        total_sec = max(0, int(delta.total_seconds()))
        days = total_sec // 86400
        hours = (total_sec % 86400) // 3600
        if days > 0:
            return f"{days} дн. {hours} ч."
        return f"{max(1, hours)} ч."

    def get_status(self) -> dict:
        if os.path.exists(self.lic_path):
            try:
                with open(self.lic_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("hwid") == self.hwid:
                    if data.get("lifetime"):
                        return {"is_pro": True, "tier": "PRO", "hwid": self.hwid, "token": data.get("token", ""), "time_left": "Навсегда"}
                    tier = data.get("tier", "")
                    if tier in ("PRO", "TRIAL") and data.get("expires_at"):
                        exp = datetime.datetime.fromisoformat(data["expires_at"])
                        now = datetime.datetime.now()
                        if now < exp:
                            return {"is_pro": True, "tier": tier, "hwid": self.hwid, "token": data.get("token", ""), "time_left": self._format_remaining(exp - now)}
                        else:
                            os.remove(self.lic_path)
            except Exception:
                pass
        return {"is_pro": False, "tier": "FREE", "hwid": self.hwid, "token": "", "time_left": "Бесплатно навсегда"}
