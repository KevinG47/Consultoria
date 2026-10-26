#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
descargar_produccion.py
=======================

Descarga paginada del dataset de Produccion de Grupos de MinCiencias
(Socrata 33dq-ab5a) a un CSV local, FUERA del repositorio y de OneDrive.

Por que existe
--------------
La evidencia del cruce censo x produccion que dejo el repositorio auditado
(04_auditoria/repo_original/evidencias/produccion_*) es agregada: no permite
construir features por persona. El dataset crudo nunca se versiono. Este
script lo descarga una vez, con hash y manifiesto, para que cualquier
resultado posterior sea reproducible.

Metodo (identico al del repositorio auditado, para que los conteos sean
comparables):

    GET https://www.datos.gov.co/resource/33dq-ab5a.csv
        ?$limit=50000&$offset=N&$order=:id

Garantias
---------
- Streaming a disco: nunca se acumulan las paginas en memoria.
- Checkpoint por offset (JSON junto al CSV): si se corta, se reanuda.
- Reintentos con backoff exponencial.
- SHA-256 calculado mientras se escribe y verificado al final.
- Manifiesto JSON con URL, fecha, bytes, filas, hash y paginas.
- El token (opcional) va por la variable de entorno SOCRATA_APP_TOKEN y
  NUNCA se escribe en el manifiesto.

Uso
---
    python 07_modelo/ingesta/descargar_produccion.py
    python 07_modelo/ingesta/descargar_produccion.py --reiniciar
    python 07_modelo/ingesta/descargar_produccion.py --salida "D:\\datos\\produccion_grupos.csv"
    python 07_modelo/ingesta/descargar_produccion.py --limit 5000   # prueba rapida

    # Con token (opcional, reduce limites de tasa):
    # PowerShell:  $env:SOCRATA_APP_TOKEN = "tu_token"
    # CMD:         set SOCRATA_APP_TOKEN=tu_token

Codigos de salida
-----------------
  0    descarga completa y hash verificado
  2    error de red no recuperable (checkpoint guardado; se puede reanudar)
  3    el hash final no coincide con el calculado durante la escritura
  4    error de configuracion (archivo existente sin checkpoint, etc.)
  130  interrumpido por el usuario (checkpoint guardado)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://www.datos.gov.co/resource/33dq-ab5a.csv"
PAGE_SIZE = 50_000
ORDER = ":id"
TIMEOUT = 300
UA = "consultoria-observatorio/1.0 (ingesta reproducible)"
TOKEN_ENV = "SOCRATA_APP_TOKEN"

SCRIPT_DIR = Path(__file__).resolve().parent
MANIFEST_DIR = SCRIPT_DIR / "manifiestos"
DEFAULT_ROOT = Path(r"C:\datos_externos\minciencias\33dq-ab5a")


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def _sha256_archivo(ruta: Path, bloque: int = 1 << 20) -> "hashlib._Hash":
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h


def _contar_filas(ruta: Path) -> int:
    """Cuenta registros CSV de una pagina (sin la cabecera)."""
    try:
        csv.field_size_limit(10 ** 7)
    except OverflowError:
        pass
    with open(ruta, "r", encoding="utf-8", errors="replace", newline="") as f:
        n = sum(1 for _ in csv.reader(f))
    return max(0, n - 1)


def _pagina_valida(ruta: Path) -> None:
    if not ruta.exists() or ruta.stat().st_size == 0:
        raise ValueError("respuesta vacia")
    with open(ruta, "rb") as f:
        inicio = f.read(128).lstrip()
    if inicio.startswith(b"<"):
        raise ValueError("la API devolvio HTML/JSON en vez de CSV")


def _descargar_pagina(offset: int, limite: int, token: str | None, tmp: Path) -> None:
    qs = urlencode({"$limit": int(limite), "$offset": int(offset), "$order": ORDER})
    req = Request(f"{API}?{qs}", headers={"User-Agent": UA, "Accept": "text/csv"})
    if token:
        req.add_header("X-App-Token", token)
    with urlopen(req, timeout=TIMEOUT) as resp, open(tmp, "wb") as f:
        while True:
            trozo = resp.read(1 << 20)
            if not trozo:
                break
            f.write(trozo)


