# -*- coding: utf-8 -*-
"""
generar_objetivo.py
===================

Generador de proyectos LaTeX por criterio de la rúbrica (y versión LITE).

Función
-------
A partir de data/objetivos.yaml (un bloque por criterio de la rúbrica),
crea un proyecto Overleaf autónomo en latex/objetivo_<n>/ con documentos
ENFOCADOS: portada + contexto/guía de lectura (con glosario en lenguaje
llano) + únicamente las secciones relevantes al criterio + un breve cruce
con el documento maestro (evita repetir contenido entre PDFs) +
conclusiones.

Modos
-----
    python src/generar_objetivo.py            # versión completa por criterio
    python src/generar_objetivo.py --lite     # versión LITE (archivos clave,
                                              # fichas compactas)
    python src/generar_objetivo.py 2 4        # solo los criterios 2 y 4

Formato de data/objetivos.yaml
------------------------------
objetivos:
  - id: 1
    titulo: "Nombre del criterio"
    descripcion: "qué pide la rúbrica"
    resumen_simple: "resumen en lenguaje llano (2-3 frases)"
    secciones_principales: ["entendimiento"]   # claves: entendimiento, datos,
                                               # codigo, estadistica, logica,
                                               # timeline
    archivos_relevantes: [ ... ]  # o todos_los_archivos: true
    datos_observacion: "texto del criterio de datos (si aplica)"
    estadistica_observacion: "texto del criterio estadístico (si aplica)"
    logica_observacion: "texto del criterio de lógica (si aplica)"
    timeline_completa: true|false
    conclusiones: "texto de conclusiones"

El resto (fichas de código, timeline, glosario) se genera automáticamente
desde data/analisis_codigo/*.json, data/commits_timeline.csv e
data/inventario_codigo.csv.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

# Reutiliza utilidades del generador maestro
from generar_documento import (
    RAIZ,
    ANALISIS,
    TIMELINE_CSV,
    _leer_analisis,
    _leer_commits,
    escapar,
    lista_latex,
    render_tabla_commits,
    _verificar_controles,
)

LATEX = RAIZ / "latex"
PREAMBULO = LATEX / "comun" / "preambulo.tex"
REFS = LATEX / "maestro_auditoria" / "refs.bib"
OBJETIVOS_YAML = RAIZ / "data" / "objetivos.yaml"
INVENTARIO_CSV = RAIZ / "data" / "inventario_codigo.csv"

# Archivos "clave" para la versión LITE (los de mayor valor pedagógico)
ARCHIVOS_CLAVE = [
    "src/Transformacion.py",
    "src/ingesta/__init__.py",
    "src/ingesta/minciencias.py",
    "src/ingesta/produccion.py",
    "src/modelo/dimensional.py",
    "src/analisis/calidad.py",
    "src/analisis/longitudinal.py",
    "src/analisis/territorial.py",
    "src/analisis/genero.py",
    "src/analisis/diversidad.py",
    "src/analisis/redes.py",
    "src/analisis/produccion.py",
    "scripts/sprint2_panel_longitudinal.py",
    "scripts/sprint2_matrices_transicion.py",
    "scripts/sprint5_produccion.py",
    "scripts/sprint6_tabla_maestra_ies.py",
    "scripts/sprint6_validacion_calidad.py",
    "streamlit_app.py",
]

# Glosario en lenguaje llano (para lectores sin formación en programación)
GLOSARIO = [
    ("HHI (Herfindahl-Hirschman)",
     "Índice que mide si algo está concentrado o repartido. Va de 0 (todo repartido) "
     "a 1 (todo en un solo lugar). En el informe se usa para ver si los investigadores "
     "se concentran en pocos departamentos."),
    ("Matriz de transición",
     "Tabla que muestra con qué probabilidad un investigador pasa de una categoría "
     "(p. ej. Junior) a otra (p. ej. Asociado) entre dos convocatorias. Permite ver "
     "si el sistema 'sube', 'mantiene' o 'pierde' investigadores."),
    ("Tasa de retención",
     "Porcentaje de investigadores que siguen presentes en la siguiente convocatoria. "
     "Una retención baja puede indicar abandono o cambio de reglas."),
    ("Representación relativa",
     "Cuántas veces aparece un grupo (p. ej. afrocolombianos) en el padrón frente a lo "
     "que correspondería según su peso en la población colombiana (DANE). Un valor de "
     "0.3 indica que aparece 3 veces menos de lo esperado."),
    ("k-prototypes",
     "Algoritmo de agrupamiento (clustering) que agrupa personas con perfiles similares "
     "cuando los datos mezclan números (edad) y categorías (área, género)."),
    ("MCA / FAMD",
     "Técnicas para resumir tablas con muchas categorías en pocos ejes visualizables, "
     "de modo que se puedan ver patrones (p. ej. qué áreas se asocian con qué géneros)."),
    ("CRISP-DM",
     "Metodología estándar de proyectos de datos: entender el problema, preparar los "
     "datos, modelar, evaluar y desplegar. El proyecto la usa como guía general."),
    ("Modelo dimensional (esquema estrella)",
     "Forma de organizar los datos en tablas de 'hechos' (métricas: quién, cuándo, qué "
     "categoría) y 'dimensiones' (descripciones: área, región, institución), para hacer "
     "consultas rápidas y reportes."),
    ("DuckDB",
     "Base de datos analítica ligera que se ejecuta dentro del propio proyecto (sin "
     "instalar un servidor). Se usa para almacenar el modelo dimensional."),
    ("Mojibake",
     "Texto ilegible por un problema de codificación (p. ej. 'FÃ­sica' en lugar de "
     "'Física'). Detectado en el CSV del repositorio."),
    ("Contrato de esquema",
     "Validación automática que garantiza que un archivo de datos tenga las columnas, "
     "tipos y valores esperados antes de analizarlo."),
    ("ETL / pipeline",
     "Cadena de procesos que extrae los datos de la fuente (ETL: Extraer, Transformar, "
     "Cargar), los limpia y los deja listos para analizar."),
    ("CI/CD y Docker",
     "Automatización de pruebas y despliegue (CI/CD) y empaquetado de la aplicación en "
     "un contenedor (Docker) para que funcione igual en cualquier máquina."),
    ("Sprint",
     "Ciclo corto de trabajo (en este proyecto, de 2 semanas) con objetivos concretos."),
]


# ---------------------------------------------------------------------------
# Índice de fichas
# ---------------------------------------------------------------------------

def _ficha_por_archivo(analisis: list[dict]) -> dict:
    """Índice archivo -> ficha (por nombre base y ruta completa)."""
    idx: dict[str, dict] = {}
    for a in analisis:
        idx[Path(a.get("archivo", "")).name] = a
        idx[a.get("archivo", "")] = a
    return idx


# ---------------------------------------------------------------------------
# Secciones comunes
# ---------------------------------------------------------------------------

def _seccion_contexto_guia(o: dict) -> str:
    resumen = o.get("resumen_simple", "")
    filas_glosario = ""
    for termino, defi in GLOSARIO:
        filas_glosario += f"    {escapar(termino)} & {escapar(defi)} \\\\\n"
    resumen_tex = (
        f"\\textbf{{En resumen:}} {escapar(resumen)}"
        if resumen else ""
    )
    return f"""% ============ 02. Contexto y guía de lectura ============
