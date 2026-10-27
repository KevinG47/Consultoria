#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expN_limpio.py
==============

Modelo "limpio": aplica la limpieza que salio del EDA de diagnostico y evalua
solo en folds (test intacto).

Limpieza:
  - 49 features eliminadas por el VIF iterativo (34 duplicados exactos + 15 VIF>10)
  - 86 features con > 99 % de ceros
  - n_productos winsorizada en el p99 de train (105)

Variantes evaluadas (config Ronda 2, 3 folds):
  base_172   : referencia (debe reproducir 0,2985)
  vif_123    : solo se quitan las 49 redundantes
  limpio_56  : se quitan redundantes y muertas (dataset limpio que se guarda)

Uso:
    python expN_limpio.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import opt_comun as oc  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
BASE_F1 = 0.2985
DELTA = 0.02
PARAMS = dict(oc.BASE, n_estimators=100, min_child_weight=1, gamma=0.1,
              subsample=0.8, max_depth=7, learning_rate=0.05)


def auditoria():
    fs = sorted(RESULTADOS.glob("auditoria_eda_*.json"))
    if not fs:
        raise SystemExit("no hay auditoria_eda_*.json: corre auditoria_eda.py primero")
    j = json.load(open(fs[-1], encoding="utf-8"))
    elim = j["d_vif"]["eliminadas"]
    redundantes = [e["feature"] for e in elim]
    duplicados = [e["feature"] for e in elim if str(e.get("motivo", "")).startswith("duplicado")]
    por_vif = [e["feature"] for e in elim if e.get("motivo") == "VIF"]
    muertas = list(j["e_muertas"]["propuesta_poda"])
    return fs[-1].name, redundantes, duplicados, por_vif, muertas


def correr(X, y, cat, per, variante):
    f1s, macros, briers, ts = [], [], [], []
    for fold in oc.FOLDS:
        t, _, p_va, p_ev, y_ev = oc.correr_fold(X, y, cat, per, fold, PARAMS)
        m = oc.metricas_eval(p_ev, y_ev, t)
        f1s.append(m["f1_baja"]); macros.append(m["f1_macro"]); briers.append(m["brier"]); ts.append(t)
    return {"variante": variante,
            "n_features": int(X.shape[1]),
            "f1_baja_folds": [round(v, 4) for v in f1s],
            "media": round(float(np.mean(f1s)), 4),
            "desv": round(float(np.std(f1s, ddof=0)), 4),
            "f1_macro_medio": round(float(np.mean(macros)), 4),
            "brier_medio": round(float(np.mean(briers)), 4),
            "umbrales": ts}


