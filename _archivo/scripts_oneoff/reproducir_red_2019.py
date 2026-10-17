# -*- coding: utf-8 -*-
"""
Reconocimiento 2 para F2-4: ¿se reproduce la red del auditado (446 nodos / 503
aristas) desde nuestra fuente? ¿De dónde salen las 32 diferencias entre 569
personas con doble afiliación y 537 pares?
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True          # no dejar .pyc en repo_auditado/

RAIZ = Path(__file__).resolve().parents[2]
REPO = RAIZ / "datos_originales" / "repo_auditado"
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
sys.path.insert(0, str(REPO / "src"))

try:
    import networkx as nx
    print(f"networkx {nx.__version__}")
except Exception as e:                                  # noqa: BLE001
    print(f"networkx FALTA: {e}")
    raise SystemExit(1)

from analisis.redes import (construir_grafo, construir_pares,   # noqa: E402
                            metricas_grafo, normalizar_institucion)

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "INST_FILIA",
                          "NME_REGION_RES_PR"])
df["ANO_CONVO_INT"] = df["ID_CONVOCATORIA"].astype(int).map(
    {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021})
df["INST_FILIA"] = df["INST_FILIA"].str.strip()

multi = df[df["INST_FILIA"].str.contains("|", regex=False)]
print(f"\nregistros con '|' en INST_FILIA      : {len(multi)}")
print(f"  de ellos, en 2019                  : "
      f"{int((multi['ANO_CONVO_INT'] == 2019).sum())}")

# --- ¿cuántos se pierden como self-loop al normalizar? --------------------
par_a, par_b = multi["INST_FILIA"].str.split("|", n=1, expand=True).T.values
na = pd.Series(par_a).str.strip().map(normalizar_institucion)
nb = pd.Series(par_b).str.strip().map(normalizar_institucion)
selfloops = int((na == nb).sum())
print(f"\npares que la normalizacion convierte en self-loop: {selfloops}")
print("  ejemplo(s):")
for i in list(pd.Series(range(len(multi)))[na == nb].head(5)):
    print(f"    {multi['INST_FILIA'].iloc[i]}")
    print(f"      -> {na.iloc[i]!r} | {nb.iloc[i]!r}")

# --- reproducir la red con el codigo del auditado -------------------------
pares = construir_pares(df)
print(f"\nconstruir_pares() -> {len(pares)} pares")
G = construir_grafo(pares, anio=2019)
m = metricas_grafo(G)
print("\n=== red de 2019 reconstruida ===")
for k in ("n_nodos", "n_aristas", "densidad", "n_componentes",
          "tam_componente_mayor", "grado_promedio", "grado_max",
          "nodo_mayor_grado"):
    print(f"  {k:22s} {m[k]}")

aud = pd.read_csv(REPO / "evidencias" / "redes_metricas_por_convocatoria.csv",
                  encoding="utf-8-sig").iloc[0]
print("\n=== contraste con la evidencia del auditado ===")
for k in ("n_nodos", "n_aristas", "n_componentes", "tam_componente_mayor",
          "grado_max", "nodo_mayor_grado"):
    ok = m[k] == aud[k]
    print(f"  [{'OK ' if ok else 'NO '}] {k:22s} reconstruido={m[k]} "
          f"evidencia={aud[k]}")
print(f"  densidad reconstruida={m['densidad']} evidencia={aud['densidad']}")

# --- region de cada institucion (proxy) ----------------------------------
print("\n=== region de cada institucion (region modal de quienes la declaran) ===")
sub = multi[multi["ANO_CONVO_INT"] == 2019]
largo = pd.concat([
    pd.DataFrame({"inst": sub["INST_FILIA"].str.split("|").str[0].str.strip()
                  .map(normalizar_institucion),
                  "region": sub["NME_REGION_RES_PR"].str.strip()}),
    pd.DataFrame({"inst": sub["INST_FILIA"].str.split("|").str[1].str.strip()
                  .map(normalizar_institucion),
                  "region": sub["NME_REGION_RES_PR"].str.strip()}),
])
reg = (largo[largo["inst"].notna()]
       .groupby("inst")["region"]
       .agg(lambda s: s.value_counts().index[0]))
multi_reg = largo.groupby("inst")["region"].nunique()
print(f"  instituciones con region asignada: {reg.size}")
print(f"  con MAS de una region declarada  : {int((multi_reg > 1).sum())}")
print(f"  distribucion de regiones: {reg.value_counts().to_dict()}")
print(f"  nodos del grafo sin region       : {len(set(G.nodes()) - set(reg.index))}")
