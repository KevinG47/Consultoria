#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pasoB_baseline_prevalencia.py
=============================

PASO B: baseline trivial de prevalencia.

p(clase) = prevalencia de TRAIN (constante para todas las filas).
El umbral de "baja" se optimiza igual que en el XGBoost (sobre val 17->19)
y se evalua en la cohorte 19->21.

Uso: <python> 07_modelo/modelado/pasoB_baseline_prevalencia.py
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
import modelo_mascaras as mm  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"


def pred_umbral(p, t):
    return np.where(p[:, 0] >= t, 0, np.where(p[:, 1] >= p[:, 2], 1, 2))


def main() -> int:
    import joblib
    import pandas as pd

    contenedor = joblib.load(mu.MODELOS_DIR / "xgb_ventana_contiguo.joblib")
    feats = [f for f in contenedor["features"] if f != "ano"]
    df = mm.preparar(pd.read_parquet(SCRIPT_DIR.parent / "datos" / "derivados" /
                                     "modelo_dataset_ventana_contiguo.parquet"))
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    tr = df[np.isin(per, [17, 18, 19])]
    va = df[per == 20]
    ev = df[per == 21]

    prev = np.bincount(tr["y"].to_numpy(), minlength=3) / len(tr)
    print("prevalencias de train (17,18,19): "
          + " | ".join(f"{c}={v:.4f}" for c, v in zip(mm.CLASES, prev)))
    print("prevalencias reales: val(20)="
          + str(np.round(np.bincount(va['y'].to_numpy(), minlength=3) / len(va), 4).tolist())
          + " | test(21)="
          + str(np.round(np.bincount(ev['y'].to_numpy(), minlength=3) / len(ev), 4).tolist()))

    p_va = np.tile(prev, (len(va), 1))
    p_ev = np.tile(prev, (len(ev), 1))
    m_va, _ = mu.umbral_baja(p_va, va["y"].to_numpy())
    t = m_va["umbral"]
    y_ev = ev["y"].to_numpy()
    m_ev = mu.metricas_completas(p_ev, y_ev, pred_umbral(p_ev, t))
    m_ev_argmax = mu.metricas_completas(p_ev, y_ev)

    print(f"\n--- BASELINE de prevalencia (constante) ---")
    print(f"   val(20): umbral optimo t={t:.2f} -> F1 baja={m_va['f1_baja_umbral']:.4f} "
          f"(prec {m_va['precision_baja_umbral']:.4f}, rec {m_va['recall_baja_umbral']:.4f})")
    print(f"   test(21) con ese umbral: F1 baja={m_ev['f1_por_clase']['baja']:.4f} | "
          f"prec={m_ev['precision_baja']:.4f} | rec={m_ev['recall_baja']:.4f} | "
          f"F1 macro={m_ev['f1_macro']:.4f} | Brier={m_ev['brier']:.4f}")
    print(f"   test(21) argmax (todo 'se_mantiene'): F1 macro={m_ev_argmax['f1_macro']:.4f} "
          f"| F1 baja={m_ev_argmax['f1_por_clase']['baja']:.4f} | Brier={m_ev_argmax['brier']:.4f}")
    print(f"   confusion (umbral): {m_ev['confusion']}")

    # XGBoost con mascaras en el mismo par val/test, para comparar
    modelos, prev_m = mm.entrenar(tr, feats)
    p_va_m = mm.predecir(modelos, prev_m, va, feats)
    p_ev_m = mm.predecir(modelos, prev_m, ev, feats)
    m_va_m, _ = mu.umbral_baja(p_va_m, va["y"].to_numpy())
    t_m = m_va_m["umbral"]
    m_ev_m = mu.metricas_completas(p_ev_m, y_ev, pred_umbral(p_ev_m, t_m))
    print(f"\n--- XGBoost con mascaras (mismo par val/test) ---")
    print(f"   t={t_m:.2f} | test F1 baja={m_ev_m['f1_por_clase']['baja']:.4f} | "
          f"prec={m_ev_m['precision_baja']:.4f} | rec={m_ev_m['recall_baja']:.4f} | "
          f"F1 macro={m_ev_m['f1_macro']:.4f} | Brier={m_ev_m['brier']:.4f}")
    print(f"   mejora sobre el baseline: F1 baja "
          f"{m_ev_m['f1_por_clase']['baja'] - m_ev['f1_por_clase']['baja']:+.4f}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": "B",
        "prevalencias_train": {c: float(v) for c, v in zip(mm.CLASES, prev)},
        "prevalencias_val": np.round(np.bincount(va["y"].to_numpy(), minlength=3) / len(va), 4).tolist(),
        "prevalencias_test": np.round(np.bincount(y_ev, minlength=3) / len(y_ev), 4).tolist(),
        "baseline": {"umbral": float(t), "val_f1_baja": m_va["f1_baja_umbral"],
                     "test_f1_baja": m_ev["f1_por_clase"]["baja"],
                     "test_precision": m_ev["precision_baja"],
                     "test_recall": m_ev["recall_baja"],
                     "test_f1_macro": m_ev["f1_macro"], "test_brier": m_ev["brier"],
                     "test_argmax_f1_macro": m_ev_argmax["f1_macro"]},
        "xgb_mascaras": {"umbral": float(t_m),
                         "test_f1_baja": m_ev_m["f1_por_clase"]["baja"],
                         "test_precision": m_ev_m["precision_baja"],
                         "test_recall": m_ev_m["recall_baja"],
                         "test_f1_macro": m_ev_m["f1_macro"],
                         "test_brier": m_ev_m["brier"]},
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("pasoB_baseline_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
