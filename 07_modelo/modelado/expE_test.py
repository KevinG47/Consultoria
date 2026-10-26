#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expE_test.py
============

EVALUACION FINAL EN TEST (una sola vez). Modelo y umbral fijados por los
experimentos A-D (resultados/spec_final.json).

Entrena con las cohortes 17, 18, 19 y 20 (todo lo anterior al test), aplica
el umbral mediana y evalua en la cohorte 21 (13 355 filas).

Uso: <python> 07_modelo/modelado/expE_test.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import opt_comun as oc  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"
ANTERIOR = {"f1_baja": 0.4223, "recall": 0.7438, "precision": 0.2949,
            "f1_macro": 0.5181, "brier": 0.4592}


def main() -> int:
    spec = json.loads((RESULTADOS / "spec_final.json").read_text(encoding="utf-8"))
    cfg = spec["config"]
    params = dict(oc.BASE, **cfg)
    k = int(spec["top_k"])
    usar_demo = bool(spec["usar_demografia"])
    t = float(spec["umbral_mediana"])
    print(f"spec: n_est={cfg['n_estimators']} mcw={cfg['min_child_weight']} "
          f"gamma={cfg['gamma']} sub={cfg['subsample']} | top {k} | "
          f"demo={'SI' if usar_demo else 'NO'} | umbral={t:.2f}")

    df, feats = oc.cargar()
    X = oc.matriz(df, feats)
    demo = oc.demo_features(df)
    Xd = demo.to_numpy(dtype="float32")
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    m_tr = np.isin(per, [17, 18, 19, 20])
    m_te = per == 21
    prev = np.bincount(y[m_tr], minlength=3) / m_tr.sum()
    mod_full = oc.entrenar_cat(X, y, cat, m_tr, params)
    gain = oc.ganancias(mod_full, len(feats))
    idx = np.argsort(-gain)[:k] if k < len(feats) else np.arange(len(feats))
    Xb = X[:, idx]
    Xf = np.column_stack([Xb, Xd]) if usar_demo else Xb
    mod = oc.entrenar_cat(Xf, y, cat, m_tr, params)
    p_te = oc.predecir_cat(mod, Xf, cat, m_te, prev)
    m = oc.metricas_eval(p_te, y[m_te], t)

    print(f"\n=== TEST (una sola vez) | train={int(m_tr.sum())} test={int(m_te.sum())} "
          f"| t={t:.2f} ===")
    print(f"   F1 baja={m['f1_baja']:.4f} | recall={m['recall_baja']:.4f} | "
          f"precision={m['precision_baja']:.4f}")
    print(f"   F1 macro={m['f1_macro']:.4f} | Brier={m['brier']:.4f}")
    print(f"\n   comparacion con el modelo anterior:")
    for kk, vv in (("f1_baja", m["f1_baja"]), ("recall", m["recall_baja"]),
                   ("precision", m["precision_baja"]), ("f1_macro", m["f1_macro"]),
                   ("brier", m["brier"])):
        print(f"      {kk:10s} {vv:.4f} vs {ANTERIOR[kk]:.4f} "
              f"({vv - ANTERIOR[kk]:+.4f})")
    mejora = m["f1_baja"] > ANTERIOR["f1_baja"]
    print(f"\n   VEREDICTO: F1 baja {'MEJORA REAL' if mejora else 'NO MEJORA'} "
          f"({m['f1_baja']:.4f} vs 0.4223)")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "E", "spec": spec,
        "n_train": int(m_tr.sum()), "n_test": int(m_te.sum()),
        "metricas": m, "anterior": ANTERIOR,
        "mejora_real": bool(mejora),
        "nota": "test evaluado una sola vez en esta ronda",
    }
    salida = RESULTADOS / ("expE_test_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
