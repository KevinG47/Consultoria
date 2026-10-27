#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
benchmark_B.py
==============

Benchmark B: entidad disjunta (cold start) sobre el mismo diseno temporal.

Regla: en cada particion, se eliminan del train y de la validacion las personas
que aparecen en el conjunto de evaluacion; y de la validacion, las del train.
Asi ningun ID_PERSONA_PR se reparte entre conjuntos.

  - B en folds: F1, F2, F3 (misma config Ronda 2, umbral elegido en validacion cold).
  - B en test (diagnostico, etiquetado como tal): train 17-19 cold, val 20 cold,
    eval 21.
  - A de referencia: folds 0,2985 (media) y test 0,4234 (modelo operativo, ya medido).

NO se modifica ni se reentrena el modelo operativo.
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
PARAMS = dict(oc.BASE, n_estimators=100, min_child_weight=1, gamma=0.1,
              subsample=0.8, max_depth=7, learning_rate=0.05)
A_FOLDS = 0.2985
A_TEST = 0.4234


def evaluar_cold(X, y, cat, per, persona, tr_p, va_p, ev_p, nombre):
    m_tr = np.isin(per, tr_p)
    m_va = per == va_p
    m_ev = per == ev_p
    ids_ev = set(persona[m_ev])
    ids_va = set(persona[m_va])
    m_tr_cold = m_tr & ~np.isin(persona, list(ids_ev | ids_va))
    m_va_cold = m_va & ~np.isin(persona, list(ids_ev))
    prior = np.bincount(y[m_tr_cold], minlength=3) / m_tr_cold.sum()
    modelos = oc.entrenar_cat(X, y, cat, m_tr_cold, PARAMS)
    p_va = oc.predecir_cat(modelos, X, cat, m_va_cold, prior)
    p_ev = oc.predecir_cat(modelos, X, cat, m_ev, prior)
    t, f1_va = oc.mejor_t_baja(p_va[:, 0], y[m_va_cold])
    m = oc.metricas_eval(p_ev, y[m_ev], t)
    return {"conjunto": nombre,
            "n_train": int(m_tr_cold.sum()), "n_val": int(m_va_cold.sum()),
            "n_eval": int(m_ev.sum()),
            "personas_eval_sin_historia": int(len(set(persona[m_ev]) - set(persona[m_tr_cold]))),
            "umbral": float(t), "f1_val": round(float(f1_va), 4),
            "f1_baja": round(float(m["f1_baja"]), 4),
            "recall": round(float(m["recall_baja"]), 4),
            "precision": round(float(m["precision_baja"]), 4),
            "f1_macro": round(float(m["f1_macro"]), 4),
            "brier": round(float(m["brier"]), 4)}


def main() -> int:
    df, feats = oc.cargar()
    X = oc.matriz(df, feats)
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    persona = df["ID_PERSONA_PR"].astype(str).to_numpy()

    print("=== Benchmark B: entidad disjunta (cold start) ===")
    print(f"base {len(feats)} features | config Ronda 2 | A folds={A_FOLDS:.4f} A test={A_TEST:.4f}")

    filas = []
    for nombre, tr_p, va_p, ev_p in oc.FOLDS:
        r = evaluar_cold(X, y, cat, per, persona, tr_p, va_p, ev_p[0], nombre)
        filas.append(r)
        print(f"  {nombre}: train={r['n_train']:6d} val={r['n_val']:5d} eval={r['n_eval']:5d} "
              f"| F1 baja={r['f1_baja']:.4f} | t={r['umbral']:.2f} | macro={r['f1_macro']:.4f}")

    media_b = float(np.mean([r["f1_baja"] for r in filas]))
    desv_b = float(np.std([r["f1_baja"] for r in filas], ddof=0))
    print(f"\nB folds: media {media_b:.4f} (desv {desv_b:.4f}) | A folds {A_FOLDS:.4f} "
          f"| delta {100*(A_FOLDS-media_b):+.2f} pp")

    r_test = evaluar_cold(X, y, cat, per, persona, [17, 18, 19], 20, 21, "TEST_2021")
    print(f"  TEST: train={r_test['n_train']} val={r_test['n_val']} eval={r_test['n_eval']} "
          f"| F1 baja={r_test['f1_baja']:.4f} | t={r_test['umbral']:.2f} | "
          f"macro={r_test['f1_macro']:.4f} | brier={r_test['brier']:.4f}")
    delta_test = A_TEST - r_test["f1_baja"]
    print(f"  delta A-B en test: {100*delta_test:+.2f} pp")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "B_entidad_disjunta",
        "definicion": "temporal + sin ID_PERSONA_PR compartido entre train, val y eval",
        "config": {k: PARAMS[k] for k in ("n_estimators", "min_child_weight", "gamma",
                                          "subsample", "max_depth", "learning_rate")},
        "folds": filas, "folds_media": round(media_b, 4), "folds_desv": round(desv_b, 4),
        "a_folds": A_FOLDS, "delta_folds_pp": round(100 * (A_FOLDS - media_b), 2),
        "test": r_test, "a_test": A_TEST, "delta_test_pp": round(100 * delta_test, 2),
        "nota": "el test se usa aqui solo como diagnostico de B; el modelo operativo "
                "sigue siendo la Ronda 2 y su evaluacion de test no se reutiliza para tuning",
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    p = RESULTADOS / ("benchmark_B_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    p.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