def main() -> int:
    nombre_aud, redundantes, duplicados, por_vif, muertas = auditoria()
    print(f"auditoria usada: {nombre_aud}")
    print(f"redundantes: {len(redundantes)} (duplicados exactos {len(duplicados)} + VIF>10 {len(por_vif)})")
    print(f"muertas >99 % ceros: {len(muertas)} | interseccion redundantes-muertas: {len(set(redundantes) & set(muertas))}")

    df = pd.read_parquet(DERIVADOS / "modelo_dataset_ventana_contiguo.parquet")
    cont = __import__("joblib").load(SCRIPT_DIR / "modelos" / "xgb_ventana_contiguo.joblib")
    feats = [f for f in cont["features"] if f != "ano"]
    df["cat"] = df["ORDEN_CLAS_PR_actual"].map(oc.CAT_MAP).astype(int)
    df["y"] = df["target_class"].map(lambda c: oc.CLASES.index(c)).astype(int)

    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    # winsorizacion de n_productos en el p99 de train
    p99 = float(df.loc[df["split"] == "train", "n_productos"].quantile(0.99))
    n_afectadas = int((df["n_productos"] > p99).sum())
    por_split = {s: int((df.loc[df["split"] == s, "n_productos"] > p99).sum())
                 for s in ("train", "val", "test")}
    print(f"winsorizacion n_productos: p99(train)={p99:.0f} | filas afectadas={n_afectadas} "
          f"({100*n_afectadas/len(df):.2f} %) | {por_split}")
    df["n_productos"] = df["n_productos"].clip(upper=p99)

    f_vif = [f for f in feats if f not in set(redundantes)]
    f_limpio = [f for f in f_vif if f not in set(muertas)]
    print(f"features: base {len(feats)} | tras VIF {len(f_vif)} | limpio {len(f_limpio)}")

    # dataset limpio (se guarda): solo metadatos utiles + features limpias.
    # El parquet original trae 101 columnas n_* que el modelo nunca uso; se omiten.
    META = ["ID_PERSONA_PR", "ID_CONVOCATORIA", "ano", "ID_CONVOCATORIA_siguiente",
            "ORDEN_CLAS_PR_actual", "target_class", "split", "cat", "y"]
    limpio = df[META + f_limpio].copy()
    ruta = DERIVADOS / "modelo_dataset_ventana_contiguo_limpio.parquet"
    limpio.to_parquet(ruta, index=False, engine="pyarrow")
    print(f"guardado: {ruta.name} | {limpio.shape[0]} filas x {limpio.shape[1]} columnas")

    resultados = {}
    print(f"\n{'variante':12s} {'n':>4s} {'folds':26s} {'media':>6} {'desv':>6} {'F1macro':>8} {'Brier':>7}  t")
    for nombre, cols in (("base_172", feats), ("vif_123", f_vif), ("limpio_56", f_limpio)):
        X = df[cols].to_numpy(dtype="float32")
        r = correr(X, y, cat, per, nombre)
        resultados[nombre] = r
        print(f"{nombre:12s} {r['n_features']:>4d} {str(r['f1_baja_folds']):26s} {r['media']:>6.4f} "
              f"{r['desv']:>6.4f} {r['f1_macro_medio']:>8.4f} {r['brier_medio']:>7.4f}  {r['umbrales']}")

    mejor = max([r for k, r in resultados.items() if k != "base_172"], key=lambda r: r["media"])
    print(f"\nMEJOR limpio: {mejor['variante']} -> {mejor['media']:.4f} "
          f"(base {BASE_F1:.4f}, delta {100*(mejor['media']-BASE_F1):+.2f} pp)")
    print(f"criterio para tocar test: {BASE_F1 + DELTA:.4f}")
    toca = bool(mejor["media"] >= BASE_F1 + DELTA)
    print("CUMPLE: se documenta plan de test." if toca else "NO cumple: test NO se toca.")
    print(f"Brier base {resultados['base_172']['brier_medio']:.4f} -> "
          f"mejor limpio {mejor['brier_medio']:.4f} "
          f"({100*(mejor['brier_medio']-resultados['base_172']['brier_medio']):+.2f} %)")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "N_modelo_limpio",
        "auditoria": nombre_aud,
        "limpieza": {"redundantes": len(redundantes), "duplicados_exactos": len(duplicados),
                     "vif_mayor_10": len(por_vif), "muertas_99": len(muertas),
                     "interseccion": len(set(redundantes) & set(muertas)),
                     "n_base": len(feats), "n_vif": len(f_vif), "n_limpio": len(f_limpio),
                     "p99_n_productos": p99, "filas_winsorizadas": n_afectadas,
                     "winsorizadas_por_split": por_split},
        "config": {k: PARAMS[k] for k in ("n_estimators", "min_child_weight", "gamma",
                                          "subsample", "max_depth", "learning_rate")},
        "resultados": resultados, "mejor": mejor["variante"],
        "base_f1_baja_oos": BASE_F1, "delta_pp": round(100 * (mejor["media"] - BASE_F1), 2),
        "criterio_test": round(BASE_F1 + DELTA, 4), "toco_test": toca,
        "dataset_limpio": str(ruta.name),
    }
    p = RESULTADOS / ("expN_limpio_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    p.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
