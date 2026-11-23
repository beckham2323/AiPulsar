from tkinter import filedialog
from core.pc_doctor import show_system_health_window
from core.ui_widgets import attach_tab_popup_to_main
from core.self_healing_identity import SelfHealingAndMemoryEngine
from core.game_cinema_mode import GameCinemaModeManager
from core.home_security_guard import HomeSecurityGuard
from core.video_call_bridge import VideoCallLauncherDialog
# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import ctypes
import inspect
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from typing import Callable, Optional
from core.audio_panel import AudioSettingsPopup
from core.clipboard_helper import enable_clipboard_and_menu
from core.commands_help import CommandsCheatsheetDialog
from core.free_chat_panel import FreeChatPanel
from core.i18n import get_lang, set_lang
from core.license_manager import AiPulsarLicenseManager
from core.pro_dialog import ProUpgradeDialog
from core.quantum_bridge import QuantumPhoneBridgeDialog
from core.ui_widgets import RoundedCard, apply_win11_round_corners, bind_child_window_to_parent

try:
    import winreg
except Exception:
    winreg = None


class AiPulsarEnvironmentWindow:
    """Строгий интерфейс Windows 11 с левой сворачиваемой боковой панелью и двумя симметричными чатами."""

    BG_ROOT = "#202020"
    BG_SIDEBAR = "#1B1B1B"
    BG_PANEL = "#2B2B2B"
    BG_INPUT = "#1F1F1F"
    BTN_BG = "#2D2D2D"
    BTN_HOVER = "#3A3A3A"
    ACCENT = "#0078D4"
    WHITE = "#FFFFFF"
    MUTED = "#B8B8B8"
    GREEN_STATUS = "#4ADE80"

    def __init__(
        self,
        on_text_command: Optional[Callable[[str], None]] = None,
        on_free_chat: Optional[Callable[[str], None]] = None,
        on_file_attached: Optional[Callable[[str], None]] = None,
        on_mic_change: Optional[Callable[[Optional[int]], None]] = None,
        on_speaker_change: Optional[Callable[[Optional[int]], None]] = None,
        on_voice_change: Optional[Callable[[str], None]] = None,
        on_lang_change: Optional[Callable[[str], None]] = None,
        on_mute_toggle: Optional[Callable[[bool], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
        models_dir: str = "models",
        **kwargs,
    ):
        self.on_text_command = on_text_command
        self.on_free_chat = on_free_chat
        self.on_file_attached = on_file_attached
        self.on_mic_change = on_mic_change
        self.on_speaker_change = on_speaker_change
        self.on_voice_change = on_voice_change
        self.on_lang_change = on_lang_change
        self.on_mute_toggle = on_mute_toggle
        self.on_quit = on_quit
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self._prefs_path = os.path.join(self.models_dir, "automation_prefs.json")

        self.root: Optional[tk.Tk] = None
        self.log_text: Optional[tk.Text] = None
        self.free_chat: Optional[FreeChatPanel] = None
        self._state = "idle"
        self._is_muted = False
        self._voice_muted = False
        self.on_voice_mute_toggle = None

    def _load_prefs(self) -> dict:
        data = {"autostart": False, "auto_evolution": True}
        if os.path.exists(self._prefs_path):
            try:
                with open(self._prefs_path, "r", encoding="utf-8") as f:
                    data.update(json.load(f))
            except Exception:
                pass
        if winreg:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ) as rk:
                    winreg.QueryValueEx(rk, "AiPulsar")
                    data["autostart"] = True
            except Exception:
                data["autostart"] = False
        return data

    def _save_prefs(self, prefs: dict):
        try:
            with open(self._prefs_path, "w", encoding="utf-8") as f:
                json.dump(prefs, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _apply_windows_autostart(self, enabled: bool):
        if not winreg:
            return
        run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE) as rk:
                if enabled:
                    exe_path = sys.executable if getattr(sys, "frozen", False) else os.path.abspath("dist/AiPulsar/AiPulsar.exe")
                    if not os.path.exists(exe_path):
                        exe_path = sys.executable
                    winreg.SetValueEx(rk, "AiPulsar", 0, winreg.REG_SZ, f'"{exe_path}" --tray')
                else:
                    try:
                        winreg.DeleteValue(rk, "AiPulsar")
                    except FileNotFoundError:
                        pass
        except Exception:
            pass

    def set_state(self, state: str):
        self._state = state

    def set_out_list(self, items):
        pass

    def set_mic_list(self, items):
        pass

    def set_mic_level(self, level):
        pass

    def log_message(self, sender: str, msg: str):
        if not self.root or not self.log_text:
            return
        def _upd():
            self.log_text.config(state=tk.NORMAL)
            is_h = sender == "Вы"
            self.log_text.insert(tk.END, "Вы: " if is_h else "AiPulsar: ", "human" if is_h else "pulsar")
            self.log_text.insert(tk.END, f"{msg}\n\n", "msg")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _upd)

    def append_log(self, sender: str, msg: str):
        if not self.root or not getattr(self, "log_text", None):
            return
        clean_msg = str(msg or "").strip()
        if not clean_msg:
            return
        import time as _t
        now = _t.time()
        norm = " ".join(clean_msg.lower().split())
        recent = getattr(self, "_recent_chat_msgs", [])
        recent = [(ts, s, m) for (ts, s, m) in recent if (now - ts) < 6.0]
        if any(s == sender and m == norm for (_ts, s, m) in recent):
            return
        recent.append((now, sender, norm))
        self._recent_chat_msgs = recent[-8:]

        def _ins():
            try:
                self.log_text.config(state=tk.NORMAL)
                tag = "human" if sender in ("Вы", "User", "Пользователь") else "pulsar"
                self.log_text.insert(tk.END, f"{sender}: ", tag)
                self.log_text.insert(tk.END, f"{clean_msg}" + chr(10)*2, "msg")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
            except Exception:
                pass
        self.root.after(0, _ins)


    def log_free_chat(self, sender: str, msg: str):
        self.append_log(sender, msg)


    def show_window(self):
        if self.root:
            self.root.after(0, lambda: (self.root.deiconify(), self.root.lift(), self.root.focus_force()))

    def hide_to_tray(self):
        if self.root:
            self.root.after(0, self.root.withdraw)
    def run_mainloop(self):
        root = tk.Tk()
        self.root = root
        root.title("AiPulsar — Интеллектуальный ассистент Windows")
        root.configure(bg=self.BG_ROOT)
        root.minsize(920, 680)

        w, h = 1040, 730
        sx = (root.winfo_screenwidth() - w) // 2
        sy = (root.winfo_screenheight() - h) // 2
        root.geometry(f"{w}x{h}+{sx}+{sy}")

        for ico_p in ("aipulsar.ico", "_internal/aipulsar.ico"):
            if os.path.exists(ico_p):
                try:
                    root.iconbitmap(ico_p)
                    break
                except Exception:
                    pass

        apply_win11_round_corners(root)

        help_dialog = CommandsCheatsheetDialog(root)
        sig = inspect.signature(AudioSettingsPopup.__init__).parameters
        kw = {}
        for k, val in (
            ("on_mic_change", self.on_mic_change),
            ("on_speaker_change", self.on_speaker_change),
            ("on_voice_change", self.on_voice_change),
            ("on_lang_change", self.on_lang_change),
            ("models_dir", self.models_dir),
        ):
            if k in sig:
                kw[k] = val
        audio_panel = AudioSettingsPopup(root, **kw)

        shell = tk.Frame(root, bg=self.BG_ROOT)
        shell.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        sidebar_card = RoundedCard(shell, bg_color=self.BG_SIDEBAR, pad=8, width=250, height=700)
        sidebar_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        sb = sidebar_card.inner

        lic_box = tk.Frame(sb, bg=self.BG_SIDEBAR)
        lic_box.pack(fill=tk.X, pady=(2, 6))

        tier_badge = tk.Label(
            lic_box,
            text="FREE",
            bg=self.BG_INPUT,
            fg=self.MUTED,
            font=("Segoe UI Semibold", 8),
            padx=8,
            pady=4,
            highlightthickness=1,
            highlightbackground="#383838",
        )
        tier_badge.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        pro_btn = tk.Button(
            lic_box,
            text="★ Pro версия",
            bg=self.ACCENT,
            fg=self.WHITE,
            activebackground="#106EBE",
            activeforeground=self.WHITE,
            relief=tk.FLAT,
            font=("Segoe UI Semibold", 8),
            padx=10,
            pady=4,
            cursor="hand2",
        )
        pro_btn.pack(side=tk.RIGHT)

        trial_btn = tk.Button(
            sb,
            text="🎁 Активировать 3 дня Pro",
            bg=self.BTN_BG,
            fg="#60CDFF",
            activebackground=self.BTN_HOVER,
            activeforeground=self.WHITE,
            relief=tk.FLAT,
            font=("Segoe UI Semibold", 8),
            pady=5,
            cursor="hand2",
        )

        def _refresh_license_ui():
            lm = AiPulsarLicenseManager(models_dir=self.models_dir)
            st = lm.get_status()
            tier = st.get("tier", "FREE")
            t_left = st.get("time_left", "")

            if st["is_pro"] and tier == "TRIAL":
                trial_btn.pack_forget()
                tier_badge.config(text=f"FREE • {t_left}", fg=self.GREEN_STATUS)
                pro_btn.config(text="★ Pro версия", bg=self.ACCENT)
            elif st["is_pro"]:
                trial_btn.pack_forget()
                pro_lbl = f"PRO • {t_left}" if (t_left and t_left != "Навсегда") else "PRO"
                tier_badge.config(text=pro_lbl, fg=self.GREEN_STATUS)
                pro_btn.config(text="★ Pro активен", bg=self.BTN_BG)
            else:
                tier_badge.config(text="FREE", fg=self.MUTED)
                pro_btn.config(text="★ Pro версия", bg=self.ACCENT)
                if not lm.is_trial_used():
                    trial_btn.pack(fill=tk.X, pady=(0, 6), after=lic_box)
                else:
                    trial_btn.pack_forget()

        def _activate_trial():
            ok, msg = AiPulsarLicenseManager(models_dir=self.models_dir).start_3day_trial()
            _refresh_license_ui()
            self.log_message("AiPulsar", msg)

        trial_btn.config(command=_activate_trial)
        pro_dialog = ProUpgradeDialog(root, on_activated=_refresh_license_ui)
        pro_btn.config(command=lambda: pro_dialog.show())

        phone_bridge = QuantumPhoneBridgeDialog(root, on_remote_cmd=self.on_text_command, on_notify=self.log_free_chat)

        def _open_teleport():
            if not AiPulsarLicenseManager(models_dir=self.models_dir).get_status().get("is_pro"):
                self.log_message("AiPulsar", "Квантовый Телепорт доступен в версии Pro.")
                pro_dialog.show()
                return
            phone_bridge.show()

        def _make_collapsible_section(title_txt: str):
            sec_wrap = tk.Frame(sb, bg=self.BG_SIDEBAR)
            sec_wrap.pack(fill=tk.X, pady=(6, 0))
            body = tk.Frame(sec_wrap, bg=self.BG_SIDEBAR)
            body.pack(fill=tk.X)
            state_box = {"open": True}
            hdr_lbl = tk.Label(
                sec_wrap,
                text=f"▾  {title_txt}",
                bg=self.BG_SIDEBAR,
                fg="#A0A0A0",
                font=("Segoe UI Semibold", 8),
                anchor="w",
                justify=tk.LEFT,
                padx=8,
                pady=4,
                cursor="hand2",
            )
            hdr_lbl.pack(fill=tk.X, before=body)
            def _toggle_sec(_e=None):
                if state_box["open"]:
                    body.pack_forget()
                    state_box["open"] = False
                    hdr_lbl.config(text=f"▸  {title_txt}")
                else:
                    body.pack(fill=tk.X)
                    state_box["open"] = True
                    hdr_lbl.config(text=f"▾  {title_txt}")
            hdr_lbl.bind("<Button-1>", _toggle_sec)
            return body

        def _nav_btn(parent_box: tk.Widget, text_lbl: str, cmd_fn):
            parts = text_lbl.strip().split("  ", 1)
            icon_part = parts[0] if len(parts) == 2 else ""
            title_part = parts[1].strip() if len(parts) == 2 else text_lbl.strip()

            row = tk.Frame(parent_box, bg=self.BTN_BG, cursor="hand2")
            row.pack(fill=tk.X, pady=2)

            ico_lbl = tk.Label(
                row,
                text=icon_part,
                bg=self.BTN_BG,
                fg=self.WHITE,
                font=("Segoe UI Emoji", 9),
                width=3,
                anchor="center",
                pady=5,
                cursor="hand2",
            )
            ico_lbl.pack(side=tk.LEFT, padx=(4, 0))

            lbl = tk.Label(
                row,
                text=title_part,
                bg=self.BTN_BG,
                fg=self.WHITE,
                font=("Segoe UI", 9),
                anchor="w",
                justify=tk.LEFT,
                padx=2,
                pady=5,
                cursor="hand2",
            )
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def _on_enter(_e):
                row.config(bg=self.BTN_HOVER)
                ico_lbl.config(bg=self.BTN_HOVER)
                lbl.config(bg=self.BTN_HOVER)

            def _on_leave(_e):
                row.config(bg=self.BTN_BG)
                ico_lbl.config(bg=self.BTN_BG)
                lbl.config(bg=self.BTN_BG)

            for w_item in (row, ico_lbl, lbl):
                w_item.bind("<Enter>", _on_enter)
                w_item.bind("<Leave>", _on_leave)
                w_item.bind("<Button-1>", lambda _e: cmd_fn())
            return row

        sec_tools = _make_collapsible_section("ИНСТРУМЕНТЫ")
        def _toggle_game_cinema():
            from tkinter import messagebox
            active = GameCinemaModeManager.get_instance().toggle_manual()
            msg = "🎮 Режим Игры / Кино ВКЛЮЧЁН (тихий режим без помех и снижение нагрузки на CPU).\n\nТакже режим включается АВТОМАТИЧЕСКИ при запуске игр/видео во весь экран или голосом: «Я играю», «Режим кино», «Я вернулся»." if active else "✅ Режим Игры / Кино ВЫКЛЮЧЕН. Ассистент вернулся в активный режим."
            messagebox.showinfo("AiPulsar — Режим Игры / Кино", msg, parent=root)
        _nav_btn(sec_tools, "👤  Профиль", lambda: SelfHealingAndMemoryEngine().open_acquaintance_dialog(root))
        _nav_btn(sec_tools, "🎮  Режим Игры / Кино", _toggle_game_cinema)
        _nav_btn(sec_tools, "🛡️  Сканировать ПК (Щит)", lambda: HomeSecurityGuard(root).manual_scan_with_report())
        _nav_btn(sec_tools, "🩺  Проверить здоровье системы", lambda: show_system_health_window(root))
        _nav_btn(sec_tools, "📞  Видеозвонок", lambda: VideoCallLauncherDialog(root).show())
        _nav_btn(sec_tools, "🌐  Браузер", lambda: ctypes.windll.shell32.ShellExecuteW(0, "open", "https://", None, None, 1))
        _nav_btn(sec_tools, "📂  Этот компьютер", lambda: subprocess.Popen(["explorer.exe", "shell:MyComputerFolder"]))
        _nav_btn(sec_tools, "⚙️  Параметры Windows", lambda: ctypes.windll.shell32.ShellExecuteW(0, "open", "ms-settings:", None, None, 1))
        _nav_btn(sec_tools, "📊  Диспетчер задач", lambda: subprocess.Popen(["taskmgr.exe"]))
        _nav_btn(sec_tools, "📱  Квантовый Телепорт", _open_teleport)
        sec_auto = _make_collapsible_section("АВТОМАТИЗАЦИЯ")
        prefs = self._load_prefs()
        var_autostart = tk.BooleanVar(value=bool(prefs.get("autostart", False)))
        var_evolution = tk.BooleanVar(value=bool(prefs.get("auto_evolution", True)))

        def _on_toggle_autostart():
            val = bool(var_autostart.get())
            prefs["autostart"] = val
            self._save_prefs(prefs)
            self._apply_windows_autostart(val)
            self.log_message("AiPulsar", "Запуск при входе в Windows включён и сохранён." if val else "Запуск при входе в Windows отключён и сохранён.")

        def _on_toggle_evolution():
            val = bool(var_evolution.get())
            prefs["auto_evolution"] = val
            self._save_prefs(prefs)
            if self.on_text_command:
                cmd_str = "Включи фоновое самообучение" if val else "Отключи фоновое самообучение"
                threading.Thread(target=self.on_text_command, args=(cmd_str,), daemon=True).start()
            self.log_message("AiPulsar", "Фоновое самообучение включено и сохранено." if val else "Фоновое самообучение отключено и сохранено.")

        for cb_text, cb_var, cb_cmd in [
            ("Запускать при входе Windows", var_autostart, _on_toggle_autostart),
            ("Фоновое самообучение", var_evolution, _on_toggle_evolution),
        ]:
            cb = tk.Checkbutton(
                sec_auto,
                text=cb_text,
                variable=cb_var,
                command=cb_cmd,
                bg=self.BTN_BG,
                fg=self.WHITE,
                selectcolor="#1F1F1F",
                activebackground=self.BTN_HOVER,
                activeforeground=self.WHITE,
                relief=tk.FLAT,
                font=("Segoe UI", 8),
                anchor="w",
                justify=tk.LEFT,
                padx=8,
                pady=4,
                cursor="hand2",
            )
            cb.pack(fill=tk.X, pady=2)

        _nav_btn(sec_auto, "🗂️  Порядок на Рабочем столе", lambda: threading.Thread(target=self.on_text_command, args=("Наведи порядок на Рабочем столе",), daemon=True).start())
        _nav_btn(sec_auto, "🧹  Очистить временные файлы", lambda: threading.Thread(target=self.on_text_command, args=("Очисти память и временные файлы",), daemon=True).start())
        _nav_btn(sec_auto, "🕒  Машина времени экрана", lambda: threading.Thread(target=self.on_text_command, args=("Включи машину времени экрана",), daemon=True).start())

        def _open_side_popup(title_txt: str, build_body_fn, height_px: int = 230):
            pop = tk.Toplevel(root)
            pop.title(title_txt)
            pop.configure(bg=self.BG_PANEL)
            pop.overrideredirect(True)
            card = RoundedCard(pop, bg_color=self.BG_PANEL, pad=12, width=420, height=height_px)
            card.pack(fill=tk.BOTH, expand=True)
            inner = card.inner
            hdr = tk.Frame(inner, bg=self.BG_PANEL)
            hdr.pack(fill=tk.X, pady=(0, 8))
            tk.Label(hdr, text=title_txt, bg=self.BG_PANEL, fg=self.WHITE, font=("Segoe UI Semibold", 10)).pack(side=tk.LEFT)
            tk.Button(hdr, text="✕", command=pop.destroy, bg=self.BG_PANEL, fg=self.WHITE, activebackground=self.BTN_HOVER, relief=tk.FLAT, font=("Segoe UI", 9), padx=6, cursor="hand2").pack(side=tk.RIGHT)
            build_body_fn(inner, pop)
            pop.update_idletasks()
            apply_win11_round_corners(pop)
            def _xy():
                return (root.winfo_rootx() + (root.winfo_width() - 420) // 2, root.winfo_rooty() + (root.winfo_height() - height_px) // 2)
            x0, y0 = _xy()
            pop.geometry(f"+{x0}+{y0}")
            bind_child_window_to_parent(root, pop, _xy)
            pop.lift()
            pop.focus_force()

        def _show_lang_dialog():
            def _body(box, pop):
                cur = get_lang()
                tk.Label(box, text="Выберите язык интерфейса и распознавания речи:", bg=self.BG_PANEL, fg=self.MUTED, font=("Segoe UI", 9), anchor="w").pack(fill=tk.X, pady=(0, 8))
                for code, name in [("ru", "🇷🇺  Русский (Россия)"), ("en", "🇺🇸  English (International)")]:
                    is_sel = (cur == code)
                    b = tk.Button(
                        box,
                        text=("✓  " + name) if is_sel else ("     " + name),
                        bg="#424242" if is_sel else "#333333",
                        fg=self.WHITE,
                        activebackground=self.BTN_HOVER,
                        relief=tk.FLAT,
                        font=("Segoe UI", 9),
                        anchor="w",
                        justify=tk.LEFT,
                        padx=12,
                        pady=6,
                        cursor="hand2",
                        command=lambda c=code: (set_lang(c), self.on_lang_change(c) if self.on_lang_change else None, pop.destroy()),
                    )
                    b.pack(fill=tk.X, pady=3)
            _open_side_popup("Язык и регион", _body, 195)

        def _show_hotkeys_dialog():
            def _body(box, _pop):
                for hk, desc in [
                    ("Активация голосом", "Скажите «Пульсар» в любой момент"),
                    ("Ctrl + C → Выжимка", "Копирование текста для анализа в чате"),
                    ("Enter в чате", "Мгновенная отправка команды или вопроса"),
                    ("Закрытие окна (✕)", "Сворачивание в системный трей Windows"),
                ]:
                    row = tk.Frame(box, bg="#333333")
                    row.pack(fill=tk.X, pady=2)
                    tk.Label(row, text=hk, bg="#333333", fg="#60CDFF", font=("Segoe UI Semibold", 8), padx=8, pady=4).pack(side=tk.LEFT)
                    tk.Label(row, text=desc, bg="#333333", fg=self.WHITE, font=("Segoe UI", 8), padx=8, pady=4).pack(side=tk.RIGHT)
            _open_side_popup("Горячие клавиши и управление", _body, 225)

        def _show_about_dialog():
            def _body(box, _pop):
                st = AiPulsarLicenseManager(models_dir=self.models_dir).get_status()
                for k_lbl, v_lbl in [
                    ("Продукт:", "AiPulsar Desktop Assistant (x64)"),
                    ("Разработчик:", "V.E. Smirnov (VESKOR)"),
                    ("Идентификатор ПК:", st.get("hwid", "—")),
                    ("Статус лицензии:", st.get("tier", "FREE")),
                    ("Целостность кода:", "Защищено цифровой подписью SHA-256"),
                ]:
                    row = tk.Frame(box, bg=self.BG_PANEL)
                    row.pack(fill=tk.X, pady=2)
                    tk.Label(row, text=k_lbl, bg=self.BG_PANEL, fg=self.MUTED, font=("Segoe UI", 9)).pack(side=tk.LEFT)
                    tk.Label(row, text=v_lbl, bg=self.BG_PANEL, fg=self.WHITE, font=("Segoe UI Semibold", 9)).pack(side=tk.RIGHT)
            _open_side_popup("Система и версия", _body, 220)
        def _show_av_guide_dialog():
            def _body(box, _pop):
                info_txt = (
                    "AiPulsar напрямую управляет файлами, папками, системными "
                    "настройками и реестром Windows.\n\n"
                    "Чтобы защитные системы не блокировали работу ассистента:\n"
                    "1. Добавьте папку установки AiPulsar в «Исключения» (Доверенные) "
                    "Защитника Windows или вашего антивируса.\n"
                    "2. Запускайте программу с правами Администратора для полного доступа "
                    "ко всем разделам и службам системы.\n"
                    "3. При необходимости временно приостановите контроль в реальном времени "
                    "на момент первичной настройки."
                )
                lbl = tk.Label(
                    box,
                    text=info_txt,
                    bg=self.BG_PANEL,
                    fg=self.WHITE,
                    font=("Segoe UI", 9),
                    justify=tk.LEFT,
                    anchor="w",
                    wraplength=390,
                )
                lbl.pack(fill=tk.BOTH, expand=True)
            _open_side_popup("Рекомендации по антивирусу и правам", _body, 255)

        sec_set = _make_collapsible_section("НАСТРОЙКИ И СПРАВКА")
        _nav_btn(sec_set, "🎙️  Параметры аудио и голоса", lambda: audio_panel.toggle())
        _nav_btn(sec_set, "🌍  Язык и регион", _show_lang_dialog)
        _nav_btn(sec_set, "⌨️  Горячие клавиши", _show_hotkeys_dialog)
        _nav_btn(sec_set, "ℹ️  Система и версия", _show_about_dialog)
        _nav_btn(sec_set, "📖  Шпаргалка команд", lambda: help_dialog.toggle())
        _nav_btn(sec_set, "🛡️  Доступ и антивирус", _show_av_guide_dialog)

        _refresh_license_ui()
        def _tick_timer():
            try:
                if root.winfo_exists():
                    _refresh_license_ui()
                    root.after(60000, _tick_timer)
            except Exception:
                pass
        root.after(60000, _tick_timer)

        right_col = tk.Frame(shell, bg=self.BG_ROOT)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 12), pady=12)

        voice_card = RoundedCard(right_col, bg_color=self.BG_PANEL, pad=10)
        voice_card.pack(fill=tk.BOTH, expand=True)
        vbox = voice_card.inner

        vhdr = tk.Frame(vbox, bg=self.BG_PANEL, height=28)
        vhdr.pack(fill=tk.X, pady=(0, 6))
        vhdr.pack_propagate(False)

        tk.Label(vhdr, text="💬 Единый умный чат и управление AiPulsar", bg=self.BG_PANEL, fg=self.WHITE, font=("Segoe UI Semibold", 10)).pack(side=tk.LEFT, padx=2)

        mute_btn = tk.Button(
            vhdr,
            text="🎙️ Микрофон включён",
            bg=self.BTN_BG,
            fg=self.WHITE,
            activebackground=self.BTN_HOVER,
            activeforeground=self.WHITE,
            relief=tk.FLAT,
            font=("Segoe UI", 9),
            padx=10,
            pady=2,
            cursor="hand2",
        )

        def _toggle_mute():
            self._is_muted = not self._is_muted
            mute_btn.config(text="🔇 Микрофон выключен" if self._is_muted else "🎙️ Микрофон включён")
            if self.on_mute_toggle:
                self.on_mute_toggle(self._is_muted)

        mute_btn.config(command=_toggle_mute)
        mute_btn.pack(side=tk.RIGHT)

        voice_btn = tk.Button(
            vhdr,
            text="🔊 Голос включён",
            bg=self.BTN_BG,
            fg=self.WHITE,
            activebackground=self.BTN_HOVER,
            activeforeground=self.WHITE,
            relief=tk.FLAT,
            font=("Segoe UI", 9),
            padx=10,
            pady=2,
            cursor="hand2",
        )

        def _toggle_voice_out():
            self._voice_muted = not self._voice_muted
            voice_btn.config(text="🔇 Голос выключен" if self._voice_muted else "🔊 Голос включён")
            if self.on_voice_mute_toggle:
                try:
                    self.on_voice_mute_toggle(self._voice_muted)
                except Exception:
                    pass

        voice_btn.config(command=_toggle_voice_out)
        voice_btn.pack(side=tk.RIGHT, padx=(0, 6))

        self.log_text = tk.Text(
            vbox,
            bg=self.BG_INPUT,
            fg=self.WHITE,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#3D3D3D",
            wrap=tk.WORD,
            padx=10,
            pady=8,
            spacing3=5,
            height=9,
            state=tk.DISABLED,
        )
        self.log_text.tag_config("human", foreground="#60CDFF", font=("Segoe UI Semibold", 9))
        self.log_text.tag_config("pulsar", foreground="#FFFFFF", font=("Segoe UI Semibold", 9))
        self.log_text.tag_config("msg", foreground="#E5E5E5", font=("Segoe UI", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        enable_clipboard_and_menu(self.log_text, readonly=True)

        vin_row = tk.Frame(vbox, bg=self.BG_PANEL, height=34)
        vin_row.pack(fill=tk.X)
        vin_row.pack_propagate(False)

        def _attach_file_unified():
            fp = filedialog.askopenfilename(
                parent=root,
                title="Выберите файл для анализа в умном чате AiPulsar",
                filetypes=[("Все поддерживаемые", "*.txt *.pdf *.docx *.xlsx *.csv *.py *.json *.png *.jpg *.jpeg"), ("Все файлы", "*.*")]
            )
            if fp:
                self.append_log("Вы", f"📎 Прикреплён файл: {fp}")
                if self.on_file_attached:
                    threading.Thread(target=self.on_file_attached, args=(fp,), daemon=True).start()
                elif self.on_text_command:
                    threading.Thread(target=self.on_text_command, args=(f"проанализируй файл {fp}",), daemon=True).start()

        tk.Button(
            vin_row,
            text="📎",
            command=_attach_file_unified,
            bg=self.BTN_BG,
            fg=self.WHITE,
            activebackground=self.BTN_HOVER,
            activeforeground=self.WHITE,
            relief=tk.FLAT,
            font=("Segoe UI", 10),
            padx=10,
            cursor="hand2",
        ).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))

        cmd_entry = tk.Entry(
            vin_row,
            bg=self.BG_INPUT,
            fg=self.WHITE,
            insertbackground=self.WHITE,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#3D3D3D",
        )
        cmd_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        enable_clipboard_and_menu(cmd_entry, readonly=False)

        def _send_cmd(_event=None):
            q = cmd_entry.get().strip()
            if not q:
                return
            cmd_entry.delete(0, tk.END)
            if self.on_text_command:
                threading.Thread(target=self.on_text_command, args=(q,), daemon=True).start()

        cmd_entry.bind("<Return>", _send_cmd)
        tk.Button(
            vin_row,
            text="Отправить",
            command=_send_cmd,
            bg=self.ACCENT,
            fg=self.WHITE,
            activebackground="#106EBE",
            activeforeground=self.WHITE,
            relief=tk.FLAT,
            font=("Segoe UI Semibold", 9),
            padx=16,
            cursor="hand2",
        ).pack(side=tk.RIGHT, fill=tk.Y)

        self.free_chat = None  # [объединено в единый умный чат]

        root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        HomeSecurityGuard(root).start_background_patrol(interval_sec=300)
        GameCinemaModeManager.get_instance().start_auto_monitor(interval_sec=5)
        def _poll_companion_mod_notifications():
            try:
                import json as _j, os as _o
                for mdir in (_o.path.join(_o.getcwd(), "models"), r"D:\AiPulsar\models", r"D:\AiPulsar\dist\AiPulsar\models"):
                    np = _o.path.join(mdir, "companion_notifications.jsonl")
                    if _o.path.exists(np):
                        with open(np, "r", encoding="utf-8", errors="ignore") as f:
                            lines = [ln.strip() for ln in f if ln.strip()]
                        _o.remove(np)
                        for ln in lines:
                            try:
                                item = _j.loads(ln)
                                title = item.get("title", "Новый навык")
                                kws = ", ".join(item.get("keywords", []))
                                msg_n = (
                                    f"🧬 ИИ-Помощник создал, протестировал в песочнице и автоматически установил новый рабочий мод:\n"
                                    f"• Навык: «{title}»\n"
                                    f"• Ключевые фразы для вызова: {kws}\n"
                                    "Мод уже активен — можете сразу проверить его в работе!"
                                )
                                self.append_log("AiPulsar", msg_n)
                            except Exception:
                                pass
            except Exception:
                pass
            try:
                if root.winfo_exists():
                    root.after(5000, _poll_companion_mod_notifications)
            except Exception:
                pass

        root.after(4000, _poll_companion_mod_notifications)

        root.mainloop()




OkoEnvironment = AiPulsarEnvironmentWindow
