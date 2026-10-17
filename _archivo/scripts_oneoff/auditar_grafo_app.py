# -*- coding: utf-8 -*-
"""
Compara el grafo del auditado (498 nodos) con el de F2-4 (446 nodos).

Se usan SUS funciones (analisis.redes) sobre NUESTRA base, para aislar de dónde
sale la diferencia: del filtro por año o del insumo.
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(RAIZ / "04_auditoria" / "repo_original" / "src"))

real = sys.stdout
sys.stdout = io.TextIOWrapper(open(os.devnull, "wb"), encoding="utf-8")
try:
    import networkx as nx
    from analisis.redes import (construir_grafo, construir_pares, metricas_grafo,
                                normalizar_institucion, subgrafo_grado_minimo)
finally:
    sys.stdout = real

FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "INST_FILIA"])
df["ANO_CONVO_INT"] = df["ID_CONVOCATORIA"].astype(int).map(
    {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021})
df["INST_FILIA"] = df["INST_FILIA"].str.strip()

con_doble = df["INST_FILIA"].str.contains("|", regex=False)
print(f"registros con «|» en INST_FILIA: {int(con_doble.sum())} "
      f"(por año: {dict(df.loc[con_doble].groupby('ANO_CONVO_INT').size())})")

pares = construir_pares(df)
print(f"pares tras normalizar y quitar self-loops: {len(pares)}")

for etiqueta, sub in (("TODAS las convocatorias (lo que hace el script del auditado)",
                      pares),
                      ("solo 2019 (lo que hace F2-4)", pares[pares["ANO_CONVO_INT"] == 2019])):
    G = construir_grafo(sub)
    m = metricas_grafo(G)
    filtrado = subgrafo_grado_minimo(G, 2)
    print(f"\n{etiqueta}")
    print(f"   nodos {m['n_nodos']} · aristas {m['n_aristas']} · "
          f"componentes {m['n_componentes']} · mayor {m['tam_componente_mayor']}")
    print(f"   subgrafo con grado >= 2: {filtrado.number_of_nodes()} nodos, "
          f"{filtrado.number_of_edges()} aristas")

# ¿Cuántos pares son de años distintos de 2019?
print("\npares por año:", dict(pares.groupby("ANO_CONVO_INT").size()))

# Distribución del grado en el grafo completo (la razón del aspecto «raro»)
G = construir_grafo(pares)
grados = pd.Series([d for _, d in G.degree()])
print(f"\ngrado en el grafo completo: {len(grados)} nodos · "
      f"hojas (grado 1) {int((grados == 1).sum())} "
      f"({100 * (grados == 1).mean():.1f} %) · máximo {int(grados.max())}")
