# -*- coding: utf-8 -*-
"""Ajustes manuales que la reescritura automática no puede hacer sola."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
SRC = DOC / "src"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parchear(ruta: Path, pares: list[tuple[str, str]], obligatorio: bool = True) -> None:
    texto = ruta.read_text(encoding="utf-8")
    nuevo = texto
    for viejo, nuevo_txt in pares:
        if viejo not in nuevo:
            if obligatorio:
                raise SystemExit(f"no se encontró en {ruta.name}:\n{viejo}")
            continue
        nuevo = nuevo.replace(viejo, nuevo_txt)
    if nuevo != texto:
        ruta.write_text(nuevo, encoding="utf-8", newline="\n")
        print(f"  [ok] {ruta.relative_to(RAIZ).as_posix()}")
    else:
        print(f"  [--] {ruta.relative_to(RAIZ).as_posix()} (sin cambios)")


def main() -> int:
    print("== 1. construir_herramienta.py: el HTML va a 02_dashboards ==")
    parchear(SRC / "construir_herramienta.py", [
        ('DIR_MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"\n'
         'SALIDA = DIR_DASH / "herramienta_trayectorias.html"',
         'DIR_MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"\n'
         'DASH = RAIZ / "02_dashboards"\n'
         'SALIDA = DASH / "herramienta_trayectorias.html"'),
    ])

    print("\n== 2. generar_dashboard_fase2.py: los JSON de resultados ==")
    parchear(SRC / "generar_dashboard_fase2.py", [
        ('MEM = DOC / "data" / "memoria"\nDASH = RAIZ / "02_dashboards"',
         'MEM = DOC / "data" / "memoria"\n'
         'RESULTADOS = RAIZ / "01_datos" / "resultados_json"\n'
         'DASH = RAIZ / "02_dashboards"'),
        ('return json.loads((MEM / f"{nombre}.json").read_text(encoding="utf-8"))',
         'return json.loads((RESULTADOS / f"{nombre}.json").read_text(encoding="utf-8"))'),
    ])

    print("\n== 3. verificar_dashboard_fase2.py: los JSON de resultados ==")
    parchear(SRC / "verificar_dashboard_fase2.py", [
        ('MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"\n'
         'DASH = RAIZ / "02_dashboards"',
         'MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"\n'
         'RESULTADOS = RAIZ / "01_datos" / "resultados_json"\n'
         'DASH = RAIZ / "02_dashboards"'),
        ('d = {k: json.loads((MEM / f"{k}.json").read_text(encoding="utf-8"))',
         'd = {k: json.loads((RESULTADOS / f"{k}.json").read_text(encoding="utf-8"))'),
    ])

    print("\n== 4. auditar_cifras.py: el cargador dinámico ==")
    parchear(RAIZ / "_archivo" / "scripts_oneoff" / "auditar_cifras.py", [
        ('MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"\n'
         'DASH = RAIZ / "02_dashboards"',
         'MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"\n'
         'RESULTADOS = RAIZ / "01_datos" / "resultados_json"\n'
         'DASH = RAIZ / "02_dashboards"'),
        ('def L(n):\n    return json.loads((MEM / f"{n}.json").read_text(encoding="utf-8"))',
         'DE_RESULTADOS = {"percapita_territorial", "modelo_estrella", "redes_nulos",\n'
         '                 "diversidad_inferencia", "clustering", "validacion_unicidad",\n'
         '                 "supervivencia", "flujos_territoriales"}\n\n\n'
         'def L(n):\n'
         '    base = RESULTADOS if n in DE_RESULTADOS else MEM\n'
         '    return json.loads((base / f"{n}.json").read_text(encoding="utf-8"))'),
    ])

    print("\n== 5. memoria/config.py: raíces de la estructura nueva ==")
    parchear(SRC / "memoria" / "config.py", [
        ('MEMORIA = DATA / "memoria"                     # artefactos que produce este sistema',
         'MEMORIA = DATA / "memoria"                     # artefactos que produce este sistema\n'
         '\n'
         '# --- Estructura "clean" del repositorio (reorganización 2026-10) ---------\n'
         '# Los entregables de la Fase 2 salieron del almacén del sistema para que el\n'
         '# próximo grupo encuentre de un vistazo datos, paneles, informes, auditoría y\n'
         '# entregas. `MEMORIA` sigue siendo el almacén interno (índice RAG, grafo,\n'
         '# decisiones, reglas y figuras PNG de cada análisis).\n'
         'DATOS = RAIZ / "01_datos"\n'
         'DATOS_FUENTE = DATOS / "datos_fuente"\n'
         'RESULTADOS_JSON = DATOS / "resultados_json"\n'
         'DASHBOARDS = RAIZ / "02_dashboards"\n'
         'INFORMES = RAIZ / "03_informes" / "analisis_fase2"\n'
         'AUDITORIA = RAIZ / "04_auditoria"\n'
         'REPO_ORIGINAL = AUDITORIA / "repo_original"\n'
         'REPO_MEJORADO = AUDITORIA / "repo_mejorado"\n'
         'ENTREGAS = RAIZ / "05_entregas"'),
    ])

    print("\n== 6. memoria/visual.py: el HTML del grafo va a 02_dashboards ==")
    parchear(SRC / "memoria" / "visual.py", [
        ('GRAFICO_HTML = config.MEMORIA / "grafo_interactivo.html"',
         'GRAFICO_HTML = config.DASHBOARDS / "grafo_interactivo.html"'),
    ])

    print("\n== 7. Los JSON de resultados citan rutas: se corrigen en el texto ==")
    reemplazos = [
        ("datos_originales/datos_fuente", "01_datos/datos_fuente"),
        ("datos_originales/repo_auditado", "04_auditoria/repo_original"),
        ("datos_originales/repo_mejorado", "04_auditoria/repo_mejorado"),
        ("datos_originales/", "04_auditoria/"),
    ]
    for p in sorted((RAIZ / "01_datos" / "resultados_json").glob("*.json")):
        texto = p.read_text(encoding="utf-8")
        nuevo = texto
        for viejo, valor in reemplazos:
            nuevo = nuevo.replace(viejo, valor)
        if nuevo != texto:
            json.loads(nuevo)          # verifica que siga siendo JSON válido
            p.write_text(nuevo, encoding="utf-8", newline="\n")
            print(f"  [ok] {p.relative_to(RAIZ).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
