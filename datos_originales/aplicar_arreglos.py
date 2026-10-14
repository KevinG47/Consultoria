# -*- coding: utf-8 -*-
"""
aplicar_arreglos.py
===================

Aplica a `repo_mejorado/` los arreglos diagnosticados en las 51 fichas de
`documentacion_auditoria/data/analisis_codigo/` y en el criterio 3
(`latex/objetivo_3/secciones/03_codigo.tex`).

Por que un script de parches y no ediciones sueltas
---------------------------------------------------
1. Es **reproducible**: `construir_repo_mejorado.py` + `aplicar_arreglos.py`
   regeneran la version mejorada desde cero.
2. Es **verificable**: cada parche declara su ancla y el script **falla** si el
   ancla no aparece exactamente una vez, en lugar de aplicar un cambio a ciegas.
3. Es **auditable**: cada parche lleva su justificacion y la cita de la ficha.

Los arreglos NO se aplican sobre `repo_auditado/` (eso destruiria la prueba y
romperia los 236 hashes del manifiesto).

Uso
---
    python datos_originales/aplicar_arreglos.py --listar   # solo enumera
    python datos_originales/aplicar_arreglos.py            # aplica
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]
REPO = RAIZ / "datos_originales" / "repo_mejorado"

# ===========================================================================
# ARREGLOS
# Cada entrada: (id, ruta, justificacion, texto_original, texto_nuevo)
# `texto_original` debe aparecer EXACTAMENTE UNA VEZ en el archivo.
# ===========================================================================

# --- Modulo nuevo: exportacion tolerante a la ausencia de kaleido ----------
EXPORTACION_PY = '''"""
exportacion.py
==============

Exportacion de figuras a PNG tolerando la ausencia del motor de imagen.

`plotly` genera el HTML por si mismo, pero para exportar un PNG necesita
`kaleido`. Sin kaleido, `fig.write_image(...)` lanza RuntimeError (o ValueError,
segun la version) y el script abortaba DESPUES de haber generado el HTML, de modo
que se perdia el resto del trabajo y el fallo parecia un bug del script.

