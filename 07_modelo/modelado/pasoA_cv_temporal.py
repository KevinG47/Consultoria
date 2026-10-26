#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pasoA_cv_temporal.py
====================

PASO A: validacion cruzada temporal del umbral para el XGBoost con mascaras.

Folds (corte por cohorte de destino = ID_CONVOCATORIA_siguiente):
    Fold 1: train 17,18 (13->14 y 14->15) | val 19 (15->17) | eval 20 (17->19)
    Fold 2: train 17,18,19                | val 20 (17->19) | eval 21 (19->21)
    Fold 3: train 17,18,19,20             | val 21 (19->21) | eval 21 (en muestra)

El umbral se elige SOLO en el val de cada fold; la metrica de interes es la del
conjunto eval (out-of-sample en los folds 1 y 2).

Uso: <python> 07_modelo/modelado/pasoA_cv_temporal.py
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
import modelo_mascaras as mm  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"
FOLDS = [
    ("Fold 1", [17, 18], [19], [20], "13->14 + 14->15 | val 15->17 | eval 17->19"),
    ("Fold 2", [17, 18, 19], [20], [21], "13->14 + 14->15 + 15->17 | val 17->19 | eval 19->21"),
    ("Fold 3", [17, 18, 19, 20], [21], [21], "hasta 17->19 | val 19->21 | eval 19->21 (en muestra)"),
]


def pred_umbral(p, t):
    return np.where(p[:, 0] >= t, 0, np.where(p[:, 1] >= p[:, 2], 1, 2))


def main() -> int:
    import joblib
    import pandas as pd

    contenedor = joblib.load(mu.MODELOS_DIR / "xgb_ventana_contiguo.joblib")
    feats = [f for f in contenedor["features"] if f != "ano"]
    df = pd.read_parquet(SCRIPT_DIR.parent / "datos" / "derivados" /
                         "modelo_dataset_ventana_contiguo.parquet")
    df = mm.preparar(df)
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    print(f"features: {len(feats)} | cohortes: "
          + ", ".join(f"{k}={int(v)}" for k, v in pd.Series(per).value_counts().sort_index().items()))

    filas, resultados = [], {}
    for nombre, tr_p, va_p, ev_p, desc in FOLDS:
        tr = df[np.isin(per, tr_p)]
        va = df[np.isin(per, va_p)]
        ev = df[np.isin(per, ev_p)]
        modelos, prev = mm.entrenar(tr, feats)
        p_va = mm.predecir(modelos, prev, va, feats)
        p_ev = mm.predecir(modelos, prev, ev, feats)
        m_va, _ = mu.umbral_baja(p_va, va["y"].to_numpy())
        t = m_va["umbral"]
        y_ev = ev["y"].to_numpy()
        pred = pred_umbral(p_ev, t)
        m_ev = mu.metricas_completas(p_ev, y_ev, pred)
        fila = {
            "fold": nombre, "descripcion": desc,
            "n_train": int(len(tr)), "n_val": int(len(va)), "n_eval": int(len(ev)),
            "umbral": float(t),
            "f1_baja_oos": float(m_ev["f1_por_clase"]["baja"]),
            "f1_macro_oos": float(m_ev["f1_macro"]),
            "brier_oos": float(m_ev["brier"]),
            "precision_baja": float(m_ev["precision_baja"]),
            "recall_baja": float(m_ev["recall_baja"]),
            "f1_baja_en_val": float(m_va["f1_baja_umbral"]),
            "confusion": m_ev["confusion"],
        }
        resultados[nombre] = fila
        filas.append(fila)
        print(f"\n=== {nombre} === {desc}")
        print(f"   n_train={len(tr):,} | n_val={len(va):,} | n_eval={len(ev):,}".replace(",", " "))
        print(f"   umbral elegido en val: t={t:.2f} (F1 baja en val {m_va['f1_baja_umbral']:.4f})")
        print(f"   EVAL: F1 baja={m_ev['f1_por_clase']['baja']:.4f} | "
              f"F1 macro={m_ev['f1_macro']:.4f} | Brier={m_ev['brier']:.4f} | "
              f"prec={m_ev['precision_baja']:.4f} | rec={m_ev['recall_baja']:.4f}")
        print(f"   confusion: {m_ev['confusion']}")

    # Fold 3 alternativo: umbral del fold 2 aplicado a la cohorte 21 (OOS de verdad)
    t2 = resultados["Fold 2"]["umbral"]
    ev3 = df[per == 21]
    tr3 = df[np.isin(per, [17, 18, 19, 20])]
    mod3, prev3 = mm.entrenar(tr3, feats)
    p3 = mm.predecir(mod3, prev3, ev3, feats)
    m_alt = mu.metricas_completas(p3, ev3["y"].to_numpy(), pred_umbral(p3, t2))
    print(f"\n=== Fold 3 alternativo (umbral de Fold 2 = {t2:.2f} aplicado a 19->21) ===")
    print(f"   EVAL: F1 baja={m_alt['f1_por_clase']['baja']:.4f} | F1 macro={m_alt['f1_macro']:.4f} | "
          f"Brier={m_alt['brier']:.4f} | prec={m_alt['precision_baja']:.4f} | "
          f"rec={m_alt['recall_baja']:.4f}")

    f1_oos = [r["f1_baja_oos"] for r in filas[:2]]
    media2, desv2 = float(np.mean(f1_oos)), float(np.std(f1_oos, ddof=0))
    f1_all = f1_oos + [m_alt["f1_por_clase"]["baja"]]
    media3, desv3 = float(np.mean(f1_all)), float(np.std(f1_all, ddof=0))
    print("\n=== RESUMEN F1 'baja' OUT-OF-SAMPLE ===")
    print(f"   folds 1 y 2 (OOS estrictos): media={media2:.4f} | desv={desv2:.4f} "
          f"| valores={[round(v, 4) for v in f1_oos]}")
    print(f"   folds 1, 2 y 3-alt (OOS):   media={media3:.4f} | desv={desv3:.4f} "
          f"| valores={[round(v, 4) for v in f1_all]}")
    criterio = media3 >= 0.25 and desv3 <= 0.08
    criterio2 = media2 >= 0.25 and desv2 <= 0.08
    print(f"   criterio (media>=0.25 y desv<=0.08): 3 folds -> "
          f"{'CUMPLE' if criterio else 'NO CUMPLE'} | 2 folds -> "
          f"{'CUMPLE' if criterio2 else 'NO CUMPLE'}")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paso": "A", "modelo": "XGBoost mascaras sin 'ano'", "n_features": len(feats),
        "folds": resultados,
        "fold3_alternativo": {
            "umbral_usado": float(t2),
            "f1_baja": float(m_alt["f1_por_clase"]["baja"]),
            "f1_macro": float(m_alt["f1_macro"]), "brier": float(m_alt["brier"]),
            "precision_baja": float(m_alt["precision_baja"]),
            "recall_baja": float(m_alt["recall_baja"]),
        },
        "resumen": {
            "f1_baja_media_2_oos": media2, "f1_baja_desv_2_oos": desv2,
            "f1_baja_media_3_oos": media3, "f1_baja_desv_3_oos": desv3,
            "criterio_media_025_desv_008_3folds": bool(criterio),
            "criterio_media_025_desv_008_2folds": bool(criterio2),
        },
        "umbral_medio_folds": float(np.mean([r["umbral"] for r in filas])),
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("pasoA_cv_temporal_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
