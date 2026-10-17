# -*- coding: utf-8 -*-
"""
verificar_arreglos.py
=====================

Verifica que los arreglos de `repo_mejorado/` estan aplicados y que el codigo
funciona. Tres niveles, de mas fuerte a mas debil, y cada uno dice que prueba:

NIVEL 1 — REAL (sin sustitutos)
  - `repo_auditado/` sigue con los 236 hashes intactos y sin archivos de mas.
  - Sintaxis: `ast.parse` sobre todos los `.py` de repo_mejorado y sobre cada
    celda de codigo de `docs/manual.ipynb`.
  - `src/exportacion.py`: se prueba el guardia de kaleido con objetos de prueba
    que lanzan los errores reales de plotly y con uno que funciona.
  - `src/analisis/diversidad.py`: se importa y se ejecuta `comparar_dane()`
    sobre los datos reales de 2021 y se contrasta con la evidencia versionada.
  - `src/ingesta.aviso_produccion_ausente()`: se llama de verdad.

NIVEL 2 — CON DOBLES DE PRUEBA (declarado)
  Este entorno NO tiene seaborn, plotly, kaleido, duckdb, openpyxl, nbformat ni
  red para instalarlos (pip se cuelga). Para poder EJECUTAR los scripts que los
  importan se usan dobles minimos en `_stubs/`, fuera de repo_mejorado. Prueban
  el flujo de control y los arreglos, NO el dibujo ni las consultas reales.

NIVEL 3 — NO VERIFICABLE AQUI (declarado)
  - `poetry.lock` no se puede regenerar: no hay poetry ni red.
  - La salida visual (PNG/Sankey) no se puede comprobar sin plotly+kaleido reales.

Uso:  python datos_originales/verificar_arreglos.py
"""

from __future__ import annotations

import ast
import csv
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.dont_write_bytecode = True     # importar el codigo NO debe dejar __pycache__

RAIZ = Path(__file__).resolve().parents[1]
AUDITADO = RAIZ / "datos_originales" / "repo_auditado"
MEJORADO = RAIZ / "datos_originales" / "repo_mejorado"
STUBS = RAIZ / "datos_originales" / "_stubs"
PRUEBA = RAIZ / "datos_originales" / "_prueba_ejecucion"

# El conjunto de archivos que los arreglos DEBEN tocar se DERIVA del script de
# arreglos, no se escribe a mano: asi esta comprobacion no puede quedarse
# desactualizada cuando se anade un arreglo.
sys.path.insert(0, str(RAIZ / "datos_originales"))
from aplicar_arreglos import ARREGLOS, REGENERADOS    # noqa: E402
from construir_repo_mejorado import LEGACY           # noqa: E402
from fs_robusto import borrar_arbol                  # noqa: E402

TOCADOS = ({ruta for _, ruta, _, _, _ in ARREGLOS}
           | REGENERADOS
           | {"docs/manual.ipynb"})
NUEVOS = {"datos/raw/README.md", "datos/processed/README.md",
          "models/README.md", "src/exportacion.py",
          "CHANGELOG.md", "legacy_referencia/README.md"}
LEGACY_SET = set(LEGACY)

fallos: list[str] = []
avisos: list[str] = []


def titulo(t: str) -> None:
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


# ---------------------------------------------------------------------------
# Dobles de prueba
# ---------------------------------------------------------------------------
SEABORN_STUB = '''"""Doble minimo de seaborn: solo lo que usan los scripts."""
import matplotlib.pyplot as plt


def set_theme(*a, **k):
    return None


def color_palette(*a, **k):
    return ["#1f77b4", "#ff7f0e", "#2ca02c"]


def heatmap(data, *a, **k):
    return plt.gca()


def barplot(*a, **k):
    return plt.gca()


def boxplot(*a, **k):
    return plt.gca()


def lineplot(*a, **k):
    return plt.gca()
'''

