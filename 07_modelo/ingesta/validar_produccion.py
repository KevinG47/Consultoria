#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validar_produccion.py
=====================

Valida el CSV de produccion descargado contra las 12 comprobaciones del
contrato (07_modelo/ingesta/contrato_produccion.json) mas la comprobacion
adicional (A01) y las estructurales (E01-E05).

Regla de oro: tolerancia CERO. Si una sola comprobacion falla, el pipeline
se detiene. El script NO construye features: solo verifica.

Uso
---
    python 07_modelo/ingesta/validar_produccion.py
    python 07_modelo/ingesta/validar_produccion.py --archivo "C:\\datos_externos\\...\\produccion_grupos.csv"
    python 07_modelo/ingesta/validar_produccion.py --manifiesto 07_modelo/ingesta/manifiestos/produccion_XXXX.json

Si no se indica --archivo, toma el archivo del manifiesto de descarga mas
reciente que exista en manifiestos/.

Salidas
-------
  OK    -> manifiestos/validacion_<UTC>.json   y codigo de salida 0
  FALLA -> manifiestos/diferencias.json        y codigo de salida 2
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[1]
CONTRATO_DEFAULT = SCRIPT_DIR / "contrato_produccion.json"
CENSO_DEFAULT = REPO / "01_datos" / "datos_fuente" / \
    "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
