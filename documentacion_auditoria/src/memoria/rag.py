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

Técnica: DOS métodos intercambiables
-----------------------------------
El índice se puede construir con dos métodos y se consulta con el que esté
activo (`metodo="tfidf"` o `metodo="embeddings"`). Los dos escriben artefactos
distintos, de modo que convivir no se pisan:

- ``tfidf`` (DEFAULT, decisión D002): TF-IDF de scikit-learn + similitud coseno.
  Se eligió porque (i) el corpus es pequeño (~150 fragmentos), (ii) no añade
  dependencias pesadas, (iii) el vocabulario es técnico y estable y (iv) el
  resultado es determinista y explicable: se puede mostrar qué término pesa en
  la recuperación (`terminos_relevantes`).
- ``embeddings`` (decisión D007): vectorización semántica con un modelo LOCAL
  (`ibm-granite/granite-embedding-97m-multilingual-r2`, 384 dimensiones, contexto
  de 32 768 tokens, arquitectura ModernBERT) ejecutado en CPU. Se eligió un modelo
  local, y no una API, porque la rúbrica prohíbe subir datos de la contraparte a
  la nube. A diferencia de TF-IDF, recupera paráfrasis y sinónimos aunque no
  compartan ni una palabra con la consulta, a cambio de más peso (torch) y de
  perder explicabilidad término a término.
  El contexto largo importa: el intento anterior con MiniLM (128 tokens) truncaba
  143 de los 150 fragmentos y solo vectorizaba el 7,8 % del contenido; Granite
  cubre el 79,6 % (solo 2 fragmentos de código superan su límite).

Cuándo usar cada uno
--------------------
- Por defecto TF-IDF: es rápido, sin dependencias y suficiente cuando la
  pregunta y el documento comparten vocabulario (cifras, rutas, nombres propios).
- Embeddings cuando la consulta está parafraseada o usa sinónimos. Como respaldo,
  TF-IDF nunca se retira: si el modelo local no está disponible, el sistema sigue
  funcionando con el método por defecto.

