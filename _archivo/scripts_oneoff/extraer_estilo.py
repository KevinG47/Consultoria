"""Extrae el bloque <style> y las declaraciones de tipografia del dashboard de
referencia, para poder copiar el estilo sin volcar 2,5 MB de HTML.

Uso: python _archivo/scripts_oneoff/extraer_estilo.py <html> [n_caracteres]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ruta = Path(sys.argv[1])
limite = int(sys.argv[2]) if len(sys.argv) > 2 else 6000
texto = ruta.read_text(encoding="utf-8", errors="replace")

print(f"=== {ruta.name}: {len(texto):,} caracteres ===")

# Bloque <style>
estilos = re.findall(r"(?s)<style[^>]*>(.*?)</style>", texto)
print(f"\nbloques <style>: {len(estilos)}")
for i, bloque in enumerate(estilos):
    print(f"\n--- bloque {i} ({len(bloque)} caracteres) ---")
    print(bloque[:limite])

# Declaraciones de font-family
fuentes = re.findall(r"font-family\s*:\s*([^;}\n]+)", texto)
print(f"\n=== font-family declaradas ({len(fuentes)}) ===")
for f in sorted(set(f.split("#")[0].strip() for f in fuentes))[:12]:
    print(f"  {f}")

# Variables CSS
raiz = re.search(r"(?s):root\s*\{(.*?)\}", texto)
if raiz:
    print("\n=== variables :root ===")
    for linea in raiz.group(1).splitlines():
        if linea.strip():
            print(f"  {linea.strip()}")

# Fuentes embebidas (base64) o enlaces externos
print("\n=== recursos externos o embebidos ===")
for pat in (r"@font-face", r"fonts\.googleapis", r"https?://", r"data:font",
            r"<link[^>]*>"):
    print(f"  {pat:20} {len(re.findall(pat, texto))}")
