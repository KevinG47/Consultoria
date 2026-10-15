"""Comprueba que el dashboard es autocontenido: nada que el navegador tenga que
descargar. Se analiza el HTML EXCLUYENDO el bundle de Plotly, porque dentro de
plotly.min.js hay cadenas con URL (licencias, esquemas) que no son peticiones.

Uso: python _archivo/scripts_oneoff/verificar_autocontenido.py <html>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ruta = Path(sys.argv[1])
texto = ruta.read_text(encoding="utf-8", errors="replace")
print(f"archivo: {ruta.name}  ({len(texto):,} caracteres, {ruta.stat().st_size:,} B)")

# 1. Separar el bundle de Plotly del resto del documento.
marcas = [m for m in re.finditer(r"<script[^>]*>(.*?)</script>", texto, re.S)]
print(f"\nbloques <script>: {len(marcas)}")
bundle = None
for m in marcas:
    if "Plotly.version" in m.group(1) or "plotly.js" in m.group(1)[:2000]:
        bundle = m
        print(f"  bundle de Plotly: {len(m.group(1)):,} caracteres "
              f"(posicion {m.start():,}..{m.end():,})")
if bundle is None:
    print("  NO se encontro el bundle de Plotly embebido  <-- problema")
    sys.exit(1)

resto = texto[:bundle.start()] + texto[bundle.end():]
print(f"resto del documento: {len(resto):,} caracteres")

# 2. En el RESTO no puede haber nada que se descargue.
print("\n=== en el resto del documento (debe ser 0) ===")
patrones = {
    "<script src": r"<script[^>]+src\s*=",
    "<link>": r"<link[^>]*>",
    "@import": r"@import",
    "url(...)": r"url\(\s*['\"]?https?:",
    "http(s)://": r"https?://",
    "//cdn": r"//cdn",
    "fetch(": r"\bfetch\s*\(",
    "XMLHttpRequest": r"XMLHttpRequest",
    "<img src": r"<img[^>]+src\s*=",
    "<iframe": r"<iframe",
}
fallos = 0
for nombre, patron in patrones.items():
    encontrados = re.findall(patron, resto, re.I)
    marca = "OK" if not encontrados else "*** PROBLEMA ***"
    if encontrados:
        fallos += 1
    print(f"  {nombre:16} {len(encontrados):>3}   {marca}")
    for e in encontrados[:3]:
        print(f"      -> {e[:120]}")

# 3. Estructura de pestanas y graficos.
print("\n=== estructura ===")
botones = re.findall(r'class="tab-btn[^"]*"\s+data-tab="([^"]+)"', resto)
paneles = re.findall(r'class="panel[^"]*"\s+id="([^"]+)"', resto)
grafos = re.findall(r'class="plotly-graph-div"', resto)
newplot = re.findall(r'Plotly\.newPlot\(\s*"([^"]+)"', resto)
print(f"  botones data-tab : {botones}")
print(f"  paneles id       : {paneles}")
print(f"  emparejados      : {set(botones) == set(paneles)}")
print(f"  divs plotly-graph-div: {len(grafos)}")
print(f"  Plotly.newPlot   : {len(newplot)} -> {newplot}")

# Cada grafico debe estar DENTRO del panel de su pestana: si un div quedara fuera,
# el grafico se veria siempre, en todas las pestanas.
print("\n=== pertenencia de cada grafico a su pestana ===")
rangos = sorted(((pid, resto.find('id="' + pid + '"')) for pid in paneles),
                key=lambda t: t[1])
for i, (pid, inicio) in enumerate(rangos):
    fin = rangos[i + 1][1] if i + 1 < len(rangos) else len(resto)
    dentro = [n for n in newplot if inicio < resto.find('id="' + n + '"') < fin]
    print(f"  {pid:16} {len(dentro):>2} graficos: {dentro}")
total_dentro = sum(
    1 for n in newplot
    if any(rangos[i][1] < resto.find('id="' + n + '"') <
           (rangos[i + 1][1] if i + 1 < len(rangos) else len(resto))
           for i in range(len(rangos))))
print(f"  graficos dentro de algun panel: {total_dentro} de {len(newplot)}  "
      f"{'OK' if total_dentro == len(newplot) else '*** HAY GRAFICOS FUERA ***'}")

# 4. Los graficos llevan datos (JSON embebido, no una imagen).
print("\n=== carga de datos por grafico ===")
for n in newplot:
    m = re.search(r'Plotly\.newPlot\(\s*"' + re.escape(n) + r'",\s*(\[.*?\])\s*,\s*\{',
                  resto, re.S)
    tam = len(m.group(1)) if m else 0
    print(f"  {n:4} datos: {tam:,} caracteres de JSON")

# 5. Comillas y cierre del HTML.
print("\n=== integridad del documento ===")
print(f"  empieza por <!DOCTYPE html>: {texto.lstrip().startswith('<!DOCTYPE html>')}")
print(f"  termina por </html>       : {texto.rstrip().endswith('</html>')}")
print(f"  <style> abiertos/cerrados : {texto.count('<style')} / {texto.count('</style>')}")
print(f"  <script> abiertos/cerrados: {texto.count('<script')} / {texto.count('</script>')}")

print(f"\nRESUMEN: {'AUTOCONTENIDO' if fallos == 0 else str(fallos) + ' PROBLEMA(S)'}")
sys.exit(1 if fallos else 0)
