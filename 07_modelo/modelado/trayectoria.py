#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
trayectoria.py
==============

Construye 4 features de TRAYECTORIA por (ID_PERSONA_PR, ID_CONVOCATORIA):

  a. tiempo_en_categoria : n de convocatorias consecutivas en la categoria
     actual, contando desde la primera aparicion en esa categoria.
  b. historial_bajas / historial_subidas : cuantas transiciones ha bajado /
     subido la persona hasta t (incluye la transicion que termina en t, que ya
     es informacion observada). 0 si es su primera observacion.
  c. momentum_produccion : n_productos(t) / (n_productos(t-1) + 1).
     1.0 si la persona no tiene fila en t-1.
  d. produccion_normalizada : n_productos(t) / mediana de n_productos de su
     categoria en t (mediana calculada por convocatoria x categoria, sin
     etiquetas).

Fuentes: modelo_dataset_ventana_contiguo.parquet (categorias y produccion) y
features_ventana_t.parquet (produccion por persona-convocatoria, para localizar
t-1 aunque no exista fila de transicion). No descarga nada.

Salida: 07_modelo/datos/derivados/trayectoria_features.parquet
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
RESULTADOS = SCRIPT_DIR / "resultados"


def main() -> int:
    df = pd.read_parquet(DERIVADOS / "modelo_dataset_ventana_contiguo.parquet",
                         columns=["ID_PERSONA_PR", "ID_CONVOCATORIA",
                                  "ORDEN_CLAS_PR_actual", "n_productos",
                                  "target_class", "split"])
    df["ID_PERSONA_PR"] = df["ID_PERSONA_PR"].astype(str)
    df = df.sort_values(["ID_PERSONA_PR", "ID_CONVOCATORIA"]).reset_index(drop=True)
    print(f"filas: {len(df)} | personas: {df.ID_PERSONA_PR.nunique()} | "
          f"convocatorias: {sorted(df.ID_CONVOCATORIA.unique().tolist())}")

    g = df.groupby("ID_PERSONA_PR", sort=False)
    df["prev_conv"] = g["ID_CONVOCATORIA"].shift()
    df["prev_cat"] = g["ORDEN_CLAS_PR_actual"].shift()
    consec = (df["ID_CONVOCATORIA"] - df["prev_conv"]) == 1
    mismo = df["ORDEN_CLAS_PR_actual"] == df["prev_cat"]
    delta = df["ORDEN_CLAS_PR_actual"] - df["prev_cat"]

    # a) tiempo en categoria (runs de misma categoria con convocatorias consecutivas)
    nuevo_run = ~(consec & mismo)
    df["_run"] = nuevo_run.astype(int).cumsum()
    df["tiempo_en_categoria"] = (df.groupby(["ID_PERSONA_PR", "_run"]).cumcount() + 1).astype("float32")

    # b) historial de bajadas / subidas (incluye la transicion que termina en t)
    baja_t = (consec & (delta < 0)).astype(int)
    sube_t = (consec & (delta > 0)).astype(int)
    df["_baja"] = baja_t
    df["_sube"] = sube_t
    df["historial_bajas"] = (df.groupby("ID_PERSONA_PR", sort=False)["_baja"].cumsum()).astype("float32")
    df["historial_subidas"] = (df.groupby("ID_PERSONA_PR", sort=False)["_sube"].cumsum()).astype("float32")

    # c) momentum: produccion t / (produccion t-1 + 1), 1.0 si no hay t-1
    feats = pd.read_parquet(DERIVADOS / "features_ventana_t.parquet",
                            columns=["ID_PERSONA_PR", "ID_CONVOCATORIA", "n_productos"])
    feats["ID_PERSONA_PR"] = feats["ID_PERSONA_PR"].astype(str)
    feats = feats.rename(columns={"ID_CONVOCATORIA": "prev_conv", "n_productos": "prod_prev"})
    izq = df[["ID_PERSONA_PR", "prev_conv"]].copy()
    izq["prev_conv"] = izq["prev_conv"].astype("float")
    merge = izq.merge(feats, on=["ID_PERSONA_PR", "prev_conv"], how="left")
    df["prod_prev"] = merge["prod_prev"].to_numpy()
    df["momentum_produccion"] = np.where(
        df["prod_prev"].notna(),
        df["n_productos"].to_numpy() / (df["prod_prev"].to_numpy() + 1.0),
        1.0).astype("float32")

    # d) produccion normalizada por mediana de su categoria en t
    med = df.groupby(["ID_CONVOCATORIA", "ORDEN_CLAS_PR_actual"])["n_productos"].transform("median")
    den = np.where(med.to_numpy() > 0, med.to_numpy(), 1.0)
    df["produccion_normalizada"] = (df["n_productos"].to_numpy() / den).astype("float32")

    cols = ["tiempo_en_categoria", "historial_bajas", "historial_subidas",
            "momentum_produccion", "produccion_normalizada"]
    for c in cols:
        print(f"\n{c}: min={df[c].min():.3f} med={df[c].median():.3f} "
              f"max={df[c].max():.3f} nulos={int(df[c].isna().sum())}")
    print("\nmomentum: proporcion con t-1 disponible = "
          f"{df['prod_prev'].notna().mean():.4f}")

    df["_target"] = df["target_class"].map({"baja": 0, "se_mantiene": 1, "sube": 2})
    print("\ncorrelacion (Spearman) con el target ordinal 0=baja,2=sube:")
    for c in cols:
        print(f"   {c:24s} {df[[c, '_target']].corr(method='spearman').iloc[0, 1]:+.3f}")
    print("\nmedia de cada feature por clase real:")
    for c in cols:
        medias = df.groupby("target_class")[c].mean()
        print(f"   {c:24s} " + " | ".join(f"{k}={v:.3f}" for k, v in medias.items()))

    salida = DERIVADOS / "trayectoria_features.parquet"
    out = df[["ID_PERSONA_PR", "ID_CONVOCATORIA"] + cols].copy()
    out["ID_CONVOCATORIA"] = out["ID_CONVOCATORIA"].astype("int16")
    out.to_parquet(salida, index=False)
    print(f"\nGuardado: {salida} ({len(out)} filas, {len(cols)} features)")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "filas": int(len(out)), "features": cols,
        "momentum_con_t_menos_1": float(df["prod_prev"].notna().mean()),
        "estadisticos": {c: {"min": float(df[c].min()), "mediana": float(df[c].median()),
                             "max": float(df[c].max()), "nulos": int(df[c].isna().sum())}
                         for c in cols},
        "correlacion_spearman_ordinal": {
            c: float(df[[c, "_target"]].corr(method="spearman").iloc[0, 1]) for c in cols},
        "media_por_clase": {c: {k: float(v) for k, v in
                                df.groupby("target_class")[c].mean().items()} for c in cols},
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    (RESULTADOS / "trayectoria_features_info.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
