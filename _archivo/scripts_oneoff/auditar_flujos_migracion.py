# -*- coding: utf-8 -*-
"""
¿Hay datos para un mapa de flujos? Dos definiciones posibles de «migración»:

  A) Cambio de departamento de RESIDENCIA entre la primera y la última
     convocatoria observada de la misma persona («se mudó entre 2013 y 2021»).
  B) Departamento de NACIMIENTO distinto del de residencia
     (migración acumulada de toda la vida, no del período).

Se cuantifican las dos para decidir cuál (o cuáles) van al mapa.
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

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR",
                          "NME_DEPARTAMENTO_RES_PR", "COD_DANE_RES_PR",
                          "NME_DEPARTAMENTO_NAC_PR", "COD_DANE_NAC_PR"])
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
for c in ("NME_DEPARTAMENTO_RES_PR", "NME_DEPARTAMENTO_NAC_PR"):
    df[c] = df[c].str.strip()

COLOMBIA = 33
print(f"registros {len(df):,} · personas {df['ID_PERSONA_PR'].nunique():,}"
      .replace(",", " "))

# ---------------------------------------------------------------- A) mudanza
df = df.sort_values(["ID_PERSONA_PR", "conv"])
prim = df.drop_duplicates("ID_PERSONA_PR", keep="first").set_index("ID_PERSONA_PR")
ult = df.drop_duplicates("ID_PERSONA_PR", keep="last").set_index("ID_PERSONA_PR")
n_conv = df.groupby("ID_PERSONA_PR").size()

per = pd.DataFrame({
    "n_conv": n_conv,
    "res_ini": prim["NME_DEPARTAMENTO_RES_PR"],
    "res_fin": ult["NME_DEPARTAMENTO_RES_PR"],
})
validas = ~per["res_ini"].isin(["Exterior", "No disponible"]) & \
          ~per["res_fin"].isin(["Exterior", "No disponible"])
con_varias = per["n_conv"] >= 2

print("\n=== A) cambio de residencia entre la primera y la última convocatoria ===")
print(f"  personas con 2+ convocatorias      : {int(con_varias.sum()):,}".replace(",", " "))
print(f"  ... y departamento válido en ambas : "
      f"{int((con_varias & validas).sum()):,}".replace(",", " "))
base = per[con_varias & validas]
mueve = base[base["res_ini"] != base["res_fin"]]
print(f"  que CAMBIAN de departamento        : {len(mueve):,} "
      f"({100 * len(mueve) / len(base):.2f} % de la base comparable)".replace(",", " "))

rutas = (mueve.groupby(["res_ini", "res_fin"]).size()
         .sort_values(ascending=False))
print(f"  rutas distintas                    : {len(rutas)}")
print(f"  rutas con 1 sola persona           : {int((rutas == 1).sum())}")
print("\n  TOP 10 rutas:")
for (o, d), n in rutas.head(10).items():
    print(f"    {o:22} -> {d:22} {n:4d}")
print(f"\n  las 10 primeras rutas explican {100 * rutas.head(10).sum() / rutas.sum():.1f} % "
      f"de los movimientos; las 20 primeras, "
      f"{100 * rutas.head(20).sum() / rutas.sum():.1f} %")

print("\n  flujo neto por departamento (los 6 mayores):")
entradas = mueve.groupby("res_fin").size()
salidas = mueve.groupby("res_ini").size()
neto = (entradas.reindex(sorted(set(entradas.index) | set(salidas.index)),
                         fill_value=0)
        - salidas.reindex(sorted(set(entradas.index) | set(salidas.index)),
                          fill_value=0)).sort_values()
for dep in list(neto.tail(3).index) + list(neto.head(3).index):
    print(f"    {dep:22} {neto[dep]:+5d}")

# ------------------------------------------------------------- B) nacimiento
print("\n=== B) departamento de nacimiento frente al de residencia ===")
ult_todos = df.drop_duplicates("ID_PERSONA_PR", keep="last")
con_nac = ult_todos["NME_DEPARTAMENTO_NAC_PR"]
print(f"  personas (última convocatoria)     : {len(ult_todos):,}".replace(",", " "))
print(f"  sin dato de nacimiento             : "
      f"{int(con_nac.isin(['No disponible', '']).sum()):,} · "
      f"nacidas en el exterior {int((con_nac == 'Exterior').sum()):,}".replace(",", " "))
ok = ~con_nac.isin(["", "No disponible"]) & \
     ~ult_todos["NME_DEPARTAMENTO_RES_PR"].isin(["Exterior", "No disponible"])
sub = ult_todos[ok]
dif = sub[sub["NME_DEPARTAMENTO_NAC_PR"] != sub["NME_DEPARTAMENTO_RES_PR"]]
print(f"  comparables                        : {len(sub):,}".replace(",", " "))
print(f"  que residen fuera de su cuna       : {len(dif):,} "
      f"({100 * len(dif) / len(sub):.1f} %)".replace(",", " "))
r2 = dif.groupby(["NME_DEPARTAMENTO_NAC_PR",
                  "NME_DEPARTAMENTO_RES_PR"]).size().sort_values(ascending=False)
print(f"  rutas distintas                    : {len(r2)}")
print("\n  TOP 10 rutas nacimiento -> residencia:")
for (o, d), n in r2.head(10).items():
    print(f"    {o:22} -> {d:22} {n:4d}")
print(f"\n  las 10 primeras rutas explican "
      f"{100 * r2.head(10).sum() / r2.sum():.1f} % de los casos")
