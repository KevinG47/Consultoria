# -*- coding: utf-8 -*-
"""¿De dónde salen los 498 nodos del grafo de la app? Se prueba con el consolidado versionado."""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
REPO = RAIZ / "datos_originales" / "repo_auditado"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "src"))

real = sys.stdout
sys.stdout = io.TextIOWrapper(open(os.devnull, "wb"), encoding="utf-8")
try:
    from analisis.redes import (construir_grafo, construir_pares, metricas_grafo,
                                subgrafo_grado_minimo)
finally:
    sys.stdout = real

CONSOLIDADO = REPO / "datos" / "tarea_join" / "investigadores_consolidado.csv"
df = pd.read_csv(CONSOLIDADO, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "INST_FILIA"])
df["ANO_CONVO_INT"] = pd.to_numeric(df["ID_CONVOCATORIA"], errors="coerce")
df["INST_FILIA"] = df["INST_FILIA"].str.strip()
print(f"consolidado: {len(df):,} filas · {df['ID_PERSONA_PR'].nunique():,} personas".replace(",", " "))
print(f"convocatorias: {sorted(df['ANO_CONVO_INT'].dropna().unique().tolist())}")

con_doble = df["INST_FILIA"].str.contains("|", regex=False)
print(f"filas con «|»: {int(con_doble.sum())}")

pares = construir_pares(df)
G = construir_grafo(pares)
m = metricas_grafo(G)
print(f"\nGRAFO del consolidado: {m['n_nodos']} nodos · {m['n_aristas']} aristas · "
      f"componentes {m['n_componentes']} · mayor {m['tam_componente_mayor']}")
print(f"subgrafo grado>=2: {subgrafo_grado_minimo(G, 2).number_of_nodes()} nodos")
print("\n(El script del auditado anuncia 498 nodos y 146 en el filtrado)")
print(f"\nfilas con «|» por año: "
      f"{dict(df.loc[con_doble].groupby('ANO_CONVO_INT').size())}")
