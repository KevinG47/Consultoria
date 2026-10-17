# -*- coding: utf-8 -*-
"""
construir_repo_mejorado.py
==========================

Construye `04_auditoria/repo_mejorado/` a partir de `repo_auditado/`.

Reparto de responsabilidades entre las dos carpetas
---------------------------------------------------
- `repo_auditado/`   : copia VERBATIM del commit 1528939. Es la PRUEBA. No se
                       toca (236 archivos, hashes en manifiesto_sha256.csv).
- `repo_mejorado/`   : el mismo codigo con los 154 bugs diagnosticados en las 51
                       fichas corregidos. Es el CODIGO DE TRABAJO.

Este script solo hace la parte estructural (copiar, quitar rellenos y apartar el
legado no ejecutable). Los arreglos de codigo se aplican despues, uno a uno,
documentados en `repo_mejorado/CHANGELOG.md`.

Que hace
--------
1. Copia los 236 archivos de `repo_auditado/` a `repo_mejorado/`.
2. Elimina los `.gitkeep` (3 rellenos sin contenido util) y deja en su lugar un
   `README.md` que explica que va en cada carpeta de datos.
3. Aparta a `legacy_referencia/` los 13 archivos que las fichas marcan como
   NO ejecutables y "no migrar" (notebooks y scripts R de las tareas academicas
   con rutas de Colab y entradas ausentes), conservando su ruta relativa.

Uso
---
    python 04_auditoria/construir_repo_mejorado.py [--dry-run]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "04_auditoria" / "repo_original"
DESTINO = RAIZ / "04_auditoria" / "repo_mejorado"

# Rellenos sin contenido util: se sustituyen por un README que si explica algo.
# Son TODOS los .gitkeep del repo auditado (se descubren en tiempo de ejecucion
# para no dejarse ninguno fuera por una lista incompleta, que es el error que se
# cometio al escribirlos a mano).
GITKEEP_PREFIJOS_CON_README = ["datos/raw", "datos/processed", "models"]

# Residuos que nunca deben viajar a la copia de trabajo.
BASURA = {"__pycache__", ".pytest_cache", ".ipynb_checkpoints", ".mypy_cache"}
BASURA_ARCHIVOS = {".DS_Store", "Thumbs.db"}

# Archivos que las 51 fichas marcan como NO ejecutables y recomiendan "no migrar":
# son tareas academicas previas con rutas /content/ de Colab o Downloads/ de R y
# entradas ausentes. Se conservan como referencia, fuera del arbol de trabajo.
LEGACY = [
    "notebooks/tarea_anlisis_bases_de_datos/2019_codigo.py",
    "notebooks/tarea_anlisis_bases_de_datos/datos_2021.ipynb",
    "notebooks/tarea_anlisis_bases_de_datos/inv_17_codigo_graficas.R",
    "notebooks/tarea_gran_tabla/analisis2.ipynb",
    "notebooks/tarea_gran_tabla/analisis_de_clusters.R",
    "notebooks/tarea_gran_tabla/analisis_multivariado_base_gran_table.R",
    "notebooks/tarea_gran_tabla/codigo_analisis_univariado.py",
    "notebooks/tarea_gran_tabla/codigo_creacion_gran_tabla_a_partir_del_modelo_estrella.py",
    "notebooks/tarea_dimensiones_y_hechos/codigo_dimensiones_C.R",
    "notebooks/tarea_dimensiones_y_hechos/dimensiones.ipynb",
    "notebooks/tarea_dimensiones_y_hechos/tabla_hechos_codigo.R",
    "notebooks/tarea_join/codigo_join.py",
    "notebooks/tarea_tabla/arreglar_base_consultoria_7.R",
]

README_DATOS = {
    "datos/raw": """# datos/raw/

Datos crudos, **no versionados** por su tamano. Aqui va lo que el pipeline
espera encontrar:

| Archivo | Como se obtiene | Tamano |
|---|---|---|
| `produccion_grupos.csv` | `python -m src.ingesta.produccion` (API Socrata; requiere red) | ~1,2 GB |
| `investigadores_consolidado.csv` | descarga desde datos.gov.co | ~18 MB |

`cargar_consolidado()` (`src/ingesta/__init__.py`) prioriza
`datos/raw/investigadores_consolidado.csv` y, si no esta, cae al XLSX de
`datos/tarea_join/`, que **si esta versionado**: por eso los analisis de
investigadores funcionan sin descargar nada.

