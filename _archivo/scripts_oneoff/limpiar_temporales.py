"""Borra los temporales de la fase de versiones, tolerando OneDrive.

Uso: python _archivo/scripts_oneoff/limpiar_temporales.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "datos_originales"))
from fs_robusto import borrar_arbol  # noqa: E402

DIRECTORIOS = [
    "_archivo/tmp_poetry_mej",
    "_archivo/tmp_poetry_cache",
    "_archivo/tmp_virtualenv_appdata",
    "_archivo/tmp_poetry_aud",
    "_archivo/wheelhouse",
    "datos_originales/_stubs",
    "datos_originales/_prueba_inventario",
    "datos_originales/_prueba_ejecucion",
]

ARCHIVOS = [
    "_archivo/scripts_oneoff/construir_wheelhouse.py",
    "_archivo/scripts_oneoff/ruedas_cache.json",
    "_archivo/scripts_oneoff/salida_ruedas_utiles.txt",
    "_archivo/scripts_oneoff/salida_wheelhouse.txt",
]

for rel in DIRECTORIOS:
    objetivo = RAIZ / rel
    if not objetivo.exists():
        print(f"  (no existe) {rel}")
        continue
    antes = sum(1 for _ in objetivo.rglob("*"))
    borrar_arbol(objetivo)
    queda = objetivo.exists()
    print(f"  {'[parcial]' if queda else '[borrado]'} {rel}  ({antes} entradas)")

for rel in ARCHIVOS:
    objetivo = RAIZ / rel
    if objetivo.exists():
        objetivo.unlink()
        print(f"  [borrado] {rel}")

print("\nQuedan a proposito:")
for rel in ("_archivo/deps_extra", "_archivo/scripts_oneoff"):
    objetivo = RAIZ / rel
    if objetivo.exists():
        mb = sum(p.stat().st_size for p in objetivo.rglob("*") if p.is_file()) / 1e6
        print(f"  {rel}  ({mb:.1f} MB)")
