# -*- coding: utf-8 -*-
"""
memoria.config
==============

Rutas y constantes compartidas por el sistema de gestión de información
del agente de IA (memoria semántica + memoria estructural + reglas).

Todas las rutas son relativas a la raíz del repositorio de trabajo
(consultoria/), de modo que el sistema sea reproducible en cualquier clon.
"""

from __future__ import annotations

from pathlib import Path

# --- Raíces ---------------------------------------------------------------
# config.py -> memoria/ -> src/ -> documentacion_auditoria/ -> consultoria/
DOC = Path(__file__).resolve().parents[2]      # documentacion_auditoria/
RAIZ = DOC.parent                              # consultoria/
DATA = DOC / "data"
LATEX = DOC / "latex"
PDF = DOC / "pdf"
MEMORIA = DATA / "memoria"                     # artefactos que produce este sistema
CLON = RAIZ / "Observatorio_Ministerio_de_Ciencias_Grupo8"   # repo auditado (clon real)

# --- Metadatos de entrada (fuente de verdad ya existente) -----------------
CAPAS_YAML = DATA / "capas.yaml"
OBJETIVOS_YAML = DATA / "objetivos.yaml"
GLOSARIO_YAML = DATA / "glosario.yaml"
COMMITS_CSV = DATA / "commits_timeline.csv"
INVENTARIO_CSV = DATA / "inventario_codigo.csv"
ANALISIS_DIR = DATA / "analisis_codigo"
VALIDACION_DIR = DATA / "validacion"

# --- Corpus documental para la memoria semántica --------------------------
# Criterios (completo y LITE): objetivo_1..6 / objetivo_1_lite..6_lite
CRITERIOS = [f"objetivo_{i}" for i in range(1, 7)]
CRITERIOS_LITE = [f"objetivo_{i}_lite" for i in range(1, 7)]
PROYECTOS_CORPUS = CRITERIOS + CRITERIOS_LITE + ["maestro_auditoria", "anteproyecto"]
# Nota: el anteproyecto se incluye porque es el documento que califica el
# docente; así la memoria puede detectar contradicciones contra él.

# Extensiones de código consideradas "código real" del repo auditado
EXTS_CODIGO = {".py", ".r", ".ipynb"}

# Cache de datos vivos extraídos con git (se refresca con --refrescar-git)
GIT_LOG_CACHE = MEMORIA / "git_log_real.csv"
GIT_FILES_CACHE = MEMORIA / "git_ls_files_real.txt"

# Artefactos del sistema
RAG_CHUNKS = MEMORIA / "rag_corpus.jsonl"
RAG_MATRIZ = MEMORIA / "rag_matriz.npz"
RAG_VECTORIZER = MEMORIA / "rag_vectorizer.pkl"
RAG_INDICE_META = MEMORIA / "rag_indice.json"
GRAFO_JSON = MEMORIA / "grafo.json"
GRAFO_RESUMEN = MEMORIA / "grafo_resumen.json"
CONSULTAS_LOG = MEMORIA / "consultas_rag.jsonl"     # bitácora de consultas (antes de redactar)
VALIDACION_JSON = MEMORIA / "validacion_reglas.json"
EVIDENCIA_MD = MEMORIA / "evidencia_validacion.md"

# --- Registros de trazabilidad (requisito del docente) --------------------
FUENTES_YAML = MEMORIA / "fuentes_externas.yaml"   # fuentes externas consultadas
DECISIONES_YAML = MEMORIA / "decisiones.yaml"      # bitácora de decisiones de diseño
GRAFICO_PNG = MEMORIA / "grafo_visual.png"         # salida de `python -m memoria dibujar`


def asegurar_memoria() -> Path:
    """Crea el directorio de artefactos si no existe."""
    MEMORIA.mkdir(parents=True, exist_ok=True)
    return MEMORIA
