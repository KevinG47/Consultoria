#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validar_agregados.py
====================

Valida las dos tablas de features de la Fase 3 contra los criterios aprobados:

  1. sum(n_filas) por convocatoria == C11 (183 868 ... 659 106)
  2. 28 590 personas con >= 1 producto (n_filas > 0)
  3. 1 496 personas con n_filas = 0 y sin_produccion = True
  4. 19 215 personas con >= 2 observaciones en el censo aparecen con al menos
     una fila por convocatoria observada (en_censo = True)
  5. 0 filas duplicadas en (ID_PERSONA_PR, ID_CONVOCATORIA) en ambas tablas
  6. 51 903 pares fuera de la grilla del censo presentes con en_censo = False

Ademas:
  - Coherencia ventana/acumulado: mismas claves, acumulado >= ventana,
    y acumulado no decreciente por persona.
  - Addendum informativo (con DuckDB, si esta disponible): naturaleza de los
    duplicados en (id_persona_pd, id_convocatoria, id_producto_pd).

Requisitos: pandas y pyarrow (y duckdb para el addendum). El entorno de
poetry no los tiene; ejecutar con el Python del sistema:

    python 07_modelo/ingesta/validar_agregados.py

Salidas:
  OK    -> manifiestos/validacion_agregados_<UTC>.json  (exit 0)
  FALLA -> manifiestos/diferencias_agregados.json       (exit 2)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"
MANIFEST_DIR = SCRIPT_DIR / "manifiestos"
CONTRATO_DEFAULT = SCRIPT_DIR / "contrato_produccion.json"
CENSO_DEFAULT = REPO / "01_datos" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
CONV_ANO = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}

ESPERADO_CON_PRODUCCION = 28590
ESPERADO_SIN_PRODUCCION = 1496
ESPERADO_PERSONAS_MULTI = 19215
ESPERADO_FUERA_CENSO = 51903


