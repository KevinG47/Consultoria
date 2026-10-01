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
cobertura de fichas, integridad referencial y consistencia del propio RAG);
R13–R14 vigilan la frescura del índice y las contradicciones numéricas entre
documentos; R15–R16, la trazabilidad de decisiones y de fuentes externas; y
R17, que las cifras del sistema citadas en los documentos (incluidos el recuento
de estados 15 PASA · 1 FALLA · 1 ADVERTENCIA y los estados de regla del banco)
coincidan con las fuentes de verdad (raíz: el fix D008 dejó cifras obsoletas sin
que nadie lo notara).
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
    esperados.add("anteproyecto")          # documento que califica el docente
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


def r14_consistencia_numerica() -> dict:
    """
    Contradicciones NUMÉRICAS entre documentos (no solo duplicados literales).

    Reutiliza la lógica de `src/verificar_consistencia.py` (importada, no
    duplicada): compara las cifras citadas en prosa contra los conteos reales de
    las fuentes (commits, archivos, scripts, criterios, fichas y líneas de
    cobertura). Así R12 cubre el texto repetido y R14 las cifras incoherentes.
    """
    import importlib.util

    ruta = config.DOC / "src" / "verificar_consistencia.py"
    if not ruta.exists():
        return _regla("R14", "Sin contradicciones numéricas entre documentos",
                      ADVERTENCIA, f"No se encontró {ruta.name}; no se pudo verificar.", {})
    spec = importlib.util.spec_from_file_location("verificar_consistencia", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)              # type: ignore[union-attr]
    comprobaciones = modulo.ejecutar()
    fallos = [c for c in comprobaciones if not c["ok"]]
    return _regla(
        "R14", "Sin contradicciones numéricas entre documentos",
        FALLA if fallos else PASA,
        f"{len(comprobaciones) - len(fallos)}/{len(comprobaciones)} comprobaciones numéricas OK "
        f"(cifras de commits/archivos/scripts/criterios, preguntas enumeradas y cobertura).",
        {"fallos": [c["nombre"] + " — " + c["detalle"] for c in fallos],
         "comprobaciones": len(comprobaciones)},
    )


# --------------------------------------------------------------------------
# R15 / R16 — trazabilidad de decisiones y fuentes externas
# --------------------------------------------------------------------------
def _cargar_decisiones() -> list[dict]:
    if not config.DECISIONES_YAML.exists():
        return []
    d = yaml.safe_load(config.DECISIONES_YAML.read_text(encoding="utf-8")) or {}
    return d.get("decisiones", [])


