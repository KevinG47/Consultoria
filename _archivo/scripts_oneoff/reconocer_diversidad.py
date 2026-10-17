# -*- coding: utf-8 -*-
"""Reconocimiento para F2-5: valores y COBERTURA de las variables de diversidad
por convocatoria en la fuente completa."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
REPO = RAIZ / "datos_originales" / "repo_auditado" / "evidencias"

COLS = ["ID_CONVOCATORIA", "ID_PERSONA_PR", "TXT_GRUPO_ETNICO",
        "TXT_POBLACION_DISCA", "ID_VICTIMA_CONFLICTO", "NME_GENERO_PR"]
df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=COLS)
df["anio"] = df["ID_CONVOCATORIA"].astype(int).map(
    {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021})
print(f"registros: {len(df):,}".replace(",", " "))

VACIOS = {"", "NO DISPONIBLE", "NO REPORTADO", "NAN", "NONE"}

for col in COLS[2:]:
    print("\n" + "=" * 88)
    print(f"{col} — valores distintos: {df[col].nunique()}")
    print("=" * 88)
    print(f"{'valor':45s} {'n':>8s} {'%':>7s}")
    for k, v in df[col].value_counts(dropna=False).items():
        print(f"  {str(k)[:43]:45s} {v:8,d} {100*v/len(df):6.2f} %".replace(",", " "))

print("\n" + "=" * 88)
print("COBERTURA POR CONVOCATORIA (proporción de valores CONOCIDOS)")
print("=" * 88)
print(f"{'año':>6s} {'n':>8s} " + " ".join(f"{c[:14]:>15s}" for c in COLS[2:]))
for anio, g in df.groupby("anio"):
    fila = [f"{len(g):8,d}".replace(",", " ")]
    for col in COLS[2:]:
        conocido = ~g[col].str.strip().str.upper().isin(VACIOS)
        fila.append(f"{100*conocido.mean():14.2f}%")
    print(f"{anio:>6d} " + " ".join(fila))

print("\n" + "=" * 88)
print("EVIDENCIA DEL AUDITADO")
print("=" * 88)
for nombre in ("diversidad_comparacion_dane.csv",
               "diversidad_cobertura_por_convocatoria.csv",
               "diversidad_distribucion_etnia_2021.csv",
               "diversidad_distribucion_discapacidad_2021.csv",
               "diversidad_distribucion_victimas_2021.csv"):
    p = REPO / nombre
    print(f"\n--- {nombre} ---")
    print(p.read_text(encoding="utf-8-sig").strip() if p.exists() else "NO EXISTE")
