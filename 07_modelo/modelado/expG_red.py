#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expG_red.py
===========

Última palanca: features de RED (co-membresía de grupo) sobre el XGBoost con
máscaras, config Ronda 2 (100 árboles, gamma 0.1, sub 0.8).

3 folds: F1 17->18->19, F2 17,18->19->20, F3 18->19->20.
Ablación: cada feature por separado y todas.
Test SOLO si la mejor supera 0.2985 + 2 pp = 0.3185.
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
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
BASE_F1 = 0.2985
DELTA = 0.02
ANTERIOR = {"f1_baja": 0.4234, "recall": 0.7878, "precision": 0.2895,
            "f1_macro": 0.5109, "brier": 0.4692}
PARAMS = dict(oc.BASE, n_estimators=100, min_child_weight=1, gamma=0.1,
              subsample=0.8, max_depth=7, learning_rate=0.05)

NUEVAS = {
    "a_companeros": ["n_companeros_distintos"],
    "b_movilidad_pares": ["companeros_que_subieron", "companeros_que_bajaron"],
    "d_centralidad": ["centralidad_grado"],
    "e_grupos": ["n_grupos_distintos_red"],
    "f_categoria_par": ["companero_categoria_modal"],
    "todas": ["n_companeros_distintos", "companeros_que_subieron",
              "companeros_que_bajaron", "centralidad_grado",
              "n_grupos_distintos_red", "companero_categoria_modal"],
}


def correr(X, y, cat, per, variante):
    f1s, macros, briers, ts = [], [], [], []
    for fold in oc.FOLDS:
        t, _, p_va, p_ev, y_ev = oc.correr_fold(X, y, cat, per, fold, PARAMS)
        m = oc.metricas_eval(p_ev, y_ev, t)
        f1s.append(m["f1_baja"])
        macros.append(m["f1_macro"])
        briers.append(m["brier"])
        ts.append(t)
    return {"variante": variante,
            "f1_baja_folds": [round(v, 4) for v in f1s],
            "media": round(float(np.mean(f1s)), 4),
            "desv": round(float(np.std(f1s, ddof=0)), 4),
            "f1_macro_medio": round(float(np.mean(macros)), 4),
            "brier_medio": round(float(np.mean(briers)), 4),
            "umbrales": ts}


def main() -> int:
    import pandas as pd

    df, feats = oc.cargar()
    red = pd.read_parquet(DERIVADOS / "red_features.parquet")
    red["ID_PERSONA_PR"] = red["ID_PERSONA_PR"].astype(str).str.zfill(10)
    red["ID_CONVOCATORIA"] = red["ID_CONVOCATORIA"].astype(int)
    df["ID_PERSONA_PR"] = df["ID_PERSONA_PR"].astype(str).str.zfill(10)
    df["ID_CONVOCATORIA"] = df["ID_CONVOCATORIA"].astype(int)
    df = df.merge(red, on=["ID_PERSONA_PR", "ID_CONVOCATORIA"], how="left",
                  validate="one_to_one")
    nuevas = [c for c in red.columns
              if c not in ("ID_PERSONA_PR", "ID_CONVOCATORIA")]
    cub = df[nuevas[0]].notna().mean()
    df[nuevas] = df[nuevas].fillna(0.0)
    print(f"base: {len(feats)} | red: {len(nuevas)} -> total {len(feats)+len(nuevas)} "
          f"| cobertura red {cub:.4f}")

    Xb = oc.matriz(df, feats)
    Xn = df[nuevas].to_numpy(dtype="float32")
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    resultados = {"sin_red": correr(Xb, y, cat, per, "sin_red (172)")}
    print(f"\n{'variante':20s} {'folds':28s} {'media':>6} {'desv':>6} {'F1macro':>8} {'Brier':>7}  t")
    f = resultados["sin_red"]
    print(f"{f['variante']:20s} {str(f['f1_baja_folds']):28s} {f['media']:>6.4f} "
          f"{f['desv']:>6.4f} {f['f1_macro_medio']:>8.4f} {f['brier_medio']:>7.4f}  {f['umbrales']}")
    for nombre, cols in NUEVAS.items():
        idx = [nuevas.index(c) for c in cols]
        X = np.column_stack([Xb, Xn[:, idx]])
        r = correr(X, y, cat, per, f"{nombre} (+{len(cols)})")
        resultados[nombre] = r
        print(f"{r['variante']:20s} {str(r['f1_baja_folds']):28s} {r['media']:>6.4f} "
              f"{r['desv']:>6.4f} {r['f1_macro_medio']:>8.4f} {r['brier_medio']:>7.4f}  {r['umbrales']}")

    orden = sorted([v for k, v in resultados.items() if k != "sin_red"],
                   key=lambda r: -r["media"])
    mejor = orden[0]
    print(f"\nMEJOR con red: {mejor['variante']} -> media {mejor['media']:.4f} "
          f"(base {BASE_F1:.4f}, delta {100*(mejor['media']-BASE_F1):+.2f} pp)")
    print(f"criterio para tocar test: media >= {BASE_F1 + DELTA:.4f}")

    toca = bool(mejor["media"] >= BASE_F1 + DELTA)
    salida_test = None
    if toca:
        print("\n*** CUMPLE: evaluación en test UNA SOLA VEZ ***")
        clave = mejor["variante"].split(" (+")[0]
        cols = NUEVAS[clave]
        idx = [nuevas.index(c) for c in cols]
        X = np.column_stack([Xb, Xn[:, idx]])
        m_tr = np.isin(per, [17, 18, 19, 20])
        m_te = per == 21
        prev = np.bincount(y[m_tr], minlength=3) / m_tr.sum()
        mod = oc.entrenar_cat(X, y, cat, m_tr, PARAMS)
        p_te = oc.predecir_cat(mod, X, cat, m_te, prev)
        t_med = float(np.median(mejor["umbrales"]))
        m = oc.metricas_eval(p_te, y[m_te], t_med)
        print(f"   TEST (t={t_med:.2f}): F1 baja={m['f1_baja']:.4f} | recall={m['recall_baja']:.4f} "
              f"| precision={m['precision_baja']:.4f} | F1 macro={m['f1_macro']:.4f} "
              f"| Brier={m['brier']:.4f}")
        print(f"   vs Ronda 2: F1 baja {m['f1_baja']-ANTERIOR['f1_baja']:+.4f} | "
              f"recall {m['recall_baja']-ANTERIOR['recall']:+.4f} | "
              f"macro {m['f1_macro']-ANTERIOR['f1_macro']:+.4f} | "
              f"Brier {m['brier']-ANTERIOR['brier']:+.4f}")
        salida_test = {"umbral": t_med, "metricas": m, "variante": mejor["variante"],
                       "features": cols, "anterior": ANTERIOR,
                       "mejora_f1_baja": m["f1_baja"] - ANTERIOR["f1_baja"]}
    else:
        print("NO cumple el +2 pp: test NO se toca. La red no aporta en este censo; "
              "se cierra con Ronda 2.")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "G", "n_base": len(feats), "n_red": len(nuevas),
        "n_total": len(feats) + len(nuevas), "cobertura_red": float(cub),
        "nota": "red construida sobre co-membresia de grupo (cod_grupo_gr): el CSV "
                "no tiene listas de coautores (1,02 autores/producto)",
        "resultados": resultados, "mejor": mejor,
        "base_f1_baja_oos": BASE_F1,
        "delta_pp": round(100 * (mejor["media"] - BASE_F1), 2),
        "criterio_test": round(BASE_F1 + DELTA, 4), "toco_test": toca,
        "test": salida_test,
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("expG_red_"
                           + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGuardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
