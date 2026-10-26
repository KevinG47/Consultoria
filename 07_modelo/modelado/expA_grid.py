#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expA_grid.py
============

EXPERIMENTO A: grid de regularizacion + n_estimators, 3 folds temporales
(todos pre-test). 3 x 3 x 3 x 2 = 54 combinaciones.

Uso: <python> 07_modelo/modelado/expA_grid.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import opt_comun as oc  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"


def main() -> int:
    df, feats = oc.cargar()
    X = oc.matriz(df, feats)
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    print(f"features={len(feats)} | filas={len(df)} | folds="
          + " ".join(f"{f[0]}[{f[1]}->{f[2]}->{f[3]}]" for f in oc.FOLDS))

    combos = [(n, mcw, g, s)
              for n in (100, 150, 200)
              for mcw in (1, 5, 10)
              for g in (0.0, 0.1, 0.3)
              for s in (0.8, 1.0)]
    print(f"combinaciones: {len(combos)}\n")
    print(f"{'#':>3} {'n_est':>5} {'mcw':>4} {'gamma':>5} {'sub':>4} | "
          f"{'F1baja_F1':>9} {'F1baja_F2':>9} {'F1baja_F3':>9} | "
          f"{'media':>6} {'desv':>6} {'F1macro':>7} {'Brier':>6} {'t(F1,F2,F3)'}")

    t0 = time.time()
    filas = []
    for i, (n, mcw, g, s) in enumerate(combos, 1):
        params = dict(oc.BASE, n_estimators=n, min_child_weight=mcw,
                      gamma=g, subsample=s, max_depth=7, learning_rate=0.05)
        f1s, ts, macros, briers = [], [], [], []
        for fold in oc.FOLDS:
            t, f1_va, p_va, p_ev, y_ev = oc.correr_fold(X, y, cat, per, fold, params)
            m = oc.metricas_eval(p_ev, y_ev, t)
            f1s.append(m["f1_baja"])
            macros.append(m["f1_macro"])
            briers.append(m["brier"])
            ts.append(t)
        media, desv = float(np.mean(f1s)), float(np.std(f1s, ddof=0))
        fila = {"i": i, "n_estimators": n, "min_child_weight": mcw,
                "gamma": g, "subsample": s,
                "f1_baja_folds": [round(v, 4) for v in f1s],
                "media": round(media, 4), "desv": round(desv, 4),
                "f1_macro_medio": round(float(np.mean(macros)), 4),
                "brier_medio": round(float(np.mean(briers)), 4),
                "umbrales": [round(v, 2) for v in ts]}
        filas.append(fila)
        print(f"{i:>3} {n:>5} {mcw:>4} {g:>5.1f} {s:>4.1f} | "
              f"{f1s[0]:>9.4f} {f1s[1]:>9.4f} {f1s[2]:>9.4f} | "
              f"{media:>6.4f} {desv:>6.4f} {fila['f1_macro_medio']:>7.4f} "
              f"{fila['brier_medio']:>6.4f} {ts}")

    seg = time.time() - t0
    orden = sorted(filas, key=lambda f: (-f["media"], f["desv"]))
    print(f"\n=== TOP 10 por media de F1 'baja' OOS ({seg/60:.1f} min) ===")
    for f in orden[:10]:
        print(f"   n_est={f['n_estimators']:>3} mcw={f['min_child_weight']:>2} "
              f"gamma={f['gamma']:.1f} sub={f['subsample']:.1f} -> "
              f"media={f['media']:.4f} desv={f['desv']:.4f} "
              f"F1macro={f['f1_macro_medio']:.4f} Brier={f['brier_medio']:.4f}")
    mejor = orden[0]
    print(f"\nMEJOR: n_estimators={mejor['n_estimators']} min_child_weight="
          f"{mejor['min_child_weight']} gamma={mejor['gamma']} "
          f"subsample={mejor['subsample']} (media {mejor['media']:.4f}, "
          f"desv {mejor['desv']:.4f})")

    # linea base de la ronda anterior (200, 1, 0, 0.8) con estos folds
    ref = next(f for f in filas if (f["n_estimators"], f["min_child_weight"],
                                    f["gamma"], f["subsample"]) == (200, 1, 0.0, 0.8))
    print(f"referencia (200,1,0,0.8) en estos folds: media={ref['media']:.4f} "
          f"desv={ref['desv']:.4f}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "A", "n_features": len(feats),
        "folds": [{"nombre": f[0], "train": f[1], "val": f[2], "eval": f[3]}
                  for f in oc.FOLDS],
        "combinaciones": filas,
        "mejor": mejor,
        "referencia_200_1_0_08": ref,
        "segundos": round(seg, 1),
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("expA_grid_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
