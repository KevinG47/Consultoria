#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
red_features.py
===============

Construye features de RED por (ID_PERSONA_PR, ID_CONVOCATORIA) desde
produccion_grupos.csv (1,26 GB, 3 166 629 filas).

HALLAZGO PREVIO IMPORTANTE
--------------------------
El archivo NO contiene listas de coautores: cada producto tiene en promedio
1,02 autores (máximo 6) porque `id_producto_pd` identifica al producto de UNA
persona (p. ej. ART-0000045012-144). Con 1 642 283 productos distintos, la
coautoría por producto compartido deja solo 72 226 pares en todo el censo:
es degenerada y no puede alimentar un modelo.

La única estructura social real del archivo es `cod_grupo_gr` (grupo de
investigación reconocido): 7 467 grupos, tamaño medio 10,3, máximo 137. Por
eso la red se construye sobre PERTENENCIA A GRUPO (co-membresía), que es el
análogo operativo de la red de coautorías en estos datos.

Features (6):
  a. n_companeros_distintos : personas distintas con las que comparte al menos
     un grupo en la convocatoria.
  b. companeros_que_subieron : de esos compañeros, cuántos subieron de
     categoría en la transición que termina en t-1.
  c. companeros_que_bajaron : ídem para bajadas.
  d. centralidad_grado      : grado del nodo normalizado por el máximo de la
     convocatoria.
  e. n_grupos_distintos_red : grupos distintos en la convocatoria (se compara
     con la feature n_grupos_distintos ya existente).
  f. companero_categoria_modal : categoría ordinal modal de sus compañeros
     en t (proxy de "categoría del coautor más frecuente", imposible con
     productos de un solo autor).

Salida: 07_modelo/datos/derivados/red_features.parquet
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.csv as pv

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
RESULTADOS = SCRIPT_DIR / "resultados"
RAW = Path(r"C:\datos_externos\minciencias\33dq-ab5a\2026-10-25\produccion_grupos.csv")
CENSO = REPO / "01_datos" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"


def cargar_produccion() -> pd.DataFrame:
    tbl = pv.read_csv(
        RAW,
        read_options=pv.ReadOptions(use_threads=True),
        convert_options=pv.ConvertOptions(
            include_columns=["id_convocatoria", "cod_grupo_gr", "id_persona_pd"],
            column_types={"id_convocatoria": "string", "cod_grupo_gr": "string",
                          "id_persona_pd": "string"},
        ),
    )
    df = tbl.to_pandas()
    df["conv"] = df["id_convocatoria"].astype(float).astype(int)
    df["persona"] = df["id_persona_pd"].str.strip()
    df["grupo"] = df["cod_grupo_gr"].str.strip()
    df = df[(df["persona"] != "") & (df["persona"] != "0000000000")]
    return df[["conv", "grupo", "persona"]].drop_duplicates()


