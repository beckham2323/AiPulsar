# -*- coding: utf-8 -*-
import os, sys

DIST_DIR = r"D:\AiPulsar\dist\AiPulsar"
EXE_PATH = os.path.join(DIST_DIR, "AiPulsar.exe")
MANIFEST_PATH = os.path.join(DIST_DIR, "_internal", "core", "release_manifest.json")

if not os.path.isfile(EXE_PATH):
    print(f"AUDIT FAIL: {EXE_PATH} not found!")
    sys.exit(1)

exposed = []
for r, _, fs in os.walk(DIST_DIR):
    for f in fs:
        if f.endswith(".py") and not f.endswith(("config.py", "config-3.py")):
            exposed.append(os.path.join(r, f))

if exposed:
    print("AUDIT FAIL: exposed .py sources found:", exposed)
    sys.exit(1)

print("RELEASE AUDIT PASSED 100% OK!")
sys.exit(0)
