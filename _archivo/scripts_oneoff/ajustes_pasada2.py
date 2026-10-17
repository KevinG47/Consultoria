# -*- coding: utf-8 -*-
"""Segunda pasada: referencias por componentes que la primera no vio."""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
UNO = RAIZ / "_archivo" / "scripts_oneoff"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# forma "por componentes": RAIZ / "documentacion_auditoria" / "data" / "memoria"
# seguida (misma o siguiente línea) de un JSON de resultados que se mudó
PATRON_JSON = re.compile(
    r'RAIZ / "documentacion_auditoria" / "data" / "memoria"\s*/\s*"'
    r'(percapita_territorial|modelo_estrella|redes_nulos|diversidad_inferencia|'
    r'clustering|validacion_unicidad|supervivencia|flujos_territoriales)\.json"')
PATRON_HTML = re.compile(
    r'RAIZ / "documentacion_auditoria" / "data" / "memoria"\s*/\s*"'
    r'(dashboard_eda|dashboard_fase2|herramienta_trayectorias|grafo_interactivo|'
    r'mapa_migracion)\.html"')

FIX = [
    ("_archivo/scripts_oneoff/resumir_percapita.py", "json"),
    ("_archivo/scripts_oneoff/resumir_estrella.py", "json"),
    ("_archivo/scripts_oneoff/detalle_juicios_r.py", "json"),
    ("_archivo/scripts_oneoff/auditar_silhouette.py", "json"),
    ("_archivo/scripts_oneoff/auditar_silhouette_mc.py", "json"),
    ("_archivo/scripts_oneoff/extraer_texto_panel.py", "html"),
    ("_archivo/scripts_oneoff/verificar_herramienta_final.py", "html"),
]


def main() -> int:
    for rel, tipo in FIX:
        p = RAIZ / rel
        texto = p.read_text(encoding="utf-8")
        if tipo == "json":
            nuevo, n = PATRON_JSON.subn(
                r'RAIZ / "01_datos" / "resultados_json" / "\1.json"', texto)
        else:
            nuevo, n = PATRON_HTML.subn(
                r'RAIZ / "02_dashboards" / "\1.html"', texto)
        if n:
            p.write_text(nuevo, encoding="utf-8", newline="\n")
        print(f"  [{'ok' if n else '--'}] {rel} ({n} reemplazo(s))")

    # volcar_bootstrap.py: la constante M solo se usa para el JSON de F2-2
    p = UNO / "volcar_bootstrap.py"
    texto = p.read_text(encoding="utf-8")
    viejo = ('M = Path(__file__).resolve().parents[2] / "documentacion_auditoria" '
             '/ "data" / "memoria"')
    nuevo = ('M = Path(__file__).resolve().parents[2] / "01_datos" / "resultados_json"')
    if viejo in texto:
        p.write_text(texto.replace(viejo, nuevo), encoding="utf-8", newline="\n")
        print(f"  [ok] _archivo/scripts_oneoff/volcar_bootstrap.py")
    else:
        print("  [--] volcar_bootstrap.py (sin cambios)")

    # verificar_colapso_genero.py: parents[3] apuntaba un nivel de más
    p = UNO / "verificar_colapso_genero.py"
    texto = p.read_text(encoding="utf-8")
    if "parents[3]" in texto:
        p.write_text(texto.replace("parents[3]", "parents[2]"), encoding="utf-8",
                     newline="\n")
        print("  [ok] _archivo/scripts_oneoff/verificar_colapso_genero.py (parents[3]→parents[2])")
    else:
        print("  [--] verificar_colapso_genero.py (sin cambios)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
