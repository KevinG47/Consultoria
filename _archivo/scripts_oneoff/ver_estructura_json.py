"""Muestra la ESTRUCTURA de un JSON: claves, tipos y tamanos, sin volcar el contenido.

Uso: python _archivo/scripts_oneoff/ver_estructura_json.py <ruta> [profundidad]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ruta = Path(sys.argv[1])
profundidad = int(sys.argv[2]) if len(sys.argv) > 2 else 3
datos = json.loads(ruta.read_text(encoding="utf-8"))


def describir(valor) -> str:
    if isinstance(valor, dict):
        return f"dict({len(valor)})"
    if isinstance(valor, list):
        if not valor:
            return "list(0) vacia"
        interno = type(valor[0]).__name__
        return f"list({len(valor)}) de {interno}"
    if isinstance(valor, str):
        return f"str({len(valor)})" if len(valor) > 60 else f"str = {valor!r}"
    return f"{type(valor).__name__} = {valor}"


def recorrer(valor, nivel: int, prefijo: str = "") -> None:
    sangria = "  " * nivel
    if isinstance(valor, dict):
        for clave, sub in valor.items():
            print(f"{sangria}{clave}: {describir(sub)}")
            if nivel < profundidad and isinstance(sub, (dict, list)):
                recorrer(sub, nivel + 1)
    elif isinstance(valor, list):
        print(f"{sangria}[0]: {describir(valor[0])}")
        if nivel < profundidad:
            if isinstance(valor[0], dict):
                print(f"{sangria}claves de cada elemento: {list(valor[0])}")
                for k, v in valor[0].items():
                    print(f"{sangria}  {k} = {v!r}"[:160])
            elif isinstance(valor[0], (list, dict)):
                recorrer(valor[0], nivel + 1)


print(f"=== {ruta.name} ===")
recorrer(datos, 0)
