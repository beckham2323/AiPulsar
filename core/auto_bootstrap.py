# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import json
import os
import subprocess
import threading
import urllib.request


class LocalModelBootstrapper:
    """В фоновом режиме проверяет наличие Ollama и локальной модели на новом ПК."""

    def __init__(self, preferred_models: list):
        self.preferred_models = preferred_models or ["oko-ru", "qwen2.5:3b", "qwen2.5:1.5b"]

    def start_background_check(self):
        threading.Thread(target=self._bootstrap_worker, daemon=True).start()

    def _bootstrap_worker(self):
        try:
            ollama_exe = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
            if not os.path.exists(ollama_exe):
                subprocess.run(
                    ["winget", "install", "-e", "--id", "Ollama.Ollama", "--silent", "--accept-package-agreements", "--accept-source-agreements"],
                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=300,
                )
            if os.path.exists(ollama_exe):
                subprocess.Popen([ollama_exe, "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
                with urllib.request.urlopen("http://" + "127.0.0.1:11434/api/tags", timeout=3) as r:
                    data = json.loads(r.read().decode("utf-8"))
                    installed = [m.get("name", "") for m in data.get("models", [])]
                    if not installed:
                        target_model = next((m for m in self.preferred_models if m != "oko-ru"), "qwen2.5:1.5b")
                        subprocess.run([ollama_exe, "pull", target_model], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=900)
        except Exception:
            pass

