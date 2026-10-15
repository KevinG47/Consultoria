# -*- coding: utf-8 -*-
"""
probar_inventario_completo.py
=============================

Prueba, uno por uno, los **51 artefactos de codigo** que el proyecto auditado
declara en `documentacion_auditoria/data/inventario_codigo.csv`, usando las
versiones MODERNAS de las librerias que hay instaladas (pandas 3, numpy 2,
plotly 7, matplotlib 3.11...).

Para que sirve
--------------
`probar_librerias_reales.py` prueba los 6 scripts que se arreglaron. Este script
responde una pregunta distinta: de los 51 artefactos del inventario, **cuantos
siguen funcionando con las versiones nuevas** y cuantos fallan, clasificando el
motivo de cada fallo.

Modos de prueba (segun el tipo de artefacto)
--------------------------------------------
- `scripts/*.py`, `streamlit_app.py`, `app/*.py`  -> se EJECUTAN
- `src/**/*.py`                                   -> se IMPORTAN (son libreria)
- `tests/*.py`                                    -> se ejecutan con pytest
- Notebooks                                       -> nbformat + compilacion de
                                                     cada celda de codigo
- `*.R`                                           -> Rscript + parse()
- los 13 artefactos de `legacy_referencia/`       -> NO MIGRADOS por diseno;
                                                     se comprueba su sintaxis

Todo se ejecuta sobre una copia desechable: `repo_mejorado/` es evidencia y no
debe quedar alterado por una corrida de prueba. Ningun artefacto se borra ni se
modifica: los que fallan se reportan con su traza.

Codigos de salida del proyecto (contrato ya documentado)
--------------------------------------------------------
  0 = corre completo        3 = le faltan datos de entrada (no versionados)
  1 = error real con traza

Uso:
    python datos_originales/probar_inventario_completo.py
    python datos_originales/probar_inventario_completo.py --sin-ejecutar
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fs_robusto import borrar_arbol  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
MEJORADO = RAIZ / "datos_originales" / "repo_mejorado"
PRUEBA = RAIZ / "datos_originales" / "_prueba_inventario"
CLON = RAIZ / "Observatorio_Ministerio_de_Ciencias_Grupo8"
INVENTARIO = RAIZ / "documentacion_auditoria" / "data" / "inventario_codigo.csv"
EXTRAS = RAIZ / "_archivo" / "deps_extra"
INFORME_CSV = RAIZ / "datos_originales" / "reporte_ejecucion_51.csv"
INFORME_JSON = RAIZ / "datos_originales" / "_reporte_ejecucion_51.json"

TIEMPO_SCRIPT = 900
TIEMPO_STREAMLIT = 60
TIEMPO_IMPORT = 300
TIEMPO_R = 120

# Estados posibles. El vocabulario es cerrado a proposito: la tabla final se lee
# de un vistazo y cada estado tiene un significado unico.
CORRE = "CORRE"
SIN_DATOS = "CORRE (sin datos de entrada)"
IMPORTA = "IMPORTA OK"
TEST_OK = "TEST PASA"
SIN_PRUEBAS = "N/A (sin pruebas)"
FALLA = "FALLA"
SIN_HERRAMIENTA = "NO EJECUTADO (falta herramienta)"
LEGACY = "LEGACY (no migrado)"


def inventario() -> list[dict]:
    # OJO: el CSV lleva BOM. Con encoding="utf-8" la primera columna se llama
    # "\ufeffruta" y todo el bucle revienta con KeyError. utf-8-sig lo consume.
    with INVENTARIO.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def localizar(ruta: str) -> tuple[Path, bool]:
    """Devuelve (ruta dentro de la COPIA desechable, es_legacy).

    Se resuelve siempre dentro de `_prueba_inventario/`, que es donde se
    ejecuta: los artefactos no migrados viven bajo `legacy_referencia/`.
    """
    rel = Path(ruta.replace("/", os.sep))
    if (MEJORADO / rel).exists():
        return PRUEBA / rel, False
    if (MEJORADO / "legacy_referencia" / rel).exists():
        return PRUEBA / "legacy_referencia" / rel, True
    return PRUEBA / rel, False


def modulo_de(ruta: str) -> tuple[str, str]:
    """Devuelve (nombre del modulo, carpeta que hay que agregar al PYTHONPATH).

    OJO con `src/`: el proyecto NO importa `src.analisis.calidad`. Los scripts
    hacen `sys.path.insert(0, ROOT/"src")` y despues `from analisis.redes import ...`
    o `from ingesta import ...`. Por eso hay que probar los modulos de `src/` con
    la MISMA raiz de importacion que usa el proyecto; importarlos como
    `src.modelo.dimensional` produce un ModuleNotFoundError de `analisis` que no
    es un defecto del codigo.
    """
    rel = ruta.replace("\\", "/")
    if rel == "src/__init__.py":
        return "src", ""
    if rel.startswith("src/"):
        interior = rel[len("src/"):]
        if interior.endswith("/__init__.py"):
            return interior[: -len("/__init__.py")].replace("/", "."), "src"
        return interior[:-3].replace("/", "."), "src"
    return rel[:-3].replace("/", "."), ""


def entorno(extra: str = "") -> dict:
    env = dict(os.environ)
    rutas = [str(PRUEBA)]
    if extra:
        rutas.append(str(PRUEBA / extra))
    # `_archivo/deps_extra` solo se agrega si el interprete en uso NO trae pytest.
    # Si se agregara siempre, su pytest taparia al del entorno virtual de poetry y
    # la prueba dejaria de ser con las versiones fijadas por el lock.
    import importlib.util as iu
    if EXTRAS.exists() and iu.find_spec("pytest") is None:
        rutas.append(str(EXTRAS))
    previo = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = ";".join(rutas + ([previo] if previo else []))
    env["PYTHONIOENCODING"] = "utf-8"
    env["MPLBACKEND"] = "Agg"
    return env


def correr(comando: list[str], limite: int, extra: str = "") -> tuple[int, str, float]:
    t0 = time.time()
    try:
        r = subprocess.run(comando, cwd=str(PRUEBA), capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=limite, env=entorno(extra))
        return r.returncode, (r.stdout or "") + (r.stderr or ""), time.time() - t0
    except subprocess.TimeoutExpired as exc:
        # OJO: al agotarse el tiempo hay que recuperar lo ya escrito. Streamlit no
        # termina nunca, asi que "You can now view" solo aparece en esa salida.
        partes = []
        for flujo in (exc.stdout, exc.stderr):
            if isinstance(flujo, bytes):
                partes.append(flujo.decode("utf-8", "replace"))
            elif flujo:
                partes.append(flujo)
        return 124, "".join(partes) + f"\n[TIEMPO AGOTADO tras {limite} s]", time.time() - t0


# --------------------------------------------------------- categorias F1-F5
# Vocabulario cerrado para clasificar CUALQUIER fallo. Vive aqui, y no en un
# script aparte, para que la tabla y su clasificacion salgan del mismo comando.
F1 = "F1 - datos de entrada ausentes"
F2 = "F2 - dependencia declarada, no instalada en este entorno"
F3 = "F3 - cambio de comportamiento de libreria (breaking change)"
F4 = "F4 - limitacion del entorno (navegador/red/tiempo)"
F5 = "F5 - artefacto legado no migrado (por diseno)"

LIBRERIAS = ("pandas", "numpy", "plotly", "matplotlib", "seaborn", "networkx",
             "scipy", "scikit", "duckdb", "streamlit", "nbformat", "kaleido")


def declaradas() -> set[str]:
    """Dependencias declaradas en el pyproject del repo mejorado."""
    import tomllib
    datos = tomllib.loads((MEJORADO / "pyproject.toml").read_text(encoding="utf-8"))
    poesia = datos.get("tool", {}).get("poetry", {})
    nombres: set[str] = set()
    for grupo in (poesia.get("dependencies", {}),
                  poesia.get("group", {}).get("dev", {}).get("dependencies", {})):
        for clave in grupo:
            nombres.add(clave.lower().replace("-", "").replace("_", ""))
    return nombres


def clasificar_fallo(salida: str, extra: dict, modo: str, decl: set[str]) -> tuple[str, str]:
    """Devuelve (categoria, motivo) de un fallo. Reglas explicitas y auditables."""
    import re as _re

    if extra.get("exit") == 3 or "datos faltantes" in salida:
        return F1, "necesita un dataset que no esta versionado"

    coincidencia = _re.search(r"(?:ModuleNotFoundError|ImportError): No module named '([^']+)'",
                              salida)
    if coincidencia:
        paquete = coincidencia.group(1).split(".")[0]
        canon = paquete.lower().replace("-", "").replace("_", "")
        if canon in decl:
            return F2, f"`{paquete}` esta declarada en pyproject.toml y no esta instalada"
        return F2, (f"`{paquete}` se importa y NO esta declarada: hueco real de "
                    f"declaracion, no del entorno")

    if "TIEMPO AGOTADO" in salida:
        return F4, "se agoto el tiempo de espera"
    if modo == "streamlit" or "kaleido" in salida or "choreographer" in salida:
        return F4, "el navegador o el servidor no arrancan en este entorno"

    for lib in LIBRERIAS:
        if lib in salida:
            if _re.search(r"(AttributeError|TypeError|ValueError|KeyError|"
                          r"NotImplementedError|FutureWarning|DeprecationWarning)", salida):
                return F3, f"apunta a un cambio de comportamiento en {lib}"
            break
    if "Traceback" in salida:
        return F3, "traza de ejecucion: revisar si es cambio de libreria o defecto propio"
    return F3, "sin clasificar con las reglas actuales"


def clasificar(ruta: str, lenguaje: str, es_legacy: bool) -> str:
    # OJO: el inventario usa "\" en Windows. Sin normalizar, startswith("src/")
    # nunca coincide y los modulos de libreria se tratarian como scripts.
    rel = ruta.replace("\\", "/")
    if es_legacy:
        return "legacy"
    if lenguaje == "Notebook":
        return "notebook"
    if lenguaje == "R":
        return "r"
    if rel.startswith("tests/"):
        return "test"
    if rel.startswith("src/"):
        return "import"
    if rel in ("streamlit_app.py", "app/streamlit_app.py"):
        return "streamlit"
    if rel.startswith("scripts/"):
        return "script"
    return "script"


def probar_notebook(ruta: Path) -> tuple[str, str, dict]:
    import nbformat

    try:
        nb = nbformat.read(str(ruta), as_version=4)
    except Exception as exc:  # noqa: BLE001
        return FALLA, f"nbformat no puede leerlo: {type(exc).__name__}: {exc}", {}

    celdas = len(nb.cells)
    codigo = [c for c in nb.cells if c.cell_type == "code"]
    errores, magias = [], 0
    for i, c in enumerate(codigo):
        fuente = c.source
        if any(l.lstrip().startswith(("!", "%")) for l in fuente.splitlines()):
            magias += 1
        try:
            compile(fuente, f"{ruta.name}:celda{i}", "exec")
        except SyntaxError as exc:
            errores.append(f"celda {i}: {exc.msg} (linea {exc.lineno})")
    detalle = {
        "celdas": celdas, "celdas_codigo": len(codigo),
        "celdas_con_magia": magias, "errores_sintaxis": errores,
    }
    if errores:
        return FALLA, f"{len(errores)} celdas no compilan: {errores[0]}", detalle
    return IMPORTA, (f"valido: {celdas} celdas ({len(codigo)} de codigo, "
                     f"{magias} con magia de Colab); todas compilan"), detalle


def probar_r(ruta: Path) -> tuple[str, str, dict]:
    if shutil.which("Rscript") is None:
        return SIN_HERRAMIENTA, "Rscript no esta instalado", {}
    expr = f"invisible(parse(file='{ruta.as_posix()}'))"
    codigo, salida, _ = correr(["Rscript", "-e", expr], TIEMPO_R)
    if codigo == 0:
        return IMPORTA, "R: parse() sin errores", {}
    lineas = [l for l in salida.strip().splitlines() if l.strip()]
    return FALLA, "R: " + (lineas[-1][:200] if lineas else "error de sintaxis"), {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-ejecutar", action="store_true",
                    help="solo comprueba sintaxis e importaciones")
    ap.add_argument("--etiqueta", default="",
                    help="sufijo para los archivos de informe, p. ej. 'poetry' "
                         "para distinguir la corrida con las versiones fijadas "
                         "por el lock de la corrida con versiones modernas")
    args = ap.parse_args()

    sufijo = f"_{args.etiqueta}" if args.etiqueta else ""
    informe_csv = INFORME_CSV.with_name(f"{INFORME_CSV.stem}{sufijo}.csv")
    informe_json = INFORME_JSON.with_name(f"{INFORME_JSON.stem}{sufijo}.json")

    filas = inventario()
    print(f"artefactos en el inventario: {len(filas)}")
    DECLARADAS = declaradas()
    print(f"dependencias declaradas en pyproject.toml: {len(DECLARADAS)}")

    import importlib.metadata as md
    print("\nVERSIONES EN USO")
    for p in ["pandas", "numpy", "matplotlib", "seaborn", "plotly", "kaleido",
              "duckdb", "openpyxl", "nbformat", "streamlit", "scikit-learn",
              "networkx"]:
        try:
            print(f"  {p:14s} {md.version(p)}")
        except Exception:  # noqa: BLE001
            print(f"  {p:14s} NO INSTALADA")
    for p in ["pytest", "pyvis", "sodapy", "pandera", "nbclient"]:
        try:
            print(f"  {p:14s} {md.version(p)}")
        except Exception:  # noqa: BLE001
            print(f"  {p:14s} NO INSTALADA (se aporta desde PYTHONPATH si aplica)")

    borrar_arbol(PRUEBA)
    print(f"\ncreando copia desechable {PRUEBA.name}/ ...")
    shutil.copytree(MEJORADO, PRUEBA, dirs_exist_ok=True)
    db = CLON / "datos" / "processed" / "observatorio.duckdb"
    if db.exists():
        destino = PRUEBA / "datos" / "processed" / "observatorio.duckdb"
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db, destino)
        print(f"  [datos] observatorio.duckdb copiado del clon")
    prod = PRUEBA / "datos" / "raw" / "produccion_grupos.csv"
    print(f"  [datos] produccion_grupos.csv presente: {prod.exists()}")

    resultados = []
    for i, fila in enumerate(filas, 1):
        ruta = fila["ruta"].replace("/", "\\")
        lenguaje = fila["lenguaje"]
        absoluta, es_legacy = localizar(fila["ruta"])
        modo = clasificar(fila["ruta"], lenguaje, es_legacy)
        print("\n" + "=" * 78)
        print(f"[{i:2d}/51] {fila['ruta']}   ({lenguaje}, {fila['lineas']} lineas, modo={modo})")
        print("=" * 78)

        if not absoluta.exists():
            estado, detalle, extra = FALLA, "el archivo no existe en repo_mejorado/", {}
        elif es_legacy:
            # Los 13 legados NO se migraron: se comprueba la sintaxis, que es lo
            # unico verificable sin sus datos de Colab.
            if lenguaje == "R":
                _, det, _ = probar_r(absoluta)
            elif lenguaje == "Notebook":
                _, det, _ = probar_notebook(absoluta)
            else:
                try:
                    compile(absoluta.read_text(encoding="utf-8", errors="replace"),
                            str(absoluta), "exec")
                    det = "compila como Python"
                except SyntaxError as exc:
                    det = f"no compila: {exc.msg} (linea {exc.lineno})"
            estado, extra = LEGACY, {"sintaxis": det}
            detalle = f"en legacy_referencia/: {det}"
        else:
            rel = absoluta.relative_to(PRUEBA).as_posix()
            if modo == "notebook":
                estado, detalle, extra = probar_notebook(absoluta)
            elif modo == "r":
                estado, detalle, extra = probar_r(absoluta)
            elif modo == "import":
                modulo, carpeta = modulo_de(fila["ruta"])
                codigo, salida, _ = correr(
                    [sys.executable, "-c",
                     f"import {modulo} as m; print('OK', len(dir(m)))"],
                    TIEMPO_IMPORT, extra=carpeta)
                if codigo == 0:
                    estado, detalle, extra = IMPORTA, f"import {modulo}: OK", {"modulo": modulo}
                else:
                    estado, detalle, extra = FALLA, f"import {modulo}: {salida.strip()[-400:]}", {"modulo": modulo}
            elif modo == "test":
                if args.sin_ejecutar:
                    estado, detalle, extra = SIN_HERRAMIENTA, "omitido (--sin-ejecutar)", {}
                else:
                    codigo, salida, _ = correr(
                        [sys.executable, "-m", "pytest", "-q", rel], TIEMPO_IMPORT)
                    # pytest devuelve 5 cuando el archivo no contiene pruebas (p. ej.
                    # un __init__.py vacio). Eso NO es un fallo: no hay nada que correr.
                    if codigo == 5:
                        estado = SIN_PRUEBAS
                        detalle = "no contiene pruebas (pytest: exit 5)"
                    else:
                        estado = TEST_OK if codigo == 0 else FALLA
                        detalle = salida.strip()[-400:] or f"pytest salida {codigo}"
                    extra = {"exit_pytest": codigo}
            elif modo == "streamlit":
                # Un app de Streamlit no se ejecuta con `python`: se arranca en
                # modo headless y se comprueba que llegue a servir.
                if args.sin_ejecutar:
                    estado, detalle, extra = SIN_HERRAMIENTA, "omitido (--sin-ejecutar)", {}
                else:
                    codigo, salida, seg = correr(
                        [sys.executable, "-m", "streamlit", "run", rel,
                         "--server.headless=true", "--server.port=8599",
                         "--browser.gatherUsageStats=false"], TIEMPO_STREAMLIT+40)
                    arranco = ("You can now view" in salida) or ("Network URL" in salida)
                    if arranco:
                        estado = CORRE
                        detalle = f"streamlit sirvio la app ({seg:.0f} s de arranque)"
                    else:
                        estado = FALLA
                        detalle = salida.strip()[-500:]
                    extra = {"arranco": arranco}
            else:  # script normal
                if args.sin_ejecutar:
                    estado, detalle, extra = SIN_HERRAMIENTA, "omitido (--sin-ejecutar)", {}
                else:
                    codigo, salida, seg = correr(
                        [sys.executable, rel], TIEMPO_SCRIPT)
                    if codigo == 0:
                        estado = CORRE
                    elif codigo == 3:
                        estado = SIN_DATOS
                    else:
                        estado = FALLA
                    ultimas = [l for l in salida.strip().splitlines() if l.strip()][-6:]
                    detalle = f"exit={codigo} ({seg:.0f} s) | " + " | ".join(l[:120] for l in ultimas)
                    extra = {"exit": codigo, "segundos": round(seg, 1)}

        # Categoria F1-F5: los legados son F5 por definicion; el resto de fallos se
        # clasifican con reglas explicitas sobre la traza.
        if estado == FALLA:
            categoria, motivo = clasificar_fallo(detalle, extra, modo, DECLARADAS)
        elif estado == LEGACY:
            categoria, motivo = F5, "esta en legacy_referencia/ por decision del proyecto"
        elif estado == SIN_DATOS:
            categoria, motivo = F1, "sale con codigo 3: falta el dataset de entrada"
        else:
            categoria, motivo = "", ""

        print(f"  -> {estado}")
        if categoria:
            print(f"     [{categoria}] {motivo}")
        print(f"     {detalle[:600]}")
        resultados.append({
            "n": i, "ruta": fila["ruta"], "lenguaje": lenguaje,
            "lineas": fila["lineas"], "carpeta": fila["carpeta"],
            "modo": modo, "estado": estado, "categoria": categoria,
            "motivo": motivo, "detalle": detalle,
            "ubicacion": "legacy_referencia" if es_legacy else "activo",
        })

    # ---------------------------------------------------------------- informe
    print("\n" + "=" * 78)
    print("TABLA DE LOS 51 ARTEFACTOS")
    print("=" * 78)
    print(f"  {'#':>2}  {'ruta':<62} {'lineas':>6}  estado")
    for r in resultados:
        print(f"  {r['n']:>2}  {r['ruta']:<62} {r['lineas']:>6}  {r['estado']}")

    print("\n" + "=" * 78)
    print("RESUMEN POR ESTADO")
    print("=" * 78)
    from collections import Counter
    cuenta = Counter(r["estado"] for r in resultados)
    for estado, n in cuenta.most_common():
        print(f"  {n:>3}  {estado}")

    activos = [r for r in resultados if r["ubicacion"] == "activo"]
    print(f"\n  artefactos activos (en repo_mejorado/): {len(activos)}")
    print(f"  artefactos en legacy_referencia/: "
          f"{len(resultados) - len(activos)}")

    print("\n" + "=" * 78)
    print("CLASIFICACION DE FALLOS (F1-F5)")
    print("=" * 78)
    por_categoria: dict[str, list[dict]] = {}
    for r in resultados:
        if r["categoria"]:
            por_categoria.setdefault(r["categoria"], []).append(r)
    for categoria in (F1, F2, F3, F4, F5):
        lista = por_categoria.get(categoria, [])
        print(f"\n  {categoria}: {len(lista)}")
        for r in lista:
            print(f"     - {r['ruta']}")
            print(f"       {r['motivo']}")

    print("\n" + "=" * 78)
    print("FALLOS (detalle)")
    print("=" * 78)
    fallos = [r for r in resultados if r["estado"] == FALLA]
    if not fallos:
        print("  ninguno")
    for r in fallos:
        print(f"\n  [{r['ruta']}]  ({r['lenguaje']}, modo={r['modo']})")
        print(f"    {r['detalle'][:700]}")

    # Veredicto sobre las versiones modernas: lo que de verdad se queria saber.
    print("\n" + "=" * 78)
    print("VEREDICTO")
    print("=" * 78)
    n_activos = len(activos)
    n_corren = sum(1 for r in activos if r["estado"] in (CORRE, IMPORTA, TEST_OK, SIN_PRUEBAS))
    n_sin_datos = sum(1 for r in activos if r["estado"] == SIN_DATOS)
    n_fallos = len([r for r in activos if r["estado"] == FALLA])
    n_f3 = len(por_categoria.get(F3, []))
    print(f"  artefactos ACTIVOS probados        : {n_activos}")
    print(f"  corren o se importan sin problema  : {n_corren}")
    print(f"  corren pero les faltan datos (F1)  : {n_sin_datos}")
    print(f"  fallan                             : {n_fallos}")
    print(f"  fallos por breaking change (F3)    : {n_f3}")

    # El nombre de la corrida, para que las dos tablas (versiones modernas vs
    # versiones fijadas por el lock) no se pisen.
    import importlib.metadata as _md
    try:
        _versiones = f"pandas {_md.version('pandas')}, numpy {_md.version('numpy')}, plotly {_md.version('plotly')}"
    except Exception:  # noqa: BLE001
        _versiones = "versiones desconocidas"
    with informe_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(resultados[0].keys()))
        w.writeheader()
        w.writerows(resultados)
    informe_json.write_text(json.dumps(
        {"entorno": {"python": sys.version.split()[0], "versiones": _versiones},
         "resultados": resultados}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  tabla escrita en {informe_csv.relative_to(RAIZ)}")

    if PRUEBA.exists():
        borrar_arbol(PRUEBA)
        print(f"  copia desechable eliminada")

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
