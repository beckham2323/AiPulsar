# -*- coding: utf-8 -*-
import os
import re
import subprocess
import threading
import time
import tkinter as tk
import urllib.parse
import urllib.request
import webbrowser

from core.ui_widgets import attach_tab_popup_to_main


class BuiltinMkvPlayerWindow:
    """Встроенный в AiPulsar плеер для воспроизведения MKV, MP4, AVI, MP3, WAV, FLAC."""

    def __init__(self, parent: tk.Misc, media_source: str, title: str = "Встроенный MKV/Аудио Плеер AiPulsar"):
        self.parent = parent
        self.media_source = media_source
        self.title = title
        self._stop_flag = False
        self._paused = False

    def show(self):
        win = tk.Toplevel(self.parent)
        win.title(f"🎬 {self.title}")
        win.geometry("760x500")
        win.configure(bg="#181818")

        hdr = tk.Frame(win, bg="#202020", height=38)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"🎬 {os.path.basename(self.media_source)}", bg="#202020", fg="#FFFFFF", font=("Segoe UI Semibold", 10)).pack(side=tk.LEFT, padx=14, pady=8)

        canvas = tk.Label(win, bg="#101010", fg="#A6A6A6", text="Загрузка медиапотока...", font=("Segoe UI", 11))
        canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        ctrl = tk.Frame(win, bg="#202020", height=44)
        ctrl.pack(fill=tk.X, padx=12, pady=(0, 10))

        def _toggle_pause():
            self._paused = not self._paused
            btn_pause.config(text="▶ Продолжить" if self._paused else "⏸ Пауза")

        def _close_player():
            self._stop_flag = True
            try:
                win.destroy()
            except Exception:
                pass

        btn_pause = tk.Button(ctrl, text="⏸ Пауза", command=_toggle_pause, bg="#333333", fg="#FFFFFF", relief=tk.FLAT, font=("Segoe UI", 9), padx=14, pady=5, cursor="hand2")
        btn_pause.pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(ctrl, text="⏹ Закрыть плеер", command=_close_player, bg="#0078D4", fg="#FFFFFF", relief=tk.FLAT, font=("Segoe UI Semibold", 9), padx=14, pady=5, cursor="hand2").pack(side=tk.RIGHT)

        attach_tab_popup_to_main(self.parent, win)
        win.protocol("WM_DELETE_WINDOW", _close_player)

        def _play_worker():
            ext = os.path.splitext(self.media_source).lower()
            if ext in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
                canvas.after(0, lambda: canvas.config(text=f"🎵 Воспроизведение аудио:\n{os.path.basename(self.media_source)}", fg="#60CDFF", font=("Segoe UI Semibold", 13)))
                try:
                    ps_aud = (
                        "Add-Type -AssemblyName presentationCore; "
                        "$mp = New-Object System.Windows.Media.MediaPlayer; "
                        f"$mp.Open([Uri]'{self.media_source}'); $mp.Play(); "
                        "Start-Sleep -Seconds 240;"
                    )
                    subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_aud], creationflags=0x08000000)
                except Exception:
                    os.startfile(self.media_source)
                return

            try:
                import cv2
                from PIL import Image, ImageTk
                cap = cv2.VideoCapture(self.media_source)
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                delay = max(0.015, 1.0 / min(fps, 60.0))
                while not self._stop_flag and cap.isOpened():
                    if self._paused:
                        time.sleep(0.08)
                        continue
                    ret, frame = cap.read()
                    if not ret:
                        break
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb).resize((730, 390))
                    tk_img = ImageTk.PhotoImage(image=img)
                    if not self._stop_flag and win.winfo_exists():
                        canvas.after(0, lambda im=tk_img: (canvas.config(image=im, text=""), setattr(canvas, "_cur_img", im)))
                    time.sleep(delay)
                cap.release()
            except Exception:
                try:
                    os.startfile(self.media_source)
                except Exception:
                    pass

        threading.Thread(target=_play_worker, daemon=True).start()


