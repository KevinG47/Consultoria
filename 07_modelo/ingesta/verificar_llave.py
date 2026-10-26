#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
verificar_llave.py
==================

Diagnostico RAPIDO y de SOLO LECTURA de la llave de union entre produccion
y censo. No escribe ningun archivo.

Responde:
  1. Que valores exactos toma id_convocatoria en produccion (deben ser 6).
  2. Con que valores del censo (ID_CONVOCATORIA) se corresponden.
  3. Cuantas filas de produccion tienen id_convocatoria vacio/nulo.
  4. Si la union es 1:1 o hace falta un mapa (p. ej. produccion "833" vs censo 20).
  5. Extra: si hay duplicados en (id_persona_pd, id_convocatoria, id_producto_pd),
     dato que condiciona n_productos = nunique(id_producto_pd).

Uso:
    python 07_modelo/ingesta/verificar_llave.py
    python 07_modelo/ingesta/verificar_llave.py --produccion "C:\\...\\produccion_grupos.csv"
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
CENSO_DEFAULT = REPO / "01_datos" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
MANIFEST_DIR = SCRIPT_DIR / "manifiestos"


def _ultimo_manifiesto() -> dict | None:
    if not MANIFEST_DIR.exists():
        return None
    candidatos = sorted(MANIFEST_DIR.glob("produccion_*.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    for p in candidatos:
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return None


def _leer_produccion(ruta: Path) -> dict:
    total = 0
    vacios = 0
    convs: Counter = Counter()
    pares_conv_ano: Counter = Counter()
    ids_mal_formados = 0
    cabecera = None
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        cabecera = next(rd)
        low = [h.strip().lower() for h in cabecera]
        i_id = low.index("id_persona_pd")
        i_conv = low.index("id_convocatoria")
        i_ano = low.index("ano_convo") if "ano_convo" in low else None
        for fila in rd:
            if not fila:
                continue
            total += 1
            conv = (fila[i_conv] if i_conv < len(fila) else "").strip()
            if not conv:
                vacios += 1
            else:
                convs[conv] += 1
                if i_ano is not None:
                    ano = (fila[i_ano] if i_ano < len(fila) else "").strip()
                    pares_conv_ano[(conv, ano[:4] if ano else "")] += 1
            idv = (fila[i_id] if i_id < len(fila) else "").strip()
            if idv and (len(idv) != 10 or not idv.isdigit()):
                ids_mal_formados += 1
    return {
        "cabecera": cabecera,
        "total": total,
        "vacios": vacios,
        "convs": convs,
        "pares_conv_ano": pares_conv_ano,
        "ids_mal_formados": ids_mal_formados,
    }


def _leer_censo(ruta: Path) -> dict:
    total = 0
    convs: Counter = Counter()
    pares_conv_ano: Counter = Counter()
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        cabecera = next(rd)
        low = [h.strip().lower() for h in cabecera]
        i_conv = low.index("id_convocatoria")
        i_ano = low.index("ano_convo")
        for fila in rd:
            if not fila:
                continue
            total += 1
            conv = fila[i_conv].strip()
            convs[conv] += 1
            pares_conv_ano[(conv, fila[i_ano].strip()[:4])] += 1
    return {"total": total, "convs": convs, "pares_conv_ano": pares_conv_ano}


def _duplicados(ruta: Path) -> dict:
    """Comprueba duplicados con DuckDB (opcional, solo lectura)."""
    try:
        import duckdb
    except ImportError:
        return {"disponible": False, "motivo": "duckdb no importable"}
    try:
        con = duckdb.connect()
        sql = (
            "SELECT count(*) AS filas, "
            "count(DISTINCT (id_persona_pd, id_convocatoria, id_producto_pd)) AS unicos "
            "FROM read_csv_auto(?, header=true)"
        )
        filas, unicos = con.execute(sql, [str(ruta)]).fetchone()
        con.close()
        return {"disponible": True, "filas": int(filas), "unicos": int(unicos),
                "duplicados": int(filas) - int(unicos)}
    except Exception as exc:  # noqa: BLE001
        return {"disponible": False, "motivo": f"error duckdb: {exc}"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnostico de la llave produccion<->censo.")
    ap.add_argument("--produccion", default=None)
    ap.add_argument("--censo", default=str(CENSO_DEFAULT))
    args = ap.parse_args()

    if args.produccion:
        prod = Path(args.produccion).expanduser().resolve()
    else:
        man = _ultimo_manifiesto()
        if not man:
            print("ERROR: no hay manifiesto de descarga; use --produccion")
            return 2
        prod = Path(man["archivo"]).expanduser().resolve()
    if not prod.exists():
        print(f"ERROR: no existe {prod}")
        return 2

    print("== Diagnostico de llave: produccion <-> censo ==")
    print(f"   produccion: {prod}")
    print(f"   censo     : {args.censo}")

    p = _leer_produccion(prod)
    c = _leer_censo(Path(args.censo))

    print(f"\n[1] Produccion: {p['total']:,} filas".replace(",", " "))
    print(f"    cabecera: {p['cabecera'][:12]} ...")
    print(f"    id_convocatoria vacios: {p['vacios']:,}".replace(",", " "))
    print(f"    id_persona_pd mal formados (no 10 digitos): {p['ids_mal_formados']:,}"
          .replace(",", " "))
    print(f"    valores distintos de id_convocatoria: {len(p['convs'])}")
    for v, n in sorted(p["convs"].items(), key=lambda x: (len(x[0]), x[0])):
        print(f"      {v!r:>8} -> {n:,} filas".replace(",", " "))

    print(f"\n[2] Censo: {c['total']:,} filas; valores distintos: {len(c['convs'])}"
          .replace(",", " "))
    for v, n in sorted(c["convs"].items(), key=lambda x: (len(x[0]), x[0])):
        print(f"      {v!r:>8} -> {n:,} filas".replace(",", " "))

    prod_vals = set(p["convs"])
    censo_vals = set(c["convs"])
    print(f"\n[3] Comparacion de conjuntos")
    print(f"    produccion: {sorted(prod_vals)}")
    print(f"    censo     : {sorted(censo_vals)}")
    print(f"    en produccion y NO en censo: {sorted(prod_vals - censo_vals)}")
    print(f"    en censo y NO en produccion: {sorted(censo_vals - prod_vals)}")

    print(f"\n[4] Correspondencia convocatoria -> ano (produccion)")
    for (conv, ano), n in sorted(p["pares_conv_ano"].items(), key=lambda x: x[0]):
        print(f"      conv {conv!r:>6} ano {ano!r:>6} -> {n:,} filas".replace(",", " "))
    print(f"    Correspondencia en el censo")
    for (conv, ano), n in sorted(c["pares_conv_ano"].items(), key=lambda x: x[0]):
        print(f"      conv {conv!r:>6} ano {ano!r:>6} -> {n:,} filas".replace(",", " "))

    print(f"\n[5] Duplicados en (id_persona_pd, id_convocatoria, id_producto_pd)")
    d = _duplicados(prod)
    if d.get("disponible"):
        print(f"    filas={d['filas']:,}  unicos={d['unicos']:,}  duplicados={d['duplicados']:,}"
              .replace(",", " "))
        print(f"    NOTA: n_productos = nunique(id_producto_pd); si duplicados>0, "
              f"la suma de n_productos NO igualara los conteos de filas de C11.")
    else:
        print(f"    no verificado ({d.get('motivo')})")

    print("\n[RESUMEN]")
    if prod_vals == censo_vals:
        print("    La llave id_convocatoria es 1:1 (mismos valores en ambos lados).")
        print("    Union directa por (id_persona_pd=id_persona_pr, id_convocatoria),")
        print("    normalizando el valor a entero (p. ej. '16' o '16.0' -> 16).")
    else:
        print("    ATENCION: los conjuntos NO coinciden; hace falta un mapa explicito.")
        print("    NO continuar con la agregacion hasta resolverlo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
