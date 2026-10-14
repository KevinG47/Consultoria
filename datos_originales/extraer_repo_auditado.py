# -*- coding: utf-8 -*-
"""
extraer_repo_auditado.py
========================

Copia VERBATIM el contenido del repositorio auditado a `datos_originales/`,
para que este repositorio sea autocontenido y el proximo grupo no necesite
clonar el original.

POR QUE SE EXTRAE DESDE GIT Y NO DESDE EL DISCO
-----------------------------------------------
El working tree del clon esta SUCIO: las ejecuciones de la propia auditoria
sobrescribieron 38 archivos rastreados (20 PNG de `artifacts/`, 3 HTML y 15 de
`evidencias/`, entre ellos `calidad_resumen.json` y `calidad_atipicos_edad.csv`).
Copiar del disco transferiria evidencia FALSIFICADA: el disco dice
`n_atipicos_edad = 19` (calculado sobre el XLSX parcial de 50 891 filas) mientras
el commit dice 22 (sobre las 77 237 declaradas). Por eso cada archivo se extrae
con `git show HEAD:<ruta>`, que devuelve el blob tal como esta versionado.

Los hashes del manifiesto son, por tanto, hashes del CONTENIDO VERSIONADO
(finales de linea LF), no de los archivos del working tree en Windows (CRLF).
`verificar_hashes.py` normaliza CRLF -> LF antes de comparar, para que la
verificacion funcione en cualquier plataforma.

Uso
---
    python datos_originales/extraer_repo_auditado.py            # extrae
    python datos_originales/extraer_repo_auditado.py --dry-run  # solo informa

Requiere el clon local en `Observatorio_Ministerio_de_Ciencias_Grupo8/`.
Sin el clon no hace falta ejecutarlo: el contenido ya esta en el repositorio.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
CLON = RAIZ / "Observatorio_Ministerio_de_Ciencias_Grupo8"
DESTINO = RAIZ / "datos_originales" / "repo_auditado"
MANIFIESTO = RAIZ / "datos_originales" / "manifiesto_sha256.csv"


def _git(*args: str) -> bytes:
    r = subprocess.run(["git", "-C", str(CLON), *args],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} fallo: "
                           f"{r.stderr.decode('utf-8', 'replace')[:300]}")
    return r.stdout


def archivos_rastreados() -> list[str]:
    return [l.strip() for l in _git("ls-files", "-z").decode("utf-8").split("\0")
            if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[3])
    ap.add_argument("--dry-run", action="store_true",
                    help="informa sin escribir nada")
    args = ap.parse_args()

    if not CLON.exists():
        print(f"[x] No existe el clon en {CLON}.")
        print("    El contenido ya esta en el repositorio: no hace falta extraerlo.")
        return 1

    head = _git("rev-parse", "--short", "HEAD").decode().strip()
    rutas = archivos_rastreados()
    print(f"clon: {CLON.name}  HEAD={head}  archivos rastreados={len(rutas)}")

    filas = []
    escritos = 0
    for rel in rutas:
        blob = _git("show", f"HEAD:{rel}")
        sha = hashlib.sha256(blob).hexdigest()
        filas.append({"ruta": rel.replace("\\", "/"), "sha256": sha,
                      "bytes": len(blob), "origen": f"repo_auditado@{head}"})
        if not args.dry_run:
            destino = DESTINO / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(blob)
            escritos += 1

    total = sum(f["bytes"] for f in filas)
    print(f"  {len(filas)} archivos, {total / 1e6:.2f} MB de contenido versionado")
    if args.dry_run:
        print("  [dry-run] no se escribio nada")
        return 0

    with MANIFIESTO.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["ruta", "sha256", "bytes", "origen"])
        w.writeheader()
        w.writerows(filas)
    print(f"  -> {escritos} archivos en {DESTINO.relative_to(RAIZ)}")
    print(f"  -> {MANIFIESTO.relative_to(RAIZ)} ({len(filas)} entradas)")
    print("\nVerifica con:  python datos_originales/verificar_hashes.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
