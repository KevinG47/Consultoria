"""Verifica que el dashboard use UNA sola paleta institucional.

Analiza el HTML EXCLUYENDO el bundle de Plotly (que trae sus propios colores por
defecto y no se usa) y comprueba:
  1. Que no quede ningun color prohibido (verde, purpura, teal, ambar) en los
     graficos.
  2. Que el rojo aparezca SOLO donde marca una excepcion (y en cuantos graficos).
  3. Que los colores de la paleta institucional esten efectivamente presentes.
  4. Que los 17 graficos + 4 secciones lleven narrativa.

Uso: python _archivo/scripts_oneoff/verificar_paleta.py [html]
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUTA = Path(sys.argv[1] if len(sys.argv) > 1 else
            "02_dashboards/dashboard_eda.html")
html = RUTA.read_text(encoding="utf-8", errors="replace")

# Separar el bundle de Plotly: dentro de el hay miles de colores por defecto que
# no se usan y que producirian falsos positivos.
# Se identifica como el bloque <script> MAS GRANDE (el unico de megas) en lugar
# de buscar una cadena concreta, que puede cambiar entre versiones de Plotly.
bloques = [(m.start(1), m.end(1)) for m in
           re.finditer(r"(?s)<script>(.*?)</script>", html)]
if bloques:
    ini_b, fin_b = max(bloques, key=lambda t: t[1] - t[0])
    cuerpo = html[:ini_b] + html[fin_b:]
    print(f"bundle de Plotly excluido: {fin_b - ini_b:,} caracteres "
          f"(de {len(html):,})\n")
else:
    cuerpo = html
    print("AVISO: no se localizaron bloques <script>; se analiza todo\n")

PALETA = {
    "primario": "#1E3780", "primario_oscuro": "#0F1F4D", "secundario": "#4A6BA8",
    "claro": "#7BA7D0", "dorado": "#B7871E", "dorado_claro": "#D4A84A",
    "gris_oscuro": "#334155", "gris_medio": "#64748B", "gris_claro": "#CBD5E1",
}
PROHIBIDOS = {"verde": "#15803D", "morado": "#7C3AED", "teal": "#0E7490",
              "ambar": "#B45309", "rojo anterior": "#B91C1C",
              "escala anterior 1": "#FDEEEC", "escala anterior 2": "#FFF1D6",
              "escala anterior 3": "#DCE9F8"}
ALERTA = "#B91C1C"
fallos = []

print("=== 1. colores PROHIBIDOS en el documento (fuera del bundle) ===")
for nombre, color in PROHIBIDOS.items():
    n = len(re.findall(re.escape(color), cuerpo, re.I))
    # El rojo #B91C1C se reutiliza a proposito como color de ALERTA.
    if color == ALERTA:
        continue
    print(f"  {'OK ' if n == 0 else 'NO '} {nombre:20} {color}  apariciones: {n}")
    if n:
        fallos.append(f"color prohibido {nombre} ({color}) aparece {n} vez(ces)")

print("\n=== 2. color de ALERTA: solo en excepciones ===")
# Las posiciones se toman del propio regex, no con `find` de una cadena exacta:
# `find` fallaba si Plotly emitia un espacio tras el parentesis, dejaba la
# rebanada vacia y la comprobacion pasaba en falso sin avisar de nada.
marcas = [(m.group(1), m.start()) for m in
          re.finditer(r'Plotly\.newPlot\(\s*"([a-z0-9]+)"', cuerpo)]
zonas = [ident for ident, _ in marcas]
print(f"  graficos detectados: {len(zonas)} -> {zonas}")
con_alerta = []
for i, (ident, ini) in enumerate(marcas):
    fin = marcas[i + 1][1] if i + 1 < len(marcas) else len(cuerpo)
    n = len(re.findall(re.escape(ALERTA), cuerpo[ini:fin], re.I))
    if n:
        con_alerta.append(f"{ident}({n})")
    if fin - ini < 100:
        fallos.append(f"la rebanada de {ident} queda vacia: la comprobacion no es fiable")
print(f"  graficos con el color de alerta: {con_alerta}")
permitidos = {"u6", "d1", "d4"}
fuera = [c.split("(")[0] for c in con_alerta if c.split("(")[0] not in permitidos]
if fuera:
    fallos.append(f"el color de alerta aparece en graficos no previstos: {fuera}")
    print(f"  *** NO PERMITIDO: {fuera} (solo se admite en {sorted(permitidos)})")
elif len(con_alerta) != len(permitidos):
    fallos.append(f"solo {len(con_alerta)} graficos usan el color de alerta; "
                  f"se esperaban {len(permitidos)}")
    print(f"  *** se esperaban {sorted(permitidos)}, hay {con_alerta}")
else:
    print(f"  OK: solo en {sorted(permitidos)} (nota de atipicos, cola >100, umbrales)")

print("\n=== 3. paleta institucional presente ===")
for nombre, color in PALETA.items():
    n = len(re.findall(re.escape(color), cuerpo, re.I))
    print(f"  {'OK ' if n else '-- '} {nombre:16} {color}  apariciones: {n}")
    if n == 0:
        fallos.append(f"el color {nombre} ({color}) no aparece en el documento")

print("\n=== 4. narrativa ===")
bloques = len(re.findall(r'class="nar"', cuerpo))
secciones = len(re.findall(r'class="seccion"', cuerpo))
etiquetas = Counter(re.findall(r'<span class="et">([^<]+)</span>', cuerpo))
# 17 narrativas de grafico + 4 de seccion = 21 bloques con las mismas 3 etiquetas.
print(f"  bloques de narrativa: {bloques} (17 de grafico + 4 de seccion = 21)")
print(f"  narrativas de seccion: {secciones} (esperado 4)")
print(f"  etiquetas usadas     : {dict(etiquetas)}")
if bloques != 21:
    fallos.append(f"hay {bloques} narrativas, se esperaban 21 (17 + 4)")
if secciones != 4:
    fallos.append(f"hay {secciones} narrativas de seccion, se esperaban 4")
for esperada in ("Qué se hizo", "Por qué", "Cómo se lee"):
    if etiquetas.get(esperada, 0) != 21:
        fallos.append(f"«{esperada}» aparece {etiquetas.get(esperada, 0)} veces, "
                      f"se esperaban 21")

print("\n=== 5. axis/template: sin la paleta por defecto de Plotly ===")
# El template institucional debe aparecer en el layout de cada figura.
d3 = len(re.findall(r"D3D3D3|636efa|EF553B|00cc96|ab63fa", cuerpo))
print(f"  colores por defecto de Plotly en las figuras: {d3}")
if d3:
    fallos.append(f"quedan {d3} referencias a la paleta por defecto de Plotly")

print("\n" + "=" * 70)
if fallos:
    print(f"{len(fallos)} PROBLEMA(S):")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("El dashboard usa una sola paleta institucional y toda la narrativa.")
