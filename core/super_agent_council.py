# -*- coding: utf-8 -*-
import ast
import re
from core.ultra_brain_cascade import UltraBrainFreeCascade


class SuperAgentCouncil:
    """Многоагентный консилиум второго порядка: Планировщик -> Исполнитель -> Критик + Песочница проверки."""

    HARD_TRIGGERS = (
        "подумай",
        "консилиум",
        "глубоко",
        "разработай",
        "спроектируй",
        "напиши код",
        "напиши скрипт",
        "напиши программу",
        "создай модуль",
        "проанализируй",
        "сравни подробно",
        "пошаговый план",
        "исправь ошибку",
        "почини",
        "оптимизируй",
        "бизнес-план",
        "архитектур",
    )

    def __init__(self):
        self.brain = UltraBrainFreeCascade()

    @classmethod
    def is_complex_query(cls, user_text: str) -> bool:
        low = (user_text or "").strip().lower()
        if len(low) > 220:
            return True
        return any(t in low for t in cls.HARD_TRIGGERS)

    @staticmethod
    def _verify_python_blocks(text: str) -> list:
        """Проверяет все блоки ```python ... ``` на синтаксические ошибки через AST."""
        errors = []
        blocks = re.findall(r"```python\s*(.*?)```", text or "", flags=re.DOTALL | re.IGNORECASE)
        for idx, code in enumerate(blocks, 1):
            try:
                ast.parse(code.strip())
            except SyntaxError as e:
                errors.append(f"Блок Python #{idx}: синтаксическая ошибка на строке {e.lineno}: {e.msg}")
        return errors

    def solve_with_council(self, user_goal: str, memory_context: str = "") -> str:
        """Запускает 3-агентный цикл: Планировщик -> Исполнитель -> Критик (с доработкой при ошибках)."""
        goal = (user_goal or "").strip()
        if not goal:
            return ""

        ctx_note = f"\nКонтекст из памяти пользователя:\n{memory_context}\n" if memory_context else ""

        # Этап 1: Агент-Планировщик (DeepSeek-R1 Reasoning)
        planner_msgs = [
            {
                "role": "system",
                "content": (
                    "Ты — Агент-Планировщик (Главный Архитектор). Твоя задача: не писать длинный финальный ответ, "
                    "а составить краткий, предельно точный инженерный план решения задачи пользователя (3–6 пунктов), "
                    "указать возможные подводные камни, краевые случаи и критерии проверки качества."
                ),
            },
            {"role": "user", "content": f"Задача пользователя: {goal}{ctx_note}"},
        ]
        plan = self.brain.ask_ultra_brain(planner_msgs, mode="reasoning")

        # Этап 2: Агент-Исполнитель (Qwen-Coder / Flagship)
        exec_msgs = [
            {
                "role": "system",
                "content": (
                    "Ты — Агент-Исполнитель высшего уровня (AiPulsar SuperCouncil). "
                    "Опираясь на план Архитектора, дай исчерпывающий, структурированный и практически применимый ответ на русском языке. "
                    "Если нужен код — пиши его полностью, без заглушек и пропусков."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Исходная задача: {goal}{ctx_note}\n\n"
                    f"План от Агента-Планировщика:\n{plan or 'Выполни задачу максимально точно и полно.'}"
                ),
            },
        ]
        draft = self.brain.ask_ultra_brain(exec_msgs, mode="code")
        if not draft:
            return ""

        # Этап 3: Агент-Критик + Автоматическая проверка синтаксиса кода
        syntax_errors = self._verify_python_blocks(draft)
        critic_msgs = [
            {
                "role": "system",
                "content": (
                    "Ты — строгий Агент-Критик (Инженер контроля качества). Проверь черновик ответа Исполнителя:\n"
                    "1. Все ли части вопроса пользователя решены полностью?\n"
                    "2. Нет ли логических ошибок, устаревших команд или небезопасных действий?\n"
                    "Если ответ отличный и замечаний нет — ответь строго одним словом: APPROVED\n"
                    "Если есть недочёты — перечисли их кратко по пунктам."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Задача: {goal}\n"
                    f"Ошибки автоматического парсера кода: {syntax_errors or 'Нет'}\n\n"
                    f"Черновик ответа:\n{draft}"
                ),
            },
        ]
        verdict = self.brain.ask_ultra_brain(critic_msgs, mode="reasoning")

        # Если Критик или AST-парсер нашли недочёты — Исполнитель делает финальную полировку
        if syntax_errors or (verdict and "APPROVED" not in verdict.upper()):
            refine_msgs = [
                {
                    "role": "system",
                    "content": (
                        "Ты — Агент-Исполнитель. Исправь все замечания Критика и ошибки кода в своём черновике "
                        "и выдай только финальный, безупречный ответ для пользователя на русском языке (без служебных комментариев)."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Задача: {goal}\n\n"
                        f"Предыдущий черновик:\n{draft}\n\n"
                        f"Замечания Критика: {verdict}\n"
                        f"Ошибки синтаксиса: {syntax_errors}"
                    ),
                },
            ]
            refined = self.brain.ask_ultra_brain(refine_msgs, mode="code")
            if refined and len(refined.strip()) > 10:
                return refined.strip()

        return draft.strip()
