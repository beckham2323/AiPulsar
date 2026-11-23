# -*- coding: utf-8 -*-
import hashlib
import json
import os
import platform
import urllib.parse
import uuid
import webbrowser


class YooMoneyPaymentBridge:
    """Формирование платёжных ссылок ЮMoney для тарифов AiPulsar Pro (1, 3, 6, 12 мес.)."""

    DEFAULT_WALLET = "410010000000000"

    PLANS = {
        "1M":  {"title": "AiPulsar Pro — 1 месяц (30 дней)",  "days": 30,  "default_rub": 299},
        "3M":  {"title": "AiPulsar Pro — 3 месяца (90 дней)", "days": 90,  "default_rub": 749},
        "6M":  {"title": "AiPulsar Pro — 6 месяцев (180 дней)", "days": 180, "default_rub": 1290},
        "12M": {"title": "AiPulsar Pro — 1 год (365 дней)",   "days": 365, "default_rub": 1990},
    }

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.cfg_path = os.path.join(self.models_dir, "yoomoney_config.json")
        self.cfg = self._load_or_init_cfg()

    def _load_or_init_cfg(self) -> dict:
        if os.path.exists(self.cfg_path):
            try:
                with open(self.cfg_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        data = {
            "wallet_number": self.DEFAULT_WALLET,
            "price_1m_rub": 299,
            "price_3m_rub": 749,
            "price_6m_rub": 1290,
            "price_12m_rub": 1990,
            "receiver_title": "AiPulsar Pro (VESKOR)",
        }
        try:
            with open(self.cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return data

    def get_device_payment_label(self, plan_code: str = "1M") -> str:
        raw = f"{uuid.getnode()}-{platform.node()}"
        short_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10].upper()
        return f"AIPULSAR-{short_id}-{plan_code.upper()}"

    def build_payment_url(self, plan_code: str = "1M") -> str:
        code = plan_code.strip().upper()
        if code not in self.PLANS:
            code = "12M" if ("12" in code or "ГОД" in code or "ENT" in code) else ("6M" if "6" in code else ("3M" if "3" in code else "1M"))
        info = self.PLANS[code]
        cfg_key = f"price_{code.lower()}_rub"
        amount = int(self.cfg.get(cfg_key, info["default_rub"]))
        wallet = str(self.cfg.get("wallet_number") or self.DEFAULT_WALLET).strip()
        label = self.get_device_payment_label(code)

        params = {
            "receiver": wallet,
            "quickpay-form": "shop",
            "targets": f"Оплата лицензии {info['title']} [{label}]",
            "paymentType": "AC",
            "sum": str(amount),
            "label": label,
        }
        return "https://yoomoney.ru?" + urllib.parse.urlencode(params, encoding="utf-8")

    def open_yoomoney_checkout(self, plan_code: str = "1M") -> tuple:
        url = self.build_payment_url(plan_code)
        label = self.get_device_payment_label(plan_code)
        webbrowser.open(url)
        return url, label
