# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import os
import re
from core.doc_reader import DocumentAndScreenAnalyzer
from core.i18n import get_lang


class PulsarLocalKnowledgeBase:
    """Локальный поиск и ответы по личным документам пользователя (Документы, Рабочий стол, Загрузки)."""

    SUPPORTED_EXTS = (".pdf", ".docx", ".xlsx", ".txt", ".md")

    def __init__(self, brain):
        self.brain = brain
        self.reader = DocumentAndScreenAnalyzer()

    def _get_search_dirs(self) -> list:
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, "Documents"),
            os.path.join(home, "Desktop"),
            os.path.join(home, "Desktop", "Pulsar_Документы"),
            os.path.join(home, "Desktop", "Pulsar_Documents"),
            os.path.join(home, "Downloads"),
        ]
        return [d for d in candidates if os.path.isdir(d)]

    def search_and_answer(self, query: str) -> str:
        is_en = get_lang() == "en"
        clean_q = re.sub(
            r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:найди в моих документах|поищи в документах|что написано в моих файлах|проверь документы|search my documents|find in my files)[:\s]*",
            "",
            query,
            flags=re.I,
        ).strip(" .!?")

        keywords = [w.lower() for w in re.findall(r"[а-яА-Яa-zA-Z0-9]{4,}", clean_q)]
        matched_snippets = []

        for folder in self._get_search_dirs():
            for root, _, files in os.walk(folder):
                if root.count(os.sep) - folder.count(os.sep) > 2:
                    continue
                for fn in files:
                    if not fn.lower().endswith(self.SUPPORTED_EXTS):
                        continue
                    full_p = os.path.join(root, fn)
                    try:
                        if os.path.getsize(full_p) > 8 * 1024 * 1024:
                            continue
                    except Exception:
                        continue

                    score = sum(2 for kw in keywords if kw in fn.lower())
                    extracted = self.reader.extract_text_from_file(full_p, max_chars=4000)
                    low_txt = extracted.lower()
                    score += sum(1 for kw in keywords if kw in low_txt)
                    if score > 0:
                        matched_snippets.append((score, fn, extracted[:2200]))
                if len(matched_snippets) >= 6:
                    break

        if not matched_snippets:
            return (
                "No matching information found in your Documents/Desktop files."
                if is_en
                else "Не удалось найти подходящие документы по этому запросу в папках Документы и Рабочий стол."
            )

        matched_snippets.sort(key=lambda x: x, reverse=True)
        top_ctx = "\n\n".join(snippet for _, _, snippet in matched_snippets[:3])
        prompt = (
            f"Answer the user's question strictly based on the following excerpts from their personal files:\n"
            f"Question: {clean_q}\n\n{top_ctx}"
            if is_en
            else f"Ответь на вопрос пользователя строго по найденным фрагментам из его личных документов (укажи название файла):\n"
            f"Вопрос: {clean_q}\n\n{top_ctx}"
        )
        ans = self.brain.ask_free_chat([{"role": "user", "content": prompt}])
        return ans or top_ctx[:1000]
