"""Resume un JSON indicando, por cada clave, tipo, longitud y rango numerico.

Sirve para saber si un bloque trae ARRAYS por observacion (necesarios para un
grafico de residuos, Q-Q, Cook...) o solo estadisticos resumidos.

Uso: python _archivo/scripts_oneoff/resumir_arrays.py <archivo.json> [prefijo...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ruta = Path(sys.argv[1])
datos = json.loads(ruta.read_text(encoding="utf-8"))
prefijo = list(sys.argv[2:])


def resumir(nombre: str, valor, nivel: int) -> None:
    sangria = "  " * nivel
    if isinstance(valor, list):
        if not valor:
            print(f"{sangria}{nombre}: list(0)")
            return
        if all(isinstance(x, (int, float)) for x in valor):
            print(f"{sangria}{nombre}: list({len(valor)}) numerico  "
                  f"min={min(valor):.4f} max={max(valor):.4f}")
        else:
            print(f"{sangria}{nombre}: list({len(valor)}) de {type(valor[0]).__name__}")
            if isinstance(valor[0], dict):
                print(f"{sangria}  claves: {list(valor[0])}")
    elif isinstance(valor, dict):
        print(f"{sangria}{nombre}: dict({len(valor)})")
        if nivel < 2:
            for k, v in valor.items():
                resumir(k, v, nivel + 1)
    elif isinstance(valor, str):
        print(f"{sangria}{nombre}: str({len(valor)})")
    else:
        print(f"{sangria}{nombre}: {type(valor).__name__} = {valor}")


nodo = datos
for p in prefijo:
    nodo = nodo[p]

print(f"=== {ruta.name}{' :: ' + '.'.join(prefijo) if prefijo else ''} ===")
if isinstance(nodo, dict):
    for k, v in nodo.items():
        resumir(k, v, 0)
else:
    resumir("(raiz)", nodo, 0)
