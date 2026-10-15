"""Comprueba que las cifras DENTRO del dashboard coincidan con los JSON fuente.

No basta con que el HTML exista: hay que verificar que lo que muestra son los
numeros de los JSON y no otros. Se buscan los valores clave en el texto del HTML.

Uso: python _archivo/scripts_oneoff/verificar_cifras_dashboard.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"
html = (MEM / "dashboard_eda.html").read_text(encoding="utf-8", errors="replace")

eda = json.loads((MEM / "eda_resultados.json").read_text(encoding="utf-8"))
est = json.loads((MEM / "estimadores_resultados.json").read_text(encoding="utf-8"))
dg = json.loads((MEM / "diagnosticos_greg.json").read_text(encoding="utf-8"))

fallos = []


def buscar(texto: str, etiqueta: str, obligatorio: bool = True) -> None:
    hay = texto in html
    if obligatorio and not hay:
        fallos.append(f"NO aparece: {etiqueta}  ({texto!r})")
    print(f"  {'OK ' if hay else 'NO '} {etiqueta:48} {texto!r}")


print("=== KPI (valores censales) ===")
buscar("77 237", "registros censales")
buscar("30 086", "personas censales")
buscar("45,52", "edad media censal")
buscar("56,2 %", "retencion censal 2013-2021")
buscar("Censo completo", "etiqueta 'Censo completo'")

print("\n=== KPI (notas muestrales, como nota al pie) ===")
r = est["retencion"]["2013\u21922021"]
buscar(f"{r['mas']['estimador']*100:.1f} %".replace(".", ","), "estimacion MAS de retencion")
buscar("Estimación MAS", "etiqueta 'Estimación MAS'")

print("\n=== Varianza entre grupos ===")
for clave, etiqueta in (("NME_CLASIFICACION_PR", "categoria"), ("NME_GRAN_AREA_PR", "area"),
                        ("NME_DEPARTAMENTO_RES_PR", "departamento"),
                        ("NME_NIV_FORM_PR", "nivel"), ("NME_GENERO_COL", "genero")):
    v = eda["estratos_candidatos"][clave]["pct_varianza_explicada"]
    buscar(f"{v:.2f} %".replace(".", ","), f"varianza de {etiqueta}")

print("\n=== Universo y diagnostico ===")
buscar(str(eda["universo"]["convocatorias"]), "numero de convocatorias")
buscar(f"{dg['modelo_edad']['g_weights']['max']:.4f}".replace(".", ","), "g-weight maximo")
buscar(f"{dg['modelo_edad']['influencia']['cook_max']:.5f}".replace(".", ","), "Cook maximo")

print("\n=== Títulos de las 4 pestañas ===")
for t in ("1 · Univariado", "2 · Bivariado", "3 · Varianza entre grupos", "4 · Diagnósticos"):
    buscar(t, f"pestaña {t!r}")

print("\n=== Trazas por grafico (interactividad real) ===")
total_trazas = 0
for ident in ("u1", "u2", "u3", "u4", "u5", "u6", "r1", "r2", "r3", "r4", "r5",
              "v1", "v2", "d1", "d2", "d3", "d4"):
    m = re.search(r'Plotly\.newPlot\(\s*"' + ident + r'",\s*(\[.*?\])\s*,\s*\{',
                  html, re.S)
    if not m:
        fallos.append(f"no se encontro la llamada newPlot de {ident}")
        continue
    n = len(re.findall(r'"type"\s*:', m.group(1)))
    total_trazas += n
    print(f"  {ident:4} {n} traza(s)")
print(f"  total de trazas en el panel: {total_trazas}")
if total_trazas < 20:
    fallos.append(f"pocas trazas ({total_trazas}): los graficos podrian estar vacios")

print("\n=== Sin recursos externos en el cuerpo ===")
for patron, nombre in ((r"<script[^>]+src=", "<script src>"),
                       (r"<link[^>]*>", "<link>"),
                       (r"@import", "@import")):
    hay = re.search(patron, html, re.I)
    print(f"  {'OK ' if not hay else 'NO '} {nombre}")
    if hay:
        fallos.append(f"el dashboard referencia un recurso externo: {nombre}")

print("\n" + "=" * 70)
if fallos:
    print(f"{len(fallos)} PROBLEMA(S):")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("Todas las cifras del dashboard coinciden con los JSON de entrada.")