PLOTLY_GRAPH_OBJECTS = '''"""Doble minimo de plotly.graph_objects."""


class _Traza:
    def __init__(self, *a, **k):
        self.kwargs = k


class Sankey(_Traza):
    pass


class Bar(_Traza):
    pass


class Scatter(_Traza):
    pass


class Figure:
    def __init__(self, data=None, layout=None, **k):
        self.data = data if isinstance(data, list) else [data] if data else []
        self.layout = layout or {}

    def update_layout(self, **k):
        self.layout.update(k)
        return self

    def add_trace(self, t):
        self.data.append(t)
        return self

    def write_html(self, path, **k):
        Path_like = str(path)
        with open(Path_like, "w", encoding="utf-8") as fh:
            fh.write("<!-- HTML de prueba -->\\n")
        return None

    def write_image(self, path, **k):
        # Reproduce el fallo REAL de plotly cuando falta kaleido.
        raise RuntimeError(
            "Image export requires the Kaleido package, v1.0.0 or greater, "
            "which can be installed using pip:  $ pip install --upgrade \\"kaleido>=1\\"")


from pathlib import Path  # noqa: E402  (para el doble, no para el codigo real)
'''

DUCKDB_STUB = '''"""Doble minimo de duckdb."""


class DuckDBPyConnection:
    def execute(self, sql, *a, **k):
        raise RuntimeError("doble de prueba: no hay motor DuckDB real")

    def close(self):
        return None


def connect(*a, **k):
    return DuckDBPyConnection()
'''


FALTANTES: list[str] = []      # lo rellena preparar_stubs(); lo usa el resumen


def preparar_stubs() -> list[str]:
    """
    Crea dobles SOLO para las dependencias que falten de verdad.

    Antes se creaban siempre y, al ir primero en el PYTHONPATH, tapaban a las
    librerias reales: con seaborn/plotly/duckdb instalados la verificacion seguia
    probando los dobles, que es la prueba mas debil. Ahora, si una dependencia
    esta instalada se usa la de verdad; el doble queda como respaldo para
    entornos minimos.
    """
    import importlib.util

    faltantes = [m for m in ("seaborn", "plotly", "duckdb")
                 if importlib.util.find_spec(m) is None]

    # borrar_arbol (no shutil.rmtree): OneDrive deja los directorios como
    # reparse points de solo lectura y rmtree falla con [WinError 5].
    borrar_arbol(STUBS)
    # exist_ok: borrar_arbol deja la carpeta vacia si no puede borrarla
    # (OneDrive la mantiene abierta), asi que puede seguir existiendo.
    STUBS.mkdir(parents=True, exist_ok=True)
    if "seaborn" in faltantes:
        (STUBS / "seaborn.py").write_text(SEABORN_STUB, encoding="utf-8")
    if "plotly" in faltantes:
        (STUBS / "plotly").mkdir()
        (STUBS / "plotly" / "__init__.py").write_text("", encoding="utf-8")
        (STUBS / "plotly" / "graph_objects.py").write_text(
            PLOTLY_GRAPH_OBJECTS, encoding="utf-8")
    if "duckdb" in faltantes:
        (STUBS / "duckdb.py").write_text(DUCKDB_STUB, encoding="utf-8")

    (STUBS / "README.md").write_text(
        "# _stubs/\n\nDobles de prueba minimos para poder EJECUTAR los scripts de\n"
        "`repo_mejorado/` cuando el entorno no tiene la dependencia de verdad.\n"
        "Los genera `verificar_arreglos.py`, que solo crea los que faltan: si\n"
        "seaborn/plotly/duckdb estan instalados se usan los reales.\n"
        f"En esta corrida se usaron dobles para: {faltantes or 'ninguna'}.\n",
        encoding="utf-8")
    global FALTANTES
    FALTANTES = faltantes
    if faltantes:
        print(f"  [dobles] faltan de verdad: {', '.join(faltantes)}")
    else:
        print("  [dobles] ninguna: todas las dependencias estan instaladas, "
              "se usan las REALES")
    return faltantes


def entorno_con_stubs(base: Path) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(STUBS), str(base), str(base / "src")])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def correr(script: str, base: Path, timeout: int = 300) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(base / script)],
                       cwd=str(base), capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env=entorno_con_stubs(base), timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# ---------------------------------------------------------------------------
