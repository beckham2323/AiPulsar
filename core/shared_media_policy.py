# -*- coding: utf-8 -*-
"""Политика немонопольного (совместного) доступа к микрофону, звуку и камере в AiPulsar."""


def get_shared_input_device_index(pa_instance):
    """Возвращает индекс устройства ввода через общий (немонопольный) MME/DirectSound хост-API."""
    try:
        default_info = pa_instance.get_default_input_device_info()
        target_name = str(default_info.get("name", ""))[:24].lower()
        for i in range(pa_instance.get_host_api_count()):
            api = pa_instance.get_host_api_info_by_index(i)
            api_name = str(api.get("name", "")).upper()
            if "MME" in api_name or "DIRECTSOUND" in api_name:
                for d_idx in range(pa_instance.get_device_count()):
                    dev = pa_instance.get_device_info_by_index(d_idx)
                    if dev.get("hostApi") == i and int(dev.get("maxInputChannels", 0)) > 0:
                        if not target_name or target_name in str(dev.get("name", "")).lower():
                            return d_idx
    except Exception:
        pass
    return None
