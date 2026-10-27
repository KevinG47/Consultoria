#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expM_lags2.py
=============

Experimento 5: lags de dos períodos.

Para cada fila (persona, cohorte c) que predice la transición c -> c+1 se añade
la producción observada en c-1 y en c-2 (cuando existen). Si no existen se
imputa 0 y se marca con una bandera.

Bloque de lags (7 variables x 2 rezagos + 2 banderas): total de productos,
artículos A1 y A2, artículos B, tesis de doctorado, proyectos de I+D y número
de grupos. Se elige este subconjunto (y no las 172 columnas duplicadas) para no
triplicar la dimensión con columnas casi colineales.

Config Ronda 2, 3 folds, test (cohorte 21) intacto.
Criterio: media F1 baja OOS >= 0.3185.
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
BASE_F1 = 0.2985
DELTA = 0.02
PARAMS = dict(oc.BASE, n_estimators=100, min_child_weight=1, gamma=0.1,
              subsample=0.8, max_depth=7, learning_rate=0.05)

COLS = {
    "prod": "n_productos",
    "a1": "n_categoria_ART_CULOS_DE_INVESTIGACI_N_CON_CALIDAD_A1",
    "a2": "n_categoria_ART_CULOS_DE_INVESTIGACI_N_CON_CALIDAD_A2",
    "b": "n_categoria_ART_CULOS_DE_INVESTIGACI_N_CON_CALIDAD_B",
    "tesis_d": "n_tipologia_TESIS_DE_DOCTORADO",
    "proy": "n_tipologia_PROYECTO_DE_INVESTIGACION_Y_DESARROLLO",
    "grupos": "n_grupos_distintos",
}


def construir_lags(df):
    import pandas as pd

    base = pd.DataFrame({
        "ID_PERSONA_PR": df["ID_PERSONA_PR"].astype(str).str.zfill(10),
        "c": pd.to_numeric(df["ID_CONVOCATORIA"], errors="coerce").astype("Int64"),
        "idx": df.index,
    })
    fuente = pd.DataFrame({"ID_PERSONA_PR": df["ID_PERSONA_PR"].astype(str).str.zfill(10),
                           "c": pd.to_numeric(df["ID_CONVOCATORIA"], errors="coerce").astype("Int64")})
    for k, col in COLS.items():
        if col in df.columns:
            fuente[k] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            fuente[k] = 0.0

    out = pd.DataFrame(index=df.index)
    for lag in (1, 2):
        prev = fuente.copy()
        prev["c"] = prev["c"] + lag
        prev = prev.drop_duplicates(["ID_PERSONA_PR", "c"])
        m = base.merge(prev, on=["ID_PERSONA_PR", "c"], how="left", suffixes=("", f"_l{lag}"))
        m.index = df.index
        for k in COLS:
            out[f"{k}_lag{lag}"] = m[k].fillna(0.0).astype("float32")
        out[f"lag{lag}_disponible"] = m[list(COLS.keys())[0]].notna().astype("float32")
    return out


def correr(X, y, cat, per, variante):
    f1s, macros, briers, ts = [], [], [], []
    for fold in oc.FOLDS:
        t, _, p_va, p_ev, y_ev = oc.correr_fold(X, y, cat, per, fold, PARAMS)
        m = oc.metricas_eval(p_ev, y_ev, t)
        f1s.append(m["f1_baja"]); macros.append(m["f1_macro"]); briers.append(m["brier"]); ts.append(t)
    return {"variante": variante,
            "f1_baja_folds": [round(v, 4) for v in f1s],
            "media": round(float(np.mean(f1s)), 4),
            "desv": round(float(np.std(f1s, ddof=0)), 4),
            "f1_macro_medio": round(float(np.mean(macros)), 4),
            "brier_medio": round(float(np.mean(briers)), 4),
            "umbrales": ts}


def main() -> int:
    df, feats = oc.cargar()
    lags = construir_lags(df)
    cols_l1 = [c for c in lags.columns if c.endswith("_lag1")] + ["lag1_disponible"]
    cols_l2 = [c for c in lags.columns if c.endswith("_lag2")] + ["lag2_disponible"]
    print(f"base: {len(feats)} features | lag1: {len(cols_l1)} | lag2: {len(cols_l2)}")
    print(f"cobertura lag1: {lags['lag1_disponible'].mean():.1%} | "
          f"cobertura lag2: {lags['lag2_disponible'].mean():.1%}")

    Xb = oc.matriz(df, feats)
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    variantes = {
        "base_172": Xb,
        "lag1": np.column_stack([Xb, lags[cols_l1].to_numpy("float32")]),
        "lag2": np.column_stack([Xb, lags[cols_l2].to_numpy("float32")]),
        "ambos_lags": np.column_stack([Xb, lags[cols_l1 + cols_l2].to_numpy("float32")]),
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
    toca = bool(mejor["media"] >= BASE_F1 + DELTA)
    print("CUMPLE: se documenta plan de test." if toca else "NO cumple: test NO se toca.")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "M_lags_dos_periodos",
        "n_base": len(feats), "n_lag1": len(cols_l1), "n_lag2": len(cols_l2),
        "columnas_rezagadas": list(COLS.values()),
        "cobertura_lag1": round(float(lags["lag1_disponible"].mean()), 4),
        "cobertura_lag2": round(float(lags["lag2_disponible"].mean()), 4),
        "config": {k: PARAMS[k] for k in ("n_estimators", "min_child_weight", "gamma",
                                          "subsample", "max_depth", "learning_rate")},
        "variantes": resultados, "mejor": mejor,
        "base_f1_baja_oos": BASE_F1, "delta_pp": round(100 * (mejor["media"] - BASE_F1), 2),
        "criterio_test": round(BASE_F1 + DELTA, 4), "toco_test": toca, "test": None,
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("expM_lags_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
