# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import ctypes
import datetime
import os
import shutil
import tempfile
import psutil
import pyperclip
from core.i18n import get_lang


class PulsarSystemDoctorAndClipboard:
    """Системный врач ПК, игровой режим «Не беспpulsarить» и умный разбор буфера обмена."""

    def __init__(self, brain):
        self.brain = brain
        self.dnd_mode = False
        self.missed_alarms = []

    def toggle_dnd(self, enable: bool) -> str:
        is_en = get_lang() == "en"
        self.dnd_mode = bool(enable)
        if self.dnd_mode:
            return "Do Not Disturb / Gaming mode enabled." if is_en else "Игровой режим «Не беспpulsarить» включён."
        missed = ""
        if self.missed_alarms:
            missed = " Пропущенные напоминания: " + "; ".join(self.missed_alarms)
            self.missed_alarms.clear()
        return ("Gaming mode disabled." if is_en else "Обычный режим включён.") + missed

    def check_pc_health(self) -> str:
        is_en = get_lang() == "en"
        cpu = psutil.cpu_percent(interval=0.4)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")
        free_gb = round(disk.free / (1024 ** 3), 1)
        if is_en:
            return f"CPU load {cpu}%, RAM {ram.percent}% used, free space on C: {free_gb} GB."
        return f"Процессор загружен на {cpu}%, память на {ram.percent}%, свободно на диске C: {free_gb} ГБ."

    def clean_temp_and_memory(self) -> str:
        is_en = get_lang() == "en"
        freed_bytes = 0
        temp_dir = tempfile.gettempdir()
        for entry in os.scandir(temp_dir):
            try:
                if entry.is_file(follow_symlinks=False):
                    sz = entry.stat().st_size
                    os.remove(entry.path)
                    freed_bytes += sz
                elif entry.is_dir(follow_symlinks=False):
                    sz = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(entry.path) for f in fs)
                    shutil.rmtree(entry.path, ignore_errors=True)
                    freed_bytes += sz
            except Exception:
                pass

        try:
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
        except Exception:
            pass

        freed_mb = round(freed_bytes / (1024 * 1024), 1)
        ram_after = psutil.virtual_memory().percent
        if is_en:
            return f"Cleaned {freed_mb} MB of temporary files. RAM load is now {ram_after}%."
        return f"Очистил {freed_mb} МБ временных файлов и корзину. Память загружена на {ram_after}%."

    def analyze_clipboard(self, mode: str = "summary") -> str:
        is_en = get_lang() == "en"
        clip = (pyperclip.paste() or "").strip()
        if not clip:
            return "Clipboard is empty. Copy some text first." if is_en else "Не могу выполнить: буфер обмена пуст. Решение: выделите текст и нажмите Ctrl+C."

        snippet = clip[:4500]
        if mode == "reply":
            prompt = (
                f"Write a polite, concise reply to this copied message:\n\n{snippet}"
                if is_en
                else f"Напиши вежливый и лаконичный ответ на это скопированное сообщение:\n\n{snippet}"
            )
        else:
            prompt = (
                f"Summarize the copied text in 3 short bullet points:\n\n{snippet}"
                if is_en
                else f"Сделай краткую выжимку из скопированного текста в 3 коротких пунктах:\n\n{snippet}"
            )
        ans = self.brain.ask_free_chat([{"role": "user", "content": prompt}])
        return ans or snippet[:600]

    @staticmethod
    def export_text_to_word(text_content: str) -> str:
        is_en = get_lang() == "en"
        clean = (text_content or "").strip()
        if not clean:
            return "Nothing to export yet." if is_en else "В чате пока нет ответа для сохранения."
        try:
            from docx import Document
            doc = Document()
            doc.add_heading("AiPulsar — Отчёт / Заметка" if not is_en else "AiPulsar — Note / Report", level=1)
            for para in clean.splitlines():
                if para.strip():
                    doc.add_paragraph(para.strip())
            desk = os.path.join(os.path.expanduser("~"), "Desktop")
            os.makedirs(desk, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(desk, f"AiPulsar_Chat_{ts}.docx")
            doc.save(out_path)
            return f"Saved to Desktop: {os.path.basename(out_path)}" if is_en else f"Сохранил на Рабочий стол: {os.path.basename(out_path)}"
        except Exception as e:
            return f"Export error: {e}"



def show_system_health_window(parent=None):
    """Открывает интерактивное окно проверки здоровья ПК (CPU, RAM, диски, процессы, очистка кэша)."""
    import os, psutil, shutil, tempfile, tkinter as tk
    from tkinter import messagebox

    win = tk.Toplevel(parent)
    win.title("🩺 AiPulsar — Проверка здоровья системы")
    win.geometry("540x420")
    win.resizable(False, False)
    win.configure(bg="#1E1E1E")

    tk.Label(win, text="🩺 Диагностика здоровья ПК в реальном времени", bg="#1E1E1E", fg="#00AFF0", font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=20, pady=(14, 6))

    box = tk.Text(win, bg="#252526", fg="#E8E8E8", font=("Consolas", 10), relief=tk.FLAT, padx=12, pady=10, height=14)
    box.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 12))

    def _run_scan():
        box.config(state=tk.NORMAL)
        box.delete("1.0", tk.END)
        cpu = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory()
        disk_c = shutil.disk_usage("C:\\")
        free_c_gb = disk_c.free / (1024 ** 3)
        total_c_gb = disk_c.total / (1024 ** 3)

        disk_d_line = ""
        if os.path.exists("D:\\"):
            disk_d = shutil.disk_usage("D:\\")
            disk_d_line = f"💾 Диск D:\\: свободно {disk_d.free / (1024**3):.1f} ГБ из {disk_d.total / (1024**3):.1f} ГБ\n"

        procs = sorted(psutil.process_iter(["name", "memory_info"]), key=lambda p: (p.info["memory_info"].rss if p.info["memory_info"] else 0), reverse=True)[:5]
        top_str = "\n".join([f"   • {p.info['name']}: {(p.info['memory_info'].rss / (1024**2)):.0f} МБ" for p in procs if p.info.get("memory_info")])

        status = "✅ Система в отличном состоянии!" if (cpu < 85 and ram.percent < 85 and free_c_gb > 10) else "⚠️ Рекомендуется очистка памяти и временных файлов"
        report = (
            f"Статус: {status}\n"
            f"{'='*52}\n"
            f"⚡ Загрузка процессора (CPU): {cpu:.1f}%\n"
            f"🧠 Оперативная память (RAM): {ram.percent:.1f}% ({ram.used / (1024**3):.1f} / {ram.total / (1024**3):.1f} ГБ)\n"
            f"💾 Диск C:\\: свободно {free_c_gb:.1f} ГБ из {total_c_gb:.1f} ГБ\n"
            f"{disk_d_line}"
            f"📊 Активных процессов Windows: {len(psutil.pids())}\n\n"
            f"🔝 Топ-5 процессов по потреблению памяти:\n{top_str}\n"
        )
        box.insert("1.0", report)
        box.config(state=tk.DISABLED)

    def _clean_temp():
        removed = 0
        tdir = tempfile.gettempdir()
        for fn in os.listdir(tdir):
            fp = os.path.join(tdir, fn)
            try:
                if os.path.isfile(fp):
                    os.remove(fp)
                    removed += 1
            except Exception:
                pass
        _run_scan()
        messagebox.showinfo("Очистка завершена", f"Удалено временных файлов: {removed}", parent=win)

    btn_row = tk.Frame(win, bg="#1E1E1E")
    btn_row.pack(fill=tk.X, padx=20, pady=(0, 14))
    tk.Button(btn_row, text="🔄 Повторить проверку", command=_run_scan, bg="#0078D4", fg="#FFFFFF", relief=tk.FLAT, font=("Segoe UI Semibold", 9), padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))
    tk.Button(btn_row, text="🧹 Очистить временные файлы", command=_clean_temp, bg="#2B2B2B", fg="#8BE9FD", relief=tk.FLAT, font=("Segoe UI", 9), padx=12, pady=6, cursor="hand2").pack(side=tk.LEFT)
    tk.Button(btn_row, text="Закрыть", command=win.destroy, bg="#2B2B2B", fg="#CCCCCC", relief=tk.FLAT, font=("Segoe UI", 9), padx=12, pady=6, cursor="hand2").pack(side=tk.RIGHT)

    _run_scan()
    win.lift()
    win.focus_force()