\\section{{Contexto y guía de lectura}}

\\subsection{{Qué es este documento}}

Este documento desarrolla el \\textbf{{criterio {o['id']} de la rúbrica}}:
\\emph{{{escapar(o.get('titulo', ''))}}}. El repositorio auditado es el
Observatorio de investigadores reconocidos del Ministerio de Ciencia,
Tecnología e Innovación de Colombia (MinCiencias), que consolida y analiza
\\textbf{{6 convocatorias (2013--2021)}} del padrón oficial de investigadores
y su producción científica.

{resumen_tex}

\\begin{{tcolorbox}}[nota]
\\textbf{{Cómo leer este documento:}} cada PDF de esta serie desarrolla \\emph{{un}}
criterio de la rúbrica. Los demás criterios se tratan a fondo en sus propios
documentos y en el \\textbf{{documento maestro}} (\\texttt{{maestro\\_auditoria.pdf}},
114 págs.). Si este es tu primer acercamiento, lee primero la portada y este
contexto; al final encontrarás las conclusiones del criterio.
\\end{{tcolorbox}}

\\subsection{{Glosario para lectores sin formación en programación}}

Los documentos usan términos técnicos con moderación; cuando aparecen, esta
tabla los explica en lenguaje sencillo:

\\begingroup
\\small
\\setlength{{\\tabcolsep}}{{3pt}}
\\begin{{longtable}}{{>{{\\raggedright\\arraybackslash}}p{{4.3cm}}>{{\\raggedright\\arraybackslash}}p{{9.8cm}}}}
\\caption{{Glosario de términos en lenguaje llano}}
\\label{{tab:glosario}}\\\\
\\toprule
\\textbf{{Término}} & \\textbf{{Qué significa}} \\\\
\\midrule
\\endfirsthead
\\toprule
\\textbf{{Término}} & \\textbf{{Qué significa}} \\\\
\\midrule
\\endhead
{filas_glosario}\\bottomrule
\\end{{longtable}}
\\endgroup
"""


def _seccion_relacion_maestro(o: dict, secciones: list[str]) -> str:
    nombres = {
        "entendimiento": "Entendimiento del objetivo del repositorio",
        "datos": "Datos utilizados: suficiencia y corrección",
        "codigo": "Documentación y crítica por archivo de código",
        "estadistica": "Validación de la calidad estadística",
        "logica": "Lógica de creación del repositorio",
        "timeline": "Línea de tiempo de commits",
    }
    otros = [n for k, n in nombres.items() if k not in secciones]
    if not otros:
        return ""
    if len(otros) == 1:
        lista = otros[0]
    else:
        lista = "; ".join(otros[:-1]) + " y " + otros[-1]
    return f"""% ============ Relación con el documento maestro ============