def _texto_archivo(rel: str) -> str:
    p = config.RAIZ / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def r15_decisiones_vs_codigo(mem: rag.MemoriaSemantica) -> dict:
    """
    Coherencia trazable entre lo decidido y lo que se está usando.

    Comprueba:
      1. Integridad de la cadena de supersesión (referencias existentes, sin ciclos).
      2. Una sola decisión actual por tema (no puede haber dos vigentes).
      3. Ninguna decisión SUPERADA puede seguir implementada en el código.
      4. El código debe reflejar la decisión ACTUAL del tema; si la actual está
         `pendiente_implementacion` y el marcador no existe, es un desfase real
         y la regla FALLA (salvo excepción temporal declarada, que la degrada a
         ADVERTENCIA y queda registrada).
      5. Los documentos del corpus no deben presentar una decisión superada como
         si fuera la actual.
    """
    decisiones = _cargar_decisiones()
    if not decisiones:
        return _regla("R15", "Las decisiones vigentes coinciden con el código y los documentos",
                      ADVERTENCIA, "No hay bitácora de decisiones (decisiones.yaml).", {})

    por_id = {d["id"]: d for d in decisiones}
    problemas: list[str] = []
    avisos: list[str] = []
    evidencia: dict = {"decisiones": len(decisiones)}

    # 1. Integridad de la cadena de supersesión
    for d in decisiones:
        for campo in ("superada_por", "supersede"):
            ref = d.get(campo)
            if not ref:
                continue
            if ref not in por_id:
                problemas.append(f"{d['id']}: {campo} apunta a un id inexistente ({ref})")
            elif campo == "superada_por" and por_id[ref].get("supersede") != d["id"]:
                problemas.append(f"{d['id']}: {ref} no declara supersede de {d['id']} (relación asimétrica)")
        if d.get("estado") == "superada" and not (d.get("superada_por") or d.get("supersede")):
            problemas.append(f"{d['id']}: estado 'superada' sin referencia a quién la reemplaza")

    # 2. Una sola decisión actual por tema
    por_tema: dict[str, list[dict]] = {}
    for d in decisiones:
        if d.get("estado") in ("vigente", "pendiente_implementacion"):
            por_tema.setdefault(d.get("tema", "sin_tema"), []).append(d)
    for tema, ds in por_tema.items():
        if len(ds) > 1:
            problemas.append(f"tema '{tema}' tiene {len(ds)} decisiones actuales: "
                             + ", ".join(x["id"] for x in ds))

    # 3 y 4. Código vs decisión superada / actual
    corpus = "\n".join(f.texto for f in mem.fragmentos)
    for d in decisiones:
        impl = d.get("implementacion") or {}
        marcador = impl.get("marcador_codigo")
        archivos = impl.get("archivos") or []
        if not marcador or not archivos:
            continue
        textos = {a: _texto_archivo(a) for a in archivos}
        presente = {a: (marcador.lower() in t.lower()) for a, t in textos.items()}
        if d.get("estado") == "superada" and any(presente.values()):
            donde = ", ".join(a for a, v in presente.items() if v)
            problemas.append(
                f"{d['id']} está SUPERADA ({d.get('superada_por') or d.get('supersede')}) "
                f"pero su implementación sigue en el código: '{marcador}' en {donde}")
        if d.get("estado") in ("vigente", "pendiente_implementacion") and not any(presente.values()):
            excepcion = impl.get("excepto_si")
            msg = (f"{d['id']} (estado {d['estado']}) no está implementada: no aparece "
                   f"'{marcador}' en {', '.join(archivos)}")
            if excepcion:
                avisos.append(msg + f" — excepción declarada: {excepcion.get('motivo','')} "
                                    f"(hasta {excepcion.get('hasta','sin fecha')})")
            else:
                problemas.append(msg)

    # 5. Documentos que presentan una decisión superada como actual
    docs_superados: list[str] = []
    for d in decisiones:
        if d.get("estado") != "superada":
            continue
        marca_doc = (d.get("implementacion") or {}).get("marcador_doc")
        if not marca_doc:
            continue
        en_corpus = marca_doc.lower() in corpus.lower()
        sucesor = por_id.get(d.get("superada_por") or d.get("supersede") or "")
        # Si los documentos mencionan TAMBIÉN la técnica sucesora, la transición
        # está declarada explícitamente y no es un problema (es justo lo que el
        # docente pide: que el cambio quede por escrito).
        marca_sucesor = ((sucesor or {}).get("implementacion") or {}).get("marcador_doc")
        transicion_declarada = bool(marca_sucesor and marca_sucesor.lower() in corpus.lower())
        if en_corpus and not transicion_declarada:
            docs_superados.append(
                f"{d['id']}: los documentos siguen citando '{marca_doc}' sin declarar el cambio a "
                f"{sucesor['id'] if sucesor else 'su sucesora'} "
                f"(basta mencionar '{marca_sucesor or 'la técnica sucesora'}' para declararlo)")

    evidencia.update({"problemas": problemas, "avisos": avisos,
                      "documentos_con_decision_superada": docs_superados,
                      "decisiones_actuales_por_tema": {k: [x["id"] for x in v] for k, v in por_tema.items()}})
    if problemas:
        estado = FALLA
    elif avisos:
        estado = ADVERTENCIA
    else:
        estado = PASA
    detalle = (f"{len(decisiones)} decisiones registradas; {len(problemas)} desfase(s) "
               f"código/documentos, {len(avisos)} excepción(es) declarada(s), "
               f"{len(docs_superados)} mención(es) de decisiones superadas en documentos.")
    return _regla("R15", "Las decisiones vigentes coinciden con el código y los documentos",
                  estado, detalle, evidencia)


