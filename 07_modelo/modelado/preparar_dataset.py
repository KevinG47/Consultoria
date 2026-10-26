#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
preparar_dataset.py
===================

Fase 4 (v2): dataset del modelo de transicion de categoria, con el dataset
PRIMARIO restringido a transiciones CONTIGUAS (siguiente = actual + 1).

Motivo del cambio: el objetivo de negocio es "predecir la proxima
convocatoria", no "predecir a horizonte variable". Los saltos (16->20,
17->20, etc.) meten horizontes de 2-4 convocatorias bajo la misma etiqueta y
diluyen la senal. Los `_completo` se conservan como conjunto de robustez.

Salidas (07_modelo/datos/derivados/):
  target.parquet                            77 237 filas (censo completo)
  modelo_dataset_ventana_contiguo.parquet   43 187 filas  (PRIMARIO)
  modelo_dataset_ventana_completo.parquet   47 151 filas  (robustez)
  modelo_dataset_acumulado_contiguo.parquet 43 187 filas  (PRIMARIO)
  modelo_dataset_acumulado_completo.parquet 47 151 filas  (robustez)

Definiciones
------------
- target_class: comparacion de ORDEN_CLAS_PR con la SIGUIENTE fila de la
  misma persona: sube / se_mantiene / baja; NaN si no hay siguiente.
- ID_CONVOCATORIA_siguiente, gap = siguiente - actual, contiguo = (gap == 1).
- split por convocatoria DESTINO:
    train: 2014, 2015, 2017   (conv 17, 18, 19)
    val:   2019               (conv 20)
    test:  2021               (conv 21)
    n/a:   sin siguiente
- dias_desde_ultimo: clip(lower=0) + flag dias_desde_ultimo_negativo=True.

Requisitos: pandas y pyarrow (Python del sistema).

Uso:
    python 07_modelo/modelado/preparar_dataset.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
MANIFEST_DIR = SCRIPT_DIR.parent / "ingesta" / "manifiestos"
CENSO_DEFAULT = REPO / "01_datos" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"

SPLIT_DESTINO = {17: "train", 18: "train", 19: "train", 20: "val", 21: "test"}
CLASES = ("sube", "se_mantiene", "baja")


def sha256(ruta: Path, bloque: int = 1 << 20) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def leer_censo(ruta: Path, pd) -> "pd.DataFrame":
    df = pd.read_csv(
        ruta,
        usecols=["ID_PERSONA_PR", "ID_CONVOCATORIA", "ORDEN_CLAS_PR"],
        dtype={"ID_PERSONA_PR": "string", "ID_CONVOCATORIA": "string",
               "ORDEN_CLAS_PR": "string"},
        encoding="utf-8-sig",
    )
    df["ID_PERSONA_PR"] = df["ID_PERSONA_PR"].str.strip().str.zfill(10)
    df["ID_CONVOCATORIA"] = pd.to_numeric(df["ID_CONVOCATORIA"], errors="coerce").astype("Int64")
    df["ORDEN_CLAS_PR_actual"] = pd.to_numeric(df["ORDEN_CLAS_PR"], errors="coerce").astype("Int64")
    df = df.drop(columns=["ORDEN_CLAS_PR"])
    df = df.sort_values(["ID_PERSONA_PR", "ID_CONVOCATORIA"]).reset_index(drop=True)
    return df


def construir_target(df: "pd.DataFrame", pd, np) -> "pd.DataFrame":
    g = df.groupby("ID_PERSONA_PR", sort=False)
    df["ORDEN_CLAS_PR_siguiente"] = g["ORDEN_CLAS_PR_actual"].shift(-1)
    df["ID_CONVOCATORIA_siguiente"] = g["ID_CONVOCATORIA"].shift(-1)
    df["gap"] = (df["ID_CONVOCATORIA_siguiente"] - df["ID_CONVOCATORIA"]).astype("Int64")
    df["contiguo"] = (df["gap"] == 1).fillna(False).astype(bool)

    cur = df["ORDEN_CLAS_PR_actual"].astype("float")
    nxt = df["ORDEN_CLAS_PR_siguiente"].astype("float")
    sube = (nxt > cur).fillna(False)
    baja = (nxt < cur).fillna(False)
    igual = (nxt == cur).fillna(False)
    df["target_class"] = np.select(
        [sube.to_numpy(), baja.to_numpy(), igual.to_numpy()],
        ["sube", "baja", "se_mantiene"],
        default=None,
    )
    destino = df["ID_CONVOCATORIA_siguiente"]
    df["split"] = destino.map(lambda v: SPLIT_DESTINO.get(int(v), "n/a") if pd.notna(v) else "n/a")
    return df


def reporte_distribucion(df: "pd.DataFrame", nombre: str) -> dict:
    print(f"\n   {nombre}: {len(df):,} filas".replace(",", " "))
    salida = {}
    for split in ("train", "val", "test", "n/a"):
        sub = df[df["split"] == split]
        if len(sub) == 0:
            continue
        total = len(sub)
        conteo = sub["target_class"].value_counts(dropna=False).to_dict()
        conteo = {("sin_siguiente" if (k is None or (isinstance(k, float) and k != k)) else k): int(v)
                  for k, v in conteo.items()}
        salida[split] = {"n": total, "clases": conteo}
        print(f"      {split:5s}: {total:7d} filas | " +
              " · ".join(f"{clase}={n} ({100*n/total:.1f} %)"
                         for clase, n in sorted(conteo.items(), key=lambda t: str(t[0]))))
    return salida


