#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
agregar_por_persona.py
======================

Fase 3: agrega la produccion por (ID_PERSONA_PR, ID_CONVOCATORIA) y escribe
dos tablas de features en parquet:

  07_modelo/datos/derivados/features_ventana_t.parquet    (solo la ventana t)
  07_modelo/datos/derivados/features_acumulado_t.parquet  (acumulado hasta t)

Decisiones de diseno (aprobadas)
--------------------------------
- Normalizacion de llaves: IDs a string de 10 caracteres con zfill(10) en
  ambos lados; id_convocatoria a entero 16..21 con int(float(x)). Produccion
  trae 7 filas con valores tipo '16.0' que, sin normalizar, rompen la union.
- n_filas    = numero de filas producto-autor del par (cuadra con C11).
- n_productos = nunique(id_producto_pd) (es el feature que entra al modelo).
  La suma de n_productos NO puede cuadrar con C11 por construccion: el
  dataset repite filas que difieren solo en cod_grupo_gr (ver diagnostico).
- n_por_clase, n_por_tipologia y n_por_categoria cuentan PRODUCTOS UNICOS
  por valor (nunique(id_producto_pd)), no filas. El addendum mostro que las
  filas duplicadas solo difieren en cod_grupo_gr: contar filas sobrepondera
  los productos adscritos a varios grupos. Con nunique, la suma de las
  columnas de cada familia en una fila es igual a n_productos.
- Pares de produccion fuera de la grilla del censo (persona reconocida en
  otra convocatoria) se incluyen con en_censo=False. Se necesitan para que
  las sumas por convocatoria reproduzcan C11.
- Los 1 496 reconocidos sin produccion entran con n_filas=0, n_productos=0
  y sin_produccion=True (no se eliminan).
- dias_desde_ultimo = fecha de la convocatoria - max(fcreacion_pd) de los
  productos de ese par. Puede ser negativo si el producto se creo despues
  de la convocatoria, y hay 2 filas con fcreacion < 1900 (anomalia del dato).

Requisitos
----------
pandas y pyarrow. El entorno de poetry del proyecto NO los tiene; ejecutar
con el Python del sistema:

    python 07_modelo/ingesta/agregar_por_persona.py

Salidas: los dos parquet + manifiestos/agregados_<UTC>.json
Codigos: 0 OK | 2 faltan dependencias | 3 pre-validacion fallida | 4 error de datos
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
CENSO_DEFAULT = REPO / "01_datos" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
CONTRATO_DEFAULT = SCRIPT_DIR / "contrato_produccion.json"
MANIFEST_DIR = SCRIPT_DIR / "manifiestos"
DERIVADOS = SCRIPT_DIR.parent / "datos" / "derivados"

CONV_ORDER = {16: 0, 17: 1, 18: 2, 19: 3, 20: 4, 21: 5}
CONV_ANO = {16: 2013, 17: 2014, 18: 2015, 19: 2017, 20: 2019, 21: 2021}


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def normalizar_id(valor: str) -> str:
    v = (valor or "").strip()
    return v.zfill(10) if v else ""


def normalizar_conv(valor: str) -> int | None:
    """int(float(x)): acepta '16', '16.0' y 16.0; devuelve 16..21 o None."""
    v = (valor or "").strip()
    if not v:
        return None
    try:
        i = int(float(v))
    except ValueError:
        return None
    return i if i in CONV_ORDER else None


def parse_fecha(texto: str) -> date | None:
    s = (texto or "").strip()
    if not s:
        return None
    s = s.replace("T", " ")[:10]
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        pass
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except ValueError:
        return None


def slug(texto: str) -> str:
    s = re.sub(r"[^A-Z0-9]+", "_", texto.upper()).strip("_")
    return (s[:70] or "VACIO")


def nombres_columnas(prefijo: str, valores: list[str]) -> list[str]:
    out: list[str] = []
    usados: set[str] = set()
    for valor in valores:
        base = f"{prefijo}_{slug(valor)}"
        nombre, k = base, 2
        while nombre in usados:
            nombre, k = f"{base}_{k}", k + 1
        usados.add(nombre)
        out.append(nombre)
    return out


