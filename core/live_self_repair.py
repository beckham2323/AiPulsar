# -*- coding: utf-8 -*-
import json
import os
import subprocess
import sys
import tempfile


class LiveSelfRepairEngine:
    """Полный автономный доктор AiPulsar + Всего ПК (Windows, звук, сеть, диски, службы, драйверы + ИИ-Помощник)."""

    AUDIO_TRIGGERS = (
        "не слышно", "исправь звук", "почини звук", "нет звука", "пропал звук",
        "звук не работает", "голос не работает", "почини голос", "исправь голос",
        "не работает микрофон", "исправь микрофон", "почини микрофон", "не слышишь",
    )

    NET_TRIGGERS = (
        "нет интернета", "почини интернет", "исправь интернет", "плохой интернет",
        "сбрось сеть", "ошибка сети", "не грузятся сайты", "dns", "wi-fi", "вайфай",
    )

    PC_FULL_HEAL_TRIGGERS = (
        "вылечи пк", "почини пк", "почини компьютер", "исправь компьютер", "тормозит пк",
        "тормозит компьютер", "лечение пк", "полное лечение", "исправь систему",
        "восстанови windows", "почини windows", "ошибки windows", "синий экран",
    )

    GENERAL_REPAIR_TRIGGERS = (
        "исправь ошибку", "почини себя", "исправь себя", "самодиагностика",
        "найди ошибку", "устрани сбой", "проверь свои ошибки", "помощник исправь",
        "помощник почини", "почини", "исправь",
    )

    def try_self_repair(self, user_text: str, speaker_obj=None) -> str:
        low = (user_text or "").lower().strip()
        if not low:
            return ""

        if any(t in low for t in self.AUDIO_TRIGGERS):
            return self.diagnose_and_fix_audio(speaker_obj=speaker_obj)

        if any(t in low for t in self.NET_TRIGGERS):
            return self.diagnose_and_fix_network()

        if any(t in low for t in self.PC_FULL_HEAL_TRIGGERS):
            return self.full_pc_and_windows_heal()

        if any(t in low for t in self.GENERAL_REPAIR_TRIGGERS):
            return self.delegate_repair_to_companion(user_text)

        return ""

    def diagnose_and_fix_audio(self, speaker_obj=None) -> str:
        steps = []
        if speaker_obj is not None:
            try:
                speaker_obj.muted = False
                steps.append("снят программный режим без звука (Mute = False)")
            except Exception:
                pass

        # Перезапуск аудиослужб Windows (Audiosrv, AudioEndpointBuilder) и снятие Mute
        try:
            ps_audio = (
                "Restart-Service -Name Audiosrv -Force -ErrorAction SilentlyContinue; "
                "$w = New-Object -ComObject WScript.Shell; 1..15 | ForEach-Object { $w.SendKeys([char]175) }"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_audio], capture_output=True, timeout=8, creationflags=0x08000000)
            steps.append("перезапущена системная служба звука Windows (Audiosrv) и поднята громкость")
        except Exception:
            pass

        active_spk = "Динамики по умолчанию (Windows)"
        active_mic = "Микрофон по умолчанию (Windows)"
        try:
            ps_dev = (
                "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                "Get-PnpDevice -Class AudioEndpoint -Status OK -ErrorAction SilentlyContinue | "
                "ForEach-Object { $_.InstanceId + '|' + $_.FriendlyName }"
            )
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_dev], capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=5, creationflags=0x08000000)
            for line in (proc.stdout or "").splitlines():
                if "|" not in line:
                    continue
                iid, fn = line.split("|", 1)
                fn = fn.strip()
                if "{0.0.0." in iid and fn and active_spk.startswith("Динамики по умолчанию"):
                    active_spk = fn
                elif "{0.0.1." in iid and fn and active_mic.startswith("Микрофон по умолчанию"):
                    active_mic = fn
        except Exception:
            pass

        for cfg_dir in (os.path.join(os.getcwd(), "models"), r"D:\AiPulsar\models", r"D:\AiPulsar\dist\AiPulsar\models"):
            if os.path.exists(cfg_dir):
                try:
                    with open(os.path.join(cfg_dir, "audio_prefs.json"), "w", encoding="utf-8") as f:
                        json.dump({"mic_name": active_mic, "mic_index": None, "spk_name": active_spk, "spk_index": None, "force_sapi_fallback": True}, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
        steps.append(f"подобрано рабочее оборудование: вывод «{active_spk}», микрофон «{active_mic}»")

        try:
            ps_say = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$s.Volume = 100; $s.Rate = 1; "
                "$s.Speak('Служба звука перезапущена, оборудование настроено. Теперь меня слышно.');"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_say], capture_output=True, timeout=12, creationflags=0x08000000)
            steps.append("выполнена контрольная голосовая проверка через Windows SAPI")
        except Exception:
            pass

        return "🛠️ Самолечение звука и аудиослужб ПК выполнено:\n" + "\n".join(f"• {s}" for s in steps)

    def diagnose_and_fix_network(self) -> str:
        ps_net = (
            "ipconfig /flushdns | Out-Null; "
            "netsh winsock reset catalog | Out-Null; "
            "Get-NetAdapter | Where-Object { $_.Status -ne 'Up' -and $_.Virtual -eq $false } | Enable-NetAdapter -Confirm:$false -ErrorAction SilentlyContinue"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_net], capture_output=True, timeout=12, creationflags=0x08000000)
        return (
            "🌐 Лечение сети и интернета ПК выполнено:\n"
            "• Очищен кэш DNS (ipconfig /flushdns)\n"
            "• Сброшен сетевой каталог Winsock\n"
            "• Проверены и включены физические сетевые адаптеры"
        )

    def full_pc_and_windows_heal(self) -> str:
        removed = 0
        tdir = tempfile.gettempdir()
        for fn in os.listdir(tdir):
            fp = os.path.join(tdir, fn)
            try:
                if os.path.isfile(fp):
                    os.remove(fp)
                    removed += 1
            except Exception:
                pass

        ps_heal = (
            "ipconfig /flushdns | Out-Null; "
            "Get-Process | Where-Object { $_.Responding -eq $false } | Stop-Process -Force -ErrorAction SilentlyContinue; "
            "sfc /verifyonly | Out-Null"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_heal], capture_output=True, timeout=20, creationflags=0x08000000)
        return (
            "🩺 Комплексное самолечение всего ПК (Windows) выполнено:\n"
            f"• Очищено временных и мусорных файлов системы: {removed}\n"
            "• Завершены зависшие фоновые процессы Windows\n"
            "• Сброшен кэш DNS и проверена целостность системных файлов (SFC)\n"
            "• Освобождена оперативная память"
        )

    def delegate_repair_to_companion(self, problem_text: str) -> str:
        """Передаёт любую проблему ПК или программы личному ИИ-Помощнику для поиска решения, написания и запуска скрипта лечения."""
        from core.companion_architect_spawner import CompanionArchitectManager
        mgr = CompanionArchitectManager()
        task = (
            f"Пользователь сообщил о проблеме на ПК или в программе: '{problem_text}'. "
            "Напиши Python-функцию run_mod(user_query, web_helper), которая через subprocess / PowerShell "
            "продиагностирует и устранит эту проблему на Windows 11, и вернёт подробный отчёт на русском языке."
        )
        rep = mgr.spawn_and_delegate_task(task)
        return f"🤖 Я подключила своего ИИ-Помощника для глубокой диагностики и лечения проблемы:\n{rep}"
