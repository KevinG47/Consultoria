# -*- coding: utf-8 -*-
"""Identifica la combinación lineal que hace singular el diseño del Cox."""
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
from supervivencia import _grad_hess  # noqa: E402

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
base = per[(per["genero_col"] != "Otro") & (per["NME_CLASIFICACION_PR"] !=
                                            "Investigador Emérito")].copy()

nombres, cols_ = [], []
for col, niveles, corto in (
        ("NME_CLASIFICACION_PR",
         ["Investigador Junior", "Investigador Asociado", "Investigador Sénior"], "cat"),
        ("genero_col", ["Masculino", "Femenino"], "gen"),
        ("NME_GRAN_AREA_PR", sorted(base["NME_GRAN_AREA_PR"].unique()), "area"),
        ("depto_top", DEPT_TOP + ["Resto"], "dep")):
    for lv in niveles[1:]:
        nombres.append(f"{corto}={lv}")
        cols_.append((base[col] == lv).astype(float).to_numpy())
X = np.column_stack(cols_)
t = base["t"].to_numpy()
e = base["evento"].to_numpy()
ll, g, h = _grad_hess(X, t, e, np.zeros(X.shape[1]))
val, vec = np.linalg.eigh(-h)
v = vec[:, 0]                      # autovector del autovalor mínimo
if np.abs(v).max() > 0:
    v = v / np.abs(v).max()
print("autovalores extremos:", val.min(), val.max())
print("autovalor 2:", val[1])
print("\ncarga del autovector nulo (|carga| > 0,05):")
for i, car in enumerate(v):
    if abs(car) > 0.05:
        print(f"  {nombres[i]:34s} {car:+.4f}")
print(f"\ngradiente en β=0 en la dirección nula: {abs(g @ vec[:, 0]):.3e}")
print(f"gradiente total: {np.abs(g).max():.3e}")

# ¿Qué columnas son combinación lineal? Se busca el rango de X sobre los eventos
print("\n=== rango del diseño restringido a los conjuntos de riesgo ===")
print(f"  rango(X completa) = {np.linalg.matrix_rank(X)} de {X.shape[1]} columnas")
for tiempo in np.unique(t[e == 1]):
    R = t >= tiempo
    r = np.linalg.matrix_rank(X[R])
    print(f"  t={tiempo:6.3f}: |R|={int(R.sum()):6,d} rango={r}")
