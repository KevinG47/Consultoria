#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expL_nivel_formacion.py
=======================

Experimento 4: nivel de formación (variable del censo con anclaje directo en los
criterios de Minciencias, ver 07_modelo/documentacion/criterios_minciencias.md).

- Fuente: NME_NIV_FORM_PR del censo (77 237 registros persona x convocatoria).
- Codificación justificada en el script: ordinal de 6 niveles (principal) y
  one-hot (control), porque la formación es una escala ordenada pero con
  categorías raras.
- Config Ronda 2 y 3 folds temporales. Test (cohorte 21) NO se toca.
- Criterio: media F1 baja OOS >= 0.3185 (+2 pp sobre 0.2985).
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
RAIZ = SCRIPT_DIR.parents[1]
CENSO = RAIZ / "01_datos" / "datos_fuente" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
BASE_F1 = 0.2985
DELTA = 0.02
PARAMS = dict(oc.BASE, n_estimators=100, min_child_weight=1, gamma=0.1,
              subsample=0.8, max_depth=7, learning_rate=0.05)

# 0 pregrado < 1 especialización < 2 maestría < 3 doctorado < 4 postdoctorado
NIVEL = {
    "Pregrado/Universitario": 0,
    "Técnico - nivel superior": 0,
    "Secundario": 0,
    "Cursos de corta duración": 0,
    "Perfeccionamiento": 1,
    "Especialización": 1,
    "Especialidad Médica": 1,
    "Maestría/Magister": 2,
    "Doctorado": 3,
    "Postdoctorado": 4,
}
OTRO = 5  # "No disponible" y vacíos


def niveles(df):
    import pandas as pd

    c = pd.read_csv(CENSO, usecols=["ID_PERSONA_PR", "ID_CONVOCATORIA", "NME_NIV_FORM_PR"],
                    dtype=str, encoding="utf-8-sig", keep_default_na=False)
    c["ID_PERSONA_PR"] = c["ID_PERSONA_PR"].str.strip().str.zfill(10)
    c["ID_CONVOCATORIA"] = pd.to_numeric(c["ID_CONVOCATORIA"], errors="coerce")
    c = c.drop_duplicates(["ID_PERSONA_PR", "ID_CONVOCATORIA"])
    c["nivel"] = c["NME_NIV_FORM_PR"].str.strip().map(NIVEL).fillna(OTRO).astype(int)
    c["nivel_txt"] = c["NME_NIV_FORM_PR"].str.strip()

    base = pd.DataFrame({"ID_PERSONA_PR": df["ID_PERSONA_PR"].astype(str).str.zfill(10),
                         "ID_CONVOCATORIA": pd.to_numeric(df["ID_CONVOCATORIA"], errors="coerce")})
    m = base.merge(c[["ID_PERSONA_PR", "ID_CONVOCATORIA", "nivel", "nivel_txt"]],
                   on=["ID_PERSONA_PR", "ID_CONVOCATORIA"], how="left")
    m.index = df.index

    out = pd.DataFrame(index=df.index)
    out["nivel_formacion"] = m["nivel"].fillna(OTRO).astype("float32")
    for k in range(6):
        out[f"nivel_{k}"] = (m["nivel"] == k).astype("float32")
    out["tiene_doctorado_o_mas"] = (m["nivel"].isin([3, 4])).astype("float32")
    out["nivel_faltante"] = m["nivel"].isna().astype("float32")
    return out, m["nivel_txt"]


def correr(X, y, cat, per, variante):
    f1s, macros, briers, ts = [], [], [], []
    for fold in oc.FOLDS:
        t, _, p_va, p_ev, y_ev = oc.correr_fold(X, y, cat, per, fold, PARAMS)
        m = oc.metricas_eval(p_ev, y_ev, t)
        f1s.append(m["f1_baja"]); macros.append(m["f1_macro"]); briers.append(m["brier"]); ts.append(t)
    return {"variante": variante,
            "f1_baja_folds": [round(v, 4) for v in f1s],
            "media": round(float(np.mean(f1s)), 4),
            "desv": round(float(np.std(f1s, ddof=0)), 4),
            "f1_macro_medio": round(float(np.mean(macros)), 4),
            "brier_medio": round(float(np.mean(briers)), 4),
            "umbrales": ts}


def main() -> int:
    df, feats = oc.cargar()
    niv, txt = niveles(df)
    print("distribución de nivel de formación en el censo (persona x convocatoria):")
    print(txt.value_counts().to_string())
    print(f"faltantes (no disponible o sin registro): {int(niv['nivel_faltante'].sum())} "
          f"({niv['nivel_faltante'].mean():.2%} de las filas del dataset)")
    print(f"\ncobertura del cruce: {1-niv['nivel_faltante'].mean():.2%} de las filas")

    Xb = oc.matriz(df, feats)
    y = df["y"].to_numpy()
    cat = df["cat"].to_numpy()
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()

    variantes = {
        "base_172": Xb,
        "ordinal": np.column_stack([Xb, niv["nivel_formacion"].to_numpy("float32")]),
        "onehot": np.column_stack([Xb] + [niv[f"nivel_{k}"].to_numpy("float32") for k in range(6)]),
        "ordinal_binario": np.column_stack([
            Xb,
            niv["nivel_formacion"].to_numpy("float32"),
            niv["tiene_doctorado_o_mas"].to_numpy("float32"),
            niv["nivel_faltante"].to_numpy("float32"),
        ]),
    }

    resultados = {}
    print(f"\n{'variante':16s} {'folds':26s} {'media':>6} {'desv':>6} {'F1macro':>8} {'Brier':>7}  t")
    for nombre, X in variantes.items():
        r = correr(X, y, cat, per, nombre)
        resultados[nombre] = r
        print(f"{nombre:16s} {str(r['f1_baja_folds']):26s} {r['media']:>6.4f} "
              f"{r['desv']:>6.4f} {r['f1_macro_medio']:>8.4f} {r['brier_medio']:>7.4f}  {r['umbrales']}")

    mejor = max([r for k, r in resultados.items() if k != "base_172"], key=lambda r: r["media"])
    print(f"\nMEJOR: {mejor['variante']} -> media {mejor['media']:.4f} "
          f"(base {BASE_F1:.4f}, delta {100*(mejor['media']-BASE_F1):+.2f} pp)")
    print(f"criterio para tocar test: media >= {BASE_F1 + DELTA:.4f}")
    toca = bool(mejor["media"] >= BASE_F1 + DELTA)
    print("CUMPLE: se documenta plan de test." if toca else "NO cumple: test NO se toca.")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "L_nivel_formacion",
        "variable": "NME_NIV_FORM_PR (censo)",
        "n_base": len(feats), "config": {k: PARAMS[k] for k in
                                         ("n_estimators", "min_child_weight", "gamma",
                                          "subsample", "max_depth", "learning_rate")},
        "cobertura": round(float(1 - niv["nivel_faltante"].mean()), 4),
        "distribucion_censo": txt.value_counts().to_dict(),
        "variantes": resultados, "mejor": mejor,
        "base_f1_baja_oos": BASE_F1, "delta_pp": round(100 * (mejor["media"] - BASE_F1), 2),
        "criterio_test": round(BASE_F1 + DELTA, 4), "toco_test": toca, "test": None,
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("expL_nivel_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
