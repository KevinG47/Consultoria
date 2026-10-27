#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expJ_tabicl.py
==============

Experimento 2: TabICLv2 (modelo de fundación tabular, open weights, BSD-3)
sobre las features de la Ronda 2, en los mismos 3 folds temporales.

- Zero-shot: se usan los hiperparámetros por defecto (sin tuning).
- Contexto: TabICL es in-context learning y su costo es O(n^2 + n m^2); en CPU
  con 4 núcleos no cabe el train completo. Se usa una submuestra estratificada
  del train por fold (--context), documentada como limitación.
- El umbral se elige en validación con el mismo protocolo que el XGBoost.
- Test (cohorte 21) NO se toca.

Uso:
    python expJ_tabicl.py --context 2000 --estimators 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# La sandbox solo permite escribir dentro del workspace: cache de HF local
_CACHE = Path(__file__).resolve().parent.parent / ".cache" / "huggingface"
_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(_CACHE))
os.environ.setdefault("HF_HUB_CACHE", str(_CACHE / "hub"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(_CACHE / "hub"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import opt_comun as oc  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"
BASE_F1 = 0.2985


def submuestra_estratificada(y, n, rng):
    """Submuestra de tamaño n conservando la proporción de clases."""
    if n >= len(y):
        return np.arange(len(y))
    idx = []
    for c in np.unique(y):
        pos = np.flatnonzero(y == c)
        k = max(1, int(round(n * len(pos) / len(y))))
        k = min(k, len(pos))
        idx.append(rng.choice(pos, size=k, replace=False))
    return np.sort(np.concatenate(idx))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", type=int, default=2000)
    ap.add_argument("--estimators", type=int, default=2)
    ap.add_argument("--features", type=int, default=172, help="top-k features por ganancia")
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--fold", default="todas", choices=["F1", "F2", "F3", "todas"])
    args = ap.parse_args()

    from tabicl import TabICLClassifier
    import joblib

    df, feats = oc.cargar()
    cont = joblib.load(SCRIPT_DIR / "modelos" / "xgb_ventana_contiguo.joblib")
    imp = np.asarray(cont["modelo"].feature_importances_)
    gain = dict(zip(cont["features"], imp))
    if args.features < len(feats):
        orden = sorted(feats, key=lambda f: -gain.get(f, 0.0))[: args.features]
        feats = orden
        print(f"features: top-{args.features} por ganancia del XGBoost base")

    X = oc.matriz(df, feats)
    y = df["y"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    rng = np.random.default_rng(42)

    print(f"TabICLv2 | context={args.context} | estimators={args.estimators} | "
          f"features={len(feats)} | device=cpu")

    filas = []
    f1s, macros, briers, ts, tiempos = [], [], [], [], []
    folds = [f for f in oc.FOLDS if args.fold == "todas" or f[0] == args.fold]
    for fold in folds:
        nombre, tr_p, va_p, ev_p = fold
        m_tr = np.isin(per, tr_p)
        m_va = per == va_p[0]
        m_ev = per == ev_p[0]
        idx_tr = np.flatnonzero(m_tr)
        sub = submuestra_estratificada(y[idx_tr], args.context, rng)
        idx_sub = idx_tr[sub]
        t0 = time.time()
        clf = TabICLClassifier(n_estimators=args.estimators, device="cpu",
                               n_jobs=4, batch_size=args.batch_size,
                               random_state=42, verbose=False)
        clf.fit(X[idx_sub], y[idx_sub])
        p_va = clf.predict_proba(X[m_va])
        p_ev = clf.predict_proba(X[m_ev])
        t, f1_va = oc.mejor_t_baja(p_va[:, 0], y[m_va])
        m = oc.metricas_eval(p_ev, y[m_ev], t)
        dt = time.time() - t0
        filas.append({"fold": nombre, "n_context": int(len(idx_sub)),
                      "n_val": int(m_va.sum()), "n_eval": int(m_ev.sum()),
                      "umbral": t, "f1_val": round(float(f1_va), 4),
                      "f1_baja_eval": round(m["f1_baja"], 4),
                      "f1_macro": round(m["f1_macro"], 4),
                      "brier": round(m["brier"], 4),
                      "segundos": round(dt, 1)})
        f1s.append(m["f1_baja"]); macros.append(m["f1_macro"]); briers.append(m["brier"]); ts.append(t)
        print(f"  {nombre}: F1 baja={m['f1_baja']:.4f} | macro={m['f1_macro']:.4f} | "
              f"brier={m['brier']:.4f} | t={t:.2f} | {dt:.0f}s")

    media = float(np.mean(f1s))
    print(f"\nTabICLv2: F1 baja OOS medio {media:.4f} | desv {np.std(f1s):.4f} | "
          f"macro {np.mean(macros):.4f} | brier {np.mean(briers):.4f}")
    print(f"XGBoost Ronda 2: {BASE_F1:.4f} | delta {100*(media-BASE_F1):+.2f} pp")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "J_tabicl_v2",
        "modelo": "TabICLv2 (Qu, Holzmuller, Varoquaux & Le Morvan, 2026, ICML; arXiv:2602.11139)",
        "licencia": "BSD-3-Clause",
        "parametros": {"context": args.context, "estimators": args.estimators,
                       "features": len(feats), "batch_size": args.batch_size,
                       "device": "cpu"},
        "nota": "contexto = submuestra estratificada del train por fold; "
                "TabICL es O(n^2) y en CPU no cabe el train completo",
        "folds": filas,
        "f1_baja_folds": [round(float(v), 4) for v in f1s],
        "media": round(media, 4),
        "desv": round(float(np.std(f1s, ddof=0)), 4),
        "f1_macro_medio": round(float(np.mean(macros)), 4),
        "brier_medio": round(float(np.mean(briers)), 4),
        "umbrales": [round(float(v), 2) for v in ts],
        "base_f1_baja_oos": BASE_F1,
        "delta_pp": round(100 * (media - BASE_F1), 2),
        "toco_test": False,
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("expJ_tabicl_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
