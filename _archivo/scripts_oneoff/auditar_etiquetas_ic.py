# -*- coding: utf-8 -*-
"""Auditoría puntual: etiquetas de departamento en cada fuente y el IC de Bogotá."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
POB = (RAIZ / "datos_originales" / "datos_fuente"
       / "dane_cnpv2018_poblacion_departamental.csv")

print("=== 1. ¿Cuál archivo escribe «Bogotá» con doble espacio? ===")
inv = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                  usecols=["NME_DEPARTAMENTO_RES_PR"])
for k in inv["NME_DEPARTAMENTO_RES_PR"].value_counts().index:
    if "Bogot" in k or "Andr" in k:
        print(f"  investigadores CSV: {k!r}  (len={len(k)})")
dane = pd.read_csv(POB, dtype=str, keep_default_na=False, encoding="utf-8")
for k in dane["departamento"]:
    if "Bogot" in k or "Andr" in k:
        print(f"  DANE CSV          : {k!r}  (len={len(k)})")

print("\n=== 2. IC del stock que publica el documento (Bogotá 135,5–139,9) ===")
p = json.loads((MEM / "percapita_territorial.json").read_text(encoding="utf-8"))
bs = p["bootstrap_personas"]["por_convocatoria_y_stock"]["stock"]["tasa_ic95"]
lo, hi = bs["lo"], bs["hi"]
st = p["tasa_por_100000"]["stock_ultima_convocatoria"]
orden = list(st)  # orden del diccionario JSON
print(f"  n departamentos: {len(lo)} · en el stock: {len(st)}")
pares = [(round(l, 1), round(h, 1)) for l, h in zip(lo, hi)]
buscado = any(abs(l - 135.5) < 0.15 and abs(h - 139.9) < 0.15 for l, h in pares)
print(f"  ¿aparece (135,5; 139,9) entre los intervalos? {buscado}")
if buscado:
    idx = [i for i, (l, h) in enumerate(pares)
           if abs(l - 135.5) < 0.15 and abs(h - 139.9) < 0.15][0]
    print(f"  posición {idx}: el stock en ese orden tiene "
          f"{list(st)[idx]!r} (tasa {st[list(st)[idx]]['tasa_por_100000']:.4f})")

print("\n=== 3. ¿El orden de los intervalos coincide con el del diccionario? ===")
# Se comprueba con la tasa nacional: la mediana de los centros debe parecerse.
centros = [(l + h) / 2 for l, h in zip(lo, hi)]
tasas = [v["tasa_por_100000"] for v in st.values()]
print(f"  correlación entre centros de IC y tasas (mismo orden): "
      f"{pd.Series(centros).corr(pd.Series(tasas)):.4f}")
