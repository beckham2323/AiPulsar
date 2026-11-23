# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import ctypes
import datetime
import os
import re
import time
import urllib.parse
import urllib.request
import zipfile
import pyautogui
import pyperclip
from PIL import Image


class PulsarSmartTools:
    """Мгновенный переводчик, OCR-распознавание картинок, конвертация в PDF/ZIP и смена обоев Windows."""

    def __init__(self, brain, vision):
        self.brain = brain
        self.vision = vision

    def translate_selection_or_text(self, command_text: str) -> str:
        low = command_text.lower().strip()

        # 1. Обратный перевод: "как будет по-английски / по-китайски: фраза"
        m_to = re.search(r"как\s+будет\s+(по-[а-яё]+|на\s+[а-яё]+)[:\s]+(.+)$", low)
        if m_to:
            lang = m_to.group(1).strip()
            phrase = command_text[m_to.start(2):].strip(" .!?")
            prompt = f"Переведи следующую фразу {lang}. Выдай ТОЛЬКО сам перевод без пояснений:\n{phrase}"
            res = self.brain.ask_free_chat([{"role": "user", "content": prompt}])
            clean_res = (res or "").strip()
            if clean_res:
                pyperclip.copy(clean_res)
                return f"Перевод ({lang}): {clean_res}\n(Скопировано в буфер обмена — можно вставить через Ctrl+V)."

        # 2. Прямой перевод выделенного текста или буфера обмена на русский
        inline_text = re.sub(r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:переведи|перевод)(?:\s+текст|\s+это|\s+выделенное)?[:\s]*", "", command_text, flags=re.I).strip()
        target_text = inline_text
        if not target_text:
            old_clip = pyperclip.paste()
            try:
                pyautogui.hotkey("ctrl", "c")
                time.sleep(0.18)
            except Exception:
                pass
            target_text = (pyperclip.paste() or old_clip or "").strip()

        if not target_text:
            return "Выдели текст на экране или скопируй его, а затем скажи «Переведи»."

        prompt = f"Переведи этот текст на чистый, естественный русский язык. Выдай только точный перевод:\n\n{target_text[:3500]}"
        translated = self.brain.ask_free_chat([{"role": "user", "content": prompt}])
        return f"Перевод:\n{translated}"

    def ocr_image_or_screen(self, image_path: str = "") -> str:
        target = (image_path or "").strip(" \"'«»")
        if not target or not os.path.exists(target):
            # Берём путь из буфера обмена, если скопирован файл картинки, иначе читаем текущий экран
            clip = (pyperclip.paste() or "").strip(" \"'")
            if clip and os.path.exists(clip) and clip.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                target = clip

        if target and os.path.exists(target) and self.vision and getattr(self.vision, "ocr", None):
            try:
                res, _ = self.vision.ocr(target)
                lines = [item for item in (res or []) if len(item) >= 2]
                extracted = "\n".join(lines).strip()
                if extracted:
                    pyperclip.copy(extracted)
                    return f"Извлечённый текст с картинки (скопирован в буфер обмена):\n{extracted[:2500]}"
            except Exception as e:
                return f"Не удалось распознать текст с картинки: {e}"

        scr_txt = self.vision.read_screen_summary() if self.vision else ""
        if scr_txt:
            pyperclip.copy(scr_txt)
            return f"Распознанный текст с экрана (скопирован в буфер обмена):\n{scr_txt[:2500]}"
        return "Не удалось обнаружить текст на изображении."

    def convert_to_pdf_or_zip(self, command_text: str) -> str:
        low = command_text.lower()
        clip_path = (pyperclip.paste() or "").strip(" \"'")
        m_path = re.search(r"([A-Za-z]:\\[^\n\"']+)", command_text)
        src = m_path.group(1).strip() if m_path else (clip_path if os.path.exists(clip_path) else "")

        if not src or not os.path.exists(src):
            return "Скопируй файл или папку (Ctrl+C) либо укажи путь, чтобы я сделал PDF или архив."

        base_no_ext = os.path.splitext(src)
        if "архив" in low or "zip" in low or "сожми" in low or os.path.isdir(src):
            zip_out = f"{base_no_ext}.zip"
            with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
                if os.path.isdir(src):
                    for root, _, files in os.walk(src):
                        for fn in files:
                            full = os.path.join(root, fn)
                            zf.write(full, os.path.relpath(full, os.path.dirname(src)))
                else:
                    zf.write(src, os.path.basename(src))
            return f"Готово! Создал архив: {zip_out}"

        # Конвертация изображения или текстового файла в PDF
        pdf_out = f"{base_no_ext}.pdf"
        ext = os.path.splitext(src).lower()
        if ext in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
            img = Image.open(src).convert("RGB")
            img.save(pdf_out, "PDF", resolution=150.0)
            return f"Готово! Сконвертировал картинку в PDF: {pdf_out}"

        with open(src, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        from PIL import ImageDraw
        page = Image.new("RGB", (1240, 1754), (255, 255, 255))
        draw = ImageDraw.Draw(page)
        y = 60
        for line in txt.splitlines()[:75]:
            draw.text((60, y), line[:110], fill=(0, 0, 0))
            y += 22
        page.save(pdf_out, "PDF", resolution=150.0)
        return f"Готово! Создал PDF-документ: {pdf_out}"

    def set_desktop_wallpaper(self, topic: str) -> str:
        q = re.sub(r"^(?:pulsar|пульсар|pulsar)?[,\s]*(?:поставь|установи|смени|сделай)\s+(?:на\s+)?обои(?:\s+рабочего\s+стола)?[:\s]*", "", topic, flags=re.I).strip(" .!?")
        if not q:
            q = "deep space nebula 4k"

        save_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Pulsar_Wallpapers")
        os.makedirs(save_dir, exist_ok=True)
        out_jpg = os.path.join(save_dir, f"wallpaper_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")

        try:
            encoded = urllib.parse.quote(f"{q} wallpaper")
            search_url = f"https://bing.com{encoded}&qft=+filterui:imagesize-wallpaper"
            req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                html = r.read().decode("utf-8", errors="ignore")
            urls = re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|jpeg|png))&quot;', html, flags=re.I)
            downloaded = False
            for img_url in urls[:6]:
                try:
                    ireq = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(ireq, timeout=6) as ir:
                        data = ir.read()
                        if len(data) > 45000:
                            with open(out_jpg, "wb") as f:
                                f.write(data)
                            downloaded = True
                            break
                except Exception:
                    continue

            if not downloaded:
                return f"Не удалось скачать обои по теме «{q}» — проверьте подключение к интернету."

            ctypes.windll.user32.SystemParametersInfoW(20, 0, out_jpg, 3)
            return f"Установил новые обои рабочего стола по теме «{q}»."
        except Exception as e:
            return f"Ошибка смены обоев: {e}"

