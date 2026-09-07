# -*- coding: utf-8 -*-
"""
generar_objetivo.py
===================

Generador de proyectos LaTeX por criterio de la rúbrica (completo y LITE).

Funcionalidades
---------------
- Documentos ENFOCADOS: portada + contexto/guía + solo las secciones del
  criterio + cruce con el maestro + conclusiones.
- Versión LITE: sección principal reducida a veredicto + 1-2 hallazgos de
  mayor impacto. Reglas de build: si el LITE es idéntico al completo o
  supera el 40% de sus palabras, la build FALLA (no se emite el PDF).
- Glosario: leído de data/glosario.yaml (fuente de verdad) e incluido solo
  con las entradas cuyos términos aparecen en el propio documento.
- Orden de archivos: por capa canónica (data/capas.yaml), igual en todos
  los documentos.
- Hallazgos con archivo.py:N-M: incrusta el fragmento real del código
  (máx. 6 líneas) extraído del repositorio auditado.
- Línea de cobertura computada ("Cobertura: X de Y archivos...").
- Portada con "Commit auditado: <hash corto>".

Modos
-----
    python src/generar_objetivo.py            # versiones completas
    python src/generar_objetivo.py --lite     # versiones LITE (con checks)
    python src/generar_objetivo.py 2 4        # solo criterios 2 y 4
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from generar_documento import (
    RAIZ,
    ANALISIS,
    TIMELINE_CSV,
    REPO,
    _leer_analisis,
    _leer_commits,
    _cargar_capas,
    capa_de_ruta,
    escapar,
    lista_latex,
    render_tabla_commits,
    _verificar_controles,
    _bugs_con_fragmentos,
)

LATEX = RAIZ / "latex"
PREAMBULO = LATEX / "comun" / "preambulo.tex"
REFS = LATEX / "maestro_auditoria" / "refs.bib"
OBJETIVOS_YAML = RAIZ / "data" / "objetivos.yaml"
GLOSARIO_YAML = RAIZ / "data" / "glosario.yaml"

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

# Títulos de sección por clave de criterio
TITULOS_CRITERIO = {
    "entendimiento": "Entendimiento del objetivo del repositorio",
    "datos": "Datos utilizados: suficiencia y corrección",
    "codigo": "Documentación y crítica por archivo de código",
    "estadistica": "Validación de la calidad de pruebas, tratamientos y lógica estadística",
    "logica": "Lógica de creación del repositorio y cumplimiento del objetivo principal",
    "timeline": "Línea de tiempo de commits",
}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _commit_auditado() -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=15,
        )
        return (r.stdout or "").strip() or "no-disponible"
    except Exception:
        return "no-disponible"


def _contar_palabras(tex: str) -> int:
    """Cuenta palabras aproximadas de un fragmento LaTeX (ignora comandos)."""
    t = re.sub(r"\\[a-zA-Z@]+", " ", tex)
    t = re.sub(r"[{}#$%&_^~]", " ", t)
    t = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", " ", t)
    return len([w for w in t.split() if any(c.isalnum() for c in w)])


def _ficha_por_archivo(analisis: list[dict]) -> dict:
    """Índice archivo -> ficha (por nombre base y ruta completa)."""
    idx: dict[str, dict] = {}
    for a in analisis:
        idx[Path(a.get("archivo", "")).name] = a
        idx[a.get("archivo", "")] = a
    return idx


def _total_archivos(idx: dict) -> int:
    """Nº de archivos únicos auditados (por el campo 'archivo' de cada ficha)."""
    return len({a.get("archivo", "") for a in idx.values()})


def _cargar_glosario() -> list[dict]:
    if not GLOSARIO_YAML.exists():
        return []
    with open(GLOSARIO_YAML, encoding="utf-8-sig") as fh:
        return yaml.safe_load(fh).get("glosario", [])


def _orden_por_capa(archivos: list[str], idx: dict) -> list[str]:
    """Ordena archivos por el ORDEN CANÓNICO de capas (data/capas.yaml) y
    luego alfabético dentro de cada capa."""
    orden, _ = _cargar_capas()

    def clave(ruta: str):
        capa = capa_de_ruta(ruta)
        return (orden.index(capa) if capa in orden else len(orden), ruta.lower())

    return sorted(archivos, key=clave)


# ---------------------------------------------------------------------------
# Secciones comunes
# ---------------------------------------------------------------------------

def _seccion_contexto_guia(o: dict, texto_doc: str, lite: bool) -> str:
    resumen = o.get("resumen_simple", "")
    glosario = _cargar_glosario()
    texto = texto_doc.lower()
    filas = []
    for g in glosario:
        claves = [c.lower() for c in g.get("claves", [])]
        # Emparejamiento con límite de palabra (\b) para no matchear
        # subcadenas accidentales (p. ej. 'etl' dentro de 'setlength').
        if any(re.search(r"\b" + re.escape(c) + r"\b", texto) for c in claves):
            filas.append((g["termino"], g["definicion"]))
    filas_glosario = "".join(
        f"    {escapar(term)} & {escapar(defi)} \\\\\n" for term, defi in filas
    )
    if not filas:
        filas_glosario = (
            "    \\multicolumn{2}{l}{Este documento no requiere términos técnicos "
            "adicionales.} \\\\\n"
        )
    resumen_tex = f"\\textbf{{En resumen:}} {escapar(resumen)}" if resumen else ""
    version_note = (
        "\\begin{tcolorbox}[nota]\\textbf{Versión LITE:} este documento resume el "
        "criterio (veredicto y hallazgos de mayor impacto). El desarrollo completo "
        "está en la versión completa del criterio y en el documento maestro."
        "\\end{tcolorbox}" if lite else ""
    )
    return f"""% ============ 02. Contexto y guía de lectura ============
