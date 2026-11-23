# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import json
import os
import subprocess


class HardwareAutoProfiler:
    """Автоматически определяет GPU, VRAM, RAM и CPU любого компьютера и подстраивает параметры программы."""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.profile_path = os.path.join(self.models_dir, "hardware_profile.json")
        self.config = self.detect_and_configure()

    def _get_ram_gb(self) -> float:
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return round(stat.ullTotalPhys / (1024 ** 3), 1)
        except Exception:
            return 8.0

    def _get_gpu_info(self) -> tuple:
        """Возвращает (название_видеокарты, объём_VRAM_в_ГБ)."""
        # 1. Пробуем nvidia-smi для точного определения VRAM видеокарт NVIDIA
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=3,
            )
            line = next(iter((res.stdout or "").splitlines()), "").strip()
            if line and "," in line:
                parts = [p.strip() for p in line.split(",")]
                name = next(iter(parts))
                vram_mb = float(parts.pop())
                return name, round(vram_mb / 1024.0, 1)
        except Exception:
            pass

        # 2. Резерв через PowerShell CIM (работает на AMD, Intel и встроенной графике)
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
                 "Get-CimInstance Win32_VideoController | Select-Object -First 1 Name, AdapterRAM | ConvertTo-Json"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=4,
            )
            data = json.loads(res.stdout or "{}")
            name = str(data.get("Name", "Встроенная графика"))
            vram_bytes = float(data.get("AdapterRAM") or 0)
            return name, round(vram_bytes / (1024 ** 3), 1)
        except Exception:
            return "Стандартный видеоадаптер", 0.0

    def detect_and_configure(self) -> dict:
        ram_gb = self._get_ram_gb()
        cpu_cores = os.cpu_count() or 4
        gpu_name, vram_gb = self._get_gpu_info()
        is_nvidia = "nvidia" in gpu_name.lower() or "rtx" in gpu_name.lower() or "gtx" in gpu_name.lower()

        if is_nvidia and vram_gb >= 6.0 and ram_gb >= 14.0:
            tier = "ULTRA"
            eye_res = 520
            ui_fps_ms = 50
            preferred_models = ["oko-ru", "qwen2.5:7b"]
            num_ctx = 4096
            num_gpu = 99
        elif (vram_gb >= 3.0 or is_nvidia) and ram_gb >= 8.0:
            tier = "BALANCED"
            eye_res = 360
            ui_fps_ms = 65
            preferred_models = ["oko-ru", "qwen2.5:3b", "qwen2.5:1.5b"]
            num_ctx = 2048
            num_gpu = 20 if is_nvidia else 0
        else:
            tier = "LITE"
            eye_res = 240
            ui_fps_ms = 85
            preferred_models = ["qwen2.5:1.5b", "qwen2.5:3b", "oko-ru"]
            num_ctx = 1536
            num_gpu = 0

        cfg = {
            "tier": tier,
            "gpu_name": gpu_name,
            "vram_gb": vram_gb,
            "ram_gb": ram_gb,
            "cpu_cores": cpu_cores,
            "eye_res": eye_res,
            "ui_fps_ms": ui_fps_ms,
            "preferred_models": preferred_models,
            "num_ctx": num_ctx,
            "num_gpu": num_gpu,
        }
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return cfg

    def get_summary_line(self) -> str:
        c = self.config
        return f"Профиль железа [{c['tier']}]: {c['gpu_name']} ({c['vram_gb']} ГБ VRAM), ОЗУ {c['ram_gb']} ГБ, CPU {c['cpu_cores']} ядер."

