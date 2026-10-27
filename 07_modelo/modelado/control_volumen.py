#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
control_volumen.py
==================

Control del benchmark B: separa el efecto "identidad" del efecto "menos datos".

B entrena con 5 005 filas (17-19 sin personas de val ni test). Este control
entrena con OTRA muestra de 5 005 filas del mismo pool, pero SIN excluir
personas, y evalua con el mismo val y el mismo test que B.

  - Si control ~ B  -> la caida se explica por el volumen de datos, no por la identidad.
  - Si control >> B -> hay un efecto de identidad adicional.

No modifica el modelo operativo.
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
N = 5005


def main() -> int:
    df, feats = oc.cargar()
    X = oc.matriz(df, feats)
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    persona = df["ID_PERSONA_PR"].astype(str).to_numpy()

    m_ev = per == 21
    m_va = per == 20
    m_tr = np.isin(per, [17, 18, 19])
    ids_ev = set(persona[m_ev])
    m_va_cold = m_va & ~np.isin(persona, list(ids_ev))
    # el control NO excluye personas: usa el pool completo de 17-19
    m_tr_pool = m_tr.copy()

    rng = np.random.default_rng(42)
    pool = np.flatnonzero(m_tr_pool)
    sub = rng.choice(pool, size=min(N, len(pool)), replace=False)
    m_tr_ctrl = np.zeros_like(m_tr)
    m_tr_ctrl[sub] = True

    print("=== Control de volumen (misma muestra que B, sin excluir identidad) ===")
    print(f"pool de B: {len(pool)} filas | muestra de control: {int(m_tr_ctrl.sum())}")

    prior = np.bincount(y[m_tr_ctrl], minlength=3) / m_tr_ctrl.sum()
    modelos = oc.entrenar_cat(X, y, cat, m_tr_ctrl, PARAMS)
    p_va = oc.predecir_cat(modelos, X, cat, m_va_cold, prior)
    p_ev = oc.predecir_cat(modelos, X, cat, m_ev, prior)
    t, f1_va = oc.mejor_t_baja(p_va[:, 0], y[m_va_cold])
    m = oc.metricas_eval(p_ev, y[m_ev], t)
    print(f"control: train={int(m_tr_ctrl.sum())} val={int(m_va_cold.sum())} eval={int(m_ev.sum())} "
          f"| F1 baja={m['f1_baja']:.4f} | recall={m['recall_baja']:.4f} | "
          f"precision={m['precision_baja']:.4f} | macro={m['f1_macro']:.4f} | brier={m['brier']:.4f} | t={t:.2f}")
    print(f"B (cold)  : F1 baja 0,4016 | recall 0,6153 | precision 0,2981 | macro 0,4412 | brier 0,4969 | t=0,17")
    print(f"A (opera.) : F1 baja 0,4234 | recall 0,7878 | precision 0,2895 | macro 0,5109 | brier 0,4692 | t=0,15")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "control_volumen",
        "n_train": int(m_tr_ctrl.sum()), "n_val": int(m_va_cold.sum()), "n_eval": int(m_ev.sum()),
        "umbral": float(t), "metricas": m,
        "referencia_B": {"f1_baja": 0.4016, "recall": 0.6153, "precision": 0.2981,
                         "f1_macro": 0.4412, "brier": 0.4969},
        "referencia_A": {"f1_baja": 0.4234, "recall": 0.7878, "precision": 0.2895,
                         "f1_macro": 0.5109, "brier": 0.4692},
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    p = RESULTADOS / ("control_volumen_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    p.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
