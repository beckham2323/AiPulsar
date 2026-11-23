from core.ui_widgets import attach_tab_popup_to_main
from core.license_excel_vault import (
    record_license_to_excel,
    find_license_by_hwid_in_excel,
    export_backup_license_file,
    verify_backup_license_file,
    get_excel_registry_path,
)
import qrcode
from PIL import ImageTk
# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import threading
import time
import tkinter as tk
import urllib.parse
import webbrowser
import pyperclip
from core.clipboard_helper import enable_clipboard_and_menu
from core.i18n import get_lang
from core.license_manager import AiPulsarLicenseManager
from core.ui_widgets import RoundedCard, apply_win11_round_corners, bind_child_window_to_parent
from core.version import APP_COPYRIGHT, APP_EMAIL


class ProUpgradeDialog:
    """Окно сравнения Free / Pro с вкладками оплаты в рублях (₽) и долларах ($) на месяц и на год."""

    ACCENT = "#7C4DFF"
    BG_ROOT = "#07090E"
    BG_CARD = "#0D1117"
    BG_FIELD = "#161B22"

    YOOKASSA_RUB_1M = "https://yookassa.ru"
    YOOKASSA_RUB_3M = "https://yookassa.ru"
    YOOKASSA_RUB_6M = "https://yookassa.ru"
    YOOKASSA_RUB_12M = "https://yookassa.ru"
    YOOKASSA_USD_1M = "https://yookassa.ru"
    YOOKASSA_USD_3M = "https://yookassa.ru"
    YOOKASSA_USD_6M = "https://yookassa.ru"
    YOOKASSA_USD_12M = "https://yookassa.ru"

    def __init__(self, root: tk.Widget, on_activated=None):
        self.root = root
        self.on_activated = on_activated
        self._win = None
        self._polling = False

    def show(self):
        if self._win and self._win.winfo_exists():
            self._win.lift()
            self._win.focus_force()
            return

        is_en = get_lang() == "en"
        lic = AiPulsarLicenseManager()
        st = lic.get_status()

        win = tk.Toplevel(self.root)
        win.title("Pulsar — Тарифы и 3 дня бесплатно")
        win.configure(bg=self.BG_ROOT)
        win.overrideredirect(True)
        win.attributes("-topmost", False)
        self._win = win

        def _close_win():
            self._polling = False
            win.destroy()

        outer = RoundedCard(win, radius=18, border_color="#383838", bg_color=self.BG_CARD, pad=14, width=800, height=675)
        outer.pack(fill=tk.BOTH, expand=True)
        box = outer.inner

        hdr = tk.Frame(box, bg=self.BG_CARD)
        hdr.pack(fill=tk.X, padx=4, pady=(2, 10))
        title_txt = "PULSAR — FREE vs PRO" if is_en else "PULSAR — СРАВНЕНИЕ FREE И PRO"
        tk.Label(hdr, text=title_txt, bg=self.BG_CARD, fg="#FFFFFF", font=("Segoe UI Semibold", 11)).pack(side=tk.LEFT)
        tk.Button(hdr, text="✕", command=_close_win, bg=self.BG_CARD, fg="#FFFFFF", activebackground="#1F242D", activeforeground=self.ACCENT, relief=tk.FLAT, font=("Segoe UI Semibold", 11), padx=6, cursor="hand2").pack(side=tk.RIGHT)

        cols = tk.Frame(box, bg=self.BG_CARD)
        cols.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 10))

        free_card = RoundedCard(cols, radius=14, border_color="#30363D", bg_color=self.BG_FIELD, pad=10, width=365, height=265)
        free_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        f_box = free_card.inner

        pro_card = RoundedCard(cols, radius=14, border_color="#383838", bg_color=self.BG_FIELD, pad=10, width=380, height=265)
        pro_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
        p_box = pro_card.inner

        free_rows = [
            ("✔", "Живой 4K-пульсар на фоне глубpulsarго космоса"),
            ("✔", "Локальная нейросеть (Ollama) с автоподстройкой"),
            ("✔", "Голосовое и текстовое управление Windows"),
            ("✔", "Таймеры, Системный врач ПК и Радар безопасности"),
            ("✖", "Облачный гибридный сплит без API-ключей"),
            ("✖", "Генерация Word (.docx), Excel (.xlsx) и поиск по файлам"),
            ("✖", "Переводчик (Ctrl+C), кликер и запись экрана .mp4"),
        ]
        tk.Label(f_box, text="PULSAR FREE  •  0 ₽ (БЕСПЛАТНО НАВСЕГДА)", bg=self.BG_FIELD, fg="#FFFFFF", font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(2, 8))
        for icon, desc in free_rows:
            r_fr = tk.Frame(f_box, bg=self.BG_FIELD)
            r_fr.pack(fill=tk.X, pady=2)
            fg_c = "#FFFFFF" if icon == "✔" else "#6E7681"
            tk.Label(r_fr, text=icon, bg=self.BG_FIELD, fg=fg_c, font=("Segoe UI Semibold", 9), width=2).pack(side=tk.LEFT)
            tk.Label(r_fr, text=desc, bg=self.BG_FIELD, fg=fg_c, font=("Segoe UI", 9), justify=tk.LEFT, wraplength=320).pack(side=tk.LEFT)

        pro_rows = [
            ("✦", "Всё, что входит в бесплатную версию Free"),
            ("✦", "Автоматический облачный сплит (без API-ключей)"),
            ("✦", "Генерация документов Word (.docx) и Excel (.xlsx)"),
            ("✦", "Поиск и ответы по вашим личным документам"),
            ("✦", "Переводчик (Ctrl+C) и голосовой кликер по экрану"),
            ("✦", "Запись экрана (.mp4) и диктофон совещаний"),
            ("✦", "Квантовый мост Телефон↔ПК по QR и Крипто-сейф в фото"),
        ]
        tk.Label(p_box, text="👑 AIPULSAR PRO  •  от 299 ₽ ($5)/мес  |  1 990 ₽ ($29)/год", bg=self.BG_FIELD, fg=self.ACCENT, font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(2, 8))
        tk.Label(p_box, text="✓ Привязка к железу (HWID): лицензия сохраняется при переустановке Windows — просто введите ключ повторно.", bg=self.BG_FIELD, fg="#8BE9FD", font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 6))

        for icon, desc in pro_rows:
            r_pr = tk.Frame(p_box, bg=self.BG_FIELD)
            r_pr.pack(fill=tk.X, pady=2)
            tk.Label(r_pr, text=icon, bg=self.BG_FIELD, fg=self.ACCENT, font=("Segoe UI Semibold", 9), width=2).pack(side=tk.LEFT)
            tk.Label(r_pr, text=desc, bg=self.BG_FIELD, fg="#FFFFFF", font=("Segoe UI Semibold", 9), justify=tk.LEFT, wraplength=335).pack(side=tk.LEFT)
        act_card = RoundedCard(box, radius=14, border_color="#383838", bg_color=self.BG_FIELD, pad=10, height=275)
        act_card.pack(fill=tk.X, padx=4, pady=(0, 6))
        a_box = act_card.inner

        top_act = tk.Frame(a_box, bg=self.BG_FIELD)
        top_act.pack(fill=tk.X, pady=(0, 6))
        tk.Label(top_act, text=f"ID УСТРОЙСТВА: {st['hwid']}", bg=self.BG_FIELD, fg="#FFFFFF", font=("Consolas", 9, "bold")).pack(side=tk.LEFT)

        self._pay_qr_lbl = tk.Label(box, bg=self.BG_CARD)
        self._pay_qr_lbl.pack(pady=(2, 2))
        status_lbl = tk.Label(a_box, text="", bg=self.BG_FIELD, fg="#64FFDA", font=("Segoe UI Semibold", 8))

        def _copy_hwid():
            pyperclip.copy(st["hwid"])
            status_lbl.config(text="ID устройства скопирован!", fg="#64FFDA")

        def _start_trial():
            ok, msg = lic.start_3day_trial()
            status_lbl.config(text=msg, fg="#64FFDA" if ok else "#FF6E6E")
            if ok and self.on_activated:
                self.on_activated()

        def _start_auto_activation_watch():
            if self._polling:
                return
            self._polling = True

            def _watch_loop():
                for _ in range(90):
                    if not self._polling or not win.winfo_exists():
                        return
                    ok, msg = lic.check_remote_activation()
                    if ok:
                        self._polling = False
                        win.after(0, lambda: status_lbl.config(text=msg, fg="#64FFDA"))
                        if self.on_activated:
                            win.after(0, self.on_activated)
                        return
                    time.sleep(4.0)
                self._polling = False

            threading.Thread(target=_watch_loop, daemon=True).start()

        tk.Button(top_act, text="📋 КОПИРОВАТЬ ID", command=_copy_hwid, bg="#21262D", fg="#FFFFFF", activebackground="#30363D", relief=tk.FLAT, font=("Segoe UI", 8), padx=8, pady=3, cursor="hand2").pack(side=tk.RIGHT)

        trial_dlg_btn = tk.Button(top_act, text="🎁 ВКЛЮЧИТЬ ПРОБНЫЙ PRO НА 3 ДНЯ", bg="#112A27", fg="#64FFDA", activebackground="#1A3F3A", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=10, pady=3, cursor="hand2")
        def _start_trial_and_hide():
            ok, msg = lic.start_3day_trial()
            status_lbl.config(text=msg, fg="#64FFDA" if ok else "#FF6E6E")
            if ok:
                trial_dlg_btn.pack_forget()
                if self.on_activated:
                    self.on_activated()
        trial_dlg_btn.config(command=_start_trial_and_hide)
        if not st["is_pro"] and not lic.is_trial_used():
            trial_dlg_btn.pack(side=tk.RIGHT, padx=(0, 8))

        email_row = tk.Frame(a_box, bg=self.BG_FIELD)
        email_row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(email_row, text="E-MAIL ДЛЯ ЧЕКА И КЛЮЧА:", bg=self.BG_FIELD, fg="#FFFFFF", font=("Segoe UI Semibold", 8)).pack(side=tk.LEFT, padx=(0, 6))

        email_entry = tk.Entry(email_row, bg=self.BG_CARD, fg="#FFFFFF", insertbackground="#FFFFFF", font=("Segoe UI", 9), relief=tk.FLAT)
        email_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        enable_clipboard_and_menu(email_entry, readonly=False)

        def _get_valid_email() -> str:
            em = email_entry.get().strip()
            if "@" not in em or "." not in em.split("@")[-1]:
                status_lbl.config(text="Укажите ваш E-mail перед оплатой — на него придёт чек и резервный ключ!", fg="#FF6E6E")
                email_entry.focus_set()
                return ""
            return em

        def _pay_yookassa(currency: str, plan: str, base_url: str, label_price: str):
            em = _get_valid_email()
            if not em:
                return
            pyperclip.copy(st["hwid"])
            q = urllib.parse.urlencode({"currency": currency, "plan": plan, "hwid": st["hwid"], "email": em})
            webbrowser.open(f"{base_url}?{q}")
            status_lbl.config(text=f"Открыта ЮKassa ({label_price}). После оплаты Pro включится сама, а чек и ключ придут на {em}.", fg="#64FFDA")
            _start_auto_activation_watch()

        tabs_bar = tk.Frame(a_box, bg=self.BG_FIELD)
        tabs_bar.pack(fill=tk.X, pady=(2, 4))
        tab_btns = {}
        plans_holder = tk.Frame(a_box, bg=self.BG_FIELD)
        plans_holder.pack(fill=tk.X, pady=(0, 6))

        rec_box = tk.Frame(a_box, bg=self.BG_FIELD)
        rec_box.pack(fill=tk.X, pady=(6, 4))

        def _backup_lic_click():
            from tkinter import filedialog, messagebox
            cur_st = self.license_mgr.get_status()
            cur_key = str(cur_st.get("key", "") or cur_st.get("license_key", "") or "HWID-PRO-VERIFIED")
            save_p = filedialog.asksaveasfilename(
                title="Сохранить резервный сертификат лицензии AiPulsar Pro",
                initialfile=f"AiPulsar_Backup_{cur_st['hwid']}.lic",
                defaultextension=".lic",
                filetypes=[("Сертификат лицензии AiPulsar", "*.lic")],
            )
            if save_p:
                export_backup_license_file(save_p, cur_st["hwid"], cur_key, int(cur_st.get("days_left", 365)))
                record_license_to_excel(cur_st["hwid"], "AiPulsar Pro (Резервная копия)", int(cur_st.get("days_left", 365)), "Оплачено", cur_key)
                messagebox.showinfo("Резервная копия создана", f"Сертификат сохранён:\n{save_p}\n\nРеестр Excel обновлён:\n{get_excel_registry_path()}")

        def _restore_hwid_click():
            from tkinter import filedialog, messagebox
            cur_st = self.license_mgr.get_status()
            rec = find_license_by_hwid_in_excel(cur_st["hwid"])
            if rec and rec.get("key"):
                if hasattr(self.license_mgr, "activate_key"):
                    self.license_mgr.activate_key(rec["key"])
                messagebox.showinfo("Лицензия восстановлена по HWID", f"Найдена активная запись для вашего оборудования ({cur_st['hwid']})!\nТариф: {rec['plan_name']}\nСтатус AiPulsar Pro восстановлен.")
                return
            lic_file = filedialog.askopenfilename(
                title="Выберите резервный файл лицензии (.lic) для восстановления без почты",
                filetypes=[("Сертификат лицензии AiPulsar", "*.lic"), ("Все файлы", "*.*")],
            )
            if lic_file:
                ok_f, msg_f, data_f = verify_backup_license_file(lic_file, cur_st["hwid"])
                if ok_f:
                    if hasattr(self.license_mgr, "activate_key") and data_f.get("key"):
                        self.license_mgr.activate_key(data_f["key"])
                    record_license_to_excel(cur_st["hwid"], "AiPulsar Pro (Восстановлено)", int(data_f.get("days", 365)), "Оплачено", data_f.get("key", ""), data_f.get("email", ""))
                    messagebox.showinfo("Лицензия восстановлена", msg_f)
                else:
                    messagebox.showwarning("Проверка лицензии", msg_f)

        tk.Button(rec_box, text="💾 Сохранить резервный файл ключа (.lic)", command=_backup_lic_click, bg="#21262D", fg="#E6EDF3", activebackground="#30363D", relief=tk.FLAT, font=("Segoe UI", 8), padx=10, pady=4, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(rec_box, text="🔄 Восстановить по HWID / Файлу (без почты)", command=_restore_hwid_click, bg="#21262D", fg="#58A6FF", activebackground="#30363D", relief=tk.FLAT, font=("Segoe UI", 8), padx=10, pady=4, cursor="hand2").pack(side=tk.LEFT)


        def _switch_currency_tab(cur: str):
            for c_key, btn in tab_btns.items():
                btn.config(bg=self.ACCENT if c_key == cur else "#0D1117", fg="#FFFFFF" if c_key == cur else "#8B949E")
            for w in plans_holder.winfo_children():
                w.destroy()

            row1 = tk.Frame(plans_holder, bg=self.BG_FIELD)
            row1.pack(fill=tk.X, pady=(0, 4))
            row2 = tk.Frame(plans_holder, bg=self.BG_FIELD)
            row2.pack(fill=tk.X)

            def _open_plan_pay(currency: str, plan_code: str, fallback_url: str, label_price: str):
                em = _get_valid_email()
                if not em:
                    return
                pyperclip.copy(st["hwid"])
                try:
                    from core.yoomoney_pay_bridge import YooMoneyPaymentBridge
                    ym_b = YooMoneyPaymentBridge()
                    if str(ym_b.cfg.get("wallet_number", "")).strip() not in ("", "410010000000000"):
                        ym_b.open_yoomoney_checkout(plan_code)
                        status_lbl.config(text=f"Открыта оплата ЮMoney ({label_price}). Чек и ключ придут на {em}.", fg="#64FFDA")
                        _start_auto_activation_watch()
                        return
                except Exception:
                    pass
                q = urllib.parse.urlencode({"currency": currency, "plan": plan_code, "hwid": st["hwid"], "email": em})
                webbrowser.open(f"{fallback_url}?{q}")
                status_lbl.config(text=f"Открыта оплата ({label_price}). После оплаты Pro включится сам, ключ придёт на {em}.", fg="#64FFDA")
                _start_auto_activation_watch()

            if cur == "RUB":
                tk.Button(row1, text="💳 1 МЕСЯЦ — 299 ₽ (базовый)", command=lambda: _open_plan_pay("RUB", "1M", self.YOOKASSA_RUB_1M, "299 ₽ / 1 мес"), bg="#21262D", fg="#FFFFFF", activebackground="#30363D", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
                tk.Button(row1, text="🔥 3 МЕСЯЦА — 749 ₽ (ВЫГОДА 17%)", command=lambda: _open_plan_pay("RUB", "3M", self.YOOKASSA_RUB_3M, "749 ₽ / 3 мес"), bg="#21262D", fg="#64FFDA", activebackground="#30363D", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True)
                tk.Button(row2, text="💎 6 МЕСЯЦЕВ — 1 290 ₽ (ВЫГОДА 28%)", command=lambda: _open_plan_pay("RUB", "6M", self.YOOKASSA_RUB_6M, "1 290 ₽ / 6 мес"), bg="#21262D", fg="#8BE9FD", activebackground="#30363D", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
                tk.Button(row2, text="👑 1 ГОД — 1 990 ₽ (ВЫГОДА 45%)", command=lambda: _open_plan_pay("RUB", "12M", self.YOOKASSA_RUB_12M, "1 990 ₽ / 1 год"), bg=self.ACCENT, fg="#FFFFFF", activebackground="#651FFF", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                tk.Button(row1, text="💳 1 MONTH — $5 (Base)", command=lambda: _open_plan_pay("USD", "1M", self.YOOKASSA_USD_1M, "$5 / 1 mo"), bg="#21262D", fg="#FFFFFF", activebackground="#30363D", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
                tk.Button(row1, text="🔥 3 MONTHS — $12 (SAVE 20%)", command=lambda: _open_plan_pay("USD", "3M", self.YOOKASSA_USD_3M, "$12 / 3 mo"), bg="#21262D", fg="#64FFDA", activebackground="#30363D", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True)
                tk.Button(row2, text="💎 6 MONTHS — $20 (SAVE 33%)", command=lambda: _open_plan_pay("USD", "6M", self.YOOKASSA_USD_6M, "$20 / 6 mo"), bg="#21262D", fg="#8BE9FD", activebackground="#30363D", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
                tk.Button(row2, text="👑 1 YEAR — $29 (SAVE 52%)", command=lambda: _open_plan_pay("USD", "12M", self.YOOKASSA_USD_12M, "$29 / 1 yr"), bg=self.ACCENT, fg="#FFFFFF", activebackground="#651FFF", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=4, cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_rub = tk.Button(tabs_bar, text="🇷🇺 ОПЛАТА В РУБЛЯХ (₽)", command=lambda: _switch_currency_tab("RUB"), relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=3, cursor="hand2")
        btn_rub.pack(side=tk.LEFT, padx=(0, 6))
        tab_btns["RUB"] = btn_rub

        btn_usd = tk.Button(tabs_bar, text="🌍 PAYMENT IN DOLLARS ($ USD)", command=lambda: _switch_currency_tab("USD"), relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=3, cursor="hand2")
        btn_usd.pack(side=tk.LEFT)
        tab_btns["USD"] = btn_usd
        _switch_currency_tab("USD" if is_en else "RUB")

        key_row = tk.Frame(a_box, bg=self.BG_FIELD)
        key_row.pack(fill=tk.X, pady=(2, 0))
        tk.Label(key_row, text="КОД АКТИВАЦИИ PRO:", bg=self.BG_FIELD, fg="#FFFFFF", font=("Segoe UI Semibold", 8)).pack(side=tk.LEFT, padx=(0, 6))

        key_entry = tk.Entry(key_row, bg=self.BG_CARD, fg="#FFFFFF", insertbackground="#FFFFFF", font=("Consolas", 9), relief=tk.FLAT)
        key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))
        enable_clipboard_and_menu(key_entry, readonly=False)

        def _activate():
            ok, msg = lic.activate_key(key_entry.get())
            status_lbl.config(text=msg, fg="#64FFDA" if ok else "#FF6E6E")
            if ok:
                key_entry.delete(0, tk.END)
                if self.on_activated:
                    self.on_activated()

        key_entry.bind("<Return>", lambda _e: _activate())
        tk.Button(key_row, text="АКТИВИРОВАТЬ", command=_activate, bg=self.ACCENT, fg="#FFFFFF", activebackground="#651FFF", relief=tk.FLAT, font=("Segoe UI Semibold", 8), padx=12, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        tk.Label(a_box, text="Promo", bg=self.BG_FIELD, fg="#8B949E", font=("Segoe UI", 7)).pack(anchor="w", padx=(132, 0), pady=(1, 2))
        status_lbl.pack(anchor="w", pady=(1, 0))
        if st["is_pro"]:
            t_info = f" ({st['time_left']})" if st.get("time_left") else ""
            status_lbl.config(text=f"СТАТУС: PULSAR {st['tier']} АКТИВЕН{t_info}", fg="#64FFDA")

        tk.Label(box, text=f"{APP_COPYRIGHT} | {APP_EMAIL}", bg=self.BG_CARD, fg="#8B949E", font=("Segoe UI", 8)).pack(anchor="center")

        win.update_idletasks()
        apply_win11_round_corners(win)

        def _calc_pro_xy():
            rw = self.root.winfo_width() or 1260
            rh = self.root.winfo_height() or 740
            nx = self.root.winfo_rootx() + (rw - win.winfo_reqwidth()) // 2
            ny = self.root.winfo_rooty() + (rh - win.winfo_reqheight()) // 2
            return (max(20, nx), max(20, ny))

        ix, iy = _calc_pro_xy()
        win.geometry(f"+{ix}+{iy}")
        bind_child_window_to_parent(self.root, win, _calc_pro_xy)







