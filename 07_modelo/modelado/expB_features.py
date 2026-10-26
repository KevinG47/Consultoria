#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expB_features.py
================

EXPERIMENTO B: reduccion de features (top 50 / 80 / 120 por gain) con la
mejor configuracion del Experimento A, sobre los 3 folds temporales.

El top-k se calcula SOLO con el train de cada fold (gain agregado de los tres
modelos por categoria).

Uso: <python> 07_modelo/modelado/expB_features.py
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


def main() -> int:
    import pandas as pd

    exp_a = sorted(RESULTADOS.glob("expA_grid_*.json"))[-1]
    mejorA = json.loads(exp_a.read_text(encoding="utf-8"))["mejor"]
    params = dict(oc.BASE, n_estimators=mejorA["n_estimators"],
                  min_child_weight=mejorA["min_child_weight"],
                  gamma=mejorA["gamma"], subsample=mejorA["subsample"],
                  max_depth=7, learning_rate=0.05)
    print(f"config A: n_est={params['n_estimators']} mcw={params['min_child_weight']} "
          f"gamma={params['gamma']} sub={params['subsample']} (media {mejorA['media']:.4f})")

    df, feats = oc.cargar()
    X = oc.matriz(df, feats)
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    resultados = {}
    for k in (172, 120, 80, 50):
        f1s, macros, briers, ts, keeps = [], [], [], [], []
        for fold in oc.FOLDS:
            _, tr_p, va_p, ev_p = fold
            m_tr = np.isin(per, tr_p)
            prev = np.bincount(y[m_tr], minlength=3) / m_tr.sum()
            mod_full = oc.entrenar_cat(X, y, cat, m_tr, params)
            if k < len(feats):
                gain = oc.ganancias(mod_full, len(feats))
                idx = np.argsort(-gain)[:k]
            else:
                idx = np.arange(len(feats))
            Xk = X[:, idx]
            mod_k = oc.entrenar_cat(Xk, y, cat, m_tr, params)
            m_va = per == va_p[0]
            m_ev = per == ev_p[0]
            p_va = oc.predecir_cat(mod_k, Xk, cat, m_va, prev)
            p_ev = oc.predecir_cat(mod_k, Xk, cat, m_ev, prev)
            t, _ = oc.mejor_t_baja(p_va[:, 0], y[m_va])
            m = oc.metricas_eval(p_ev, y[m_ev], t)
            f1s.append(m["f1_baja"])
            macros.append(m["f1_macro"])
            briers.append(m["brier"])
            ts.append(t)
            keeps.append([feats[j] for j in idx[:5]])
        res = {"k": k, "f1_baja_folds": [round(v, 4) for v in f1s],
               "media": round(float(np.mean(f1s)), 4),
               "desv": round(float(np.std(f1s, ddof=0)), 4),
               "f1_macro_medio": round(float(np.mean(macros)), 4),
               "brier_medio": round(float(np.mean(briers)), 4),
               "umbrales": ts, "top5_por_fold": keeps}
        resultados[str(k)] = res
        print(f"   top {k:>3} features -> F1 baja OOS folds {res['f1_baja_folds']} | "
              f"media={res['media']:.4f} desv={res['desv']:.4f} | "
              f"F1macro={res['f1_macro_medio']:.4f} | Brier={res['brier_medio']:.4f} "
              f"| t={ts}")

    orden = sorted(resultados.values(), key=lambda r: (-r["media"], r["desv"]))
    mejor = orden[0]
    print(f"\nMEJOR: top {mejor['k']} features (media {mejor['media']:.4f}, "
          f"desv {mejor['desv']:.4f})")
    print(f"   referencia sin reduccion: media={resultados['172']['media']:.4f} "
          f"desv={resultados['172']['desv']:.4f}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "B", "config_A": mejorA, "resultados": resultados,
        "mejor_k": mejor["k"],
        "nota": "el top-k se calcula con el gain del train de cada fold",
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("expB_features_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
