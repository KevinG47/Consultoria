#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validar_dataset.py
==================

Valida los parquet de la Fase 4 (v2, primario = transiciones contiguas):

  V01  filas de los `_contiguo` = 43 187 en ambos (y `_completo` = 47 151)
  V02  2019->2021 y 2017->2019 coinciden con las matrices del auditado
  V03  0 NaN en (ID_PERSONA_PR, ID_CONVOCATORIA) en los cinco parquet
  V04  0 duplicados en (ID_PERSONA_PR, ID_CONVOCATORIA) en los cinco
  V05  los 77 237 pares del censo estan en target.parquet
  V06  anti-leakage: las features coinciden con la fila de target de la
       MISMA convocatoria; target_class y split recompuestos desde el censo
  V07  en los `_contiguo`, todas las filas tienen gap == 1
  V08  en los `_contiguo`, split coincide con el destino
       (train -> 17/18/19; val -> 20; test -> 21)
  V09  en los `_contiguo`, 0 filas con gap > 1

Requisitos: pandas y pyarrow (Python del sistema).

Uso:
    python 07_modelo/modelado/validar_dataset.py

Salidas:
  OK    -> 07_modelo/ingesta/manifiestos/validacion_dataset_<UTC>.json  (exit 0)
  FALLA -> 07_modelo/ingesta/manifiestos/diferencias_dataset.json       (exit 2)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
MANIFEST_DIR = SCRIPT_DIR.parent / "ingesta" / "manifiestos"
EVIDENCIAS = REPO / "04_auditoria" / "repo_original" / "evidencias"
CENSO_DEFAULT = REPO / "01_datos" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"

CLASES = ("sube", "se_mantiene", "baja")
SPLIT_DESTINO = {17: "train", 18: "train", 19: "train", 20: "val", 21: "test"}
ORDEN = {"Junior": 12, "Asociado": 13, "Senior": 14, "Emérito": 15}
ESPERADO_CONTIGUO = 43187
ESPERADO_COMPLETO = 47151
ESPERADO_CENSO = 77237


