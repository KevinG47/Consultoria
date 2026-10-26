#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expD_umbral_mediana.py
======================

EXPERIMENTO D: umbral estable = MEDIANA de los umbrales elegidos en los folds.

Con el mejor modelo de A+B+C:
  - se elige el umbral optimo de cada fold en su val,
  - se toma la MEDIANA,
  - se aplica ese unico umbral a los 3 eval y se reporta F1 'baja' OOS.

Deja en resultados/spec_final.json la configuracion y el umbral para la
evaluacion final en test.

Uso: <python> 07_modelo/modelado/expD_umbral_mediana.py
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


def main() -> int:
    exp_a = json.loads(sorted(RESULTADOS.glob("expA_grid_*.json"))[-1]
                       .read_text(encoding="utf-8"))
    exp_b = json.loads(sorted(RESULTADOS.glob("expB_features_*.json"))[-1]
                       .read_text(encoding="utf-8"))
    exp_c = json.loads(sorted(RESULTADOS.glob("expC_demografia_*.json"))[-1]
                       .read_text(encoding="utf-8"))
    mejorA = exp_a["mejor"]
    k = int(exp_b["mejor_k"])
    usar_demo = bool(exp_c["se_queda"])
    params = dict(oc.BASE, n_estimators=mejorA["n_estimators"],
                  min_child_weight=mejorA["min_child_weight"],
                  gamma=mejorA["gamma"], subsample=mejorA["subsample"],
                  max_depth=7, learning_rate=0.05)
    print(f"modelo elegido: n_est={params['n_estimators']} mcw={params['min_child_weight']} "
          f"gamma={params['gamma']} sub={params['subsample']} | top {k} features | "
          f"demografia={'SI' if usar_demo else 'NO'}")

    df, feats = oc.cargar()
    X = oc.matriz(df, feats)
    demo = oc.demo_features(df)
    Xd = demo.to_numpy(dtype="float32")
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    ts, f1s_propio, p_evs, y_evs = [], [], [], []
    for fold in oc.FOLDS:
        _, tr_p, va_p, ev_p = fold
        m_tr = np.isin(per, tr_p)
        prev = np.bincount(y[m_tr], minlength=3) / m_tr.sum()
        mod_full = oc.entrenar_cat(X, y, cat, m_tr, params)
        gain = oc.ganancias(mod_full, len(feats))
        idx = np.argsort(-gain)[:k] if k < len(feats) else np.arange(len(feats))
        Xb = X[:, idx]
        Xf = np.column_stack([Xb, Xd]) if usar_demo else Xb
        mod = oc.entrenar_cat(Xf, y, cat, m_tr, params)
        m_va = per == va_p[0]
        m_ev = per == ev_p[0]
        p_va = oc.predecir_cat(mod, Xf, cat, m_va, prev)
        p_ev = oc.predecir_cat(mod, Xf, cat, m_ev, prev)
        t_propio, _ = oc.mejor_t_baja(p_va[:, 0], y[m_va])
        ts.append(t_propio)
        f1s_propio.append(oc.metricas_eval(p_ev, y[m_ev], t_propio)["f1_baja"])
        p_evs.append(p_ev)
        y_evs.append(y[m_ev])

    t_med = float(np.median(ts))
    print(f"umbrales por fold: {ts} -> MEDIANA t={t_med:.2f}")

    f1s_med, macros, briers = [], [], []
    for p_ev, y_ev in zip(p_evs, y_evs):
        m = oc.metricas_eval(p_ev, y_ev, t_med)
        f1s_med.append(m["f1_baja"])
        macros.append(m["f1_macro"])
        briers.append(m["brier"])

    print(f"\n=== UMBRAL MEDIANA t={t_med:.2f} aplicado a los 3 folds ===")
    for fold, f1, fm in zip(oc.FOLDS, f1s_med, macros):
        print(f"   {fold[0]} eval {fold[3]}: F1 baja={f1:.4f} | F1 macro={fm:.4f}")
    media = float(np.mean(f1s_med))
    desv = float(np.std(f1s_med, ddof=0))
    print(f"   media={media:.4f} | desv={desv:.4f}")
    print(f"   (umbral propio de cada fold: media={np.mean(f1s_propio):.4f}, "
          f"desv={np.std(f1s_propio, ddof=0):.4f})")

    spec = {
        "config": {k2: params[k2] for k2 in ("n_estimators", "min_child_weight",
                                             "gamma", "subsample", "max_depth",
                                             "learning_rate")},
        "top_k": k, "usar_demografia": usar_demo,
        "umbral_mediana": t_med,
        "umbrales_folds": ts,
        "f1_baja_oos_media": round(media, 4),
        "f1_baja_oos_desv": round(desv, 4),
        "f1_baja_oos_folds": [round(v, 4) for v in f1s_med],
        "f1_baja_con_umbral_propio_media": round(float(np.mean(f1s_propio)), 4),
    }
    (RESULTADOS / "spec_final.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    resumen = {"fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "experimento": "D", **spec}
    salida = RESULTADOS / ("expD_umbral_mediana_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