def r16_integridad_registros() -> dict:
    """
    Integridad de los registros de trazabilidad (fuentes_externas.yaml y
    decisiones.yaml): ids únicos, campos obligatorios y — sobre todo — que no
    queden URLs en "PENDIENTE" en la versión que se entrega.
    """
    problemas: list[str] = []
    fuentes: list[dict] = []
    if config.FUENTES_YAML.exists():
        fuentes = (yaml.safe_load(config.FUENTES_YAML.read_text(encoding="utf-8")) or {}).get("fuentes", [])
    else:
        problemas.append("No existe data/memoria/fuentes_externas.yaml")

    requeridos_f = ["id", "url", "fecha_consulta", "usado_para", "documento"]
    vistos: set[str] = set()
    for f in fuentes:
        faltan = [c for c in requeridos_f if not str(f.get(c, "")).strip()]
        if faltan:
            problemas.append(f"{f.get('id','?')}: faltan campos {faltan}")
        if f.get("id") in vistos:
            problemas.append(f"id de fuente duplicado: {f.get('id')}")
        vistos.add(f.get("id"))
        url = str(f.get("url", ""))
        if "PENDIENTE" in url.upper() or not url.strip():
            problemas.append(f"{f.get('id','?')}: URL sin confirmar (marcador PENDIENTE o vacía)")
        elif not (url.startswith("http") or url.startswith("local:")):
            problemas.append(f"{f.get('id','?')}: URL con formato no reconocido ({url[:40]})")

    decisiones = _cargar_decisiones()
    ids_d: set[str] = set()
    for d in decisiones:
        for c in ("id", "fecha", "decision", "justificacion", "estado"):
            if not str(d.get(c, "")).strip():
                problemas.append(f"decisión {d.get('id','?')}: falta '{c}'")
        if d.get("id") in ids_d:
            problemas.append(f"id de decisión duplicado: {d.get('id')}")
        ids_d.add(d.get("id"))
        if d.get("estado") not in ("vigente", "superada", "propuesta", "pendiente_implementacion"):
            problemas.append(f"{d.get('id')}: estado no permitido ({d.get('estado')})")

    return _regla(
        "R16", "Registros de trazabilidad íntegros y sin marcadores PENDIENTE",
        PASA if not problemas else FALLA,
        f"{len(fuentes)} fuentes externas y {len(decisiones)} decisiones registradas; "
        f"{len(problemas)} problema(s) de integridad.",
        {"problemas": problemas, "fuentes": len(fuentes), "decisiones": len(decisiones)},
    )


# --------------------------------------------------------------------------
# R17 — las cifras del sistema citadas en los documentos no se quedan atrás
# --------------------------------------------------------------------------
# Motivo (defecto detectado al cerrar el ciclo del fix D008): al corregir el
# indexador de markdown el corpus pasó de 145 a 150 fragmentos y de 105.167 a
# 116.277 palabras, y la cifra vieja sobrevivió en 6 sitios de la documentación
# sin que NINGUNA de las 16 reglas lo notara. R17 cierra ese hueco: compara toda
# cifra del sistema que ya es fuente de verdad contra cada documento que la cita.
#
# Fuentes de verdad:
#   rag_indice.json    -> fragmentos, palabras, términos del vocabulario
#   grafo_resumen.json -> nodos, aristas
#   decisiones.yaml    -> número de decisiones registradas
#   número de reglas   -> se cuenta EN VIVO en esta ejecución (leer
#                         validacion_reglas.json compararía contra la ejecución
#                         anterior, porque este mismo proceso lo escribe al final)
_DOCS_CIFRAS = [
    "latex/anteproyecto/secciones/06b_memoria_agente.tex",
    "README.md",
    "guia_defensa_sistema_memoria.md",
    "data/memoria/texto_seccion_6_2.md",   # texto justificativo de §6.2 (se quedó atrás dos veces)
    "scripts/banco_preguntas.py",
]

