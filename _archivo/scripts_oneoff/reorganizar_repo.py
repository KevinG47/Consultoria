# -*- coding: utf-8 -*-
"""
reorganizar_repo.py
===================

Migración de una sola vez: deja el repositorio en la estructura "clean" de cinco
carpetas numeradas y **reescribe todas las rutas del código y de los documentos**
para que nada quede apuntando al sitio viejo.

Estructura de destino
---------------------
    01_datos/datos_fuente/          datasets de entrada (CSV del DANE y la base)
    01_datos/resultados_json/       JSON de resultados de los análisis (F2-2 … F2-11)
    02_dashboards/                  HTML autocontenidos (paneles, mapa, visor, grafo)
    03_informes/analisis_fase2/     informes .md de la Fase 2 y la metodología
    04_auditoria/repo_original/     copia verbatim del repositorio auditado
    04_auditoria/repo_mejorado/     copia mejorada + scripts de extracción/verificación
    05_entregas/                    entregas al docente (PDF)

Lo que NO se mueve (y por qué)
------------------------------
    documentacion_auditoria/src/    el código; sus rutas son `Path(__file__)`
    documentacion_auditoria/data/   sigue siendo el almacén del sistema de memoria
                                    (índice RAG, grafo, decisiones, reglas) y las
                                    figuras PNG de cada análisis
    documentacion_auditoria/latex/  el documento LaTeX ya entregado
    data/validacion/ y latex/       fuentes que vigila R13: reescribirlas cambiaría
                                    su fecha y R13 pasaría a ADVERTENCIA

Los archivos que sí salen de `data/memoria/` son los que son *entregables* (HTML y
JSON de resultados); los artefactos internos del sistema (rag_*, grafo*,
decisiones.yaml, validacion_reglas.json, …) se quedan donde las reglas los buscan.

Uso
---
    python _archivo/scripts_oneoff/reorganizar_repo.py --dry-run   # solo informa
    python _archivo/scripts_oneoff/reorganizar_repo.py             # ejecuta
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
YO = Path(__file__).resolve()

# ---------------------------------------------------------------- inventario
HTML = ["dashboard_eda", "dashboard_fase2", "herramienta_trayectorias",
        "grafo_interactivo", "mapa_migracion"]
JSON_RESULTADOS = ["percapita_territorial", "modelo_estrella", "redes_nulos",
                   "diversidad_inferencia", "clustering", "validacion_unicidad",
                   "supervivencia", "flujos_territoriales"]
MD_INFORMES = ["analisis_longitudinal", "analisis_modelo_estrella", "analisis_redes",
               "analisis_diversidad", "analisis_clustering", "analisis_unicidad",
               "analisis_percapita_territorial", "analisis_supervivencia",
               "analisis_flujos", "metodologia_muestreo",
               "estudio_viabilidad_mapas", "reporte_validacion_cruzada",
               "evaluacion_cumplimiento", "comparacion_tfidf_vs_embeddings"]

# directorios que se mueven completos
MOVER_DIRS = [
    ("datos_originales/repo_auditado", "04_auditoria/repo_original"),
    ("datos_originales/repo_mejorado", "04_auditoria/repo_mejorado"),
    ("datos_originales/datos_fuente", "01_datos/datos_fuente"),
    ("ENTREGA_1", "05_entregas/ENTREGA_1"),
    ("entregables_2Corte", "05_entregas/entregables_2Corte"),
]

DIRS_NUEVOS = ["01_datos/datos_fuente", "01_datos/resultados_json", "02_dashboards",
               "03_informes/analisis_fase2", "04_auditoria/repo_original",
               "04_auditoria/repo_mejorado", "05_entregas/ENTREGA_1",
               "05_entregas/entregables_2Corte"]

# ------------------------------------------------------------ reescritura de rutas
H = "|".join(HTML)
J = "|".join(JSON_RESULTADOS)
M = "|".join(MD_INFORMES)

REGLAS: list[tuple[str, str, str]] = [
    # --- python con prefijo DOC / "data" / "memoria" / "x"
    (rf'DOC\s*/\s*"data"\s*/\s*"memoria"\s*/\s*"({H})\.html"',
     r'RAIZ / "02_dashboards" / "\1.html"', 'DOC/data/memoria html'),
    (rf'DOC\s*/\s*"data"\s*/\s*"memoria"\s*/\s*"({J})\.json"',
     r'RAIZ / "01_datos" / "resultados_json" / "\1.json"', 'DOC/data/memoria json'),
    # --- python con la constante MEM
    (rf'MEM\s*/\s*"({H})\.html"', r'DASH / "\1.html"', 'MEM html'),
    (rf'MEM\s*/\s*"({J})\.json"', r'RESULTADOS / "\1.json"', 'MEM json'),
    # --- python con la constante DOC y un informe .md
    (rf'DOC\s*/\s*"({M})\.md"',
     r'RAIZ / "03_informes" / "analisis_fase2" / "\1.md"', 'DOC informe md'),
    # --- javascript con componentes sueltos
    (rf'"documentacion_auditoria",\s*"data",\s*"memoria",\s*"({H})\.html"',
     r'"02_dashboards", "\1.html"', 'js path.join html'),
    (rf'"documentacion_auditoria",\s*"data",\s*"memoria",\s*"({J})\.json"',
     r'"01_datos", "resultados_json", "\1.json"', 'js path.join json'),
    # --- texto con la ruta completa
    (rf"documentacion_auditoria/data/memoria/({H})\.html",
     r"02_dashboards/\1.html", 'texto html'),
    (rf"documentacion_auditoria/data/memoria/({J})\.json",
     r"01_datos/resultados_json/\1.json", 'texto json'),
    (rf"(?<!documentacion_auditoria/)data/memoria/({H})\.html",
     r"02_dashboards/\1.html", 'texto corto html'),
    (rf"(?<!documentacion_auditoria/)data/memoria/({J})\.json",
     r"01_datos/resultados_json/\1.json", 'texto corto json'),
    (rf"documentacion_auditoria/({M})\.md",
     r"03_informes/analisis_fase2/\1.md", 'texto informe md'),
    # --- datos_originales (python entrecomillado y texto plano)
    (r'"datos_originales"\s*/\s*"datos_fuente"', '"01_datos" / "datos_fuente"',
     'py datos_fuente'),
    (r'"datos_originales"\s*/\s*"repo_auditado"', '"04_auditoria" / "repo_original"',
     'py repo_auditado'),
    (r'"datos_originales"\s*/\s*"repo_mejorado"', '"04_auditoria" / "repo_mejorado"',
     'py repo_mejorado'),
    (r"datos_originales/datos_fuente", "01_datos/datos_fuente", 'texto datos_fuente'),
    (r"datos_originales/repo_auditado", "04_auditoria/repo_original",
     'texto repo_auditado'),
    (r"datos_originales/repo_mejorado", "04_auditoria/repo_mejorado",
     'texto repo_mejorado'),
    (r'"datos_originales"', '"04_auditoria"', 'py datos_originales'),
    (r"datos_originales", "04_auditoria", 'texto datos_originales'),
    # --- entregas
    (r"\bENTREGA_1/", "05_entregas/ENTREGA_1/", 'texto ENTREGA_1'),
    (r"\bentregables_2Corte/", "05_entregas/entregables_2Corte/",
     'texto entregables_2Corte'),
]

EXTENSIONES = {".py", ".md", ".txt", ".yaml", ".yml", ".js", ".css"}
EXCLUIR_PREFIJOS = ("documentacion_auditoria/latex/", "documentacion_auditoria/pdf/",
                    "documentacion_auditoria/zip_overleaf/",
                    "documentacion_auditoria/data/validacion/", "_archivo/logs",
                    "documentacion_auditoria/data/memoria/rag_",
                    # el clon del auditado (441 MB, con su .venv) no se toca
                    "Observatorio_Ministerio_de_Ciencias_Grupo8/",
                    # las dos copias del proyecto auditado son SNAPSHOTS: no se
                    # reescriben, o dejarían de ser la copia que verifican los
                    # manifiestos y `verificar_arreglos.py`
                    "datos_originales/repo_auditado/", "datos_originales/repo_mejorado/",
                    "04_auditoria/repo_original/", "04_auditoria/repo_mejorado/")
EXCLUIR_SUFIJOS = (".log", ".jsonl", ".pdf", ".zip", ".png", ".npy", ".npz", ".pkl")


def textos_objetivo() -> list[Path]:
    """Archivos de texto versionados que se reescriben."""
    salida = []
    for p in RAIZ.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(RAIZ).as_posix()
        if p.resolve() == YO:
            continue
        if rel.startswith(EXCLUIR_PREFIJOS) or rel.endswith(EXCLUIR_SUFIJOS):
            continue
        if rel.endswith((".csv", ".html")):
            continue
        if any(part in ("__pycache__", ".venv", ".git") for part in p.parts):
            continue
        if rel.startswith("_archivo/") and p.suffix.lower() in (".txt", ".log"):
            continue          # salidas y mensajes históricos: no se reescriben
        if p.suffix.lower() in EXTENSIONES or p.name == ".gitignore":
            salida.append(p)
    return salida


def git(*args: str) -> None:
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"falló `git {' '.join(args)}`:\n{r.stderr}")


def versionado(rel: str) -> bool:
    r = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=RAIZ,
                       capture_output=True, text=True)
    return r.returncode == 0


def mover(rel: str, destino_rel: str, dry: bool, log: list[str]) -> None:
    origen = RAIZ / rel
    if not origen.exists():
        log.append(f"  [ya] {rel} (no existe; se omite)")
        return
    destino = RAIZ / destino_rel
    if destino.exists() and not destino.is_dir():
        raise SystemExit(f"destino {destino_rel} ya existe y es un archivo")
    destino.parent.mkdir(parents=True, exist_ok=True)
    tipo = "git mv" if versionado(rel) else "mv (no versionado)"
    log.append(f"  [{tipo}] {rel}  →  {destino_rel}")
    if dry:
        return
    if tipo == "git mv":
        git("mv", rel, destino_rel)
    else:
        import shutil
        shutil.move(str(origen), str(destino))


def main(dry: bool) -> int:
    log: list[str] = []
    print(("== SIMULACIÓN (dry-run): no se toca nada ==\n" if dry else "== APLICANDO ==\n"))

    print("== 1. Carpetas nuevas ==")
    for d in DIRS_NUEVOS:
        print(f"  {d}")
        if not dry:
            (RAIZ / d).mkdir(parents=True, exist_ok=True)

    print("\n== 2. Movimientos (git mv) ==")
    for origen, destino in MOVER_DIRS:
        mover(origen, destino, dry, log)
    for nombre in HTML:
        mover(f"documentacion_auditoria/data/memoria/{nombre}.html",
              f"02_dashboards/{nombre}.html", dry, log)
    for nombre in JSON_RESULTADOS:
        mover(f"documentacion_auditoria/data/memoria/{nombre}.json",
              f"01_datos/resultados_json/{nombre}.json", dry, log)
    for nombre in MD_INFORMES:
        mover(f"documentacion_auditoria/{nombre}.md",
              f"03_informes/analisis_fase2/{nombre}.md", dry, log)
    # lo que queda de datos_originales (scripts, README, ERRATA, manifiesto, reportes)
    for p in sorted((RAIZ / "datos_originales").glob("*")):
        if p.is_file():
            mover(f"datos_originales/{p.name}", f"04_auditoria/{p.name}", dry, log)
    print("\n".join(log) if log else "  (nada)")

    print("\n== 3. Reescritura de rutas ==")
    archivos = textos_objetivo()
    total = 0
    for p in archivos:
        try:
            texto = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        nuevo = texto
        n = 0
        for patron, reemplazo, _etiqueta in REGLAS:
            nuevo, k = re.subn(patron, reemplazo, nuevo)
            n += k
        if nuevo != texto:
            print(f"  {p.relative_to(RAIZ).as_posix():70s} {n:3d} reemplazo(s)")
            total += n
            if not dry:
                p.write_text(nuevo, encoding="utf-8", newline="\n")
    print(f"  {total} reemplazo(s) en {len(archivos)} archivos candidatos")

    print("\n== 4. Constantes nuevas en los scripts ==")
    sin_constante = []
    for p in archivos:
        if p.suffix != ".py" or not p.exists():
            continue
        texto = p.read_text(encoding="utf-8")
        falta = []
        if re.search(r"\bRESULTADOS / ", texto) and "RESULTADOS = " not in texto:
            falta.append(("RESULTADOS", '"01_datos" / "resultados_json"'))
        if re.search(r"\bDASH / ", texto) and "DASH = " not in texto:
            falta.append(("DASH", '"02_dashboards"'))
        if not falta:
            continue
        print(f"  {p.relative_to(RAIZ).as_posix():70s} + {', '.join(c for c, _ in falta)}")
        lineas = texto.splitlines(keepends=True)
        ancla = next((i for i, l in enumerate(lineas)
                      if re.match(r"(MEM|DIR_MEM)\s*=\s*", l)), None)
        if ancla is None:
            ancla = next((i for i, l in enumerate(lineas)
                          if re.match(r"(RAIZ|DOC)\s*=\s*", l)), None)
        if ancla is None:
            sin_constante.append(p.relative_to(RAIZ).as_posix())
            continue
        sangria = re.match(r"\s*", lineas[ancla]).group(0)
        nuevas = [f"{sangria}{nombre} = RAIZ / {valor}\n" for nombre, valor in falta]
        lineas[ancla + 1:ancla + 1] = nuevas
        if not dry:
            p.write_text("".join(lineas), encoding="utf-8", newline="\n")
    if sin_constante:
        print(f"  [REVISAR A MANO] sin ancla para las constantes: {sin_constante}")

    print("\n== 5. Sobrantes en datos_originales ==")
    resto = RAIZ / "datos_originales"
    if resto.exists():
        for p in sorted(resto.iterdir()):
            rel = p.relative_to(RAIZ).as_posix()
            if p.name == "__pycache__":
                print(f"  [borrar] {rel}")
                if not dry:
                    import shutil
                    shutil.rmtree(rel, ignore_errors=True)
                continue
            destino = f"04_auditoria/{p.name}"
            print(f"  [mover sin versión] {rel}  →  {destino}")
            if not dry:
                import shutil
                destino_abs = RAIZ / destino
                if destino_abs.exists():
                    destino_abs.unlink() if destino_abs.is_file() else None
                else:
                    shutil.move(rel, destino)
    else:
        print("  (datos_originales ya no existe)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--dry-run" in sys.argv))
