#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluar_bayesiano.py
====================

Evalua en VAL (destino 2019) el modelo bayesiano ordinal jerarquico ya
muestreado. Test NO se toca.

  - Probabilidades predichas (posterior predictive; periodo 20 como nivel nuevo).
  - F1 macro, F1 por clase, AUC OvR, Brier multiclase.
  - Intervalos de credibilidad 80 % y 95 % para la probabilidad de cada clase.
  - Comparacion con XGBoost r1 (F1 macro 0,3939; AUC baja 0,563; Brier 0,5479).

Uso:
    <python 07_modelo/.venv-bayes> 07_modelo/modelado/evaluar_bayesiano.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

CLASES = ("baja", "se_mantiene", "sube")
XGB_R1 = {"f1_macro": 0.3939, "f1_por_clase": {"baja": 0.132, "se_mantiene": 0.709, "sube": 0.340},
          "auc_baja": 0.563, "brier": 0.5479}


def main() -> int:
    try:
        import arviz as az
        import numpy as np
        from sklearn.metrics import f1_score, roc_auc_score
        import entrenar_bayesiano as eb
    except ImportError as exc:
        print("ERROR: falta dependencia:", exc)
        print("  Use 07_modelo/.venv-bayes")
        return 2

    trace = SCRIPT_DIR / "modelos" / "trace_bayesiano.nc"
    if not trace.exists():
        print(f"ERROR: no existe {trace}; ejecute antes entrenar_bayesiano.py")
        return 2

    idata = az.from_netcdf(trace)
    post = idata.posterior
    beta = post["beta"].values.reshape(-1, post["beta"].shape[-1])
    u = post["u"].values.reshape(-1, post["u"].shape[-1])
    v = post["v"].values.reshape(-1, post["v"].shape[-1])
    sigma_v = post["sigma_v"].values.reshape(-1)
    k1 = post["kappa1"].values.reshape(-1)
    k2 = post["kappa2"].values.reshape(-1)
    S_total = beta.shape[0]

    # Reconstruir datos (misma logica que el entrenamiento)
    import numpy as np
    import pandas as pd
    ruta = SCRIPT_DIR.parent / "datos" / "derivados" / "modelo_dataset_ventana_contiguo.parquet"
    df = pd.read_parquet(ruta)
    censo = eb.cargar_censo(pd)
    datos = eb.construir_features(df, censo, pd, np)

    X_val = datos["X_val"]
    y_val = datos["y_val"]
    y_str = np.array([CLASES[i] for i in y_val])
    cat = datos["cat_val"]
    mask_ij = datos["mask_ij_val"]
    mask_ie = datos["mask_ie_val"]

    # Posterior predictive con el periodo 20 como nivel nuevo (v ~ N(0, sigma_v))
    idx = np.linspace(0, S_total - 1, min(2000, S_total)).astype(int)
    b, uu, vv, sv = beta[idx], u[idx], v[idx], sigma_v[idx]
    eta = X_val @ b.T
    eta = eta + uu[:, cat].T
    rng = np.random.default_rng(42)
    v_new = rng.normal(0.0, sv)
    eta = eta + v_new[None, :]
    p1 = 1.0 / (1.0 + np.exp(-(k1[idx][None, :] - eta)))
    p2 = 1.0 / (1.0 + np.exp(-(k2[idx][None, :] - eta)))
    p = np.stack([p1, p2 - p1, 1.0 - p2], axis=-1).astype("float32")
    p = np.clip(p, 1e-9, 1.0)
    # Mascaras del val
    p[mask_ij, :, 0] = 0.0
    p[mask_ie, :, 2] = 0.0
    p = p / p.sum(axis=2, keepdims=True)

    p_mean = p.mean(axis=1)
    pred = p_mean.argmax(axis=1)
    pred_str = np.array([CLASES[i] for i in pred])

    f1_macro = float(f1_score(y_str, pred_str, labels=list(CLASES), average="macro", zero_division=0))
    f1_clase = f1_score(y_str, pred_str, labels=list(CLASES), average=None, zero_division=0)
    auc = {}
    for i, c in enumerate(CLASES):
        yb = (y_str == c).astype(int)
        auc[c] = float(roc_auc_score(yb, p_mean[:, i])) if len(np.unique(yb)) > 1 else None
    onehot = np.zeros_like(p_mean)
    onehot[np.arange(len(y_val)), y_val] = 1.0
    brier = float(np.mean(np.sum((p_mean - onehot) ** 2, axis=1)))

    # Intervalos de credibilidad (agregados por clase y por observacion)
    ci = {}
    for i, c in enumerate(CLASES):
        media_por_draw = p[:, :, i].mean(axis=0)  # S
        q80 = np.percentile(media_por_draw, [10, 90])
        q95 = np.percentile(media_por_draw, [2.5, 97.5])
        obs_q80 = np.percentile(p[:, :, i], [10, 90], axis=0)
        obs_q95 = np.percentile(p[:, :, i], [2.5, 97.5], axis=0)
        ci[c] = {
            "media": float(media_por_draw.mean()),
            "ic80_agregado": [float(q80[0]), float(q80[1])],
            "ic95_agregado": [float(q95[0]), float(q95[1])],
            "ancho_medio_ic80_por_obs": float(np.mean(obs_q80[1] - obs_q80[0])),
            "ancho_medio_ic95_por_obs": float(np.mean(obs_q95[1] - obs_q95[0])),
        }

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trace": str(trace), "draws_usados": int(len(idx)), "draws_totales": int(S_total),
        "n_val": int(len(y_val)),
        "metricas": {"f1_macro": f1_macro,
                     "f1_por_clase": {c: float(v) for c, v in zip(CLASES, f1_clase)},
                     "auc_ovr": auc, "brier": brier},
        "intervalos": ci,
        "xgboost_r1": XGB_R1,
        "comparacion": {
            "delta_f1_macro_pp": round(100 * (f1_macro - XGB_R1["f1_macro"]), 2),
            "delta_brier": round(brier - XGB_R1["brier"], 4),
            "delta_auc_baja": round((auc["baja"] or 0) - XGB_R1["auc_baja"], 4),
        },
    }

    print(f"Interprete: {sys.executable}")
    print(f"Trace: {trace} | draws usados: {len(idx)}/{S_total}")
    print(f"\nVAL (n={len(y_val)}) — bayesiano ordinal jerarquico")
    print(f"   F1 macro = {f1_macro:.4f}  (XGBoost r1: {XGB_R1['f1_macro']:.4f}, "
          f"delta {resumen['comparacion']['delta_f1_macro_pp']:+.1f} pp)")
    print(f"   F1 sube={f1_clase[2]:.3f} | F1 mantiene={f1_clase[1]:.3f} | F1 baja={f1_clase[0]:.3f}")
    print(f"   AUC baja={auc['baja']} | AUC mantiene={auc['se_mantiene']} | AUC sube={auc['sube']}")
    print(f"   Brier = {brier:.4f}  (XGBoost r1: {XGB_R1['brier']:.4f}, "
          f"delta {resumen['comparacion']['delta_brier']:+.4f})")
    print("\nIntervalos de credibilidad (probabilidad media por clase):")
    for c in CLASES:
        d = ci[c]
        print(f"   {c:<12} media={d['media']:.3f} | IC80=[{d['ic80_agregado'][0]:.3f}, "
              f"{d['ic80_agregado'][1]:.3f}] | IC95=[{d['ic95_agregado'][0]:.3f}, "
              f"{d['ic95_agregado'][1]:.3f}] | ancho medio por obs: "
              f"IC80={d['ancho_medio_ic80_por_obs']:.3f}, IC95={d['ancho_medio_ic95_por_obs']:.3f}")

    salida = SCRIPT_DIR / "resultados" / f"evaluacion_bayesiano_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
