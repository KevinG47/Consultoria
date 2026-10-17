# -*- coding: utf-8 -*-
"""Confirmación: reconstruir el stock de F2-2 (territorio válido) frente al de F2-10."""
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
POB = (RAIZ / "01_datos" / "datos_fuente"
       / "dane_cnpv2018_poblacion_departamental.csv")

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "COD_DANE_RES_PR",
                          "NME_DEPARTAMENTO_RES_PR"])
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
cod = df["COD_DANE_RES_PR"].str.strip()
df["prefijo"] = cod.str.slice(0, 2).where(cod.str.len() >= 2, "")
df["etiqueta"] = df["NME_DEPARTAMENTO_RES_PR"].str.strip()

pob = pd.read_csv(POB, dtype={"codigo_dane": str})
codigos = pob["codigo_dane"].tolist()
mapa = dict(zip(pob["codigo_dane"], pob["departamento"]))

# Definición A (F2-2): última convocatoria ENTRE las filas con territorio colombiano
val = df[df["prefijo"].isin(codigos)]
ultA = val.sort_values("conv").drop_duplicates("ID_PERSONA_PR", keep="last")
ultA = ultA.assign(depto=ultA["prefijo"].map(mapa))

# Definición B (F2-10 / EDA): última convocatoria observada, sin filtrar
ultB = df.sort_values("conv").drop_duplicates("ID_PERSONA_PR", keep="last")

p = json.loads((RESULTADOS / "percapita_territorial.json").read_text(encoding="utf-8"))
print("=== stock de personas ===")
print(f"  A (última con territorio colombiano): {len(ultA):,}".replace(",", " "))
print(f"  B (última observada)               : {len(ultB):,}".replace(",", " "))
print(f"  publicado en percapita.json        : {p['conteos']['stock_personas']:,}".replace(",", " "))

print("\n=== Bogotá ===")
print(f"  A: {int((ultA['depto'] == 'Bogotá, D. C.').sum()):,}".replace(",", " "))
print(f"  B: {int((ultB['etiqueta'] == 'Bogotá, D. C.').sum()):,}".replace(",", " "))
print("  publicado en percapita.json:",
      p["tasa_por_100000"]["stock_ultima_convocatoria"]["Bogotá, D. C."]["investigadores"])

print("\n=== ¿Quiénes son las personas que solo cuenta A? ===")
soloA = set(ultA["ID_PERSONA_PR"]) - set(
    ultB.loc[ultB["prefijo"].isin(codigos), "ID_PERSONA_PR"])
print(f"  personas en A y no en B: {len(soloA):,}".replace(",", " "))
etqB = ultB[ultB["ID_PERSONA_PR"].isin(soloA)]["etiqueta"].value_counts()
print("  su última etiqueta observada:", {k: int(v) for k, v in etqB.items()})

print("\n=== efecto sobre las cifras publicadas ===")
pob_map = {str(r["departamento"]).strip(): float(r["poblacion_censada_2018"])
           for _, r in pob.iterrows()}
pob_bog = float(pob[pob["codigo_dane"] == "11"]["poblacion_censada_2018"].iloc[0])
tot_pob = float(pob["poblacion_censada_2018"].sum())
cA = int((ultA["depto"] == "Bogotá, D. C.").sum())
print(f"  tasa Bogotá A: {cA / pob_bog * 1e5:.4f}  (publicada 137,6877)")
print(f"  cuota Bogotá A: {cA / len(ultA) * 100:.4f} %  (publicada 34,1554 %)")
print(f"  cociente A: {(cA / len(ultA)) / (pob_bog / tot_pob):.4f}  (publicado 2,1005)")
