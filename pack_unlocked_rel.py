import os, zipfile
with zipfile.ZipFile("AiPulsar_Windows.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for r, _, fs in os.walk("AiPulsar_Release_Ready/AiPulsar_Portable"):
        for f in fs:
            fp = os.path.join(r, f)
            zf.write(fp, os.path.relpath(fp, "AiPulsar_Release_Ready/AiPulsar_Portable"))
print("PORTABLE ZIP UPDATED OK!")
