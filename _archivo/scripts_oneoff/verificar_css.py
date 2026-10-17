"""Comprueba que toda variable CSS usada en el dashboard este definida.

Una `var(--x)` sin definir no da error: el navegador simplemente ignora la
propiedad, y el panel se ve distinto sin que nadie se entere. Se compara lo usado
contra lo declarado en `:root`.

Uso: python _archivo/scripts_oneoff/verificar_css.py [html]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUTA = Path(sys.argv[1] if len(sys.argv) > 1 else
            "02_dashboards/dashboard_eda.html")
html = RUTA.read_text(encoding="utf-8", errors="replace")

estilo = re.search(r"(?s)<style>(.*?)</style>", html)
if not estilo:
    print("no se encontro el bloque <style>")
    sys.exit(1)
css = estilo.group(1)

raiz = re.search(r"(?s):root\s*\{(.*?)\}", css)
definidas = set(re.findall(r"(--[\w-]+)\s*:", raiz.group(1))) if raiz else set()
usadas = set(re.findall(r"var\((--[\w-]+)", css))

print(f"variables definidas en :root: {len(definidas)}")
for d in sorted(definidas):
    print(f"  {d}")
print(f"\nvariables usadas con var(): {len(usadas)}")
faltan = sorted(usadas - definidas)
sin_usar = sorted(definidas - usadas)

if faltan:
    print(f"\n*** {len(faltan)} variables USADAS y NO DEFINIDAS:")
    for f in faltan:
        print(f"    {f}  (el navegador ignoraria esa propiedad en silencio)")
else:
    print("\nOK: todas las variables usadas estan definidas")

if sin_usar:
    print(f"\nDefinidas y no usadas ({len(sin_usar)}): {', '.join(sin_usar)}")

# Colores en crudo dentro del CSS: se admiten, pero conviene saber cuantos hay.
crudos = re.findall(r"#[0-9A-Fa-f]{6}", css)
print(f"\ncolores en crudo en el CSS: {len(crudos)} -> {sorted(set(crudos))}")

print("\n" + "=" * 60)
print("CSS consistente" if not faltan else f"{len(faltan)} variable(s) sin definir")
sys.exit(1 if faltan else 0)
