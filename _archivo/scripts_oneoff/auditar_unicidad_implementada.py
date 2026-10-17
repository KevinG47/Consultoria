# -*- coding: utf-8 -*-
"""Verifica la regla IMPLEMENTADA del auditado: dif_edad > 4,1 (una cola)."""
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
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
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

impl = p["dif_edad"] > 4.1                      # regla del auditado
doc = (p["residuo"].abs() > 4.0) | (p["ga"] != p["gb"])   # regla documentada

u = json.loads((RESULTADOS / "validacion_unicidad.json").read_text(encoding="utf-8"))
cc = u["contraste_con_la_implementacion"]
print("=== regla implementada (dif_edad > 4,1) ===")
print(f"  pares marcados: recalculado {int(impl.sum()):,} · "
      f"publicado {cc['pares_marcados_implementada']:,}".replace(",", " "))
print(f"=== regla documentada ===")
print(f"  pares marcados: recalculado {int(doc.sum()):,} · "
      f"publicado {cc['pares_marcados_documentada']:,}".replace(",", " "))
fp = int((impl & ~doc).sum())
fn = int((~impl & doc).sum())
print(f"  falsos positivos: recalculado {fp:,} · "
      f"publicado {cc['falsos_positivos_de_la_implementada']:,}".replace(",", " "))
print(f"  falsos negativos: recalculado {fn} · "
      f"publicado {cc['falsos_negativos_de_la_implementada']}")
retro = int((p["dif_edad"] < -4).sum())
print(f"  pares con la edad retrocediendo más de 4 años: recalculado {retro} · "
      f"publicado {cc['pares_con_edad_que_retrocede_mas_de_4']}")

print("\n=== sensibilidad a la tolerancia (regla de edad, bilateral) ===")
for t in (0.5, 1.0, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0):
    calc = int((p["residuo"].abs() > t).sum())
    pub = u["sensibilidad_tolerancia"]["pares_por_tolerancia"][str(t)]
    print(f"  ±{t:<4}: recalculado {calc:6,} · publicado {pub:6,} "
          f"{'OK' if calc == pub else 'MAL'}".replace(",", " "))
