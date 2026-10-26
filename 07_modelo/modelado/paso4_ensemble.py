#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
paso4_ensemble.py
=================

PASO 4: ensamble por promedio simple de probabilidades
        bayesiano minimo (ta=0.95) + XGBoost r1 calibrado (sigmoid, en val).

Reporta F1 macro, F1 por clase, AUC, Brier (argmax) y con umbral optimizado
de "baja" (metrica principal).

Uso: <python> 07_modelo/modelado/paso4_ensemble.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import metricas_umbral as mu  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"


def main() -> int:
    p_bayes, y, df, datos = mu.probabilidades_bayesiano()
    p_cal = np.load(RESULTADOS / "p_xgb_cal.npy")
    assert p_cal.shape == p_bayes.shape, (p_cal.shape, p_bayes.shape)
    p_ens = (p_bayes + p_cal) / 2.0
    np.save(RESULTADOS / "p_bayes.npy", p_bayes)
    np.save(RESULTADOS / "p_ens.npy", p_ens)

    for nombre, p in (("bayesiano", p_bayes), ("xgb_calibrado", p_cal),
                      ("ensamble", p_ens)):
        m = mu.metricas_completas(p, y)
        mb, _ = mu.umbral_baja(p, y)
        mm, _ = mu.pesos_macro(p, y)
        print(f"\n=== {nombre} ===")
        print(f"   argmax : F1 macro={m['f1_macro']:.4f} | "
              f"F1 baja={m['f1_por_clase']['baja']:.4f} | "
              f"F1 mantiene={m['f1_por_clase']['se_mantiene']:.4f} | "
              f"F1 sube={m['f1_por_clase']['sube']:.4f}")
        print(f"            AUC baja={m['auc_ovr']['baja']:.4f} | Brier={m['brier']:.4f}")
        print(f"   umbral baja t={mb['umbral']:.2f}: F1 baja={mb['f1_baja_umbral']:.4f} "
              f"(prec {mb['precision_baja_umbral']:.4f}, rec {mb['recall_baja_umbral']:.4f}) "
              f"| F1 macro={mb['f1_macro']:.4f}")
        print(f"   pesos F1macro w=({mm['w_baja']:.2f},{mm['w_sube']:.2f}): "
              f"F1 macro={mm['f1_macro']:.4f} | F1 baja={mm['f1_por_clase']['baja']:.4f}")

    m = mu.metricas_completas(p_ens, y)
    mb, _ = mu.umbral_baja(p_ens, y)
    mm, _ = mu.pesos_macro(p_ens, y)
    print("\n--- comparacion con las partes (F1 baja con umbral) ---")
    mb_b, _ = mu.umbral_baja(p_bayes, y)
    mb_c, _ = mu.umbral_baja(p_cal, y)
    print(f"   bayesiano {mb_b['f1_baja_umbral']:.4f} | xgb_cal {mb_c['f1_baja_umbral']:.4f} "
          f"| ensamble {mb['f1_baja_umbral']:.4f}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": 4, "modelo": "promedio simple bayesiano_minimo + xgb_r1_calibrado",
        "n_val": int(len(y)),
        "ensamble": {"argmax": m, "umbral_f1_baja": mb, "pesos_f1_macro": mm},
        "partes": {},
    }
    for k, p in (("bayesiano", p_bayes), ("xgb_calibrado", p_cal)):
        mk = mu.metricas_completas(p, y)
        mk_umbral, _ = mu.umbral_baja(p, y)
        resumen["partes"][k] = {
            "brier": mk["brier"],
            "f1_macro_argmax": mk["f1_macro"],
            "f1_baja_umbral": mk_umbral["f1_baja_umbral"],
            "umbral": mk_umbral["umbral"],
        }

    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("paso4_ensemble_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