class InternetMediaAndBrowserEngine:
    """Поиск на ПК и во всём интернете + мгновенное воспроизведение музыки, видео и скачивание файлов."""

    def __init__(self):
        self.dl_dir = os.path.join(os.path.expanduser("~"), "Downloads", "AiPulsar_Media")
        os.makedirs(self.dl_dir, exist_ok=True)

    def _find_local_media_match(self, query: str) -> str:
        tokens = [t.lower() for t in re.findall(r"[А-Яа-яЁёA-Za-z0-9]{2,}", query)]
        if not tokens:
            return ""
        search_roots = [
            self.dl_dir,
            os.path.join(os.path.expanduser("~"), "Music"),
            os.path.join(os.path.expanduser("~"), "Videos"),
            os.path.join(os.path.expanduser("~"), "Downloads"),
            os.path.join(os.path.expanduser("~"), "Desktop"),
        ]
        exts = (".mp3", ".mkv", ".mp4", ".avi", ".mov", ".wav", ".flac", ".m4a")
        for root_dir in search_roots:
            if not os.path.isdir(root_dir):
                continue
            for r, _, files in os.walk(root_dir):
                for fn in files:
                    if fn.lower().endswith(exts):
                        fn_low = fn.lower()
                        if all(tok in fn_low for tok in tokens):
                            return os.path.join(r, fn)
        return ""

    def _find_direct_watch_url(self, query: str) -> str:
        enc = urllib.parse.quote_plus(query)
        try:
            req = urllib.request.Request(
                f"https://youtube.com{enc}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            html = urllib.request.urlopen(req, timeout=4.0).read().decode("utf-8", errors="ignore")
            m_vid = re.search(r'"videoId":"([A-Za-z0-9_-]{11})"', html)
            if m_vid:
                return f"https://youtube.com{m_vid.group(1)}&autoplay=1"
        except Exception:
            pass
        return ""

    def handle_media_or_web_request(self, user_text: str, ui_obj=None) -> str:
        q = (user_text or "").strip()
        low = q.lower()

        m_local = re.search(r'([A-Za-z]:\\[^\n"]+\.(?:mkv|mp4|avi|mov|mp3|wav|flac))', q, flags=re.IGNORECASE)
        if m_local and os.path.exists(m_local.group(1)):
            fp = m_local.group(1)
            if ui_obj and getattr(ui_obj, "root", None):
                ui_obj.root.after(0, lambda: BuiltinMkvPlayerWindow(ui_obj.root, fp).show())
            return f"🎬 Запустила «{os.path.basename(fp)}» во встроенном MKV/Аудио-плеере AiPulsar."

        if any(w in low for w in ("скачай", "загрузи", "сохрани картинку", "скачать файл", "скачать песню", "скачать видео")):
            topic = re.sub(r"^(?:скачай|загрузи|найди и скачай)\s+", "", q, flags=re.IGNORECASE).strip()
            enc = urllib.parse.quote_plus(topic)
            if any(w in low for w in ("картинк", "фото", "изображен", "обои")):
                try:
                    img_url = f"https://loremflickr.com{urllib.parse.quote(topic)}"
                    out_img = os.path.join(self.dl_dir, f"image_{int(time.time())}.jpg")
                    urllib.request.urlretrieve(img_url, out_img)
                    os.startfile(self.dl_dir)
                    return f"📥 Скачала изображение по запросу «{topic}» в папку:\n{out_img}"
                except Exception:
                    webbrowser.open(f"https://yandex.ru{enc}")
                    return f"🌐 Открыла поиск изображений «{topic}» в браузере."

            webbrowser.open(f"https://yandex.ru{enc}")
            webbrowser.open(f"https://youtube.com{enc}")
            return f"📥 Открыла источники для загрузки «{topic}» в браузере. Папка загрузок: {self.dl_dir}"

        sys_non_media = ("режим игры", "режим кино", "микрофон", "голос", "звук", "wi-fi", "вайфай", "блютуз", "bluetooth", "компьютер", "пк", "камеру", "помощник", "мод")
        is_play_req = any(w in low for w in ("включи", "поставь", "воспроизведи", "найди песню", "найди видео", "найди клип", "послушать", "посмотреть"))
        is_not_system = not any(s in low for s in sys_non_media)

        if is_play_req and is_not_system:
            clean_query = re.sub(
                r"(?:пожалуйста|найди\s+и|включи|поставь|воспроизведи|найди|мне|песню|музыку|трек|видео|клип|фильм|ролик)",
                " ",
                q,
                flags=re.IGNORECASE,
            )
            clean_query = " ".join(clean_query.split()).strip() or q

            local_hit = self._find_local_media_match(clean_query)
            if local_hit:
                if ui_obj and getattr(ui_obj, "root", None):
                    ui_obj.root.after(0, lambda: BuiltinMkvPlayerWindow(ui_obj.root, local_hit).show())
                return f"🎬 Нашла на вашем ПК файл «{os.path.basename(local_hit)}» и запустила во встроенном MKV/Аудио-плеере!"

            wants_video = any(w in low for w in ("видео", "клип", "фильм", "сериал", "ролик", "посмотреть"))
            search_q = clean_query if wants_video else f"{clean_query} official audio"
            direct_watch = self._find_direct_watch_url(search_q)
            enc = urllib.parse.quote_plus(clean_query)

            if direct_watch:
                webbrowser.open(direct_watch)
                label = "видео" if wants_video else "музыку / аудиопоток"
                return f"🎵 Нашла {label} «{clean_query}» и сразу запустила воспроизведение:\n{direct_watch}"

            webbrowser.open(f"https://yandex.ru{enc}")
            webbrowser.open(f"https://rutube.ru{enc}")
            return f"🎵 Открыла «{clean_query}» на Яндекс Музыке и Rutube для воспроизведения!"

        return ""
