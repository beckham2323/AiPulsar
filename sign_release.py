# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import os
import py_compile

_INTEGRITY_SECRET = b"VESKOR_SMIRNOV_VE_AIPULSAR_ANTI_TAMPER_2026_SIG"
DIST_DIR = os.path.join("dist", "AiPulsar")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def protect_and_sign():
    # 1. Компилируем все .py внутри dist\AiPulsar\_internal\core в оптимизированный байт-код (-OO) и удаляем открытые .py исходники!
    core_dist = os.path.join(DIST_DIR, "_internal", "core")
    if os.path.isdir(core_dist):
        for fn in os.listdir(core_dist):
            if fn.endswith(".py"):
                py_path = os.path.join(core_dist, fn)
                pyc_path = py_path + "c"
                py_compile.compile(py_path, cfile=pyc_path, optimize=2)
                os.remove(py_path)

    # 2. Подписываем ключевые файлы сборки криптографической печатью HMAC-SHA256
    files_map = {}
    targets = ["AiAiPulsar.exe", "aipulsar.ico", "LICENSE.txt"]
    for t in targets:
        fp = os.path.join(DIST_DIR, t)
        if os.path.exists(fp):
            files_map[t] = _sha256(fp)

    if os.path.isdir(core_dist):
        for fn in sorted(os.listdir(core_dist)):
            fp = os.path.join(core_dist, fn)
            if os.path.isfile(fp):
                rel = f"_internal/core/{fn}"
                files_map[rel] = _sha256(fp)

    raw_payload = json.dumps(files_map, sort_keys=True).encode("utf-8")
    sig = hmac.new(_INTEGRITY_SECRET, raw_payload, hashlib.sha256).hexdigest()

    sig_out = os.path.join(DIST_DIR, "_internal", "integrity.sig")
    with open(sig_out, "w", encoding="utf-8") as f:
        json.dump({"owner": "V.E. Smirnov (VESKOR)", "files": files_map, "signature": sig}, f, indent=2)

    print(f"ANTI-TAMPER & ANTI-MOD SEAL APPLIED OK ({len(files_map)} protected files, 0 .py sources exposed).")


if __name__ == "__main__":
    protect_and_sign()
