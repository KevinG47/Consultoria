#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expF_trayectoria.py
===================

Última ronda: features de trayectoria sobre el XGBoost con máscaras.

- Config fija de la ronda 2: n_est=100, mcw=1, gamma=0.1, sub=0.8.
- 3 folds temporales: F1 17->18->19, F2 17,18->19->20, F3 18->19->20.
- Ablación: cada feature nueva por separado, el par de historial, y todas.
- Test SOLO si la mejor config supera 0.2985 + 2 pp = 0.3185.
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
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
BASE_F1 = 0.2985
DELTA = 0.02
ANTERIOR = {"f1_baja": 0.4234, "recall": 0.7878, "precision": 0.2895,
            "f1_macro": 0.5109, "brier": 0.4692}
PARAMS = dict(oc.BASE, n_estimators=100, min_child_weight=1, gamma=0.1,
              subsample=0.8, max_depth=7, learning_rate=0.05)

NUEVAS = {
    "a_tiempo": ["tiempo_en_categoria"],
    "b_historial": ["historial_bajas", "historial_subidas"],
    "c_momentum": ["momentum_produccion"],
    "d_normalizada": ["produccion_normalizada"],
    "todas": ["tiempo_en_categoria", "historial_bajas", "historial_subidas",
              "momentum_produccion", "produccion_normalizada"],
}


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
    import pandas as pd

    df, feats = oc.cargar()
    tray = pd.read_parquet(DERIVADOS / "trayectoria_features.parquet")
    tray["ID_PERSONA_PR"] = tray["ID_PERSONA_PR"].astype(str)
    df = df.merge(tray, on=["ID_PERSONA_PR", "ID_CONVOCATORIA"], how="left",
                  validate="one_to_one")
    nuevas = [c for c in tray.columns if c not in ("ID_PERSONA_PR", "ID_CONVOCATORIA")]
    print(f"base: {len(feats)} features | nuevas: {len(nuevas)} -> total {len(feats)+len(nuevas)}")
    assert df[nuevas].isna().sum().sum() == 0, "hay nulos en features de trayectoria"

    Xb = oc.matriz(df, feats)
    Xn = df[nuevas].to_numpy(dtype="float32")
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    resultados = {"sin_nuevas": correr(Xb, y, cat, per, "sin_nuevas (172)")}
    print(f"\n{'variante':20s} {'folds':28s} {'media':>6} {'desv':>6} {'F1macro':>8} {'Brier':>7}  t")
    f = resultados["sin_nuevas"]
    print(f"{f['variante']:20s} {str(f['f1_baja_folds']):28s} {f['media']:>6.4f} "
          f"{f['desv']:>6.4f} {f['f1_macro_medio']:>8.4f} {f['brier_medio']:>7.4f}  {f['umbrales']}")

    for nombre, cols in NUEVAS.items():
        idx = [nuevas.index(c) for c in cols]
        X = np.column_stack([Xb, Xn[:, idx]])
        r = correr(X, y, cat, per, f"{nombre} (+{len(cols)})")
        resultados[nombre] = r
        print(f"{r['variante']:20s} {str(r['f1_baja_folds']):28s} {r['media']:>6.4f} "
              f"{r['desv']:>6.4f} {r['f1_macro_medio']:>8.4f} {r['brier_medio']:>7.4f}  {r['umbrales']}")

    orden = sorted([v for k, v in resultados.items() if k != "sin_nuevas"],
                   key=lambda r: -r["media"])
    mejor = orden[0]
    print(f"\nMEJOR con trayectoria: {mejor['variante']} -> media {mejor['media']:.4f} "
          f"(base {BASE_F1:.4f}, delta {100*(mejor['media']-BASE_F1):+.2f} pp)")
    print(f"criterio para tocar test: media >= {BASE_F1 + DELTA:.4f}")

    toca_test = bool(mejor["media"] >= BASE_F1 + DELTA)
    salida_test = None
    if toca_test:
        print("\n*** CUMPLE: se evaluará en test UNA SOLA VEZ ***")
        cols = NUEVAS[mejor["variante"].split(" (+")[0]] if mejor["variante"] != "todas" else NUEVAS["todas"]
        idx = [nuevas.index(c) for c in cols]
        X = np.column_stack([Xb, Xn[:, idx]])
        m_tr = np.isin(per, [17, 18, 19, 20])
        m_te = per == 21
        prev = np.bincount(y[m_tr], minlength=3) / m_tr.sum()
        mod = oc.entrenar_cat(X, y, cat, m_tr, PARAMS)
        p_te = oc.predecir_cat(mod, X, cat, m_te, prev)
        t_med = float(np.median(mejor["umbrales"]))
        m = oc.metricas_eval(p_te, y[m_te], t_med)
        print(f"   TEST (t={t_med:.2f}): F1 baja={m['f1_baja']:.4f} | recall={m['recall_baja']:.4f} "
              f"| precision={m['precision_baja']:.4f} | F1 macro={m['f1_macro']:.4f} "
              f"| Brier={m['brier']:.4f}")
        print(f"   vs ronda 2: F1 baja {m['f1_baja']-ANTERIOR['f1_baja']:+.4f} | "
              f"recall {m['recall_baja']-ANTERIOR['recall']:+.4f} | "
              f"macro {m['f1_macro']-ANTERIOR['f1_macro']:+.4f} | "
              f"Brier {m['brier']-ANTERIOR['brier']:+.4f}")
        salida_test = {"umbral": t_med, "metricas": m, "variante": mejor["variante"],
                       "features_nuevas": cols, "anterior": ANTERIOR,
                       "mejora_f1_baja": m["f1_baja"] - ANTERIOR["f1_baja"]}
    else:
        print("NO cumple el +2 pp: test NO se toca. Las features de trayectoria no "
              "aportan; el modelo actual es el techo del dato.")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "F", "n_base": len(feats), "n_nuevas": len(nuevas),
        "n_total": len(feats) + len(nuevas),
        "nota_n": "las 4 features conceptuales ocupan 5 columnas (historial_bajas y "
                  "historial_subidas van separadas)",
        "config": {k: PARAMS[k] for k in ("n_estimators", "min_child_weight",
                                          "gamma", "subsample", "max_depth",
                                          "learning_rate")},
        "resultados": resultados, "mejor": mejor,
        "base_f1_baja_oos": BASE_F1, "delta_pp": round(100 * (mejor["media"] - BASE_F1), 2),
        "criterio_test": round(BASE_F1 + DELTA, 4), "toco_test": toca_test,
        "test": salida_test,
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("expF_trayectoria_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
