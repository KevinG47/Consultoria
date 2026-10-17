# -*- coding: utf-8 -*-
"""¿De qué insumo salen los «141 nodos» y «61 componentes» que anuncia la app? Prueba con el XLSX."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
REPO = RAIZ / "04_auditoria" / "repo_original"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "src"))

real = sys.stdout
sys.stdout = io.TextIOWrapper(open(os.devnull, "wb"), encoding="utf-8")
try:
    from analisis.redes import (construir_grafo, construir_pares, metricas_grafo,
                                subgrafo_grado_minimo)
finally:
    sys.stdout = real

XLSX = REPO / "datos" / "tarea_join" / "investigadores_consolidado.xlsx"
df = pd.read_excel(XLSX, usecols=["ID_CONVOCATORIA", "ANO_CONVO", "ID_PERSONA_PR",
                                  "INST_FILIA"])
df.columns = [c.upper() for c in df.columns]
df["ANO_CONVO_INT"] = pd.to_datetime(df["ANO_CONVO"], errors="coerce").dt.year
df["INST_FILIA"] = df["INST_FILIA"].astype(str).str.strip()
print(f"XLSX: {len(df):,} filas · {df['ID_PERSONA_PR'].nunique():,} personas"
      .replace(",", " "))
print(f"años: {sorted(df['ANO_CONVO_INT'].dropna().unique().tolist())}")
doble = df["INST_FILIA"].str.contains("|", regex=False)
print(f"filas con «|»: {int(doble.sum())} "
      f"(por año {dict(df.loc[doble].groupby('ANO_CONVO_INT').size())})")

pares = construir_pares(df)
G = construir_grafo(pares)
m = metricas_grafo(G)
f = subgrafo_grado_minimo(G, 2)
print(f"\ngrafo completo: {m['n_nodos']} nodos · {m['n_aristas']} aristas · "
      f"{m['n_componentes']} componentes · mayor {m['tam_componente_mayor']}")
print(f"subgrafo grado>=2: {f.number_of_nodes()} nodos · "
      f"{f.number_of_edges()} aristas")
print("\nla app anuncia: 2021 · 141 nodos (filtrado) · 61 componentes")