\\section{{Relación con los demás criterios}}

Este documento se centra en el criterio {o['id']}. Los demás criterios de la
rúbrica — {escapar(lista)} — se desarrollan a fondo en sus propios documentos
y en el \\textbf{{documento maestro}} de la auditoría (\\texttt{{maestro\\_auditoria.pdf}}),
que los integra todos con el detalle completo de datos, código, estadística,
lógica y línea de tiempo. Esta separación evita repetir contenido: cada PDF
profundiza en lo suyo.
"""


def _seccion_conclusiones(o: dict) -> str:
    texto = o.get("conclusiones", "")
    if not texto:
        return ""
    return f"""% ============ Conclusiones ============
\\section{{Conclusiones y recomendaciones del criterio}}

{escapar(texto)}
"""


# ---------------------------------------------------------------------------
# Secciones por criterio (usadas según "secciones_principales")
# ---------------------------------------------------------------------------

def _seccion_entendimiento(o: dict) -> str:
    return f"""% ============ Criterio: entendimiento ============
\\section{{Entendimiento del objetivo del repositorio}}

{escapar(o.get('entendimiento_observacion', o.get('descripcion', '')))}

\\subsection{{Preguntas de investigación que el repositorio responde}}

El repositorio declara 7 preguntas (README): fiabilidad de los datos,
retención entre convocatorias, concentración territorial, brecha de género,
redes de co-filiación, diversidad poblacional y productividad cruzada con el
dataset de producción. Cada pregunta mapea a un módulo de análisis
(\\texttt{{src/analisis/*}}), lo que demuestra una descomposición
objetivo $\\rightarrow$ preguntas $\\rightarrow$ módulos correcta y trazable.
"""


def _seccion_datos(o: dict) -> str:
    return f"""% ============ Criterio: datos ============
\\section{{Datos utilizados: suficiencia y corrección}}

{escapar(o.get('datos_observacion', ''))}

\\subsection{{Fuentes del repositorio}}

\\begin{{itemize}}
  \\item \\textbf{{Padrón de investigadores}} (Socrata \\texttt{{bqtm-4y2h}}):
        convocatorias 2013--2021, 30 variables, \\textbf{{77\\,237 registros
        declarados}} y 30\\,086 investigadores únicos.
  \\item \\textbf{{Producción de grupos}} (Socrata \\texttt{{33dq-ab5a}}):
        3\\,166\\,629 filas producto-autor; dataset grande, no versionado en git.
  \\item \\textbf{{Catálogo}}: \\texttt{{datos/catalogo.yaml}} con metadatos,
        diccionario de datos y llaves de cruce (\\texttt{{id\\_persona\\_pr}} ↔
        \\texttt{{id\\_persona\\_pd}}).
\\end{{itemize}}

\\begin{{tcolorbox}}[nota]
Los datos no son solo los archivos: también se evaluó \\emph{{cómo se
versionaron}} en el repositorio. El detalle de la verificación (conteos reales,
codificación, hallazgos) está en este documento y en el maestro.
\\end{{tcolorbox}}
"""


def _seccion_codigo(o: dict, idx: dict, lite: bool) -> str:
    todos = o.get("todos_los_archivos", False)
    if lite:
        archivos = [a for a in ARCHIVOS_CLAVE if (idx.get(a) or idx.get(Path(a).name))]
    elif todos:
        archivos = sorted({k for k in idx.keys() if "/" in k or "\\" in k})
    else:
        archivos = o.get("archivos_relevantes", [])
    vistos: set[str] = set()
    unicos = []
    for a in archivos:
        if a not in vistos:
            vistos.add(a)
            unicos.append(a)
    archivos = sorted(unicos)

    cuerpo = [f"\\section{{Documentación y crítica por archivo de código}}",
              f"\\noindent Archivos documentados en este documento: "
              f"\\textbf{{{len(archivos)}}} de {len(idx)} auditados en total.",
              ""]
    if lite:
        cuerpo.append("\\begin{tcolorbox}[nota]"
                      "\\textbf{Versión LITE:} esta versión documenta los archivos "
                      "más representativos del proyecto en formato compacto. La "
                      "documentación completa de los 51 archivos (descripción, "
                      "lógica, fortalezas, debilidades, mejoras, ejecutabilidad) "
                      "está en el documento maestro y en el PDF del criterio 3 "
                      "completo."
                      "\\end{tcolorbox}")
        cuerpo.append("")
    for nombre in archivos:
        ficha = idx.get(nombre) or idx.get(Path(nombre).name)
        if ficha:
            cuerpo.append(_render_ficha(ficha, lite=lite))
        else:
            cuerpo.append(f"\\subsubsection{{{escapar(nombre)}}}")
            cuerpo.append("\\noindent \\textit{{Sin ficha de auditoría disponible.}}")
            cuerpo.append("")
    return "\n".join(cuerpo)


def _seccion_estadistica(o: dict) -> str:
    return f"""% ============ Criterio: estadística ============
\\section{{Validación de la calidad de pruebas, tratamientos y lógica estadística}}

{escapar(o.get('estadistica_observacion', ''))}

\\begin{{tcolorbox}}[nota]
\\textbf{{Principio de la auditoría:}} la crítica es constructiva. Cuando un
análisis o un archivo está bien construido se dice explícitamente; las
debilidades se presentan como oportunidades de mejora, no como reproches.
El detalle metodológico por eje (Markov, HHI, brechas, redes, clustering)
está en el documento maestro, sección 6.
\\end{{tcolorbox}}
"""


def _seccion_logica(o: dict) -> str:
    return f"""% ============ Criterio: lógica ============
\\section{{Lógica de creación del repositorio y cumplimiento del objetivo principal}}

{escapar(o.get('logica_observacion', ''))}

\\begin{{tcolorbox}}[hallazgo]
El repositorio se construyó en dos etapas: tareas académicas iniciales
(notebooks, ago--oct 2025) y pipeline de ingeniería de datos (\\texttt{{src/}} +
\\texttt{{scripts/sprint*}}, oct 2025 -- may 2026). La valoración detallada de
flujos correctos e incorrectos está en el documento maestro (sección 7) y en
el PDF del criterio 5.
\\end{{tcolorbox}}
"""


def _seccion_timeline(o: dict, commits: list[dict]) -> str:
    n = len(commits)
    completa = o.get("timeline_completa", False)
    tabla = render_tabla_commits(commits) if completa and commits else ""
    intro = f"""El repositorio fue construido con \\textbf{{{n} commits}} entre
\\textbf{{{commits[0]['fecha']}}} y \\textbf{{{commits[-1]['fecha']}}} por 12
identidades de autor (camiloacr1322 46, Victor-Diaz-Usta 34, Maria Amaya 13,
Paula 11, JulianMendez27 11, PaulaGuevara 4, y otros)."""
    fases = """\\subsection{Las tres fases de construcción}

\\begin{itemize}
  \\item \\textbf{Fase académica} (ago--oct 2025): análisis por convocatoria,
        join, dimensiones/hechos y gran tabla (autores: Paula, JulianMendez27,
        camiloacr1322, Maria Amaya).
  \\item \\textbf{Fase de ingeniería} (oct 2025 -- abr 2026): \\texttt{src/},
        \\texttt{scripts/sprint2..5}, DuckDB y dashboard (Victor-Diaz-Usta).
  \\item \\textbf{Fase de cierre} (abr--may 2026): Sprint 6 (calidad, tabla
        maestra IES, Sankeys, geografía) y merge final (Victor-Diaz-Usta).
\\end{itemize}
"""
    return f"""% ============ Criterio: timeline ============
\\section{{Línea de tiempo de commits}}

{intro}

{fases}{tabla}"""


# ---------------------------------------------------------------------------
# Render de fichas
# ---------------------------------------------------------------------------

def _render_ficha(a: dict, lite: bool = False) -> str:
    """Ficha por archivo. Modo lite: versión compacta y menos técnica."""
    archivo = a.get("archivo", "desconocido")
    rol = a.get("rol", "")
    lineas = a.get("lineas", "")
    descripcion = a.get("descripcion", "—")
    logica = a.get("logica", "—")
    recomendacion = a.get("recomendacion", "—")
    bugs = a.get("bugs", []) or []
    debilidades = a.get("critica_debilidades", []) or []
    fortalezas = a.get("critica_fortalezas", []) or []
    mejoras = a.get("mejoras", []) or []

    if lite:
        partes = [
            "\\subsubsection{" + escapar(archivo) + "}",
            f"\\textbf{{Rol:}} {escapar(rol)} · \\textbf{{Líneas:}} {escapar(str(lineas))}",
            "",
            "\\textbf{Qué hace:} " + escapar(descripcion),
            "",
            "\\textbf{Valoración:} " + escapar(recomendacion),
            "",
        ]
        if bugs:
            partes += ["\\textbf{Hallazgos relevantes:}", lista_latex(bugs), ""]
        partes += ["\\medskip", "\\hrule", ""]
        return "\n".join(partes)

    partes = [
        "\\subsubsection{" + escapar(archivo) + "}",
        f"\\textbf{{Rol:}} {escapar(rol)} · \\textbf{{Líneas:}} {escapar(str(lineas))}",
        "",
        "\\paragraph{Descripción funcional}",
        escapar(descripcion),
        "",
        "\\paragraph{Análisis de la lógica}",
        escapar(logica),
        "",
    ]
    if fortalezas:
        partes += ["\\paragraph{Lo que está bien construido}", lista_latex(fortalezas), ""]
    if debilidades:
        partes += ["\\paragraph{Puntos de mejora (si aplican)}", lista_latex(debilidades), ""]
    else:
        partes += ["\\paragraph{Puntos de mejora}",
                   "\\noindent No se identifican debilidades significativas: el archivo "
                   "cumple su función de forma clara y consistente.", ""]
    if mejoras:
        partes += ["\\paragraph{Sugerencias concretas}", lista_latex(mejoras), ""]
    partes += [
        "\\paragraph{Ejecutabilidad}",
        escapar(a.get("ejecutabilidad", "—")),
        "",
        "\\paragraph{¿Produce lo que se buscaba?}",
        escapar(a.get("produce_esperado", "—")),
        "",
    ]
    if bugs:
        partes += ["\\begin{tcolorbox}[riesgo]",
                   "\\textbf{Problemas detectados:}",
                   lista_latex(bugs),
                   "\\end{tcolorbox}", ""]
    partes += [
        "\\paragraph{Valoración global}",
        "\\textbf{" + escapar(recomendacion) + "}",
        "",
        "\\medskip",
        "\\hrule",
        "",
    ]
    return "\n".join(partes)


# ---------------------------------------------------------------------------
# Ensamblado
# ---------------------------------------------------------------------------

SECCIONES_DISPONIBLES = {
    "entendimiento": _seccion_entendimiento,
    "datos": _seccion_datos,
    "codigo": _seccion_codigo,
    "estadistica": _seccion_estadistica,
    "logica": _seccion_logica,
    "timeline": _seccion_timeline,
}


def generar_objetivo(o: dict, commits: list[dict], idx: dict, lite: bool = False) -> Path:
    n = o["id"]
    sufijo = "_lite" if lite else ""
    carpeta = LATEX / f"objetivo_{n}{sufijo}"
    secc = carpeta / "secciones"
    secc.mkdir(parents=True, exist_ok=True)

    shutil.copy2(PREAMBULO, carpeta / "preambulo.tex")
    shutil.copy2(REFS, carpeta / "refs.bib")

    secciones_sel = o.get("secciones_principales", [])
    if not secciones_sel:
        secciones_sel = list(SECCIONES_DISPONIBLES.keys())

    orden = ["entendimiento", "datos", "codigo", "estadistica", "logica", "timeline"]
    includes = [
        "\\input{secciones/01_portada.tex}",
        "\\tableofcontents",
        "\\newpage",
        "\\input{secciones/02_contexto.tex}",
    ]
    for k in orden:
        if k in secciones_sel:
            includes.append(f"\\input{{secciones/03_{k}.tex}}")
    includes.append("\\input{secciones/04_relacion.tex}")
    if o.get("conclusiones"):
        includes.append("\\input{secciones/05_conclusiones.tex}")
    includes.append("\\bibliographystyle{plainnat}")
    includes.append("\\bibliography{refs}")
    includes.append("\\end{document}")

    titulo_doc = o.get("titulo", f"Criterio {n}")
    version = "LITE (versión resumida)" if lite else "1.0"

    (carpeta / "main.tex").write_text(f"""% =====================================================================
% Documento de auditoría — Criterio {n}{' (LITE)' if lite else ''}
% Observatorio MinCiencias · USTA · 2026-I
% Proyecto Overleaf: subir esta carpeta y compilar con pdfLaTeX.
% =====================================================================
\\input{{preambulo.tex}}

\\renewcommand{{\\doctitulo}}{{Criterio {n}: {escapar(titulo_doc)}}}
\\renewcommand{{\\docsubtitulo}}{{Documentación técnica de auditoría · {'Versión' if lite else 'Documento'} {version} · Un documento por criterio de la rúbrica}}
\\renewcommand{{\\docversion}}{{{version}}}

\\begin{{document}}

{chr(10).join(includes)}
""", encoding="utf-8")

    (carpeta / "secciones" / "01_portada.tex").write_text("\\hacerportada\n", encoding="utf-8")
    (carpeta / "secciones" / "02_contexto.tex").write_text(_seccion_contexto_guia(o), encoding="utf-8")
    for k in orden:
        if k in secciones_sel:
            if k == "codigo":
                contenido = _seccion_codigo(o, idx, lite)
            elif k == "timeline":
                contenido = _seccion_timeline(o, commits)
            else:
                contenido = SECCIONES_DISPONIBLES[k](o)
            (carpeta / "secciones" / f"03_{k}.tex").write_text(contenido, encoding="utf-8")
    (carpeta / "secciones" / "04_relacion.tex").write_text(
        _seccion_relacion_maestro(o, secciones_sel), encoding="utf-8")
    if o.get("conclusiones"):
        (carpeta / "secciones" / "05_conclusiones.tex").write_text(
            _seccion_conclusiones(o), encoding="utf-8")

    print(f"[objetivo {n}{' (LITE)' if lite else ''}] {carpeta}")
    return carpeta


def main() -> None:
    if not OBJETIVOS_YAML.exists():
        print(f"No existe {OBJETIVOS_YAML}.")
        return

    lite = "--lite" in sys.argv
    solo = {int(x) for x in sys.argv if x.isdigit()}

    with open(OBJETIVOS_YAML, encoding="utf-8-sig") as fh:
        data = yaml.safe_load(fh)

    objetivos = data.get("objetivos", [])
    if not objetivos:
        print("El YAML no define objetivos.")
        return

    analisis = _leer_analisis()
    idx = _ficha_por_archivo(analisis)
    commits = _leer_commits()

    for o in objetivos:
        if solo and int(o["id"]) not in solo:
            continue
        carpeta = generar_objetivo(o, commits, idx, lite=lite)
        for tex in carpeta.glob("secciones/*.tex"):
            _verificar_controles(tex)

    print("Generación de proyectos por objetivo completada.")


if __name__ == "__main__":
    main()
