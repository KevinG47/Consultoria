#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pasoC_sobreajuste.py
====================

PASO C: analisis de sobreajuste del XGBoost con mascaras.

- F1 macro en train (en muestra) vs val (cohorte 20).
- Curva de aprendizaje: F1 macro val y train para n_estimators 100/200/400/800.
- Regla: si train F1 > 0.70 y val F1 < 0.55 -> sobreajuste.

Uso: <python> 07_modelo/modelado/pasoC_sobreajuste.py
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
import metricas_umbral as mu  # noqa: E402
import modelo_mascaras as mm  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"


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
    y_tr, y_va = tr["y"].to_numpy(), va["y"].to_numpy()

    modelos, prev = mm.entrenar(tr, feats)
    m_tr = mu.metricas_completas(mm.predecir(modelos, prev, tr, feats), y_tr)
    m_va = mu.metricas_completas(mm.predecir(modelos, prev, va, feats), y_va)
    print("--- F1 macro con n_estimators=200 ---")
    print(f"   train: F1 macro={m_tr['f1_macro']:.4f} | Brier={m_tr['brier']:.4f}")
    print(f"   val  : F1 macro={m_va['f1_macro']:.4f} | Brier={m_va['brier']:.4f}")
    print(f"   brecha train-val: {m_tr['f1_macro']-m_va['f1_macro']:+.4f}")
    sobre = bool(m_tr["f1_macro"] > 0.70 and m_va["f1_macro"] < 0.55)
    print(f"   regla (train>0.70 y val<0.55): {'SOBREAJUSTE' if sobre else 'sin sobreajuste'}")

    print("\n--- curva de aprendizaje (n_estimators) ---")
    print("   n_est   F1_train  F1_val   Brier_val  seg")
    curva = []
    for n in (100, 200, 400, 800):
        t0 = time.time()
        mod_n, prev_n = mm.entrenar(tr, feats, n_estimators=n)
        seg = time.time() - t0
        f_tr = mu.metricas_completas(mm.predecir(mod_n, prev_n, tr, feats), y_tr)
        f_va = mu.metricas_completas(mm.predecir(mod_n, prev_n, va, feats), y_va)
        curva.append({"n_estimators": n, "f1_train": f_tr["f1_macro"],
                      "f1_val": f_va["f1_macro"], "brier_val": f_va["brier"],
                      "segundos": round(seg, 1)})
        print(f"   {n:<7d} {f_tr['f1_macro']:.4f}     {f_va['f1_macro']:.4f}   "
              f"{f_va['brier']:.4f}     {seg:.1f}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": "C", "modelo": "XGBoost mascaras sin 'ano'",
        "train": {"n": int(len(tr)), "f1_macro": m_tr["f1_macro"], "brier": m_tr["brier"]},
        "val": {"n": int(len(va)), "f1_macro": m_va["f1_macro"], "brier": m_va["brier"]},
        "brecha_f1_macro": m_tr["f1_macro"] - m_va["f1_macro"],
        "sobreajuste_segun_regla": sobre,
        "curva": curva,
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("pasoC_sobreajuste_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
