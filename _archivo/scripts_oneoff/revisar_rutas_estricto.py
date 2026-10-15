"""Comprobacion ESTRICTA: cada ruta citada debe existir tal cual, sin permitir
que se salve porque exista un archivo con el mismo nombre en otra carpeta.

Uso: python _archivo/scripts_oneoff/revisar_rutas_estricto.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

texto = (RAIZ / "README.md").read_text(encoding="utf-8")

PATRON = re.compile(
    r"`([\w./\-]+\.(?:py|md|yaml|yml|csv|json|lock|toml|txt|ipynb|html|tex|pdf|npz|pkl|jsonl|xlsx|R))`"
)
rutas = sorted(set(PATRON.findall(texto)))

print(f"rutas con extension citadas entre backticks: {len(rutas)}\n")
malas = []
for r in rutas:
    ok = (RAIZ / r).exists()
    print(f"  {'OK ' if ok else 'NO '} {r}")
    if not ok:
        malas.append(r)

print()
# Tambien las rutas del arbol de estructura, que van sin backticks.
arbol = re.findall(r"[├└]── ([\w./\-]+\.(?:py|csv|md|yaml))", texto)
print(f"rutas citadas en el arbol: {len(arbol)}")
for r in sorted(set(arbol)):
    ok = (RAIZ / "datos_originales" / r).exists()
    print(f"  {'OK ' if ok else 'NO '} datos_originales/{r}")
    if not ok:
        malas.append(r)

print(f"\nRESUMEN: {len(malas)} ruta(s) que no existen tal cual")
for m in malas:
    print(f"  {m}")
sys.exit(1 if malas else 0)
