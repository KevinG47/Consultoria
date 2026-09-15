# -*- coding: utf-8 -*-
"""
memoria.grafo
=============

Memoria estructural del agente: un grafo explícito del proyecto.

Modelo
------
Criterio (rúbrica) --tiene_documento--> Documento (completo | LITE)
Documento --usa_termino--> TerminoGlosario
ArchivoCodigo --pertenece_a--> Capa
Documento(criterio 3) --documenta--> ArchivoCodigo
Commit --tiene_autor--> Autor
Documento(criterio 6 / maestro) --documenta--> Commit
Criterio --verificado_por--> Documento(validación)

Datos vivos del repo auditado
-----------------------------
El grafo NO usa una copia congelada: ejecuta `git log` y `git ls-files` sobre
el clon real (commit auditado 1528939) para obtener commits y archivos de
código reales, y los compara con lo documentado. Los resultados se cachean en
data/memoria/ (git_log_real.csv, git_ls_files_real.txt) para no repetir la
llamada a git en cada validación; se refrescan con --refrescar-git.

Escala
------
Decenas/cientos de nodos: un grafo en memoria con networkx es suficiente. No se
levanta un motor externo (Neo4j/Memgraph) porque no hay volumen, concurrencia ni
consultas de grafos complejas que lo justifiquen.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import networkx as nx
import pandas as pd
import yaml

from . import config
from .rag import limpiar_latex, limpiar_markdown


# --------------------------------------------------------------------------
# Datos vivos del repo auditado (git real)
# --------------------------------------------------------------------------
def _git(clon: Path, *args: str, timeout: int = 900) -> str:
    r = subprocess.run(["git", "-C", str(clon), *args],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falló: {r.stderr[:300]}")
    return r.stdout or ""


def git_log_real(refrescar: bool = False) -> pd.DataFrame:
    """Commits reales del repo auditado (`git log`), cacheados en CSV."""
    config.asegurar_memoria()
    if config.GIT_LOG_CACHE.exists() and not refrescar:
        return pd.read_csv(config.GIT_LOG_CACHE)
    salida = _git(config.CLON, "log", "--pretty=format:%H|%h|%ad|%an|%ae|%s", "--date=short")
    filas = []
    for linea in salida.splitlines():
        if not linea.strip():
            continue
        partes = linea.split("|", 5)
        if len(partes) < 6:
            continue
        filas.append({
            "hash_completo": partes[0],
            "hash": partes[1],
            "fecha": partes[2],
            "autor": partes[3],
            "email": partes[4],
            "asunto": partes[5],
        })
    df = pd.DataFrame(filas)
    df.to_csv(config.GIT_LOG_CACHE, index=False, encoding="utf-8")
    return df


def git_archivos_reales(refrescar: bool = False) -> list[str]:
    """Archivos de CÓDIGO rastreados por git en el repo auditado (estado real)."""
    config.asegurar_memoria()
    if config.GIT_FILES_CACHE.exists() and not refrescar:
        return [l.strip() for l in config.GIT_FILES_CACHE.read_text(encoding="utf-8").splitlines() if l.strip()]
    salida = _git(config.CLON, "ls-files")
    todos = [l.strip() for l in salida.splitlines() if l.strip()]
    codigo = [p for p in todos if Path(p).suffix.lower() in config.EXTS_CODIGO]
    config.GIT_FILES_CACHE.write_text("\n".join(codigo), encoding="utf-8")
    return codigo


def commit_auditado_real() -> str:
    return _git(config.CLON, "rev-parse", "--short", "HEAD").strip()


# --------------------------------------------------------------------------
# Metadatos documentados
# --------------------------------------------------------------------------
def _texto_documento(proyecto: str) -> str:
    d = config.LATEX / proyecto
    if not d.exists():
        return ""
    return "\n".join(
        limpiar_latex(p.read_text(encoding="utf-8", errors="replace"))
        for p in sorted(d.rglob("secciones/*.tex"))
    )


def _texto_validaciones() -> str:
    return "\n".join(
        limpiar_markdown(p.read_text(encoding="utf-8", errors="replace"))
        for p in sorted(config.VALIDACION_DIR.glob("*.md"))
    )


def _usa_termino(texto_minusculas: str, claves: list[str]) -> bool:
    """
    ¿El texto usa realmente el término? Se exige COINCIDENCIA POR PALABRA COMPLETA.

    Motivo (bug detectado al ejecutar sobre datos reales): con coincidencia por
    subcadena, la clave "etl" del glosario hacía match dentro de \\setLength /
    \\setlist, generando falsos positivos. Con \\b se evita.
    """
    for clave in claves:
        if re.search(r"\b" + re.escape(clave.lower()) + r"\b", texto_minusculas):
            return True
    return False


# --------------------------------------------------------------------------
# Construcción del grafo
# --------------------------------------------------------------------------
@dataclass
class ResumenGrafo:
    nodos_por_tipo: dict
    aristas_por_relacion: dict
    total_nodos: int
    total_aristas: int
    commit_auditado: str
    commits_reales: int
    commits_documentados: int
    archivos_codigo_reales: int
    archivos_documentados: int
    archivos_solo_reales: list
    archivos_solo_documentados: list
    terminos_usados: int
    terminos_no_usados: list
    capas_usadas: dict
    archivos_sin_capa: list


def construir(refrescar_git: bool = False, guardar: bool = True) -> tuple[nx.DiGraph, ResumenGrafo]:
    objetivos = yaml.safe_load(config.OBJETIVOS_YAML.read_text(encoding="utf-8"))["objetivos"]
    glosario = yaml.safe_load(config.GLOSARIO_YAML.read_text(encoding="utf-8"))["glosario"]
    capas = yaml.safe_load(config.CAPAS_YAML.read_text(encoding="utf-8"))
    inventario = pd.read_csv(config.INVENTARIO_CSV)
    timeline = pd.read_csv(config.COMMITS_CSV)

    g = nx.DiGraph()

    # --- Criterios y documentos (LaTeX) ---
    textos_doc: dict[str, str] = {}
    for o in objetivos:
        cid = f"criterio_{o['id']}"
        g.add_node(cid, tipo="Criterio", titulo=o["titulo"],
                   secciones_principales=o.get("secciones_principales", []))
        for sufijo, tipo_doc in (("", "completo"), ("_lite", "lite")):
            nombre = f"objetivo_{o['id']}{sufijo}"
            if not (config.LATEX / nombre).exists():
                continue
            doc = f"doc::{nombre}"
            textos_doc[nombre] = _texto_documento(nombre)
            g.add_node(doc, tipo="Documento", nombre=nombre, variante=tipo_doc,
                       ruta=f"latex/{nombre}", palabras=len(textos_doc[nombre].split()))
            g.add_edge(cid, doc, rel="tiene_documento", variante=tipo_doc)
        # maestro
        if (config.LATEX / "maestro_auditoria").exists():
            textos_doc["maestro_auditoria"] = _texto_documento("maestro_auditoria")
            dm = "doc::maestro_auditoria"
            g.add_node(dm, tipo="Documento", nombre="maestro_auditoria", variante="completo",
                       ruta="latex/maestro_auditoria", palabras=len(textos_doc["maestro_auditoria"].split()))
            for c in [f"criterio_{o['id']}" for o in objetivos]:
                g.add_edge(c, dm, rel="consolidado_en")

    # --- Criterio -> informes de validación que lo cubren ---
    texto_val = _texto_validaciones()
    for val in sorted(config.VALIDACION_DIR.glob("*.md")):
        vd = f"validacion::{val.name}"
        g.add_node(vd, tipo="DocumentoValidacion", nombre=val.name,
                   ruta=str(val.relative_to(config.RAIZ)), kb=round(val.stat().st_size / 1024, 1))
        for o in objetivos:
            if f"criterio {o['id']}" in val.name.lower() or f"_d" in val.name.lower() and o["id"] in (1, 2, 3, 4, 5):
                pass
        # relación genérica: los informes D/S validan el bloque documento/sustentación
        if val.name.endswith("_D.md") or "rubrica" in val.name or "factica" in val.name:
            for o in objetivos:
                g.add_edge(f"criterio_{o['id']}", vd, rel="verificado_por")

    # --- Glosario: términos y su uso real en los documentos ---
    terminos_usados, terminos_no_usados = [], []
    corpus_docs = "\n".join(textos_doc.values()).lower()
    for i, term in enumerate(glosario, start=1):
        tid = f"termino_{i}"
        usados_en = []
        for nombre, texto in textos_doc.items():
            if _usa_termino(texto.lower(), term["claves"]):
                usados_en.append(nombre)
        g.add_node(tid, tipo="TerminoGlosario", termino=term["termino"],
                   claves=term["claves"], n_documentos_que_lo_usan=len(usados_en))
        (terminos_usados if usados_en else terminos_no_usados).append(term["termino"])
        for nombre in usados_en:
            g.add_edge(f"doc::{nombre}", tid, rel="usa_termino")

    # --- Capas y archivos de código ---
    for capa in capas["orden"]:
        g.add_node(f"capa::{capa}", tipo="Capa", nombre=capa)

    def capa_de(ruta: str) -> str:
        norm = ruta.replace("\\", "/").lower()
        for capa in capas["orden"]:
            for pref in capas["reglas"].get(capa, []):
                if norm.startswith(pref.lower()):
                    return capa
        return "otro"

    codigo_real = git_archivos_reales(refrescar=refrescar_git)
    doc_inv = {str(r).replace("\\", "/") for r in inventario["ruta"]}
    real_norm = {p.replace("\\", "/") for p in codigo_real}
    solo_reales = sorted(real_norm - doc_inv)
    solo_doc = sorted(doc_inv - real_norm)

    capas_usadas: dict[str, int] = {}
    archivos_sin_capa: list[str] = []
    for ruta in sorted(real_norm | doc_inv):
        nodo = f"archivo::{ruta}"
        capa = capa_de(ruta)
        g.add_node(nodo, tipo="ArchivoCodigo", ruta=ruta,
                   documentado=ruta in doc_inv, real=ruta in real_norm)
        g.add_edge(nodo, f"capa::{capa}", rel="pertenece_a")
        capas_usadas[capa] = capas_usadas.get(capa, 0) + 1
        if capa == "otro":
            archivos_sin_capa.append(ruta)

    # --- Documento del criterio de código -> archivos que documenta ---
    doc_codigo = g.nodes["doc::objetivo_3"] if "doc::objetivo_3" in g else None
    if doc_codigo is not None:
        texto_codigo = textos_doc.get("objetivo_3", "")
        for ruta in sorted(real_norm):
            base = Path(ruta).name
            if base in texto_codigo or ruta in texto_codigo:
                g.add_edge("doc::objetivo_3", f"archivo::{ruta}", rel="documenta")

    # --- Commits y autores (documentados vs reales) ---
    real = git_log_real(refrescar=refrescar_git)
    for _, row in real.iterrows():
        c = f"commit::{row['hash']}"
        g.add_node(c, tipo="Commit", hash=row["hash"], fecha=row["fecha"],
                   asunto=row["asunto"], documentado=False)
        a = f"autor::{row['autor']}"
        g.add_node(a, tipo="Autor", nombre=row["autor"], email=row["email"])
        g.add_edge(c, a, rel="tiene_autor")
    for _, row in timeline.iterrows():
        h = str(row["hash"])[:7]
        c = f"commit::{h}"
        if c not in g:
            g.add_node(c, tipo="Commit", hash=h, fecha=str(row["fecha"]),
                       asunto=str(row["asunto"]), documentado=True)
        else:
            g.nodes[c]["documentado"] = True
        a = f"autor::{row['autor']}"
        g.add_node(a, tipo="Autor", nombre=str(row["autor"]), email=str(row.get("email", "")))
        g.add_edge(c, a, rel="tiene_autor")
        g.add_edge("doc::objetivo_6", c, rel="documenta")

    # --- Resumen ---
    nodos_por_tipo: dict[str, int] = {}
    for _, d in g.nodes(data=True):
        nodos_por_tipo[d["tipo"]] = nodos_por_tipo.get(d["tipo"], 0) + 1
    aristas: dict[str, int] = {}
    for _, _, d in g.edges(data=True):
        aristas[d.get("rel", "?")] = aristas.get(d.get("rel", "?"), 0) + 1

    resumen = ResumenGrafo(
        nodos_por_tipo=nodos_por_tipo,
        aristas_por_relacion=aristas,
        total_nodos=g.number_of_nodes(),
        total_aristas=g.number_of_edges(),
        commit_auditado=commit_auditado_real(),
        commits_reales=len(real),
        commits_documentados=len(timeline),
        archivos_codigo_reales=len(real_norm),
        archivos_documentados=len(doc_inv),
        archivos_solo_reales=solo_reales,
        archivos_solo_documentados=solo_doc,
        terminos_usados=len(terminos_usados),
        terminos_no_usados=terminos_no_usados,
        capas_usadas=capas_usadas,
        archivos_sin_capa=archivos_sin_capa,
    )

    if guardar:
        config.asegurar_memoria()
        config.GRAFO_JSON.write_text(
            json.dumps(nx.node_link_data(g, edges="aristas"), ensure_ascii=False),
            encoding="utf-8")
        config.GRAFO_RESUMEN.write_text(
            json.dumps({
                "fecha": datetime.now().isoformat(timespec="seconds"),
                **{k: v for k, v in resumen.__dict__.items()},
            }, ensure_ascii=False, indent=2),
            encoding="utf-8")
    return g, resumen