def main() -> int:
    ap = argparse.ArgumentParser(description="Construye target y datasets del modelo (contiguos + completo).")
    ap.add_argument("--censo", default=str(CENSO_DEFAULT))
    ap.add_argument("--ventana", default=str(DERIVADOS / "features_ventana_t.parquet"))
    ap.add_argument("--acumulado", default=str(DERIVADOS / "features_acumulado_t.parquet"))
    args = ap.parse_args()

    try:
        import numpy as np
        import pandas as pd
        import pyarrow  # noqa: F401
    except ImportError as exc:
        print("ERROR: faltan pandas/pyarrow. Ejecute con el Python del sistema:")
        print("  python 07_modelo/modelado/preparar_dataset.py")
        print(f"  Detalle: {exc}")
        return 2

    censo = Path(args.censo)
    for p in (censo, Path(args.ventana), Path(args.acumulado)):
        if not p.exists():
            print(f"ERROR: no existe {p}")
            return 2

    DERIVADOS.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    print("== Dataset del modelo (primario: transiciones contiguas) ==")
    df = leer_censo(censo, pd)
    df = construir_target(df, pd, np)

    target_cols = ["ID_PERSONA_PR", "ID_CONVOCATORIA", "ID_CONVOCATORIA_siguiente",
                   "ORDEN_CLAS_PR_actual", "ORDEN_CLAS_PR_siguiente", "gap",
                   "contiguo", "target_class", "split"]
    target = df[target_cols].copy()
    ruta_target = DERIVADOS / "target.parquet"
    target.to_parquet(ruta_target, index=False, engine="pyarrow")
    rep_target = reporte_distribucion(target, "target.parquet (censo completo)")

    con_siguiente = target["target_class"].notna()
    contiguos = int((con_siguiente & target["contiguo"]).sum())
    print(f"\n   pares con siguiente: {int(con_siguiente.sum()):,} | "
          f"contiguos: {contiguos:,}".replace(",", " "))
    print("   distribucion de gap (pares con siguiente): " +
          " · ".join(f"{int(g)}:{n}" for g, n in
                     target.loc[con_siguiente, "gap"].value_counts().sort_index().items()))

    def construir_modelo(features_path: Path, salida: Path, solo_contiguo: bool):
        feat = pd.read_parquet(features_path)
        mod = feat.merge(
            target[["ID_PERSONA_PR", "ID_CONVOCATORIA", "ID_CONVOCATORIA_siguiente",
                    "ORDEN_CLAS_PR_actual", "gap", "contiguo", "target_class", "split"]],
            on=["ID_PERSONA_PR", "ID_CONVOCATORIA"], how="inner", validate="one_to_one",
        )
        mod = mod[mod["target_class"].notna()].copy()
        if solo_contiguo:
            mod = mod[mod["contiguo"]].copy()

        neg = (mod["dias_desde_ultimo"] < 0).fillna(False).astype(bool)
        mod["dias_desde_ultimo"] = mod["dias_desde_ultimo"].clip(lower=0)
        cols = list(mod.columns)
        pos = cols.index("dias_desde_ultimo") + 1
        mod.insert(pos, "dias_desde_ultimo_negativo", neg)

        mod.to_parquet(salida, index=False, engine="pyarrow")
        return mod, int(neg.sum())

    salidas = {
        "ventana_contiguo": (DERIVADOS / "features_ventana_t.parquet",
                             DERIVADOS / "modelo_dataset_ventana_contiguo.parquet", True),
        "ventana_completo": (DERIVADOS / "features_ventana_t.parquet",
                             DERIVADOS / "modelo_dataset_ventana_completo.parquet", False),
        "acumulado_contiguo": (DERIVADOS / "features_acumulado_t.parquet",
                               DERIVADOS / "modelo_dataset_acumulado_contiguo.parquet", True),
        "acumulado_completo": (DERIVADOS / "features_acumulado_t.parquet",
                               DERIVADOS / "modelo_dataset_acumulado_completo.parquet", False),
    }
    modelos = {}
    for clave, (feat, salida, solo_contiguo) in salidas.items():
        mod, neg = construir_modelo(feat, salida, solo_contiguo)
        modelos[clave] = {"df": mod, "neg": neg, "ruta": salida,
                          "dist": reporte_distribucion(mod, salida.name)}

    manifiesto = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": 2,
        "primario": "contiguo (gap == 1)",
        "censo": {"archivo": str(censo), "sha256": sha256(censo)},
        "target": {"archivo": str(ruta_target), "filas": int(len(target)),
                   "columnas": int(target.shape[1]), "sha256": sha256(ruta_target)},
        "split_destino": {str(k): v for k, v in SPLIT_DESTINO.items()},
        "distribucion_target": rep_target,
        "modelos": {},
        "negativos_dias": {},
    }
    for clave, info in modelos.items():
        manifiesto["modelos"][clave] = {
            "archivo": str(info["ruta"]), "filas": int(len(info["df"])),
            "columnas": int(info["df"].shape[1]),
            "sha256": sha256(info["ruta"]),
            "distribucion": info["dist"],
        }
        manifiesto["negativos_dias"][clave] = info["neg"]

    ruta_man = MANIFEST_DIR / f"dataset_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    ruta_man.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    print("\nEscrito:")
    for clave, info in modelos.items():
        d = info["df"]
        print(f"   {info['ruta'].name}: {len(d):,} x {d.shape[1]}".replace(",", " "))
    print(f"   manifiesto: {ruta_man}")
    print("\nSiguiente paso:")
    print("   python 07_modelo/modelado/validar_dataset.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
