# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import html
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


class WebInternetAgent:
    """Доступ в интернет: поисковые системы (Яндекс / DuckDuckGo), Яндекс Новости и чтение страниц."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "ru-RU,ru;q=0.9",
    }

    NEWS_FEEDS = {
        "главные": "https://yandex.ru",
        "владивосток": "https://yandex.ru",
        "политика": "https://yandex.ru",
        "экономика": "https://yandex.ru",
        "технологии": "https://yandex.ru",
        "спорт": "https://yandex.ru",
    }

    def _clean_html(self, raw_html: str) -> str:
        no_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw_html, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", no_scripts)
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    def get_yandex_news(self, topic: str = "главные", limit: int = 7) -> str:
        """Получает свежие заголовки и сводки из Яндекс Новостей."""
        low = (topic or "главные").lower()
        feed_url = self.NEWS_FEEDS["главные"]
        for key, url in self.NEWS_FEEDS.items():
            if key in low:
                feed_url = url
                break

        items_out = []
        try:
            req = urllib.request.Request(feed_url, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item")[:limit]:
                title = self._clean_html(item.findtext("title") or "")
                desc = self._clean_html(item.findtext("description") or "")
                if title:
                    items_out.append(f"• {title}" + (f" — {desc[:160]}" if desc else ""))
        except Exception:
            pass

        if not items_out:
            return self.search_internet(f"Яндекс новости сегодня {topic} Владивосток")

        return f"Свежие Яндекс Новости ({topic}):\n" + "\n".join(items_out)

    def search_internet(self, query: str) -> str:
        q = (query or "").strip()
        if not q:
            return "Пустой поисковый запрос."
        results = []

        # 1. Поисковая система Яндекс (регион lr=75 — Владивосток)
        try:
            y_url = "https://yandex.ru" + f"/search/?text={urllib.parse.quote(q)}&lr=75"
            req = urllib.request.Request(y_url, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                page = resp.read().decode("utf-8", errors="ignore")
                blocks = re.findall(r'class="[^"]*(?:OrganicText|ExtendedText)[^"]*"[^>]*>(.*?)</div>', page, flags=re.S)
                for b in blocks[:5]:
                    clean = self._clean_html(b)
                    if len(clean) > 25 and clean not in results:
                        results.append(clean[:320])
        except Exception:
            pass

        # 2. Резервная поисковая система DuckDuckGo
        if not results:
            try:
                ddg_url = "https://duckduckgo.com" + f"/html/?q={urllib.parse.quote(q)}"
                req = urllib.request.Request(ddg_url, headers=self.HEADERS)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    page = resp.read().decode("utf-8", errors="ignore")
                    blocks = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', page, flags=re.S)
                    for b in blocks[:5]:
                        clean = self._clean_html(b)
                        if len(clean) > 25 and clean not in results:
                            results.append(clean[:320])
            except Exception:
                pass

        if results:
            return f"Результаты поиска в интернете по запросу «{q}»:\n" + "\n".join(f"- {r}" for r in results)
        return f"По запросу «{q}» ничего не найдено."

    def read_webpage(self, url: str) -> str:
        target = (url or "").strip()
        if not target.startswith("http"):
            target = "https://" + target
        try:
            req = urllib.request.Request(target, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
                clean = self._clean_html(raw)
                return f"Содержимое страницы {target}:\n{clean[:3500]}"
        except Exception as e:
            return f"Не удалось прочитать страницу {target}: {e}"

    def download_file(self, url: str, filename: str = "") -> str:
        target = (url or "").strip()
        if not target:
            return "Не указана ссылка для скачивания."
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads, exist_ok=True)
        fname = filename.strip() or os.path.basename(urllib.parse.urlparse(target).path) or "downloaded_file"
        save_path = os.path.join(downloads, fname)
        try:
            req = urllib.request.Request(target, headers=self.HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp, open(save_path, "wb") as out:
                out.write(resp.read())
            return f"Файл успешно скачан в Загрузки: {save_path}"
        except Exception as e:
            return f"Ошибка скачивания файла: {e}"

