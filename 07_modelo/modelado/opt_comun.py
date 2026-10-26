#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
opt_comun.py
============

Utilidades de la ronda de mejora SOLO con validacion temporal (test intacto).

Folds (todos pre-test: cohortes 17,18,19,20):
    F1: train 17        | val 18 | eval 19
    F2: train 17,18     | val 19 | eval 20
    F3: train 18        | val 19 | eval 20   (menos historia que F2)

Test = cohorte 21. No se toca en A-D.
"""

from __future__ import annotations

import numpy as np

CLASES = ("baja", "se_mantiene", "sube")
CAT_MAP = {12: 0, 13: 1, 14: 2, 15: 3}
FOLDS = [
    ("F1", [17], [18], [19]),
    ("F2", [17, 18], [19], [20]),
    ("F3", [18], [19], [20]),
]
BASE = dict(tree_method="hist", n_jobs=4, random_state=42, verbosity=0)
GRID = np.round(np.arange(0.01, 1.0, 0.01), 2)


def cargar():
    """df con columnas cat/y + lista de features del r1 sin 'ano'."""
    import joblib
    import pandas as pd

    from pathlib import Path
    script_dir = Path(__file__).resolve().parent
    df = pd.read_parquet(script_dir.parent / "datos" / "derivados" /
                         "modelo_dataset_ventana_contiguo.parquet")
    cont = joblib.load(script_dir / "modelos" / "xgb_ventana_contiguo.joblib")
    feats = [f for f in cont["features"] if f != "ano"]
    df["cat"] = df["ORDEN_CLAS_PR_actual"].map(CAT_MAP).astype(int)
    df["y"] = df["target_class"].map(lambda c: CLASES.index(c)).astype(int)
    return df, feats


def matriz(df, cols):
    return df[cols].to_numpy(dtype="float32")


def ganancias(modelos, n_features):
    acc = np.zeros(n_features)
    for m in modelos.values():
        acc += m.feature_importances_
    return acc


CENSO = None


def demo_features(df):
    """Variables demograficas del censo, alineadas al indice de df."""
    import pandas as pd
    from pathlib import Path

    global CENSO
    if CENSO is None:
        CENSO = (Path(__file__).resolve().parents[2] / "01_datos" / "datos_fuente" /
                 "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
    cols = ["ID_PERSONA_PR", "ID_CONVOCATORIA", "NME_GENERO_PR", "EDAD_ANOS_PR",
            "NME_DEPARTAMENTO_RES_PR", "INST_FILIA"]
    c = pd.read_csv(CENSO, usecols=cols, dtype=str, encoding="utf-8-sig",
                    keep_default_na=False)
    c["ID_PERSONA_PR"] = c["ID_PERSONA_PR"].str.strip().str.zfill(10)
    c["ID_CONVOCATORIA"] = pd.to_numeric(c["ID_CONVOCATORIA"], errors="coerce")
    c = c.drop_duplicates(["ID_PERSONA_PR", "ID_CONVOCATORIA"])

    base = pd.DataFrame({"ID_PERSONA_PR": df["ID_PERSONA_PR"].astype(str).str.zfill(10),
                         "ID_CONVOCATORIA": pd.to_numeric(df["ID_CONVOCATORIA"],
                                                          errors="coerce")})
    m = base.merge(c, on=["ID_PERSONA_PR", "ID_CONVOCATORIA"], how="left")
    m.index = df.index

    gen = m["NME_GENERO_PR"].fillna("").str.strip()
    out = pd.DataFrame(index=df.index)
    out["genero_masculino"] = (gen == "Masculino").astype("float32")
    out["genero_femenino"] = (gen == "Femenino").astype("float32")
    out["genero_desconocido"] = (~gen.isin(["Masculino", "Femenino"])).astype("float32")

    edad = pd.to_numeric(m["EDAD_ANOS_PR"].fillna("").str.replace(",", "."),
                         errors="coerce")
    out["edad_faltante"] = edad.isna().astype("float32")
    med = float(edad.median())
    out["edad"] = edad.fillna(med).astype("float32")

    dep = m["NME_DEPARTAMENTO_RES_PR"].fillna("").str.strip().str.upper()
    top_dep = dep.value_counts().head(8).index.tolist()
    for i, d in enumerate(top_dep):
        out[f"depto_{i}"] = (dep == d).astype("float32")
    out["depto_otras"] = (~dep.isin(top_dep) & (dep != "")).astype("float32")
    out["depto_faltante"] = (dep == "").astype("float32")

    inst = m["INST_FILIA"].fillna("").str.strip().str.upper()
    top_inst = inst.value_counts().head(10).index.tolist()
    for i, s in enumerate(top_inst):
        out[f"inst_{i}"] = (inst == s).astype("float32")
    out["inst_otras"] = (~inst.isin(top_inst) & (inst != "")).astype("float32")
    out["inst_faltante"] = (inst == "").astype("float32")
    return out


def mejor_t_baja(p0, y):
    """Umbral (0.01..0.99) que maximiza F1 de 'baja' para p(baja)=p0."""
    yb = (y == 0)
    npos = int(yb.sum())
    mejor = (0.0, 0.0)
    for t in GRID:
        sel = p0 >= t
        tp = int(np.sum(sel & yb))
        if tp == 0:
            continue
        prec = tp / int(sel.sum())
        rec = tp / npos
        f1 = 2 * prec * rec / (prec + rec)
        if f1 > mejor[0]:
            mejor = (float(f1), float(t))
    return mejor[1], mejor[0]


def pred_umbral(p, t):
    return np.where(p[:, 0] >= t, 0, np.where(p[:, 1] >= p[:, 2], 1, 2))


def entrenar_cat(X, y, cats, mask, params):
    """Entrena los modelos por categoria dentro de 'mask'. Devuelve dict.

    Si una categoria no tiene al menos 2 clases en train, no se entrena y sus
    filas quedan con la prevalencia de train (prior).
    """
    import xgboost as xgb

    modelos = {}
    base = {k: v for k, v in params.items()
            if k not in ("objective", "eval_metric")}
    for c in (0, 1, 2):
        sel = mask & (cats == c)
        if sel.sum() < 50:
            continue
        Xc = X[sel]
        if c == 0:
            yb = (y[sel] == 2).astype(int)
            conteo = np.maximum(np.bincount(yb, minlength=2), 1)
            if len(np.unique(yb)) < 2:
                continue
            w = len(yb) / (2.0 * conteo)
            m = xgb.XGBClassifier(objective="binary:logistic",
                                  eval_metric="logloss", **base)
            m.fit(Xc, yb, sample_weight=w[yb])
        else:
            yc = y[sel]
            if len(np.unique(yc)) < 2:
                continue
            conteo = np.maximum(np.bincount(yc, minlength=3), 1)
            w = len(yc) / (3.0 * conteo)
            m = xgb.XGBClassifier(objective="multi:softprob", num_class=3,
                                  eval_metric="mlogloss", **base)
            m.fit(Xc, yc, sample_weight=w[yc])
        modelos[c] = m
    return modelos


def predecir_cat(modelos, X, cats, mask, prior):
    n = int(mask.sum())
    p = np.tile(prior, (n, 1))
    sub_cats = cats[mask]
    sub_X = X[mask]
    for c, m in modelos.items():
        s = sub_cats == c
        if not s.any():
            continue
        raw = m.predict_proba(sub_X[s])
        if c == 0:
            ps = raw[:, 1]
            p[s] = 0.0
            p[s, 1] = 1.0 - ps
            p[s, 2] = ps
        else:
            # el modelo puede haber visto solo 2 clases: recolocar columnas
            clases = list(getattr(m, "classes_", np.arange(raw.shape[1])))
            bloque = np.zeros((raw.shape[0], 3))
            for j, k in enumerate(clases):
                bloque[:, int(k)] = raw[:, j]
            p[s] = bloque
    return p


def correr_fold(X, y, cat, per, fold, params):
    """Entrena en el train del fold, elige t en val y evalua OOS en eval."""
    _, tr_p, va_p, ev_p = fold
    m_tr = np.isin(per, tr_p)
    m_va = per == va_p[0]
    m_ev = per == ev_p[0]
    prior = np.bincount(y[m_tr], minlength=3) / m_tr.sum()
    modelos = entrenar_cat(X, y, cat, m_tr, params)
    p_va = predecir_cat(modelos, X, cat, m_va, prior)
    p_ev = predecir_cat(modelos, X, cat, m_ev, prior)
    t, f1_va = mejor_t_baja(p_va[:, 0], y[m_va])
    return t, f1_va, p_va, p_ev, y[m_ev]


def metricas_eval(p, y, t):
    from sklearn.metrics import f1_score

    pred = pred_umbral(p, t)
    y_str = np.array([CLASES[i] for i in y])
    pred_str = np.array([CLASES[i] for i in pred])
    f1 = f1_score(y_str, pred_str, labels=list(CLASES), average=None, zero_division=0)
    onehot = np.eye(3)[y]
    yb = y == 0
    sel = pred == 0
    tp = int(np.sum(sel & yb))
    prec = tp / max(int(sel.sum()), 1)
    rec = tp / max(int(yb.sum()), 1)
    return {
        "f1_baja": float(f1[0]),
        "f1_macro": float(np.mean(f1)),
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "precision_baja": float(prec),
        "recall_baja": float(rec),
    }
