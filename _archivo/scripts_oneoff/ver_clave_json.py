"""Vuelca un subarbol de un JSON, dado un camino de claves.

Uso:
    python _archivo/scripts_oneoff/ver_clave_json.py <archivo.json> clave1 clave2 ...
    python _archivo/scripts_oneoff/ver_clave_json.py <archivo.json> --claves clave1
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ruta = Path(sys.argv[1])
datos = json.loads(ruta.read_text(encoding="utf-8"))

if len(sys.argv) > 2 and sys.argv[2] == "--claves":
    nodo = datos
    for parte in sys.argv[3:]:
        nodo = nodo[parte]
    print(f"claves de {'.'.join(sys.argv[3:])}: {list(nodo)}")
    sys.exit(0)

nodo = datos
camino = []
for parte in sys.argv[2:]:
    camino.append(parte)
    try:
        nodo = nodo[parte]
    except (KeyError, TypeError, IndexError):
        print(f"no existe la clave {parte!r} en {'.'.join(camino[:-1]) or '(raiz)'}")
        print(f"claves disponibles: {list(nodo) if isinstance(nodo, dict) else type(nodo).__name__}")
        sys.exit(1)

print(f"=== {ruta.name} :: {'.'.join(camino)} ===")
texto = json.dumps(nodo, indent=2, ensure_ascii=False)
limite = 2500
print(texto[:limite] + ("\n... (truncado)" if len(texto) > limite else ""))
