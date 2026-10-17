"""Detalle fino del lock: nombres duplicados, grupos y marcas.

Uso: python _archivo/scripts_oneoff/detalle_locks.py
"""

from __future__ import annotations

import collections
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LOCKS = {
    "auditado": RAIZ / "04_auditoria" / "repo_original" / "poetry.lock",
    "mejorado": RAIZ / "04_auditoria" / "repo_mejorado" / "poetry.lock",
}

for etiqueta, ruta in LOCKS.items():
    datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
    paquetes = datos.get("package", [])
    nombres = [p["name"] for p in paquetes]
    cuenta = collections.Counter(nombres)
    dup = {n: c for n, c in cuenta.items() if c > 1}

    print("=" * 72)
    print(f"{etiqueta.upper()}  ({ruta.name})")
    print("=" * 72)
    print(f"  bloques [[package]]      : {len(paquetes)}")
    print(f"  nombres unicos           : {len(set(nombres))}")
    print(f"  nombres duplicados       : {len(dup)}")
    for n, c in sorted(dup.items()):
        vers = [p["version"] for p in paquetes if p["name"] == n]
        extras = [
            (p.get("python-versions"), sorted(p.get("extras", [])), dict(p.get("dependencies", {})))
            for p in paquetes
            if p["name"] == n
        ]
        print(f"     {n:<20} x{c}  versiones={vers}")
        for e in extras:
            print(f"         python={e[0]}  extras={e[1]}  deps={list(e[2])}")
    metadatos = {k: v for k, v in datos.items() if k != "package"}
    print(f"  metadatos                : {metadatos}")
    print()
