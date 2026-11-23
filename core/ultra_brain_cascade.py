# -*- coding: utf-8 -*-
import concurrent.futures
import json
import re
import urllib.request


class UltraBrainFreeCascade:
    """Сверхмощный бесплатный консилиум моделей (DeepSeek-R1/V3, Qwen 72B/Coder, Llama 3.3 70B) без платных ключей."""

    ENDPOINTS = [
        # 1. Pollinations OpenAI-compatible gateway (бесплатно, без ключа, поддерживает deepseek-r1, qwen-coder, openai-large)
        {
            "name": "DeepSeek-R1-Reasoning",
            "url": "https://pollinations.ai",
            "model": "deepseek-r1",
            "role": "reasoning",
        },
        {
            "name": "Qwen-2.5-Coder-32B",
            "url": "https://pollinations.ai",
            "model": "qwen-coder",
            "role": "code",
        },
        {
            "name": "OpenAI-Large-Flagship",
            "url": "https://pollinations.ai",
            "model": "openai-large",
            "role": "general",
        },
        {
            "name": "Llama-3.3-70B",
            "url": "https://pollinations.ai",
            "model": "llama",
            "role": "general",
        },
    ]

    @staticmethod
    def _clean_thinking_tags(text: str) -> str:
        # Убираем внутренние теги рассуждений <think>...</think> у DeepSeek-R1, оставляя чистый итоговый ответ
        cleaned = re.sub(r"<think>.*?</think>", "", str(text or ""), flags=re.DOTALL | re.IGNORECASE).strip()
        return cleaned or str(text or "").strip()

    def _call_single_node(self, node: dict, messages: list, timeout_sec: float = 14.0) -> str:
        payload = {
            "model": node["model"],
            "messages": messages,
            "temperature": 0.45 if node["role"] in ("reasoning", "code") else 0.65,
            "max_tokens": 2048,
        }
        req = urllib.request.Request(
            node["url"],
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "AiPulsar-UltraBrain/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
            data = json.loads(raw)
            content = data["choices"]["message"]["content"]
            return self._clean_thinking_tags(content)

    def ask_ultra_brain(self, messages: list, mode: str = "auto") -> str:
        """
        mode='code' / 'reasoning' -> приоритет DeepSeek-R1 + Qwen-Coder
        mode='auto' -> параллельная гонка лучших флагманов за самый быстрый и качественный ответ
        """
        if not messages:
            return ""

        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = str(m.get("content", "")).lower()
                break

        is_hard_task = mode in ("code", "reasoning") or any(
            k in last_user for k in ("напиши код", "скрипт", "мод", "исправь", "ошибк", "почини", "архитектур", "анализ", "формул", "python", "powershell")
        )

        ordered = list(self.ENDPOINTS)
        if not is_hard_task:
            # Для обычных вопросов ставим вперёд самые быстрые флагманские модели
            ordered = [n for n in self.ENDPOINTS if n["role"] == "general"] + [n for n in self.ENDPOINTS if n["role"] != "general"]

        # Запускаем первые 2 узла параллельно — берём первый успешный качественный ответ!
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self._call_single_node, node, messages, 15.0) for node in ordered[:2]]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    ans = fut.result()
                    if ans and len(ans.strip()) > 3:
                        return ans.strip()
                except Exception:
                    pass

        # Резервный последовательный проход по оставшимся узлам каскада
        for node in ordered[2:]:
            try:
                ans = self._call_single_node(node, messages, 14.0)
                if ans and len(ans.strip()) > 3:
                    return ans.strip()
            except Exception:
                continue

        return ""
