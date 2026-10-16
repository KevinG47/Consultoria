"""Resume objetivos.yaml: los 6 criterios de la auditoria."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

datos = yaml.safe_load(Path("documentacion_auditoria/data/objetivos.yaml").read_text(
    encoding="utf-8"))

print(f"claves de nivel superior: {list(datos)}")


def recorrer(nodo, nivel=0):
    sangria = "  " * nivel
    if isinstance(nodo, dict):
        for k, v in nodo.items():
            if isinstance(v, (dict, list)):
                print(f"{sangria}{k}: {type(v).__name__}({len(v)})")
                if nivel < 2:
                    recorrer(v, nivel + 1)
            else:
                texto = str(v)
                texto = texto[:150] + ("..." if len(texto) > 150 else "")
                print(f"{sangria}{k}: {texto}")
    elif isinstance(nodo, list):
        for i, v in enumerate(nodo[:6]):
            if isinstance(v, (dict, list)):
                print(f"{sangria}[{i}]:")
                recorrer(v, nivel + 1)
            else:
                print(f"{sangria}[{i}] {str(v)[:150]}")
        if len(nodo) > 6:
            print(f"{sangria}... y {len(nodo) - 6} mas")


recorrer(datos)
