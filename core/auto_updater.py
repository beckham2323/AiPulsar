# -*- coding: utf-8 -*-
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request


class GitHubAutoUpdater:
    """Автоматическая проверка, загрузка и тихая установка обновлений из GitHub Releases (beckham2323/AiPulsar)."""

    CURRENT_VERSION = "1.0.0"
    GITHUB_REPO = "beckham2323/AiPulsar"
    API_LATEST_URL = f"https://github.com{GITHUB_REPO}/releases/latest"

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.cfg_path = os.path.join(self.models_dir, "update_config.json")
        self._init_cfg()

    def _init_cfg(self):
        if not os.path.exists(self.cfg_path):
            try:
                with open(self.cfg_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "auto_update_enabled": True,
                        "repo": self.GITHUB_REPO,
                        "current_version": self.CURRENT_VERSION,
                    }, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    @staticmethod
    def _parse_ver(v_str: str) -> tuple:
        nums = [int(x) for x in re.findall(r"\d+", str(v_str or "0"))]
        while len(nums) < 3:
            nums.append(0)
        return tuple(nums[:3])

    def check_and_install_update(self, ui_obj=None, silent_if_none: bool = True) -> str:
        try:
            req = urllib.request.Request(
                self.API_LATEST_URL,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "AiPulsar-Updater/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except Exception as e:
            if not silent_if_none:
                return f"🔄 Не удалось связаться с сервером обновлений GitHub ({self.GITHUB_REPO}): {e}"
            return ""

        tag = str(data.get("tag_name") or "").strip()
        if not tag:
            return "" if silent_if_none else f"🔄 На GitHub ({self.GITHUB_REPO}) пока не опубликовано ни одного релиза."

        remote_ver = self._parse_ver(tag)
        local_ver = self._parse_ver(self.CURRENT_VERSION)

        if remote_ver <= local_ver:
            if not silent_if_none:
                return f"✅ У вас установлена самая актуальная версия AiPulsar ({self.CURRENT_VERSION})."
            return ""

        # Ищем файл Setup_AiPulsar.exe во вложениях релиза (assets)
        setup_url = ""
        for asset in data.get("assets", []):
            aname = str(asset.get("name") or "")
            if aname.lower().endswith(".exe") and "setup" in aname.lower():
                setup_url = str(asset.get("browser_download_url") or "")
                break

        if not setup_url:
            html_url = str(data.get("html_url") or f"https://github.com/{self.GITHUB_REPO}/releases")
            msg_manual = f"🚀 Вышла новая версия AiPulsar {tag}! Скачать обновление можно на странице релиза:\n{html_url}"
            if ui_obj:
                ui_obj.append_log("AiPulsar", msg_manual)
            return msg_manual

        notes = str(data.get("body") or "").strip()[:300]
        if ui_obj:
            ui_obj.append_log(
                "AiPulsar",
                f"🚀 Обнаружено новое обновление AiPulsar {tag}!\n{notes}\n⏳ Начинаю автоматическую загрузку и установку..."
            )

        try:
            tmp_setup = os.path.join(tempfile.gettempdir(), f"Setup_AiPulsar_{tag}.exe")
            urllib.request.urlretrieve(setup_url, tmp_setup)
            if os.path.exists(tmp_setup) and os.path.getsize(tmp_setup) > 1024 * 1024:
                if ui_obj:
                    ui_obj.append_log("AiPulsar", "✅ Обновление загружено! Перезапускаю программу для установки новой версии...")
                time.sleep(1.5)
                subprocess.Popen(
                    [tmp_setup, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                    creationflags=0x00000008,
                    close_fds=True,
                )
                os._exit(0)
        except Exception as dl_err:
            err_msg = f"⚠️ Ошибка при загрузке обновления {tag}: {dl_err}"
            if ui_obj:
                ui_obj.append_log("AiPulsar", err_msg)
            return err_msg

        return ""

    def start_background_update_checker(self, ui_holder: dict):
        def _bg_worker():
            time.sleep(12)
            while True:
                try:
                    self.check_and_install_update(ui_obj=ui_holder.get("ui"), silent_if_none=True)
                except Exception:
                    pass
                time.sleep(21600)  # Проверка каждые 6 часов

        threading.Thread(target=_bg_worker, daemon=True).start()


class PulsarAutoUpdater(GitHubAutoUpdater):
    """Совместимый адаптер для вызова из main.py (строка 83)."""

    def __init__(self, current_version: str = "1.0.0", models_dir: str = "models", **kwargs):
        super().__init__(models_dir=models_dir)
        self.CURRENT_VERSION = str(current_version or "1.0.0")

    def check_updates_async(self, callback=None):
        def _run():
            res = self.check_and_install_update(silent_if_none=True)
            if callback and res:
                try:
                    callback(res)
                except Exception:
                    pass
        import threading
        threading.Thread(target=_run, daemon=True).start()
