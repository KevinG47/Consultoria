#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
paso1_umbral_bayesiano.py
=========================

PASO 1: umbral optimizado sobre el bayesiano minimo (trace ta=0.95).

- Probabilidades en val (n=9 994).
- Barrido de umbral t sobre p(baja) en 0,01..0,99 para maximizar F1 de "baja".
- Barrido de pesos por clase (equivalente a umbrales) para maximizar F1 macro.
- Comparacion con el argmax puro.

Metrica principal: F1 de "baja" con umbral optimizado.

Uso: <python> 07_modelo/modelado/paso1_umbral_bayesiano.py
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


def main() -> int:
    p, y, df, datos = mu.probabilidades_bayesiano()
    print(f"val: n={len(y)} | p(baja) media={p[:, 0].mean():.4f} | "
          f"prevalencia baja={np.mean(y == 0):.4f}")

    base = mu.metricas_completas(p, y)
    print("\n--- ARGMAX (sin umbral) ---")
    print(f"   F1 macro={base['f1_macro']:.4f} | F1 baja={base['f1_por_clase']['baja']:.4f} | "
          f"F1 mantiene={base['f1_por_clase']['se_mantiene']:.4f} | "
          f"F1 sube={base['f1_por_clase']['sube']:.4f}")
    print(f"   precision baja={base['precision_baja']:.4f} | recall baja={base['recall_baja']:.4f}")
    print(f"   pred baja={100*base['pred_baja_pct']:.2f} % de las filas")

    # --- umbral para F1 de "baja" ---
    m_baja, pred_baja = mu.umbral_baja(p, y)
    print("\n--- UMBRAL QUE MAXIMIZA F1 DE 'BAJA' ---")
    print(f"   umbral t={m_baja['umbral']:.2f}  (predice 'baja' si p(baja) >= t)")
    print(f"   F1 baja={m_baja['f1_baja_umbral']:.4f} | precision={m_baja['precision_baja_umbral']:.4f} "
          f"| recall={m_baja['recall_baja_umbral']:.4f}")
    print(f"   con ese umbral: F1 macro={m_baja['f1_macro']:.4f} | "
          f"F1 mantiene={m_baja['f1_por_clase']['se_mantiene']:.4f} | "
          f"F1 sube={m_baja['f1_por_clase']['sube']:.4f} | "
          f"pred baja={100*m_baja['pred_baja_pct']:.2f} %")
    print(f"   matriz de confusion (filas=real, cols=pred: baja, mantiene, sube):\n"
          f"      {m_baja['confusion']}")

    # --- pesos por clase para F1 macro ---
    m_macro, _ = mu.pesos_macro(p, y)
    print("\n--- PESOS POR CLASE QUE MAXIMIZAN F1 MACRO ---")
    print(f"   w_baja={m_macro['w_baja']:.3f} | w_sube={m_macro['w_sube']:.3f} "
          f"(equivale a t_baja={m_macro['t_baja_equiv']:.3f}, t_sube={m_macro['t_sube_equiv']:.3f})")
    print(f"   F1 macro={m_macro['f1_macro']:.4f} | F1 baja={m_macro['f1_por_clase']['baja']:.4f} | "
          f"F1 mantiene={m_macro['f1_por_clase']['se_mantiene']:.4f} | "
          f"F1 sube={m_macro['f1_por_clase']['sube']:.4f}")
    print(f"   precision baja={m_macro['precision_baja']:.4f} | recall baja={m_macro['recall_baja']:.4f}"
          f" | pred baja={100*m_macro['pred_baja_pct']:.2f} %")
    print(f"   matriz de confusion:\n      {m_macro['confusion']}")

    # --- curva F1 baja vs umbral (para ver la meseta) ---
    curva = []
    for t in np.round(np.arange(0.05, 0.61, 0.05), 2):
        mm, _ = mu.umbral_baja(p, y, grid=[t])
        curva.append({"t": float(t), "f1_baja": mm["f1_baja_umbral"],
                      "precision": mm["precision_baja_umbral"],
                      "recall": mm["recall_baja_umbral"],
                      "f1_macro": mm["f1_macro"]})
    print("\n--- curva F1 baja vs umbral ---")
    print("   t     F1_baja  prec   rec    F1_macro")
    for c in curva:
        print(f"   {c['t']:.2f}   {c['f1_baja']:.4f}  {c['precision']:.4f} "
              f"{c['recall']:.4f}  {c['f1_macro']:.4f}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": 1, "modelo": "bayesiano_minimo (trace ta=0.95)",
        "n_val": int(len(y)),
        "argmax": base,
        "umbral_f1_baja": m_baja,
        "pesos_f1_macro": m_macro,
        "curva_f1_baja": curva,
        "metrica_principal": "f1_baja con umbral optimizado",
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("paso1_umbral_bayesiano_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