def main() -> int:
    df = cargar_produccion()
    print(f"produccion: {len(df)} combinaciones unicas (conv, grupo, persona) | "
          f"convocatorias {sorted(df.conv.unique().tolist())} | "
          f"personas {df.persona.nunique()} | grupos {df.grupo.nunique()}")

    censo = pd.read_csv(CENSO, usecols=["ID_PERSONA_PR", "ID_CONVOCATORIA",
                                        "ORDEN_CLAS_PR"], dtype=str,
                        encoding="utf-8-sig", keep_default_na=False)
    censo["persona"] = censo["ID_PERSONA_PR"].str.strip().str.zfill(10)
    censo["conv"] = pd.to_numeric(censo["ID_CONVOCATORIA"], errors="coerce")
    censo["orden"] = pd.to_numeric(censo["ORDEN_CLAS_PR"], errors="coerce")
    censo = censo.dropna(subset=["conv", "orden"])
    censo["conv"] = censo["conv"].astype(int)
    cat = {(p, c): int(o) for p, c, o in zip(censo["persona"], censo["conv"],
                                             censo["orden"])}
    print(f"censo: {len(cat)} pares (persona, convocatoria) con categoria | "
          f"convocatorias {sorted(censo.conv.unique().tolist())}")

    # miembros por (conv, grupo)
    grupos = defaultdict(list)
    for conv, grupo, persona in df.itertuples(index=False):
        grupos[(conv, grupo)].append(persona)
    print(f"grupos-convocatoria: {len(grupos)} | tamano medio "
          f"{np.mean([len(v) for v in grupos.values()]):.1f}")

    filas = []
    for conv in sorted(df.conv.unique()):
        peers = defaultdict(set)
        n_grupos = defaultdict(set)
        for (c, grupo), miembros in grupos.items():
            if c != conv:
                continue
            for p in miembros:
                n_grupos[p].add(grupo)
                peers[p].update(miembros)
        grados = {}
        for p, conjunto in peers.items():
            conjunto.discard(p)
            grados[p] = len(conjunto)
        max_grado = max(grados.values()) if grados else 1
        for p, conjunto in peers.items():
            subieron = bajaron = 0
            for q in conjunto:
                prev2, prev1 = cat.get((q, conv - 2)), cat.get((q, conv - 1))
                if prev1 is None or prev2 is None:
                    continue
                if prev1 > prev2:
                    subieron += 1
                elif prev1 < prev2:
                    bajaron += 1
            cats = [cat[(q, conv)] for q in conjunto if (q, conv) in cat]
            modal = Counter(cats).most_common(1)[0][0] if cats else 0
            filas.append({
                "persona": p, "conv": conv,
                "n_companeros_distintos": len(conjunto),
                "companeros_que_subieron": subieron,
                "companeros_que_bajaron": bajaron,
                "centralidad_grado": len(conjunto) / max_grado if max_grado else 0.0,
                "n_grupos_distintos_red": len(n_grupos[p]),
                "companero_categoria_modal": float(modal),
            })
        print(f"   conv {conv}: personas con red {len(peers)} | grado max {max_grado}")

    out = pd.DataFrame(filas)
    print(f"\nfilas de red: {len(out)}")
    for c in ["n_companeros_distintos", "companeros_que_subieron",
              "companeros_que_bajaron", "centralidad_grado",
              "n_grupos_distintos_red", "companero_categoria_modal"]:
        print(f"   {c:28s} min={out[c].min():.2f} med={out[c].median():.2f} "
              f"max={out[c].max():.2f}")

    # cotejo de n_grupos_distintos contra el dataset del modelo
    dat = pd.read_parquet(DERIVADOS / "modelo_dataset_ventana_contiguo.parquet",
                          columns=["ID_PERSONA_PR", "ID_CONVOCATORIA",
                                   "n_grupos_distintos", "target_class"])
    dat["persona"] = dat["ID_PERSONA_PR"].astype(str).str.zfill(10)
    dat["conv"] = dat["ID_CONVOCATORIA"].astype(int)
    cmp = dat.merge(out, left_on=["persona", "conv"], right_on=["persona", "conv"],
                    how="left")
    cubierto = cmp["n_companeros_distintos"].notna().mean()
    ok = cmp.dropna(subset=["n_grupos_distintos_red"])
    corr = np.corrcoef(ok["n_grupos_distintos"], ok["n_grupos_distintos_red"])[0, 1]
    iguales = float((ok["n_grupos_distintos"] == ok["n_grupos_distintos_red"]).mean())
    print(f"\ncotejo con el dataset del modelo ({len(dat)} filas):")
    print(f"   cobertura de la red: {cubierto:.4f}")
    print(f"   n_grupos_distintos vs n_grupos_distintos_red: corr={corr:.4f} | "
          f"igualdad exacta={iguales:.4f}")

    out["ID_PERSONA_PR"] = out["persona"]
    out["ID_CONVOCATORIA"] = out["conv"].astype("int16")
    salida = DERIVADOS / "red_features.parquet"
    out[["ID_PERSONA_PR", "ID_CONVOCATORIA", "n_companeros_distintos",
         "companeros_que_subieron", "companeros_que_bajaron", "centralidad_grado",
         "n_grupos_distintos_red", "companero_categoria_modal"]].to_parquet(
        salida, index=False)
    print(f"\nGuardado: {salida} ({len(out)} filas)")

    resumen = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hallazgo_coautoria_por_producto": {
            "productos_distintos": 1642283, "autores_por_producto_media": 1.02,
            "autores_por_producto_max": 6, "pares_coautoria_totales": 72226,
            "conclusion": "productos personales: la coautoria por producto es "
                          "degenerada; la red se construye sobre grupo de "
                          "investigacion (co-membresia)"},
        "filas_red": int(len(out)), "cobertura_dataset": float(cubierto),
        "cotejo_n_grupos": {"correlacion": float(corr), "igualdad_exacta": iguales},
        "features": ["n_companeros_distintos", "companeros_que_subieron",
                     "companeros_que_bajaron", "centralidad_grado",
                     "n_grupos_distintos_red", "companero_categoria_modal"],
    }
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    (RESULTADOS / "red_features_info.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
