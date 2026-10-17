# -*- coding: utf-8 -*-
"""Inspecciona el poetry.lock regenerado: paquetes clave y versiones."""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

lock = Path("04_auditoria/repo_mejorado/poetry.lock")
t = lock.read_text(encoding="utf-8")
print(f"  bytes: {len(t)}   entradas 'name = ': {len(re.findall(r'^name = ', t, re.M))}")

PAT = re.compile(r'^name = "([^"]+)"\nversion = "([^"]+)"', re.M)
versiones = {m.group(1): m.group(2) for m in PAT.finditer(t)}

for p in ["kaleido", "openpyxl", "pyyaml", "nbformat", "ipython", "plotly",
          "duckdb", "seaborn", "streamlit", "sodapy", "pandas", "numpy"]:
    print(f"  {p:12s} {versiones.get(p, 'NO ESTA EN EL LOCK')}")

print("\n  paquetes que el codigo importa y que el lock NO contiene:")
faltan = [p for p in ["kaleido", "openpyxl", "pyyaml", "nbformat", "ipython"]
          if p not in versiones]
print(f"    {faltan or 'ninguno'}")

# Contraste con lo realmente instalado
print("\n  contraste con el entorno instalado:")
import importlib.metadata as md
for p in ["plotly", "duckdb", "seaborn", "streamlit", "kaleido"]:
    try:
        inst = md.version(p)
    except Exception:
        inst = "no instalado"
    lock_v = versiones.get(p, "—")
    aviso = "" if inst.startswith(lock_v.split(".")[0]) else "   <-- DISCREPANCIA"
    print(f"    {p:12s} lock={lock_v:10s} instalado={inst}{aviso}")