`cargar_produccion()` **no tiene respaldo**: sin `produccion_grupos.csv` los
scripts de produccion (`sprint5_produccion.py`, `sprint5_duckdb.py`,
`sprint6_ocde_composicion.py`) no pueden producir sus salidas. Se comportan como
se documenta en `CHANGELOG.md`: avisan, dicen el comando exacto y salen con
codigo 3 en vez de lanzar un traceback.
""",
    "datos/processed": """# datos/processed/

Artefactos derivados, **no versionados** (`*.duckdb` esta en `.gitignore`).

| Archivo | Como se obtiene |
|---|---|
| `observatorio.duckdb` | `python scripts/sprint2_duckdb.py` (requiere el consolidado) |

Se regenera de forma determinista a partir del consolidado. `sprint5_duckdb.py`
lo exige como punto de partida y avisa si falta.
""",
    "models": """# models/

Modelos entrenados. **Vacio a proposito y versionado como carpeta**: `*.pkl` y
`*.joblib` estan en `.gitignore` por tamano.

El proyecto no entrena modelos predictivos: `src/modelo/dimensional.py` construye
un modelo de datos (estrella), no un modelo estadistico. Si se anaden modelos,
declarar aqui como se regeneran.
""",
}


LEGACY_README = """# `legacy_referencia/` — material academico apartado

Los **13 archivos** de las tareas academicas previas (`notebooks/tarea_*`) que las
51 fichas de auditoria marcan como **NO ejecutables** y con recomendacion
explicita de **"no migrar"**.

## Por que no son ejecutables

| Causa | Archivos |
|---|---|
| Rutas de Colab (`/content/...`) que no existen fuera de Colab | 6 |
| `!pip install` y `display()`: magias de notebook, no Python valido | 3 |
| Rutas de `Downloads/*.xlsx` locales del autor | 4 |
| Variables usadas sin definirse en el propio archivo | 3 |

## Por que se conservan (y no se borran)

Son **referencia metodologica** de valor: k-prototypes para datos mixtos,
analisis de correspondencias (CA/MCA/FAMD), el proceso de join y de deduplicacion,
y los primeros EDA por convocatoria (donde esta documentado el hallazgo del
outlier de edad de 956 anios). Ademas son la evidencia de la capa `legacy` del
repositorio que la auditoria clasifica.

## Por que se apartan del arbol de trabajo

Su logica **ya esta reimplementada** en el pipeline moderno —`src/ingesta/`,
`src/analisis/` y `src/modelo/`— con tipos correctos y validacion. Dejarlas
mezcladas con el codigo que si funciona hace que quien llega pierda el tiempo
intentando ejecutarlas (y creyendo que el proyecto esta roto). Aqui estan, fuera
del camino, sin perder nada.

Se conserva la **ruta relativa original** de cada una: `legacy_referencia/notebooks/
tarea_gran_tabla/analisis2.ipynb` es el antiguo `notebooks/tarea_gran_tabla/analisis2.ipynb`.

## Nota sobre la sintaxis

