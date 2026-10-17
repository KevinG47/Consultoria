# -*- coding: utf-8 -*-
"""Comprobaciones del estudio: ¿es ruido Bogotá<->Cundinamarca? y ¿cómo es el subgrafo filtrado?"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR",
                          "NME_DEPARTAMENTO_RES_PR", "NME_MUNICIPIO_RES_PR"])
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
for c in ("NME_DEPARTAMENTO_RES_PR", "NME_MUNICIPIO_RES_PR"):
    df[c] = df[c].str.strip()
df = df.sort_values(["ID_PERSONA_PR", "conv"])
prim = df.drop_duplicates("ID_PERSONA_PR", keep="first").set_index("ID_PERSONA_PR")
ult = df.drop_duplicates("ID_PERSONA_PR", keep="last").set_index("ID_PERSONA_PR")
per = pd.DataFrame({
    "dep_ini": prim["NME_DEPARTAMENTO_RES_PR"], "dep_fin": ult["NME_DEPARTAMENTO_RES_PR"],
    "mun_ini": prim["NME_MUNICIPIO_RES_PR"], "mun_fin": ult["NME_MUNICIPIO_RES_PR"]})
ok = ~per["dep_ini"].isin(["Exterior", "No disponible"]) & \
     ~per["dep_fin"].isin(["Exterior", "No disponible"])
per = per[ok]
mueve = per[per["dep_ini"] != per["dep_fin"]]
mueve = mueve.assign(mismo_mun=mueve["mun_ini"] == mueve["mun_fin"])

print("=== ¿las mudanzas de departamento son también de municipio? ===")
print(f"  personas que cambian de departamento: {len(mueve)}")
print(f"  ... y conservan el MISMO municipio  : {int(mueve['mismo_mun'].sum())} "
      f"({100 * mueve['mismo_mun'].mean():.1f} %)")
print("  por ruta (top 10) — mismo municipio / total:")
rutas = (mueve.groupby(["dep_ini", "dep_fin"])
         .agg(total=("mismo_mun", "size"), mismo=("mismo_mun", "sum"))
         .sort_values("total", ascending=False).head(10).reset_index())
for _, r in rutas.iterrows():
    marca = "  <-- sospechosa" if r["mismo"] / r["total"] > 0.5 else ""
    print(f"    {r['dep_ini']:20} -> {r['dep_fin']:20} "
          f"{int(r['mismo']):3d}/{int(r['total']):3d}{marca}")

print("\n  municipios de la ruta Bogotá -> Cundinamarca (los 5 más frecuentes):")
b = mueve[(mueve["dep_ini"] == "Bogotá, D. C.") &
          (mueve["dep_fin"] == "Cundinamarca")]
print(f"    {dict(b['mun_fin'].value_counts().head(5))}")
print("\n  municipios de la ruta Cundinamarca -> Bogotá (los 5 más frecuentes):")
c = mueve[(mueve["dep_ini"] == "Cundinamarca") &
          (mueve["dep_fin"] == "Bogotá, D. C.")]
print(f"    {dict(c['mun_ini'].value_counts().head(5))}")

# ---------------------------------------------------------------- subgrafo
REPO = RAIZ / "04_auditoria" / "repo_original"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "src"))
real = sys.stdout
sys.stdout = io.TextIOWrapper(open(os.devnull, "wb"), encoding="utf-8")
try:
    import networkx as nx
    from analisis.redes import (construir_grafo, construir_pares,
                                subgrafo_grado_minimo)
finally:
    sys.stdout = real

d2 = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "INST_FILIA"])
d2["ANO_CONVO_INT"] = d2["ID_CONVOCATORIA"].astype(int).map(
    {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021})
G = construir_grafo(construir_pares(d2))
F = subgrafo_grado_minimo(G, 2)
comp = sorted((len(c) for c in nx.connected_components(F)), reverse=True)
print(f"\n=== subgrafo filtrado (grado >= 2) ===")
print(f"  {F.number_of_nodes()} nodos · {F.number_of_edges()} aristas · "
      f"densidad {nx.density(F):.4f}")
print(f"  componentes {len(comp)} · mayor {comp[0]} ({100 * comp[0] / F.number_of_nodes():.1f} % "
      f"de los nodos) · resto {comp[1:]}")
