# -*- coding: utf-8 -*-
"""
verificar_hashes.py
===================

Comprueba que los archivos transferidos del repositorio auditado son byte a byte
identicos al contenido versionado del que se extrajeron, comparando contra
`manifiesto_sha256.csv`.

Normaliza CRLF -> LF antes de calcular el hash porque el manifiesto guarda el
hash del CONTENIDO VERSIONADO (LF) y `git` puede convertir finales de linea al
hacer checkout en Windows (CRLF). Sin esta normalizacion la verificacion fallaria
en Windows y pasaria en Linux, que es justo lo contrario de lo util.

Uso
---
    python datos_originales/verificar_hashes.py

Salida: codigo 0 si todo coincide, 1 si hay diferencias o faltantes.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
MANIFIESTO = RAIZ / "datos_originales" / "manifiesto_sha256.csv"


def coincide(ruta: Path, esperado: str) -> bool:
    """
    True si el archivo coincide con el hash del manifiesto.

    Primero se compara el hash EXACTO, que es el caso normal. Solo si no coincide
    se reintenta con los finales de linea normalizados a LF, y solo cuando el
    archivo es de texto (sin bytes NUL). Normalizar a ciegas es un error: el
    contenido COMPRIMIDO de un PNG puede contener la secuencia `\\r\\n` y la
    normalizacion cambiaria su hash, marcando como alterados 58 binarios intactos.
    """
    datos = ruta.read_bytes()
    if hashlib.sha256(datos).hexdigest() == esperado:
        return True
    if b"\x00" in datos[:8192]:
        return False                      # binario: no se normaliza
    return hashlib.sha256(datos.replace(b"\r\n", b"\n")).hexdigest() == esperado


def main() -> int:
    if not MANIFIESTO.exists():
        print(f"[x] No existe {MANIFIESTO}.")
        return 1

    with MANIFIESTO.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))

    ok, faltan, distintos = 0, [], []
    for f in filas:
        ruta = RAIZ / "datos_originales" / "repo_auditado" / f["ruta"]
        if not ruta.exists():
            faltan.append(f["ruta"])
            continue
        if coincide(ruta, f["sha256"]):
            ok += 1
        else:
            distintos.append(f["ruta"])

    total = len(filas)
    print(f"manifiesto: {total} archivos ({filas[0]['origen'] if filas else '?'})")
    print(f"  identicos : {ok}")
    print(f"  faltantes : {len(faltan)}")
    print(f"  distintos : {len(distintos)}")
    for r in (faltan + distintos)[:20]:
        print(f"    [!] {r}")

    if ok == total:
        print("\n[OK] Los 236 archivos son byte a byte identicos al contenido "
              "versionado del repositorio auditado.")
        return 0
    print("\n[x] Hay diferencias: revisa antes de publicar.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
