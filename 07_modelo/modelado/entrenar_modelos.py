#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
entrenar_modelos.py
===================

Fase 5 (parte 1): entrena los modelos de la transicion de categoria.
REGLA ESTRICTA: test NO se toca. Solo train para ajuste y val (destino 2019)
para seleccion.

Modelos por dataset (ventana_contiguo y acumulado_contiguo):
  - Baseline trivial: predice siempre "se_mantiene".
  - Regresion logistica multinomial (class_weight='balanced', max_iter=2000).
  - XGBoost multiclase con sample_weight balanceado (N / (3 * n_clase)).
    Grid: max_depth {3,5,7} x learning_rate {0.05,0.1} x
          n_estimators {200,400} x subsample {0.8,1.0} = 24 combinaciones.

Guarda en 07_modelo/modelado/modelos/:
  logistica_<dataset>.joblib
  xgb_<dataset>.joblib
  config_<dataset>.json   (features exactas, hiperparametros, metricas en val)

Requisitos: pandas, numpy, sklearn, xgboost, joblib. El Python del sistema NO
tiene xgboost; usar el interprete que si lo tenga (se informa en el error).

Uso:
    python 07_modelo/modelado/entrenar_modelos.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
MODELOS_DIR = SCRIPT_DIR / "modelos"

CLASES = ("baja", "se_mantiene", "sube")

# Columnas que NUNCA son features: identificadores, objetivo, particion y
# columnas derivadas del futuro (gap, contiguo, conv siguiente) o banderas.
EXCLUIR = [
    "ID_PERSONA_PR",
    "ID_CONVOCATORIA",
    "ID_CONVOCATORIA_siguiente",
    "ORDEN_CLAS_PR_actual",
    "ORDEN_CLAS_PR_siguiente",
    "target_class",
    "split",
    "gap",
    "contiguo",
    "dias_desde_ultimo_negativo",
    "sin_produccion",
]


def cargar_stack():
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: F401
    from sklearn.metrics import f1_score, roc_auc_score
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    import xgboost as xgb
    return {
        "joblib": joblib, "np": np, "pd": pd, "xgb": xgb,
        "f1_score": f1_score, "roc_auc_score": roc_auc_score,
        "SimpleImputer": SimpleImputer, "LogisticRegression": LogisticRegression,
        "Pipeline": Pipeline, "StandardScaler": StandardScaler,
    }


def metricas(y_true_str, pred_idx, proba, np, f1_score, roc_auc_score):
    """y_true_str: array de strings; pred_idx: indices 0..2; proba: Nx3."""
    y_pred_str = [CLASES[i] for i in pred_idx]
    f1_macro = float(f1_score(y_true_str, y_pred_str, labels=list(CLASES),
                              average="macro", zero_division=0))
    f1_por_clase = f1_score(y_true_str, y_pred_str, labels=list(CLASES),
                            average=None, zero_division=0)
    auc = {}
    for i, clase in enumerate(CLASES):
        y_bin = (np.asarray(y_true_str) == clase).astype(int)
        if len(np.unique(y_bin)) > 1:
            auc[clase] = float(roc_auc_score(y_bin, proba[:, i]))
        else:
            auc[clase] = None
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


def preparar(ds, ruta, stack):
    pd, np = stack["pd"], stack["np"]
    df = pd.read_parquet(ruta)
    if (df["split"] == "test").sum() > 0:
        print("   [ok] test presente en el parquet pero NO se usara")
    train = df[df["split"] == "train"]
    val = df[df["split"] == "val"]
    features = [c for c in df.columns if c not in EXCLUIR]
    # Columnas constantes en train: no aportan y ensucian el modelo.
    constantes = [c for c in features if train[c].nunique(dropna=False) <= 1]
    features = [c for c in features if c not in constantes]
    print(f"\n== {ds} ==")
    print(f"   train: {len(train):,} | val: {len(val):,} | test usado: 0"
          .replace(",", " "))
    print(f"   features excluidas por constante (train): {constantes or 'ninguna'}")
    print(f"   features ({len(features)}): " + ", ".join(features))
    return df, train, val, features, constantes


