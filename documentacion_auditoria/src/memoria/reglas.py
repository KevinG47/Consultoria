# -*- coding: utf-8 -*-
"""
memoria.reglas
==============

Reglas de validación sobre la memoria estructural (grafo) y los datos reales.

Cada regla devuelve: id, descripción, estado (PASA | FALLA | ADVERTENCIA),
detalle legible y evidencia (conteos y ejemplos). No hay valores "esperados"
codificados a mano: todo se calcula contra los datos reales del proyecto.

Las seis reglas mínimas exigidas son R1–R6; R7–R12 se añadieron porque cubren
riesgos reales detectados en la auditoría (commit auditado, capas sin asignar,
cobertura de fichas, integridad referencial y consistencia del propio RAG).
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from . import config, grafo, rag

PASA, FALLA, ADVERTENCIA = "PASA", "FALLA", "ADVERTENCIA"


def _regla(rid, descripcion, estado, detalle, evidencia=None) -> dict:
    return {"id": rid, "descripcion": descripcion, "estado": estado,
            "detalle": detalle, "evidencia": evidencia or {}}


# --------------------------------------------------------------------------
# R1–R6: reglas mínimas exigidas
# --------------------------------------------------------------------------
def r1_documentos_por_criterio(objetivos, g) -> dict:
    faltan = []
    for o in objetivos:
        c = f"criterio_{o['id']}"
        hijos = [g.nodes[n] for n in g.successors(c) if g.nodes[n]["tipo"] == "Documento"]
        tiene_completo = any(h["variante"] == "completo" and h["nombre"].startswith("objetivo_") for h in hijos)
        tiene_lite = any(h["variante"] == "lite" for h in hijos)
        if not (tiene_completo and tiene_lite):
            faltan.append({"criterio": o["id"], "completo": tiene_completo, "lite": tiene_lite})
    return _regla(
        "R1", "Cada criterio tiene documento completo Y LITE",
        PASA if not faltan else FALLA,
        f"{len(objetivos)} criterios revisados; {len(faltan)} sin el par completo/LITE.",
        {"criterios": len(objetivos), "faltantes": faltan,
         "documentos_por_criterio": {
             f"criterio_{o['id']}": sorted(n.replace('doc::', '') for n in g.successors(f"criterio_{o['id']}")
                                           if g.nodes[n]['tipo'] == 'Documento')
             for o in objetivos}},
    )


def r2_conclusiones_completos(objetivos) -> dict:
    faltan, cortos = [], []
    for o in objetivos:
        yaml_ok = bool(str(o.get("conclusiones", "")).strip())
        tex = config.LATEX / f"objetivo_{o['id']}" / "secciones" / "05_conclusiones.tex"
        tex_palabras = 0
        if tex.exists():
            tex_palabras = len(rag.limpiar_latex(tex.read_text(encoding="utf-8", errors="replace")).split())
        if not (yaml_ok and tex.exists() and tex_palabras > 0):
            faltan.append({"criterio": o["id"], "yaml_conclusiones": yaml_ok, "palabras_tex": tex_palabras})
        elif tex_palabras < 50:
            cortos.append({"criterio": o["id"], "palabras_tex": tex_palabras})
    if faltan:
        estado = FALLA
    elif cortos:
        estado = ADVERTENCIA
    else:
        estado = PASA
    return _regla(
        "R2", "Todo documento completo tiene conclusiones registradas",
        estado,
        f"{len(objetivos) - len(faltan)}/{len(objetivos)} criterios con conclusiones en YAML y sección 05 presente. "
        f"Secciones muy breves (<50 palabras): {len(cortos)}.",
        {"faltantes": faltan, "muy_breves": cortos},
    )


def r3_veredicto_lite(objetivos) -> dict:
    faltan, sin_palabra = [], []
    for o in objetivos:
        veredicto = bool(str(o.get("lite_veredicto", "")).strip())
        hallazgos = len(o.get("lite_hallazgos", []) or [])
        tex = config.LATEX / f"objetivo_{o['id']}_lite" / "secciones" / "05_conclusiones.tex"
        texto = rag.limpiar_latex(tex.read_text(encoding="utf-8", errors="replace")) if tex.exists() else ""
        menciona = bool(re.search(r"veredicto", texto, re.I))
        registro = {"criterio": o["id"], "yaml_veredicto": veredicto, "hallazgos_yaml": hallazgos,
                    "seccion_05_palabras": len(texto.split()), "menciona_palabra_veredicto": menciona}
        if not veredicto or not texto.strip():
            faltan.append(registro)
        elif not menciona:
            sin_palabra.append(registro)
    if faltan:
        estado = FALLA
    elif sin_palabra:
        estado = ADVERTENCIA
    else:
        estado = PASA
    return _regla(
        "R3", "Todo documento LITE tiene veredicto resumido",
        estado,
        f"{len(objetivos) - len(faltan)}/{len(objetivos)} LITE con veredicto declarado en objetivos.yaml "
        f"(lite_veredicto) y sección 05 con contenido; {len(sin_palabra)} sin la palabra literal 'veredicto'.",
        {"faltantes": faltan, "sin_palabra_veredicto": sin_palabra},
    )


def r4_glosario_usado(glosario, resumen) -> dict:
    return _regla(
        "R4", "Todo término del glosario está efectivamente usado en algún documento",
        PASA if not resumen.terminos_no_usados else FALLA,
        f"{resumen.terminos_usados}/{len(glosario)} términos aparecen en al menos un documento "
        f"(búsqueda por claves sobre el texto de los 6 criterios, LITE y maestro).",
        {"no_usados": resumen.terminos_no_usados},
    )


def r5_timeline_vs_git(real: pd.DataFrame, doc: pd.DataFrame) -> dict:
    r = {str(h)[:7]: row for h, row in zip(real["hash"], real.to_dict("records"))}
    d = {str(h)[:7]: row for h, row in zip(doc["hash"], doc.to_dict("records"))}
    solo_real = sorted(set(r) - set(d))
    solo_doc = sorted(set(d) - set(r))
    comunes = sorted(set(r) & set(d))
    dif_asunto = [h for h in comunes if str(r[h]["asunto"]).strip() != str(d[h]["asunto"]).strip()]
    dif_fecha = [h for h in comunes if str(r[h]["fecha"]).strip() != str(d[h]["fecha"]).strip()]
    autores_real = Counter(str(v["autor"]) for v in r.values())
    autores_doc = Counter(str(v["autor"]) for v in d.values())
    estado = PASA if not (solo_real or solo_doc or dif_asunto or dif_fecha) else FALLA
    ejemplos = [{"hash": h, "git": r[h]["asunto"][:70], "csv": d[h]["asunto"][:70]} for h in dif_asunto[:3]]
    return _regla(
        "R5", "La línea de tiempo documentada coincide con el git log real",
        estado,
        f"git log real={len(r)} commits; commits_timeline.csv={len(d)}; coinciden por hash={len(comunes)}; "
        f"solo en git={len(solo_real)}; solo en CSV={len(solo_doc)}; asunto distinto={len(dif_asunto)}; "
        f"fecha distinta={len(dif_fecha)}.",
        {"solo_en_git": solo_real[:5], "solo_en_csv": solo_doc[:5],
         "asuntos_distintos": ejemplos, "n_autores_git": len(autores_real), "n_autores_csv": len(autores_doc)},
    )


def r6_archivos_en_documento_codigo(g, real_files: list[str]) -> dict:
    texto = rag.limpiar_latex(
        (config.LATEX / "objetivo_3" / "secciones" / "03_codigo.tex").read_text(encoding="utf-8", errors="replace")
    ) if (config.LATEX / "objetivo_3" / "secciones" / "03_codigo.tex").exists() else ""
    faltan = [p for p in sorted(set(real_files)) if Path(p).name not in texto and p not in texto]
    return _regla(
        "R6", "Todo archivo de código real está referenciado en el documento del criterio de código",
        PASA if not faltan else FALLA,
        f"{len(set(real_files)) - len(faltan)}/{len(set(real_files))} archivos reales del repo auditado "
        f"aparecen en latex/objetivo_3 (Criterio 3).",
        {"faltantes": faltan[:15], "n_faltantes": len(faltan)},
    )


# --------------------------------------------------------------------------
# R7–R12: reglas añadidas
# --------------------------------------------------------------------------
def r7_commit_auditado(resumen) -> dict:
    doc: dict[str, str] = {}
    for main in sorted(config.LATEX.glob("objetivo_*/main.tex")):
        txt = main.read_text(encoding="utf-8", errors="replace")
        # en los proyectos se declara como \renewcommand{\doccommit}{HASH}
        m = re.search(r"doccommit\}\{([^}]+)\}", txt) or re.search(r"\\doccommit\{([^}]+)\}", txt)
        if m:
            doc[main.parent.name] = m.group(1).strip()
    valores = sorted(set(doc.values()))
    estado = PASA if valores == [resumen.commit_auditado] else FALLA
    return _regla(
        "R7", "El commit auditado documentado coincide con el HEAD real del clon",
        estado,
        f"HEAD real={resumen.commit_auditado}; documentado en {len(doc)} proyectos: {valores}.",
        {"documentado_por_proyecto": doc, "head_real": resumen.commit_auditado,
         "proyectos_revisados": len(list(config.LATEX.glob("objetivo_*/main.tex")))},
    )


def r8_capas_asignadas(resumen, inventario: pd.DataFrame) -> dict:
    """
    ¿Cada archivo queda clasificado por una REGLA EXPLÍCITA de capas.yaml?

    Se distingue "no clasificado" (cae al valor por defecto 'otro' sin que ninguna
    regla lo mencione) de "clasificado explícitamente como 'otro'" (decisión
    declarada en el YAML). Solo lo primero es un fallo: significa que un archivo
    nuevo podría entrar al orden canónico sin que nadie lo haya decidido.
    """
    sin_regla = resumen.archivos_sin_capa
    return _regla(
        "R8", "Todo archivo tiene capa asignada por una regla explícita en capas.yaml",
        PASA if not sin_regla else FALLA,
        f"{len(sin_regla)} archivo(s) sin regla explícita; "
        f"clasificados explícitamente como 'otro': {len(resumen.archivos_en_otro)}. "
        f"Distribución: {resumen.capas_usadas}.",
        {"sin_regla_explicita": sin_regla,
         "explicitamente_otro": resumen.archivos_en_otro,
         "distribucion": resumen.capas_usadas},
    )


def r9_cobertura_fichas(inventario: pd.DataFrame, real_files: list[str], resumen) -> dict:
    fichas = sorted(config.ANALISIS_DIR.glob("*.json"))
    n_doc, n_real, n_fichas = len(inventario), len(set(real_files)), len(fichas)
    estado = PASA if n_fichas == n_doc == n_real else (ADVERTENCIA if n_fichas == n_doc else FALLA)
    return _regla(
        "R9", "Cobertura de fichas de análisis == archivos documentados y reales",
        estado,
        f"inventario={n_doc}; archivos reales (git ls-files)={n_real}; fichas en data/analisis_codigo={n_fichas}.",
        {"inventario": n_doc, "reales": n_real, "fichas": n_fichas,
         "solo_reales": resumen.archivos_solo_reales[:10],
         "solo_documentados": resumen.archivos_solo_documentados[:10]},
    )


def r10_integridad_grafo(g, objetivos) -> dict:
    problemas = []
    # cada Criterio debe tener sus PDF compilados
    for o in objetivos:
        for nombre in (f"objetivo_{o['id']}.pdf", f"objetivo_{o['id']}_lite.pdf"):
            if not (config.PDF / nombre).exists():
                problemas.append(f"Falta PDF: {nombre}")
    # cada Documento del grafo debe existir en disco
    for n, d in g.nodes(data=True):
        if d["tipo"] == "Documento" and d.get("variante") == "completo" and d["nombre"].startswith("objetivo_"):
            if not (config.LATEX / d["nombre"] / "main.tex").exists():
                problemas.append(f"Documento sin main.tex: {d['nombre']}")
    # aristas a nodos inexistentes
    for u, v in g.edges():
        if u not in g or v not in g:
            problemas.append(f"Arista rota: {u} -> {v}")
    return _regla(
        "R10", "Integridad referencial del grafo (PDF, documentos y aristas)",
        PASA if not problemas else FALLA,
        f"{g.number_of_nodes()} nodos y {g.number_of_edges()} aristas revisados; {len(problemas)} problema(s).",
        {"problemas": problemas[:15]},
    )


def r11_rag_cubre_corpus(mem: rag.MemoriaSemantica, objetivos) -> dict:
    docs_indexados = {f.documento for f in mem.fragmentos}
    esperados = set()
    for o in objetivos:
        esperados.add(f"objetivo_{o['id']}")
        esperados.add(f"objetivo_{o['id']}_lite")
    esperados.add("maestro_auditoria")
    esperados |= {p.name for p in config.VALIDACION_DIR.glob("*.md")}
    faltan = sorted(esperados - docs_indexados)
    # consulta de humo: debe recuperar algo
    prueba = mem.consultar("criterio de la rúbrica auditoría del repositorio", k=3)
    estado = PASA if (not faltan and prueba) else FALLA
    return _regla(
        "R11", "El índice RAG cubre todo el corpus declarado y responde consultas",
        estado,
        f"documentos en el índice={len(docs_indexados)}; esperados={len(esperados)}; faltan={len(faltan)}; "
        f"consulta de prueba devolvió {len(prueba)} fragmento(s).",
        {"faltantes": faltan,
         "prueba": [{"documento": p["documento"], "seccion": p["seccion"], "puntaje": p["puntaje"]} for p in prueba]},
    )


def r12_duplicados_y_lite(mem: rag.MemoriaSemantica) -> dict:
    """
    Dos comprobaciones distintas, para no mezclar métricas:

      (a) REGLA DEL PROYECTO (la que aplica la build): la SECCIÓN PRINCIPAL
          (03_*.tex) del LITE debe ser ≤ 40 % de la del documento completo.
          Si se incumple → FALLA.
      (b) DUPLICADOS LITERALES entre documentos (secciones idénticas palabra por
          palabra): revela qué se copia (p. ej. contexto o conclusiones) →
          ADVERTENCIA, no fallo.
    """
    pares = []
    for i in range(1, 7):
        def _palabras(doc: str, prefijo: str | None = None) -> int:
            return sum(f.n_palabras for f in mem.fragmentos
                       if f.documento == doc and (prefijo is None or f.seccion.startswith(prefijo)))
        pc_p = _palabras(f"objetivo_{i}", "03_")
        pl_p = _palabras(f"objetivo_{i}_lite", "03_")
        pc_t = _palabras(f"objetivo_{i}")
        pl_t = _palabras(f"objetivo_{i}_lite")
        pct_p = round(100 * pl_p / pc_p, 1) if pc_p else None
        pares.append({
            "criterio": i,
            "principal_completo": pc_p, "principal_lite": pl_p, "principal_pct": pct_p,
            "cumple_40_principal": bool(pct_p is not None and pct_p <= 40.0),
            "total_completo": pc_t, "total_lite": pl_t,
            "total_pct": round(100 * pl_t / pc_t, 1) if pc_t else None,
        })
    incumplen = [p for p in pares if not p["cumple_40_principal"]]

    por_texto: dict[str, list[str]] = {}
    for f in mem.fragmentos:
        por_texto.setdefault(f.texto.strip().lower(), []).append(f"{f.documento}::{f.seccion}")
    duplicados = {k[:70]: sorted(set(v)) for k, v in por_texto.items() if len(set(v)) > 1}

    estado = FALLA if incumplen else (ADVERTENCIA if duplicados else PASA)
    return _regla(
        "R12", "LITE ≤ 40 % de la sección principal del completo (y sin copias literales)",
        estado,
        f"Pares completo/LITE que incumplen el 40 % en su sección principal: {len(incumplen)}; "
        f"secciones copiadas literalmente entre documentos: {len(duplicados)}.",
        {"ratios": pares, "duplicados": duplicados},
    )


def r13_frescura_indice(mem: rag.MemoriaSemantica) -> dict:
    """
    ¿El índice RAG está actualizado respecto a los documentos fuente?

    Motivo (defecto detectado al aplicar los fixes): tras regenerar los
    documentos desde el YAML, el índice seguía apuntando al texto antiguo, de
    modo que R4 y R12 daban resultados obsoletos (falsos duplicados). Esta regla
    compara la fecha del índice con la del documento fuente más reciente.
    """
    import datetime as _dt

    # Solo se vigilan las fuentes que PERTENECEN al corpus indexado (criterios +
    # LITE + maestro + informes de validación). Así, editar el anteproyecto —que
    # no forma parte de la memoria semántica— no invalida el índice ni genera
    # advertencias falsas.
    fuentes: list = []
    for proyecto in config.PROYECTOS_CORPUS:
        fuentes += list((config.LATEX / proyecto).rglob("secciones/*.tex"))
    fuentes += list(config.VALIDACION_DIR.glob("*.md"))
    if not fuentes or not config.RAG_INDICE_META.exists():
        return _regla("R13", "El índice RAG está actualizado respecto a las fuentes",
                      ADVERTENCIA, "No se pudo comparar: faltan fuentes o metadatos del índice.", {})
    fuente_max = max(f.stat().st_mtime for f in fuentes)
    indice_mtime = config.RAG_INDICE_META.stat().st_mtime
    desfase_min = (indice_mtime - fuente_max) / 60.0
    viejo = indice_mtime < fuente_max
    return _regla(
        "R13", "El índice RAG está actualizado respecto a las fuentes",
        ADVERTENCIA if viejo else PASA,
        ("El índice es MÁS ANTIGUO que algún documento fuente: hay que reindexar "
         "(`python -m memoria indexar`) antes de confiar en R4/R12."
         if viejo else
         f"Índice al día: posterior al documento fuente más reciente por {desfase_min:.1f} min."),
        {"documento_fuente_mas_reciente": _dt.datetime.fromtimestamp(fuente_max).isoformat(timespec="seconds"),
         "indice": _dt.datetime.fromtimestamp(indice_mtime).isoformat(timespec="seconds"),
         "desfase_min": round(desfase_min, 1), "desactualizado": viejo},
    )


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
def ejecutar(refrescar_git: bool = False, verbose: bool = True) -> dict:
    config.asegurar_memoria()
    objetivos = yaml.safe_load(config.OBJETIVOS_YAML.read_text(encoding="utf-8"))["objetivos"]
    glosario = yaml.safe_load(config.GLOSARIO_YAML.read_text(encoding="utf-8"))["glosario"]
    inventario = pd.read_csv(config.INVENTARIO_CSV)
    timeline = pd.read_csv(config.COMMITS_CSV)
    real = grafo.git_log_real(refrescar=refrescar_git)
    archivos = grafo.git_archivos_reales(refrescar=refrescar_git)

    g, resumen = grafo.construir(refrescar_git=refrescar_git, guardar=True)
    mem = rag.MemoriaSemantica()
    if config.RAG_CHUNKS.exists():
        mem.cargar()
    else:
        mem.indexar()

    resultados = [
        r1_documentos_por_criterio(objetivos, g),
        r2_conclusiones_completos(objetivos),
        r3_veredicto_lite(objetivos),
        r4_glosario_usado(glosario, resumen),
        r5_timeline_vs_git(real, timeline),
        r6_archivos_en_documento_codigo(g, archivos),
        r7_commit_auditado(resumen),
        r8_capas_asignadas(resumen, inventario),
        r9_cobertura_fichas(inventario, archivos, resumen),
        r10_integridad_grafo(g, objetivos),
        r11_rag_cubre_corpus(mem, objetivos),
        r12_duplicados_y_lite(mem),
        r13_frescura_indice(mem),
    ]
    conteo = Counter(r["estado"] for r in resultados)
    informe = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "commit_auditado": resumen.commit_auditado,
        "grafo": {"nodos": resumen.total_nodos, "aristas": resumen.total_aristas,
                  "nodos_por_tipo": resumen.nodos_por_tipo,
                  "aristas_por_relacion": resumen.aristas_por_relacion},
        "rag": mem.meta,
        "reglas": resultados,
        "resumen": {"total": len(resultados), "PASA": conteo.get(PASA, 0),
                    "FALLA": conteo.get(FALLA, 0), "ADVERTENCIA": conteo.get(ADVERTENCIA, 0)},
    }
    config.VALIDACION_JSON.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    if verbose:
        print(f"[memoria] grafo: {resumen.total_nodos} nodos / {resumen.total_aristas} aristas "
              f"| RAG: {mem.meta.get('n_fragmentos', len(mem.fragmentos))} fragmentos")
        for r in resultados:
            print(f"  [{r['estado']:11s}] {r['id']}: {r['descripcion']}")
            print(f"               {r['detalle']}")
        print(f"[memoria] reglas: {conteo.get(PASA,0)} PASA, {conteo.get(FALLA,0)} FALLA, "
              f"{conteo.get(ADVERTENCIA,0)} ADVERTENCIA")
    return informe


def antes_de_compilar(forzar: bool = False) -> dict:
    """
    Puerta de validación previa a compilar el PDF final.
    Se invoca desde compilar.py; si alguna regla FALLA, se aborta (salvo --forzar).
    """
    informe = ejecutar(verbose=False)
    fallos = [r for r in informe["reglas"] if r["estado"] == FALLA]
    avisos = [r for r in informe["reglas"] if r["estado"] == ADVERTENCIA]
    informe["abortar"] = bool(fallos) and not forzar
    conteo = informe["resumen"]
    print(f"[memoria] validación previa: {conteo['PASA']} PASA, {conteo['FALLA']} FALLA, "
          f"{conteo['ADVERTENCIA']} ADVERTENCIA (de {conteo['total']} reglas)")
    for r in avisos:
        print(f"  [ADVERTENCIA] {r['id']}: {r['detalle']}")
    for r in fallos:
        print(f"  [FALLA] {r['id']}: {r['descripcion']}\n          {r['detalle']}")
    if fallos and forzar:
        print("[memoria] --forzar activo: se continúa pese a los fallos.")
    return informe
