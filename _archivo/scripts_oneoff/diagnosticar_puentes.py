# -*- coding: utf-8 -*-
"""Diagnostica por qué 326 nodos quedaron sin prueba en el nulo de intercambio."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
J = json.loads((RAIZ / "01_datos" / "resultados_json" / "redes_nulos.json")
               .read_text(encoding="utf-8"))

print("=== nulo_de_intercambio ===")
print(json.dumps(J["nulo_de_intercambio"], ensure_ascii=False, indent=1))

nodos = pd.read_csv(DOC / "data" / "memoria" / "redes_nodos_2019.csv",
                    encoding="utf-8")
print(f"\n=== distribución de grado de los 446 nodos ===")
print(nodos["grado"].value_counts().sort_index().to_string())
print(f"\nnodos con z disponible: {nodos['betweenness_z'].notna().sum()}")
print(f"nodos con z NaN       : {nodos['betweenness_z'].isna().sum()}")
por_grado = nodos.groupby("grado")["betweenness_z"].agg(
    ["size", lambda s: s.notna().sum()]).rename(
    columns={"<lambda_0>": "con_z"})
print("\n=== por grado: cuántos nodos y cuántos tienen z ===")
print(por_grado.to_string())

print("\n=== betweenness por grado (observada) ===")
print(nodos.groupby("grado")["betweenness"].agg(
    ["size", "mean", "max"]).to_string())
