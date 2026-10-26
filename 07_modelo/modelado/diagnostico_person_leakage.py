#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
diagnostico_person_leakage.py
=============================

Diagnostico A: split POR PERSONA (80/20 por ID_PERSONA_PR, ignorando el ano)
frente al split TEMPORAL. Si el F1 cae mucho, hay person leakage (el modelo
memoriza personas).

Se reentrena XGBoost con la mejor config de ronda 1:
  ventana   : depth 7 lr 0.05 n 200 sub 0.8
  acumulado : depth 5 lr 0.05 n 200 sub 1.0

Solo train/val; test no se toca.

Uso:
    <python con xgboost> 07_modelo/modelado/diagnostico_person_leakage.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
MODELOS_DIR = SCRIPT_DIR / "modelos"
RESULTADOS_DIR = SCRIPT_DIR / "resultados"

CLASES = ("baja", "se_mantiene", "sube")


def metricas(y_true, pred_idx, proba, np, f1_score, roc_auc_score):
    pred = [CLASES[i] for i in pred_idx]
    f1m = float(f1_score(y_true, pred, labels=list(CLASES), average="macro", zero_division=0))
    f1c = f1_score(y_true, pred, labels=list(CLASES), average=None, zero_division=0)
    y_baja = (np.asarray(y_true) == "baja").astype(int)
    auc = None
    if len(np.unique(y_baja)) > 1:
        auc = float(roc_auc_score(y_baja, proba[:, CLASES.index("baja")]))
    return {"f1_macro": f1m, "f1_por_clase": {c: float(v) for c, v in zip(CLASES, f1c)},
            "auc_baja": auc, "n": int(len(y_true))}


def main() -> int:
    try:
        import numpy as np
        import pandas as pd
        from sklearn.metrics import f1_score, roc_auc_score
        import xgboost as xgb
    except ImportError as exc:
        print("ERROR: falta dependencia:", exc)
        print(f"Interprete actual: {sys.executable}")
        return 2

    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Interprete: {sys.executable}")
    print(f"xgboost {xgb.__version__}")
    print("REGLA: train/val; test no se toca. Split por persona 80/20, semilla 42.")

    resultados = {}
    for ds in ("ventana_contiguo", "acumulado_contiguo"):
        cfg = json.loads((MODELOS_DIR / f"config_{ds}.json").read_text(encoding="utf-8"))
        params = cfg["xgboost"]["mejor"]
        feats = cfg["features"]
        df = pd.read_parquet(DERIVADOS / f"modelo_dataset_{ds}.parquet")

        def pesos(y):
            yi = np.array([CLASES.index(c) for c in y])
            w = np.bincount(yi, minlength=3)
            w = len(yi) / (3.0 * w)
            return yi, w[yi]

        def ajustar(train):
            yi, w = pesos(train["target_class"])
            m = xgb.XGBClassifier(objective="multi:softprob", eval_metric="mlogloss",
                                  tree_method="hist", n_jobs=-1, random_state=42,
                                  verbosity=0, **params)
            m.fit(train[feats], yi, sample_weight=w)
            return m

        # --- referencia temporal (la de ronda 1) ---
        train_t = df[df["split"] == "train"]
        val_t = df[df["split"] == "val"]
        m_t = ajustar(train_t)
        p_t = m_t.predict_proba(val_t[feats])
        met_t = metricas(val_t["target_class"].to_numpy(), p_t.argmax(1), p_t,
                         np, f1_score, roc_auc_score)

        # --- split por persona ---
        ids = df["ID_PERSONA_PR"].unique()
        rng = np.random.default_rng(42)
        perm = rng.permutation(len(ids))
        corte = int(0.8 * len(ids))
        train_ids = set(ids[perm[:corte]])
        val_ids = set(ids[perm[corte:]])
        train_p = df[df["ID_PERSONA_PR"].isin(train_ids)]
        val_p = df[df["ID_PERSONA_PR"].isin(val_ids)]
        m_p = ajustar(train_p)
        p_p = m_p.predict_proba(val_p[feats])
        met_p = metricas(val_p["target_class"].to_numpy(), p_p.argmax(1), p_p,
                         np, f1_score, roc_auc_score)

        delta = met_p["f1_macro"] - met_t["f1_macro"]
        if delta < -0.05:
            veredicto = "person leakage CONFIRMADO"
        elif delta > -0.03:
            veredicto = "sin person leakage"
        else:
            veredicto = "zona ambigua (entre -3 y -5 pp)"

        print(f"\n== {ds} ==")
        print(f"   temporal : F1 macro={met_t['f1_macro']:.4f} | AUC baja={met_t['auc_baja']} "
              f"| n={met_t['n']} | clases={met_t['f1_por_clase']}")
        print(f"   por persona: F1 macro={met_p['f1_macro']:.4f} | AUC baja={met_p['auc_baja']} "
              f"| n={met_p['n']} (train {len(train_p)}, val {len(val_p)}) | clases={met_p['f1_por_clase']}")
        print(f"   delta F1 macro = {100*delta:+.1f} pp -> {veredicto}")

        resultados[ds] = {
            "params": params, "n_features": len(feats),
            "temporal": met_t, "por_persona": met_p,
            "delta_pp": round(100 * delta, 2), "veredicto": veredicto,
            "n_personas_train": len(train_ids), "n_personas_val": len(val_ids),
        }

    salida = RESULTADOS_DIR / f"diagnostico_leakage_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
