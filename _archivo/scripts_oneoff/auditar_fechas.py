# -*- coding: utf-8 -*-
"""Auditoria: fechas por convocatoria y consistencia de las series de tiempo."""
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
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "ANO_CONVO"])
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
print("=== fechas distintas por ID_CONVOCATORIA ===")
for c, g in df.groupby("conv"):
    val = g["ANO_CONVO"].value_counts()
    print(f"  conv {c}: {len(val)} fecha(s) distinta(s)")
    for f, n in val.items():
        print(f"      {f!r} -> {n:,} filas")