def main() -> int:
    ap = argparse.ArgumentParser(description="Entrena baseline, logistica y XGBoost (solo train/val).")
    ap.add_argument("--datasets", nargs="+", default=["ventana_contiguo", "acumulado_contiguo"])
    args = ap.parse_args()

    try:
        stack = cargar_stack()
    except ImportError as exc:
        print("ERROR: falta una dependencia del modelado:", exc)
        print("  El Python del sistema no tiene xgboost. Ejecute con el interprete que si lo tenga")
        print("  (por ejemplo el venv de Agente) o instale xgboost en este interprete.")
        print(f"  Interprete actual: {sys.executable}")
        return 2

    pd, np, xgb = stack["pd"], stack["np"], stack["xgb"]
    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Interprete: {sys.executable}")
    print(f"xgboost {xgb.__version__} | pandas {pd.__version__}")

    resumen_global = {}
    for ds in args.datasets:
        ruta = DERIVADOS / f"modelo_dataset_{ds}.parquet"
        if not ruta.exists():
            print(f"ERROR: no existe {ruta}")
            return 2
        df, train, val, features, constantes = preparar(ds, ruta, stack)

        X_train = train[features]
        X_val = val[features]
        yi_train = np.array([CLASES.index(c) for c in train["target_class"]])
        yi_val = np.array([CLASES.index(c) for c in val["target_class"]])
        y_val_str = val["target_class"].to_numpy()

        # ---- baseline trivial ----
        t0 = time.time()
        pred_base = np.full(len(val), CLASES.index("se_mantiene"))
        proba_base = np.zeros((len(val), 3))
        proba_base[:, CLASES.index("se_mantiene")] = 1.0
        m_base = metricas(y_val_str, pred_base, proba_base, np,
                          stack["f1_score"], stack["roc_auc_score"])
        t_base = time.time() - t0
        print(f"\n   baseline: F1 macro={m_base['f1_macro']:.4f}")

        # ---- logistica multinomial ----
        t0 = time.time()
        pipe = stack["Pipeline"]([
            ("imp", stack["SimpleImputer"](strategy="median")),
            ("sc", stack["StandardScaler"]()),
            ("lr", stack["LogisticRegression"](max_iter=2000, class_weight="balanced")),
        ])
        pipe.fit(X_train, yi_train)
        pred_lr = pipe.predict(X_val).astype(int)
        proba_lr = pipe.predict_proba(X_val)
        m_lr = metricas(y_val_str, pred_lr, proba_lr, np,
                        stack["f1_score"], stack["roc_auc_score"])
        t_lr = time.time() - t0
        print(f"   logistica: F1 macro={m_lr['f1_macro']:.4f} ({t_lr:.1f} s)")

        # ---- XGBoost con pesos balanceados ----
        conteo = np.bincount(yi_train, minlength=3)
        pesos_clase = len(yi_train) / (3.0 * conteo)
        w_train = pesos_clase[yi_train]
        print(f"   pesos de clase: {dict(zip(CLASES, np.round(pesos_clase, 3)))}")

        mejores = None
        resultados_grid = []
        t_grid0 = time.time()
        for max_depth in (3, 5, 7):
            for lr in (0.05, 0.1):
                for n_est in (200, 400):
                    for sub in (0.8, 1.0):
                        t0 = time.time()
                        modelo = xgb.XGBClassifier(
                            objective="multi:softprob",
                            eval_metric="mlogloss",
                            max_depth=max_depth,
                            learning_rate=lr,
                            n_estimators=n_est,
                            subsample=sub,
                            tree_method="hist",
                            n_jobs=-1,
                            random_state=42,
                            verbosity=0,
                        )
                        modelo.fit(X_train, yi_train, sample_weight=w_train)
                        proba = modelo.predict_proba(X_val)
                        pred = proba.argmax(axis=1)
                        f1m = float(stack["f1_score"](
                            y_val_str, [CLASES[i] for i in pred],
                            labels=list(CLASES), average="macro", zero_division=0))
                        fila = {"max_depth": max_depth, "learning_rate": lr,
                                "n_estimators": n_est, "subsample": sub,
                                "f1_macro": f1m, "segundos": round(time.time() - t0, 2)}
                        resultados_grid.append(fila)
                        print(f"      depth={max_depth} lr={lr} n={n_est} sub={sub} "
                              f"-> F1 macro={f1m:.4f} ({fila['segundos']:.1f} s)")
                        if mejores is None or f1m > mejores["metricas"]["f1_macro"]:
                            mejores = {"params": {"max_depth": max_depth,
                                                  "learning_rate": lr,
                                                  "n_estimators": n_est,
                                                  "subsample": sub},
                                       "modelo": modelo, "metricas": fila,
                                       "proba": proba, "pred": pred}
        t_grid = time.time() - t_grid0
        m_xgb = metricas(y_val_str, mejores["pred"], mejores["proba"], np,
                         stack["f1_score"], stack["roc_auc_score"])
        print(f"   MEJOR XGBoost: {mejores['params']} -> F1 macro={m_xgb['f1_macro']:.4f}"
              f" (grid {t_grid:.1f} s)")

        # ---- guardar ----
        stack["joblib"].dump({"modelo": pipe, "features": features,
                              "clases": list(CLASES), "tipo": "logistica"},
                             MODELOS_DIR / f"logistica_{ds}.joblib")
        stack["joblib"].dump({"modelo": mejores["modelo"], "features": features,
                              "clases": list(CLASES), "tipo": "xgboost",
                              "params": mejores["params"]},
                             MODELOS_DIR / f"xgb_{ds}.joblib")

        config = {
            "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "dataset": ds,
            "archivo": str(ruta),
            "regla": "solo train (ajuste) y val (seleccion); test no usado",
            "filas_train": int(len(train)),
            "filas_val": int(len(val)),
            "features": features,
            "columnas_constantes_excluidas": constantes,
            "clases": list(CLASES),
            "baseline": {**m_base, "segundos": round(t_base, 2)},
            "logistica": {**m_lr, "segundos": round(t_lr, 2)},
            "xgboost": {
                "mejor": mejores["params"],
                **m_xgb,
                "segundos_grid": round(t_grid, 2),
                "grid": resultados_grid,
            },
        }
        (MODELOS_DIR / f"config_{ds}.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        resumen_global[ds] = config

    print("\nResumen en val:")
    for ds, cfg in resumen_global.items():
        print(f"   {ds}: baseline F1={cfg['baseline']['f1_macro']:.4f} | "
              f"logistica F1={cfg['logistica']['f1_macro']:.4f} | "
              f"xgboost F1={cfg['xgboost']['f1_macro']:.4f} "
              f"({cfg['xgboost']['mejor']})")
    print(f"\nModelos y configuraciones en {MODELOS_DIR}")
    print("\nSiguiente paso:")
    print("   python 07_modelo/modelado/evaluar_val.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