\\section{{Contexto y guía de lectura}}

\\subsection{{Qué es este documento}}

Este documento desarrolla el \\textbf{{criterio {o['id']} de la rúbrica}}:
\\emph{{{escapar(o.get('titulo', ''))}}}. El repositorio auditado es el
Observatorio de investigadores reconocidos del Ministerio de Ciencia,
Tecnología e Innovación de Colombia (MinCiencias), que consolida y analiza
\\textbf{{6 convocatorias (2013--2021)}} del padrón oficial de investigadores
y su producción científica. Esta serie cubre los \\textbf{{6 criterios}} de la
rúbrica en documentos separados, más el documento maestro que los integra.

{resumen_tex}

{version_note}

\\begin{{tcolorbox}}[nota]
\\textbf{{Cómo leer este documento:}} cada PDF de esta serie desarrolla \\emph{{un}}
criterio de la rúbrica. Los demás criterios se tratan a fondo en sus propios
documentos y en el \\textbf{{documento maestro}} (\\texttt{{maestro\\_auditoria.pdf}}).
Si este es tu primer acercamiento, lee primero la portada y este contexto; al
final encontrarás las conclusiones del criterio.
\\end{{tcolorbox}}

\\subsection{{Glosario (solo los términos que usa este documento)}}

Esta tabla incluye únicamente los términos técnicos que aparecen en este
documento, explicados en lenguaje sencillo:

\\begingroup
\\small
\\setlength{{\\tabcolsep}}{{3pt}}
\\begin{{longtable}}{{>{{\\raggedright\\arraybackslash}}p{{4.3cm}}>{{\\raggedright\\arraybackslash}}p{{9.8cm}}}}
\\caption{{Glosario de términos presentes en este documento}}
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
# Secciones principales (completas)
# ---------------------------------------------------------------------------

