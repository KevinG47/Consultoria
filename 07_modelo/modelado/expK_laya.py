#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
expK_laya.py
============

Experimento 3: Laya zero-shot (prueba de concepto, 100 filas del fold F1).

- Fold F1: evaluar en la cohorte 19 (2017) entrenando con 17 (2014).
- Se describe cada investigador en un JSON compacto y se le pregunta a Laya,
  con una pregunta de tipo `score` (0-2), la probabilidad de subir de categoría.
- Se compara la respuesta con la etiqueta real (0=baja, 1=se mantiene, 2=sube).
- Sin ajuste, sin fine-tuning: es una sonda de señal, no un clasificador.

Uso:
    python expK_laya.py --n 100
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

os.environ.setdefault("USE_TF", "0")  # evita el sondeo de TensorFlow de transformers

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import opt_comun as oc  # noqa: E402

RESULTADOS = SCRIPT_DIR / "resultados"
COHORTE_A_ANO = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}
CLASES = ("baja", "se_mantiene", "sube")


def campo(df, nombre, i):
    return float(df.iloc[i][nombre]) if nombre in df.columns else 0.0


def descripcion(df, i):
    cat = int(df.iloc[i]["cat"])
    inst = str(df.iloc[i].get("institucion", "") or "").strip()
    return {
        "categoria_actual": ["Junior", "Asociado", "Sénior", "Emérito"][cat] if cat < 4 else "Desconocida",
        "cohorte": COHORTE_A_ANO.get(int(df.iloc[i]["ID_CONVOCATORIA"]), 0),
        "institucion": inst if inst else "no registrada",
        "productos_totales": campo(df, "n_productos", i),
        "tesis_doctorado": campo(df, "n_tipologia_TESIS_DE_DOCTORADO", i),
        "tesis_maestria": campo(df, "n_tipologia_TESIS_DE_MAESTRIA", i),
        "tesis_pregrado": campo(df, "n_tipologia_TESIS_DE_PREGRADO", i),
        "articulos_a1": campo(df, "n_categoria_ART_CULOS_DE_INVESTIGACI_N_CON_CALIDAD_A1", i),
        "articulos_a2": campo(df, "n_categoria_ART_CULOS_DE_INVESTIGACI_N_CON_CALIDAD_A2", i),
        "articulos_b": campo(df, "n_categoria_ART_CULOS_DE_INVESTIGACI_N_CON_CALIDAD_B", i),
        "articulos_c": campo(df, "n_categoria_ART_CULOS_DE_INVESTIGACI_N_CON_CALIDAD_C", i),
        "libros_a1": campo(df, "n_categoria_LIBROS_DE_INVESTIGACI_N_CON_CALIDAD_A1", i),
        "proyectos_id": campo(df, "n_tipologia_PROYECTO_DE_INVESTIGACION_Y_DESARROLLO", i),
        "tiempo_en_categoria": campo(df, "tiempo_en_categoria", i),
        "grupos": campo(df, "n_grupos_distintos", i),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--modelo", default="convaiinnovations/laya")
    args = ap.parse_args()

    df, feats = oc.cargar()

    # institución desde el censo (el dataset no la trae)
    import pandas as pd
    censo = pd.read_csv(SCRIPT_DIR.parents[1] / "01_datos" / "datos_fuente" /
                        "Investigadores_Reconocidos_por_convocatoria_20261006.csv",
                        usecols=["ID_PERSONA_PR", "ID_CONVOCATORIA", "INST_FILIA"],
                        dtype=str, encoding="utf-8-sig", keep_default_na=False)
    censo["ID_PERSONA_PR"] = censo["ID_PERSONA_PR"].str.strip().str.zfill(10)
    censo["ID_CONVOCATORIA"] = pd.to_numeric(censo["ID_CONVOCATORIA"], errors="coerce")
    censo = censo.drop_duplicates(["ID_PERSONA_PR", "ID_CONVOCATORIA"])
    censo["institucion"] = censo["INST_FILIA"].str.strip().str.upper()
    base = pd.DataFrame({"ID_PERSONA_PR": df["ID_PERSONA_PR"].astype(str).str.zfill(10),
                         "ID_CONVOCATORIA": pd.to_numeric(df["ID_CONVOCATORIA"], errors="coerce")})
    m = base.merge(censo[["ID_PERSONA_PR", "ID_CONVOCATORIA", "institucion"]],
                   on=["ID_PERSONA_PR", "ID_CONVOCATORIA"], how="left")
    m.index = df.index
    df["institucion"] = m["institucion"]

    # fold F1: evaluación = cohorte 19
    per = df["ID_CONVOCATORIA_siguiente"].to_numpy()
    y = df["y"].to_numpy()
    idx = np.flatnonzero(per == 19)
    rng = np.random.default_rng(42)
    sub = rng.choice(idx, size=min(args.n, len(idx)), replace=False)
    print(f"fold F1 | filas de evaluación: {len(idx)} | muestra: {len(sub)}")
    print(f"distribución de la etiqueta en la muestra: "
          f"{dict(zip(*np.unique(y[sub], return_counts=True)))}")

    print(f"cargando Laya ({args.modelo}) en CPU ...")
    t0 = time.time()
    import laya
    agent = laya.load(args.modelo)
    print(f"modelo cargado en {time.time()-t0:.1f}s")

    pregunta = {
        "subida": {
            "type": "score",
            "instructions": ("¿Cuál es la probabilidad de que este investigador suba "
                             "de categoría en la siguiente convocatoria?"),
            "criteria": ["muy improbable", "posible", "muy probable"],
        }
    }

    filas = []
    t_inf = time.time()
    for k, i in enumerate(sub):
        estado = descripcion(df, i)
        try:
            r = agent.predict(estado, pregunta)
            score = float(r["answers"]["subida"]["score"])
        except Exception as e:  # noqa: BLE001
            score = float("nan")
            print(f"  fila {k}: error {type(e).__name__}: {e}")
        filas.append({"i": int(i), "y": int(y[i]), "score": score,
                      "p_sube": score / 2.0 if score == score else float("nan"),
                      "estado": estado})
        if (k + 1) % 20 == 0:
            print(f"  {k+1}/{len(sub)} ... ({time.time()-t_inf:.0f}s)")
    dt = time.time() - t_inf

    sc = np.array([f["score"] for f in filas], dtype=float)
    yy = np.array([f["y"] for f in filas], dtype=float)
    ok = np.isfinite(sc)
    sc, yy = sc[ok], yy[ok]

    corr = {}
    if len(sc) > 3:
        from scipy.stats import spearmanr, pearsonr
        corr["spearman_score_vs_y"] = round(float(spearmanr(sc, yy).statistic), 4)
        corr["pearson_score_vs_y"] = round(float(pearsonr(sc, yy).statistic), 4)
        corr["spearman_p"] = float(spearmanr(sc, yy).pvalue)
        sube = (yy == 2).astype(int)
        if 0 < sube.sum() < len(sube):
            corr["spearman_score_vs_sube_bin"] = round(float(spearmanr(sc, sube).statistic), 4)
        corr["media_score_baja"] = round(float(sc[yy == 0].mean()), 3) if (yy == 0).any() else None
        corr["media_score_mantiene"] = round(float(sc[yy == 1].mean()), 3) if (yy == 1).any() else None
        corr["media_score_sube"] = round(float(sc[yy == 2].mean()), 3) if (yy == 2).any() else None
        corr["n_validas"] = int(len(sc))
        corr["n_errores"] = int((~ok).sum())

    print("\ncorrelaciones:", json.dumps(corr, ensure_ascii=False))
    hay_senal = corr.get("spearman_score_vs_y", 0) is not None and abs(corr.get("spearman_score_vs_y", 0)) > 0.1
    print("SEÑAL > 0.1: " + ("sí, documentar" if hay_senal else "no; Laya no aporta en zero-shot"))

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experimento": "K_laya_zero_shot",
        "modelo": args.modelo,
        "fold": "F1 (eval cohorte 19)",
        "n": int(len(sub)),
        "pregunta": pregunta,
        "correlaciones": corr,
        "senal_mayor_01": bool(hay_senal),
        "segundos_inferencia": round(dt, 1),
        "predicciones": filas,
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida = RESULTADOS / ("expK_laya_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".json")
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado: {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
