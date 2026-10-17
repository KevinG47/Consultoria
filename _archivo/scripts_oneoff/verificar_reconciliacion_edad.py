# -*- coding: utf-8 -*-
"""Verifica la causa de que 12 personas con edad >100 den 11 al colapsar."""
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
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "EDAD_ANOS_PR",
                          "NME_CONVOCATORIA"])
df["conv_i"] = df["ID_CONVOCATORIA"].astype(int)
df["edad"] = pd.to_numeric(df["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                           errors="coerce")

masc = df["edad"] > 100
print(f"registros con edad > 100        : {int(masc.sum())}")
print(f"personas distintas con alguno   : {df.loc[masc, 'ID_PERSONA_PR'].nunique()}")

ult = df.sort_values("conv_i").drop_duplicates("ID_PERSONA_PR", keep="last")
print(f"personas con edad > 100 en su ULTIMA convocatoria: "
      f"{int((ult['edad'] > 100).sum())}")

# ¿Quién está en el primer conjunto pero no en el segundo?
p_todas = set(df.loc[masc, "ID_PERSONA_PR"])
p_ult = set(ult.loc[ult["edad"] > 100, "ID_PERSONA_PR"])
difs = sorted(p_todas - p_ult)
print(f"\npersonas con >100 en alguna convocatoria y NO en la última: {len(difs)}")
for p in difs:
    sub = df[df["ID_PERSONA_PR"] == p].sort_values("conv_i")
    print(f"\n  ID {p}:")
    for _, r in sub.iterrows():
        marca = "  <-- >100" if r["edad"] > 100 else ""
        print(f"    {r['conv_i']} ({r['NME_CONVOCATORIA']}): "
              f"edad={r['edad']}{marca}")
    edades = sub["edad"].tolist()
    print(f"    ¿la edad DECRECE? {edades != sorted(edades)}")

# Distribución de cuántos registros >100 aporta cada persona
print("\nregistros >100 por persona:")
for k, v in df.loc[masc].groupby("ID_PERSONA_PR").size().value_counts().sort_index().items():
    print(f"   {k} registro(s): {v} persona(s)")
