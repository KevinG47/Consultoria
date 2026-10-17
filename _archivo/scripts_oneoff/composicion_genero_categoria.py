# -*- coding: utf-8 -*-
"""Composicion categoria x genero (ultima convocatoria) para la narrativa de F2-10."""
from __future__ import annotations
import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "NME_CLASIFICACION_PR",
                          "NME_GENERO_PR", "NME_GRAN_AREA_PR"])
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
ult = (df.sort_values("conv").groupby("ID_PERSONA_PR", observed=True).last()
       .reset_index())

g = ult[ult["NME_GENERO_PR"].isin(["Masculino", "Femenino"])]
print("personas (última conv.):", len(g))
tab = pd.crosstab(g["NME_CLASIFICACION_PR"], g["NME_GENERO_PR"])
print("\nconteos:\n", tab)
pct = pd.crosstab(g["NME_CLASIFICACION_PR"], g["NME_GENERO_PR"], normalize="index") * 100
print("\n% de mujeres por categoría:\n", pct["Femenino"].round(2))
print("\nreparto de las mujeres entre categorías (%):")
print((tab["Femenino"] / tab["Femenino"].sum() * 100).round(2))
print("\nreparto de los hombres entre categorías (%):")
print((tab["Masculino"] / tab["Masculino"].sum() * 100).round(2))

ta = pd.crosstab(g["NME_GRAN_AREA_PR"], g["NME_GENERO_PR"], normalize="index") * 100
print("\n% de mujeres por gran área:\n", ta["Femenino"].round(2))
