#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pasoE_test_final.py
===================

PASO E: evaluacion final UNICA en test (cohorte 19->21, 13 355 filas).

- Modelo: XGBoost con mascaras reentrenado con todo lo anterior al test
  (cohortes 17, 18, 19 y 20).
- Umbral: media de los umbrales elegidos en los folds del Paso A.
- Se evalua una sola vez y este es el numero final.

Uso: <python> 07_modelo/modelado/pasoE_test_final.py
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

    paso_a = sorted(RESULTADOS.glob("pasoA_cv_temporal_*.json"))[-1]
    datos_a = json.loads(paso_a.read_text(encoding="utf-8"))
    umbrales = [f["umbral"] for f in datos_a["folds"].values()]
    t = float(np.mean(umbrales))
    print(f"umbrales de los folds: {umbrales} -> media t={t:.4f}")

    contenedor = joblib.load(mu.MODELOS_DIR / "xgb_ventana_contiguo.joblib")
    feats = [f for f in contenedor["features"] if f != "ano"]
    df = mm.preparar(pd.read_parquet(SCRIPT_DIR.parent / "datos" / "derivados" /
                                     "modelo_dataset_ventana_contiguo.parquet"))
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    tr = df[np.isin(per, [17, 18, 19, 20])]
    te = df[per == 21]
    print(f"train (17,18,19,20): {len(tr):,} | test (21): {len(te):,}".replace(",", " "))

    modelos, prev = mm.entrenar(tr, feats)
    p_te = mm.predecir(modelos, prev, te, feats)
    y = te["y"].to_numpy()
    pred = pred_umbral(p_te, t)

    m = mu.metricas_completas(p_te, y, pred)
    m_arg = mu.metricas_completas(p_te, y)
    print(f"\n=== TEST (una sola evaluacion), t={t:.4f} ===")
    print(f"   F1 baja={m['f1_por_clase']['baja']:.4f} | recall={m['recall_baja']:.4f} | "
          f"precision={m['precision_baja']:.4f}")
    print(f"   F1 macro={m['f1_macro']:.4f} | Brier={m['brier']:.4f} | "
          f"exactitud={m['exactitud']:.4f}")
    print(f"   F1 por clase: baja={m['f1_por_clase']['baja']:.4f} | "
          f"mantiene={m['f1_por_clase']['se_mantiene']:.4f} | "
          f"sube={m['f1_por_clase']['sube']:.4f}")
    print(f"   AUC baja={m['auc_ovr']['baja']:.4f} | mantiene={m['auc_ovr']['se_mantiene']:.4f} "
          f"| sube={m['auc_ovr']['sube']:.4f}")
    print(f"   alertadas: {100*m['pred_baja_pct']:.2f} % de las filas")
    print(f"   confusion (filas=real, cols=pred): {m['confusion']}")
    print(f"   (referencia argmax puro: F1 macro={m_arg['f1_macro']:.4f}, "
          f"F1 baja={m_arg['f1_por_clase']['baja']:.4f})")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": "E", "modelo": "XGBoost mascaras sin 'ano'",
        "umbral": t, "umbrales_folds": umbrales,
        "n_train": int(len(tr)), "n_test": int(len(te)),
        "metricas": m, "argmax": {"f1_macro": m_arg["f1_macro"],
                                  "f1_baja": m_arg["f1_por_clase"]["baja"],
                                  "brier": m_arg["brier"]},
        "nota": "evaluacion unica; test no se vuelve a usar en esta ronda",
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("pasoE_test_final_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
