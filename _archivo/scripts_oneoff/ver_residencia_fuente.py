# -*- coding: utf-8 -*-
"""Inspecciona las columnas de RESIDENCIA (no de nacimiento) y el código DANE."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
CSV = (RAIZ / "01_datos" / "datos_fuente"
       / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")

COLS = ["ID_CONVOCATORIA", "ID_PERSONA_PR", "NME_PAIS_RES_PR", "NME_REGION_RES_PR",
        "NME_DEPARTAMENTO_RES_PR", "COD_DANE_RES_PR"]
df = pd.read_csv(CSV, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=COLS)
print(f"filas: {len(df):,}\n")

for col in COLS[2:]:
    print(f"=== {col} ({df[col].nunique()} distintos) ===")
    for k, v in df[col].value_counts().items():
        print(f"  {k!r:58s} {v:8,d}".replace(",", " "))
    print()

# ¿El código DANE permite reconstruir el departamento?
print("=== relación COD_DANE_RES_PR -> departamento ===")
if "COD_DANE_RES_PR" in df.columns:
    rel = (df.groupby(["COD_DANE_RES_PR", "NME_DEPARTAMENTO_RES_PR"])
             .size().reset_index(name="n"))
    amb = rel.groupby("COD_DANE_RES_PR").size()
    print(f"  códigos distintos            : {amb.size}")
    print(f"  códigos con >1 departamento  : {(amb > 1).sum()}")
    print(f"  longitudes del código        : "
          f"{sorted({len(str(c)) for c in df['COD_DANE_RES_PR']})}")

    print("\n  prefijo de 2 dígitos -> cuántos departamentos empareja")
    pre = rel.copy()
    pre["prefijo"] = pre["COD_DANE_RES_PR"].str.slice(0, 2)
    malos = []
    for pref, g in pre.groupby("prefijo"):
        deps = set(g["NME_DEPARTAMENTO_RES_PR"])
        if len(deps) > 1:
            malos.append((pref, sorted(deps)))
    print(f"  prefijos ambiguos: {len(malos)}")
    for p, d in malos[:10]:
        print(f"    {p} -> {d}")

    print("\n  departamentos distintos por prefijo (solo prefijos presentes):")
    for pref, g in sorted(pre.groupby("prefijo")):
        deps = sorted(set(g["NME_DEPARTAMENTO_RES_PR"]))
        print(f"    {pref} -> {deps}")
