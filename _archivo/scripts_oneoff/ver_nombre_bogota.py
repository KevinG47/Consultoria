# -*- coding: utf-8 -*-
"""Muestra la representación EXACTA de los nombres de departamento."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["NME_DEPARTAMENTO_RES_PR"])
for v in df["NME_DEPARTAMENTO_RES_PR"].value_counts().head(8).index:
    print(f"  {v!r:60s} n={df['NME_DEPARTAMENTO_RES_PR'].value_counts()[v]:,}"
          .replace(",", " "))
print()
objetivo = "Bogotá  D. C."
print(f"¿existe {objetivo!r} exactamente?: {objetivo in set(df['NME_DEPARTAMENTO_RES_PR'])}")
for v in sorted(set(df["NME_DEPARTAMENTO_RES_PR"])):
    if "Bogot" in v:
        print(f"  encontrado: {v!r}  (espacios: {v.count(' ')})")
