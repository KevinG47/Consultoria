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


ENUNCIADO_PREGUNTAS = re.compile(
    r"Preguntas de investigaci[oó]n que el repositorio responde")
BLOQUE_ENUMERATE = re.compile(r"\\begin\{enumerate\}(.*?)\\end\{enumerate\}", re.S)


def _archivos_tex() -> list[Path]:
    """
    Los .tex del corpus, ORDENADOS.

    El orden importa y NO es el mismo en Windows que en Linux: `rglob` devuelve
    el orden del sistema de archivos. Con el codigo anterior el conteo de
    preguntas dependia de ese orden (con las mismas fuentes daba 5, 7 u 8 en
    Windows y 842 dentro del contenedor Linux), porque el enunciado que se busca
    aparece en tres documentos y el `\\end{enumerate}` que cerraba la busqueda
    podia pertenecer a otro archivo. Ordenar lo hace reproducible en los dos
    sistemas.
    """
    return sorted(LATEX.rglob("*.tex"),
                  key=lambda p: p.relative_to(LATEX).as_posix())


def _leer_tex() -> str:
    textos = []
    for p in _archivos_tex():
        try:
            # utf-8-sig = utf-8 tolerando BOM si algun archivo lo trae. Los saltos
            # de linea no hacen falta normalizarlos: al leer en modo texto Python
            # ya convierte CRLF en LF.
            textos.append(p.read_text(encoding="utf-8-sig", errors="replace"))
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


def _contar_preguntas() -> tuple[int, str]:
    r"""Preguntas enumeradas del maestro: los `\item` del primer bloque enumerate
    que sigue al enunciado, EXIGIENDO que enunciado y bloque esten en el MISMO
    archivo.

    Antes se buscaba sobre la concatenacion de los 133 .tex. El enunciado aparece
    tambien en `objetivo_1/secciones/03_entendimiento.tex` y en su version LITE,
    que NO tienen bloque, asi que `(.*?)\end{enumerate}` se estiraba hasta el
    siguiente cierre de enumerate del corpus entero. Eso ataba el resultado al
    orden de lectura: 5, 7 u 8 en Windows y 842 dentro del contenedor Linux.

    Devuelve (n, nombre_del_archivo); (-1, "") si ningun archivo trae el enunciado
    seguido de un bloque enumerate cerrado.
    """
    for ruta in _archivos_tex():
        try:
            texto = ruta.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        enunciado = ENUNCIADO_PREGUNTAS.search(texto)
        if not enunciado:
            continue
        bloque = BLOQUE_ENUMERATE.search(texto, enunciado.end())
        if not bloque:
            continue        # el documento menciona las preguntas pero no las enumera
        return len(re.findall(r"\\item", bloque.group(1))), ruta.name
    return -1, ""


def ejecutar() -> list[dict]:
    """
    Ejecuta las comprobaciones y devuelve resultados ESTRUCTURADOS (reutilizable
    desde memoria.reglas como regla R14, sin duplicar lógica).

    Devuelve una lista de {nombre, ok, detalle}.
    """
    tex = _leer_tex()
    resultados: list[dict] = []

    def comprobar(nombre: str, cond: bool, detalle: str = "") -> None:
        resultados.append({"nombre": nombre, "ok": bool(cond), "detalle": detalle})

    # 1. Cifras canónicas (deben aparecer con el valor exacto esperado).
    n_commits = _contar_csv("commits_timeline.csv")
    n_archivos = _contar_csv("inventario_codigo.csv")
    n_scripts = _contar_csv("ejecucion_resumen.csv")
    n_criterios = _contar_yaml_objetivos()
    n_fichas = len(list((DATA / "analisis_codigo").glob("*.json")))

    comprobar(f"cifra canónica de commits ('{n_commits} commits')",
              f"{n_commits} commits" in tex, "esperado presente")
    comprobar(f"cifra canónica de scripts ('{n_scripts} scripts')",
              f"{n_scripts} scripts" in tex, "esperado presente")
    comprobar(f"cifra canónica de criterios ('{n_criterios} criterios')",
              f"{n_criterios} criterios" in tex, "esperado presente")

    # 2. Preguntas enumeradas vs cifra citada
    n_preg, archivo_preg = _contar_preguntas()
    for m in re.finditer(r"declara (\d+) preguntas", tex, re.I):
        comprobar("preguntas enumeradas vs cifra citada",
                  n_preg > 0 and int(m.group(1)) == n_preg,
                  f"'{m.group(0)}' -> {n_preg} enumeradas"
                  + (f" en {archivo_preg}" if archivo_preg else ""))

    # 3. Líneas de cobertura (X de Y) vs conteos reales.
    for m in re.finditer(r"Cobertura:?[^\d]*(\d+) de (\d+) archivos", tex, re.I):
        x, y = int(m.group(1)), int(m.group(2))
        comprobar(f"cobertura {x} de {y}", x <= y <= n_archivos,
                  f"archivos reales {n_archivos}")

    # 4. Fichas de código: 100% de cobertura en el maestro
    comprobar("fichas JSON == inventario", n_fichas == n_archivos,
              f"fichas {n_fichas} vs inventario {n_archivos}")

    return resultados


def main() -> None:
    resultados = ejecutar()
    fallos = sum(1 for r in resultados if not r["ok"])
    for r in resultados:
        estado = "OK  " if r["ok"] else "FALLO"
        print(f"[{estado}] {r['nombre']} ({r['detalle']})")
    print(f"\n{len(resultados)} comprobaciones, {fallos} fallos.")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
