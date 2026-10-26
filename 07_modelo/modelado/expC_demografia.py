#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expC_demografia.py
==================

EXPERIMENTO C: anadir demografia (genero, edad, departamento, institucion)
con la mejor config del A y el mejor tamano de feature set del B.

Compara, en los 3 folds temporales, el mismo modelo con y sin demografia.
Si sube >= 2 pp en F1 'baja' OOS medio, se queda.

Uso: <python> 07_modelo/modelado/expC_demografia.py
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
    exp_a = json.loads(sorted(RESULTADOS.glob("expA_grid_*.json"))[-1]
                       .read_text(encoding="utf-8"))
    exp_b = json.loads(sorted(RESULTADOS.glob("expB_features_*.json"))[-1]
                       .read_text(encoding="utf-8"))
    mejorA = exp_a["mejor"]
    k = int(exp_b["mejor_k"])
    params = dict(oc.BASE, n_estimators=mejorA["n_estimators"],
                  min_child_weight=mejorA["min_child_weight"],
                  gamma=mejorA["gamma"], subsample=mejorA["subsample"],
                  max_depth=7, learning_rate=0.05)
    print(f"config A: n_est={params['n_estimators']} mcw={params['min_child_weight']} "
          f"gamma={params['gamma']} sub={params['subsample']} | features top {k}")

    df, feats = oc.cargar()
    X = oc.matriz(df, feats)
    demo = oc.demo_features(df)
    Xd = demo.to_numpy(dtype="float32")
    cols_demo = list(demo.columns)
    print(f"demografia: {len(cols_demo)} columnas -> {cols_demo}")
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    res = {}
    for etiqueta, usar_demo in (("sin_demografia", False), ("con_demografia", True)):
        f1s, macros, briers, ts = [], [], [], []
        for fold in oc.FOLDS:
            _, tr_p, va_p, ev_p = fold
            m_tr = np.isin(per, tr_p)
            prev = np.bincount(y[m_tr], minlength=3) / m_tr.sum()
            mod_full = oc.entrenar_cat(X, y, cat, m_tr, params)
            gain = oc.ganancias(mod_full, len(feats))
            idx = np.argsort(-gain)[:k] if k < len(feats) else np.arange(len(feats))
            Xb = X[:, idx]
            Xf = np.column_stack([Xb, Xd]) if usar_demo else Xb
            mod = oc.entrenar_cat(Xf, y, cat, m_tr, params)
            m_va = per == va_p[0]
            m_ev = per == ev_p[0]
            p_va = oc.predecir_cat(mod, Xf, cat, m_va, prev)
            p_ev = oc.predecir_cat(mod, Xf, cat, m_ev, prev)
            t, _ = oc.mejor_t_baja(p_va[:, 0], y[m_va])
            m = oc.metricas_eval(p_ev, y[m_ev], t)
            f1s.append(m["f1_baja"])
            macros.append(m["f1_macro"])
            briers.append(m["brier"])
            ts.append(t)
        res[etiqueta] = {"f1_baja_folds": [round(v, 4) for v in f1s],
                         "media": round(float(np.mean(f1s)), 4),
                         "desv": round(float(np.std(f1s, ddof=0)), 4),
                         "f1_macro_medio": round(float(np.mean(macros)), 4),
                         "brier_medio": round(float(np.mean(briers)), 4),
                         "umbrales": ts}
        print(f"   {etiqueta:15s} -> folds {res[etiqueta]['f1_baja_folds']} | "
              f"media={res[etiqueta]['media']:.4f} desv={res[etiqueta]['desv']:.4f} | "
              f"F1macro={res[etiqueta]['f1_macro_medio']:.4f} "
              f"Brier={res[etiqueta]['brier_medio']:.4f}")

    delta = 100 * (res["con_demografia"]["media"] - res["sin_demografia"]["media"])
    mejora = delta >= 2.0
    print(f"\n   delta F1 'baja' OOS al anadir demografia: {delta:+.2f} pp -> "
          f"{'SE QUEDA' if mejora else 'NO SE QUEDA'} (criterio >= 2 pp)")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "C", "config_A": mejorA, "top_k": k,
        "columnas_demografia": cols_demo,
        "resultados": res, "delta_pp": round(delta, 2),
        "se_queda": bool(mejora), "criterio_pp": 2.0,
    }
    salida = RESULTADOS / ("expC_demografia_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