Trazabilidad
------------
Cada consulta se registra en data/memoria/consultas_rag.jsonl con su tema, los
fragmentos recuperados y sus puntajes: la consulta queda auditada.
"""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

from . import config


# --------------------------------------------------------------------------
# Métodos de recuperación y modelo local de embeddings
# --------------------------------------------------------------------------
METODOS = ("tfidf", "embeddings")
METODO_POR_DEFECTO = "tfidf"
TECNICA_TFIDF = "TF-IDF (1-2 gramas, sublinear_tf) + similitud coseno"
TECNICA_EMBEDDINGS = (f"embeddings locales ({config.MODELO_EMBEDDINGS}) + similitud coseno")

# Presupuesto de tokens por lote al vectorizar. Se agrupan los fragmentos por
# longitud y se corta el lote cuando se supera este presupuesto: asi los lotes
# cortos van llenos y una secuencia de 32 768 tokens viaja sola (mezclarla con
# otras multiplicaria el relleno y dispararia la memoria).
LOTE_TOKENS = 16384


def _hilos_torch() -> int | None:
    """Hilos configurados para torch (0/None si no se pudo consultar)."""
    try:
        import torch
        return int(torch.get_num_threads())
    except Exception:                   # pragma: no cover
        return None

# Caché de proceso: cargar el modelo cuesta ~20 s y no se repite en la misma corrida.
_MODELOS: dict[str, object] = {}


def _cargar_modelo(nombre: str | None = None):
    """
    Carga el modelo de embeddings DESDE LA CACHÉ LOCAL. Nunca descarga.

    Se fuerzan HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE antes de importar la librería
    para que, si el modelo no estuviera ya descargado, falle con un error claro
    en lugar de intentar bajar ~120 MB por red (la rúbrica prohíbe enviar datos
    de la contraparte a la nube; aquí directamente no se usa red).
    """
    nombre = nombre or config.MODELO_EMBEDDINGS
    if nombre in _MODELOS:
        return _MODELOS[nombre]
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:      # pragma: no cover - depende del entorno
        raise RuntimeError(
            "El método 'embeddings' requiere sentence-transformers. "
            "Instálalo con:  pip install sentence-transformers"
        ) from exc
    try:
        modelo = SentenceTransformer(nombre, device="cpu")
    except Exception as exc:        # pragma: no cover - depende del entorno
        raise RuntimeError(
            f"No se pudo cargar el modelo local '{nombre}'. Debe estar ya "
            f"descargado en la caché de Hugging Face (el sistema no descarga "
            f"modelos). Error original: {exc}"
        ) from exc

    # --- Precisión e hilos ---------------------------------------------------
    # Granite se publica en bfloat16. En equipos sin bf16 nativo (esta CPU
    # reporta AVX2) PyTorch EMULA ese tipo y el coste se dispara: medido en esta
    # máquina, una matmul 512x512 tarda 2,07 s en bfloat16 frente a 0,0044 s en
    # float32 (467x). Pasar el modelo a float32 cuesta 0,1 s y hace el indexado
    # viable sin cambiar el resultado de la recuperación (los vectores siguen
    # normalizados y el orden por similitud coseno es el mismo).
    try:
        import torch
        torch.set_num_threads(max(1, min(4, os.cpu_count() or 2)))
        if any(p.dtype == torch.bfloat16 for p in modelo.parameters()):
            modelo.float()
    except Exception:               # pragma: no cover - torch siempre está aquí
        pass

    _MODELOS[nombre] = modelo
    return modelo


def hash_corpus(fragmentos: list["Fragmento"]) -> str:
    """Huella del corpus (ids en orden): detecta matriz y fragmentos desalineados."""
    h = hashlib.sha256()
    for f in fragmentos:
        h.update(f.id.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


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
    """
    Índice consultable sobre el corpus documental del proyecto.

    Soporta dos métodos intercambiables (`metodo`): "tfidf" (por defecto) y
    "embeddings" (modelo local). Ver el docstring del módulo para el criterio
    de elección.
    """

    def __init__(self, metodo: str = METODO_POR_DEFECTO) -> None:
        if metodo not in METODOS:
            raise ValueError(f"método no reconocido: {metodo!r}. Usa uno de {METODOS}")
        self.metodo: str = metodo
        self.vectorizer: TfidfVectorizer | None = None      # solo tfidf
        self.matriz = None                                  # sparse (tfidf) | ndarray (embeddings)
        self.modelo = None                                  # solo embeddings (perezoso)
        self.fragmentos: list[Fragmento] = []
        self.meta: dict = {}

    # --- construcción ---
    def indexar(self, guardar: bool = True, metodo: str | None = None) -> dict:
        """Construye el índice con el método activo (o el que se indique)."""
        if metodo:
            if metodo not in METODOS:
                raise ValueError(f"método no reconocido: {metodo!r}. Usa uno de {METODOS}")
            self.metodo = metodo
        config.asegurar_memoria()
        self.fragmentos = construir_fragmentos()
        if not self.fragmentos:
            raise RuntimeError("Corpus vacío: no hay fragmentos que indexar.")
        if self.metodo == "embeddings":
            return self._indexar_embeddings(guardar=guardar)
        return self._indexar_tfidf(guardar=guardar)

    def _base_meta(self, tecnica: str) -> dict:
        meta = {
            "fecha_construccion": datetime.now().isoformat(timespec="seconds"),
            "n_fragmentos": len(self.fragmentos),
            "n_documentos": len({f.documento for f in self.fragmentos}),
            "por_coleccion": {},
            "palabras_totales": sum(f.n_palabras for f in self.fragmentos),
            "tecnica": tecnica,
            "metodo": self.metodo,
            "corpus": sorted({f.documento for f in self.fragmentos}),
            "hash_corpus": hash_corpus(self.fragmentos),
        }
        for f in self.fragmentos:
            meta["por_coleccion"][f.coleccion] = meta["por_coleccion"].get(f.coleccion, 0) + 1
        return meta

    def _indexar_tfidf(self, guardar: bool = True) -> dict:
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
        self.meta = self._base_meta(TECNICA_TFIDF)
        self.meta["n_terminos_vocabulario"] = len(self.vectorizer.vocabulary_)
        if guardar:
            self._guardar()
        return self.meta

    def _indexar_embeddings(self, guardar: bool = True,
                            verbose: bool = True) -> dict:
        """
        Vectoriza el corpus con el modelo local de embeddings.

        No se usan prefijos de consulta/documento porque el modelo declara
        `prompts` vacios para ambos (`config_sentence_transformers.json`), de modo
        que `encode` es suficiente; `encode_query`/`encode_document` existen pero
        no aportan nada distinto en este modelo.
        """
        modelo = _cargar_modelo()
        textos = [f.texto for f in self.fragmentos]
        max_len = int(getattr(modelo, "max_seq_length", 0) or 0)

        # Longitud real en tokens de ESTE tokenizer (una sola pasada, ~0,5 s).
        t0 = time.time()
        largos = [len(x) for x in modelo.tokenizer(
            textos, truncation=False, padding=False, add_special_tokens=True)["input_ids"]]
        seg_tok = time.time() - t0
        excedidos = [i for i, L in enumerate(largos) if max_len and L > max_len]

        # Lotes homogeneos por longitud, con tope de tokens por lote.
        orden = sorted(range(len(textos)), key=lambda i: largos[i])
        lotes: list[list[int]] = []
        actual: list[int] = []
        acum = 0
        for i in orden:
            if actual and acum + largos[i] > LOTE_TOKENS:
                lotes.append(actual)
                actual, acum = [], 0
            actual.append(i)
            acum += largos[i]
        if actual:
            lotes.append(actual)

        vectores = np.zeros((len(textos), int(modelo.get_embedding_dimension())),
                            dtype="float32")
        if verbose:
            print(f"[RAG] vectorizando {len(textos)} fragmentos en {len(lotes)} lotes "
                  f"({sum(largos)} tokens; max {max(largos)})...", flush=True)
        t0 = time.time()
        for k, lote in enumerate(lotes, 1):
            salida = modelo.encode(
                [textos[i] for i in lote],
                batch_size=len(lote),
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,   # unitarios -> producto punto == coseno
            )
            vectores[lote] = np.asarray(salida, dtype="float32")
            if verbose and (k % 20 == 0 or k == len(lotes)):
                print(f"[RAG]   lote {k}/{len(lotes)} — {time.time()-t0:.0f} s "
                      f"acumulados", flush=True)
        segundos = time.time() - t0

        self.matriz = vectores
        self.meta = self._base_meta(TECNICA_EMBEDDINGS)
        self.meta.update({
            "modelo": config.MODELO_EMBEDDINGS,
            "dimension": int(self.matriz.shape[1]),
            "normalizado": True,
            "n_terminos_vocabulario": None,   # no aplica: no hay vocabulario discreto
            "tiempo_generacion_segundos": round(segundos, 2),
            "dispositivo": "cpu",
            "precision": str(next(modelo.parameters()).dtype),
            "hilos_torch": _hilos_torch(),
            "truncamiento": {
                "max_seq_length": max_len,
                "n_fragmentos": len(largos),
                "n_exceden": len(excedidos),
                "pct_exceden": round(100 * len(excedidos) / len(largos), 2),
                "tokens_min": min(largos),
                "tokens_mediana": sorted(largos)[len(largos) // 2],
                "tokens_promedio": round(sum(largos) / len(largos), 1),
                "tokens_max": max(largos),
                "tokens_totales": sum(largos),
                "tokens_efectivos": sum(min(L, max_len) for L in largos) if max_len
                                    else sum(largos),
                "cobertura_pct": round(100 * sum(min(L, max_len) for L in largos)
                                       / sum(largos), 2) if max_len else 100.0,
                "fragmentos_excedidos": [
                    {"id": self.fragmentos[i].id, "tokens": largos[i]}
                    for i in sorted(excedidos, key=lambda i: -largos[i])],
                "segundos_tokenizando": round(seg_tok, 2),
                "lotes": len(lotes),
                "tope_tokens_por_lote": LOTE_TOKENS,
            },
        })
        if guardar:
            self._guardar_embeddings()
        return self.meta

    def _guardar_embeddings(self) -> None:
        """Escribe el corpus compartido, la matriz .npy y los metadatos del índice."""
        self._guardar_fragmentos()
        np.save(str(config.RAG_EMBEDDINGS_MATRIZ), self.matriz)
        config.RAG_INDICE_EMBEDDINGS.write_text(
            json.dumps(self.meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def _guardar_fragmentos(self) -> None:
        """El corpus de fragmentos es COMPARTIDO por los dos métodos."""
        with config.RAG_CHUNKS.open("w", encoding="utf-8") as fh:
            for f in self.fragmentos:
                fh.write(json.dumps(asdict(f), ensure_ascii=False) + "\n")

    def _guardar(self) -> None:
        self._guardar_fragmentos()
        sparse.save_npz(str(config.RAG_MATRIZ), self.matriz)
        with config.RAG_VECTORIZER.open("wb") as fh:
            pickle.dump(self.vectorizer, fh)
        config.RAG_INDICE_META.write_text(
            json.dumps(self.meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- carga ---
    def cargar(self, metodo: str | None = None) -> "MemoriaSemantica":
        if metodo:
            if metodo not in METODOS:
                raise ValueError(f"método no reconocido: {metodo!r}. Usa uno de {METODOS}")
            self.metodo = metodo
        if not config.RAG_CHUNKS.exists():
            raise FileNotFoundError(
                "No hay índice RAG. Ejecuta primero:  python -m memoria indexar")
        self.fragmentos = [
            Fragmento(**json.loads(l))
            for l in config.RAG_CHUNKS.read_text(encoding="utf-8").splitlines() if l.strip()
        ]
        if self.metodo == "embeddings":
            return self._cargar_embeddings()

        self.matriz = sparse.load_npz(str(config.RAG_MATRIZ)).tocsr()
        with config.RAG_VECTORIZER.open("rb") as fh:
            self.vectorizer = pickle.load(fh)
        if config.RAG_INDICE_META.exists():
            self.meta = json.loads(config.RAG_INDICE_META.read_text(encoding="utf-8"))
        return self

    def _cargar_embeddings(self) -> "MemoriaSemantica":
        if not config.RAG_INDICE_EMBEDDINGS.exists():
            raise FileNotFoundError(
                "No hay índice de embeddings. Ejecuta primero:  "
                "python -m memoria indexar --metodo embeddings")
        self.meta = json.loads(config.RAG_INDICE_EMBEDDINGS.read_text(encoding="utf-8"))
        self.matriz = np.load(str(config.RAG_EMBEDDINGS_MATRIZ))
        # Integridad: si el corpus se reconstruyó con otro contenido, la matriz
        # quedaría desalineada respecto a los fragmentos (y los puntajes serían
        # silenciosamente falsos). Se aborta con instrucciones.
        assert self.matriz.shape[0] == len(self.fragmentos), (
            f"matriz {self.matriz.shape} vs {len(self.fragmentos)} fragmentos: "
            "vuelve a indexar con  python -m memoria indexar --metodo embeddings")
        esperado = self.meta.get("hash_corpus")
        actual = hash_corpus(self.fragmentos)
        if esperado and esperado != actual:
            raise RuntimeError(
                f"El corpus cambió desde que se indexó con embeddings "
                f"(hash {actual} != {esperado}). Reindexa:  "
                f"python -m memoria indexar --metodo embeddings")
        return self

    # --- consulta ---
    def consultar(self, consulta: str, k: int = 5, coleccion: str | None = None) -> list[dict]:
        """Devuelve los k fragmentos más similares con su puntaje coseno."""
        if self.matriz is None:
            self.cargar()
        assert self.matriz is not None
        if self.metodo == "embeddings":
            if self.modelo is None:
                self.modelo = _cargar_modelo(self.meta.get("modelo"))
            q = self.modelo.encode([consulta], normalize_embeddings=True,
                                   convert_to_numpy=True)[0].astype("float32")
            sims = self.matriz @ q            # ambos unitarios -> coseno
        else:
            if self.vectorizer is None:
                self.cargar()
            assert self.vectorizer is not None
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
        """
        Términos del vocabulario que más pesan en la consulta (explicabilidad).

        Solo tiene sentido con TF-IDF: los embeddings no tienen un vocabulario
        discreto que mostrar, así que con ese método devuelve una lista vacía.
        """
        if self.metodo == "embeddings":
            return []
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
def antes_de_redactar(tema: str, k: int = 5, registrar: bool = True,
                      metodo: str = METODO_POR_DEFECTO) -> dict:
    """
    Se invoca ANTES de redactar o afirmar algo nuevo.

    Devuelve lo que ya se dijo sobre el tema (para no contradecirse ni repetir)
    y deja constancia auditable de la consulta.
    """
    mem = MemoriaSemantica(metodo).cargar()
    resultados = mem.consultar(tema, k=k)
    info = {
        "momento": datetime.now().isoformat(timespec="seconds"),
        "tema": tema,
        "metodo": mem.metodo,
        "tecnica": mem.meta.get("tecnica", TECNICA_TFIDF),
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
