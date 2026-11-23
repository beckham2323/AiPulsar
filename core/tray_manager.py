# -*- coding: utf-8 -*-
import os
import threading
from PIL import Image
import pystray


class PulsarTrayManager:
    def __init__(self, icon_path: str = "aipulsar.ico", on_show_cb=None, on_quit_cb=None):
        self.icon_path = icon_path
        self.on_show_cb = on_show_cb
        self.on_quit_cb = on_quit_cb
        self._tray = None

    def _load_transparent_image(self) -> Image.Image:
        for candidate in ("aipulsar_icon.png", self.icon_path, "_internal/aipulsar_icon.png"):
            if os.path.exists(candidate):
                try:
                    return Image.open(candidate).convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
                except Exception:
                    pass
        return Image.new("RGBA", (64, 64), (124, 77, 255, 255))

    def start(self):
        def _run():
            img = self._load_transparent_image()
            menu = pystray.Menu(
                pystray.MenuItem("Открыть AiPulsar", lambda: self.on_show_cb() if self.on_show_cb else None, default=True),
                pystray.MenuItem("Выход", lambda: self.on_quit_cb() if self.on_quit_cb else None),
            )
            self._tray = pystray.Icon("AiPulsar", img, "AiPulsar — VESKOR", menu)
            self._tray.run()

        threading.Thread(target=_run, daemon=True).start()

    def stop(self):
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
