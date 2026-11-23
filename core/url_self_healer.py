# -*- coding: utf-8 -*-
import re
import urllib.parse


def sanitize_and_repair_url(raw_url: str) -> str:
    """Автоматически чинит битые поисковые URL (пробелы в домене, missing /search/, punycode-ошибки)."""
    u = (raw_url or "").strip()
    if not u:
        return "https://ya.ru"

    m = re.match(r"^https?://(?:ya\.ru|yandex\.ru)(?!/)([^\s]+)$", u, flags=re.IGNORECASE)
    if m:
        tail = urllib.parse.unquote_plus(m.group(1)).replace("&lr=75", "").strip()
        return f"https://ya.ru{urllib.parse.quote_plus(tail)}&lr=75"

    if " " in u and not u.startswith("http"):
        return f"https://ya.ru{urllib.parse.quote_plus(u)}&lr=75"

    return u
