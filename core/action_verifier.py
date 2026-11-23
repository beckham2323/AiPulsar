# -*- coding: utf-8 -*-
import os
import re
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from PIL import ImageGrab
from core.url_self_healer import sanitize_and_repair_url


class VisualActionVerifier:
    """Контролёр выполнения: проверяет открытие ссылки/информации, видит ошибки на экране через OCR и сам исправляет их."""

    ERROR_MARKERS = (
        "не удается получить доступ",
        "не удаётся получить доступ",
        "err_name_not_resolved",
        "err_connection",
        "404 not found",
        "страница не найдена",
        "ничего не найдено",
        "xn--",
        "dns_probe",
        "синтаксическая ошибка",
    )

    @staticmethod
    def _extract_query_from_url(url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            for k in ("text", "q", "query", "search_query"):
                if k in qs and qs[k]:
                    return str(qs[k]).strip()
            tail = urllib.parse.unquote_plus(parsed.path.strip("/"))
            return re.sub(r"^(search|video/search|results)", "", tail).strip()
        except Exception:
            return ""

    @classmethod
    def check_url_alive(cls, url: str) -> tuple[bool, str]:
        """Проверяет DNS/HTTP-доступность ссылки и наличие осмысленного ответа до показа пользователю."""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = getattr(resp, "status", 200)
                raw = resp.read(24000).decode("utf-8", errors="ignore")
                low = raw.lower()
                if code >= 400 or any(m in low for m in ("ничего не найдено", "404 not found", "page not found")):
                    return False, f"HTTP {code} / пустой результат"
                # Извлекаем заголовок <title> для анализа
                m_title = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.IGNORECASE | re.DOTALL)
                title = re.sub(r"\s+", " ", m_title.group(1)).strip() if m_title else ""
                return True, title
        except Exception as e:
            return False, str(e)

    @classmethod
    def verify_screen_after_open(cls, original_url: str, fallback_query: str = "", ui_callback=None):
        """Через 2.8 сек после открытия браузера считывает экран через OCR, проверяет успех и при сбое сам чинит."""
        time.sleep(2.8)
        tmp_png = os.path.join(tempfile.gettempdir(), "aipulsar_verify_screen.png")
        try:
            img = ImageGrab.grab()
            img.save(tmp_png, "PNG")
            from rapidocr_onnxruntime import RapidOCR
            ocr = RapidOCR()
            res, _ = ocr(tmp_png)
            if not res:
                return
            screen_text = " ".join(str(item) for item in res if len(item) > 1).lower()

            # Если браузер показал ошибку загрузки, пустой поиск или битый punycode-домен xn--
            if any(err in screen_text for err in cls.ERROR_MARKERS):
                q = fallback_query or cls._extract_query_from_url(original_url) or "популярные фильмы онлайн"
                repaired_url = f"https://ya.ru{urllib.parse.quote_plus(q)}"
                if repaired_url != original_url:
                    if ui_callback:
                        ui_callback(f"👁️ Проверка экрана: заметил, что страница не загрузилась корректно. Сам исправил ссылку и открываю рабочий поиск по запросу «{q}»...")
                    webbrowser.open(repaired_url)
                    return

            # Анализируем открытую информацию и сообщаем пользователю подтверждение
            if ui_callback:
                m_live, page_title = cls.check_url_alive(original_url)
                if m_live and page_title:
                    ui_callback(f"✅ Проверено: страница успешно открыта и загружена («{page_title[:90]}»).")
        except Exception:
            pass
        finally:
            try:
                if os.path.exists(tmp_png):
                    os.remove(tmp_png)
            except Exception:
                pass

    @classmethod
    def open_and_verify(cls, raw_url: str, query_hint: str = "", ui_callback=None) -> str:
        """Единый умный запуск ссылки с предварительным лечением URL, проверкой сети и визуальным контролем экрана."""
        clean_url = sanitize_and_repair_url(raw_url)
        q = query_hint or cls._extract_query_from_url(clean_url)

        ok_net, info = cls.check_url_alive(clean_url)
        if not ok_net and q:
            # Если первичный URL недоступен или пуст — сразу переключаемся на рабочий резервный поиск
            clean_url = f"https://ya.ru{urllib.parse.quote_plus(q)}"
            ok_net, info = cls.check_url_alive(clean_url)

        webbrowser.open(clean_url)
        threading.Thread(
            target=cls.verify_screen_after_open,
            args=(clean_url, q, ui_callback),
            daemon=True,
        ).start()
        return clean_url
