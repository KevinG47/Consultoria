# -*- coding: utf-8 -*-
"""
memoria.rag
===========

Memoria semántica del agente (RAG ligero).

Qué hace
--------
Indexa el corpus documental YA GENERADO del proyecto para que, antes de
redactar o afirmar algo nuevo, el agente recupere qué se dijo antes sobre ese
tema y no se contradiga entre documentos.

Corpus indexado
---------------
- Secciones LaTeX de los 6 criterios (versión completa y LITE): objetivo_1..6
  y objetivo_1_lite..6_lite  (secciones/*.tex)
- Secciones LaTeX del documento maestro (maestro_auditoria/secciones/*.tex)
- Informes de validación (data/validacion/*.md), troceados por encabezados

Técnica
-------
TF-IDF (scikit-learn) + similitud coseno. Se eligió TF-IDF y no embeddings
porque: (i) el corpus es pequeño (~150 fragmentos), (ii) no hay dependencia de
un proveedor externo ni red, (iii) el vocabulario es técnico y estable, y
(iv) el resultado es determinista y auditable (se puede mostrar el término que
pesa en la recuperación).

Trazabilidad
------------
Cada consulta se registra en data/memoria/consultas_rag.jsonl con su tema, los
fragmentos recuperados y sus puntajes: la consulta queda auditada.
"""

from __future__ import annotations

import json
import pickle
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

from . import config