# Número citado: admite separadores de miles (116 277 / 105.167 / 116\,277 / 45 799).
_NUM_CITADO = r"([\d][\d\s.,\u00a0\\~]*)"
# Recuento de estados citado en los documentos: "15 PASA · 1 FALLA · 1 ADVERTENCIA",
# "\textbf{15 PASA, 1 FALLA, 1 ADVERTENCIA}" o la salida de consola
# "[memoria] reglas: 15 PASA, 1 FALLA, 1 ADVERTENCIA". Si R15 cambia de estado
# (p. ej. al implementar D007), los documentos que citan el recuento quedan
# obsoletos y R17 FALLA hasta que se actualicen: es el mismo tipo de error que
# vigilan las demás cifras.
_TALLY_CITADO = (r"(\d{1,2})\s*PASA[^\d\n]{0,24}?(\d{1,2})\s*FALLA"
                 r"[^\d\n]{0,24}?(\d{1,2})\s*ADVERTENCIA")
# Estados de regla citados en el banco de preguntas, p. ej.
#   {"id": 16, ..., "pregunta": "¿Cuál es el resultado de la regla R15?",
#    "esperado": "FALLA", ...}
# El estado se atribuye a la regla R<n> nombrada en la propia pregunta. Si R15
# cambia de estado (por ejemplo al implementar D007) la pregunta queda obsoleta
# y R17 FALLA nombrando el archivo, la línea, la regla y su estado real.
_ESPERADO_ESTADO = re.compile(r'"esperado":\s*"([^"]+)"')
_REGLA_EN_PREGUNTA = re.compile(r"\bR(\d{1,2})\b")
# Números escritos con palabras (el anteproyecto dice "Dieciséis reglas").
_PALABRAS_NUM = {"dieciseis": 16, "diecisiete": 17, "dieciocho": 18,
                 "quince": 15, "catorce": 14, "trece": 13}

# (clave, patrón, mínimo). El mínimo evita confundir la cifra global con cifras
# locales de un ejemplo de consola (p. ej. "[criterio_lite, 69 palabras]" o
# "dibujados 19 nodos de 255 nodos").
_CIFRAS_VIGILADAS = [
    ("fragmentos", _NUM_CITADO + r"\s*fragmentos", 100),
    ("palabras", _NUM_CITADO + r"\s*palabras", 100),
    ("terminos", _NUM_CITADO + r"\s*t[eé]rminos", 100),
    ("nodos", _NUM_CITADO + r"\s*nodos", 100),
    ("aristas", _NUM_CITADO + r"\s*aristas", 100),
    ("reglas", r"(\d{1,2}|diecis[eé]is|diecisiete|trece)\s*reglas", 1),
    ("decisiones", r"(\d{1,2})\s+(?:decisiones|registradas)", 1),
]


def _sin_acentos(texto: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", texto)
                   if not unicodedata.combining(c))


def _citas_de_cifras(texto: str, patron: str, minimo: int) -> list[dict]:
    """Cifras citadas en `texto` que parecen referirse al total del sistema."""
    citas: list[dict] = []
    for m in re.finditer(patron, texto, flags=re.IGNORECASE):
        crudo = m.group(1)
        digitos = re.sub(r"\D", "", crudo)
        valor = int(digitos) if digitos else _PALABRAS_NUM.get(_sin_acentos(crudo.lower()))
        if valor is None or valor < minimo:
            continue
        citas.append({
            "valor": valor,
            "texto": " ".join(m.group(0).split()),
            "linea": texto.count("\n", 0, m.start()) + 1,
        })
    return citas


def _tallies_citados(texto: str) -> list[dict]:
    """Recuentos de estado (PASA / FALLA / ADVERTENCIA) citados en `texto`."""
    return [
        {"pasa": int(m.group(1)), "falla": int(m.group(2)), "advertencia": int(m.group(3)),
         "texto": " ".join(m.group(0).split()), "linea": texto.count("\n", 0, m.start()) + 1}
        for m in re.finditer(_TALLY_CITADO, texto, flags=re.IGNORECASE)
    ]


