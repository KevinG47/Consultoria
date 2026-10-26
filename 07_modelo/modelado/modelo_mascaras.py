#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
modelo_mascaras.py
==================

Entrenador reutilizable del XGBoost con mascaras estructurales (sin 'ano'):

    IJ (Junior)   -> binario sube / se_mantiene (p_baja = 0 por estructura)
    I  (Asociado) -> tricotomo
    IS (Senior)   -> tricotomo
    IE (Emerico)  -> sin modelo (sin transiciones en los datos)

Se usa en los pasos A-E de la validacion honesta.
"""

from __future__ import annotations

import numpy as np

CAT_MAP = {12: 0, 13: 1, 14: 2, 15: 3}
PARAMS = dict(max_depth=7, learning_rate=0.05, n_estimators=200, subsample=0.8,
              tree_method="hist", n_jobs=-1, random_state=42, verbosity=0)
CLASES = ("baja", "se_mantiene", "sube")


def preparar(df):
    """Anade columnas 'cat' (categoria) e 'y' (indice de clase)."""
    df = df.copy()
    df["cat"] = df["ORDEN_CLAS_PR_actual"].map(CAT_MAP).astype(int)
    df["y"] = df["target_class"].map(lambda c: CLASES.index(c)).astype(int)
    return df


def entrenar(df_tr, feats, **over):
    """Devuelve (modelos por categoria, prevalencias de train)."""
    import xgboost as xgb

    params = dict(PARAMS)
    params.update(over)
    prev = np.bincount(df_tr["y"].to_numpy(), minlength=3) / len(df_tr)
    modelos = {}
    for c in (0, 1, 2):
        tr = df_tr[df_tr["cat"] == c]
        if len(tr) == 0:
            continue
        base = {k: v for k, v in params.items()
                if k not in ("objective", "eval_metric")}
        X = tr[feats]
        if c == 0:                      # Junior: binario
            yb = (tr["y"].to_numpy() == 2).astype(int)
            w = len(yb) / (2.0 * np.bincount(yb, minlength=2))
            m = xgb.XGBClassifier(objective="binary:logistic",
                                  eval_metric="logloss", **base)
            m.fit(X, yb, sample_weight=w[yb])
        else:                            # Asociado / Senior: tricotomo
            y = tr["y"].to_numpy()
            w = len(y) / (3.0 * np.bincount(y, minlength=3))
            m = xgb.XGBClassifier(objective="multi:softprob",
                                  eval_metric="mlogloss", **base)
            m.fit(X, y, sample_weight=w[y])
        modelos[c] = m
    return modelos, prev


def predecir(modelos, prev, df_pred, feats):
    """Matriz (n, 3) de probabilidades con la estructura aplicada."""
    p = np.tile(prev, (len(df_pred), 1))
    cats = df_pred["cat"].to_numpy()
    for c, m in modelos.items():
        mask = cats == c
        if not mask.any():
            continue
        X = df_pred.loc[mask, feats]
        if c == 0:
            ps = m.predict_proba(X)[:, 1]
            p[mask] = 0.0
            p[mask, 1] = 1.0 - ps
            p[mask, 2] = ps
        else:
            p[mask] = m.predict_proba(X)
    return p


def ganancias(modelos, feats):
    """Ganancia normalizada por modelo y suma agregada (dict feature -> gain)."""
    acc = {f: 0.0 for f in feats}
    detalle = {}
    for c, m in modelos.items():
        imp = m.feature_importances_          # gain normalizado de xgboost
        detalle[int(c)] = {f: float(v) for f, v in zip(feats, imp)}
        for f, v in zip(feats, imp):
            acc[f] += float(v)
    return acc, detalle