def _seccion_entendimiento(o: dict) -> str:
    return f"""% ============ Criterio: entendimiento ============
\\section{{{TITULOS_CRITERIO['entendimiento']}}}

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
\\section{{{TITULOS_CRITERIO['datos']}}}

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
        # Todos los archivos auditados, por el campo 'archivo' de cada ficha
        # (incluye archivos raíz sin barra, p. ej. streamlit_app.py)
        archivos = sorted({a.get("archivo", "") for a in idx.values()})
    else:
        archivos = o.get("archivos_relevantes", [])
    archivos = _orden_por_capa(list(dict.fromkeys(archivos)), idx)
    total = _total_archivos(idx)

    cuerpo = [f"\\section{{{TITULOS_CRITERIO['codigo']}}}",
              f"\\noindent \\textbf{{Cobertura:}} {len(archivos)} de {total} "
              f"archivos de código documentados en esta versión.",
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
\\section{{{TITULOS_CRITERIO['estadistica']}}}

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
\\section{{{TITULOS_CRITERIO['logica']}}}

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
\\textbf{{{commits[0]['fecha']}}} y \\textbf{{{commits[-1]['fecha']}}} por 11
autores (12 identidades nombre+correo): camiloacr1322 46, Victor-Diaz-Usta 39,
Maria Amaya 13, Paula 11, JulianMendez27 11, PaulaGuevara 4, y otros."""
    fases = """\\subsection{Las tres fases de construcción}

La actividad no fue continua: entre el 2025-11-18 y el 2026-02-26 hubo un
\\textbf{hiato de ~100 días sin commits} (los repositorios académicos suelen
pausarse entre periodos).

\\begin{itemize}
  \\item \\textbf{Fase académica} (ago--nov 2025): análisis por convocatoria,
        join, dimensiones/hechos y gran tabla (autores: Paula, JulianMendez27,
        camiloacr1322, Maria Amaya).
  \\item \\textbf{Hiato} (nov 2025 -- feb 2026): sin actividad registrada.
  \\item \\textbf{Fase de ingeniería y cierre} (feb/mar--may 2026):
        \\texttt{{src/}}, \\texttt{{scripts/sprint2..6}}, DuckDB, dashboard,
        producción y ajustes finales (Victor-Diaz-Usta, con revisión del
        director).
\\end{itemize}
"""
    return f"""% ============ Criterio: timeline ============
\\section{{{TITULOS_CRITERIO['timeline']}}}

{intro}

{fases}{tabla}"""


# ---------------------------------------------------------------------------
# Sección principal LITE (veredicto + hallazgos de mayor impacto)
# ---------------------------------------------------------------------------

def _seccion_lite(o: dict, clave: str) -> str:
    veredicto = o.get("lite_veredicto", "") or o.get("resumen_simple", "")
    hallazgos = o.get("lite_hallazgos", []) or []
    titulo = TITULOS_CRITERIO.get(clave, clave)
    hallazgos_tex = lista_latex(hallazgos) if hallazgos else (
        "\\noindent Ver las conclusiones del documento para los hallazgos clave."
    )
    return f"""% ============ Criterio {clave} (LITE) ============
\\section{{{titulo}}}

\\begin{{tcolorbox}}[hallazgo]
\\textbf{{Veredicto:}} {escapar(veredicto)}
\\end{{tcolorbox}}

\\subsection{{Hallazgos de mayor impacto}}

{hallazgos_tex}
"""


SECCIONES_COMPLETAS = {
    "entendimiento": _seccion_entendimiento,
    "datos": _seccion_datos,
    "estadistica": _seccion_estadistica,
    "logica": _seccion_logica,
}


def _seccion_principal(o: dict, clave: str, idx: dict, commits: list[dict],
                       lite: bool) -> str:
    """Devuelve el contenido LaTeX de la sección principal del criterio."""
    if clave == "codigo":
        return _seccion_codigo(o, idx, lite)
    if clave == "timeline":
        return _seccion_lite(o, clave) if lite else _seccion_timeline(o, commits)
    if lite:
        return _seccion_lite(o, clave)
    return SECCIONES_COMPLETAS[clave](o)


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
            partes += ["\\textbf{Hallazgos relevantes:}", _bugs_con_fragmentos(bugs), ""]
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
                   _bugs_con_fragmentos(bugs),
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

