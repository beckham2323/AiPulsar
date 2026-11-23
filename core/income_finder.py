# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import urllib.parse


class LegalIncomeFinder:
    """Аналитический поиск легальных способов заработка, фриланс-заказов и субсидий."""

    def __init__(self, web_agent):
        self.web = web_agent

    def search_opportunities(self, skills_or_goal: str, region: str = "Владивосток / удалённо") -> str:
        topic = (skills_or_goal or "удалённая работа и фриланс").strip()

        queries = [
            f"фриланс заказы вакансии {topic} {region}",
            f"легальные способы заработка монетизация {topic} 2026",
            f"государственные гранты субсидии самозанятым {region}",
        ]

        collected = []
        for q in queries:
            res = self.web.search_internet(q)
            if res and "Найдено в интернете" in res:
                collected.append(res)

        if not collected:
            return f"По направлению «{topic}» не удалось получить свежую выдачу, проверьте подключение к сети."

        return (
            f"АНАЛИТИЧЕСКАЯ СВОДКА ЛЕГАЛЬНЫХ ВАРИАНТОВ ДОХОДА ({topic}, {region}):\n\n"
            + "\n\n".join(collected)
            + "\n\n[ИНСТРУКЦИЯ ДЛЯ ОКА]: Отбери только надёжные, легальные и реалистичные варианты "
            "(фриланс-проекты, официальная подработка, продажа готовых чертежей/услуг, гранты), "
            "отбрось сомнительные схемы и кратко озвучь пользователю 2–3 лучших варианта с конкретным первым шагом."
        )

