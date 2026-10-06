"""Reconocimiento previo al analisis longitudinal.

Preguntas que responde (todas determinan reglas de analisis):
  1. Existen duplicados (ID_PERSONA_PR, ID_CONVOCATORIA)?
  2. Los atributos de una persona son constantes entre convocatorias?
  3. Cuantos vacios hay en las columnas clave?
  4. Distribucion a nivel PERSONA (no registro) de los atributos clave.

Solo lectura: no escribe ni modifica nada.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CSV = RAIZ / "Datos" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"

COLS = [
    "ID_CONVOCATORIA", "NME_CONVOCATORIA", "ID_PERSONA_PR",
    "NME_GENERO_PR", "NME_DEPARTAMENTO_RES_PR", "NME_GRAN_AREA_PR",
    "NME_NIV_FORM_PR", "NME_CLASIFICACION_PR", "ID_CLAS_PR",
]

partes = []
for trozo in pd.read_csv(CSV, dtype=str, keep_default_na=False,
                         chunksize=50_000, encoding="utf-8"):
    partes.append(trozo[COLS].copy())
df = pd.concat(partes, ignore_index=True)
del partes

print(f"filas={len(df)}  columnas leidas={len(COLS)}")
print(f"personas unicas={df['ID_PERSONA_PR'].nunique()}")
print(f"convocatorias={df['ID_CONVOCATORIA'].nunique()}")

# --- 1. duplicados persona x convocatoria ---
dup = df.duplicated(subset=["ID_PERSONA_PR", "ID_CONVOCATORIA"], keep=False)
print(f"\n[1] filas en duplicado (ID_PERSONA, CONV) = {int(dup.sum())}")
if dup.any():
    print(df[dup].sort_values(["ID_PERSONA_PR", "ID_CONVOCATORIA"]).head(12).to_string())

# --- 2. consistencia de atributos por persona ---
print("\n[2] personas con mas de un valor distinto del atributo:")
for col in ["NME_GENERO_PR", "NME_DEPARTAMENTO_RES_PR", "NME_GRAN_AREA_PR",
            "NME_NIV_FORM_PR", "NME_CLASIFICACION_PR"]:
    n = df.groupby("ID_PERSONA_PR", observed=True)[col].nunique(dropna=False)
    print(f"    {col:26s} >1 valor: {int((n > 1).sum()):6d}"
          f"   max valores distintos: {int(n.max())}")

# --- 3. vacios por columna ---
print("\n[3] vacios (cadena vacia) por columna:")
for col in COLS:
    v = int((df[col] == "").sum())
    print(f"    {col:26s} {v:7d}")

# --- 4. distribucion a nivel persona (ultima convocatoria de cada persona) ---
df["_conv"] = df["ID_CONVOCATORIA"].astype(int)
ult = df.sort_values("_conv").groupby("ID_PERSONA_PR", observed=True).last()
print(f"\n[4] marco de personas (ultima convocatoria observada) = {len(ult)}")
for col in ["NME_GENERO_PR", "NME_CLASIFICACION_PR", "NME_GRAN_AREA_PR",
            "NME_NIV_FORM_PR", "NME_DEPARTAMENTO_RES_PR"]:
    print(f"\n  --- {col} (nivel persona) ---")
    vc = ult[col].value_counts(dropna=False)
    for k, v in vc.items():
        print(f"      {str(k)[:48]:50s} {v:7d}  {100*v/len(ult):6.2f}%")

# --- 5. registros por persona ---
print("\n[5] registros por persona:")
rpp = df.groupby("ID_PERSONA_PR", observed=True).size()
print(rpp.value_counts().sort_index().to_string())
print(f"    media={rpp.mean():.3f}  max={rpp.max()}")

sys.exit(0)