def sha256(ruta: Path, bloque: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def leer_matriz(ruta: Path) -> dict:
    texto = ruta.read_text(encoding="utf-8-sig")
    rd = csv.reader(io.StringIO(texto))
    cabecera = next(rd)
    cols = [c.strip() for c in cabecera[1:]]
    acc: Counter = Counter()
    for fila in rd:
        if not fila:
            continue
        ini = fila[0].strip()
        oi = ORDEN[ini]
        for col, valor in zip(cols, fila[1:]):
            n = int(float(valor or 0))
            oj = ORDEN[col]
            acc["sube" if oj > oi else ("baja" if oj < oi else "se_mantiene")] += n
    return {clase: int(acc.get(clase, 0)) for clase in CLASES}


def cargar_censo(censo: Path) -> tuple[set, dict]:
    filas = []
    with open(censo, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        cabecera = next(rd)
        low = [h.strip().lower() for h in cabecera]
        i_id = low.index("id_persona_pr")
        i_conv = low.index("id_convocatoria")
        i_orden = low.index("orden_clas_pr")
        for fila in rd:
            if not fila:
                continue
            filas.append((fila[i_id].strip().zfill(10),
                          int(float(fila[i_conv])),
                          int(float(fila[i_orden]))))
    filas.sort(key=lambda t: (t[0], t[1]))
    pares: set[tuple[str, int]] = set()
    mapa: dict[tuple[str, int], tuple] = {}
    for i, (pid, conv, orden) in enumerate(filas):
        pares.add((pid, conv))
        if i + 1 < len(filas) and filas[i + 1][0] == pid:
            nconv, norden = filas[i + 1][1], filas[i + 1][2]
            clase = "sube" if norden > orden else ("baja" if norden < orden else "se_mantiene")
            mapa[(pid, conv)] = (orden, nconv, norden, clase, SPLIT_DESTINO.get(nconv, "n/a"))
        else:
            mapa[(pid, conv)] = (orden, None, None, None, "n/a")
    return pares, mapa


def main() -> int:
    ap = argparse.ArgumentParser(description="Valida los parquet del dataset del modelo (contiguo + completo).")
    ap.add_argument("--target", default=str(DERIVADOS / "target.parquet"))
    ap.add_argument("--ventana-contiguo",
                    default=str(DERIVADOS / "modelo_dataset_ventana_contiguo.parquet"))
    ap.add_argument("--ventana-completo",
                    default=str(DERIVADOS / "modelo_dataset_ventana_completo.parquet"))
    ap.add_argument("--acumulado-contiguo",
                    default=str(DERIVADOS / "modelo_dataset_acumulado_contiguo.parquet"))
    ap.add_argument("--acumulado-completo",
                    default=str(DERIVADOS / "modelo_dataset_acumulado_completo.parquet"))
    ap.add_argument("--censo", default=str(CENSO_DEFAULT))
    args = ap.parse_args()

    try:
        import pandas as pd
        import pyarrow  # noqa: F401
    except ImportError as exc:
        print("ERROR: faltan pandas/pyarrow. Ejecute con el Python del sistema:")
        print("  python 07_modelo/modelado/validar_dataset.py")
        print(f"  Detalle: {exc}")
        return 2

    rutas = {
        "target": Path(args.target),
        "ventana_contiguo": Path(args.ventana_contiguo),
        "ventana_completo": Path(args.ventana_completo),
        "acumulado_contiguo": Path(args.acumulado_contiguo),
        "acumulado_completo": Path(args.acumulado_completo),
    }
    for p in rutas.values():
        if not p.exists():
            print(f"ERROR: no existe {p}")
            return 2

    target = pd.read_parquet(rutas["target"])
    modelos = {k: pd.read_parquet(v) for k, v in rutas.items() if k != "target"}
    v_con = modelos["ventana_contiguo"]
    a_con = modelos["acumulado_contiguo"]
    pares_censo, mapa = cargar_censo(Path(args.censo))

    checks: list[dict] = []

    def add(cid, nombre, esperado, observado, ok, detalle=None):
        checks.append({"id": cid, "nombre": nombre, "esperado": esperado,
                       "observado": observado, "ok": bool(ok), "detalle": detalle})

    # V01
    add("V01", "filas_contiguo", ESPERADO_CONTIGUO,
        {"ventana_contiguo": int(len(v_con)), "acumulado_contiguo": int(len(a_con)),
         "ventana_completo": int(len(modelos["ventana_completo"])),
         "acumulado_completo": int(len(modelos["acumulado_completo"]))},
        len(v_con) == ESPERADO_CONTIGUO and len(a_con) == ESPERADO_CONTIGUO)

    # V02: matrices del auditado. Con contiguos, conv 19 solo puede ir a 20 y
    # conv 20 solo a 21 (gap == 1).
    m_20 = leer_matriz(EVIDENCIAS / "matriz_transicion_2019_2021.csv")
    m_19 = leer_matriz(EVIDENCIAS / "matriz_transicion_2017_2019.csv")
    comparaciones = []
    for conv, destino, esperado, etiqueta in (
            (20, 21, m_20, "2019->2021"),
            (19, 20, m_19, "2017->2019")):
        sub = v_con[(v_con["ID_CONVOCATORIA"] == conv)
                    & (v_con["ID_CONVOCATORIA_siguiente"] == destino)]
        obs = {c: int((sub["target_class"] == c).sum()) for c in CLASES}
        comparaciones.append({"transicion": etiqueta, "convocatoria": conv,
                              "destino": destino, "filas": int(len(sub)),
                              "esperado": esperado, "observado": obs,
                              "ok": obs == esperado})
    add("V02", "matrices_transicion", [c["esperado"] for c in comparaciones],
        [c["observado"] for c in comparaciones],
        all(c["ok"] for c in comparaciones),
        [c["transicion"] for c in comparaciones])

    # V03: nulos en llaves (cinco parquet)
    nulos = {k: int(df[["ID_PERSONA_PR", "ID_CONVOCATORIA"]].isna().sum().sum())
             for k, df in [("target", target)] + list(modelos.items())}
    add("V03", "nulos_en_llaves", {k: 0 for k in nulos}, nulos,
        all(v == 0 for v in nulos.values()))

    # V04: duplicados en llaves (cinco parquet)
    dups = {k: int(df.duplicated(subset=["ID_PERSONA_PR", "ID_CONVOCATORIA"]).sum())
            for k, df in [("target", target)] + list(modelos.items())}
    add("V04", "duplicados_llaves", {k: 0 for k in dups}, dups,
        all(v == 0 for v in dups.values()))

    # V05: censo completo en target
    claves_target = set(zip(target["ID_PERSONA_PR"], target["ID_CONVOCATORIA"].astype(int)))
    add("V05", "censo_completo_en_target", ESPERADO_CENSO,
        {"filas": int(len(target)), "pares": len(claves_target),
         "coincide": claves_target == pares_censo},
        len(target) == ESPERADO_CENSO and claves_target == pares_censo)

    # V06: anti-leakage en los cuatro datasets del modelo
    llaves = ["ID_PERSONA_PR", "ID_CONVOCATORIA"]
    resumen_v6 = {}
    for nombre, df in modelos.items():
        m = df.merge(target, on=llaves, how="left", suffixes=("", "_target"),
                     validate="many_to_one")
        mal_clase = int((m["target_class"] != m["target_class_target"]).sum())
        mal_split = int((m["split"] != m["split_target"]).sum())
        sin_target = int(m["target_class_target"].isna().sum())

        mm_clase = mm_split = mm_conv = mm_orden = 0
        for pid, conv, clase, split, orden in zip(
                df["ID_PERSONA_PR"], df["ID_CONVOCATORIA"].astype(int),
                df["target_class"], df["split"], df["ORDEN_CLAS_PR_actual"].astype(int)):
            exp = mapa.get((pid, int(conv)))
            if exp is None or exp[1] is None:
                mm_conv += 1
                continue
            if exp[3] != clase:
                mm_clase += 1
            if exp[4] != split:
                mm_split += 1
            if exp[0] != orden:
                mm_orden += 1
        resumen_v6[nombre] = {
            "merge_filas": int(len(m)), "merge_sin_target": sin_target,
            "merge_clase_distinta": mal_clase, "merge_split_distinto": mal_split,
            "recompuesto_clase_distinta": mm_clase,
            "recompuesto_split_distinto": mm_split,
            "recompuesto_conv_sin_siguiente": mm_conv,
            "recompuesto_orden_distinto": mm_orden,
        }
    ok_v6 = all(v == 0 for r in resumen_v6.values() for k, v in r.items()
                if k != "merge_filas")
    add("V06", "anti_leakage", 0, resumen_v6, ok_v6)

    # V07-V09: garantias de los contiguos
    no_contiguo = {}
    split_mal = {}
    gap_mayor = {}
    for nombre, df in (("ventana_contiguo", v_con), ("acumulado_contiguo", a_con)):
        no_contiguo[nombre] = int(((df["gap"] != 1) | df["gap"].isna()).sum())
        destino = df["ID_CONVOCATORIA_siguiente"].astype(int)
        esperado_split = destino.map(SPLIT_DESTINO)
        split_mal[nombre] = int((df["split"] != esperado_split).sum())
        gap_mayor[nombre] = int((df["gap"] > 1).sum())
    add("V07", "contiguo_gap_igual_1", {"ventana_contiguo": 0, "acumulado_contiguo": 0},
        no_contiguo, all(v == 0 for v in no_contiguo.values()))
    add("V08", "contiguo_split_por_destino",
        {"ventana_contiguo": 0, "acumulado_contiguo": 0}, split_mal,
        all(v == 0 for v in split_mal.values()))
    add("V09", "contiguo_sin_gap_mayor_1", {"ventana_contiguo": 0, "acumulado_contiguo": 0},
        gap_mayor, all(v == 0 for v in gap_mayor.values()))

    # ---- tabla ----
    print("\nComprobaciones:")
    for c in checks:
        marca = "OK  " if c["ok"] else "FALLA"
        print(f"  [{marca}] {c['id']} {c['nombre']:<28} esperado={c['esperado']!s:>16}  "
              f"observado={c['observado']!s:>16}")
        if c["detalle"]:
            print(f"          detalle: {c['detalle']}")

    print("\nDistribucion de target_class por split:")
    for nombre, df in modelos.items():
        print(f"\n   {nombre} ({len(df):,} filas)".replace(",", " "))
        for split in ("train", "val", "test"):
            sub = df[df["split"] == split]
            if len(sub) == 0:
                continue
            total = len(sub)
            partes = " · ".join(f"{c}={int((sub['target_class'] == c).sum())} "
                                f"({100*int((sub['target_class'] == c).sum())/total:.1f} %)"
                                for c in CLASES)
            print(f"      {split:5s}: {total:6d} filas | {partes}")

    fallos = [c for c in checks if not c["ok"]]
    ok_total = not fallos
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    if ok_total:
        destino = MANIFEST_DIR / f"validacion_dataset_{ts}.json"
        payload = {
            "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "checks": checks,
            "resultado": "OK",
            "archivos": {k: {"archivo": str(p), "filas": int(len(pd.read_parquet(p))),
                             "sha256": sha256(p)} for k, p in rutas.items()},
        }
        destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")
        print(f"\nRESULTADO: OK. {len(checks)}/{len(checks)} comprobaciones pasan.")
        print(f"   validacion: {destino}")
        return 0

    destino = MANIFEST_DIR / "diferencias_dataset.json"
    payload = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "resultado": "FALLA",
        "fallos": fallos,
        "checks": checks,
        "resumen": f"{len(fallos)} de {len(checks)} comprobaciones fallaron",
    }
    destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(f"\nRESULTADO: FALLA. {len(fallos)} comprobacion(es) no coinciden.")
    print(f"   diferencias: {destino}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
