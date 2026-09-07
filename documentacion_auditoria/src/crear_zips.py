# -*- coding: utf-8 -*-
"""Crea los 13 ZIPs Overleaf con zipfile (robusto a bloqueos de archivos)."""
import io
import sys
import zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(r".\documentacion_auditoria")
LATEX = BASE / "latex"
ZIPS = BASE / "zip_overleaf"
ZIPS.mkdir(exist_ok=True)

nombres = sorted(p.name for p in LATEX.iterdir() if (p / "main.tex").exists())

ok, err = 0, 0
for n in nombres:
    src = LATEX / n
    if not (src / "main.tex").exists():
        print(f"FALTA PROYECTO: {n}")
        err += 1
        continue
    destino = ZIPS / f"{n}_overleaf.zip"
    try:
        if destino.exists():
            destino.unlink()
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(src.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(src))
        ok += 1
    except Exception as e:  # noqa: BLE001
        print(f"ERROR {n}: {e}")
        err += 1

print(f"ZIPs OK={ok} ERRORES={err}")