MANIFEST_DIR = SCRIPT_DIR / "manifiestos"


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def _sha256(ruta: Path, bloque: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def _cargar_json(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def _normalizar_conv(valor: str, mapa: dict) -> int | None:
    """Convierte 16..21 (o 2013..2021) en el ano de la convocatoria."""
    v = (valor or "").strip()
    if not v:
        return None
    try:
        i = int(float(v))
    except ValueError:
        return None
    if str(i) in mapa:
        return int(mapa[str(i)])
    if 1900 <= i <= 2100:
        return i
    return None


def _anio(ano_convo: str, conv: str, mapa: dict) -> int | None:
    """Ano de la fila: primero por ano_convo, si no por id_convocatoria."""
    a = (ano_convo or "").strip()
    if a:
        if len(a) >= 4 and a[:4].isdigit():
            return int(a[:4])
        if "/" in a:
            ult = a.split("/")[-1][:4]
            if ult.isdigit():
                return int(ult)
    return _normalizar_conv(conv, mapa)


def _cargar_censo(ruta: Path) -> tuple[set[str], Counter, dict[str, set[str]]]:
    """Devuelve (ids globales, conteo por convocatoria, ids por convocatoria).

    Los ids por convocatoria son imprescindibles para A01: la interseccion
    correcta es censo DEL ANO x produccion DEL ANO, no censo global.
    """
    ids: set[str] = set()
    por_conv: Counter = Counter()
    ids_por_conv: dict[str, set[str]] = defaultdict(set)
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        cabecera = next(rd)
        low = [h.strip().lower() for h in cabecera]
        try:
            i_id = low.index("id_persona_pr")
            i_conv = low.index("id_convocatoria")
        except ValueError:
            raise SystemExit(f"El censo no tiene ID_PERSONA_PR/ID_CONVOCATORIA: {cabecera[:6]}")
        for fila in rd:
            if not fila:
                continue
            conv = fila[i_conv].strip()
            idv = fila[i_id].strip()
            if idv:
                idv_n = idv.zfill(10)
                ids.add(idv_n)
                ids_por_conv[conv].add(idv_n)
            por_conv[conv] += 1
    return ids, por_conv, ids_por_conv


def _manifiesto_para(archivo: Path | None, ruta: str | None = None) -> dict | None:
    if ruta:
        p = Path(ruta)
        return _cargar_json(p) if p.exists() else None
    if not MANIFEST_DIR.exists():
        return None
    candidatos = sorted(MANIFEST_DIR.glob("produccion_*.json"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    for p in candidatos:
        try:
            d = _cargar_json(p)
        except (OSError, ValueError):
            continue
        if archivo is None:
            return d
        try:
            if Path(d.get("archivo", "")).resolve() == archivo.resolve():
                return d
        except OSError:
            continue
    return None


def _comparar(esperado, observado) -> tuple[bool, dict | int]:
    if isinstance(esperado, dict):
        esp = {str(k): int(v) for k, v in esperado.items()}
        obs = {str(k): int(v) for k, v in observado.items()}
        return esp == obs, obs
    return int(esperado) == int(observado), int(observado)


def _fmt(valor) -> str:
    if isinstance(valor, dict):
        return "{" + ", ".join(f"{k}:{v}" for k, v in sorted(valor.items())) + "}"
    return f"{int(valor):,}".replace(",", " ")


def _delta(esperado, observado):
    if isinstance(esperado, dict) or not isinstance(observado, int):
        return None
    try:
        return int(observado) - int(esperado)
    except (TypeError, ValueError):
        return None


# ----------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Valida el CSV de produccion contra el contrato (tolerancia cero)."
    )
    ap.add_argument("--archivo", default=None, help="Ruta del CSV de produccion.")
    ap.add_argument("--contrato", default=str(CONTRATO_DEFAULT),
                    help="Ruta del contrato JSON.")
    ap.add_argument("--censo", default=str(CENSO_DEFAULT),
                    help="Ruta del censo (CSV).")
    ap.add_argument("--manifiesto", default=None,
                    help="Manifiesto de descarga concreto (opcional).")
    args = ap.parse_args()

    contrato = _cargar_json(Path(args.contrato))
    mapa = {str(k): int(v) for k, v in contrato["mapa_convocatorias"].items()}
    anios_validos = set(mapa.values())

    if args.archivo:
        archivo = Path(args.archivo).expanduser().resolve()
    else:
        man = _manifiesto_para(None)
        if not man:
            print("ERROR: no se indico --archivo y no hay manifiestos de descarga.")
            return 2
        archivo = Path(man["archivo"]).expanduser().resolve()
        print(f"   archivo (desde manifiesto): {archivo}")

    if not archivo.exists():
        print(f"ERROR: no existe el archivo {archivo}")
        return 2

    censo_ids, censo_por_conv, censo_ids_por_conv = _cargar_censo(Path(args.censo))
    censo_por_ano: dict[int, int] = {}
    for conv, n in censo_por_conv.items():
        year = _normalizar_conv(conv, mapa)
        if year is not None:
            censo_por_ano[year] = censo_por_ano.get(year, 0) + n
    censo_ids_por_ano: dict[int, set[str]] = defaultdict(set)
    for conv, conjunto in censo_ids_por_conv.items():
        year = _normalizar_conv(conv, mapa)
        if year is not None:
            censo_ids_por_ano[year] |= conjunto

    print("== Validacion de produccion ==")
    print(f"   archivo : {archivo}")
    print(f"   censo   : {Path(args.censo)}  ({len(censo_ids):,} IDs)".replace(",", " "))
    print(f"   contrato: {Path(args.contrato)} (v{contrato.get('version', '?')})")

    total = 0
    autores: set[str] = set()
    per_ano: Counter = Counter()
    rec_filas: Counter = Counter()
    prod_set: dict[int, set[str]] = defaultdict(set)
    bad = nulos = anio_desc = 0

    try:
        with open(archivo, encoding="utf-8-sig", newline="") as f:
            rd = csv.reader(f)
            cabecera = next(rd)
            low = [h.strip().lower() for h in cabecera]
            try:
                i_id = low.index("id_persona_pd")
                i_conv = low.index("id_convocatoria")
                i_ano = low.index("ano_convo")
            except ValueError:
                print(f"ERROR: faltan columnas en la cabecera: {cabecera[:10]}")
                return 2
            for fila in rd:
                if not fila:
                    continue
                total += 1
                idv = (fila[i_id] if i_id < len(fila) else "").strip()
                conv = (fila[i_conv] if i_conv < len(fila) else "").strip()
                ano_raw = (fila[i_ano] if i_ano < len(fila) else "").strip()

                if not idv or not conv:
                    nulos += 1
                    continue
                if len(idv) != 10 or not idv.isdigit():
                    bad += 1
                    continue
                year = _anio(ano_raw, conv, mapa)
                if year is None:
                    anio_desc += 1
                    continue
                per_ano[year] += 1
                autores.add(idv)
                prod_set[year].add(idv)
                if idv in censo_ids:
                    rec_filas[year] += 1

                if total % 1_000_000 == 0:
                    print(f"   ... {total:,} filas leidas".replace(",", " "))
    except UnicodeDecodeError as exc:
        print(f"ERROR: el archivo no es UTF-8 valido: {exc}")
        return 2

    interseccion = censo_ids & autores
    c09 = len(interseccion)
    c10 = len(censo_ids) - c09
    anios_extra = sorted(set(per_ano) - anios_validos)

    print(f"   filas leidas: {total:,} | autores unicos: {len(autores):,}"
          .replace(",", " "))

    # ---- 12 comprobaciones del contrato ----
    resultados = []
    for ch in contrato["checks"]:
        cid = ch["id"]
        if cid == "C01":
            obs = total
        elif cid == "C08":
            obs = len(autores)
        elif cid == "C09":
            obs = c09
        elif cid == "C10":
            obs = c10
        elif cid == "C11":
            obs = {int(y): rec_filas.get(int(y), 0) for y in ch["esperado"]}
        elif cid == "C12":
            obs = {int(y): censo_por_ano.get(int(y), 0) for y in ch["esperado"]}
        else:  # C02..C07
            obs = per_ano.get(int(ch["ano"]), 0)

        ok, obs_norm = _comparar(ch["esperado"], obs)
        resultados.append({
            "id": cid,
            "nombre": ch["nombre"],
            "esperado": ch["esperado"],
            "observado": obs_norm,
            "ok": ok,
            "delta": _delta(ch["esperado"], obs_norm),
        })

    # ---- adicionales (A01): censo DEL ANO x produccion DEL ANO ----
    adicionales = []
    for ch in contrato.get("comprobaciones_adicionales", []):
        obs = {
            int(y): len(prod_set.get(int(y), set()) & censo_ids_por_ano.get(int(y), set()))
            for y in ch["esperado"]
        }
        ok, obs_norm = _comparar(ch["esperado"], obs)
        adicionales.append({
            "id": ch["id"],
            "nombre": ch["nombre"],
            "esperado": ch["esperado"],
            "observado": obs_norm,
            "ok": ok,
            "delta": _delta(ch["esperado"], obs_norm),
        })

    # ---- informativas (A01_global): censo GLOBAL x produccion DEL ANO ----
    # Se conserva solo para documentar la diferencia con A01. NO bloquea.
    informativas = []
    for ch in contrato.get("comprobaciones_informativas", []):
        obs = {y: len(prod_set.get(y, set()) & censo_ids) for y in sorted(anios_validos)}
        informativas.append({
            "id": ch["id"],
            "nombre": ch["nombre"],
            "informativa": True,
            "observado": obs,
            "ok": True,
        })

    # ---- estructurales (E01-E04) ----
    sha = _sha256(archivo)
    size = archivo.stat().st_size

    man = None
    if args.manifiesto:
        man = _manifiesto_para(None, args.manifiesto)
    else:
        man = _manifiesto_para(archivo)
    e05 = 0
    if man is not None:
        if man.get("sha256") != sha or int(man.get("bytes", -1)) != size:
            e05 = 1

    estructurales = [
        {"id": "E01", "nombre": "formato_id_persona_pd", "esperado": 0,
         "observado": bad, "ok": bad == 0},
        {"id": "E02", "nombre": "nulos_en_clave", "esperado": 0,
         "observado": nulos, "ok": nulos == 0},
        {"id": "E03", "nombre": "anio_indeterminable", "esperado": 0,
         "observado": anio_desc, "ok": anio_desc == 0},
        {"id": "E04", "nombre": "anio_inesperado", "esperado": 0,
         "observado": len(anios_extra), "ok": len(anios_extra) == 0},
        {"id": "E05", "nombre": "hash_vs_manifiesto", "esperado": 0,
         "observado": e05, "ok": e05 == 0},
    ]

    # ---- tabla en pantalla ----
    print("\nComprobaciones del contrato:")
    for r in resultados:
        marca = "OK  " if r["ok"] else "FALLA"
        print(f"  [{marca}] {r['id']} {r['nombre']:<34} "
              f"esperado={_fmt(r['esperado']):>28}  observado={_fmt(r['observado']):>28}")
    for r in adicionales:
        marca = "OK  " if r["ok"] else "FALLA"
        print(f"  [{marca}] {r['id']} {r['nombre']:<34} "
              f"esperado={_fmt(r['esperado']):>28}  observado={_fmt(r['observado']):>28}")
    for r in estructurales:
        marca = "OK  " if r["ok"] else "FALLA"
        print(f"  [{marca}] {r['id']} {r['nombre']:<34} "
              f"esperado={r['esperado']:>28}  observado={r['observado']:>28}")
    if informativas:
        print("\nInformativas (no bloquean):")
        for r in informativas:
            print(f"  [INFO] {r['id']} {r['nombre']:<22} "
                  f"observado={_fmt(r['observado']):>28}")

    fallos = [r for r in resultados + adicionales + estructurales if not r["ok"]]
    ok_total = not fallos
    total_bloqueantes = len(resultados) + len(adicionales) + len(estructurales)

    if anios_extra:
        print(f"\n   ANOS INESPERADOS: {anios_extra}")

    # ---- salida ----
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if ok_total:
        destino_json = MANIFEST_DIR / f"validacion_{ts}.json"
        payload = {
            "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "archivo": str(archivo),
            "bytes": size,
            "sha256": sha,
            "contrato": str(Path(args.contrato)),
            "contrato_version": contrato.get("version"),
            "censo": str(Path(args.censo)),
            "censo_ids": len(censo_ids),
            "manifiesto": str(man.get("archivo")) if man else None,
            "checks": resultados,
            "adicionales": adicionales,
            "informativas": informativas,
            "estructurales": estructurales,
            "resultado": "OK",
        }
        destino_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        print(f"\nRESULTADO: OK. {total_bloqueantes}/{total_bloqueantes} comprobaciones "
              f"bloqueantes pasan.")
        print(f"   informativas (no bloquean): {len(informativas)}")
        print(f"   validacion: {destino_json}")
        print(f"   sha256    : {sha}")
        print(f"   bytes     : {size:,}".replace(",", " "))
        return 0

    destino_json = MANIFEST_DIR / "diferencias.json"
    payload = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "archivo": str(archivo),
        "bytes": size,
        "sha256": sha,
        "contrato": str(Path(args.contrato)),
        "criterio_parada": contrato.get("criterio_parada"),
        "resultado": "FALLA",
        "fallos": fallos,
        "informativas": informativas,
        "resumen": f"{len(fallos)} de {total_bloqueantes} comprobaciones fallaron",
        "anios_extra": anios_extra,
    }
    destino_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(f"\nRESULTADO: FALLA. {len(fallos)} comprobacion(es) no coinciden.")
    print("   El pipeline se detiene: no se construyen features ni dataset de modelo.")
    print(f"   diferencias: {destino_json}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