# NIVEL 1
# ---------------------------------------------------------------------------
def n1_limpieza() -> None:
    """
    `repo_mejorado/` debe ser exactamente `repo_auditado/` con los cambios
    declarados y NADA mas. Esta comprobacion existe porque la primera version del
    verificador EJECUTABA los scripts dentro de repo_mejorado y dejaba ahi las
    figuras y los CSV regenerados (con los dobles de prueba): el entregable
    quedaba contaminado sin que ninguna comprobacion lo notara.
    """
    titulo("NIVEL 1a — Limpieza: solo los archivos declarados cambian")
    import hashlib

    def h(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    en_aud = {p.relative_to(AUDITADO).as_posix(): p
              for p in AUDITADO.rglob("*") if p.is_file()}
    en_mej = {p.relative_to(MEJORADO).as_posix(): p
              for p in MEJORADO.rglob("*") if p.is_file()}

    gitkeeps = {k for k in en_aud if k.endswith(".gitkeep")}
    faltan, indebidos, sobrantes = [], [], []

    for rel, p in en_aud.items():
        if rel in gitkeeps:
            if rel in en_mej:
                sobrantes.append(f"{rel} (.gitkeep que debia eliminarse)")
            continue
        if rel in LEGACY_SET:
            destino = f"legacy_referencia/{rel}"
            if destino not in en_mej:
                faltan.append(destino)
            elif h(en_mej[destino]) != h(p):
                indebidos.append(destino)
            continue
        if rel not in en_mej:
            faltan.append(rel)
        elif h(en_mej[rel]) != h(p) and rel not in TOCADOS:
            indebidos.append(rel)

    for rel in en_mej:
        if "__pycache__" in rel or rel.endswith(".pyc"):
            sobrantes.append(f"{rel} (residuo de ejecucion)")
            continue
        if rel in NUEVOS:
            continue
        if rel.startswith("legacy_referencia/"):
            interno = rel[len("legacy_referencia/"):]
            if interno not in LEGACY_SET:
                sobrantes.append(f"{rel} (no declarado en legacy_referencia)")
            continue
        if rel in en_aud:
            continue
        sobrantes.append(f"{rel} (archivo no declarado)")

    # Los archivos nuevos declarados tambien deben EXISTIR. Sin esta comprobacion,
    # borrar CHANGELOG.md pasaba desapercibido: la comprobacion de sobrantes solo
    # miraba que no hubiera archivos de mas, no que estuvieran los de menos.
    for rel in sorted(NUEVOS):
        if rel not in en_mej:
            faltan.append(f"{rel} (archivo nuevo declarado y ausente)")

    print(f"  archivos en repo_auditado : {len(en_aud)}")
    print(f"  archivos en repo_mejorado : {len(en_mej)}")
    print(f"  cambios declarados        : {len(TOCADOS)} archivos + {len(NUEVOS)} nuevos")
    print(f"  .gitkeep eliminados       : {len(gitkeeps)}")
    print(f"  legacy apartados          : {len(LEGACY_SET)}")
    for etq, lista in (("faltan", faltan), ("alterados sin declarar", indebidos),
                       ("sobrantes", sobrantes)):
        if lista:
            print(f"  [x] {etq}: {len(lista)}")
            for x in lista[:10]:
                print(f"      {x}")
                fallos.append(f"limpieza: {etq} -> {x}")
    if not (faltan or indebidos or sobrantes):
        print(f"  -> PRUEBA: repo_mejorado = repo_auditado - {len(gitkeeps)} "
              f".gitkeep + {len(LEGACY_SET)} legacy apartados + {len(TOCADOS)} "
              f"arreglos declarados + {len(NUEVOS)} archivos nuevos, sin residuos")


def n1_auditado_intacto() -> None:
    titulo("NIVEL 1a — repo_auditado/ sigue siendo la prueba verbatim")
    r = subprocess.run([sys.executable, str(RAIZ / "datos_originales" /
                                           "verificar_hashes.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    print("\n".join(l for l in r.stdout.splitlines()
                    if l.strip().startswith(("identicos", "faltantes",
                                             "distintos", "sobrantes", "[OK]"))))
    if r.returncode != 0:
        fallos.append("repo_auditado/ no pasa la verificacion de hashes")
    else:
        print("  -> PRUEBA: los 236 archivos son identicos al commit 1528939")


def n1_sintaxis() -> None:
    titulo("NIVEL 1b — Sintaxis de todo el codigo de repo_mejorado/")
    n_py, n_legacy = 0, 0
    for p in sorted(MEJORADO.rglob("*.py")):
        if "legacy_referencia" in p.parts:
            # Los archivos legacy NO son Python valido a proposito: contienen
            # magias de Colab ("!pip install", "display()") que solo interpreta
            # el notebook. Por eso estan apartados y no se ejecutan.
            n_legacy += 1
            continue
        try:
            ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            n_py += 1
        except SyntaxError as e:
            fallos.append(f"sintaxis: {p.relative_to(MEJORADO)}:{e.lineno} {e.msg}")
            # Se informa AL INSTANTE: si un chequeo posterior revienta, un fallo
            # registrado en silencio se perderia (el resumen final no llegaria).
            print(f"  [x] SINTAXIS {p.relative_to(MEJORADO)}:{e.lineno}: {e.msg}")
    print(f"  .py con sintaxis valida: {n_py}")
    print(f"  excluidos (legacy_referencia, sintaxis Colab): {n_legacy}")

    nb = MEJORADO / "docs" / "manual.ipynb"
    n_celdas = 0
    d = json.loads(nb.read_text(encoding="utf-8"))
    for i, c in enumerate(d["cells"]):
        if c.get("cell_type") != "code":
            continue
        src = "".join(c.get("source", []))
        try:
            ast.parse(src)
            n_celdas += 1
        except SyntaxError as e:
            fallos.append(f"sintaxis: manual.ipynb celda {i}: {e.msg}")
            print(f"  [x] SINTAXIS manual.ipynb celda {i}: {e.msg}")
    print(f"  celdas de codigo de manual.ipynb validas: {n_celdas}")

    # --- Defectos en CODIGO EJECUTABLE: se comprueban con el arbol sintactico,
    # no con busqueda de texto. Buscar texto marcaba como fallo el docstring de
    # dimensional.py que EXPLICA la deprecacion de .fetchdf(), y no habria visto
    # una llamada escrita de otra forma.
    llamadas_malas = []
    for p in sorted(MEJORADO.rglob("*.py")):
        if "legacy_referencia" in p.parts or p.name == "exportacion.py":
            continue
        try:
            arbol = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue                      # ya reportado arriba
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call):
                continue
            f = nodo.func
            if not isinstance(f, ast.Attribute):
                continue
            if f.attr == "fetchdf":
                llamadas_malas.append(
                    f"{p.relative_to(MEJORADO)}:{nodo.lineno} llama a .fetchdf() "
                    f"(deprecado en duckdb 0.9)")
            if f.attr == "write_image":
                llamadas_malas.append(
                    f"{p.relative_to(MEJORADO)}:{nodo.lineno} llama a .write_image() "
                    f"sin pasar por exportacion.exportar_png")
    fallos.extend(llamadas_malas)
    for x in llamadas_malas:
        print(f"  [x] {x}")

    # --- Defectos que viven DENTRO DE CADENAS (el generador del manual escribe
    # codigo como texto): aqui la busqueda de texto SI es la herramienta correcta.
    dentro_de_cadenas = {
        'print(m["conteos"])': "manual: m['conteos'] sobre una tupla",
        "columna=\"NME_DEPARTAMENTO_RES_PR\"": "kwarg 'columna' inexistente",
        '["python3",': "python3 no existe en Windows",
    }
    generador = MEJORADO / "scripts" / "generar_manual.py"
    nb_txt = nb.read_text(encoding="utf-8")
    restos = []
    for pat, desc in dentro_de_cadenas.items():
        for etq, txt in (("scripts/generar_manual.py",
                          generador.read_text(encoding="utf-8")),
                         ("docs/manual.ipynb", nb_txt)):
            if pat in txt:
                restos.append(f"{etq}: {desc}")
    fallos.extend(restos)
    for x in restos:
        print(f"  [x] patron erroneo restante -> {x}")

    # --- Comprobaciones POSITIVAS: que el arreglo este, no solo que falte el
    # defecto. Sin esto, borrar el archivo entero tambien "pasaria".
    def contiene(ruta: Path, *fragmentos: str) -> None:
        txt = ruta.read_text(encoding="utf-8", errors="replace")
        for fr in fragmentos:
            if fr not in txt:
                fallos.append(f"falta el arreglo: '{fr}' en "
                              f"{ruta.relative_to(MEJORADO)}")
                print(f"  [x] falta '{fr}' en {ruta.relative_to(MEJORADO)}")

    print("  comprobaciones positivas de los arreglos:")
    contiene(MEJORADO / "src" / "exportacion.py", "def exportar_png")
    contiene(MEJORADO / "src" / "ingesta" / "__init__.py",
             "def aviso_produccion_ausente", "return 3")
    for s in ("sprint6_sankey_categoria.py", "sprint6_sankey_territorial.py"):
        contiene(MEJORADO / "scripts" / s, "exportar_png(")
    for s in ("sprint5_produccion.py", "sprint5_duckdb.py",
              "sprint6_ocde_composicion.py"):
        contiene(MEJORADO / "scripts" / s, "aviso_produccion_ausente", "-> int")
    contiene(MEJORADO / "scripts" / "sprint6_geografia_institucional.py",
             'sys.stdout.reconfigure(encoding="utf-8"')
    contiene(MEJORADO / "scripts" / "generar_manual.py",
             "[sys.executable,", 'col_geo="NME_DEPARTAMENTO_RES_PR"')
    # En el .ipynb el codigo va dentro de JSON, con las comillas escapadas: se
    # busca la forma sin comillas.
    contiene(nb, "[sys.executable,", "col_geo=")
    contiene(MEJORADO / "src" / "analisis" / "diversidad.py",
             'reindex(columns=["FEMENINO", "MASCULINO"]',
             "respuestas CONOCIDAS")
    contiene(MEJORADO / "src" / "modelo" / "dimensional.py",
             "def resumen_modelo(con: duckdb.DuckDBPyConnection) -> str")
    contiene(MEJORADO / "pyproject.toml", 'PyYAML', 'kaleido', 'nbformat')

    # --- F2-3: el enunciado del modelo estrella. Verificado sobre el esquema
    # real, tiene 9 TABLAS = 7 dimensiones + 1 tabla de hechos + 1 tabla puente.
    # El informe decia "nueve dimensiones"; eso es lo que corrigen los arreglos K.
    informe = MEJORADO / "informe_final.md"
    txt_informe = informe.read_text(encoding="utf-8", errors="replace")
    if "nueve dimensiones" in txt_informe:
        fallos.append("informe_final.md sigue diciendo 'nueve dimensiones'")
        print("  [x] informe_final.md sigue diciendo 'nueve dimensiones'")
    contiene(informe, "siete dimensiones", "tabla puente",
             "(nueve tablas en total)")

    print("    (si no hay lineas [x] arriba, todos los arreglos estan "
          "presentes en su sitio)")
    print("  -> PRUEBA: sintaxis valida, defectos de codigo ausentes (via AST), "
          "defectos en cadenas ausentes y arreglos presentes")


def n1_exportacion() -> None:
    titulo("NIVEL 1c — Guardia de kaleido (src/exportacion.py), prueba REAL")
    sys.path.insert(0, str(MEJORADO / "src"))
    from exportacion import exportar_png  # noqa: E402

    class FigSinKaleido:
        def write_image(self, ruta, **k):
            raise RuntimeError("Image export requires the Kaleido package, "
                               'v1.0.0 or greater, which can be installed '
                               'using pip:  $ pip install --upgrade "kaleido>=1"')

    class FigOk:
        def write_image(self, ruta, **k):
            Path(ruta).write_text("png de prueba", encoding="utf-8")

    class FigOtroError:
        def write_image(self, ruta, **k):
            raise ValueError("alguna otra cosa salio mal")

    # Caso REAL de kaleido 1.x: esta instalado pero el navegador no arranca. La
    # excepcion viene de choreographer y su mensaje NO menciona "kaleido", asi que
    # la primera version del guardia (que miraba el texto) la dejaba escapar y el
    # script moria igual. Esta prueba es la regresion de ese hallazgo.
    class BrowserFailedError(RuntimeError):
        pass
    BrowserFailedError.__module__ = "choreographer.browsers._errors"

    class FigSinNavegador:
        def write_image(self, ruta, **k):
            raise BrowserFailedError(
                "The browser seemed to close immediately after starting.")

    print("  caso 1: falta kaleido -> debe devolver False y NO lanzar")
    r1 = exportar_png(FigSinKaleido(), STUBS / "x.png", width=100)
    print(f"          devolvio {r1}")
    if r1 is not False:
        fallos.append("exportar_png no devolvio False sin kaleido")
    else:
        print("  -> PRUEBA: el script ya no aborta por falta de kaleido")

    print("  caso 1b: kaleido presente pero el NAVEGADOR no arranca "
          "(BrowserFailedError de choreographer) -> debe devolver False")
    r1b = exportar_png(FigSinNavegador(), STUBS / "x2.png", width=100)
    print(f"          devolvio {r1b}")
    if r1b is not False:
        fallos.append("exportar_png no reconoce el fallo del navegador "
                      "(BrowserFailedError de choreographer)")
    else:
        print("  -> PRUEBA: reconoce el fallo por el MODULO de la excepcion, "
              "no por el texto del mensaje")

    print("  caso 2: kaleido presente -> debe escribir y devolver True")
    r2 = exportar_png(FigOk(), STUBS / "y.png", width=100)
    if r2 is not True or not (STUBS / "y.png").exists():
        fallos.append("exportar_png no exporto con motor presente")
    else:
        print(f"          devolvio {r2} y creo el archivo")

    print("  caso 3: error NO relacionado con kaleido -> debe propagarse")
    try:
        exportar_png(FigOtroError(), STUBS / "z.png")
        fallos.append("exportar_png se trago un error ajeno a kaleido")
    except ValueError:
        print("  -> PRUEBA: solo absorbe los fallos de kaleido; el resto se ve")


def n1_diversidad() -> None:
    titulo("NIVEL 1d — comparar_dane() sobre datos reales, prueba REAL")
    sys.dont_write_bytecode = True          # no contaminar repo_mejorado
    sys.path.insert(0, str(MEJORADO / "src"))
    import pandas as pd
    from analisis.diversidad import comparar_dane
    from Transformacion import COLS_NUMERICAS, limpiar_texto, tratar_faltantes

    csv_fuente = (RAIZ / "datos_originales" / "datos_fuente" /
                  "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
    df = pd.read_csv(csv_fuente, dtype=str, keep_default_na=False, encoding="utf-8")
    for col in COLS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(",", ".", regex=False),
                                    errors="coerce")
    d21 = tratar_faltantes(limpiar_texto(df[df["ID_CONVOCATORIA"] == "21"].copy()))
    obtenido = comparar_dane(d21)

    ev = AUDITADO / "evidencias" / "diversidad_comparacion_dane.csv"
    with ev.open(encoding="utf-8", newline="") as fh:
        esperado = pd.DataFrame(list(csv.DictReader(fh)))

    ok = True
    for col in ["grupo", "n_minciencias_2021", "pct_minciencias",
                "pct_dane_2018", "razon_subrepresentacion"]:
        a = [str(x) for x in obtenido[col].tolist()]
        b = [str(x) for x in esperado[col].tolist()]
        if a != b:
            ok = False
            fallos.append(f"diversidad: columna {col} difiere de la evidencia")
            print(f"    [!] {col}: {a} != {b}")
    if ok:
        print("  -> PRUEBA: comparar_dane() reproduce la evidencia versionada "
              "fila por fila")
        print("            (afro 3,0x; indigena 7,9x; discapacidad 8,0x; "
              "victimas 8,6x)")
        print("            el comentario corregido describe la base que el "
              "codigo realmente usa")

    # El caso limite del KeyError tambien queda cubierto
    vacio = d21.copy()
    vacio["NME_GENERO_PR"] = "MASCULINO"
    from analisis.diversidad import interseccional_genero_etnia
    try:
        interseccional_genero_etnia(vacio)
        print("  -> PRUEBA: sin mujeres en ningun grupo ya no lanza KeyError")
    except KeyError as e:
        fallos.append(f"interseccional_genero_etnia sigue lanzando KeyError: {e}")


def n1_aviso_produccion() -> None:
    titulo("NIVEL 1e — aviso_produccion_ausente(), prueba REAL")
    sys.path.insert(0, str(MEJORADO / "src"))
    from ingesta import aviso_produccion_ausente
    print("  llamada real:")
    code = aviso_produccion_ausente(FileNotFoundError("Dataset de producción no encontrado"))
    print(f"  devolvio codigo {code}")
    if code != 3:
        fallos.append("aviso_produccion_ausente no devuelve 3")
    else:
        print("  -> PRUEBA: codigo 3, distinto de 1 (error real) y de 0 (exito)")


# ---------------------------------------------------------------------------
# NIVEL 2
# ---------------------------------------------------------------------------
def n2_scripts() -> None:
    titulo("NIVEL 2 — Ejecucion de los 6 scripts")
    faltantes = preparar_stubs()
    if faltantes:
        print("  AVISO: se sustituyen con dobles las dependencias ausentes "
              f"({', '.join(faltantes)}).")
        print("  Se prueba el FLUJO y los ARREGLOS, no el dibujo real.")
        print("  Para la prueba con librerias de verdad: "
              "python datos_originales/probar_librerias_reales.py")
    else:
        print("  Todas las dependencias estan instaladas: esta corrida usa las "
              "librerias REALES.")
    print("  Los scripts ESCRIBEN figuras y CSV, asi que se ejecutan sobre una")
    print("  copia desechable (_prueba_ejecucion) para no contaminar el entregable.")
    print("  Para pasar de la carga inicial se deja ahi el consolidado en")
    print("  datos/raw/investigadores_consolidado.csv (la ruta que prefiere")
    print("  cargar_consolidado()), asi no depende de openpyxl.\n")

    esperado = {
        # script: (codigos aceptables, descripcion de lo que se prueba)
        "scripts/sprint6_geografia_institucional.py":
            ({0}, "ya no muere con UnicodeEncodeError al imprimir la flecha"),
        "scripts/sprint6_sankey_territorial.py":
            ({0}, "ya no aborta sin kaleido: genera el HTML y avisa del PNG"),
        "scripts/sprint6_sankey_categoria.py":
            ({0}, "guardia de kaleido y recorrido de todos los pares de la entrada"),
        "scripts/sprint5_produccion.py":
            ({3}, "avisa de datos faltantes y sale con codigo 3, sin traceback"),
        "scripts/sprint6_ocde_composicion.py":
            ({3}, "aviso de datos faltantes y codigo 3, sin traceback"),
        "scripts/sprint5_duckdb.py":
            ({3}, "avisa de la base DuckDB ausente y sale con codigo 3"),
    }

    borrar_arbol(PRUEBA)
    shutil.copytree(MEJORADO, PRUEBA, dirs_exist_ok=True)
    fixture = PRUEBA / "datos" / "raw" / "investigadores_consolidado.csv"
    origen = PRUEBA / "datos" / "tarea_join" / "investigadores_consolidado.csv"
    try:
        if origen.exists():
            shutil.copy2(origen, fixture)
            print(f"  [fixture] consolidado en datos/raw/ "
                  f"({fixture.stat().st_size / 1e6:.1f} MB)\n")

        for script, (codes, desc) in esperado.items():
            # La copia trae los HTML del proyecto auditado. Sin esta foto previa,
            # contar los que EXISTEN despues hace creer que el script genero 5
            # pares cuando el consolidado versionado solo tiene 3 convocatorias
            # (2 pares). Se cuenta lo REGENERADO, no lo presente.
            carpeta_sankey = PRUEBA / "artifacts" / "sprint6_sankey"
            antes_html = {p: p.stat().st_mtime
                          for p in carpeta_sankey.glob("sankey_20*.html")}
            try:
                rc, salida = correr(script, PRUEBA)
            except subprocess.TimeoutExpired:
                fallos.append(f"{script}: se colgo (>300 s)")
                print(f"  [x] {script}: TIMEOUT")
                continue
            ok = rc in codes
            marca = "[ok]" if ok else "[x] "
            print(f"  {marca} {script}  exit={rc}  ({desc})")
            if not ok:
                fallos.append(f"{script}: exit {rc}, se esperaba {codes}")
                print("      --- ultimas lineas ---")
                for l in salida.strip().splitlines()[-8:]:
                    print(f"      {l[:130]}")
                continue
            if rc == 3 and "datos faltantes" not in salida:
                fallos.append(f"{script}: exit 3 sin aviso accionable")
            elif rc == 3:
                print("      -> aviso accionable presente")
            if "Traceback" in salida:
                fallos.append(f"{script}: imprime un traceback")
            else:
                print("      -> sin traceback")
            if script.endswith("sprint6_sankey_territorial.py"):
                if "kaleido" in salida:
                    print("      -> avisa de kaleido y continua")
                html = (PRUEBA / "artifacts" / "sprint6_sankey" /
                        "sankey_territorial.html")
                print(f"      -> HTML generado: {html.exists()}")
            if script.endswith("sprint6_sankey_categoria.py"):
                htmls = list(carpeta_sankey.glob("sankey_20*.html"))
                regenerados = [p for p in htmls
                               if antes_html.get(p) != p.stat().st_mtime]
                csv_fl = PRUEBA / "evidencias" / "sankey_transiciones.csv"
                print(f"      -> HTMLs de pares REGENERADOS: {len(regenerados)} "
                      f"(de {len(htmls)} presentes: el resto viene de la copia)")
                print(f"      -> CSV de flujos reescrito: {csv_fl.exists()}")
    finally:
        if PRUEBA.exists():
            borrar_arbol(PRUEBA)
            print("\n  [copia desechable] _prueba_ejecucion eliminada")


def main() -> int:
    print("VERIFICACION DE repo_mejorado/")
    print(f"  auditado (prueba)  : {AUDITADO.relative_to(RAIZ)}")
    print(f"  mejorado (trabajo) : {MEJORADO.relative_to(RAIZ)}")

    preparar_stubs()
    n1_limpieza()
    n1_auditado_intacto()
    n1_sintaxis()
    n1_exportacion()
    n1_diversidad()
    n1_aviso_produccion()
    n2_scripts()

    titulo("RESUMEN")
    print(f"  fallos : {len(fallos)}")
    for f in fallos:
        print(f"    [x] {f}")
    print(f"  avisos : {len(avisos)}")
    for a in avisos:
        print(f"    [!] {a}")
    print("\n  ALCANCE DE ESTA VERIFICACION (se declara, no se disimula):")
    if FALTANTES:
        print(f"    - Se sustituyeron con DOBLES: {', '.join(FALTANTES)}.")
        print("      Por eso no se probaron el dibujo ni las consultas reales.")
        print("      Con las dependencias instaladas, la prueba fuerte es:")
        print("        python datos_originales/probar_librerias_reales.py")
    else:
        print("    - Todas las dependencias estan instaladas: NO se uso ningun doble")
        print("      (seaborn, plotly, kaleido, duckdb, openpyxl, nbformat).")
        print("      Para la prueba con foco en librerias reales y salidas:")
        print("        python datos_originales/probar_librerias_reales.py")
    print("    - PNG/Sankey: si kaleido no logra arrancar un navegador, el script")
    print("      avisa y continua; el HTML y los CSV si se generan.")
    print("    - docs/manual.ipynb: se valida sintaxis y coherencia con el")
    print("      generador, no su corrida (3 secciones exigen produccion).")
    if (RAIZ / "datos_originales" / "repo_mejorado" / "poetry.lock").exists():
        print("    - poetry.lock: presente y preservado por el constructor.")
    if not fallos:
        print("\n[OK] Todos los arreglos verificables pasan.")
        return 0
    print("\n[x] Hay fallos.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