def _verificar_lite(o: dict, clave: str, idx: dict, commits: list[dict]) -> None:
    """Reglas de build para LITE: si es idéntico al completo o supera el 40%
    de sus palabras, la build FALLA (no se emite el PDF)."""
    contenido_full = _seccion_principal(o, clave, idx, commits, lite=False)
    contenido_lite = _seccion_principal(o, clave, idx, commits, lite=True)
    if contenido_full.strip() == contenido_lite.strip():
        raise SystemExit(
            f"[FALLO BUILD] LITE idéntico al completo en criterio {o['id']} "
            f"(sección '{clave}'). Corrige lite_veredicto/lite_hallazgos.")
    wf = _contar_palabras(contenido_full)
    wl = _contar_palabras(contenido_lite)
    if wf > 0 and wl > 0.40 * wf:
        raise SystemExit(
            f"[FALLO BUILD] LITE supera el 40% de palabras del completo en "
            f"criterio {o['id']} (sección '{clave}'): {wl} vs {wf} "
            f"({wl / wf:.0%}). Recorta el contenido LITE.")


def generar_objetivo(o: dict, commits: list[dict], idx: dict,
                     lite: bool = False) -> Path:
    n = o["id"]
    sufijo = "_lite" if lite else ""
    carpeta = LATEX / f"objetivo_{n}{sufijo}"
    secc = carpeta / "secciones"
    secc.mkdir(parents=True, exist_ok=True)

    shutil.copy2(PREAMBULO, carpeta / "preambulo.tex")
    shutil.copy2(REFS, carpeta / "refs.bib")

    secciones_sel = o.get("secciones_principales", [])
    if not secciones_sel:
        secciones_sel = list(TITULOS_CRITERIO.keys())

    # Reglas de build para LITE (antes de escribir nada)
    if lite:
        for clave in secciones_sel:
            _verificar_lite(o, clave, idx, commits)

    # Construir contenido de las secciones principales
    orden = ["entendimiento", "datos", "codigo", "estadistica", "logica", "timeline"]
    contenidos: dict[str, str] = {}
    for k in orden:
        if k in secciones_sel:
            contenidos[k] = _seccion_principal(o, k, idx, commits, lite=lite)

    relacion = _seccion_relacion_maestro(o, secciones_sel)
    conclusiones = _seccion_conclusiones(o) if o.get("conclusiones") else ""

    # Texto del documento (sin glosario) para filtrar términos
    texto_doc = "\n".join(contenidos.values()) + relacion + conclusiones
    contexto = _seccion_contexto_guia(o, texto_doc, lite)

    includes = [
        "\\input{secciones/01_portada.tex}",
        "\\tableofcontents",
        "\\newpage",
        "\\input{secciones/02_contexto.tex}",
    ]
    for k in orden:
        if k in contenidos:
            includes.append(f"\\input{{secciones/03_{k}.tex}}")
    includes.append("\\input{secciones/04_relacion.tex}")
    if conclusiones:
        includes.append("\\input{secciones/05_conclusiones.tex}")
    includes.append("\\bibliographystyle{plainnat}")
    includes.append("\\bibliography{refs}")
    includes.append("\\end{document}")

    commit = _commit_auditado()
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
\\renewcommand{{\\doccommit}}{{{commit}}}

\\begin{{document}}

{chr(10).join(includes)}
""", encoding="utf-8")

    (carpeta / "secciones" / "01_portada.tex").write_text("\\hacerportada\n", encoding="utf-8")
    (carpeta / "secciones" / "02_contexto.tex").write_text(contexto, encoding="utf-8")
    for k, contenido in contenidos.items():
        (carpeta / "secciones" / f"03_{k}.tex").write_text(contenido, encoding="utf-8")
    (carpeta / "secciones" / "04_relacion.tex").write_text(relacion, encoding="utf-8")
    if conclusiones:
        (carpeta / "secciones" / "05_conclusiones.tex").write_text(conclusiones, encoding="utf-8")

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
