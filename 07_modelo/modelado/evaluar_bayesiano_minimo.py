#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluar_bayesiano_minimo.py
===========================

Evaluacion en VAL del modelo bayesiano minimo ya muestreado
(trace_bayesiano_minimo.nc). No reajusta nada.

Reporta: F1 macro, F1 por clase, AUC OvR por clase, Brier multiclase,
intervalos de credibilidad 80 % y 95 %, y comparacion con XGBoost r1
(F1 macro 0.3939 | AUC baja 0.563 | Brier 0.5479).

Uso:
    <python 07_modelo/.venv-bayes> 07_modelo/modelado/evaluar_bayesiano_minimo.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_TMP_CACHE = Path(os.environ.get("TEMP", ".")) / "dsh_bayes"
_TMP_CACHE.mkdir(parents=True, exist_ok=True)
os.environ["PYTENSOR_FLAGS"] = (
    "cxx=,base_compiledir=" + str(_TMP_CACHE / "pytensor").replace("\\", "/"))

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
_CACHE_DIR = SCRIPT_DIR.parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)
os.environ["LOCALAPPDATA"] = str(_CACHE_DIR)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_DIR / "matplotlib"))
try:
    import platformdirs as _pd
    _orig = _pd.user_cache_dir

    def _uc(appname=None, appauthor=None, version=None, roaming=False):
        if appname == "arviz":
            return str(_CACHE_DIR / "arviz")
        return _orig(appname, appauthor, version, roaming)

    _pd.user_cache_dir = _uc
except Exception:  # pragma: no cover
    pass


def main() -> int:
    try:
        import arviz as az
        import numpy as np
        import pandas as pd
        from sklearn.metrics import f1_score, roc_auc_score
        import entrenar_bayesiano_minimo as em
    except ImportError as exc:
        print("ERROR: falta dependencia:", exc)
        return 2

    trace = SCRIPT_DIR / "modelos" / "trace_bayesiano_minimo.nc"
    if not trace.exists():
        print(f"ERROR: no existe {trace}")
        return 2

    ruta = SCRIPT_DIR.parent / "datos" / "derivados" / \
        "modelo_dataset_ventana_contiguo.parquet"
    df = pd.read_parquet(ruta)
    df = df[df["split"].isin(["train", "val"])].copy()   # test nunca se carga
    censo = em.cargar_censo(pd)
    datos = em.construir_features(df, censo, pd, np)

    idata = az.from_netcdf(trace)
    pred = em.predecir_val(idata, datos, np)
    p_mean = pred["p_mean"]
    y_val = datos["y_val"]
    y_str = np.array([em.CLASES[i] for i in y_val])
    pred_idx = p_mean.argmax(axis=1)
    pred_str = np.array([em.CLASES[i] for i in pred_idx])

    f1_macro = float(f1_score(y_str, pred_str, labels=list(em.CLASES),
                              average="macro", zero_division=0))
    f1_clase = f1_score(y_str, pred_str, labels=list(em.CLASES),
                        average=None, zero_division=0)
    auc = {}
    for i, c in enumerate(em.CLASES):
        yb = (y_str == c).astype(int)
        auc[c] = (float(roc_auc_score(yb, p_mean[:, i]))
                  if len(np.unique(yb)) > 1 else None)
    onehot = np.zeros_like(p_mean)
    onehot[np.arange(len(y_val)), y_val] = 1.0
    brier = float(np.mean(np.sum((p_mean - onehot) ** 2, axis=1)))
    acc = float(np.mean(pred_idx == y_val))

    ci = {}
    for i, c in enumerate(em.CLASES):
        md = pred["media_por_draw"][:, i]
        q80 = np.percentile(md, [10, 90])
        q95 = np.percentile(md, [2.5, 97.5])
        obs = pred["p_ic"][:, i, :]
        o80 = np.percentile(obs, [10, 90], axis=1)
        o95 = np.percentile(obs, [2.5, 97.5], axis=1)
        ci[c] = {
            "media": float(md.mean()),
            "ic80_agregado": [float(q80[0]), float(q80[1])],
            "ic95_agregado": [float(q95[0]), float(q95[1])],
            "ancho_medio_ic80_por_obs": float(np.mean(o80[1] - o80[0])),
            "ancho_medio_ic95_por_obs": float(np.mean(o95[1] - o95[0])),
        }

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trace": str(trace),
        "draws_usados": {"total": pred["S"], "usados_para_ic": pred["draws_ic"]},
        "n_val": int(len(y_val)),
        "metricas": {
            "f1_macro": f1_macro, "accuracy": acc,
            "f1_por_clase": {c: float(v) for c, v in zip(em.CLASES, f1_clase)},
            "auc_ovr": auc, "brier": brier,
        },
        "intervalos": ci,
        "xgboost_r1": em.XGB_R1,
        "comparacion": {
            "delta_f1_macro_pp": round(100 * (f1_macro - em.XGB_R1["f1_macro"]), 2),
            "delta_brier": round(brier - em.XGB_R1["brier"], 4),
            "delta_auc_baja": round((auc["baja"] or 0) - em.XGB_R1["auc_baja"], 4),
        },
    }
    salida = SCRIPT_DIR / "resultados" / (
        "evaluacion_bayesiano_minimo_"
        + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2),
                      encoding="utf-8")

    print(f"Interprete: {sys.executable}")
    print(f"Trace: {trace} | draws usados: {pred['S']} "
          f"(IC con {pred['draws_ic']})")
    print(f"\nVAL (n={len(y_val)}) — bayesiano minimo (12 predictores)")
    print(f"   F1 macro = {f1_macro:.4f}  (XGBoost r1 {em.XGB_R1['f1_macro']:.4f}, "
          f"delta {resumen['comparacion']['delta_f1_macro_pp']:+.1f} pp)")
    print(f"   Accuracy = {acc:.4f}")
    print(f"   F1 baja={f1_clase[0]:.3f} | F1 se_mantiene={f1_clase[1]:.3f} | "
          f"F1 sube={f1_clase[2]:.3f}")
    print(f"   AUC baja={auc['baja']} | AUC se_mantiene={auc['se_mantiene']} | "
          f"AUC sube={auc['sube']}   (XGBoost r1 AUC baja {em.XGB_R1['auc_baja']})")
    print(f"   Brier = {brier:.4f}  (XGBoost r1 {em.XGB_R1['brier']:.4f}, "
          f"delta {resumen['comparacion']['delta_brier']:+.4f})")
    print("\nIntervalos de credibilidad (probabilidad media por clase):")
    for c in em.CLASES:
        d = ci[c]
        print(f"   {c:<12} media={d['media']:.3f} | IC80=[{d['ic80_agregado'][0]:.3f}, "
              f"{d['ic80_agregado'][1]:.3f}] | IC95=[{d['ic95_agregado'][0]:.3f}, "
              f"{d['ic95_agregado'][1]:.3f}] | ancho medio por obs: "
              f"IC80={d['ancho_medio_ic80_por_obs']:.3f}, "
              f"IC95={d['ancho_medio_ic95_por_obs']:.3f}")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