Aqui la exportacion a PNG es *best-effort*: si falta el motor se avisa con el
comando exacto para instalarlo y se continua con el resto de las salidas. Solo se
absorben los fallos relacionados con kaleido; cualquier otro error se propaga.
"""

from __future__ import annotations

from pathlib import Path

MENSAJE = ('falta kaleido, el motor de exportacion de imagenes de plotly. '
           'Instalalo con:  pip install "kaleido>=1"')


def exportar_png(fig, ruta, **kwargs) -> bool:
    """
    Exporta `fig` a PNG. Devuelve True si lo consiguio y False si falta kaleido.

    En el segundo caso imprime un aviso accionable y NO interrumpe el script: el
    HTML ya esta generado y las demas salidas siguen siendo utiles.
    """
    try:
        fig.write_image(ruta, **kwargs)
        return True
    except (ImportError, ModuleNotFoundError) as exc:
        _avisar(ruta, exc)
        return False
    except (RuntimeError, ValueError) as exc:
        # plotly senala la ausencia del motor con RuntimeError o ValueError; si el
        # mensaje no menciona kaleido es otro problema y debe verse tal cual.
        if "kaleido" not in str(exc).lower():
            raise
        _avisar(ruta, exc)
        return False


def _avisar(ruta, exc) -> None:
    detalle = str(exc).splitlines()[0][:140] if str(exc) else type(exc).__name__
    print(f"      [aviso] no se pudo escribir {Path(ruta).name}: {MENSAJE}")
    print(f"              detalle: {type(exc).__name__}: {detalle}")
    print("              el HTML SI se genero; solo falta la imagen.")
'''

# --- Helper de datos de produccion ausentes (una sola fuente del texto) ----
HELPER_PRODUCCION = '''

def aviso_produccion_ausente(exc: Exception) -> int:
    """
    Avisa de que falta el dataset de produccion y devuelve el codigo de salida 3.

    `cargar_produccion()` necesita `datos/raw/produccion_grupos.csv` (~1,2 GB),
    que NO se versiona en el repositorio. Sin el, los scripts de produccion no
    pueden producir sus salidas: antes morian con un traceback que parecia un bug
    de codigo. Ahora informan y terminan con un codigo distinto de 1 para que
    quien orqueste pueda distinguir "faltan datos" de "el script fallo".

    El texto vive aqui, junto a `cargar_produccion()`, para no repetirlo en los
    tres scripts que la usan.
    """
    print("\\n" + "=" * 70)
    print("[datos faltantes] no se puede continuar sin el dataset de produccion")
    print("=" * 70)
    print(f"  detalle: {exc}")
    print("  El archivo NO esta versionado (~1,2 GB). Para obtenerlo:")
    print("      python -m src.ingesta.produccion")
    print("  Requiere conexion a la API de Socrata. Sin el, este script no puede")
    print("  generar sus tablas ni figuras: se prefiere avisar antes que dejar")
    print("  evidencia parcial que parezca completa.")
    print("=" * 70)
    return 3
'''

ARREGLOS: list[tuple[str, str, str, str, str]] = [

    # =====================================================================
    # A. Kaleido: los dos scripts que abortaban en fig.write_image()
    # =====================================================================
    ("A1", "scripts/sprint6_sankey_categoria.py",
     "Ficha sprint6_sankey_categoria.py:146-147: 'write_image sin comprobacion de "
     "kaleido: dependencia implicita que rompe la ejecucion en entornos minimos'. "
     "El script ya habia escrito el HTML y abortaba despues. Se delega en "
     "src/exportacion.exportar_png, que avisa y continua.",
     """        fig.write_image(ARTIFACTS / f"{nombre}.png",
                        width=1100, height=520, scale=2)""",
     """        exportar_png(fig, ARTIFACTS / f"{nombre}.png",
                     width=1100, height=520, scale=2)"""),

    ("A2", "scripts/sprint6_sankey_categoria.py",
     "Import del helper de exportacion.",
     "from Transformacion import transformar",
     "from Transformacion import transformar\nfrom exportacion import exportar_png"),

    ("A3", "scripts/sprint6_sankey_territorial.py",
     "Ficha sprint6_sankey_territorial.py:125-129: misma dependencia implicita de "
     "kaleido; el log del pipeline auditado registra 'RuntimeError: Image export "
     "requires the Kaleido package' con EXIT=1.",
     """    fig.write_image(ARTIFACTS / "sankey_territorial.png",
                     width=1200, height=620, scale=2)""",
     """    exportar_png(fig, ARTIFACTS / "sankey_territorial.png",
                 width=1200, height=620, scale=2)"""),

    ("A4", "scripts/sprint6_sankey_territorial.py",
     "Import del helper de exportacion.",
     "import pandas as pd\nimport plotly.graph_objects as go",
     "import pandas as pd\nimport plotly.graph_objects as go\n\nsys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / \"src\"))"
     "\nfrom exportacion import exportar_png  # noqa: E402"),

    # =====================================================================
    # B. UnicodeEncodeError en consola Windows (geografia)
    # =====================================================================
    ("B1", "scripts/sprint6_geografia_institucional.py",
     "Ficha del script: 'UnicodeEncodeError: flecha U+2192 en print, Windows "
     "cp1252' (EXIT=1 en el log del pipeline). El script imprime 'residencia -> "
     "institucion' con la flecha real. Reconfigurar stdout a UTF-8 arregla TODOS "
     "los print de una vez, en lugar de reescribir cada mensaje.",
     'ROOT = pathlib.Path(__file__).resolve().parent.parent\nsys.path.insert(0, str(ROOT / "src"))',
     'ROOT = pathlib.Path(__file__).resolve().parent.parent\nsys.path.insert(0, str(ROOT / "src"))\n\n'
     '# La consola de Windows usa cp1252 y los mensajes llevan "->" (U+2192): sin\n'
     '# esto el script muere con UnicodeEncodeError al imprimir el paso [3/5].\n'
     'sys.stdout.reconfigure(encoding="utf-8", errors="replace")\n'
     'sys.stderr.reconfigure(encoding="utf-8", errors="replace")'),

    # =====================================================================
    # C. Datos de produccion ausentes: los tres scripts que morian con traceback
    # =====================================================================
    ("C1", "src/ingesta/__init__.py",
     "Ficha src/ingesta/__init__.py:44-48: 'cargar_produccion() lanza "
     "FileNotFoundError sin alternativa; en el clon todos los scripts sprint5/"
     "sprint6 de produccion mueren en el arranque'. Se anyade un helper con el "
     "aviso accionable y el codigo de salida 3.",
     '''def cargar_produccion() -> pd.DataFrame:''',
     HELPER_PRODUCCION.strip() + '''


def cargar_produccion() -> pd.DataFrame:'''),

    ("C2", "scripts/sprint5_produccion.py",
     "Ficha del script: 'NO ejecutable tal cual con el clon: cargar_produccion() "
     "lanza FileNotFoundError porque datos/raw/produccion_grupos.csv esta "
     "gitignored y ausente'. Arreglo minimo: avisar y salir con codigo 3 en vez "
     "de un traceback.",
     """def main() -> None:
    print("[1/8] Cargando datasets...")
    inv = transformar(cargar_consolidado())
    prod = normalizar_produccion(cargar_produccion())""",
     """def main() -> int:
    print("[1/8] Cargando datasets...")
    inv = transformar(cargar_consolidado())
    try:
        prod = normalizar_produccion(cargar_produccion())
    except FileNotFoundError as exc:
        return aviso_produccion_ausente(exc)"""),

    ("C3", "scripts/sprint5_produccion.py",
     "Import del helper y salida con codigo 0 bien definida.",
     "from ingesta import cargar_consolidado, cargar_produccion",
     "from ingesta import (aviso_produccion_ausente, cargar_consolidado,\n                     cargar_produccion)"),

    ("C4", "scripts/sprint5_produccion.py",
     "main() ahora devuelve codigo de salida.",
     '''    print(f"\\nFiguras : {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs    : {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()''',
     '''    print(f"\\nFiguras : {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs    : {EVIDENCIAS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())'''),

    ("C5", "scripts/sprint5_duckdb.py",
     "Dos causas de fallo: el dataset de produccion y la base DuckDB previa. La "
     "comprobacion de la base ya existia pero lanzaba una excepcion; ahora ambas "
     "informan y salen con codigo 3.",
     '''def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"No existe {DB_PATH}. Ejecute primero: python scripts/sprint2_duckdb.py"
        )

    con = duckdb.connect(str(DB_PATH))
    construir_tablas(con)''',
     '''def main() -> int:
    if not DB_PATH.exists():
        print("\\n" + "=" * 70)
        print("[datos faltantes] no existe la base DuckDB del modelo estrella")
        print("=" * 70)
        print(f"  falta: {DB_PATH}")
        print("  La base se regenera (no se versiona, *.duckdb esta en .gitignore):")
        print("      python scripts/sprint2_duckdb.py")
        print("=" * 70)
        return 3

    con = duckdb.connect(str(DB_PATH))
    try:
        construir_tablas(con)
    except FileNotFoundError as exc:
        con.close()
        return aviso_produccion_ausente(exc)'''),

    ("C6", "scripts/sprint5_duckdb.py",
     "Import del helper.",
     "from ingesta import cargar_produccion",
     "from ingesta import aviso_produccion_ausente, cargar_produccion"),

    ("C7", "scripts/sprint5_duckdb.py",
     "fetchdf() esta deprecado desde duckdb 0.9.0 (ficha del script:110) y el "
     "cierre de la conexion no estaba protegido (ficha :97-123). Se usa .df() y "
     "try/finally.",
     '''    con = duckdb.connect(str(DB_PATH))
    try:
        construir_tablas(con)
    except FileNotFoundError as exc:
        con.close()
        return aviso_produccion_ausente(exc)

    print("\\n--- Consultas de validación ---\\n")
    lineas = [f"Modelo extendido — Sprint 5 (Producción)\\n{'='*55}\\n"]
    for nombre, sql in CONSULTAS_VALIDACION.items():
        sep = f"\\n{'-'*55}\\n{nombre}\\n{'-'*55}"
        print(sep)
        df = con.execute(sql).fetchdf()
        print(df.to_string(index=False))
        lineas.append(sep)
        lineas.append(df.to_string(index=False))

    reporte = EVIDENCIAS / "duckdb_resumen_sprint5.txt"
    reporte.write_text("\\n".join(lineas), encoding="utf-8")
    con.close()
    print(f"\\nDB     : {DB_PATH.relative_to(ROOT)}")
    print(f"Reporte: {reporte.relative_to(ROOT)}")


if __name__ == "__main__":
    main()''',
     '''    con = duckdb.connect(str(DB_PATH))
    try:
        try:
            construir_tablas(con)
        except FileNotFoundError as exc:
            return aviso_produccion_ausente(exc)

        print("\\n--- Consultas de validación ---\\n")
        lineas = [f"Modelo extendido — Sprint 5 (Producción)\\n{'='*55}\\n"]
        for nombre, sql in CONSULTAS_VALIDACION.items():
            sep = f"\\n{'-'*55}\\n{nombre}\\n{'-'*55}"
            print(sep)
            df = con.execute(sql).df()          # .fetchdf() quedo deprecado en duckdb 0.9
            print(df.to_string(index=False))
            lineas.append(sep)
            lineas.append(df.to_string(index=False))

        reporte = EVIDENCIAS / "duckdb_resumen_sprint5.txt"
        reporte.write_text("\\n".join(lineas), encoding="utf-8")
        print(f"\\nDB     : {DB_PATH.relative_to(ROOT)}")
        print(f"Reporte: {reporte.relative_to(ROOT)}")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())'''),

    ("C8", "scripts/sprint6_ocde_composicion.py",
     "Ficha del script: 'NO ejecutable tal cual con el clon: cargar_produccion() "
     "falla por ausencia de datos/raw/produccion_grupos.csv (gitignored)'.",
     """def main() -> None:
    print("[1/5] Cargando datasets...")
    inv = transformar(cargar_consolidado())
    prod = normalizar_produccion(cargar_produccion())""",
     """def main() -> int:
    print("[1/5] Cargando datasets...")
    inv = transformar(cargar_consolidado())
    try:
        prod = normalizar_produccion(cargar_produccion())
    except FileNotFoundError as exc:
        return aviso_produccion_ausente(exc)"""),

    ("C9", "scripts/sprint6_ocde_composicion.py",
     "Import del helper.",
     "from ingesta import cargar_consolidado, cargar_produccion",
     "from ingesta import (aviso_produccion_ausente, cargar_consolidado,\n                     cargar_produccion)"),

    ("C10", "scripts/sprint6_ocde_composicion.py",
     "main() devuelve codigo de salida.",
     '''    print(f"\\nFiguras: {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs:    {EVIDENCIAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()''',
     '''    print(f"\\nFiguras: {ARTIFACTS.relative_to(ROOT)}")
    print(f"CSVs:    {EVIDENCIAS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())'''),

    # =====================================================================
    # D. sprint2_duckdb: fetchdf deprecado, reporte incompleto, cierre sin proteger
    # =====================================================================
    ("D1", "scripts/sprint2_duckdb.py",
     "Tres bugs de la ficha: :110 fetchdf() deprecado; :104 resumen_modelo(con) "
     "imprime a stdout pero NO se agrega a lineas_reporte, asi que la evidencia "
     "guardada omite el resumen que el propio docstring declara como validacion; "
     ":97-123 sin try/finally (una excepcion deja la conexion abierta).",
     '''def main() -> None:
    print("[1/3] Cargando y transformando datos...")
    df = transformar(cargar_consolidado())
    print(f"      Shape: {df.shape}")

    print("\\n[2/3] Construyendo modelo estrella en DuckDB...")
    con = cargar_en_duckdb(df, path=DB_PATH, verbose=True)
    resumen_modelo(con)

    print("\\n[3/3] Ejecutando consultas de validacion...\\n")
    lineas_reporte = [f"Modelo estrella — observatorio.duckdb\\n{'='*50}\\n"]

    for nombre, sql in CONSULTAS.items():
        resultado = con.execute(sql).fetchdf()
        separador = f"\\n{'-'*50}\\n{nombre}\\n{'-'*50}"
        print(separador)
        print(resultado.to_string(index=False))
        lineas_reporte.append(separador)
        lineas_reporte.append(resultado.to_string(index=False))

    # Guardar reporte de texto
    reporte_path = EVIDENCIAS / "duckdb_resumen_modelo.txt"
    reporte_path.write_text("\\n".join(lineas_reporte), encoding="utf-8")

    con.close()
    print(f"\\nBase de datos : {DB_PATH.relative_to(ROOT)}")
    print(f"Reporte       : {reporte_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()''',
     '''def main() -> int:
    print("[1/3] Cargando y transformando datos...")
    df = transformar(cargar_consolidado())
    print(f"      Shape: {df.shape}")

    print("\\n[2/3] Construyendo modelo estrella en DuckDB...")
    con = cargar_en_duckdb(df, path=DB_PATH, verbose=True)
    try:
        # El resumen del modelo se imprime Y se guarda: antes solo se imprimia y
        # la evidencia versionada lo omitia.
        resumen = resumen_modelo(con)

        print("\\n[3/3] Ejecutando consultas de validacion...\\n")
        lineas_reporte = [f"Modelo estrella — observatorio.duckdb\\n{'='*50}\\n"]
        if resumen:
            lineas_reporte.append(str(resumen))
            lineas_reporte.append("")

        for nombre, sql in CONSULTAS.items():
            resultado = con.execute(sql).df()   # .fetchdf() quedo deprecado en duckdb 0.9
            separador = f"\\n{'-'*50}\\n{nombre}\\n{'-'*50}"
            print(separador)
            print(resultado.to_string(index=False))
            lineas_reporte.append(separador)
            lineas_reporte.append(resultado.to_string(index=False))

        # Guardar reporte de texto
        reporte_path = EVIDENCIAS / "duckdb_resumen_modelo.txt"
        reporte_path.write_text("\\n".join(lineas_reporte), encoding="utf-8")

        print(f"\\nBase de datos : {DB_PATH.relative_to(ROOT)}")
        print(f"Reporte       : {reporte_path.relative_to(ROOT)}")
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())'''),

    # =====================================================================
    # E. diversidad.py: la contradiccion comentario-codigo y dos casos limite
    # =====================================================================
    ("E1", "src/analisis/diversidad.py",
     "Ficha src/analisis/diversidad.py:78-79: el comentario manda excluir "
     "'NINGUN GRUPO ETNICO' del denominador y el codigo NO lo hace. VERIFICADO "
     "con los datos reales que el CODIGO es el correcto y el comentario el "
     "erroneo: la referencia DANE son porcentajes de la poblacion TOTAL, y "
     "'NINGUN GRUPO ETNICO' (19 674 de 20 423 respuestas, el 96 %) es una "
     "respuesta declarada, no un dato faltante. Excluirla daria 'afro 72 %' "
     "(razon 0,1x) frente al 2,22 % real (razon 3,0x), que es la cifra publicada "
     "y coincide con evidencias/diversidad_comparacion_dane.csv. Se corrige el "
     "comentario y se documenta la base.",
     '''    # Etnia: excluir "NINGUN GRUPO ETNICO" del denominador para ver minorias
    etnia = df_2021[df_2021["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE"]
    n_etnia_resp = len(etnia)''',
     '''    # Etnia: denominador = respuestas CONOCIDAS, es decir todas menos
    # "NO DISPONIBLE". Se conservan "NINGUN GRUPO ETNICO" y "BLANCO O MESTIZO"
    # porque son respuestas declaradas (el 96 % de los registros de 2021), no
    # datos faltantes, y porque DANE_REFERENCIA["etnia"] son porcentajes de la
    # POBLACION TOTAL: la base comparable es el total de respuestas conocidas.
    # Excluir a la mayoria mezclaria bases (seria "que proporcion de las
    # minorias es afro" contra "que proporcion del pais es afro") y daria
    # resultados absurdos: afro pasaria del 2,22 % al 72 %.
    etnia = df_2021[df_2021["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE"]
    n_etnia_resp = len(etnia)'''),

    ("E2", "src/analisis/diversidad.py",
     "Ficha :145: d['FEMENINO'] puede lanzar KeyError si ningun grupo etnico "
     "tiene mujeres, porque unstack(fill_value=0) no crea la columna.",
     '''        .assign(total=lambda d: d.sum(axis=1))
        .assign(pct_femenino=lambda d: (d["FEMENINO"] / d["total"] * 100).round(1))''',
     '''        .assign(total=lambda d: d.sum(axis=1))
        # reindex garantiza que existan ambas columnas de genero: si ningun grupo
        # tiene mujeres, unstack no crea 'FEMENINO' y d["FEMENINO"] lanzaria
        # KeyError (ficha :145).
        .reindex(columns=["FEMENINO", "MASCULINO"], fill_value=0)
        .assign(total=lambda d: d.sum(axis=1))
        .assign(pct_femenino=lambda d: (d["FEMENINO"] / d["total"] * 100).round(1))'''),

    ("E3", "src/analisis/diversidad.py",
     "La columna se llama pct_dane_2018 pero la referencia mezcla DANE 2018 "
     "(etnia, discapacidad) y RUV 2021 (victimas). Se documenta la fuente real "
     "para que la etiqueta no enganye a quien lea el CSV o la figura.",
     '''# Proporciones poblacionales de referencia (DANE 2018 / RUV 2021)
DANE_REFERENCIA = {''',
     '''# Proporciones poblacionales de referencia.
# OJO con la etiqueta: la columna de salida se llama `pct_dane_2018` por
# compatibilidad con sprint4_diversidad.py, streamlit_app.py y la evidencia ya
# versionada (evidencias/diversidad_comparacion_dane.csv), pero la referencia NO
# es toda de 2018: la etnia y la discapacidad son del censo DANE 2018 y las
# victimas del conflicto son del RUV 2021 sobre poblacion 2021. Se mantiene el
# nombre por contrato entre archivos y se documenta aqui la fuente de cada uno.
DANE_REFERENCIA = {'''),

    # =====================================================================
    # F. generar_manual.py: los tres bugs que se propagan al manual.ipynb
    # =====================================================================
    ("F1", "scripts/generar_manual.py",
     "Ficha de generar_manual.py:197 (y docs/manual.ipynb): "
     "matrices_todos_periodos() devuelve {periodo: (conteos, probs)} y la celda "
     "hace m['conteos'] sobre una tupla -> TypeError al ejecutar el notebook.",
     '''for periodo, m in matrices.items():
    print(f"\\\\n{periodo}")
    print(m["conteos"])''',
     '''for periodo, m in matrices.items():
    conteos, _probs = m      # matrices_todos_periodos devuelve (conteos, probs)
    print(f"\\\\n{periodo}")
    print(conteos)'''),

    ("F2", "scripts/generar_manual.py",
     "Ficha :251: hhi_por_convocatoria() recibe el kwarg 'columna', pero el "
     "parametro real es 'col_geo' -> TypeError: unexpected keyword argument.",
     'hhi = hhi_por_convocatoria(inv_clean, columna="NME_DEPARTAMENTO_RES_PR")',
     'hhi = hhi_por_convocatoria(inv_clean, col_geo="NME_DEPARTAMENTO_RES_PR")'),

    ("F3", "scripts/generar_manual.py",
     "Ficha :213, :318, :357 y :509: las celdas del manual invocan 'python3', que "
     "no existe en Windows (el proyecto vive en Windows) -> FileNotFoundError. Se "
     "usa sys.executable, que es el interprete en uso en cualquier plataforma.",
     'subprocess.run(["python3", "scripts/sprint6_sankey_categoria.py"], cwd=ROOT, check=True)',
     'subprocess.run([sys.executable, "scripts/sprint6_sankey_categoria.py"], cwd=ROOT, check=True)'),

    ("F4", "scripts/generar_manual.py",
     "Mismo arreglo de python3 -> sys.executable (geografia).",
     'subprocess.run(["python3", "scripts/sprint6_geografia_institucional.py"],',
     'subprocess.run([sys.executable, "scripts/sprint6_geografia_institucional.py"],'),

    ("F5", "scripts/generar_manual.py",
     "Mismo arreglo de python3 -> sys.executable (sankey territorial).",
     'subprocess.run(["python3", "scripts/sprint6_sankey_territorial.py"], cwd=ROOT, check=True)',
     'subprocess.run([sys.executable, "scripts/sprint6_sankey_territorial.py"], cwd=ROOT, check=True)'),

    ("F6", "scripts/generar_manual.py",
     "Mismo arreglo de python3 -> sys.executable (ocde).",
     'subprocess.run(["python3", "scripts/sprint6_ocde_composicion.py"], cwd=ROOT, check=True)',
     'subprocess.run([sys.executable, "scripts/sprint6_ocde_composicion.py"], cwd=ROOT, check=True)'),

    # =====================================================================
    # G. streamlit_app.py: cierre de la app por ValueError
    # =====================================================================
    # =====================================================================
    # G. streamlit_app.py: cierre de la app por ValueError
    # =====================================================================
    ("G1", "streamlit_app.py",
     "Ficha streamlit_app.py: 'Seccion 3: hhi_por_convocatoria(...).reset_index() "
     "devuelve 5 columnas (index + ANO_CONVO_INT + hhi + n_total + n_territorios) "
     "y luego hhi_df.columns = [Año, HHI] lanza ValueError'. Es un cierre de la "
     "app en la pestana de territorio.",
     '''            hhi_df = hhi_por_convocatoria(df, col_geo=col).reset_index()
            hhi_df.columns = ["Año", "HHI"]''',
     '''            hhi_df = hhi_por_convocatoria(df, col_geo=col).reset_index()
            # hhi_por_convocatoria devuelve mas de dos columnas (HHI, n_total,
            # n_territorios): reasignar nombres a ciegas lanzaba ValueError y
            # cerraba la app. Se renombran por nombre, no por posicion.
            hhi_df = hhi_df.rename(columns={"ANO_CONVO_INT": "Año", "hhi": "HHI"})[
                ["Año", "HHI"]]'''),

    # =====================================================================
    # H. Dependencias: el codigo importa paquetes que el proyecto no declara
    # =====================================================================
    ("H1", "pyproject.toml",
     "Verificado con grep de imports: el codigo usa pyyaml (minciencias.py:19, "
     "produccion.py:24), nbformat (generar_manual.py:16), IPython (celdas del "
     "manual generado) y kaleido (write_image de los dos sankey) y NINGUNO esta "
     "declarado; openpyxl solo estaba en requirements.txt. Ademas las 4 ultimas "
     "dependencias estaban indentadas de forma inconsistente (inofensivo en TOML, "
     "pero enganya al leer).",
     '''scikit-learn = "^1.4"
    sodapy = "^2.2"
    duckdb = "^1.0"
    networkx = "^3.2"
    pyvis = "^0.3"''',
     '''scikit-learn = "^1.4"
sodapy = "^2.2"
duckdb = "^1.0"
networkx = "^3.2"
pyvis = "^0.3"
# Anadidas en la version mejorada: el codigo las importa y no estaban declaradas.
openpyxl = "^3.1"      # pandas.read_excel: cargar_consolidado() cae al XLSX
PyYAML = "^6.0"        # src/ingesta/minciencias.py:19 y src/ingesta/produccion.py:24
kaleido = "^1.0"       # plotly: fig.write_image() en scripts/sprint6_sankey_*.py
nbformat = "^5.9"      # scripts/generar_manual.py:16
ipython = "^8.0"       # celdas del manual generado (IPython.display.IFrame)'''),

    # =====================================================================
    # I. dimensional.py: la tercera llamada a fetchdf() y el resumen perdido
    # =====================================================================
    ("I1", "src/modelo/dimensional.py",
     "Dos defectos que las fichas senalan en los scripts pero que nacen aqui: "
     "(a) :283 usa .fetchdf(), deprecado desde duckdb 0.9.0, y es la TERCERA "
     "llamada deprecada del proyecto (las otras dos estan en sprint2_duckdb.py y "
     "sprint5_duckdb.py); (b) resumen_modelo() imprime pero NO devuelve nada, asi "
     "que el arreglo de agregar el resumen a la evidencia era cosmetico: se "
     "concatena 'None'. Ahora devuelve el texto sin duplicar el formateo.",
     '''def resumen_modelo(con: duckdb.DuckDBPyConnection) -> None:
    """Imprime un resumen del modelo estrella cargado."""
    print("\\n=== Modelo estrella en DuckDB ===")
    tablas = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY 1"
    ).fetchdf()
    for t in tablas["table_name"]:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:35s} {n:>8,} filas")''',
     '''def resumen_modelo(con: duckdb.DuckDBPyConnection) -> str:
    """
    Imprime un resumen del modelo estrella y DEVUELVE el mismo texto.

    Antes solo imprimia, y por eso la evidencia versionada
    (evidencias/duckdb_resumen_modelo.txt) omitia el resumen del modelo que el
    propio docstring de sprint2_duckdb.py declara como parte de la validacion
    (ficha scripts/sprint2_duckdb.py:104). Devolverlo permite agregarlo al
    reporte sin duplicar el formateo.

    Nota: .df() sustituye a .fetchdf(), deprecado desde duckdb 0.9.0.
    """
    lineas = ["\\n=== Modelo estrella en DuckDB ==="]
    tablas = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY 1"
    ).df()
    for t in tablas["table_name"]:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        lineas.append(f"  {t:35s} {n:>8,} filas")
    texto = "\\n".join(lineas)
    print(texto)
    return texto'''),

    # =====================================================================
    # J. Guia de la version mejorada al frente del README
    # =====================================================================
    ("J1", "README.md",
     "La carpeta necesita explicar QUE es y QUE funciona ahora, pero su README.md "
     "es el del proyecto auditado (318 lineas, citado por la auditoria: "
     "'README.md:268, Atipicos de edad: 22 casos (no 10)'), asi que NO se "
     "sobrescribe: se antepone una guia y el original queda intacto debajo. En "
     "repo_mejorado los numeros de linea NO son los del commit (29 archivos "
     "cambiaron); las citas de la auditoria se verifican sobre repo_auditado/.",
     '''# Observatorio MinCiencias — Investigadores Reconocidos

> **Ustadistica** -- Consultoria e Investigacion . Universidad Santo Tomas . 2026-I''',
     '''# `repo_mejorado/` — la version del proyecto auditado con los arreglos aplicados

> **Esta carpeta NO es el repositorio auditado.** Es el mismo codigo (commit
> `1528939`) con los defectos diagnosticados en las 51 fichas de auditoria
> **corregidos**. La copia verbatim e intocable de la que sale, con los 236 hashes
> SHA-256, esta en `../repo_auditado/`.
>
> | | `repo_auditado/` | `repo_mejorado/` (esta) |
> |---|---|---|
> | Naturaleza | **prueba**: copia verbatim, intocable | **trabajo**: codigo corregido |
> | Archivos | 236 | 234 |
> | Para que | citar lineas exactas y comprobar la auditoria | partir de aqui para seguir |
> | Se puede editar | **no** | si |
>
> ⚠️ Los numeros de linea de las citas de la auditoria (p. ej.
> `sprint2_duckdb.py:110`) valen para `repo_auditado/`: aqui 29 archivos
> cambiaron. Detalle de cada cambio en **`CHANGELOG.md`**.

## Que funciona ahora

Los **6 scripts que fallaban** en un clon limpio:

| Script | Antes | Ahora |
|---|---|---|
| `scripts/sprint6_geografia_institucional.py` | `UnicodeEncodeError` | corre completo |
| `scripts/sprint6_sankey_categoria.py` | `RuntimeError: Kaleido` | corre: 5 HTML + CSV |
| `scripts/sprint6_sankey_territorial.py` | `RuntimeError: Kaleido` | corre: HTML (avisa del PNG) |
| `scripts/sprint5_produccion.py` | traceback | sale con **3** y dice que falta |
| `scripts/sprint6_ocde_composicion.py` | traceback | sale con **3** y dice que falta |
| `scripts/sprint5_duckdb.py` | traceback | sale con **3** y dice que falta |

Tambien se corrigieron defectos que no aparecian en esa corrida:
`src/analisis/diversidad.py` (un comentario que contradecia al codigo y un
`KeyError` en un caso limite), `src/modelo/dimensional.py` (`.fetchdf()`
deprecado y un resumen que no se guardaba), `streamlit_app.py` (la pestana de
territorio **cerraba la app**), `scripts/generar_manual.py` y `docs/manual.ipynb`
(3 bugs) y 5 dependencias que el codigo importa y el proyecto no declaraba.

## Que sigue igual

- **La logica de analisis no se toco**: ninguna metrica, ningun modelo y ninguna
  decision metodologica cambiaron. Los arreglos son de ejecucion (dependencias,
  codificacion, rutas, guardias) mas tres bugs de codigo ya senalados.
- **La estructura de carpetas es la del original.** Unico cambio: el material
  academico no ejecutable se aparto a `legacy_referencia/`.
- **Los datos crudos siguen sin versionarse** (`datos/raw/`); ahora hay un
  `README.md` en cada carpeta de datos que explica que va ahi y como obtenerlo.
- **`poetry.lock` no se regenero** (no habia `poetry` ni red): hazlo antes de usar
  poetry, con `poetry lock && poetry install`.

## Como usarlo

```bash
pip install -r requirements.txt        # opcion rapida (poetry exige regenerar el lock)

python scripts/sprint2_panel_longitudinal.py        # analisis de investigadores: sin descargas
python scripts/sprint4_diversidad.py
python scripts/sprint6_geografia_institucional.py
python scripts/sprint6_sankey_categoria.py          # requiere plotly; el PNG, kaleido
streamlit run streamlit_app.py                      # dashboard

python -m src.ingesta.produccion      # dataset de produccion (~1,2 GB, requiere red)
python scripts/sprint5_produccion.py  # y entonces ya corre
```

**Codigos de salida:** `0` correcto · `1` error real (con traceback) ·
**`3` faltan datos de entrada** (el script lo explica y no deja salidas parciales).

Reproducir esta carpeta (no se edito a mano):

```bash
python datos_originales/construir_repo_mejorado.py
python datos_originales/aplicar_arreglos.py
python datos_originales/verificar_arreglos.py
```

Cualquier edicion manual aqui **se pierde** al reconstruir: si quieres un cambio
permanente, anadelo como parche en `aplicar_arreglos.py`.

---

# README ORIGINAL DEL PROYECTO AUDITADO

> El texto que sigue es el `README.md` original del proyecto auditado, conservado
> intacto porque la auditoria lo cita. Empieza en lo que aqui es la seccion
> "Observatorio MinCiencias -- Investigadores Reconocidos" del documento original.

## Observatorio MinCiencias — Investigadores Reconocidos

> **Ustadistica** -- Consultoria e Investigacion . Universidad Santo Tomas . 2026-I'''),

    ("H2", "requirements.txt",
     "requirements.txt declaraba 5 paquetes y no alcanzaba para correr ni los "
     "scripts ni el propio dashboard (faltaban matplotlib, seaborn, networkx, "
     "duckdb, PyYAML). Se completa como conjunto de instalacion rapida con pip y "
     "se remite a pyproject.toml como declaracion completa.",
     '''streamlit>=1.31
pandas>=2.2
numpy>=1.26
plotly>=5.18
openpyxl>=3.1''',
     '''# Instalacion rapida con pip del conjunto que el codigo realmente importa.
# La declaracion completa (con restricciones de version y dependencias de
# desarrollo) esta en pyproject.toml; este archivo es para "pip install -r".
streamlit>=1.31
pandas>=2.2
numpy>=1.26
matplotlib>=3.8
seaborn>=0.13
plotly>=5.18
openpyxl>=3.1
PyYAML>=6.0
kaleido>=1
networkx>=3.2
duckdb>=1.0
pyvis>=0.3
sodapy>=2.2
nbformat>=5.9
ipython>=8.0'''),
]


def parchear_manual_ipynb() -> int:
    """
    Aplica al cuaderno generado `docs/manual.ipynb` los mismos tres arreglos de
    `scripts/generar_manual.py`.

    Por que se parchea a mano: el cuaderno es un ARTEFACTO GENERADO por
    `scripts/generar_manual.py`, y lo correcto seria regenerarlo. No se puede en
    este entorno porque `nbformat` no esta instalado y no hay red. Se parchea el
    JSON (que es lo que `nbformat` lee) y `verificar_arreglos.py` comprueba que
    cada celda de codigo siga siendo Python valido y que los tres patrones
    erroneos ya no aparezcan. Cuando haya red, `python scripts/generar_manual.py`
    regenera el archivo con el generador ya corregido.
    """
    import json

    f = REPO / "docs" / "manual.ipynb"
    if not f.exists():
        print("[x] no existe docs/manual.ipynb")
        return 1

    nb = json.loads(f.read_text(encoding="utf-8"))
    cambios = 0
    for celda in nb.get("cells", []):
        if celda.get("cell_type") != "code":
            continue
        src = "".join(celda.get("source", []))
        nuevo = src
        nuevo = nuevo.replace(
            'for periodo, m in matrices.items():\n    print(f"\\n{periodo}")\n'
            '    print(m["conteos"])',
            'for periodo, m in matrices.items():\n'
            '    conteos, _probs = m   # matrices_todos_periodos: (conteos, probs)\n'
            '    print(f"\\n{periodo}")\n    print(conteos)')
        nuevo = nuevo.replace(
            'hhi_por_convocatoria(inv_clean, columna="NME_DEPARTAMENTO_RES_PR")',
            'hhi_por_convocatoria(inv_clean, col_geo="NME_DEPARTAMENTO_RES_PR")')
        nuevo = nuevo.replace('[ "python3",', '[sys.executable,').replace(
            '["python3",', '[sys.executable,')
        if nuevo != src:
            celda["source"] = nuevo.splitlines(keepends=True)
            cambios += 1

    if not cambios:
        print("[!] docs/manual.ipynb: ningun patron erroneo encontrado "
              "(ya estaba parcheado o cambio el cuaderno)")
        return 1
    f.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n",
                 encoding="utf-8")
    print(f"[ok] docs/manual.ipynb  ({cambios} celdas corregidas)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[3])
    ap.add_argument("--listar", action="store_true", help="enumera sin aplicar")
    args = ap.parse_args()

    if not REPO.exists():
        print(f"[x] No existe {REPO.relative_to(RAIZ)}. "
              f"Ejecuta primero construir_repo_mejorado.py")
        return 1

    # El modulo nuevo se escribe aparte: no es un parche sobre texto existente.
    nuevo = REPO / "src" / "exportacion.py"

    if args.listar:
        print(f"{len(ARREGLOS)} arreglos + 1 modulo nuevo (src/exportacion.py)\n")
        for id_, ruta, just, _, _ in ARREGLOS:
            print(f"  {id_:3s} {ruta}")
            print(f"      {just[:150]}")
        return 0

    if not nuevo.exists():
        nuevo.write_text(EXPORTACION_PY, encoding="utf-8")
        print(f"[nuevo] src/exportacion.py "
              f"({len(EXPORTACION_PY.splitlines())} lineas)")

    aplicados, errores = 0, []
    for id_, ruta, just, viejo, nuevo_txt in ARREGLOS:
        f = REPO / ruta
        if not f.exists():
            errores.append(f"{id_}: no existe {ruta}")
            continue
        txt = f.read_text(encoding="utf-8")
        n = txt.count(viejo)
        if n != 1:
            errores.append(f"{id_}: el ancla aparece {n} veces en {ruta} "
                           f"(se esperaba exactamente 1)")
            continue
        f.write_text(txt.replace(viejo, nuevo_txt, 1), encoding="utf-8")
        aplicados += 1
        print(f"[ok] {id_:3s} {ruta}")

    print(f"\naplicados: {aplicados} de {len(ARREGLOS)}")
    if errores:
        print("\nERRORES (ningun cambio aplicado en esos casos):")
        for e in errores:
            print(f"  [!] {e}")
        return 1
    rc_nb = parchear_manual_ipynb()
    print("todos los arreglos aplicados. Verifica con: "
          "python datos_originales/verificar_arreglos.py")
    return rc_nb


if __name__ == "__main__":
    raise SystemExit(main())
