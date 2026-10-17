# -*- coding: utf-8 -*-
"""
Reconocimiento para F2-4: cobertura de INST_FILIA y de la doble afiliación por
convocatoria, y forma de los pares de co-filiación.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
REPO = RAIZ / "04_auditoria" / "repo_original" / "evidencias"

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "INST_FILIA"])
df["anio"] = df["ID_CONVOCATORIA"].astype(int).map(
    {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021})
df["inst"] = df["INST_FILIA"].str.strip()
df["vacio"] = df["inst"] == ""
df["doble"] = df["inst"].str.contains("|", regex=False)

print(f"registros: {len(df):,}".replace(",", " "))
print("\n=== INST_FILIA por convocatoria ===")
print(f"{'año':>6s} {'registros':>10s} {'vacíos':>9s} {'% vacío':>8s} "
      f"{'con 2 inst':>11s} {'% doble':>8s}")
for a, g in df.groupby("anio"):
    print(f"{a:>6d} {len(g):10,d} {int(g['vacio'].sum()):9,d} "
          f"{100*g['vacio'].mean():7.2f}% {int(g['doble'].sum()):11,d} "
          f"{100*g['doble'].mean():7.2f}%".replace(",", " "))

print("\n=== personas distintas con doble afiliación, por convocatoria ===")
for a, g in df.groupby("anio"):
    d = g[g["doble"]]
    print(f"  {a}: {d['ID_PERSONA_PR'].nunique():,} personas · "
          f"{len(d):,} registros".replace(",", " "))

print("\n=== ¿cuántas instituciones por registro? ===")
n_inst = df.loc[df["doble"], "inst"].str.count(r"\|") + 1
print(f"  distribución del número de instituciones por registro con doble: "
      f"{n_inst.value_counts().sort_index().to_dict()}")

print("\n=== EVIDENCIA DEL AUDITADO ===")
for nombre in ("redes_metricas_por_convocatoria.csv",
               "redes_pares_cofiliacion.csv",
               "redes_nodos_global.csv",
               "redes_aristas_global.csv"):
    p = REPO / nombre
    print(f"\n--- {nombre} ---")
    if not p.exists():
        print("  NO EXISTE")
        continue
    d = pd.read_csv(p, encoding="utf-8-sig")
    print(f"  shape: {d.shape}")
    print(f"  columnas: {list(d.columns)}")
    print(d.head(6).to_string(index=False))
