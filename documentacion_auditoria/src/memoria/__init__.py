# -*- coding: utf-8 -*-
"""
memoria
=======

Sistema de gestión de información del agente de IA del proyecto
"Auditoría del Observatorio MinCiencias" (USTA 2026-II).

Tres piezas:
    rag.MemoriaSemantica  — memoria semántica (TF-IDF + coseno) del corpus ya escrito.
    grafo.construir       — memoria estructural (networkx) con datos vivos del repo auditado.
    reglas.ejecutar       — reglas de validación que se corren ANTES de compilar el PDF final.

Uso:
    python -m memoria indexar
    python -m memoria consultar "texto a consultar" -k 5
    python -m memoria antes-de-redactar "tema nuevo"
    python -m memoria grafo
    python -m memoria validar [--refrescar-git] [--json]
    python -m memoria evidencia
"""

from .rag import MemoriaSemantica, antes_de_redactar, limpiar_latex, limpiar_markdown  # noqa: F401
from .grafo import construir, git_log_real, git_archivos_reales, commit_auditado_real  # noqa: F401
from .reglas import ejecutar, antes_de_compilar  # noqa: F401

__all__ = [
    "MemoriaSemantica",
    "antes_de_redactar",
    "construir",
    "git_log_real",
    "git_archivos_reales",
    "commit_auditado_real",
    "ejecutar",
    "antes_de_compilar",
    "limpiar_latex",
    "limpiar_markdown",
]
