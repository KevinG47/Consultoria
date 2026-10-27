#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expI_hhi.py
===========

Experimento 1 de la iteración Laya/open-weights: contexto institucional.

Motivación: Godoy, Abramo, D'Angelo & Cortés (2026, Scientometrics 131(9):5803-5824)
encuentran que la concentración de capital académico en la institución
(researcher_rank_hhi) es el correlato más fuerte del resultado de carrera,
por encima de la movilidad geográfica.

Construcción (SOLO folds 17..20; test = 21 NO se toca):
  - HHI de rangos por (institución, convocatoria): sum_k p_k^2 con k=12..15.
  - share_senior = (n_senior + n_emerito) / n_institucion.
  - log del tamaño de la institución.
  - REZAGO: para la fila (persona, cohorte c) se usa la institución de c y el
    HHI de esa institución medido en c-1.
  - movilidad institucional: institución en c != institución en c-1.

Variantes: base 172 | +HHI | +movilidad | +todo.
Criterio: media F1 baja OOS >= 0.3185 (+2 pp sobre 0.2985) para tocar test.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import opt_comun as oc  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"
RAIZ = SCRIPT_DIR.parents[1]
CENSO = RAIZ / "01_datos" / "datos_fuente" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
BASE_F1 = 0.2985
DELTA = 0.02
PARAMS = dict(oc.BASE, n_estimators=100, min_child_weight=1, gamma=0.1,
              subsample=0.8, max_depth=7, learning_rate=0.05)


# --------------------------------------------------------------------------
# Construcción de features institucionales
# --------------------------------------------------------------------------
def censo_instituciones():
    import pandas as pd

    c = pd.read_csv(CENSO, usecols=["ID_PERSONA_PR", "ID_CONVOCATORIA",
                                    "ORDEN_CLAS_PR", "INST_FILIA"],
                    dtype=str, encoding="utf-8-sig", keep_default_na=False)
    c["ID_PERSONA_PR"] = c["ID_PERSONA_PR"].str.strip().str.zfill(10)
    c["ID_CONVOCATORIA"] = pd.to_numeric(c["ID_CONVOCATORIA"], errors="coerce").astype("Int64")
    c["ORDEN_CLAS_PR"] = pd.to_numeric(c["ORDEN_CLAS_PR"], errors="coerce").astype("Int64")
    c["INST_FILIA"] = c["INST_FILIA"].str.strip().str.upper()
    c = c[c["ID_CONVOCATORIA"].notna() & c["ORDEN_CLAS_PR"].notna()].copy()
    c = c.drop_duplicates(["ID_PERSONA_PR", "ID_CONVOCATORIA"])
    return c


def hhi_por_institucion(c):
    """HHI de rangos, share senior y tamaño por (institución, convocatoria)."""
    import pandas as pd

    out = []
    for (inst, conv), g in c.groupby(["INST_FILIA", "ID_CONVOCATORIA"]):
        n = len(g)
        if inst == "" or n == 0:
            continue
        p = np.array([(g["ORDEN_CLAS_PR"] == k).sum() / n for k in (12, 13, 14, 15)])
        out.append({
            "INST_FILIA": inst,
            "ID_CONVOCATORIA": int(conv),
            "hhi_rango": float(np.sum(p ** 2)),
            "share_senior": float(p[2] + p[3]),
            "n_inst": float(n),
        })
    d = pd.DataFrame(out)
    d["log_n_inst"] = np.log1p(d["n_inst"])
    return d


def features_institucionales(df):
    import pandas as pd

    c = censo_instituciones()
    hhi = hhi_por_institucion(c)

    # institución de cada persona en cada cohorte
    inst = c[["ID_PERSONA_PR", "ID_CONVOCATORIA", "INST_FILIA"]].copy()
    inst["ID_CONVOCATORIA"] = inst["ID_CONVOCATORIA"].astype(int)

    base = pd.DataFrame({
        "ID_PERSONA_PR": df["ID_PERSONA_PR"].astype(str).str.zfill(10),
        "ID_CONVOCATORIA": pd.to_numeric(df["ID_CONVOCATORIA"], errors="coerce").astype(int),
    })
    base["ID_CONVOCATORIA_PREV"] = base["ID_CONVOCATORIA"] - 1  # cohortes 16..20 -> 15..19

    # institución actual (cohorte c) y anterior (c-1)
    act = inst.rename(columns={"ID_CONVOCATORIA": "ID_CONVOCATORIA", "INST_FILIA": "inst_t"})
    prev = inst.rename(columns={"ID_CONVOCATORIA": "ID_CONVOCATORIA_PREV",
                                "INST_FILIA": "inst_prev"})
    m = base.merge(act, on=["ID_PERSONA_PR", "ID_CONVOCATORIA"], how="left")
    m = m.merge(prev, on=["ID_PERSONA_PR", "ID_CONVOCATORIA_PREV"], how="left")
    m.index = df.index

    # HHI de la institución actual medido en c-1 (REZAGO)
    hhi_prev = hhi.rename(columns={
        "ID_CONVOCATORIA": "ID_CONVOCATORIA_PREV",
        "hhi_rango": "hhi_rango_lag1",
        "share_senior": "share_senior_lag1",
        "log_n_inst": "log_n_inst_lag1",
    })[["INST_FILIA", "ID_CONVOCATORIA_PREV", "hhi_rango_lag1",
        "share_senior_lag1", "log_n_inst_lag1"]]
    m = m.merge(hhi_prev, left_on=["inst_t", "ID_CONVOCATORIA_PREV"],
                right_on=["INST_FILIA", "ID_CONVOCATORIA_PREV"], how="left")

    out = pd.DataFrame(index=df.index)
    out["hhi_rango_lag1"] = m["hhi_rango_lag1"].astype("float64")
    out["share_senior_lag1"] = m["share_senior_lag1"].astype("float64")
    out["log_n_inst_lag1"] = m["log_n_inst_lag1"].astype("float64")
    out["hhi_faltante"] = out["hhi_rango_lag1"].isna().astype("float32")

    # movilidad institucional entre c-1 y c
    a = m["inst_t"].fillna("").str.strip().str.upper()
    b = m["inst_prev"].fillna("").str.strip().str.upper()
    valido = (a != "") & (b != "")
    out["mov_inst"] = (valido & (a != b)).astype("float32")
    out["mov_inst_faltante"] = (~valido).astype("float32")
    return out


