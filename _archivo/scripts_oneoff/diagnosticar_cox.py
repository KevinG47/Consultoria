# -*- coding: utf-8 -*-
"""
Diagnóstico de la no convergencia del Cox en F2-10.

Hipótesis a comprobar:
  H1. El empate masivo en t = 0 (36 % de las personas aparecen en una sola
      convocatoria, así que t = 0) rompe la identificación.
  H2. Algún nivel de covariable no tiene a nadie en riesgo después del último
      evento que experimenta (separación).
  H3. El hessiano está mal condicionado por colinealidad de los dummies.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "documentacion_auditoria" / "src"))
sys.dont_write_bytecode = True

from supervivencia import _grad_hess, cox_efron  # noqa: E402

FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
DEPT_TOP = ["Bogotá  D. C.", "Antioquia", "Valle del Cauca", "Atlántico",
            "Santander"]
cols = ["ID_CONVOCATORIA", "ID_PERSONA_PR", "ANO_CONVO",
        "NME_CLASIFICACION_PR", "NME_GENERO_PR", "NME_GRAN_AREA_PR",
        "NME_DEPARTAMENTO_RES_PR"]
df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=cols)
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
df["fecha"] = pd.to_datetime(df["ANO_CONVO"], format="%d/%m/%Y")
df = df.sort_values(["ID_PERSONA_PR", "conv"])
pri = df.drop_duplicates("ID_PERSONA_PR", keep="first")
ult = df.drop_duplicates("ID_PERSONA_PR", keep="last")
per = ult.merge(pri[["ID_PERSONA_PR", "fecha", "conv"]], on="ID_PERSONA_PR",
                suffixes=("_ult", "_prim"))
per["t"] = (per["fecha_ult"] - per["fecha_prim"]).dt.days / 365.25
per["evento"] = (per["conv_ult"] != 21).astype(float)
per["genero_col"] = per["NME_GENERO_PR"].map(
    lambda g: g if g in ("Masculino", "Femenino") else "Otro")
per["depto_top"] = np.where(per["NME_DEPARTAMENTO_RES_PR"].isin(DEPT_TOP),
                            per["NME_DEPARTAMENTO_RES_PR"], "Resto")

print(f"personas: {len(per):,}".replace(",", " "))
print(f"\n=== H1: masa en t = 0 ===")
print(f"  personas con t = 0: {int((per['t'] == 0).sum()):,} "
      f"({100*(per['t'] == 0).mean():.1f} %)")
print(f"  de ellas con evento: {int(((per['t'] == 0) & (per['evento'] == 1)).sum()):,}")
print(f"  tiempos de evento distintos: {per.loc[per['evento'] == 1, 't'].nunique()}")

print("\n=== H2: ¿algún nivel se queda sin riesgo después de sus eventos? ===")
for col in ("NME_CLASIFICACION_PR", "NME_GRAN_AREA_PR", "depto_top",
            "genero_col"):
    print(f"\n  {col}:")
    for lv, g in per.groupby(col):
        ev = g[g["evento"] == 1]["t"]
        if ev.empty:
            print(f"    {str(lv)[:34]:36s} n={len(g):6,d} sin eventos")
            continue
        t_last = ev.max()
        en_riesgo_despues = int((g["t"] > t_last).sum())
        t0 = int((ev == 0).sum())
        print(f"    {str(lv)[:34]:36s} n={len(g):6,d} ev={len(ev):6,d} "
              f"ev en t=0: {t0:6,d} · en riesgo tras su último evento: "
              f"{en_riesgo_despues}")

print("\n=== H3: condicionamiento del hessiano en β = 0 ===")
base = per[(per["genero_col"] != "Otro") & (per["NME_CLASIFICACION_PR"] !=
                                            "Investigador Emérito")].copy()
dummies = {}
for col, niveles, corto in (
        ("NME_CLASIFICACION_PR",
         ["Investigador Junior", "Investigador Asociado", "Investigador Sénior"], "cat"),
        ("genero_col", ["Masculino", "Femenino"], "gen"),
        ("NME_GRAN_AREA_PR", sorted(base["NME_GRAN_AREA_PR"].unique()), "area"),
        ("depto_top", DEPT_TOP + ["Resto"], "dep")):
    for lv in niveles[1:]:
        dummies[f"{corto}={lv}"] = (base[col] == lv).astype(float).to_numpy()
X = np.column_stack(list(dummies.values()))
t = base["t"].to_numpy()
e = base["evento"].to_numpy()
ll, g, h = _grad_hess(X, t, e, np.zeros(X.shape[1]))
autoval = np.linalg.eigvalsh(-h)
print(f"  n={len(base):,} p={X.shape[1]}".replace(",", " "))
print(f"  condicionamiento del hessiano: {autoval.max()/max(autoval.min(), 1e-300):.3e}")
print(f"  autovalores mínimos: {np.sort(autoval)[:4]}")

print("\n=== H1b: ¿converge si se excluyen las personas con t = 0? ===")
m = t > 0
r = cox_efron(X[m], t[m], e[m])
print(f"  t > 0: n={int(m.sum()):,} eventos={int(e[m].sum()):,} "
      f"convergio={r['convergio']} gradiente="
      f"{r.get('gradiente_final', float('nan')):.2e}".replace(",", " "))

print("\n=== H2b: ¿converge con solo algunas covariables? ===")
for etiqueta, prefijos in (
        ("solo género", ["gen="]),
        ("género + categoría", ["gen=", "cat="]),
        ("género + categoría + área", ["gen=", "cat=", "area="]),
        ("todas", ["gen=", "cat=", "area=", "dep="])):
    sel = [i for i, k in enumerate(dummies) if any(k.startswith(p)
                                                   for p in prefijos)]
    r = cox_efron(X[:, sel], t, e)
    print(f"  {etiqueta:28s} p={len(sel):2d} convergio={r['convergio']} "
          f"gradiente={r.get('gradiente_final', float('nan')):.2e} "
          f"it={r.get('iteraciones', '?')}")
