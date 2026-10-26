#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
prueba_estructural.py
=====================

Fase 5, prueba estructural: modelos POR CATEGORIA DE ORIGEN (IJ, I, IS, IE)
frente al modelo global, en el split temporal (val = destino 2019).

Pregunta: ¿las dinamicas de transicion son distintas por categoria de origen,
hasta el punto de que un modelo global pierda señal que un modelo local
recupera? Si los modelos locales baten al global dentro de su categoria,
hay base para un jerarquico con partial pooling.

Solo train/val; test no se toca.

Uso:
    <python con xgboost> 07_modelo/modelado/prueba_estructural.py
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
ORDEN_NOMBRE = {12: "IJ (Junior)", 13: "I (Asociado)", 14: "IS (Senior)", 15: "IE (Emerito)"}


def f1s(y_true, y_pred, np, f1_score, labels):
    if not labels:
        return None
    return float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0))


def main() -> int:
    try:
        import joblib
        import numpy as np
        import pandas as pd
        from sklearn.metrics import f1_score
        import xgboost as xgb
    except ImportError as exc:
        print("ERROR: falta dependencia:", exc)
        print(f"Interprete actual: {sys.executable}")
        return 2

    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Interprete: {sys.executable}")
    print("REGLA: train/val; test no se toca.")
    resultados = {}

    for ds in ("ventana_contiguo", "acumulado_contiguo"):
        cfg = json.loads((MODELOS_DIR / f"config_{ds}.json").read_text(encoding="utf-8"))
        params = cfg["xgboost"]["mejor"]
        df = pd.read_parquet(DERIVADOS / f"modelo_dataset_{ds}.parquet")
        train = df[df["split"] == "train"].copy()
        val = df[df["split"] == "val"].copy()

        r1 = joblib.load(MODELOS_DIR / f"xgb_{ds}.joblib")
        feats = r1["features"]
        proba_g = r1["modelo"].predict_proba(val[feats])
        pred_g = [CLASES[i] for i in proba_g.argmax(axis=1)]
        val = val.assign(pred_global=pred_g)

        print(f"\n== {ds} ==  params r1: {params}")
        filas = {}
        for orden in (12, 13, 14, 15):
            tr = train[train["ORDEN_CLAS_PR_actual"] == orden]
            va = val[val["ORDEN_CLAS_PR_actual"] == orden]
            nombre = ORDEN_NOMBRE[orden]
            if len(va) == 0:
                filas[str(orden)] = {"categoria": nombre, "n_train": int(len(tr)),
                                     "n_val": 0, "nota": "sin filas en val (estado terminal o sin transicion)"}
                print(f"   {nombre}: sin filas en val")
                continue

            labels = [c for c in CLASES if (va["target_class"] == c).any()]
            y_tr = tr["target_class"].to_numpy()
            y_va = va["target_class"].to_numpy()
            clases_tr = sorted(set(y_tr))
            global_macro = f1s(y_va, va["pred_global"].to_numpy(), np, f1_score, labels)
            global_baja = (float(f1_score(y_va, va["pred_global"].to_numpy(),
                                          labels=["baja"], average="macro", zero_division=0))
                           if "baja" in labels else None)

            local_macro = None
            local_baja = None
            nota = None
            if len(clases_tr) < 2:
                nota = f"no se puede ajustar: train local con una sola clase {clases_tr}"
            else:
                clases_locales = sorted(set(y_tr))
                mapa = {c: i for i, c in enumerate(clases_locales)}
                yi_tr = np.array([mapa[c] for c in y_tr])
                conteo = np.bincount(yi_tr, minlength=len(clases_locales))
                w = len(yi_tr) / (len(clases_locales) * conteo)
                # Con 2 clases XGBClassifier usa binary:logistic; forzar
                # multi:softprob sin num_class es un error en xgboost 3.x.
                n_cl = len(clases_locales)
                objetivo = "multi:softprob" if n_cl > 2 else "binary:logistic"
                metrica = "mlogloss" if n_cl > 2 else "logloss"
                modelo = xgb.XGBClassifier(objective=objetivo, eval_metric=metrica,
                                           tree_method="hist", n_jobs=-1, random_state=42,
                                           verbosity=0, **params)
                modelo.fit(tr[feats], yi_tr, sample_weight=w[yi_tr])
                proba_l = modelo.predict_proba(va[feats])
                pred_l = [clases_locales[i] for i in proba_l.argmax(axis=1)]
                local_macro = f1s(y_va, pred_l, np, f1_score, labels)
                if "baja" in labels:
                    local_baja = float(f1_score(y_va, pred_l, labels=["baja"],
                                                average="macro", zero_division=0))

            filas[str(orden)] = {
                "categoria": nombre,
                "n_train": int(len(tr)), "n_val": int(len(va)),
                "n_baja_real": int((y_va == "baja").sum()),
                "clases_train": clases_tr,
                "labels_eval": labels,
                "global_f1_macro": global_macro,
                "global_f1_baja": global_baja,
                "local_f1_macro": local_macro,
                "local_f1_baja": local_baja,
                "delta_macro_pp": (None if local_macro is None else round(100 * (local_macro - global_macro), 2)),
                "delta_baja_pp": (None if local_baja is None else round(100 * (local_baja - global_baja), 2)),
                "nota": nota,
            }
            print(f"   {nombre:<16} n_train={len(tr):>5} n_val={len(va):>4} | "
                  f"global F1macro={global_macro:.3f} F1baja={global_baja if global_baja is None else round(global_baja,3)} | "
                  f"local F1macro={local_macro if local_macro is None else round(local_macro,3)} "
                  f"F1baja={local_baja if local_baja is None else round(local_baja,3)}"
                  + (f" | {nota}" if nota else ""))

        resultados[ds] = filas

    salida = RESULTADOS_DIR / f"prueba_estructural_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
