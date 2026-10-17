# -*- coding: utf-8 -*-
"""Comprueba el entorno para F2-3: duckdb disponible y formato de entrada."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
REPO = RAIZ / "datos_originales" / "repo_auditado"

print("=== dependencias ===")
for mod in ("duckdb", "openpyxl", "numpy", "pandas", "matplotlib"):
    try:
        m = __import__(mod)
        print(f"   {mod:12s} OK  {getattr(m, '__version__', '?')}")
    except Exception as e:                                  # noqa: BLE001
        print(f"   {mod:12s} FALTA  {type(e).__name__}: {e}")

print("\n=== cabeceras ===")
fuente = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
consolidado = REPO / "datos" / "tarea_join" / "investigadores_consolidado.csv"

h_fuente = list(pd.read_csv(fuente, nrows=2, dtype=str,
                            keep_default_na=False, encoding="utf-8").columns)
h_cons = list(pd.read_csv(consolidado, nrows=2, dtype=str,
                          keep_default_na=False, encoding="utf-8").columns)

print(f"   fuente (6 convocatorias)      : {len(h_fuente)} columnas")
print(f"   consolidado (3 convocatorias) : {len(h_cons)} columnas")
print(f"   ¿mismas columnas y orden?     : {h_fuente == h_cons}")
if h_fuente != h_cons:
    print(f"   solo en fuente      : {[c for c in h_fuente if c not in h_cons]}")
    print(f"   solo en consolidado : {[c for c in h_cons if c not in h_fuente]}")
    print(f"   orden fuente      : {h_fuente}")
    print(f"   orden consolidado : {h_cons}")

print("\n=== columna ANO_CONVO ===")
for nombre, ruta in (("fuente", fuente), ("consolidado", consolidado)):
    s = pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding="utf-8",
                    usecols=["ANO_CONVO"])["ANO_CONVO"]
    print(f"   {nombre:12s} {s.nunique()} valores distintos: "
          f"{sorted(s.unique().tolist())[:8]}")

print("\n=== ingesta del auditado: qué prefiere cargar_consolidado() ===")
print((REPO / "src" / "ingesta" / "__init__.py").read_text(encoding="utf-8"))