def _descargar_con_reintentos(
    offset: int,
    limite: int,
    token: str | None,
    tmp: Path,
    max_reintentos: int,
) -> None:
    for intento in range(1, max_reintentos + 1):
        try:
            _descargar_pagina(offset, limite, token, tmp)
            _pagina_valida(tmp)
            return
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            if tmp.exists():
                tmp.unlink()
            if intento >= max_reintentos:
                raise RuntimeError(
                    f"fallo tras {max_reintentos} intentos en offset={offset}: {exc}"
                ) from exc
            espera = min(60.0, float(2 ** intento) + random.random())
            print(f"   [reintento {intento}/{max_reintentos}] offset={offset}: "
                  f"{exc}. Espero {espera:.1f}s")
            time.sleep(espera)


def _anexar(tmp: Path, salida, primera: bool, hasher) -> None:
    """Copia la pagina al CSV final, sin repetir la cabecera."""
    with open(tmp, "rb") as f:
        cabecera = f.readline()
        if primera:
            if cabecera.startswith(b"\xef\xbb\xbf"):
                cabecera = cabecera[3:]
            salida.write(cabecera)
            hasher.update(cabecera)
        for trozo in iter(lambda: f.read(1 << 20), b""):
            salida.write(trozo)
            hasher.update(trozo)