def sha256(ruta: Path, bloque: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def cargar_censo(ruta: Path) -> tuple[dict[str, set[int]], int]:
    convs: dict[str, set[int]] = {}
    total = 0
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        cabecera = next(rd)
        low = [h.strip().lower() for h in cabecera]
        i_conv = low.index("id_convocatoria")
        i_id = low.index("id_persona_pr")
        for fila in rd:
            if not fila:
                continue
            idv = fila[i_id].strip().zfill(10)
            try:
                conv = int(float(fila[i_conv].strip()))
            except ValueError:
                continue
            convs.setdefault(idv, set()).add(conv)
            total += 1
    return convs, total


def addendum_duplicados(prod: Path, censo: Path) -> dict:
    try:
        import duckdb
    except ImportError:
        return {"disponible": False, "motivo": "duckdb no importable"}
    fila = """(
  COALESCE(CAST(id_convocatoria AS VARCHAR),'<n>'), COALESCE(nme_convocatoria,'<n>'),
  COALESCE(CAST(ano_convo AS VARCHAR),'<n>'), COALESCE(id_producto_pd,'<n>'),
  COALESCE(nme_clase_pd,'<n>'), COALESCE(nme_tipo_medicion_pd,'<n>'),
  COALESCE(nme_tipologia_pd,'<n>'), COALESCE(id_tipo_pd_med,'<n>'),
  COALESCE(nme_categoria_pd,'<n>'), COALESCE(CAST(fcreacion_pd AS VARCHAR),'<n>'),
  COALESCE(nme_producto_pd,'<n>'), COALESCE(cod_grupo_gr,'<n>'),
  COALESCE(nme_grupo_gr,'<n>'), COALESCE(id_persona_pd,'<n>'))"""
    sql = f"""
    WITH p AS (
      SELECT lpad(CAST(id_persona_pd AS VARCHAR), 10, '0') AS id,
             CAST(CAST(id_convocatoria AS DOUBLE) AS INT) AS conv,
             id_producto_pd AS prod,
             COALESCE(nme_tipologia_pd, '<n>') AS tip,
             COALESCE(nme_categoria_pd, '<n>') AS cat,
             COALESCE(cod_grupo_gr, '<n>') AS grupo,
             {fila} AS fila
      FROM read_csv_auto(?, header=true)
    ), c AS (
      SELECT DISTINCT lpad(CAST(ID_PERSONA_PR AS VARCHAR), 10, '0') AS id
      FROM read_csv_auto(?, header=true)
    ), g AS (
      SELECT id, conv, prod, count(*) AS c,
             count(DISTINCT tip) AS t, count(DISTINCT cat) AS cn,
             count(DISTINCT grupo) AS gr, count(DISTINCT fila) AS fn
      FROM p WHERE id IN (SELECT id FROM c)
      GROUP BY 1,2,3 HAVING count(*) > 1
    )
    SELECT count(*) AS grupos, sum(c-1) AS extra,
           count(*) FILTER (WHERE t>1) AS g_tip,
           count(*) FILTER (WHERE cn>1) AS g_cat,
           count(*) FILTER (WHERE gr>1) AS g_grupo,
           count(*) FILTER (WHERE fn=1) AS g_puro
    FROM g
    """
    try:
        con = duckdb.connect()
        r = con.execute(sql, [str(prod), str(censo)]).fetchone()
        con.close()
    except Exception as exc:  # noqa: BLE001
        return {"disponible": False, "motivo": f"error duckdb: {exc}"}
    return {
        "disponible": True,
        "alcance": "autores del censo",
        "grupos_duplicados": int(r[0]),
        "filas_extra": int(r[1]),
        "grupos_cambia_tipologia": int(r[2]),
        "grupos_cambia_categoria": int(r[3]),
        "grupos_cambia_grupo": int(r[4]),
        "grupos_todas_columnas_identicas": int(r[5]),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Valida las tablas de agregados por persona (Fase 3)."
    )
    ap.add_argument("--ventana", default=str(DERIVADOS / "features_ventana_t.parquet"))
    ap.add_argument("--acumulado", default=str(DERIVADOS / "features_acumulado_t.parquet"))
    ap.add_argument("--censo", default=str(CENSO_DEFAULT))
    ap.add_argument("--contrato", default=str(CONTRATO_DEFAULT))
    ap.add_argument("--produccion", default=None,
                    help="CSV de produccion para el addendum (por defecto, el del manifiesto).")
    args = ap.parse_args()

    try:
        import pandas as pd
        import pyarrow  # noqa: F401
    except ImportError as exc:
        print("ERROR: faltan pandas/pyarrow en este interprete.")
        print("  Ejecute con el Python del sistema:")
        print("    python 07_modelo/ingesta/validar_agregados.py")
        print(f"  Detalle: {exc}")
        return 2

    ventana_path = Path(args.ventana)
    acum_path = Path(args.acumulado)
    for ruta in (ventana_path, acum_path):
        if not ruta.exists():
            print(f"ERROR: no existe {ruta}")
            return 2

    contrato = json.loads(Path(args.contrato).read_text(encoding="utf-8"))
    c11 = None
    for ch in contrato.get("checks", []):
        if ch["id"] == "C11":
            c11 = {int(k): int(v) for k, v in ch["esperado"].items()}
            break

    convs_censo, total_censo = cargar_censo(Path(args.censo))
    personas_multi = sorted(p for p, cs in convs_censo.items() if len(cs) >= 2)

    ventana = pd.read_parquet(ventana_path)
    acum = pd.read_parquet(acum_path)

    checks: list[dict] = []

    def add(cid, nombre, esperado, observado, ok, detalle=None):
        checks.append({"id": cid, "nombre": nombre, "esperado": esperado,
                       "observado": observado, "ok": bool(ok),
                       "detalle": detalle})

    # 1. sum(n_filas) por convocatoria == C11
    suma = {int(k): int(v) for k, v in ventana.groupby("ano")["n_filas"].sum().items()}
    ok1 = c11 is not None and suma == c11
    add("V01", "sum_n_filas_por_convocatoria", c11, suma, ok1,
        None if ok1 else {a: suma.get(a, 0) - c11.get(a, 0) for a in sorted(c11 or {})})

    # 2. personas con >= 1 producto
    por_persona = ventana.groupby("ID_PERSONA_PR")["n_filas"].sum()
    con_prod = int((por_persona > 0).sum())
    add("V02", "personas_con_produccion", ESPERADO_CON_PRODUCCION, con_prod,
        con_prod == ESPERADO_CON_PRODUCCION)

    # 3. personas sin produccion
    ids_sin = set(por_persona[por_persona == 0].index)
    sin_prod = len(ids_sin)
    flag_ok = True
    if ids_sin:
        sub = ventana[ventana["ID_PERSONA_PR"].isin(ids_sin)]
        flag_ok = bool(sub["sin_produccion"].all())
    add("V03", "personas_sin_produccion", ESPERADO_SIN_PRODUCCION, sin_prod,
        sin_prod == ESPERADO_SIN_PRODUCCION and flag_ok,
        None if flag_ok else "hay filas sin_produccion=False para personas sin produccion")

    # 4. personas con >= 2 observaciones presentes en todas sus convocatorias
    presentes: dict[str, set[int]] = {}
    en_censo = ventana[ventana["en_censo"]]
    for idv, conv in zip(en_censo["ID_PERSONA_PR"], en_censo["ID_CONVOCATORIA"]):
        presentes.setdefault(idv, set()).add(int(conv))
    faltan = [p for p in personas_multi if not convs_censo[p] <= presentes.get(p, set())]
    ok4 = len(personas_multi) == ESPERADO_PERSONAS_MULTI and not faltan
    add("V04", "personas_multi_presentes", ESPERADO_PERSONAS_MULTI,
        len(personas_multi) - len(faltan), ok4,
        None if not faltan else f"faltan {len(faltan)} personas; ej. {faltan[:5]}")

    # 5. duplicados en la llave
    dup_v = int(ventana.duplicated(subset=["ID_PERSONA_PR", "ID_CONVOCATORIA"]).sum())
    dup_a = int(acum.duplicated(subset=["ID_PERSONA_PR", "ID_CONVOCATORIA"]).sum())
    add("V05", "duplicados_llave_ventana", 0, dup_v, dup_v == 0)
    add("V06", "duplicados_llave_acumulado", 0, dup_a, dup_a == 0)

    # 6. pares fuera de la grilla del censo
    fuera = int((~ventana["en_censo"]).sum())
    add("V07", "pares_fuera_censo", ESPERADO_FUERA_CENSO, fuera,
        fuera == ESPERADO_FUERA_CENSO)

    # 7. coherencia ventana/acumulado
    claves_v = set(zip(ventana["ID_PERSONA_PR"], ventana["ID_CONVOCATORIA"]))
    claves_a = set(zip(acum["ID_PERSONA_PR"], acum["ID_CONVOCATORIA"]))
    add("V08", "mismas_claves_ventana_acumulado", len(claves_v),
        len(claves_a), claves_v == claves_a)

    nf_acum = dict(zip(zip(acum["ID_PERSONA_PR"], acum["ID_CONVOCATORIA"]),
                       acum["n_filas"]))
    incumple = 0
    for idv, conv, valor in zip(ventana["ID_PERSONA_PR"], ventana["ID_CONVOCATORIA"],
                                ventana["n_filas"]):
        if int(nf_acum.get((idv, conv), -1)) < int(valor):
            incumple += 1
    add("V09", "acumulado_ge_ventana", 0, incumple, incumple == 0)

    monotono = 0
    orden = {c: i for i, c in CONV_ANO.items()}
    for idv, grupo in acum.groupby("ID_PERSONA_PR"):
        valores = [int(v) for _, v in sorted(zip(grupo["ID_CONVOCATORIA"],
                                                 grupo["n_filas"]),
                                             key=lambda t: orden.get(t[0], 99))]
        if any(b < a for a, b in zip(valores, valores[1:])):
            monotono += 1
    add("V10", "acumulado_no_decreciente_por_persona", 0, monotono, monotono == 0)

    # V11-V14: la suma de las columnas one-hot de categoria/tipologia debe
    # igualar n_productos en cada fila (nunique, no conteo de filas).
    cols_cat = [c for c in ventana.columns if c.startswith("n_categoria_")]
    cols_tip = [c for c in ventana.columns if c.startswith("n_tipologia_")]

    incumple_cat = int((ventana[cols_cat].sum(axis=1) != ventana["n_productos"]).sum())
    add("V11", "suma_categoria_igual_n_productos", 0, incumple_cat, incumple_cat == 0)

    incumple_tip = int((ventana[cols_tip].sum(axis=1) != ventana["n_productos"]).sum())
    add("V12", "suma_tipologia_igual_n_productos", 0, incumple_tip, incumple_tip == 0)

    incumple_cat_a = int((acum[cols_cat].sum(axis=1) != acum["n_productos"]).sum())
    add("V13", "suma_categoria_igual_n_productos_acumulado", 0, incumple_cat_a,
        incumple_cat_a == 0)

    incumple_tip_a = int((acum[cols_tip].sum(axis=1) != acum["n_productos"]).sum())
    add("V14", "suma_tipologia_igual_n_productos_acumulado", 0, incumple_tip_a,
        incumple_tip_a == 0)

    # V15-V16: la misma identidad para la clase (nunique, no conteo de filas).
    cols_clase = [c for c in ventana.columns if c.startswith("n_clase_")]
    incumple_clase = int((ventana[cols_clase].sum(axis=1) != ventana["n_productos"]).sum())
    add("V15", "suma_clase_igual_n_productos", 0, incumple_clase, incumple_clase == 0)

    incumple_clase_a = int((acum[cols_clase].sum(axis=1) != acum["n_productos"]).sum())
    add("V16", "suma_clase_igual_n_productos_acumulado", 0, incumple_clase_a,
        incumple_clase_a == 0)

    # ---- addendum informativo ----
    prod_path = None
    if args.produccion:
        prod_path = Path(args.produccion)
    else:
        man = None
        for p in sorted(MANIFEST_DIR.glob("produccion_*.json"),
                        key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                man = json.loads(p.read_text(encoding="utf-8"))
                break
            except (OSError, ValueError):
                continue
        if man:
            prod_path = Path(man["archivo"])
    addendum = {"disponible": False, "motivo": "sin ruta de produccion"}
    if prod_path and prod_path.exists():
        print("   calculando addendum de duplicados (duckdb)...")
        addendum = addendum_duplicados(prod_path, Path(args.censo))

    # ---- tabla ----
    print("\nComprobaciones:")
    for c in checks:
        marca = "OK  " if c["ok"] else "FALLA"
        print(f"  [{marca}] {c['id']} {c['nombre']:<36} esperado={c['esperado']!s:>12}  "
              f"observado={c['observado']!s:>12}")
        if c["detalle"]:
            print(f"          detalle: {c['detalle']}")

    if addendum.get("disponible"):
        print("\nAddendum informativo (duplicados en id_persona_pd x convocatoria x producto, "
              "autores del censo):")
        print(f"   grupos duplicados                     : {addendum['grupos_duplicados']:,}"
              .replace(",", " "))
        print(f"   filas extra                           : {addendum['filas_extra']:,}"
              .replace(",", " "))
        print(f"   grupos donde cambia nme_tipologia_pd  : {addendum['grupos_cambia_tipologia']:,}"
              .replace(",", " "))
        print(f"   grupos donde cambia nme_categoria_pd  : {addendum['grupos_cambia_categoria']:,}"
              .replace(",", " "))
        print(f"   grupos donde cambia cod_grupo_gr      : {addendum['grupos_cambia_grupo']:,}"
              .replace(",", " "))
        print(f"   grupos con TODAS las columnas iguales : "
              f"{addendum['grupos_todas_columnas_identicas']:,}".replace(",", " "))
    else:
        print(f"\nAddendum informativo: no disponible ({addendum.get('motivo')})")

    fallos = [c for c in checks if not c["ok"]]
    ok_total = not fallos
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    if ok_total:
        destino = MANIFEST_DIR / f"validacion_agregados_{ts}.json"
        payload = {
            "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ventana": {"archivo": str(ventana_path), "sha256": sha256(ventana_path),
                        "filas": int(ventana.shape[0]), "columnas": int(ventana.shape[1])},
            "acumulado": {"archivo": str(acum_path), "sha256": sha256(acum_path),
                          "filas": int(acum.shape[0]), "columnas": int(acum.shape[1])},
            "censo": {"archivo": str(Path(args.censo)), "filas": total_censo,
                      "personas": len(convs_censo)},
            "contrato": str(Path(args.contrato)),
            "checks": checks,
            "addendum_duplicados": addendum,
            "resultado": "OK",
        }
        destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                           encoding="utf-8")
        print(f"\nRESULTADO: OK. {len(checks)}/{len(checks)} comprobaciones pasan.")
        print(f"   validacion: {destino}")
        return 0

    destino = MANIFEST_DIR / "diferencias_agregados.json"
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
