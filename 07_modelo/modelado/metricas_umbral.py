#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
metricas_umbral.py
==================

Utilidades compartidas por los pasos 1-5 de la ronda de mejora:

- probabilidades en VAL del bayesiano minimo (trace_bayesiano_minimo.nc),
- probabilidades en VAL del XGBoost r1 (xgb_ventana_contiguo.joblib),
- metricas completas (F1 macro, F1 por clase, precision/recall de "baja",
  AUC OvR, Brier multiclase),
- busqueda de umbrales/pesos que maximizan F1 de "baja" y F1 macro.

Nunca carga el split test.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

_CACHE_DIR = SCRIPT_DIR.parent / ".cache"
_CACHE_DIR.mkdir(exist_ok=True)
os.environ.setdefault("LOCALAPPDATA", str(_CACHE_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_DIR / "matplotlib"))
try:  # ArviZ cachea via platformdirs: redirigir ANTES de importar arviz
    import platformdirs as _pd
    _orig_ucd = _pd.user_cache_dir

    def _ucd(appname=None, appauthor=None, version=None, roaming=False):
        if appname == "arviz":
            return str(_CACHE_DIR / "arviz")
        return _orig_ucd(appname, appauthor, version, roaming)

    _pd.user_cache_dir = _ucd
except Exception:  # pragma: no cover
    pass

CLASES = ("baja", "se_mantiene", "sube")
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
MODELOS_DIR = SCRIPT_DIR / "modelos"
EXCLUIR = [
    "ID_PERSONA_PR", "ID_CONVOCATORIA", "ID_CONVOCATORIA_siguiente",
    "ORDEN_CLAS_PR_actual", "ORDEN_CLAS_PR_siguiente", "target_class",
    "split", "gap", "contiguo", "dias_desde_ultimo_negativo", "sin_produccion",
]

GRID_T = np.round(np.arange(0.01, 1.0, 0.01), 2)


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------
def cargar_df(pd):
    df = pd.read_parquet(DERIVADOS / "modelo_dataset_ventana_contiguo.parquet")
    return df[df["split"].isin(["train", "val"])].copy()   # test nunca se carga


def features_r1(df, pd):
    """Reproduce la lista de features de la ronda 1 (sin constantes en train)."""
    train = df[df["split"] == "train"]
    feats = [c for c in df.columns if c not in EXCLUIR]
    constantes = [c for c in feats if train[c].nunique(dropna=False) <= 1]
    return [c for c in feats if c not in constantes], constantes


def probabilidades_bayesiano(np_mod=None):
    """p (n_val, 3) del bayesiano minimo + y (indices) + df/val."""
    import pandas as pd
    import arviz as az
    import entrenar_bayesiano_minimo as em

    df = cargar_df(pd)
    datos = em.construir_features(df, em.cargar_censo(pd), pd, np)
    idata = az.from_netcdf(MODELOS_DIR / "trace_bayesiano_minimo.nc")
    pred = em.predecir_val(idata, datos, np)
    return pred["p_mean"], datos["y_val"], df, datos


def cargar_xgb_r1(pd):
    """Modelo r1 entrenado (joblib: dict con 'modelo' y 'features') + X_val + y."""
    import joblib

    df = cargar_df(pd)
    contenedor = joblib.load(MODELOS_DIR / "xgb_ventana_contiguo.joblib")
    xgb = contenedor["modelo"]
    feats = list(contenedor["features"])
    val = df[df["split"] == "val"]
    X_val = val[feats]
    y = np.array([CLASES.index(c) for c in val["target_class"]])
    return xgb, X_val, y, feats, val


# --------------------------------------------------------------------------
# Metricas
# --------------------------------------------------------------------------
def _conf(y, pred):
    m = np.zeros((3, 3), dtype=int)
    for t, p in zip(y, pred):
        m[t, p] += 1
    return m


def metricas_completas(p, y, pred=None):
    from sklearn.metrics import f1_score, roc_auc_score, precision_score, recall_score

    if pred is None:
        pred = p.argmax(axis=1)
    y_str = np.array([CLASES[i] for i in y])
    pred_str = np.array([CLASES[i] for i in pred])
    f1 = f1_score(y_str, pred_str, labels=list(CLASES), average=None, zero_division=0)
    auc = {}
    for i, c in enumerate(CLASES):
        yb = (y == i).astype(int)
        auc[c] = float(roc_auc_score(yb, p[:, i])) if len(np.unique(yb)) > 1 else None
    onehot = np.eye(3)[y]
    return {
        "f1_macro": float(f1_score(y_str, pred_str, labels=list(CLASES),
                                   average="macro", zero_division=0)),
        "f1_por_clase": {c: float(v) for c, v in zip(CLASES, f1)},
        "precision_baja": float(precision_score(y == 0, pred == 0, zero_division=0)),
        "recall_baja": float(recall_score(y == 0, pred == 0, zero_division=0)),
        "auc_ovr": auc,
        "auc_baja": auc["baja"],
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "exactitud": float(np.mean(pred == y)),
        "pred_baja_pct": float(np.mean(pred == 0)),
        "confusion": _conf(y, pred).tolist(),
    }


# --------------------------------------------------------------------------
# Umbrales
# --------------------------------------------------------------------------
def umbral_baja(p, y, grid=GRID_T):
    """Umbral t sobre p(baja): predice 'baja' si p0 >= t; si no, argmax(p1,p2)."""
    mejor = None
    for t in grid:
        pred = np.where(p[:, 0] >= t, 0,
                        np.where(p[:, 1] >= p[:, 2], 1, 2))
        tp = int(np.sum((pred == 0) & (y == 0)))
        fp = int(np.sum((pred == 0) & (y != 0)))
        fn = int(np.sum((pred != 0) & (y == 0)))
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1b = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        cand = (f1b, rec, prec, t, pred)
        if mejor is None or cand[:2] > mejor[:2]:
            mejor = cand
    f1b, rec, prec, t, pred = mejor
    m = metricas_completas(p, y, pred)
    m.update({"umbral": float(t), "f1_baja_umbral": float(f1b),
              "precision_baja_umbral": float(prec),
              "recall_baja_umbral": float(rec)})
    return m, pred


def pesos_macro(p, y):
    """Escala por clase w=(w_baja,1,w_sube); pred=argmax(w*p). Equivale a t_k=1/w_k."""
    def f1_macro_rapido(pred):
        conf = np.zeros((3, 3), dtype=np.int64)
        np.add.at(conf, (y, pred), 1)
        f1s = []
        for k in range(3):
            den = conf[:, k].sum() + conf[k, :].sum()
            f1s.append(2.0 * conf[k, k] / den if den else 0.0)
        return float(np.mean(f1s))

    mejor = None
    for w0 in np.round(np.logspace(0, 1.85, 45), 4):        # 1 .. ~70
        for w2 in np.round(np.logspace(0, 1.4, 30), 4):     # 1 .. ~25
            pred = np.argmax(np.column_stack([w0 * p[:, 0], p[:, 1], w2 * p[:, 2]]), axis=1)
            f1m = f1_macro_rapido(pred)
            if mejor is None or f1m > mejor[0]:
                mejor = (f1m, pred, w0, w2)
    _, pred, w0, w2 = mejor
    m = metricas_completas(p, y, pred)
    m.update({"w_baja": float(w0), "w_sube": float(w2),
              "t_baja_equiv": float(1 / w0), "t_sube_equiv": float(1 / w2)})
    return m, pred