# --------------------------------------------------------------------------
# Evaluación
# --------------------------------------------------------------------------
def correr(X, y, cat, per, variante):
    f1s, macros, briers, ts = [], [], [], []
    for fold in oc.FOLDS:
        t, _, p_va, p_ev, y_ev = oc.correr_fold(X, y, cat, per, fold, PARAMS)
        m = oc.metricas_eval(p_ev, y_ev, t)
        f1s.append(m["f1_baja"])
        macros.append(m["f1_macro"])
        briers.append(m["brier"])
        ts.append(t)
    return {"variante": variante,
            "f1_baja_folds": [round(v, 4) for v in f1s],
            "media": round(float(np.mean(f1s)), 4),
            "desv": round(float(np.std(f1s, ddof=0)), 4),
            "f1_macro_medio": round(float(np.mean(macros)), 4),
            "brier_medio": round(float(np.mean(briers)), 4),
            "umbrales": ts}


def main() -> int:
    df, feats = oc.cargar()
    inst_feats = features_institucionales(df)
    nuevas = ["hhi_rango_lag1", "share_senior_lag1", "log_n_inst_lag1", "hhi_faltante",
              "mov_inst", "mov_inst_faltante"]
    print(f"base: {len(feats)} features | nuevas: {len(nuevas)} -> total {len(feats)+len(nuevas)}")
    print(f"cobertura HHI lag1: {1-inst_feats['hhi_faltante'].mean():.1%} de las filas")
    print(f"movilidad institucional observada: {inst_feats.loc[inst_feats['mov_inst_faltante']==0,'mov_inst'].mean():.2%}")

    Xb = oc.matriz(df, feats)
    Xn = inst_feats[nuevas].to_numpy(dtype="float32")
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    # el test (cohorte 21) no entra en ningún fold: los folds solo usan 17..20
    assert set(np.unique(per)) <= {17, 18, 19, 20, 21}

    def cols(*nombres):
        idx = [nuevas.index(c) for c in nombres]
        return np.column_stack([Xb, Xn[:, idx]])

    variantes = {
        "base_172": Xb,
        "hhi": cols("hhi_rango_lag1", "share_senior_lag1", "log_n_inst_lag1", "hhi_faltante"),
        "movilidad": cols("mov_inst", "mov_inst_faltante"),
        "hhi_movilidad": np.column_stack([Xb, Xn]),
    }

    resultados = {}
    print(f"\n{'variante':16s} {'folds':26s} {'media':>6} {'desv':>6} {'F1macro':>8} {'Brier':>7}  t")
    for nombre, X in variantes.items():
        r = correr(X, y, cat, per, nombre)
        resultados[nombre] = r
        print(f"{nombre:16s} {str(r['f1_baja_folds']):26s} {r['media']:>6.4f} "
              f"{r['desv']:>6.4f} {r['f1_macro_medio']:>8.4f} {r['brier_medio']:>7.4f}  {r['umbrales']}")

    mejor = max([r for k, r in resultados.items() if k != "base_172"], key=lambda r: r["media"])
    print(f"\nMEJOR: {mejor['variante']} -> media {mejor['media']:.4f} "
          f"(base {BASE_F1:.4f}, delta {100*(mejor['media']-BASE_F1):+.2f} pp)")
    print(f"criterio para tocar test: media >= {BASE_F1 + DELTA:.4f}")
    toca_test = bool(mejor["media"] >= BASE_F1 + DELTA)
    print("CUMPLE el +2 pp: se documenta plan de test." if toca_test
          else "NO cumple el +2 pp: test NO se toca.")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "I_hhi_institucional",
        "fuente_metodologica": "Godoy, Abramo, D'Angelo & Cortés (2026), Scientometrics 131(9):5803-5824",
        "n_base": len(feats), "n_nuevas": len(nuevas), "n_total": len(feats) + len(nuevas),
        "cobertura_hhi_lag1": round(float(1 - inst_feats["hhi_faltante"].mean()), 4),
        "tasa_movilidad_institucional": round(float(
            inst_feats.loc[inst_feats["mov_inst_faltante"] == 0, "mov_inst"].mean()), 4),
        "config": {k: PARAMS[k] for k in ("n_estimators", "min_child_weight", "gamma",
                                          "subsample", "max_depth", "learning_rate")},
        "resultados": resultados, "mejor": mejor,
        "base_f1_baja_oos": BASE_F1, "delta_pp": round(100 * (mejor["media"] - BASE_F1), 2),
        "criterio_test": round(BASE_F1 + DELTA, 4), "toco_test": toca_test,
        "test": None,
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("expI_hhi_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
