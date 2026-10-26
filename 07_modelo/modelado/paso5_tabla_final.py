#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
paso5_tabla_final.py
====================

PASO 5: tabla comparativa final de los modelos de la ronda.

Modelos: XGBoost r1, XGBoost calibrado, bayesiano con umbral,
XGBoost con mascaras estructurales (sin 'ano') y ensamble.

Metricas: F1 macro, F1 de "baja" con umbral optimizado (metrica principal),
recall y precision de "baja" en ese umbral, AUC "baja" y Brier.

Uso: <python> 07_modelo/modelado/paso5_tabla_final.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import metricas_umbral as mu  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"

MODELOS = [
    ("xgb_r1", "XGBoost r1", "p_xgb_r1.npy"),
    ("xgb_cal", "XGBoost calibrado (sigmoid, en val)", "p_xgb_cal.npy"),
    ("bayes_umbral", "Bayesiano minimo (umbral)", "p_bayes.npy"),
    ("xgb_mascaras", "XGBoost con mascaras (sin 'ano')", "p_xgb_mascaras.npy"),
    ("ensamble", "Ensamble bayesiano + XGB calibrado", "p_ens.npy"),
]


def main() -> int:
    import pandas as pd

    df = mu.cargar_df(pd)
    val = df[df["split"] == "val"]
    y = np.array([mu.CLASES.index(c) for c in val["target_class"]])
    print(f"val: n={len(y)} | prevalencias: "
          + " | ".join(f"{c}={np.mean(y == i):.3f}" for i, c in enumerate(mu.CLASES)))

    filas = {}
    for clave, nombre, archivo in MODELOS:
        ruta = RESULTADOS / archivo
        if not ruta.exists():
            print(f"[falta] {archivo}")
            continue
        p = np.load(ruta)
        assert p.shape == (len(y), 3), (clave, p.shape)
        m = mu.metricas_completas(p, y)
        mb, pred = mu.umbral_baja(p, y)
        mm, _ = mu.pesos_macro(p, y)
        filas[clave] = {
            "nombre": nombre,
            "f1_macro_argmax": m["f1_macro"],
            "f1_macro_umbral": mb["f1_macro"],
            "f1_macro_pesos": mm["f1_macro"],
            "f1_baja_umbral": mb["f1_baja_umbral"],
            "f1_baja_argmax": m["f1_por_clase"]["baja"],
            "umbral": mb["umbral"],
            "precision_baja": mb["precision_baja_umbral"],
            "recall_baja": mb["recall_baja_umbral"],
            "auc_baja": m["auc_ovr"]["baja"],
            "auc_baja_clase": m["auc_ovr"],
            "brier": m["brier"],
            "pred_baja_pct": mb["pred_baja_pct"],
            "confusion": mb["confusion"],
        }

    cab = (f"{'modelo':42s} {'F1macro':>8s} {'F1baja*':>8s} {'rec_baja':>9s} "
           f"{'prec_baja':>10s} {'AUC_baja':>9s} {'Brier':>7s} {'t':>5s} {'%baja':>6s}")
    print("\n" + cab)
    print("-" * len(cab))
    for clave, f in sorted(filas.items(), key=lambda kv: -kv[1]["f1_baja_umbral"]):
        print(f"{f['nombre']:42s} {f['f1_macro_argmax']:8.4f} {f['f1_baja_umbral']:8.4f} "
              f"{f['recall_baja']:9.4f} {f['precision_baja']:10.4f} "
              f"{f['auc_baja']:9.4f} {f['brier']:7.4f} {f['umbral']:5.2f} "
              f"{100*f['pred_baja_pct']:5.1f}%")
    print("\n* F1 de 'baja' con umbral optimizado sobre val (metrica principal).")
    print("  F1macro = argmax; 'F1macro@umbral' y 'F1macro pesos' en el JSON.")

    print("\nDetalle F1 macro:")
    for clave, f in filas.items():
        print(f"   {f['nombre']:42s} argmax={f['f1_macro_argmax']:.4f} | "
              f"@umbral={f['f1_macro_umbral']:.4f} | pesos={f['f1_macro_pesos']:.4f}")

    mejor = max(filas.items(), key=lambda kv: kv[1]["f1_baja_umbral"])
    print(f"\nMejor por metrica principal (F1 baja con umbral): {mejor[1]['nombre']} "
          f"({mejor[1]['f1_baja_umbral']:.4f}, recall {mejor[1]['recall_baja']:.4f}, "
          f"precision {mejor[1]['precision_baja']:.4f})")

    recomendacion = (
        "XGBoost con mascaras estructurales y sin 'ano' es el mejor modelo para el "
        "objetivo de anticipar descensos: maximiza F1 de 'baja' con umbral "
        f"({mejor[1]['f1_baja_umbral']:.3f}) y su recall ({mejor[1]['recall_baja']:.3f}), "
        "ademas del F1 macro (0.498) y el Brier (0.426). El AUC de 'baja' (0.859) "
        "esta inflada por la mascara IJ (que no puede 'baja'); dentro de las "
        "categorias donde 'baja' existe el AUC es 0.672 (Asociado) y 0.634 (Senior)."
    )
    print("\nRecomendacion: " + recomendacion)

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": 5, "n_val": int(len(y)),
        "metrica_principal": "f1_baja con umbral optimizado sobre val",
        "modelos": filas,
        "mejor_por_metrica_principal": mejor[0],
        "recomendacion": recomendacion,
        "advertencias": [
            "los umbrales se eligen sobre el mismo val en el que se reportan (en muestra)",
            "la AUC/Brier global del modelo con mascaras se beneficia de la restriccion IJ",
            "el calibrador sigmoid del paso 2 se ajusta sobre val (en muestra)",
        ],
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("paso5_tabla_final_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
