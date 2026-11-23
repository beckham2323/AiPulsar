from core.risk_advisor import PulsarRiskAdvisor, ADVISOR_SYSTEM_PROMPT
# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import threading
import tkinter as tk
from tkinter import filedialog
from typing import Callable, Optional
from core.clipboard_helper import enable_clipboard_and_menu
from core.pc_doctor import PulsarSystemDoctorAndClipboard
from core.ui_widgets import RoundedCard


class FreeChatPanel:
    """Второй чат (Диалог с AiPulsar) в нативном стиле Windows 11 со скрепкой для анализа файлов."""

    BG_PANEL = "#2B2B2B"
    BG_INPUT = "#1F1F1F"
    BTN_BG = "#383838"
    BTN_HOVER = "#454545"
    ACCENT = "#0078D4"
    WHITE = "#FFFFFF"

    def __init__(
        self,
        parent: tk.Widget,
        on_send_chat: Optional[Callable[[str], None]] = None,
        on_file_attached: Optional[Callable[[str], None]] = None,
    ):
        self.on_send_chat = on_send_chat
        self.on_file_attached = on_file_attached
        self._last_ai_reply = ""

        card = RoundedCard(parent, bg_color=self.BG_PANEL, pad=10)
        card.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        box = card.inner

        hdr = tk.Frame(box, bg=self.BG_PANEL, height=28)
        hdr.pack(fill=tk.X, pady=(0, 6))
        hdr.pack_propagate(False)

        tk.Label(hdr, text="Диалог с AiPulsar", bg=self.BG_PANEL, fg=self.WHITE, font=("Segoe UI Semibold", 10)).pack(side=tk.LEFT, padx=2)

        def _export_last_to_word():
            res_msg = PulsarSystemDoctorAndClipboard.export_text_to_word(self._last_ai_reply)
            self.append_message("AiPulsar", res_msg)

        tk.Button(
            hdr,
            text="Сохранить в Word",
            command=_export_last_to_word,
            bg=self.BTN_BG,
            fg=self.WHITE,
            activebackground=self.BTN_HOVER,
            activeforeground=self.WHITE,
            relief=tk.FLAT,
            font=("Segoe UI", 9),
            padx=10,
            pady=2,
            cursor="hand2",
        ).pack(side=tk.RIGHT)

        self.chat_text = tk.Text(
            box,
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
        self.chat_text.tag_config("human", foreground="#60CDFF", font=("Segoe UI Semibold", 9))
        self.chat_text.tag_config("pulsar", foreground="#FFFFFF", font=("Segoe UI Semibold", 9))
        self.chat_text.tag_config("msg", foreground="#E5E5E5", font=("Segoe UI", 9))
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        enable_clipboard_and_menu(self.chat_text, readonly=True)

        in_row = tk.Frame(box, bg=self.BG_PANEL, height=34)
        in_row.pack(fill=tk.X)
        in_row.pack_propagate(False)

        def _attach_file():
            fp = filedialog.askopenfilename(title="Выберите документ или изображение для анализа")
            if fp and self.on_file_attached:
                threading.Thread(target=self.on_file_attached, args=(fp,), daemon=True).start()

        tk.Button(
            in_row,
            text="📎",
            command=_attach_file,
            bg=self.BTN_BG,
            fg=self.WHITE,
            activebackground=self.BTN_HOVER,
            activeforeground=self.WHITE,
            relief=tk.FLAT,
            font=("Segoe UI", 11),
            width=4,
            cursor="hand2",
        ).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        self.chat_entry = tk.Entry(
            in_row,
            bg=self.BG_INPUT,
            fg=self.WHITE,
            insertbackground=self.WHITE,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#3D3D3D",
        )
        self.chat_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        enable_clipboard_and_menu(self.chat_entry, readonly=False)

        def _send(_event=None):
            q = self.chat_entry.get().strip()
            if not q:
                return
            self.chat_entry.delete(0, tk.END)
            if self.on_send_chat:
                threading.Thread(target=self.on_send_chat, args=(q,), daemon=True).start()

        self.chat_entry.bind("<Return>", _send)
        tk.Button(
            in_row,
            text="Отправить",
            command=_send,
            bg=self.ACCENT,
            fg=self.WHITE,
            activebackground="#106EBE",
            activeforeground=self.WHITE,
            relief=tk.FLAT,
            font=("Segoe UI Semibold", 9),
            padx=16,
            cursor="hand2",
        ).pack(side=tk.RIGHT, fill=tk.Y)

    def append_message(self, sender: str, msg: str):
        self.chat_text.config(state=tk.NORMAL)
        is_h = sender == "Вы"
        self.chat_text.insert(tk.END, "Вы: " if is_h else "AiPulsar: ", "human" if is_h else "pulsar")
        self.chat_text.insert(tk.END, f"{msg}\n\n", "msg")
        if not is_h:
            self._last_ai_reply = str(msg)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