def sha256(ruta: Path, bloque: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def ultimo_manifiesto() -> dict | None:
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


class Acum:
    """Agregado de un par (persona, convocatoria)."""
    __slots__ = ("n_filas", "productos", "grupos", "max_fcre")

    def __init__(self) -> None:
        self.n_filas = 0
        # producto -> (clase, tipologia, categoria). Se guarda el producto
        # UNICO: las filas duplicadas solo difieren en cod_grupo_gr (addendum).
        self.productos: dict[str, tuple[str, str, str]] = {}
        self.grupos: set[str] = set()
        self.max_fcre: date | None = None


# ----------------------------------------------------------------------------
# Lectura del censo
# ----------------------------------------------------------------------------
def cargar_censo(ruta: Path) -> tuple[set, set, dict, dict]:
    pares: set[tuple[str, int]] = set()
    ids: set[str] = set()
    convs_por_persona: dict[str, set[int]] = defaultdict(set)
    fechas: dict[int, date] = {}
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        cabecera = next(rd)
        low = [h.strip().lower() for h in cabecera]
        try:
            i_conv = low.index("id_convocatoria")
            i_ano = low.index("ano_convo")
            i_id = low.index("id_persona_pr")
        except ValueError:
            raise SystemExit(f"El censo no tiene las columnas esperadas: {cabecera[:8]}")
        for fila in rd:
            if not fila:
                continue
            conv = normalizar_conv(fila[i_conv])
            idv = normalizar_id(fila[i_id])
            if conv is None or not idv:
                continue
            pares.add((idv, conv))
            ids.add(idv)
            convs_por_persona[idv].add(conv)
            fecha = parse_fecha(fila[i_ano])
            if fecha and conv not in fechas:
                fechas[conv] = fecha
    return pares, ids, convs_por_persona, fechas


# ----------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Agrega produccion por persona y convocatoria en dos parquet."
    )
    ap.add_argument("--produccion", default=None,
                    help="CSV de produccion (por defecto, el del ultimo manifiesto).")
    ap.add_argument("--censo", default=str(CENSO_DEFAULT))
    ap.add_argument("--contrato", default=str(CONTRATO_DEFAULT))
    args = ap.parse_args()

    try:
        import numpy as np
        import pandas as pd
        import pyarrow  # noqa: F401
    except ImportError as exc:
        print("ERROR: faltan pandas/pyarrow en este interprete.")
        print("  El entorno de poetry NO las tiene. Ejecute con el Python del sistema:")
        print("    python 07_modelo/ingesta/agregar_por_persona.py")
        print(f"  Detalle: {exc}")
        return 2

    if args.produccion:
        prod = Path(args.produccion).expanduser().resolve()
    else:
        man = ultimo_manifiesto()
        if not man:
            print("ERROR: no hay manifiesto de descarga; use --produccion")
            return 2
        prod = Path(man["archivo"]).expanduser().resolve()
    censo = Path(args.censo).expanduser().resolve()
    if not prod.exists() or not censo.exists():
        print(f"ERROR: no existe {prod} o {censo}")
        return 2

    DERIVADOS.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    print("== Agregados por persona ==")
    print(f"   produccion: {prod}")
    print(f"   censo     : {censo}")

    pares_censo, censo_ids, convs_por_persona, fechas = cargar_censo(censo)
    print(f"   censo: {len(censo_ids):,} personas, {len(pares_censo):,} pares"
          .replace(",", " "))

    # ---- pase unico por produccion (streaming) ----
    datos: dict[tuple[str, int], Acum] = {}
    total = leidos = 0
    with open(prod, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        cabecera = next(rd)
        low = [h.strip().lower() for h in cabecera]
        try:
            i_id = low.index("id_persona_pd")
            i_conv = low.index("id_convocatoria")
            i_prod = low.index("id_producto_pd")
            i_clase = low.index("nme_clase_pd")
            i_tip = low.index("nme_tipologia_pd")
            i_cat = low.index("nme_categoria_pd")
            i_grupo = low.index("cod_grupo_gr")
            i_fcre = low.index("fcreacion_pd")
        except ValueError:
            print(f"ERROR: faltan columnas en produccion: {cabecera[:12]}")
            return 4
        for fila in rd:
            total += 1
            if not fila:
                continue
            idv = normalizar_id(fila[i_id])
            if idv not in censo_ids:
                continue
            conv = normalizar_conv(fila[i_conv])
            if conv is None:
                continue
            clave = (idv, conv)
            a = datos.get(clave)
            if a is None:
                a = Acum()
                datos[clave] = a
            a.n_filas += 1
            leidos += 1
            prod_id = fila[i_prod].strip()
            clase = fila[i_clase].strip()
            tip = fila[i_tip].strip()
            cat = fila[i_cat].strip()
            if prod_id not in a.productos:
                a.productos[prod_id] = (clase, tip, cat)
            grupo = fila[i_grupo].strip()
            if grupo:
                a.grupos.add(grupo)
            fcre = parse_fecha(fila[i_fcre])
            if fcre and (a.max_fcre is None or fcre > a.max_fcre):
                a.max_fcre = fcre
            if total % 1_000_000 == 0:
                print(f"   ... {total:,} filas leidas".replace(",", " "))

    print(f"   filas produccion: {total:,} | usadas (autor del censo): {leidos:,}"
          .replace(",", " "))

    # ---- grilla: censo U produccion ----
    claves = sorted(set(pares_censo) | set(datos), key=lambda k: (k[0], k[1]))
    n = len(claves)
    if n == 0:
        print("ERROR: grilla vacia.")
        return 4
    print(f"   grilla: {n:,} pares ({len(pares_censo):,} del censo + "
          f"{n - len(pares_censo):,} solo produccion)".replace(",", " "))

    # ---- valores para las columnas one-hot ----
    vals_clase = sorted({c for a in datos.values() for c, _, _ in a.productos.values() if c})
    vals_tip = sorted({t for a in datos.values() for _, t, _ in a.productos.values() if t})
    vals_cat = sorted({x for a in datos.values() for _, _, x in a.productos.values() if x})
    cols_clase = nombres_columnas("n_clase", vals_clase)
    cols_tip = nombres_columnas("n_tipologia", vals_tip)
    cols_cat = nombres_columnas("n_categoria", vals_cat)
    cols = cols_clase + cols_tip + cols_cat
    off_tip = len(cols_clase)
    off_cat = off_tip + len(cols_tip)
    idx_clase = {v: i for i, v in enumerate(vals_clase)}
    idx_tip = {v: i for i, v in enumerate(vals_tip)}
    idx_cat = {v: i for i, v in enumerate(vals_cat)}
    print(f"   columnas one-hot: {len(cols)} "
          f"(clase {len(vals_clase)}, tipologia {len(vals_tip)}, "
          f"categoria {len(vals_cat)})")

    mat = np.zeros((n, len(cols)), dtype=np.int32)
    nf = np.zeros(n, dtype=np.int64)
    nprod = np.zeros(n, dtype=np.int64)
    ngrupos = np.zeros(n, dtype=np.int64)
    dias = np.full(n, np.nan, dtype=float)
    en_censo = np.zeros(n, dtype=bool)

    for i, (idv, conv) in enumerate(claves):
        en_censo[i] = (idv, conv) in pares_censo
        a = datos.get((idv, conv))
        if a is None:
            continue
        nf[i] = a.n_filas
        nprod[i] = len(a.productos)
        ngrupos[i] = len(a.grupos)
        if a.max_fcre and conv in fechas:
            dias[i] = (fechas[conv] - a.max_fcre).days
        # Las tres one-hot cuentan nunique(id_producto_pd) por valor.
        clase_ctr: Counter = Counter()
        tip_ctr: Counter = Counter()
        cat_ctr: Counter = Counter()
        for cl, t, c in a.productos.values():
            if cl:
                clase_ctr[cl] += 1
            if t:
                tip_ctr[t] += 1
            if c:
                cat_ctr[c] += 1
        for v, c in clase_ctr.items():
            mat[i, idx_clase[v]] = c
        for v, c in tip_ctr.items():
            mat[i, off_tip + idx_tip[v]] = c
        for v, c in cat_ctr.items():
            mat[i, off_cat + idx_cat[v]] = c

    # ---- acumulado hasta t (mismo orden cronologico del censo) ----
    mat_acum = np.zeros_like(mat)
    nf_acum = np.zeros(n, dtype=np.int64)
    prod_acum = np.zeros(n, dtype=np.int64)
    grupos_acum = np.zeros(n, dtype=np.int64)
    dias_acum = np.full(n, np.nan, dtype=float)

    por_persona: dict[str, list[int]] = defaultdict(list)
    for i in range(n):
        por_persona[claves[i][0]].append(i)

    for idv, idxs in por_persona.items():
        idxs.sort(key=lambda i: CONV_ORDER[claves[i][1]])
        filas = 0
        productos: dict[str, tuple[str, str, str]] = {}
        grupos: set[str] = set()
        max_fcre: date | None = None
        clase: Counter = Counter()
        tip: Counter = Counter()
        cat: Counter = Counter()
        for i in idxs:
            a = datos.get(claves[i])
            if a is not None:
                filas += a.n_filas
                for prod_id, valores in a.productos.items():
                    if prod_id not in productos:
                        productos[prod_id] = valores
                        cl, t, c = valores
                        if cl:
                            clase[cl] += 1
                        if t:
                            tip[t] += 1
                        if c:
                            cat[c] += 1
                grupos |= a.grupos
                if a.max_fcre and (max_fcre is None or a.max_fcre > max_fcre):
                    max_fcre = a.max_fcre
            nf_acum[i] = filas
            prod_acum[i] = len(productos)
            grupos_acum[i] = len(grupos)
            if max_fcre and claves[i][1] in fechas:
                dias_acum[i] = (fechas[claves[i][1]] - max_fcre).days
            for v, c in clase.items():
                mat_acum[i, idx_clase[v]] = c
            for v, c in tip.items():
                mat_acum[i, off_tip + idx_tip[v]] = c
            for v, c in cat.items():
                mat_acum[i, off_cat + idx_cat[v]] = c

    # ---- pre-validacion contra el contrato (antes de escribir) ----
    contrato_path = Path(args.contrato)
    if contrato_path.exists():
        contrato = json.loads(contrato_path.read_text(encoding="utf-8"))
        esperado = None
        for ch in contrato.get("checks", []):
            if ch["id"] == "C11":
                esperado = {int(k): int(v) for k, v in ch["esperado"].items()}
                break
        if esperado:
            convs = np.array([k[1] for k in claves], dtype=np.int16)
            suma = {}
            for conv, valor in zip(convs, nf):
                suma[conv] = suma.get(conv, 0) + int(valor)
            desvio = {c: suma.get(c, 0) - esperado.get(CONV_ANO[c], 0)
                      for c in sorted(suma)}
            print("   suma n_filas por convocatoria vs C11:")
            for c in sorted(suma):
                print(f"      {CONV_ANO[c]}: {suma[c]:,} (esperado {esperado[CONV_ANO[c]]:,})"
                      .replace(",", " "))
            if any(v != 0 for v in desvio.values()):
                print("ERROR: la suma de n_filas no reproduce C11. No se escriben archivos.")
                print(f"   deltas: {desvio}")
                return 3

    # ---- construir y escribir parquet ----
    ids_arr = np.array([k[0] for k in claves], dtype=object)
    convs_arr = np.array([k[1] for k in claves], dtype=np.int16)
    anos_arr = np.array([CONV_ANO[c] for c in convs_arr], dtype=np.int16)

    def construir_df(nf_, nprod_, ngrupos_, dias_, mat_) -> "pd.DataFrame":
        df = pd.DataFrame(mat_, columns=cols)
        df.insert(0, "dias_desde_ultimo", dias_)
        df.insert(0, "n_grupos_distintos", ngrupos_)
        df.insert(0, "n_productos", nprod_)
        df.insert(0, "n_filas", nf_)
        df.insert(0, "sin_produccion", nf_ == 0)
        df.insert(0, "en_censo", en_censo)
        df.insert(0, "ano", anos_arr)
        df.insert(0, "ID_CONVOCATORIA", convs_arr)
        df.insert(0, "ID_PERSONA_PR", ids_arr)
        return df

    df_ventana = construir_df(nf, nprod, ngrupos, dias, mat)
    df_acum = construir_df(nf_acum, prod_acum, grupos_acum, dias_acum, mat_acum)

    ruta_ventana = DERIVADOS / "features_ventana_t.parquet"
    ruta_acum = DERIVADOS / "features_acumulado_t.parquet"
    df_ventana.to_parquet(ruta_ventana, index=False, engine="pyarrow")
    df_acum.to_parquet(ruta_acum, index=False, engine="pyarrow")

    personas = len(por_persona)
    con_prod = sum(1 for idv in por_persona
                   if any(nf[i] > 0 for i in por_persona[idv]))
    sin_prod = personas - con_prod
    fuera_censo = n - len(pares_censo)

    manifiesto = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": 1,
        "produccion": {"archivo": str(prod), "sha256": sha256(prod)},
        "censo": {"archivo": str(censo), "sha256": sha256(censo)},
        "normalizacion": {
            "id": "string 10 caracteres con zfill(10)",
            "id_convocatoria": "int(float(x)) -> 16..21",
            "mapa_convocatorias": {str(c): CONV_ANO[c] for c in sorted(CONV_ANO)},
        },
        "ventana": {
            "archivo": str(ruta_ventana),
            "filas": int(df_ventana.shape[0]),
            "columnas": int(df_ventana.shape[1]),
            "bytes": ruta_ventana.stat().st_size,
            "sha256": sha256(ruta_ventana),
        },
        "acumulado": {
            "archivo": str(ruta_acum),
            "filas": int(df_acum.shape[0]),
            "columnas": int(df_acum.shape[1]),
            "bytes": ruta_acum.stat().st_size,
            "sha256": sha256(ruta_acum),
        },
        "resumen": {
            "personas": personas,
            "pares": n,
            "pares_censo": len(pares_censo),
            "pares_fuera_censo": fuera_censo,
            "personas_con_produccion": con_prod,
            "personas_sin_produccion": sin_prod,
            "columnas_one_hot": len(cols),
        },
        "notas": [
            "n_filas cuadra con C11 (filas producto-autor).",
            "n_productos = nunique(id_producto_pd); su suma no cuadra con C11 a proposito.",
            "n_por_clase, n_por_tipologia y n_por_categoria cuentan productos unicos "
            "por valor (nunique), no filas: las filas duplicadas solo difieren en "
            "cod_grupo_gr.",
            "dias_desde_ultimo puede ser negativo (128 filas con fcreacion > convocatoria) "
            "y hay 2 filas con fcreacion < 1900.",
        ],
    }
    nombre = f"agregados_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    ruta_man = MANIFEST_DIR / nombre
    ruta_man.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    print("\nEscrito:")
    print(f"   {ruta_ventana}  ({df_ventana.shape[0]:,} filas x {df_ventana.shape[1]} cols)"
          .replace(",", " "))
    print(f"   {ruta_acum}  ({df_acum.shape[0]:,} filas x {df_acum.shape[1]} cols)"
          .replace(",", " "))
    print(f"   personas: {personas:,} | con produccion: {con_prod:,} | "
          f"sin produccion: {sin_prod:,}".replace(",", " "))
    print(f"   manifiesto: {ruta_man}")
    print("\nSiguiente paso:")
    print("   python 07_modelo/ingesta/validar_agregados.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
