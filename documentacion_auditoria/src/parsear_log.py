# -*- coding: utf-8 -*-
"""
parsear_log.py
==============

Tabla de resultados (EXIT, tiempo, estado) de la ejecución del pipeline del
repositorio auditado: los 16 scripts `sprint*` corridos en clon fresco.

DÓNDE ESTÁ EL LOG Y POR QUÉ ESTABA ROTO
---------------------------------------
La versión anterior apuntaba por defecto a
`.\documentacion_auditoria\data\ejecucion_log.txt`, una ruta **relativa al
directorio de trabajo** que no existe (comprobado: `Test-Path` = False), así que
el script no encontraba nada al ejecutarlo como está documentado. El log real
vive en `_archivo/logs_pipeline_auditado/ejecucion_log.txt` y ahora se resuelve
con `Path(__file__)`, igual que el resto de scripts del proyecto: funciona desde
cualquier directorio de trabajo.

TRAMPA DEL FORMATO (la razón del heurístico de codificación)
------------------------------------------------------------
El archivo tiene codificación MIXTA: la cabecera está en UTF-8 y los cuerpos de
los scripts en UTF-16LE (el volcado de consola de PowerShell se anexó con otra
codificación). Leído como UTF-8, las líneas `EXIT=` no aparecen en absoluto; solo
se recuperan al decodificar como UTF-16LE. Por eso se decodifica de las dos
formas y se elige la que encuentra más marcadores `EXIT=`. Sin este paso el
script informa «no se encontraron resultados» sobre un log que sí los tiene.

La tabla también está curada en `data/ejecucion_resumen.csv`; con `--cotejar` se
comparan las dos fuentes (que coinciden en los 16 scripts).

Uso
---
    python documentacion_auditoria/src/parsear_log.py
    python documentacion_auditoria/src/parsear_log.py --cotejar
    python documentacion_auditoria/src/parsear_log.py --log otra/ruta.log
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
LOG_POR_DEFECTO = RAIZ / "_archivo" / "logs_pipeline_auditado" / "ejecucion_log.txt"
RESUMEN_CSV = RAIZ / "documentacion_auditoria" / "data" / "ejecucion_resumen.csv"

PATRON = re.compile(
    r"=== (sprint\w+\.py) ===(.*?)EXIT=(-?\d+) TIEMPO=([\d.]+)s", re.S)


def leer_texto(ruta: Path) -> str:
    """Decodifica el log tolerando su codificación mixta UTF-8 / UTF-16LE."""
    b = ruta.read_bytes()
    t8 = b.decode("utf-8", errors="replace")
    t16 = b.decode("utf-16-le", errors="replace")
    return t16 if t16.count("EXIT=") > t8.count("EXIT=") else t8


def parsear(ruta: Path) -> list[dict]:
    txt = leer_texto(ruta)
    filas = []
    for nombre, cuerpo, exit_, tiempo in PATRON.findall(txt):
        err = "ERROR" in cuerpo.upper() or "Traceback" in cuerpo
        filas.append({
            "script": nombre,
            "exit": int(exit_),
            "tiempo_s": float(tiempo),
            "estado": "ERROR" if (err or int(exit_) != 0) else "OK",
        })
    return filas


def cotejar_con_csv(filas: list[dict]) -> int:
    """Compara contra data/ejecucion_resumen.csv (segunda fuente independiente)."""
    if not RESUMEN_CSV.exists():
        print(f"\n[aviso] no existe {RESUMEN_CSV.relative_to(RAIZ)}; no se coteja.")
        return 0
    import csv as _csv
    # utf-8-sig: el CSV lleva BOM y sin quitarlo la primera clave sería
    # '\ufeff"script"' (KeyError en la línea siguiente).
    with RESUMEN_CSV.open(encoding="utf-8-sig", newline="") as fh:
        resumen = {r["script"]: r for r in _csv.DictReader(fh)}
    discrepan = []
    for f in filas:
        r = resumen.get(f["script"])
        if r is None:
            discrepan.append(f"{f['script']}: no está en el CSV")
            continue
        if int(r["exit"]) != f["exit"]:
            discrepan.append(f"{f['script']}: log EXIT={f['exit']} vs CSV {r['exit']}")
    print(f"\n[cotejo] {len(filas)} scripts del log contra "
          f"{len(resumen)} del CSV: "
          + ("sin discrepancias." if not discrepan else f"{len(discrepan)} discrepancia(s)"))
    for d in discrepan:
        print(f"    [!] {d}")
    return 1 if discrepan else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Tabla de resultados del pipeline auditado.")
    ap.add_argument("--log", default=str(LOG_POR_DEFECTO),
                    help="ruta del log de ejecución (por defecto, el de _archivo/)")
    ap.add_argument("--cotejar", action="store_true",
                    help="compara contra data/ejecucion_resumen.csv")
    args = ap.parse_args()

    ruta = Path(args.log)
    if not ruta.exists():
        print(f"[x] No existe el log: {ruta}")
        print(f"    El log vive en {LOG_POR_DEFECTO.relative_to(RAIZ)}; "
              f"usa --log para indicar otra ruta.")
        return 1

    filas = parsear(ruta)
    if not filas:
        print(f"[x] El log {ruta.name} no contiene marcadores 'EXIT=... TIEMPO=...s'.")
        print("    Comprueba que no esté truncado o en otro formato.")
        return 1

    print(f"log: {ruta.relative_to(RAIZ) if ruta.is_relative_to(RAIZ) else ruta}")
    print(f"{'SCRIPT':36s} {'EXIT':>4} {'TIEMPO':>8}  ESTADO")
    for f in filas:
        print(f"{f['script']:36s} {f['exit']:>4} {f['tiempo_s']:>7}s  {f['estado']}")
    ok = sum(1 for f in filas if f["estado"] == "OK")
    print(f"\n{ok} OK / {len(filas) - ok} ERROR de {len(filas)} scripts")

    return cotejar_con_csv(filas) if args.cotejar else 0


if __name__ == "__main__":
    raise SystemExit(main())
