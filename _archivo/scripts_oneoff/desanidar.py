# -*- coding: utf-8 -*-
"""
desanidar.py — corrige los directorios que quedaron dentro de sí mismos.

`git mv dir destino` con `destino` ya creado mete el directorio DENTRO del
destino. Este script deja cada cosa en su sitio:

    01_datos/datos_fuente/datos_fuente/*            -> 01_datos/datos_fuente/
    04_auditoria/repo_original/repo_auditado/*      -> 04_auditoria/repo_original/
    04_auditoria/repo_mejorado/repo_mejorado/*      -> 04_auditoria/repo_mejorado/
    05_entregas/ENTREGA_1/ENTREGA_1/*               -> 05_entregas/ENTREGA_1/
    05_entregas/entregables_2Corte/entregables_2Corte/* -> .../entregables_2Corte/
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "04_auditoria"))
import fs_robusto  # noqa: E402  (borrado tolerante a OneDrive)

PARES = [
    ("01_datos/datos_fuente/datos_fuente", "01_datos/datos_fuente"),
    ("04_auditoria/repo_original/repo_auditado", "04_auditoria/repo_original"),
    ("04_auditoria/repo_mejorado/repo_mejorado", "04_auditoria/repo_mejorado"),
    ("05_entregas/ENTREGA_1/ENTREGA_1", "05_entregas/ENTREGA_1"),
    ("05_entregas/entregables_2Corte/entregables_2Corte",
     "05_entregas/entregables_2Corte"),
]


def git(*args: str) -> None:
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"falló `git {' '.join(args)}`:\n{r.stderr}")


def versionado(rel: str) -> bool:
    r = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=RAIZ,
                       capture_output=True, text=True)
    return r.returncode == 0


def main() -> int:
    for interno, externo in PARES:
        dentro = RAIZ / interno
        fuera = RAIZ / externo
        if not dentro.exists():
            print(f"  [ok] {interno} ya no existe")
            continue
        print(f"  {interno}  ->  {externo}")
        for nombre in sorted(os.listdir(dentro)):
            origen = f"{interno}/{nombre}"
            destino = f"{externo}/{nombre}"
            if versionado(origen):
                git("mv", origen, destino)
            else:
                shutil.move(str(RAIZ / origen), str(RAIZ / destino))
        resto = sorted(p.name for p in dentro.iterdir())
        if resto:
            print(f"    [AVISO] quedan dentro: {resto}")
        else:
            fs_robusto.borrar_arbol(dentro)
            print(f"    carpeta interna vacía eliminada: {interno}")
    # el directorio viejo debió quedar vacío
    viejo = RAIZ / "datos_originales"
    if viejo.exists():
        sobra = sorted(p.name for p in viejo.iterdir())
        if sobra:
            print(f"  [AVISO] datos_originales/ todavía contiene: {sobra}")
        else:
            fs_robusto.borrar_arbol(viejo)
            print("  datos_originales/ eliminado (quedó vacío)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
