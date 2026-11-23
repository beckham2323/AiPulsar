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


def open_pro_tariffs_selector_window(parent_tk, models_dir: str = "models"):
    """Окно выбора тарифов AiPulsar Pro (1, 3, 6, 12 месяцев) с рабочими ссылками на оплату."""
    import tkinter as tk
    from core.ui_widgets import attach_tab_popup_to_main

    bridge = YooMoneyPaymentBridge(models_dir=models_dir)
    win = tk.Toplevel(parent_tk)
    win.title("🔑 AiPulsar Pro — Выбор тарифа и активация")
    win.geometry("560x480")
    win.configure(bg="#202020")
    win.resizable(False, False)

    tk.Label(win, text="🔑 Выберите тарифный план AiPulsar Pro", bg="#202020", fg="#FFFFFF", font=("Segoe UI Semibold", 14)).pack(anchor="w", padx=20, pady=(16, 4))
    tk.Label(win, text="Полный безлимитный доступ ко всем нейросетевым функциям, медиаплееру и авторемонту ПК", bg="#202020", fg="#A6A6A6", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 12))

    selected_plan = tk.StringVar(value="12M")
    status_lbl = tk.Label(win, text="", bg="#202020", fg="#60CDFF", font=("Segoe UI", 9), wraplength=510, justify="left")

    plans_ui = [
        ("1M",  "1 месяц (30 дней)",   "299 ₽",   "Базовый тариф (299 ₽/мес)"),
        ("3M",  "3 месяца (90 дней)",  "749 ₽",   "Выгода 17% — экономия 148 ₽ (250 ₽/мес)"),
        ("6M",  "6 месяцев (180 дней)","1 290 ₽", "Выгода 28% — экономия 504 ₽ (215 ₽/мес)"),
        ("12M", "1 год (365 дней)",    "1 990 ₽", "Выгода 45% — экономия 1 598 ₽ (166 ₽/мес)"),
    ]

    for code, title, price, badge in plans_ui:
        card = tk.Frame(win, bg="#2B2B2B", highlightthickness=1, highlightbackground="#3D3D3D")
        card.pack(fill=tk.X, padx=20, pady=4)
        rb = tk.Radiobutton(
            card,
            text=f"  {title}  —  {price}",
            variable=selected_plan,
            value=code,
            bg="#2B2B2B",
            fg="#FFFFFF",
            selectcolor="#202020",
            activebackground="#2B2B2B",
            activeforeground="#60CDFF",
            font=("Segoe UI Semibold", 10),
            cursor="hand2",
        )
        rb.pack(side=tk.LEFT, padx=10, pady=8)
        tk.Label(card, text=badge, bg="#2B2B2B", fg="#3CCB5A" if "Выгода" in badge else "#A6A6A6", font=("Segoe UI", 8)).pack(side=tk.RIGHT, padx=12)

    def _pay_selected():
        code = selected_plan.get()
        url, lbl = bridge.open_yoomoney_checkout(code)
        status_lbl.config(text=f"🌐 Открыта страница оплаты тарифа {code} (метка ПК: {lbl}). После оплаты введите ключ в окне лицензии.")

    tk.Button(
        win,
        text="💳 Перейти к оплате выбранного тарифа",
        command=_pay_selected,
        bg="#0078D4",
        fg="#FFFFFF",
        activebackground="#106EBE",
        activeforeground="#FFFFFF",
        relief=tk.FLAT,
        font=("Segoe UI Semibold", 10),
        padx=18,
        pady=9,
        cursor="hand2",
    ).pack(fill=tk.X, padx=20, pady=(14, 6))

    status_lbl.pack(anchor="w", padx=20, pady=(0, 8))
    attach_tab_popup_to_main(parent_tk, win)


def render_updated_tariffs_comparison_cards(parent_frame, models_dir: str = "models"):
    """Отрисовывает 4 актуальных тарифа AiPulsar Pro (299 / 749 / 1290 / 1990 ₽) с рабочими кнопками оплаты."""
    import tkinter as tk
    from core.yoomoney_pay_bridge import YooMoneyPaymentBridge

    bridge = YooMoneyPaymentBridge(models_dir=models_dir)
    info_lbl = tk.Label(parent_frame, text="", bg="#202020", fg="#60CDFF", font=("Segoe UI", 9), wraplength=540, justify="left")

    plans = [
        ("1M",  "Pro — 1 месяц",   "30 дней",  "299 ₽",   "Базовый тариф (299 ₽/мес)",              "#383838"),
        ("3M",  "Pro — 3 месяца",  "90 дней",  "749 ₽",   "Выгода 17% — экономия 148 ₽ (250 ₽/мес)", "#383838"),
        ("6M",  "Pro — 6 месяцев", "180 дней", "1 290 ₽", "Выгода 28% — экономия 504 ₽ (215 ₽/мес)", "#383838"),
        ("12M", "Pro — 1 год",     "365 дней", "1 990 ₽", "Выгода 45% — экономия 1 598 ₽ (166 ₽/мес)", "#60CDFF"),
    ]

    for code, title, period, price, badge, border_col in plans:
        row = tk.Frame(parent_frame, bg="#2B2B2B", highlightthickness=1, highlightbackground=border_col)
        row.pack(fill=tk.X, padx=14, pady=4)

        left_box = tk.Frame(row, bg="#2B2B2B")
        left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=8)
        tk.Label(left_box, text=f"{title} ({period}) — {price}", bg="#2B2B2B", fg="#FFFFFF", font=("Segoe UI Semibold", 10)).pack(anchor="w")
        tk.Label(left_box, text=badge, bg="#2B2B2B", fg="#3CCB5A" if "Выгода" in badge else "#A6A6A6", font=("Segoe UI", 8)).pack(anchor="w")

        def _make_pay_cb(c=code, p=price):
            def _do_pay():
                url, lbl = bridge.open_yoomoney_checkout(c)
                info_lbl.config(text=f"💳 Открыта ссылка оплаты тарифа {c} ({p}). Метка вашего ПК: {lbl}")
            return _do_pay

        tk.Button(
            row,
            text=f"💳 Оплатить {price}",
            command=_make_pay_cb(),
            bg="#0078D4",
            fg="#FFFFFF",
            activebackground="#106EBE",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            font=("Segoe UI Semibold", 9),
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side=tk.RIGHT, padx=12, pady=8)

    info_lbl.pack(anchor="w", padx=14, pady=(6, 4))
