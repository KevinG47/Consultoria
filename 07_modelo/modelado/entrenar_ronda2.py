#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
entrenar_ronda2.py
==================

Fase 5, ronda 2: seis mejoras sobre la ronda 1, SIN TOCAR TEST.

  1. Ablacion sin "ano".
  2. Umbrales optimizados por clase (sobre prob. del mejor modelo sin "ano").
  3. Cost-sensitive learning con matriz de costos explicita.
  4. Agrupacion de categorias/tipologias raras (< 50 apariciones en train).
  5. Ordinal encoding con XGBRegressor + discretizacion 0.5 / 1.5.
  6. Evaluacion por categoria de origen (IJ, I, IS, IE).

Requisitos: pandas, numpy, scikit-learn, xgboost, joblib, pyarrow.
Se ejecuta con el interprete que tenga xgboost (el script lo documenta).

Uso:
    <python con xgboost> 07_modelo/modelado/entrenar_ronda2.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
MODELOS_DIR = SCRIPT_DIR / "modelos"
RESULTADOS_DIR = SCRIPT_DIR / "resultados"

CLASES = ("baja", "se_mantiene", "sube")
ORDEN_NOMBRE = {12: "IJ (Junior)", 13: "I (Asociado)", 14: "IS (Senior)", 15: "IE (Emerito)"}
UMBRAL_RARAS = 50

FAMILIAS = {
    "n_clase_": "otras_clase",
    "n_tipologia_": "otras_tipologia",
    "n_categoria_": "otras_categoria",
}


def cargar_stack():
    import joblib
    import numpy as np
    import pandas as pd
    import pyarrow
    import sklearn
    from sklearn.metrics import confusion_matrix, f1_score, roc_auc_score
    import xgboost as xgb
    return {"joblib": joblib, "np": np, "pd": pd, "pyarrow": pyarrow,
            "sklearn": sklearn, "xgb": xgb, "f1_score": f1_score,
            "roc_auc_score": roc_auc_score, "confusion_matrix": confusion_matrix}


def metricas(y_true_str, pred_idx, np, f1_score, roc_auc_score, proba=None, scores=None):
    pred_str = [CLASES[i] for i in pred_idx]
    f1_macro = float(f1_score(y_true_str, pred_str, labels=list(CLASES),
                              average="macro", zero_division=0))
    f1_clase = f1_score(y_true_str, pred_str, labels=list(CLASES),
                        average=None, zero_division=0)
    auc = {}
    for i, clase in enumerate(CLASES):
        y_bin = (np.asarray(y_true_str) == clase).astype(int)
        if len(np.unique(y_bin)) < 2:
            auc[clase] = None
            continue
        puntaje = proba[:, i] if proba is not None else scores[:, i]
        auc[clase] = float(roc_auc_score(y_bin, puntaje))
    brier = None
    if proba is not None:
        yi = np.array([CLASES.index(c) for c in y_true_str])
        onehot = np.zeros_like(proba)
        onehot[np.arange(len(yi)), yi] = 1.0
        brier = float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))
    return {
        "f1_macro": f1_macro,
        "f1_por_clase": {c: float(v) for c, v in zip(CLASES, f1_clase)},
        "auc_ovr_por_clase": auc,
        "brier_multiclase": brier,
    }


def conf(y_true_str, pred_idx, confusion_matrix):
    return confusion_matrix(y_true_str, [CLASES[i] for i in pred_idx],
                            labels=list(CLASES)).tolist()


def buscar_umbrales(proba, y_true_str, np, f1_score):
    """Umbral sobre p(baja): si p_baja >= t -> baja; si no, argmax(mant, sube)."""
    i_baja = CLASES.index("baja")
    resto = proba.copy()
    resto[:, i_baja] = -1.0
    alt = resto.argmax(axis=1)
    mejor_macro = None
    mejor_baja = None
    for t in np.arange(0.01, 1.0, 0.01):
        pred = np.where(proba[:, i_baja] >= t, i_baja, alt)
        pred_str = [CLASES[i] for i in pred]
        f1m = float(f1_score(y_true_str, pred_str, labels=list(CLASES),
                             average="macro", zero_division=0))
        f1b = float(f1_score(y_true_str, pred_str, labels=["baja"],
                             average="macro", zero_division=0))
        if mejor_macro is None or f1m > mejor_macro["f1_macro"]:
            mejor_macro = {"umbral": round(float(t), 2), "f1_macro": f1m,
                           "f1_baja": f1b, "pred": pred}
        if mejor_baja is None or f1b > mejor_baja["f1_baja"]:
            mejor_baja = {"umbral": round(float(t), 2), "f1_baja": f1b,
                          "f1_macro": f1m, "pred": pred}
    return mejor_macro, mejor_baja


