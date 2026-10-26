#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
paso3_xgb_mascaras.py
=====================

PASO 3: XGBoost con mascaras estructurales y SIN la feature 'ano'.

Modelos separados por categoria de origen:
    IJ (Junior)  -> binario: sube / se_mantiene  (no puede "baja")
    I  (Asociado)-> tricotomo
    IS (Senior)  -> tricotomo
    IE (Emerico) -> excluido (sin transiciones en train/val)

Features: las del r1 menos 'ano'. Se reportan las features reales usadas
(el r1 usa 173 tras excluir 102 constantes; sin 'ano' quedan 172).

Uso: <python> 07_modelo/modelado/paso3_xgb_mascaras.py
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

RESULTADOS = SCRIPT_DIR / "resultados"
CAT_MAP = {12: 0, 13: 1, 14: 2, 15: 3}
NOMBRES = {0: "IJ (Junior)", 1: "I (Asociado)", 2: "IS (Senior)", 3: "IE (Emerico)"}
PARAMS = dict(objective="multi:softprob", eval_metric="mlogloss",
              max_depth=7, learning_rate=0.05, n_estimators=200, subsample=0.8,
              tree_method="hist", n_jobs=-1, random_state=42, verbosity=0)


def main() -> int:
    import pandas as pd
    import xgboost as xgb

    df = mu.cargar_df(pd)
    contenedor = __import__("joblib").load(mu.MODELOS_DIR / "xgb_ventana_contiguo.joblib")
    feats = [f for f in contenedor["features"] if f != "ano"]
    print(f"features r1: {len(contenedor['features'])} | sin 'ano': {len(feats)}")

    df["cat"] = df["ORDEN_CLAS_PR_actual"].map(CAT_MAP)
    df["y"] = df["target_class"].map(lambda c: mu.CLASES.index(c))
    train = df[df["split"] == "train"]
    val = df[df["split"] == "val"]

    print("\nDistribucion por categoria (train | val):")
    for c, nom in NOMBRES.items():
        tr_c = train[train["cat"] == c]
        va_c = val[val["cat"] == c]
        dist_tr = tr_c["target_class"].value_counts().to_dict()
        print(f"   {nom:<14} train {len(tr_c):>6} {dist_tr} | val {len(va_c):>6}")

    n_val = len(val)
    p_val = np.zeros((n_val, 3))
    resumen_cat = {}
    t0 = time.time()

    for c in (0, 1, 2):
        tr = train[train["cat"] == c]
        va_mask = (val["cat"] == c).to_numpy()
        Xtr, Xva = tr[feats], val.loc[va_mask, feats]
        ytr = tr["y"].to_numpy()
        if c == 0:  # Junior: solo se_mantiene(1) / sube(2) -> binario
            ytr_bin = (ytr == 2).astype(int)
            modelo = xgb.XGBClassifier(objective="binary:logistic",
                                       eval_metric="logloss", **{
                                           k: v for k, v in PARAMS.items()
                                           if k not in ("objective", "eval_metric")})
            w = len(ytr_bin) / (2.0 * np.bincount(ytr_bin, minlength=2))
            modelo.fit(Xtr, ytr_bin, sample_weight=w[ytr_bin])
            p_sube = modelo.predict_proba(Xva)[:, 1]
            p_val[va_mask, 2] = p_sube
            p_val[va_mask, 1] = 1.0 - p_sube
            p_val[va_mask, 0] = 0.0
            clases_modelo = ["se_mantiene", "sube"]
        else:
            modelo = xgb.XGBClassifier(**PARAMS)
            conteo = np.bincount(ytr, minlength=3)
            w = len(ytr) / (3.0 * conteo)
            modelo.fit(Xtr, ytr, sample_weight=w[ytr])
            p_val[va_mask] = modelo.predict_proba(Xva)
            clases_modelo = list(mu.CLASES)
        yva = val.loc[va_mask, "y"].to_numpy()
        m = mu.metricas_completas(p_val[va_mask], yva)
        m_baja, _ = mu.umbral_baja(p_val[va_mask], yva)
        resumen_cat[NOMBRES[c]] = {
            "n_train": int(len(tr)), "n_val": int(va_mask.sum()),
            "clases_modelo": clases_modelo,
            "argmax": m,
            "umbral_f1_baja": {"t": m_baja["umbral"],
                               "f1_baja": m_baja["f1_baja_umbral"],
                               "precision": m_baja["precision_baja_umbral"],
                               "recall": m_baja["recall_baja_umbral"]},
        }
        print(f"\n--- {NOMBRES[c]} ({clases_modelo}) ---")
        print(f"   F1 macro={m['f1_macro']:.4f} | F1 baja={m['f1_por_clase']['baja']:.4f} | "
              f"F1 mantiene={m['f1_por_clase']['se_mantiene']:.4f} | "
              f"F1 sube={m['f1_por_clase']['sube']:.4f}")
        print(f"   AUC baja={m['auc_ovr']['baja']} | Brier={m['brier']:.4f}")
        if c == 0:
            print(f"   umbral F1 baja: t={m_baja['umbral']:.2f} "
                  f"(no aplica: IJ no tiene 'baja'; p_baja=0 por mascara)")

    segundos = time.time() - t0
    y_all = val["y"].to_numpy()
    m_all = mu.metricas_completas(p_val, y_all)
    m_all_umbral, _ = mu.umbral_baja(p_val, y_all)

    print("\n=== COMBINADO ponderado por n (todos los val) ===")
    print(f"   F1 macro={m_all['f1_macro']:.4f} | F1 baja={m_all['f1_por_clase']['baja']:.4f} | "
          f"F1 mantiene={m_all['f1_por_clase']['se_mantiene']:.4f} | "
          f"F1 sube={m_all['f1_por_clase']['sube']:.4f}")
    print(f"   precision baja={m_all['precision_baja']:.4f} | recall baja={m_all['recall_baja']:.4f}")
    print(f"   AUC baja={m_all['auc_ovr']['baja']:.4f} | Brier={m_all['brier']:.4f}")
    print(f"   con umbral optimizado t={m_all_umbral['umbral']:.2f}: "
          f"F1 baja={m_all_umbral['f1_baja_umbral']:.4f} "
          f"(prec {m_all_umbral['precision_baja_umbral']:.4f}, "
          f"rec {m_all_umbral['recall_baja_umbral']:.4f}) | "
          f"F1 macro={m_all_umbral['f1_macro']:.4f}")
    print(f"   matriz de confusion:\n      {m_all['confusion']}")
    print(f"   tiempo: {segundos:.1f} s")

    r1 = {"f1_macro": 0.3939, "f1_baja": 0.132, "auc_baja": 0.563, "brier": 0.5479}
    print(f"\n   vs r1: F1 macro {m_all['f1_macro']-r1['f1_macro']:+.4f} | "
          f"F1 baja {m_all['f1_por_clase']['baja']-r1['f1_baja']:+.4f} | "
          f"AUC baja {m_all['auc_ovr']['baja']-r1['auc_baja']:+.4f} | "
          f"Brier {m_all['brier']-r1['brier']:+.4f}")

    np.save(RESULTADOS / "p_xgb_mascaras.npy", p_val)
    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": 3, "modelo": "XGBoost con mascaras estructurales, sin 'ano'",
        "n_features": len(feats), "nota_features":
            "el r1 usa 173 features (no 25); sin 'ano' quedan 172",
        "params": {k: v for k, v in PARAMS.items() if k != "n_jobs"},
        "categorias": resumen_cat,
        "combinado": m_all,
        "combinado_umbral_f1_baja": m_all_umbral,
        "r1": r1,
        "segundos": round(segundos, 1),
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("paso3_xgb_mascaras_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
