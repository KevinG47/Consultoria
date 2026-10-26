#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
paso2_calibrar_xgb.py
=====================

PASO 2: calibracion del XGBoost r1 con CalibratedClassifierCV(sigmoid).

El calibrador se ajusta sobre VAL (prefit del modelo r1) y se evalua sobre el
mismo VAL: es una calibracion EN MUESTRA, util para planificar, y asi se
declara. El test no se toca.

Reporta Brier, F1 macro, F1 por clase y AUC antes/despues.

Uso: <python> 07_modelo/modelado/paso2_calibrar_xgb.py
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
CONSTANTE_BRIER = 0.4510   # constante con prevalencias de val (calculado en paso 1/verif)


def main() -> int:
    import pandas as pd
    from sklearn.calibration import CalibratedClassifierCV

    try:
        from sklearn.frozen import FrozenEstimator
        api = "FrozenEstimator"
        cal = None
    except ImportError:  # sklearn < 1.6
        FrozenEstimator = None
        api = "cv='prefit'"

    xgb, X_val, y, feats, val = mu.cargar_xgb_r1(pd)
    print(f"xgboost r1 cargado | features {len(feats)} | n_val={len(y)}")
    p_antes = xgb.predict_proba(X_val)
    m_antes = mu.metricas_completas(p_antes, y)

    print("\n--- ANTES (r1 sin calibrar) ---")
    print(f"   Brier={m_antes['brier']:.4f} | F1 macro={m_antes['f1_macro']:.4f} | "
          f"F1 baja={m_antes['f1_por_clase']['baja']:.4f} | "
          f"F1 mantiene={m_antes['f1_por_clase']['se_mantiene']:.4f} | "
          f"F1 sube={m_antes['f1_por_clase']['sube']:.4f}")
    print(f"   AUC baja={m_antes['auc_ovr']['baja']:.4f} | "
          f"mantiene={m_antes['auc_ovr']['se_mantiene']:.4f} | "
          f"sube={m_antes['auc_ovr']['sube']:.4f}")

    if FrozenEstimator is not None:
        cal = CalibratedClassifierCV(FrozenEstimator(xgb), method="sigmoid")
    else:
        cal = CalibratedClassifierCV(xgb, method="sigmoid", cv="prefit")
    cal.fit(X_val, y)
    p_desp = cal.predict_proba(X_val)
    m_desp = mu.metricas_completas(p_desp, y)

    print(f"\n--- DESPUES (sigmoid, ajustado en val; API {api}) ---")
    print(f"   Brier={m_desp['brier']:.4f} (antes {m_antes['brier']:.4f}) | "
          f"F1 macro={m_desp['f1_macro']:.4f} (antes {m_antes['f1_macro']:.4f})")
    print(f"   F1 baja={m_desp['f1_por_clase']['baja']:.4f} | "
          f"F1 mantiene={m_desp['f1_por_clase']['se_mantiene']:.4f} | "
          f"F1 sube={m_desp['f1_por_clase']['sube']:.4f}")
    print(f"   AUC baja={m_desp['auc_ovr']['baja']:.4f} (antes {m_antes['auc_ovr']['baja']:.4f}) | "
          f"mantiene={m_desp['auc_ovr']['se_mantiene']:.4f} | sube={m_desp['auc_ovr']['sube']:.4f}")

    m_umbral, _ = mu.umbral_baja(p_desp, y)
    print(f"\n   umbral F1 baja optimizado: t={m_umbral['umbral']:.2f} -> "
          f"F1 baja={m_umbral['f1_baja_umbral']:.4f} (prec {m_umbral['precision_baja_umbral']:.4f}, "
          f"rec {m_umbral['recall_baja_umbral']:.4f})")
    print(f"   aceptable para planificar (Brier < {CONSTANTE_BRIER}): "
          + ("SI" if m_desp["brier"] < CONSTANTE_BRIER else "NO"))

    np.save(RESULTADOS / "p_xgb_cal.npy", p_desp)
    np.save(RESULTADOS / "p_xgb_r1.npy", p_antes)

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": 2,
        "api_calibracion": api,
        "metodo": "sigmoid",
        "ajuste_calibrador": "sobre val (en muestra); declarado",
        "n_val": int(len(y)), "n_features": len(feats),
        "antes": m_antes, "despues": m_desp,
        "umbral_f1_baja": m_umbral,
        "constante_brier_referencia": CONSTANTE_BRIER,
        "aceptable_para_planificar": bool(m_desp["brier"] < CONSTANTE_BRIER),
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("paso2_xgb_calibrado_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
