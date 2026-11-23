# -*- coding: utf-8 -*-
import ctypes
import os
import threading
import time
from typing import Callable, Optional


class GameCinemaModeManager:
    """Автоматический и голосовой Режим Игры / Кино («Не беспокоить») для AiPulsar."""

    ACTIVATE_PHRASES = (
        "я играю", "режим игры", "игровой режим", "режим кино",
        "смотрю кино", "смотрю фильм", "не беспокой", "не беспокоить", "тихий режим",
    )
    DEACTIVATE_PHRASES = (
        "я вернулся", "выйти из игрового", "обычный режим", "отключи тихий режим", "можно говорить",
    )

    _instance: Optional["GameCinemaModeManager"] = None

    def __init__(self, on_state_change: Optional[Callable[[bool, str], None]] = None):
        self.on_state_change = on_state_change
        self.manual_enabled = False
        self.auto_fullscreen_active = False
        self._running = False
        GameCinemaModeManager._instance = self

    @classmethod
    def get_instance(cls) -> "GameCinemaModeManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_quiet_active(self) -> bool:
        return bool(self.manual_enabled or self.auto_fullscreen_active)

    def _detect_windows_fullscreen(self) -> bool:
        """Определяет полноэкранную игру или фильм через SHQueryUserNotificationState и размеры активного окна."""
        try:
            state = ctypes.c_int(0)
            # QUNS_BUSY (2), QUNS_RUNNING_D3D_FULL_SCREEN (3), QUNS_PRESENTATION_MODE (4)
            hr = ctypes.windll.shell32.SHQueryUserNotificationState(ctypes.byref(state))
            if hr == 0 and state.value in (2, 3, 4):
                return True
        except Exception:
            pass

        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return False
            pid = ctypes.c_ulong(0)
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == os.getpid():
                return False

            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            rect = RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return False
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            win_w = rect.right - rect.left
            win_h = rect.bottom - rect.top
            if sw > 0 and sh > 0 and win_w >= sw and win_h >= sh:
                return True
        except Exception:
            pass
        return False

    def _apply_process_priority(self, quiet: bool):
        """Снижает приоритет AiPulsar в игре/кино, чтобы не забирать FPS и ресурсы."""
        try:
            # BELOW_NORMAL_PRIORITY_CLASS = 0x00004000, NORMAL_PRIORITY_CLASS = 0x00000020
            prio = 0x00004000 if quiet else 0x00000020
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetPriorityClass(handle, prio)
        except Exception:
            pass

    def set_manual(self, enabled: bool) -> str:
        self.manual_enabled = bool(enabled)
        self._apply_process_priority(self.is_quiet_active)
        reason = "Включено вручную / голосом" if self.manual_enabled else "Выключено"
        if self.on_state_change:
            try:
                self.on_state_change(self.is_quiet_active, reason)
            except Exception:
                pass
        return (
            "🎮 Режим Игры / Кино включён. Я перешёл в тихий фоновый режим, снизил нагрузку на ПК и не буду отвлекать вас всплывающими окнами."
            if self.manual_enabled
            else "✅ Режим Игры / Кино выключен. Я снова на связи в обычном режиме!"
        )

    def toggle_manual(self) -> bool:
        self.set_manual(not self.manual_enabled)
        return self.is_quiet_active

    def handle_voice_command(self, cmd_text: str) -> Optional[str]:
        low = (cmd_text or "").strip().lower()
        if not low:
            return None
        if any(p in low for p in self.ACTIVATE_PHRASES):
            return self.set_manual(True)
        if any(p in low for p in self.DEACTIVATE_PHRASES):
            return self.set_manual(False)
        return None

    def start_auto_monitor(self, interval_sec: int = 5):
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._monitor_loop, args=(interval_sec,), daemon=True).start()

    def _monitor_loop(self, interval_sec: int):
        while self._running:
            try:
                prev_quiet = self.is_quiet_active
                self.auto_fullscreen_active = self._detect_windows_fullscreen()
                cur_quiet = self.is_quiet_active
                if cur_quiet != prev_quiet:
                    self._apply_process_priority(cur_quiet)
                    if self.on_state_change:
                        reason = "Автоопределение: игра или фильм во весь экран" if cur_quiet else "Выход из полноэкранного режима"
                        self.on_state_change(cur_quiet, reason)
            except Exception:
                pass
            time.sleep(interval_sec)
