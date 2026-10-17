# -*- coding: utf-8 -*-
"""Reconocimiento para F2-6: sklearn disponible, cardinalidad y faltantes de las
variables que el cluster del auditado interpretaba."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")

for mod in ("sklearn", "scipy", "numpy"):
    try:
        m = __import__(mod)
        print(f"{mod:10s} {getattr(m, '__version__', '?')}")
    except Exception as e:                                  # noqa: BLE001
        print(f"{mod:10s} FALTA: {e}")

COLS = ["ID_CONVOCATORIA", "ID_PERSONA_PR", "NME_GRAN_AREA_PR", "NME_GENERO_PR",
        "NME_REGION_NAC_PR", "NME_NIV_FORM_PR", "NME_CLASIFICACION_PR",
        "NME_REGION_RES_PR", "EDAD_ANOS_PR", "TXT_POBLACION_DISCA"]
df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=COLS)
df["anio"] = df["ID_CONVOCATORIA"].astype(int).map(
    {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021})
print(f"\nregistros: {len(df):,} · personas: {df['ID_PERSONA_PR'].nunique():,}"
      .replace(",", " "))

print("\n=== cardinalidad y vacíos de las candidatas ===")
print(f"{'columna':26s} {'cat':>5s} {'vacíos':>8s} {'%':>7s} {'NO DISP/NO REG':>15s}")
for c in COLS[2:]:
    s = df[c].str.strip()
    vac = (s == "").sum()
    nulos = s.str.upper().isin(["NO DISPONIBLE", "NO REGISTRA",
                                "NO REPORTADO"]).sum()
    print(f"{c:26s} {s.nunique():5d} {vac:8,d} {100*vac/len(df):6.2f}% "
          f"{100*nulos/len(df):14.2f}%".replace(",", " "))

print("\n=== EDAD_ANOS_PR numérica ===")
edad = pd.to_numeric(df["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                     errors="coerce")
print(f"  faltantes: {int(edad.isna().sum())} · "
      f"min={edad.min():.2f} · max={edad.max():.2f} · media={edad.mean():.2f}")

print("\n=== distribuciones de las categóricas (top 12) ===")
for c in ("NME_GRAN_AREA_PR", "NME_GENERO_PR", "NME_NIV_FORM_PR",
          "NME_CLASIFICACION_PR", "NME_REGION_RES_PR", "NME_REGION_NAC_PR"):
    vc = df[c].str.strip().value_counts()
    print(f"\n  {c} ({vc.size}):")
    for k, v in vc.head(12).items():
        print(f"    {k[:44]:46s} {v:8,d} {100*v/len(df):6.2f}%".replace(",", " "))

print("\n=== ¿las categóricas cambian dentro de la misma persona? ===")
for c in ("NME_GRAN_AREA_PR", "NME_GENERO_PR", "NME_NIV_FORM_PR",
          "NME_CLASIFICACION_PR", "NME_REGION_RES_PR"):
    n = int((df.groupby("ID_PERSONA_PR")[c].nunique() > 1).sum())
    print(f"  {c:24s} personas con más de un valor: {n:6,d}".replace(",", " "))
