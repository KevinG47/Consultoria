# -*- coding: utf-8 -*-
"""¿Con qué definición exacta se reproduce «documentada = 18 pares, FP = 1 058, FN = 9»?"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"
RESULTADOS = RAIZ / "01_datos" / "resultados_json"
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ANO_CONVO", "ID_PERSONA_PR",
                          "EDAD_ANOS_PR", "NME_GENERO_PR"])
df["fecha"] = pd.to_datetime(df["ANO_CONVO"], format="%d/%m/%Y", errors="coerce")
df["edad"] = pd.to_numeric(df["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                           errors="coerce")
df["genero"] = df["NME_GENERO_PR"].str.strip()
df = df.sort_values(["ID_PERSONA_PR", "fecha"])
g = df.groupby("ID_PERSONA_PR", observed=True, sort=False)
p = pd.DataFrame({
    "id": df["ID_PERSONA_PR"], "a": g["edad"].shift(1), "b": df["edad"],
    "ga": g["genero"].shift(1), "gb": df["genero"],
    "fa": g["fecha"].shift(1), "fb": df["fecha"]}).dropna(subset=["a", "b", "fa", "fb"])
p["anios"] = (p["fb"] - p["fa"]).dt.days / 365.25
p["dif_edad"] = p["b"] - p["a"]
p["residuo"] = p["dif_edad"] - p["anios"]

impl = p["dif_edad"] > 4.1
definiciones = {
    "documentada = SOLO edad (±4, bilateral)": p["residuo"].abs() > 4.0,
    "documentada = edad O género": (p["residuo"].abs() > 4.0) | (p["ga"] != p["gb"]),
    "documentada = edad Y género (literal)": (p["residuo"].abs() > 4.0) & (p["ga"] != p["gb"]),
}
u = json.loads((RESULTADOS / "validacion_unicidad.json").read_text(encoding="utf-8"))
cc = u["contraste_con_la_implementacion"]
print(f"publicado: documentada {cc['pares_marcados_documentada']} · "
      f"FP {cc['falsos_positivos_de_la_implementada']} · "
      f"FN {cc['falsos_negativos_de_la_implementada']}\n")
for nombre, doc in definiciones.items():
    print(f"{nombre}")
    print(f"   marcados {int(doc.sum())} · FP {int((impl & ~doc).sum())} · "
          f"FN {int((~impl & doc).sum())}")
