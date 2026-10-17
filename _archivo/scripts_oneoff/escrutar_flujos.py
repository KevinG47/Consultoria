# -*- coding: utf-8 -*-
"""Escrutinio previo al mapa F2-11: numeros exactos y evidencia municipal."""
from __future__ import annotations

import io
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
FUENTE = (RAIZ / "datos_originales" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
COLS = ["ID_CONVOCATORIA", "ID_PERSONA_PR", "NME_DEPARTAMENTO_RES_PR",
        "COD_DANE_RES_PR", "NME_MUNICIPIO_RES_PR",
        "NME_DEPARTAMENTO_NAC_PR", "COD_DANE_NAC_PR", "NME_MUNICIPIO_NAC_PR"]

df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=COLS)
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
for c in ("NME_DEPARTAMENTO_RES_PR", "NME_DEPARTAMENTO_NAC_PR", "NME_MUNICIPIO_RES_PR",
          "NME_MUNICIPIO_NAC_PR"):
    df[c] = df[c].str.strip()

print(f"registros {len(df)} · personas {df['ID_PERSONA_PR'].nunique()}")

print("\n=== etiquetas de departamento de residencia ===")
vc = df["NME_DEPARTAMENTO_RES_PR"].value_counts()
print(f"{len(vc)} etiquetas")
for k, v in vc.items():
    print(f"  {k!r:58} {v:6d}")

print("\n=== codigo DANE por etiqueta (residencia) ===")
for k, g in df.groupby("NME_DEPARTAMENTO_RES_PR", observed=True):
    cods = sorted(set(g["COD_DANE_RES_PR"]))
    print(f"  {k!r:58} {cods[:4]}")

df = df.sort_values(["ID_PERSONA_PR", "conv"])
prim = df.drop_duplicates("ID_PERSONA_PR", keep="first").set_index("ID_PERSONA_PR")
ult = df.drop_duplicates("ID_PERSONA_PR", keep="last").set_index("ID_PERSONA_PR")
n_conv = df.groupby("ID_PERSONA_PR").size()

per = pd.DataFrame({
    "n_conv": n_conv,
    "res_ini": prim["NME_DEPARTAMENTO_RES_PR"],
    "res_fin": ult["NME_DEPARTAMENTO_RES_PR"],
    "mun_ini": prim["NME_MUNICIPIO_RES_PR"],
    "mun_fin": ult["NME_MUNICIPIO_RES_PR"],
    "nac_ini": prim["NME_DEPARTAMENTO_NAC_PR"],
    "mun_nac": prim["NME_MUNICIPIO_NAC_PR"],
})
validas = ~per["res_ini"].isin(["Exterior", "No disponible"]) & \
          ~per["res_fin"].isin(["Exterior", "No disponible"])
con_varias = per["n_conv"] >= 2
base = per[con_varias & validas]
mueve = base[base["res_ini"] != base["res_fin"]]

print("\n=== A) mudanza de residencia 2013-2021 ===")
print(f"  2+ convocatorias            : {int(con_varias.sum())}")
print(f"  comparables                 : {len(base)}")
print(f"  cambian de departamento     : {len(mueve)}  ({100*len(mueve)/len(base):.2f} %)")
print(f"  2+ conv, sin salir de su depto: {len(base) - len(mueve)}")

rutas = mueve.groupby(["res_ini", "res_fin"]).size().sort_values(ascending=False)
print(f"  rutas                      : {len(rutas)}")
print(f"  rutas de 1 persona         : {int((rutas == 1).sum())}")
print(f"  top10 comparten            : {100*rutas.head(10).sum()/rutas.sum():.2f} %")
print(f"  top20 comparten            : {100*rutas.head(20).sum()/rutas.sum():.2f} %")
print(f"  top5 comparten             : {100*rutas.head(5).sum()/rutas.sum():.2f} %")
print("\n  top 20 rutas A:")
for (o, d), n in rutas.head(20).items():
    sub = mueve[(mueve["res_ini"] == o) & (mueve["res_fin"] == d)]
    mun_o = Counter(sub["mun_ini"]).most_common(3)
    mun_d = Counter(sub["mun_fin"]).most_common(3)
    print(f"  {o:24} -> {d:26} {n:4d} | {mun_o} -> {mun_d}")
print(f"  rutas con misma etiqueta de municipio: "
      f"{int((mueve['mun_ini'] == mueve['mun_fin']).sum())}")

print("\n  flujo neto A:")
enta = mueve.groupby("res_fin").size()
sale = mueve.groupby("res_ini").size()
idx = sorted(set(enta.index) | set(sale.index))
neto = (enta.reindex(idx, fill_value=0) - sale.reindex(idx, fill_value=0)
        ).sort_values()
print(f"  entradas totales {int(enta.sum())} · salidas {int(sale.sum())} · "
      f"depts con neto != 0: {int((neto != 0).sum())} (positivos "
      f"{int((neto > 0).sum())}, negativos {int((neto < 0).sum())})")
for dep, v in neto.items():
    print(f"    {dep:24} {v:+5d}")

print("\n=== B) nacimiento -> residencia ===")
ult_todos = df.drop_duplicates("ID_PERSONA_PR", keep="last")
con_nac = ult_todos["NME_DEPARTAMENTO_NAC_PR"]
print(f"  sin dato nacimiento: "
      f"{int(con_nac.isin(['No disponible', '']).sum())} · exterior "
      f"{int((con_nac == 'Exterior').sum())}")
ok = ~con_nac.isin(["", "No disponible"]) & \
     ~ult_todos["NME_DEPARTAMENTO_RES_PR"].isin(["Exterior", "No disponible"])
sub = ult_todos[ok]
dif = sub[sub["NME_DEPARTAMENTO_NAC_PR"] != sub["NME_DEPARTAMENTO_RES_PR"]]
print(f"  comparables       : {len(sub)}")
print(f"  fuera de su cuna  : {len(dif)}  ({100*len(dif)/len(sub):.2f} %)")
r2 = dif.groupby(["NME_DEPARTAMENTO_NAC_PR", "NME_DEPARTAMENTO_RES_PR"]
                 ).size().sort_values(ascending=False)
print(f"  rutas             : {len(r2)} · top10 "
      f"{100*r2.head(10).sum()/r2.sum():.2f} % · top20 "
      f"{100*r2.head(20).sum()/r2.sum():.2f} %")
print("\n  top 20 rutas B:")
for (o, d), n in r2.head(20).items():
    q = dif[(dif["NME_DEPARTAMENTO_NAC_PR"] == o) &
            (dif["NME_DEPARTAMENTO_RES_PR"] == d)]
    print(f"  {o:24} -> {d:26} {n:4d} | dest {Counter(q['NME_MUNICIPIO_RES_PR']).most_common(3)}")

print("\n  neto B:")
e2 = dif.groupby("NME_DEPARTAMENTO_RES_PR").size()
s2 = dif.groupby("NME_DEPARTAMENTO_NAC_PR").size()
i2 = sorted(set(e2.index) | set(s2.index))
n2 = (e2.reindex(i2, fill_value=0) - s2.reindex(i2, fill_value=0)).sort_values()
for dep, v in n2.items():
    print(f"    {dep:24} {v:+6d}")
