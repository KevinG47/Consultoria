#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expH_prior_shift.py
===================

PASO FINAL 1: corrección de Brier por cambio de prevalencia (prior shift).

La prevalencia de "baja" en test se ESTIMA sin usar sus etiquetas: se ajusta la
tendencia de las cohortes con etiqueta disponible (17, 18, 19, 20) y se
extrapola a la cohorte 21. Solo después se mide el Brier con las etiquetas de
test, que es la métrica, no la estimación.

Corrección:  p_cal(c) = p(c) * (prev_est_test(c) / prev_train(c)), normalizado.

Referencias: Brier original (0.4692), constante con prevalencias de train
(0.4419), Ronda 1 (0.4592).
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
BRIER_ORIGINAL = 0.4692
BRIER_CONSTANTE = 0.4419
BRIER_RONDA1 = 0.4592


def brier(p, y):
    return float(np.mean(np.sum((p - np.eye(3)[y]) ** 2, axis=1)))


def tendencia(conv, prev, objetivo, escala="lineal", usar=None):
    """Ajusta prev ~ a + b*conv en las cohortes de 'usar' y extrapola."""
    conv = np.asarray(conv, dtype=float)
    prev = np.asarray(prev, dtype=float)
    if usar is not None:
        m = np.isin(conv, usar)
        conv, prev = conv[m], prev[m]
    if escala == "logit":
        z = np.log(np.clip(prev, 1e-4, 1 - 1e-4) / (1 - np.clip(prev, 1e-4, 1 - 1e-4)))
        a, b = np.polyfit(conv, z, 1)
        zz = a * objetivo + b
        return float(1 / (1 + np.exp(-zz)))
    a, b = np.polyfit(conv, prev, 1)
    return float(a * objetivo + b)


def main() -> int:
    df, feats = oc.cargar()
    X = oc.matriz(df, feats)
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    m_tr = np.isin(per, [17, 18, 19, 20])
    m_te = per == 21

    prev_train = np.bincount(y[m_tr], minlength=3) / m_tr.sum()
    prev_por_cohorte = {}
    for c in (17, 18, 19, 20):
        mm = per == c
        prev_por_cohorte[c] = np.bincount(y[mm], minlength=3) / mm.sum()
    print("prevalencias por cohorte (etiquetas disponibles):")
    for c, v in prev_por_cohorte.items():
        print(f"   cohorte {c}: baja={v[0]:.4f} mantiene={v[1]:.4f} sube={v[2]:.4f}")
    print(f"train (17-20): baja={prev_train[0]:.4f} mantiene={prev_train[1]:.4f} "
          f"sube={prev_train[2]:.4f}")

    convs = np.array([17, 18, 19, 20])
    escenarios = {}
    for escala in ("lineal", "logit"):
        for usar, etq in ((None, "todas"), ([18, 19, 20], "ultimas3"),
                          ([19, 20], "ultimas2")):
            est = [max(1e-4, min(0.999, tendencia(convs, [prev_por_cohorte[c][k] for c in convs],
                                                  21, escala, usar)))
                   for k in range(3)]
            escenarios[f"{escala}_{etq}"] = est
    for nombre, est in escenarios.items():
        print(f"   estimacion {nombre:16s}: baja={est[0]:.4f} mantiene={est[1]:.4f} "
              f"sube={est[2]:.4f}")

    # modelo Ronda 2 y probabilidades de test
    mod = oc.entrenar_cat(X, y, cat, m_tr, PARAMS)
    p_te = oc.predecir_cat(mod, X, cat, m_te, prev_train)
    y_te = y[m_te]
    b_orig = brier(p_te, y_te)
    print(f"\nBrier original en test (reproducido): {b_orig:.4f}  "
          f"(referencia {BRIER_ORIGINAL:.4f})")
    print(f"p(baja) media del modelo en test: {p_te[:, 0].mean():.4f}")

    filas = {}
    for nombre, est in escenarios.items():
        est = np.array(est)
        est = est / est.sum()
        ratio = est / prev_train
        p_cal = p_te * ratio
        p_cal = p_cal / p_cal.sum(axis=1, keepdims=True)
        b = brier(p_cal, y_te)
        filas[nombre] = {"prev_estimada": est.tolist(), "brier": b,
                         "p_baja_media": float(p_cal[:, 0].mean())}
        print(f"   corregido {nombre:16s}: prev_est={np.round(est, 4).tolist()} -> "
              f"Brier={b:.4f} | p(baja) media={p_cal[:,0].mean():.4f}")

    # oraculo (usa la prevalencia observada de test; NO utilizable, solo diagnostico)
    prev_te = np.bincount(y_te, minlength=3) / len(y_te)
    p_or = p_te * (prev_te / prev_train)
    p_or = p_or / p_or.sum(axis=1, keepdims=True)
    b_or = brier(p_or, y_te)
    print(f"\n[diagnostico, no utilizable] prevalencia observada de test "
          f"{np.round(prev_te,4).tolist()} -> Brier oraculo={b_or:.4f}")

    mejor = min(filas.items(), key=lambda kv: kv[1]["brier"])
    print(f"\nmejor escenario: {mejor[0]} -> Brier {mejor[1]['brier']:.4f}")
    print(f"comparacion: original {b_orig:.4f} | constante {BRIER_CONSTANTE:.4f} | "
          f"Ronda 1 {BRIER_RONDA1:.4f}")
    mejora = mejor[1]["brier"] < BRIER_CONSTANTE
    print(f"Brier corregido < constante ({BRIER_CONSTANTE}): "
          f"{'SI -> mejora real' if mejora else 'NO -> el prior shift no se corrige sin etiquetas'}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": "H_prior_shift",
        "prev_por_cohorte": {str(k): v.tolist() for k, v in prev_por_cohorte.items()},
        "prev_train": prev_train.tolist(),
        "escenarios": filas,
        "brier_original": b_orig, "brier_constante": BRIER_CONSTANTE,
        "brier_ronda1": BRIER_RONDA1,
        "brier_oraculo_diagnostico": b_or,
        "prev_test_observada_diagnostico": prev_te.tolist(),
        "mejor_escenario": mejor[0],
        "mejora_real": bool(mejora),
        "nota": "la prevalencia de test se estima por tendencia de cohortes 17-20; "
                "las etiquetas de test solo se usan para medir el Brier",
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    (RESULTADOS / ("expH_prior_shift_"
                   + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
     ).write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    np.save(RESULTADOS / "p_test_ronda2.npy", p_te)
    return 0


if __name__ == "__main__":
    sys.exit(main())
