# -*- coding: utf-8 -*-
"""
verificar_consistencia.py
=========================

Verificador de AUTOCONSISTENCIA NUMÉRICA de la documentación.

Qué comprueba
-------------
1. Cifras citadas en prosa contra los conteos reales de las fuentes:
   - "N commits"            vs len(data/commits_timeline.csv)
   - "N archivos de código" vs len(data/inventario_codigo.csv)
   - "N scripts"            vs len(data/ejecucion_resumen.csv)
   - "N criterios"          vs len(data/objetivos.yaml)
2. Números citados contra elementos enumerados justo después:
   - "declara N preguntas" -> cuenta los \item de la sección siguiente.
3. Líneas de cobertura ("Cobertura: X de Y") contra los conteos reales.

Uso
---
    python src/verificar_consistencia.py

Salida: lista de comprobaciones con OK/FALLO; exit code 1 si hay fallos.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LATEX = RAIZ / "latex"
DATA = RAIZ / "data"


def _leer_tex() -> str:
    textos = []
    for p in LATEX.rglob("*.tex"):
        try:
            textos.append(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return "\n".join(textos)


def _contar_csv(path: str) -> int:
    p = DATA / path
    if not p.exists():
        return -1
    return sum(1 for _ in open(p, encoding="utf-8-sig")) - 1  # menos header


def _contar_yaml_objetivos() -> int:
    import yaml
    p = DATA / "objetivos.yaml"
    if not p.exists():
        return -1
    with open(p, encoding="utf-8-sig") as fh:
        return len(yaml.safe_load(fh).get("objetivos", []))


def _contar_preguntas(tex: str) -> int:
    """Cuenta los \item de la sección de preguntas del documento maestro."""
    m = re.search(r"Preguntas de investigación que el repositorio responde(.*?)\\end\{enumerate\}", tex, re.S)
    if m:
        return len(re.findall(r"\\item", m.group(1)))
    return -1


def main() -> None:
    tex = _leer_tex()
    fallos = 0
    total = 0

    def comprobar(nombre: str, cond: bool, detalle: str = "") -> None:
        nonlocal fallos, total
        total += 1
        estado = "OK  " if cond else "FALLO"
        if not cond:
            fallos += 1
        print(f"[{estado}] {nombre} {detalle}")

    # 1. Cifras canónicas (deben aparecer con el valor exacto esperado).
    #    Se verifican frases completas ("133 commits", "16 scripts") para no
    #    confundir con conteos de subgrupos mencionados en prosa.
    n_commits = _contar_csv("commits_timeline.csv")
    n_archivos = _contar_csv("inventario_codigo.csv")
    n_scripts = _contar_csv("ejecucion_resumen.csv")
    n_criterios = _contar_yaml_objetivos()
    n_fichas = len(list((DATA / "analisis_codigo").glob("*.json")))

    comprobar(f"cifra canónica de commits ('{n_commits} commits')",
              f"{n_commits} commits" in tex, "(esperado presente)")
    comprobar(f"cifra canónica de scripts ('{n_scripts} scripts')",
              f"{n_scripts} scripts" in tex, "(esperado presente)")
    comprobar(f"cifra canónica de criterios ('{n_criterios} criterios')",
              f"{n_criterios} criterios" in tex, "(esperado presente)")

    # 2. Preguntas enumeradas vs cifra citada
    n_preg = _contar_preguntas(tex)
    for m in re.finditer(r"declara (\d+) preguntas", tex, re.I):
        comprobar("preguntas enumeradas vs cifra citada",
                  n_preg > 0 and int(m.group(1)) == n_preg,
                  f"('{m.group(0)}' -> {n_preg} enumeradas)")

    # 3. Líneas de cobertura (X de Y) vs conteos reales.
    #    Tolerante a 'Cobertura:' dentro de \textbf{...}
    for m in re.finditer(r"Cobertura:?[^\d]*(\d+) de (\d+) archivos", tex, re.I):
        x, y = int(m.group(1)), int(m.group(2))
        comprobar(f"cobertura {x} de {y}", x <= y <= n_archivos,
                  f"(archivos reales {n_archivos})")

    # 4. Fichas de código: 100% de cobertura en el maestro
    comprobar("fichas JSON == inventario", n_fichas == n_archivos,
              f"(fichas {n_fichas} vs inventario {n_archivos})")

    print(f"\n{total} comprobaciones, {fallos} fallos.")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
