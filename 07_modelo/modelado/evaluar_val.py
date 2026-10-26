#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
evaluar_val.py
==============

Fase 5 (parte 2): evalua en VAL (destino 2019) el mejor XGBoost de cada
dataset, la logistica y el baseline trivial. Test NO se toca.

Reporta por modelo y dataset:
  F1 macro, F1 por clase, AUC OvR por clase, matriz de confusion 3x3,
  Brier score multiclase.

Salida: 07_modelo/modelado/resultados/evaluacion_val_<UTC>.json

Requisitos: pandas, numpy, sklearn, xgboost, joblib (interprete con xgboost).

Uso:
    python 07_modelo/modelado/evaluar_val.py
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


def metricas(y_true_str, pred_idx, proba, np, f1_score, roc_auc_score):
    y_pred_str = [CLASES[i] for i in pred_idx]
    f1_macro = float(f1_score(y_true_str, y_pred_str, labels=list(CLASES),
                              average="macro", zero_division=0))
    f1_por_clase = f1_score(y_true_str, y_pred_str, labels=list(CLASES),
                            average=None, zero_division=0)
    auc = {}
    for i, clase in enumerate(CLASES):
        y_bin = (np.asarray(y_true_str) == clase).astype(int)
        auc[clase] = float(roc_auc_score(y_bin, proba[:, i])) if len(np.unique(y_bin)) > 1 else None
    yi = np.array([CLASES.index(c) for c in y_true_str])
    onehot = np.zeros_like(proba)
    onehot[np.arange(len(yi)), yi] = 1.0
    brier = float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))
    return {
        "f1_macro": f1_macro,
        "f1_por_clase": {c: float(v) for c, v in zip(CLASES, f1_por_clase)},
        "auc_ovr_por_clase": auc,
        "brier_multiclase": brier,
    }


def main() -> int:
    try:
        import joblib
        import numpy as np
        import pandas as pd
        from sklearn.metrics import confusion_matrix, f1_score, roc_auc_score
    except ImportError as exc:
        print("ERROR: falta una dependencia del modelado:", exc)
        print("  Use el interprete con xgboost (por ejemplo el venv de Agente).")
        print(f"  Interprete actual: {sys.executable}")
        return 2

    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    resultados = {}
    print(f"Interprete: {sys.executable}")

    for ds in ("ventana_contiguo", "acumulado_contiguo"):
        config_path = MODELOS_DIR / f"config_{ds}.json"
        if not config_path.exists():
            print(f"ERROR: no existe {config_path}; ejecute antes entrenar_modelos.py")
            return 2
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        features = cfg["features"]
        df = pd.read_parquet(DERIVADOS / f"modelo_dataset_{ds}.parquet")
        val = df[df["split"] == "val"]
        X = val[features]
        y_str = val["target_class"].to_numpy()
        yi = np.array([CLASES.index(c) for c in y_str])

        res = {"filas_val": int(len(val)), "modelos": {}}

        # baseline
        pred_base = np.full(len(val), CLASES.index("se_mantiene"))
        proba_base = np.zeros((len(val), 3))
        proba_base[:, CLASES.index("se_mantiene")] = 1.0
        res["modelos"]["baseline"] = metricas(y_str, pred_base, proba_base, np,
                                              f1_score, roc_auc_score)
        res["modelos"]["baseline"]["confusion"] = confusion_matrix(
            y_str, [CLASES[i] for i in pred_base], labels=list(CLASES)).tolist()

        # logistica
        lr = joblib.load(MODELOS_DIR / f"logistica_{ds}.joblib")
        pred_lr = lr["modelo"].predict(X).astype(int)
        proba_lr = lr["modelo"].predict_proba(X)
        res["modelos"]["logistica"] = metricas(y_str, pred_lr, proba_lr, np,
                                               f1_score, roc_auc_score)
        res["modelos"]["logistica"]["confusion"] = confusion_matrix(
            y_str, [CLASES[i] for i in pred_lr], labels=list(CLASES)).tolist()

        # xgboost
        xgbm = joblib.load(MODELOS_DIR / f"xgb_{ds}.joblib")
        proba_x = xgbm["modelo"].predict_proba(X)
        pred_x = proba_x.argmax(axis=1)
        res["modelos"]["xgboost"] = metricas(y_str, pred_x, proba_x, np,
                                             f1_score, roc_auc_score)
        res["modelos"]["xgboost"]["confusion"] = confusion_matrix(
            y_str, [CLASES[i] for i in pred_x], labels=list(CLASES)).tolist()
        res["xgboost_params"] = xgbm.get("params")
        resultados[ds] = res

    # ---- tabla ----
    print("\nTabla en VAL (destino 2019) — clases: baja / se_mantiene / sube")
    print(f"{'dataset':<20} {'modelo':<10} {'F1macro':>8} {'F1sube':>7} {'F1mant':>7} "
          f"{'F1baja':>7} {'AUCsube':>8} {'AUCmant':>8} {'AUCbaja':>8} {'Brier':>7}")
    for ds, res in resultados.items():
        for modelo in ("baseline", "logistica", "xgboost"):
            m = res["modelos"][modelo]
            f = m["f1_por_clase"]
            a = m["auc_ovr_por_clase"]
            print(f"{ds:<20} {modelo:<10} {m['f1_macro']:>8.4f} {f['sube']:>7.3f} "
                  f"{f['se_mantiene']:>7.3f} {f['baja']:>7.3f} "
                  f"{a['sube'] if a['sube'] is not None else float('nan'):>8.3f} "
                  f"{a['se_mantiene'] if a['se_mantiene'] is not None else float('nan'):>8.3f} "
                  f"{a['baja'] if a['baja'] is not None else float('nan'):>8.3f} "
                  f"{m['brier_multiclase']:>7.4f}")

    print("\nMatriz de confusion — XGBoost (filas = real, columnas = predicho):")
    for ds, res in resultados.items():
        print(f"\n   {ds} (orden: baja, se_mantiene, sube)")
        for fila in res["modelos"]["xgboost"]["confusion"]:
            print("      " + "  ".join(f"{v:6d}" for v in fila))

    payload = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "regla": "evaluacion en val (destino 2019); test no usado",
        "clases": list(CLASES),
        "resultados": resultados,
    }
    salida = RESULTADOS_DIR / f"evaluacion_val_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    salida.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
