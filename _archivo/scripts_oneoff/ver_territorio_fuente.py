# -*- coding: utf-8 -*-
"""Valores territoriales reales en el CSV fuente de investigadores."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
CSV = (RAIZ / "datos_originales" / "datos_fuente"
       / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")

cab = pd.read_csv(CSV, nrows=3, dtype=str, keep_default_na=False, encoding="utf-8")
print("=== COLUMNAS ===")
for i, c in enumerate(cab.columns):
    print(f"  {i:3d}  {c}")

REL = [c for c in cab.columns if any(
    k in c.upper() for k in ("DEPARTAMENTO", "REGION", "MUNICIPIO", "CONVOCATORIA",
                             "ID_PERSONA", "PAIS"))]
print(f"\n=== COLUMNAS TERRITORIALES: {REL} ===")

df = pd.read_csv(CSV, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=REL)
print(f"\nfilas totales: {len(df):,}")

for col in REL:
    if "ID_PERSONA" in col.upper():
        print(f"\n{col}: {df[col].nunique():,} valores distintos")
        continue
    print(f"\n=== {col} ({df[col].nunique()} valores distintos) ===")
    vc = df[col].value_counts(dropna=False)
    for k, v in vc.items():
        print(f"  {k!r:55s} {v:8,d}".replace(",", " "))
