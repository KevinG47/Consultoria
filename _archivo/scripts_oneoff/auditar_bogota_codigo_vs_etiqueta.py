# -*- coding: utf-8 -*-
"""
Auditoría: ¿por qué F2-2 cuenta 9 888 personas en Bogotá y F2-10 cuenta 9 813?

F2-2 asigna departamento por el PREFIJO DIVIPOLA del código (`COD_DANE_RES_PR`).
F2-10 (y el EDA) lo asignan por la ETIQUETA (`NME_DEPARTAMENTO_RES_PR`).
Si las dos no coinciden, hay personas que caen en departamentos distintos según
el análisis. Aquí se mide cuántas y por qué.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
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

print("=== 1. Registros sin código DIVIPOLA (los que F2-2 excluye) ===")
sin = df["prefijo"] == ""
print(f"  registros sin código: {int(sin.sum()):,}".replace(",", " "))
print("  por etiqueta:", {k: int(v) for k, v in
                          df.loc[sin, "etiqueta"].value_counts().items()})
print(f"  personas distintas sin código: "
      f"{df.loc[sin, 'ID_PERSONA_PR'].nunique():,}".replace(",", " "))

print("\n=== 2. ¿Coinciden código y etiqueta? (última convocatoria) ===")
ult = df.sort_values("conv").groupby("ID_PERSONA_PR", observed=True).last()
pob = pd.read_csv(POB)
pob["codigo_dane"] = pob["codigo_dane"].astype(str).str.zfill(2)
mapa = dict(zip(pob["codigo_dane"], pob["departamento"]))

con_cod = ult[ult["prefijo"] != ""].copy()
con_cod["depto_por_codigo"] = con_cod["prefijo"].map(mapa)
discrepa = con_cod[con_cod["depto_por_codigo"] != con_cod["etiqueta"]]
print(f"  personas con código: {len(con_cod):,}".replace(",", " "))
print(f"  personas donde código y etiqueta NO coinciden: "
      f"{len(discrepa):,}".replace(",", " "))
print(f"  personas sin código: {len(ult) - len(con_cod):,}".replace(",", " "))
print(f"  total personas: {len(ult):,}".replace(",", " "))

print("\n=== 3. Los pares (etiqueta, depto_por_código) que discrepan ===")
tab = (discrepa.groupby(["etiqueta", "depto_por_codigo"])
       .size().sort_values(ascending=False))
for (et, co), n in tab.items():
    print(f"  {n:5d}  etiqueta={et!r:34} -> código dice {co!r}")

print("\n=== 4. Conteo de Bogotá por los dos métodos ===")
etiqueta_bog = int((ult["etiqueta"] == "Bogotá, D. C.").sum())
codigo_bog = int((con_cod["depto_por_codigo"] == "Bogotá, D. C.").sum())
print(f"  por etiqueta (F2-10 / EDA): {etiqueta_bog:,}".replace(",", " "))
print(f"  por código   (F2-2)        : {codigo_bog:,}".replace(",", " "))
print(f"  diferencia: {codigo_bog - etiqueta_bog}")

print("\n=== 5. Efecto en la tasa y en el cociente publicado ===")
pob_map = {str(r["departamento"]).strip(): float(r["poblacion_censada_2018"])
           for _, r in pob.iterrows()}
pob_map = {k.replace("  ", " "): v for k, v in pob_map.items()}
tin = 9888
tet = etiqueta_bog
tot_cod = len(con_cod)
tot_et = len(ult[~ult["etiqueta"].isin(["Exterior", "No disponible"])])
p_bog = pob_map["Bogotá D. C."] if "Bogotá D. C." in pob_map else pob_map.get("Bogotá, D. C.")
print(f"  población Bogotá (DANE): {p_bog:,.0f}".replace(",", " "))
print(f"  tasa por código : {tin / p_bog * 1e5:.4f}   (publicada 137,6877)")
print(f"  tasa por etiqueta: {tet / p_bog * 1e5:.4f}")
print(f"  stock por código: {tot_cod:,} · por etiqueta: {tot_et:,}".replace(",", " "))
print(f"  cociente Bogotá por código  : "
      f"{(tin / tot_cod) / (p_bog / sum(pob_map.values())):.4f}  (publicado 2,1005)")
print(f"  cociente Bogotá por etiqueta: "
      f"{(tet / tot_et) / (p_bog / sum(pob_map.values())):.4f}")