Estos archivos **no son Python valido** a proposito: contienen `!pip install` y
`display()` de Colab/IPython. Por eso `verificar_arreglos.py` los excluye del
chequeo de sintaxis y por eso no se ejecutan.
"""


# El borrado robusto vive en fs_robusto.py, compartido con los otros scripts
# de verificacion: una sola implementacion para el mismo problema de OneDrive.
from fs_robusto import borrar_arbol, vaciar  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[3])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not ORIGEN.exists():
        print(f"[x] No existe {ORIGEN}.")
        return 1

    archivos = sorted(p for p in ORIGEN.rglob("*") if p.is_file())
    print(f"origen : {ORIGEN.relative_to(RAIZ)}  ({len(archivos)} archivos)")

    gitkeeps = sorted(p for p in archivos if p.name == ".gitkeep")
    residuos = sorted(p for p in archivos
                      if any(parte in BASURA for parte in p.parts)
                      or p.name in BASURA_ARCHIVOS)
    # La copia verbatim debe tener EXACTAMENTE el contenido versionado.
    manifest = RAIZ / "04_auditoria" / "manifiesto_sha256.csv"
    esperados = None
    if manifest.exists():
        import csv as _csv
        with manifest.open(encoding="utf-8", newline="") as fh:
            esperados = {f["ruta"] for f in _csv.DictReader(fh)}
        reales = {p.relative_to(ORIGEN).as_posix() for p in archivos}
        if reales != esperados:
            print(f"\n[x] {ORIGEN.name}/ NO coincide con el manifiesto:")
            for x in sorted(reales - esperados)[:10]:
                print(f"      sobra   {x}")
            for x in sorted(esperados - reales)[:10]:
                print(f"      falta   {x}")
            print("    Corrige la copia (python 04_auditoria/verificar_hashes.py)")
            print("    antes de construir la version mejorada.")
            return 1
        print(f"          coincide con el manifiesto ({len(esperados)} archivos)")

    if args.dry_run:
        print(f"destino: {DESTINO.relative_to(RAIZ)}")
        print(f"  se copiarian {len(archivos)} archivos")
        print(f"  se eliminarian {len(gitkeeps)} .gitkeep "
              f"({', '.join(p.relative_to(ORIGEN).as_posix() for p in gitkeeps)})")
        print(f"  se ignorarian {len(residuos)} residuos "
              f"({', '.join(sorted({p.parent.name for p in residuos})) or 'ninguno'})")
        print(f"  se apartarian {len(LEGACY)} archivos legacy a legacy_referencia/")
        return 0

    if DESTINO.exists():
        # Archivos que NO se regeneran al reconstruir y que, sin esta salvaguarda,
        # se perderian:
        #   - poetry.lock: lo produce `poetry lock` (aqui no hay poetry ni red).
        #   - CHANGELOG.md: documento redactado a mano, no un parche de texto.
        # El README.md SI se rehace: el parche J1 antepone la guia al README
        # original del proyecto auditado.
        preservados = {}
        for nombre in ("poetry.lock", "CHANGELOG.md"):
            f = DESTINO / nombre
            if f.exists():
                preservados[nombre] = f.read_bytes()
        if preservados:
            detalle = ", ".join(f"{k} ({len(v)} B)" for k, v in preservados.items())
            print(f"  [conserva] {detalle}")
            print("             (no se regeneran: se restauran tras reconstruir)")
        # Se VACIA en vez de borrar: os.rmdir sobre la carpeta puede
        # fallar con [WinError 5] porque OneDrive la mantiene abierta, y no
        # hace falta eliminarla.
        vaciar(DESTINO)
    else:
        preservados = {}
    DESTINO.mkdir(parents=True, exist_ok=True)

    # 1. copia verbatim, saltando residuos
    copiados = 0
    for p in archivos:
        if p in residuos:
            continue
        rel = p.relative_to(ORIGEN)
        dst = DESTINO / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        copiados += 1
    print(f"  copiados            : {copiados}")
    if residuos:
        print(f"  residuos omitidos   : {len(residuos)} "
              f"({', '.join(sorted({p.name for p in residuos}))})")

    # 2. fuera TODOS los .gitkeep, dentro README explicativo donde la carpeta
    #    quedaria vacia o necesita explicacion
    quitados = 0
    for f in gitkeeps:
        (DESTINO / f.relative_to(ORIGEN)).unlink()
        quitados += 1
    for prefijo in GITKEEP_PREFIJOS_CON_README:
        carpeta = DESTINO / prefijo
        if carpeta.exists():
            (carpeta / "README.md").write_text(README_DATOS[prefijo], encoding="utf-8")
    print(f"  .gitkeep eliminados : {quitados} "
          f"(+ {len(GITKEEP_PREFIJOS_CON_README)} README.md explicativos)")

    # 3. legado apartado, conservando la ruta relativa
    movidos = 0
    faltan = []
    for rel in LEGACY:
        src = DESTINO / rel
        if not src.exists():
            faltan.append(rel)
            continue
        dst = DESTINO / "legacy_referencia" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        movidos += 1
    print(f"  legacy apartados    : {movidos} -> legacy_referencia/")
    if faltan:
        print(f"  [!] no encontrados  : {faltan}")
        return 1

    (DESTINO / "legacy_referencia" / "README.md").write_text(
        LEGACY_README, encoding="utf-8")

    if preservados:
        for nombre, contenido in preservados.items():
            (DESTINO / nombre).write_bytes(contenido)
        print(f"  [restaurados] {', '.join(preservados)}")

    n = sum(1 for p in DESTINO.rglob("*") if p.is_file())
    print(f"\ndestino: {DESTINO.relative_to(RAIZ)}  ({n} archivos)")
    print("  siguiente paso: aplicar los arreglos de CHANGELOG.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