def _leer_checkpoint(ruta: Path) -> dict | None:
    if not ruta.exists():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _guardar_checkpoint(
    ruta: Path, destino: Path, offset: int, filas: int, paginas: int, page_size: int
) -> None:
    datos = {
        "destino": str(destino),
        "offset": offset,
        "filas": filas,
        "paginas": paginas,
        "bytes": destino.stat().st_size,
        "page_size": page_size,
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    tmp = ruta.with_name(ruta.name + ".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, ruta)


# ----------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Descarga paginada del dataset 33dq-ab5a (produccion) con hash y manifiesto."
    )
    ap.add_argument("--salida", default=None,
                    help="Ruta completa del CSV de salida. Por defecto: "
                         r"C:\datos_externos\minciencias\33dq-ab5a\<fecha>\produccion_grupos.csv")
    ap.add_argument("--page-size", type=int, default=PAGE_SIZE,
                    help=f"Filas por pagina (por defecto {PAGE_SIZE}).")
    ap.add_argument("--max-reintentos", type=int, default=8,
                    help="Intentos por pagina antes de abortar (por defecto 8).")
    ap.add_argument("--pausa", type=float, default=0.5,
                    help="Segundos de espera entre paginas (por defecto 0.5).")
    ap.add_argument("--limit", type=int, default=None,
                    help="Solo para pruebas: descarga como maximo N filas.")
    ap.add_argument("--reiniciar", action="store_true",
                    help="Borra el CSV y el checkpoint y empieza de cero.")
    args = ap.parse_args()

    token = os.environ.get(TOKEN_ENV) or None

    if args.salida:
        destino = Path(args.salida).expanduser().resolve()
    else:
        fecha = datetime.now().strftime("%Y-%m-%d")
        destino = DEFAULT_ROOT / fecha / "produccion_grupos.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    ckpt = destino.with_name("checkpoint.json")
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    if args.reiniciar:
        for p in (destino, ckpt):
            if p.exists():
                p.unlink()

    estado = _leer_checkpoint(ckpt)
    if estado and str(Path(estado.get("destino", "")).resolve()) != str(destino):
        estado = None
    if estado and not destino.exists():
        estado = None

    if not estado and destino.exists() and destino.stat().st_size > 0:
        print("ERROR: el archivo existe pero no hay checkpoint valido.")
        print("       Use --reiniciar para empezar de cero (borra el CSV).")
        return 4

    if estado:
        offset = int(estado["offset"])
        total = int(estado["filas"])
        paginas = int(estado["paginas"])
        with open(destino, "r+b") as f:
            f.truncate(int(estado["bytes"]))
        hasher = _sha256_archivo(destino)
        if destino.stat().st_size != int(estado["bytes"]):
            print("   checkpoint inconsistente: se reinicia desde cero")
            destino.write_bytes(b"")
            offset = total = paginas = 0
            hasher = hashlib.sha256()
    else:
        destino.write_bytes(b"")
        offset = total = paginas = 0
        hasher = hashlib.sha256()

    print("== Descarga de produccion (Socrata 33dq-ab5a) ==")
    print(f"   destino : {destino}")
    print(f"   reanuda : offset={offset} filas | paginas previas={paginas}")
    print(f"   token   : {'si' if token else 'no'}")

    salida = open(destino, "ab")
    tmp = destino.with_name(destino.name + ".pagina.tmp")
    page_size = max(1, int(args.page_size))

    try:
        while True:
            limite = page_size
            if args.limit is not None:
                restante = int(args.limit) - total
                if restante <= 0:
                    break
                limite = min(page_size, restante)

            _descargar_con_reintentos(
                offset, limite, token, tmp, max(1, int(args.max_reintentos))
            )
            n = _contar_filas(tmp)
            if n == 0:
                tmp.unlink(missing_ok=True)
                break

            _anexar(tmp, salida, primera=(paginas == 0), hasher=hasher)
            tmp.unlink(missing_ok=True)
            offset += n
            total += n
            paginas += 1
            salida.flush()
            _guardar_checkpoint(ckpt, destino, offset, total, paginas, page_size)

            mb = destino.stat().st_size / 1_000_000
            print(f"   pagina {paginas:3d} | offset {offset:9d} | filas {total:9d} | "
                  f"{mb:8.1f} MB")
            if n < limite:
                break
            time.sleep(max(0.0, float(args.pausa)))
    except RuntimeError as exc:
        salida.flush()
        _guardar_checkpoint(ckpt, destino, offset, total, paginas, page_size)
        print(f"\nERROR de red: {exc}")
        print("   Checkpoint guardado: vuelva a ejecutar el mismo comando para reanudar.")
        return 2
    except KeyboardInterrupt:
        salida.flush()
        _guardar_checkpoint(ckpt, destino, offset, total, paginas, page_size)
        print("\nInterrumpido por el usuario. Checkpoint guardado; se puede reanudar.")
        return 130
    finally:
        salida.close()

    if total == 0:
        print("\nERROR: no se descargo ninguna fila.")
        return 2

    hasher_final = _sha256_archivo(destino)
    if hasher_final.hexdigest() != hasher.hexdigest():
        print("\nERROR: el hash final no coincide con el calculado al escribir.")
        return 3

    bytes_total = destino.stat().st_size
    parcial = args.limit is not None
    manifiesto = {
        "dataset": "33dq-ab5a",
        "url": API,
        "metodo": f"API paginada ($limit={page_size}, $order={ORDER})",
        "fecha_descarga_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "archivo": str(destino),
        "bytes": bytes_total,
        "filas": total,
        "sha256": hasher_final.hexdigest(),
        "paginas": paginas,
        "page_size": page_size,
        "script": str(Path(__file__).resolve()),
        "script_sha256": _sha256_archivo(Path(__file__).resolve()).hexdigest(),
        "token_usado": bool(token),
        "descarga_parcial": parcial,
        "notas": ("Descarga completa; filas contadas con csv.reader (sin cabecera). "
                  "Hash verificado releyendo el archivo." if not parcial else
                  "Descarga PARCIAL de prueba (--limit); no usar para validar."),
    }
    nombre = f"produccion_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    ruta_man = MANIFEST_DIR / nombre
    ruta_man.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    print("\nDescarga completa.")
    print(f"   archivo   : {destino}")
    print(f"   filas     : {total:,}".replace(",", " "))
    print(f"   bytes     : {bytes_total:,}".replace(",", " "))
    print(f"   sha256    : {hasher_final.hexdigest()}")
    print(f"   manifiesto: {ruta_man}")
    if parcial:
        print("   AVISO: descarga parcial de prueba (--limit); no sirve para validar.")
    else:
        print("\nSiguiente paso:")
        print("   python 07_modelo/ingesta/validar_produccion.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
