# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import os
import tkinter as tk
from tkinter import filedialog


class DocumentAndScreenAnalyzer:
    """Читает PDF, Word (.docx), Excel (.xlsx), текстовые файлы и содержимое текущего экрана."""

    def pick_file_dialog(self) -> str:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Выберите документ или файл для анализа в Pulsar",
            filetypes=[
                ("Все поддерживаемые", "*.pdf;*.docx;*.xlsx;*.txt;*.py;*.json;*.csv;*.md"),
                ("PDF документы", "*.pdf"),
                ("Word документы", "*.docx"),
                ("Excel таблицы", "*.xlsx"),
                ("Текстовые и код", "*.txt;*.py;*.json;*.csv;*.md"),
            ],
        )
        root.destroy()
        return path or ""

    def extract_text_from_file(self, path: str, max_chars: int = 8500) -> str:
        if not path or not os.path.exists(path):
            return ""
        ext = os.path.splitext(path).lower()
        name = os.path.basename(path)
        text = ""
        try:
            if ext == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(path)
                parts = []
                for idx, page in enumerate(reader.pages[:15]):
                    parts.append(f"--- Страница {idx + 1} ---\n{page.extract_text() or ''}")
                text = "\n".join(parts)
            elif ext == ".docx":
                import docx
                doc = docx.Document(path)
                text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            elif ext == ".xlsx":
                import openpyxl
                wb = openpyxl.load_workbook(path, data_only=True)
                lines = []
                for sheet in wb.sheetnames[:4]:
                    ws = wb[sheet]
                    lines.append(f"=== Лист: {sheet} ===")
                    for row in list(ws.iter_rows(values_only=True))[:60]:
                        vals = [str(v) for v in row if v is not None]
                        if vals:
                            lines.append(" | ".join(vals))
                text = "\n".join(lines)
            else:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
        except Exception as e:
            return f"[Ошибка чтения файла {name}: {e}]"

        clean = text.strip()[:max_chars]
        return f"[СОДЕРЖИМОЕ ФАЙЛА «{name}»]:\n{clean}" if clean else f"[Файл «{name}» пуст или не содержит текста]"