def _estados_de_regla_citados(texto: str) -> list[dict]:
    """
    Preguntas del banco cuyo campo `esperado` es un ESTADO de regla.

    Se atribuyen a la regla R<n> nombrada en la pregunta. Las citas sin regla
    atribuible se devuelven igual (regla=None) para poder reportarlas: un estado
    afirmado sin fuente identificable es el mismo defecto que R17 persigue.
    """
    citas: list[dict] = []
    for m in _ESPERADO_ESTADO.finditer(texto):
        valor = re.sub(r"[^A-Z]", "", m.group(1).upper())      # "FALLA (R15)" -> "FALLA"
        if valor not in (PASA, FALLA, ADVERTENCIA):
            continue
        previo = texto[max(0, m.start() - 400):m.start()]
        encontradas = _REGLA_EN_PREGUNTA.findall(previo)
        citas.append({
            "regla": f"R{encontradas[-1]}" if encontradas else None,
            "citado": valor,
            "texto": " ".join(m.group(0).split()),
            "linea": texto.count("\n", 0, m.start()) + 1,
        })
    return citas


def r17_cifras_en_documentos(n_reglas: int, estados: list[dict] | None = None,
                             docs: list[str] | None = None) -> dict:
    """
    ¿Las cifras del sistema citadas en los documentos coinciden con las fuentes?

    Si un documento cita la cifra vieja (p. ej. "145 fragmentos" cuando el índice
    ya tiene 150, o "Dieciséis reglas" cuando ya son diecisiete), la regla FALLA
    y nombra archivo y línea. Así la documentación no puede quedarse atrás en
    silencio, que es justo lo que pasó tras el fix D008.

    Vigila también el RECUENTO DE ESTADOS ("15 PASA · 1 FALLA · 1 ADVERTENCIA") y
    los ESTADOS DE REGLA que cita el banco de preguntas (Q16 afirma que R15 da
    FALLA): si una regla cambia de estado —por ejemplo R15 al implementar
    D007—, los documentos y las preguntas que citan el estado anterior quedan
    obsoletos y R17 FALLA hasta que se actualicen.
    """
    esperado: dict[str, int] = {}
    fuentes: dict[str, str] = {}
    if config.RAG_INDICE_META.exists():
        meta = json.loads(config.RAG_INDICE_META.read_text(encoding="utf-8"))
        esperado["fragmentos"] = meta.get("n_fragmentos")
        esperado["palabras"] = meta.get("palabras_totales")
        esperado["terminos"] = meta.get("n_terminos_vocabulario")
        fuentes["fragmentos/palabras/terminos"] = "data/memoria/rag_indice.json"
    if config.GRAFO_RESUMEN.exists():
        resumen_grafo = json.loads(config.GRAFO_RESUMEN.read_text(encoding="utf-8"))
        esperado["nodos"] = resumen_grafo.get("total_nodos")
        esperado["aristas"] = resumen_grafo.get("total_aristas")
        fuentes["nodos/aristas"] = "data/memoria/grafo_resumen.json"
    esperado["reglas"] = n_reglas
    fuentes["reglas"] = "conteo en vivo de esta ejecución"
    if config.DECISIONES_YAML.exists():
        registro = yaml.safe_load(config.DECISIONES_YAML.read_text(encoding="utf-8")) or {}
        esperado["decisiones"] = len(registro.get("decisiones", []))
        fuentes["decisiones"] = "data/memoria/decisiones.yaml"

    # Recuento de estados de ESTA ejecución. R17 se cuenta a sí misma en PASA: es
    # el punto fijo coherente, porque el recuento que los documentos deben citar
    # es el del sistema funcionando. Si R17 FALLA, el recuento real de la corrida
    # baja a `tally_si_r17_falla`, que se escribe en el detalle.
    conteo = Counter(r["estado"] for r in (estados or []))
    esperado_tally = {PASA: conteo.get(PASA, 0) + 1, FALLA: conteo.get(FALLA, 0),
                      ADVERTENCIA: conteo.get(ADVERTENCIA, 0)}
    tally_si_falla = dict(esperado_tally)
    tally_si_falla[PASA] -= 1
    tally_si_falla[FALLA] += 1
    fuentes["tally"] = "estados de esta ejecución (R1..R16) + R17 en PASA"
    estados_por_id = {e["id"]: e["estado"] for e in (estados or [])}
    # Mismo punto fijo que el recuento: al comparar, R17 cuenta como PASA.
    estados_por_id["R17"] = PASA

    revisados = 0
    citas_ok = 0
    citas_estado: list[dict] = []
    problemas: list[str] = []
    for rel in (docs or _DOCS_CIFRAS):
        ruta = config.DOC / rel
        if not ruta.exists():
            continue
        revisados += 1
        texto = ruta.read_text(encoding="utf-8", errors="replace")
        for clave, patron, minimo in _CIFRAS_VIGILADAS:
            if esperado.get(clave) is None:
                continue
            for cita in _citas_de_cifras(texto, patron, minimo):
                if cita["valor"] == esperado[clave]:
                    citas_ok += 1
                else:
                    problemas.append(
                        f"{rel}:{cita['linea']} cita \"{cita['texto']}\" pero {clave} = {esperado[clave]}"
                    )
        for cita in _tallies_citados(texto):
            if (cita["pasa"], cita["falla"], cita["advertencia"]) == (
                    esperado_tally[PASA], esperado_tally[FALLA], esperado_tally[ADVERTENCIA]):
                citas_ok += 1
            else:
                problemas.append(
                    f"{rel}:{cita['linea']} cita \"{cita['texto']}\" pero el recuento real es "
                    f"{esperado_tally[PASA]} PASA / {esperado_tally[FALLA]} FALLA / "
                    f"{esperado_tally[ADVERTENCIA]} ADVERTENCIA"
                )
        # Estados de regla citados en el banco de preguntas (Q16: R15 = FALLA).
        if estados and rel.endswith("banco_preguntas.py"):
            for cita in _estados_de_regla_citados(texto):
                citas_estado.append(cita)
                real = estados_por_id.get(cita["regla"])
                if real is None:
                    problemas.append(
                        f"{rel}:{cita['linea']} cita el estado \"{cita['citado']}\" de "
                        f"{cita['regla'] or 'una regla sin identificar en la pregunta'}, "
                        f"que no se puede atribuir a ninguna regla de esta ejecución"
                    )
                elif cita["citado"] != real:
                    problemas.append(
                        f"{rel}:{cita['linea']} cita el estado \"{cita['citado']}\" de "
                        f"{cita['regla']} pero su estado real es {real}"
                    )
                else:
                    citas_ok += 1

    return _regla(
        "R17",
        "Las cifras del sistema (índice, grafo, reglas, decisiones), el recuento de estados y los estados de regla del banco coinciden con la ejecución real",
        FALLA if problemas else PASA,
        (f"{len(problemas)} cifra(s) desactualizada(s) en {revisados} documento(s) revisado(s) "
         f"(recuento real de esta corrida si R17 falla: {tally_si_falla[PASA]} PASA / "
         f"{tally_si_falla[FALLA]} FALLA / {tally_si_falla[ADVERTENCIA]} ADVERTENCIA): "
         + " | ".join(problemas[:8]) + (" …" if len(problemas) > 8 else ""))
        if problemas else
        f"{revisados} documento(s) revisado(s); {citas_ok} cita(s) de cifras del sistema, "
        f"todas coincidentes con las fuentes de verdad.",
        {"esperado": esperado, "tally_esperado": esperado_tally,
         "tally_si_r17_falla": tally_si_falla, "fuentes": fuentes,
         "documentos": docs or _DOCS_CIFRAS, "citas_correctas": citas_ok,
         "estados_de_regla_citados": citas_estado, "problemas": problemas},
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
        r14_consistencia_numerica(),
        r15_decisiones_vs_codigo(mem),
        r16_integridad_registros(),
    ]
    # R17 se cuenta a sí misma: al llamarla, `resultados` aún no la incluye.
    resultados.append(r17_cifras_en_documentos(n_reglas=len(resultados) + 1,
                                               estados=list(resultados)))
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