def agrupar_raras(train, val, features, umbral=UMBRAL_RARAS):
    """Agrupa one-hot con < umbral apariciones en train en columnas 'otras_*'."""
    raras_todas = set()
    nuevas = []
    for prefijo, nombre in FAMILIAS.items():
        cols = [c for c in features if c.startswith(prefijo)]
        if not cols:
            continue
        apariciones = (train[cols] > 0).sum(axis=0)
        raras = [c for c in cols if int(apariciones[c]) < umbral]
        if not raras:
            continue
        raras_todas |= set(raras)
        train[nombre] = (train[raras] > 0).any(axis=1).astype("int8")
        val[nombre] = (val[raras] > 0).any(axis=1).astype("int8")
        nuevas.append(nombre)
    feats = [c for c in features if c not in raras_todas] + nuevas
    return feats, sorted(raras_todas), nuevas


def main() -> int:
    try:
        stack = cargar_stack()
    except ImportError as exc:
        print("ERROR: falta una dependencia del modelado:", exc)
        print("  Use el interprete con xgboost (por ejemplo el venv-agente).")
        print(f"  Interprete actual: {sys.executable}")
        return 2

    pd, np, xgb = stack["pd"], stack["np"], stack["xgb"]
    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Interprete: {sys.executable}")
    print(f"xgboost {xgb.__version__} | pandas {pd.__version__} | "
          f"sklearn {stack['sklearn'].__version__} | numpy {np.__version__}")
    print("REGLA: solo train (ajuste) y val (seleccion); test no se toca.")

    versiones = {
        "xgboost": xgb.__version__,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit-learn": stack["sklearn"].__version__,
        "joblib": stack["joblib"].__version__,
        "pyarrow": stack["pyarrow"].__version__,
    }
    req = "\n".join(f"{k}=={v}" for k, v in versiones.items()) + "\n"
    (SCRIPT_DIR / "requirements_ronda2.txt").write_text(req, encoding="utf-8")

    resultados = {"fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "interprete": sys.executable, "versiones": versiones,
                  "ano_fuera": None, "datasets": {}}

    for ds in ("ventana_contiguo", "acumulado_contiguo"):
        cfg = json.loads((MODELOS_DIR / f"config_{ds}.json").read_text(encoding="utf-8"))
        df = pd.read_parquet(DERIVADOS / f"modelo_dataset_{ds}.parquet")
        train = df[df["split"] == "train"].copy()
        val = df[df["split"] == "val"].copy().reset_index(drop=True)
        if (df["split"] == "test").sum() > 0:
            print(f"\n[{ds}] test presente en el parquet; NO se usa")

        feats_r1 = cfg["features"]
        feats_na = [f for f in feats_r1 if f != "ano"]
        params = cfg["xgboost"]["mejor"]
        yi_train = np.array([CLASES.index(c) for c in train["target_class"]])
        yi_val = np.array([CLASES.index(c) for c in val["target_class"]])
        y_val = val["target_class"].to_numpy()
        i_baja = CLASES.index("baja")

        print(f"\n== {ds} ==  train {len(train):,} | val {len(val):,} | "
              f"params {params}".replace(",", " "))

        variantes = {}

        # Ronda 1: metrica guardada (referencia)
        r1 = cfg["xgboost"]
        variantes["r1"] = {
            "f1_macro": r1["f1_macro"], "f1_por_clase": r1["f1_por_clase"],
            "auc_ovr_por_clase": r1["auc_ovr_por_clase"],
            "brier_multiclase": r1["brier_multiclase"],
            "n_features": len(feats_r1), "params": params, "segundos": None,
            "confusion": None, "nota": "ronda 1 (con ano), tomado del config",
        }

        def ajustar(feats, pesos=None):
            t0 = time.time()
            modelo = xgb.XGBClassifier(objective="multi:softprob", eval_metric="mlogloss",
                                       tree_method="hist", n_jobs=-1, random_state=42,
                                       verbosity=0, **params)
            modelo.fit(train[feats], yi_train, sample_weight=pesos)
            proba = modelo.predict_proba(val[feats])
            return modelo, proba, round(time.time() - t0, 2)

        # 1. sin ano
        m2, p2, t2 = ajustar(feats_na)
        pred2 = p2.argmax(axis=1)
        variantes["sin_ano"] = {**metricas(y_val, pred2, np, stack["f1_score"],
                                           stack["roc_auc_score"], proba=p2),
                                "n_features": len(feats_na), "params": params,
                                "segundos": t2, "confusion": conf(y_val, pred2, stack["confusion_matrix"]),
                                "nota": "ablacion: sin ano"}
        print(f"   sin_ano: F1 macro={variantes['sin_ano']['f1_macro']:.4f} "
              f"(r1 {r1['f1_macro']:.4f}) | AUC baja={variantes['sin_ano']['auc_ovr_por_clase']['baja']}")

        # 3. cost-sensitive
        costos = np.array([[0, 5, 5], [1, 0, 1], [3, 3, 0]], dtype=float)
        w_clase = costos.sum(axis=1)
        w_clase = w_clase / w_clase.mean()
        w_train = w_clase[yi_train]
        m3, p3, t3 = ajustar(feats_na, w_train)
        pred3 = p3.argmax(axis=1)
        variantes["cost_sensitive"] = {**metricas(y_val, pred3, np, stack["f1_score"],
                                                  stack["roc_auc_score"], proba=p3),
                                       "n_features": len(feats_na), "params": params,
                                       "segundos": t3,
                                       "confusion": conf(y_val, pred3, stack["confusion_matrix"]),
                                       "nota": f"costos C={costos.tolist()}, pesos={np.round(w_clase,3).tolist()}"}
        print(f"   cost_sensitive: F1 macro={variantes['cost_sensitive']['f1_macro']:.4f} "
              f"| AUC baja={variantes['cost_sensitive']['auc_ovr_por_clase']['baja']}")

        # 4. agrupar raras sobre el mejor de (1,3)
        base_nombre = ("cost_sensitive" if variantes["cost_sensitive"]["f1_macro"]
                       > variantes["sin_ano"]["f1_macro"] else "sin_ano")
        pesos_base = w_train if base_nombre == "cost_sensitive" else None
        feats_raras, raras, nuevas = agrupar_raras(train, val, feats_na)
        m4, p4, t4 = ajustar(feats_raras, pesos_base)
        pred4 = p4.argmax(axis=1)
        variantes["raras"] = {**metricas(y_val, pred4, np, stack["f1_score"],
                                         stack["roc_auc_score"], proba=p4),
                              "n_features": len(feats_raras), "params": params,
                              "segundos": t4,
                              "confusion": conf(y_val, pred4, stack["confusion_matrix"]),
                              "nota": f"base={base_nombre}; {len(raras)} columnas raras -> {nuevas}"}
        print(f"   raras (base {base_nombre}): F1 macro={variantes['raras']['f1_macro']:.4f} "
              f"| features {len(feats_raras)} (raras {len(raras)})")

        # combinacion cost + raras (si no es ya la de arriba)
        if base_nombre == "sin_ano":
            m7, p7, t7 = ajustar(feats_raras, w_train)
            pred7 = p7.argmax(axis=1)
            variantes["cost_raras"] = {**metricas(y_val, pred7, np, stack["f1_score"],
                                                  stack["roc_auc_score"], proba=p7),
                                       "n_features": len(feats_raras), "params": params,
                                       "segundos": t7,
                                       "confusion": conf(y_val, pred7, stack["confusion_matrix"]),
                                       "nota": "cost-sensitive + raras"}
            print(f"   cost_raras: F1 macro={variantes['cost_raras']['f1_macro']:.4f}")

        # 5. ordinal
        t0 = time.time()
        reg = xgb.XGBRegressor(objective="reg:squarederror", tree_method="hist",
                               n_jobs=-1, random_state=42, verbosity=0, **params)
        reg.fit(train[feats_na], yi_train.astype(float))
        pred_raw = reg.predict(val[feats_na])
        pred5 = np.digitize(pred_raw, [0.5, 1.5])
        scores = np.column_stack([-pred_raw, -np.abs(pred_raw - 1.0), pred_raw])
        variantes["ordinal"] = {**metricas(y_val, pred5, np, stack["f1_score"],
                                           stack["roc_auc_score"], scores=scores),
                                "n_features": len(feats_na), "params": params,
                                "segundos": round(time.time() - t0, 2),
                                "confusion": conf(y_val, pred5, stack["confusion_matrix"]),
                                "nota": "XGBRegressor reg:squarederror; cortes 0.5/1.5; Brier no aplica"}
        print(f"   ordinal: F1 macro={variantes['ordinal']['f1_macro']:.4f} "
              f"| AUC baja={variantes['ordinal']['auc_ovr_por_clase']['baja']}")

        # 2. umbrales sobre el mejor de (sin_ano, raras)
        nombre_umbral = ("raras" if variantes["raras"]["f1_macro"]
                         > variantes["sin_ano"]["f1_macro"] else "sin_ano")
        proba_u = p4 if nombre_umbral == "raras" else p2
        mejor_macro, mejor_baja = buscar_umbrales(proba_u, y_val, np, stack["f1_score"])
        conv = stack["confusion_matrix"]
        umbrales = {
            "base": nombre_umbral,
            "macro": {"umbral": mejor_macro["umbral"],
                      "f1_macro": mejor_macro["f1_macro"],
                      "f1_baja": float(stack["f1_score"](y_val,
                                                        [CLASES[i] for i in mejor_macro["pred"]],
                                                        labels=["baja"], average="macro",
                                                        zero_division=0)),
                      "confusion": conf(y_val, mejor_macro["pred"], conv)},
            "baja": {"umbral": mejor_baja["umbral"],
                     "f1_macro": mejor_baja["f1_macro"],
                     "f1_baja": mejor_baja["f1_baja"],
                     "confusion": conf(y_val, mejor_baja["pred"], conv)},
            "argmax": {"f1_macro": variantes[nombre_umbral]["f1_macro"],
                       "f1_baja": variantes[nombre_umbral]["f1_por_clase"]["baja"],
                       "confusion": variantes[nombre_umbral]["confusion"]},
        }
        variantes["umbral_macro"] = {
            "f1_macro": mejor_macro["f1_macro"],
            "f1_por_clase": {c: float(v) for c, v in zip(
                CLASES, stack["f1_score"](y_val, [CLASES[i] for i in mejor_macro["pred"]],
                                          labels=list(CLASES), average=None, zero_division=0))},
            "auc_ovr_por_clase": variantes[nombre_umbral]["auc_ovr_por_clase"],
            "brier_multiclase": variantes[nombre_umbral]["brier_multiclase"],
            "n_features": len(feats_raras if nombre_umbral == "raras" else feats_na),
            "params": params, "segundos": None,
            "confusion": umbrales["macro"]["confusion"],
            "nota": f"umbral p(baja)>={mejor_macro['umbral']} sobre {nombre_umbral}",
        }
        variantes["umbral_baja"] = {
            "f1_macro": mejor_baja["f1_macro"],
            "f1_por_clase": {c: float(v) for c, v in zip(
                CLASES, stack["f1_score"](y_val, [CLASES[i] for i in mejor_baja["pred"]],
                                          labels=list(CLASES), average=None, zero_division=0))},
            "auc_ovr_por_clase": variantes[nombre_umbral]["auc_ovr_por_clase"],
            "brier_multiclase": variantes[nombre_umbral]["brier_multiclase"],
            "n_features": len(feats_raras if nombre_umbral == "raras" else feats_na),
            "params": params, "segundos": None,
            "confusion": umbrales["baja"]["confusion"],
            "nota": f"umbral p(baja)>={mejor_baja['umbral']} sobre {nombre_umbral}",
        }
        print(f"   umbral macro={mejor_macro['umbral']} -> F1 macro={mejor_macro['f1_macro']:.4f}; "
              f"umbral baja={mejor_baja['umbral']} -> F1 baja={mejor_baja['f1_baja']:.4f} "
              f"(argmax F1 baja={variantes[nombre_umbral]['f1_por_clase']['baja']:.4f})")

        # 6. mejor variante y evaluacion por origen (r1 no tiene predicciones)
        candidatas = {k: v for k, v in variantes.items() if k != "r1"}
        mejor_nombre = max(candidatas, key=lambda k: candidatas[k]["f1_macro"])
        preds = {
            "sin_ano": pred2, "cost_sensitive": pred3, "raras": pred4,
            "ordinal": pred5, "umbral_macro": mejor_macro["pred"],
            "umbral_baja": mejor_baja["pred"],
        }
        if "cost_raras" in variantes:
            preds["cost_raras"] = pred7
        pred_mejor = preds[mejor_nombre]
        pred_str = [CLASES[i] for i in pred_mejor]

        por_origen = {}
        for orden, grupo in val.groupby("ORDEN_CLAS_PR_actual"):
            pos = grupo.index.to_numpy()
            y_g = grupo["target_class"].to_numpy()
            p_g = [pred_str[i] for i in pos]
            f1b = float(stack["f1_score"](y_g, p_g, labels=["baja"],
                                          average="macro", zero_division=0))
            por_origen[str(int(orden))] = {
                "categoria": ORDEN_NOMBRE.get(int(orden), str(orden)),
                "n": int(len(grupo)),
                "n_baja_real": int((y_g == "baja").sum()),
                "n_pred_baja": int(sum(1 for x in p_g if x == "baja")),
                "f1_baja": f1b,
                "f1_macro": float(stack["f1_score"](y_g, p_g, labels=list(CLASES),
                                                     average="macro", zero_division=0)),
                "confusion": stack["confusion_matrix"](y_g, p_g,
                                                       labels=list(CLASES)).tolist(),
            }
        print(f"   mejor variante: {mejor_nombre} (F1 macro={variantes[mejor_nombre]['f1_macro']:.4f})")
        print("   F1 baja por origen: " + " · ".join(
            f"{v['categoria']}={v['f1_baja']:.3f} (n={v['n']})" for v in por_origen.values()))

        # guardar el mejor modelo (se reajusta si hace falta)
        if mejor_nombre == "sin_ano":
            modelo_final, feats_final = m2, feats_na
        elif mejor_nombre == "cost_sensitive":
            modelo_final, feats_final = m3, feats_na
        elif mejor_nombre == "raras":
            modelo_final, feats_final = m4, feats_raras
        elif mejor_nombre == "cost_raras":
            modelo_final, feats_final = m7, feats_raras
        else:  # umbral/ordinal: se guarda el modelo base y se anota el umbral
            modelo_final, feats_final = (m4, feats_raras) if nombre_umbral == "raras" else (m2, feats_na)
        stack["joblib"].dump({"modelo": modelo_final, "features": feats_final,
                              "clases": list(CLASES), "variante": mejor_nombre},
                             MODELOS_DIR / f"ronda2_{ds}.joblib")

        resultados["datasets"][ds] = {
            "n_train": int(len(train)), "n_val": int(len(val)),
            "variantes": variantes, "umbrales": umbrales,
            "mejor": mejor_nombre, "por_origen": por_origen,
            "features_raras": {"n_raras": len(raras), "nuevas": nuevas,
                               "n_features_final": len(feats_raras)},
        }

    # decision sobre ano
    deltas = {}
    for ds, r in resultados["datasets"].items():
        deltas[ds] = round(r["variantes"]["sin_ano"]["f1_macro"]
                           - r["variantes"]["r1"]["f1_macro"], 4)
    resultados["delta_sin_ano"] = deltas
    resultados["ano_fuera"] = all(d > 0.03 for d in deltas.values())
    print(f"\nDelta F1 macro sin ano: {deltas} -> ano fuera: {resultados['ano_fuera']}")

    salida = RESULTADOS_DIR / f"ronda2_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    print("requirements_ronda2.txt escrito con las versiones exactas.")
    print("\nSiguiente paso:\n   <python con xgboost> 07_modelo/modelado/evaluar_ronda2.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