# --------------------------------------------------------------------------
# Limpieza de LaTeX -> texto plano comparable
# --------------------------------------------------------------------------
_RE_COMENTARIO = re.compile(r"(?m)^\s*%.*$")
_RE_CMD_CON_ARG = re.compile(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?(\{([^{}]*)\})?")
_RE_LLAVES = re.compile(r"[{}$&~^\\]")          # OJO: NO se elimina "_" (rompería rutas como streamlit_app.py)
_RE_ESPACIOS = re.compile(r"\s+")


def _conservar_argumento(m: re.Match) -> str:
    """
    Sustituye un comando LaTeX por EL TEXTO DE SU ARGUMENTO (no lo borra).

    Motivo (bug detectado al ejecutar sobre datos reales): al borrar el
    argumento se perdían los títulos de sección \\subsubsection{ruta/archivo.py},
    y la regla R6 reportaba 6 archivos "no documentados" que sí lo estaban.
    """
    return " " + (m.group(3) or "") + " "


def limpiar_latex(texto: str) -> str:
    """Convierte LaTeX a texto plano legible para el índice."""
    t = _RE_COMENTARIO.sub(" ", texto)
    t = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", " ", t)
    t = re.sub(r"\\input\{[^}]*\}", " ", t)          # no seguir inclusiones: cada archivo es un chunk
    t = t.replace("\\_", "_")                        # \_ -> _ (conserva nombres de archivo y rutas)
    t = _RE_CMD_CON_ARG.sub(_conservar_argumento, t)  # conserva el contenido de \subsection{}, \texttt{}, etc.
    t = _RE_LLAVES.sub(" ", t)
    return _RE_ESPACIOS.sub(" ", t).strip()


# Fila separadora de tabla markdown (`|---|---|`): la línea solo contiene
# pipes, guiones, dos puntos y espacios, y tiene al menos un pipe y un guion.
_RE_FILA_SEPARADORA = re.compile(r"(?m)^[ \t]*(?=[^\n]*\|)(?=[^\n]*-)[|:\- \t]+$")


def limpiar_markdown(texto: str) -> str:
    """
    Quita sintaxis markdown básica (encabezados, énfasis, tablas, código).

    CAMBIO (decisión D008): las tablas se indexan. Antes se hacía
    `re.sub(r"^\\s*\\|.*$", " ", t, flags=re.M)`, que borraba la fila COMPLETA
    antes de indexar: en las 11 fuentes de validación eso descartaba 329 filas
    y el 37 % del texto. Como la evidencia auditada vive en tablas (fichas
    verificadas, contadores, veredictos por ítem), datos como
    `n_atipicos_edad=19` nunca llegaban al índice y 5 de las 20 preguntas del
    banco de evaluación quedaban sin respuesta posible. Ahora solo se eliminan
    los delimitadores `|`, nunca el contenido de la celda.

    Tampoco se elimina `_`: los identificadores (`n_atipicos_edad`,
    `streamlit_app.py`) deben sobrevivir igual que en `limpiar_latex`, que ya
    lo conserva a propósito (ver _RE_LLAVES).
    """
    t = re.sub(r"```.*?```", " ", texto, flags=re.S)
    t = _RE_FILA_SEPARADORA.sub(" ", t)               # |---|---| (no aporta texto)
    t = t.replace("|", " ")                           # delimitadores: inicio, fin e internos
    t = re.sub(r"^\s*[-*]\s+", " ", t, flags=re.M)    # viñetas
    t = re.sub(r"[*`>#]", " ", t)                     # OJO: NO se elimina "_" (ver D008)
    return _RE_ESPACIOS.sub(" ", t).strip()


# --------------------------------------------------------------------------
# Fragmentos (chunks)
# --------------------------------------------------------------------------
@dataclass
class Fragmento:
    id: str
    coleccion: str      # "criterio_completo" | "criterio_lite" | "maestro" | "validacion"
    documento: str      # p. ej. "objetivo_3" | "validacion_final_D.md"
    seccion: str        # archivo .tex o encabezado markdown
    ruta: str
    texto: str
    n_palabras: int


def _chunks_latex() -> list[Fragmento]:
    frags: list[Fragmento] = []
    for proyecto in config.PROYECTOS_CORPUS:
        d = config.LATEX / proyecto
        if not d.exists():
            continue
        if proyecto.startswith("objetivo_"):
            coleccion = "criterio_lite" if proyecto.endswith("_lite") else "criterio_completo"
        elif proyecto == "anteproyecto":
            coleccion = "anteproyecto"      # documento que califica el docente
        else:
            coleccion = "maestro"
        for tex in sorted(d.rglob("secciones/*.tex")):
            crudo = tex.read_text(encoding="utf-8", errors="replace")
            texto = limpiar_latex(crudo)
            if len(texto.split()) < 15:      # portadas y similares no aportan memoria
                continue
            frags.append(Fragmento(
                id=f"{proyecto}::{tex.stem}",
                coleccion=coleccion,
                documento=proyecto,
                seccion=tex.stem,
                ruta=str(tex.relative_to(config.RAIZ)),
                texto=texto,
                n_palabras=len(texto.split()),
            ))
    return frags


def _chunks_validacion() -> list[Fragmento]:
    frags: list[Fragmento] = []
    for md in sorted(config.VALIDACION_DIR.glob("*.md")):
        crudo = md.read_text(encoding="utf-8", errors="replace")
        # trocear por encabezados de nivel 2
        partes = re.split(r"(?m)^##\s+", crudo)
        for i, parte in enumerate(partes):
            lineas = parte.strip().splitlines()
            if not lineas:
                continue
            titulo = lineas[0][:90] if i > 0 else "encabezado"
            texto = limpiar_markdown(parte)
            if len(texto.split()) < 25:
                continue
            frags.append(Fragmento(
                id=f"{md.name}::h{i}",
                coleccion="validacion",
                documento=md.name,
                seccion=titulo,
                ruta=str(md.relative_to(config.RAIZ)),
                texto=texto,
                n_palabras=len(texto.split()),
            ))
    return frags


def construir_fragmentos() -> list[Fragmento]:
    return _chunks_latex() + _chunks_validacion()


# --------------------------------------------------------------------------
# Índice
# --------------------------------------------------------------------------
class MemoriaSemantica:
    """Índice TF-IDF consultable sobre el corpus documental del proyecto."""

    def __init__(self) -> None:
        self.vectorizer: TfidfVectorizer | None = None
        self.matriz: sparse.csr_matrix | None = None
        self.fragmentos: list[Fragmento] = []
        self.meta: dict = {}

    # --- construcción ---
    def indexar(self, guardar: bool = True) -> dict:
        config.asegurar_memoria()
        self.fragmentos = construir_fragmentos()
        if not self.fragmentos:
            raise RuntimeError("Corpus vacío: no hay fragmentos que indexar.")
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
            token_pattern=r"(?u)\b\w[\wáéíóúñü\-]{2,}\b",
        )
        textos = [f.texto for f in self.fragmentos]
        self.matriz = self.vectorizer.fit_transform(textos)
        self.meta = {
            "fecha_construccion": datetime.now().isoformat(timespec="seconds"),
            "n_fragmentos": len(self.fragmentos),
            "n_documentos": len({f.documento for f in self.fragmentos}),
            "n_terminos_vocabulario": len(self.vectorizer.vocabulary_),
            "por_coleccion": {},
            "palabras_totales": sum(f.n_palabras for f in self.fragmentos),
            "tecnica": "TF-IDF (1-2 gramas, sublinear_tf) + similitud coseno",
            "corpus": sorted({f.documento for f in self.fragmentos}),
        }
        for f in self.fragmentos:
            self.meta["por_coleccion"][f.coleccion] = self.meta["por_coleccion"].get(f.coleccion, 0) + 1
        if guardar:
            self._guardar()
        return self.meta

    def _guardar(self) -> None:
        with config.RAG_CHUNKS.open("w", encoding="utf-8") as fh:
            for f in self.fragmentos:
                fh.write(json.dumps(asdict(f), ensure_ascii=False) + "\n")
        sparse.save_npz(str(config.RAG_MATRIZ), self.matriz)
        with config.RAG_VECTORIZER.open("wb") as fh:
            pickle.dump(self.vectorizer, fh)
        config.RAG_INDICE_META.write_text(
            json.dumps(self.meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- carga ---
    def cargar(self) -> "MemoriaSemantica":
        if not config.RAG_CHUNKS.exists():
            raise FileNotFoundError(
                "No hay índice RAG. Ejecuta primero:  python -m memoria indexar")
        self.fragmentos = [
            Fragmento(**json.loads(l))
            for l in config.RAG_CHUNKS.read_text(encoding="utf-8").splitlines() if l.strip()
        ]
        self.matriz = sparse.load_npz(str(config.RAG_MATRIZ)).tocsr()
        with config.RAG_VECTORIZER.open("rb") as fh:
            self.vectorizer = pickle.load(fh)
        if config.RAG_INDICE_META.exists():
            self.meta = json.loads(config.RAG_INDICE_META.read_text(encoding="utf-8"))
        return self

    # --- consulta ---
    def consultar(self, consulta: str, k: int = 5, coleccion: str | None = None) -> list[dict]:
        """Devuelve los k fragmentos más similares con su puntaje coseno."""
        if self.vectorizer is None or self.matriz is None:
            self.cargar()
        assert self.vectorizer is not None and self.matriz is not None
        q = self.vectorizer.transform([consulta])
        sims = (self.matriz @ q.T).toarray().ravel()
        orden = np.argsort(-sims)
        salida: list[dict] = []
        for idx in orden:
            if sims[idx] <= 0:
                continue
            frag = self.fragmentos[int(idx)]
            if coleccion and frag.coleccion != coleccion:
                continue
            salida.append({
                "puntaje": round(float(sims[idx]), 4),
                "documento": frag.documento,
                "coleccion": frag.coleccion,
                "seccion": frag.seccion,
                "ruta": frag.ruta,
                "extracto": frag.texto[:400],
                "n_palabras": frag.n_palabras,
            })
            if len(salida) >= k:
                break
        return salida

    def terminos_relevantes(self, consulta: str, k: int = 8) -> list[tuple[str, float]]:
        """Términos del vocabulario que más pesan en la consulta (explicabilidad)."""
        if self.vectorizer is None:
            self.cargar()
        assert self.vectorizer is not None
        q = self.vectorizer.transform([consulta])
        nombres = self.vectorizer.get_feature_names_out()
        fila = q.toarray().ravel()
        idx = np.argsort(-fila)
        return [(str(nombres[i]), round(float(fila[i]), 4)) for i in idx[:k] if fila[i] > 0]


# --------------------------------------------------------------------------
# Herramienta para el flujo de redacción (RAG antes de redactar)
# --------------------------------------------------------------------------
def antes_de_redactar(tema: str, k: int = 5, registrar: bool = True) -> dict:
    """
    Se invoca ANTES de redactar o afirmar algo nuevo.

    Devuelve lo que ya se dijo sobre el tema (para no contradecirse ni repetir)
    y deja constancia auditable de la consulta.
    """
    mem = MemoriaSemantica().cargar()
    resultados = mem.consultar(tema, k=k)
    info = {
        "momento": datetime.now().isoformat(timespec="seconds"),
        "tema": tema,
        "tecnica": mem.meta.get("tecnica", "TF-IDF + coseno"),
        "n_fragmentos_indice": len(mem.fragmentos),
        "recuperados": resultados,
        "terminos_consulta": mem.terminos_relevantes(tema),
        "veredicto": (
            "sin antecedentes" if not resultados
            else f"{len(resultados)} antecedente(s); el más similar: "
                 f"{resultados[0]['documento']}::{resultados[0]['seccion']} "
                 f"(cos={resultados[0]['puntaje']})"
        ),
    }
    if registrar:
        config.asegurar_memoria()
        with config.CONSULTAS_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(info, ensure_ascii=False) + "\n")
    return info
