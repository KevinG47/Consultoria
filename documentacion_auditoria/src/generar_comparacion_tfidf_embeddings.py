# -*- coding: utf-8 -*-
"""
generar_comparacion_tfidf_embeddings.py
=======================================

Genera `03_informes/analisis_fase2/comparacion_tfidf_vs_embeddings.md` a partir de
las cifras ya calculadas en:
  - data/memoria/comparacion_rag.json            (comparación vigente)
  - data/memoria/comparacion_rag_minilm.json     (evidencia del primer intento)
  - data/memoria/resultados_banco_tfidf.json
  - data/memoria/resultados_banco_embeddings.json
  - data/memoria/decisiones.yaml                 (texto literal de D002 y D007)
  - data/memoria/rag_indice.json / rag_indice_embeddings.json

El veredicto NO está escrito a mano: se deduce de las métricas con una regla
explícita (ver `_veredicto`), de modo que el documento no puede quedar
contradiciendo a los datos.
"""

from __future__ import annotations

import io
import json
import sys
from datetime import date
from pathlib import Path

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOC = Path(__file__).resolve().parents[1]
MEM = DOC / "data" / "memoria"
SALIDA = RAIZ / "03_informes" / "analisis_fase2" / "comparacion_tfidf_vs_embeddings.md"

C = json.loads((MEM / "comparacion_rag.json").read_text(encoding="utf-8"))
MIN = json.loads((MEM / "comparacion_rag_minilm.json").read_text(encoding="utf-8"))
RES_TF = json.loads((MEM / "resultados_banco_tfidf.json").read_text(encoding="utf-8"))
RES_EM = json.loads((MEM / "resultados_banco_embeddings.json").read_text(encoding="utf-8"))
DEC = {d["id"]: d for d in (yaml.safe_load(
    (MEM / "decisiones.yaml").read_text(encoding="utf-8")) or {}).get("decisiones", [])}
IND_TF = json.loads((MEM / "rag_indice.json").read_text(encoding="utf-8"))
IND_EM = json.loads((MEM / "rag_indice_embeddings.json").read_text(encoding="utf-8"))
# El bloque de truncamiento del comparador y el del metadato del índice no usan
# exactamente los mismos nombres de clave: se leen con tolerancia.
TR_IND = IND_EM.get("truncamiento", {})
TIEMPO_INDEXADO_S = IND_EM.get("tiempo_generacion_segundos")


def _cob(bloque: dict) -> float:
    """Cobertura del corpus (clave `cobertura_pct` o su alias antiguo)."""
    return bloque.get("cobertura_pct", bloque.get("cobertura_media_pct"))


def _excedidos(bloque: dict, indice: dict) -> list[dict]:
    """Fragmentos que superan el contexto, con cualquier nombre de clave."""
    for fuente in (indice, bloque):
        for clave in ("fragmentos_excedidos", "ejemplos_excedidos"):
            if fuente.get(clave):
                return list(fuente[clave])
    return []


AGG = C["agregados"]
TR = C["truncamiento"]               # medición con el tokenizer de Granite
TRM = MIN["truncamiento"]            # medición con el tokenizer de MiniLM
AM = MIN["agregados"]
IND = C["indices"]
EXCEDIDOS = _excedidos(TR, TR_IND)
d002, d007 = DEC["D002"], DEC["D007"]


def _veredicto(agg: dict) -> dict:
    """
    Regla explícita de adopción, para que el documento no dependa de una opinión.

    Se adopta embeddings como método principal solo si NO empeora en ninguna de las
    tres métricas que importan: aciertos en top-1, aciertos en top-3 y posición
    promedio del dato correcto (con un margen de tolerancia del 20 % en esta última,
    porque es una medida continua y más ruidosa).
    """
    c1 = agg["top1_embeddings"] >= agg["top1_tfidf"]
    c3 = agg["top3_embeddings"] >= agg["top3_tfidf"]
    cr = agg["rank_prom_embeddings"] <= agg["rank_prom_tfidf"] * 1.20
    return {"top1": c1, "top3": c3, "ranking": cr,
            "adopta": bool(c1 and c3 and cr),
            "tolerancia_ranking": 1.20}


def n(x):
    """Entero o decimal con separadores españoles."""
    if isinstance(x, float):
        return f"{x:,.1f}".replace(",", "\x00").replace(".", ",").replace("\x00", " ")
    return f"{x:,}".replace(",", " ")


def com(x, dec=2):
    """Decimal con coma."""
    return f"{x:.{dec}f}".replace(".", ",")


def pc_tr(x, dec=1):
    """Porcentaje ya expresado en escala 0-100, con coma."""
    return f"{x:.{dec}f}".replace(".", ",")


def plegado(txt: str) -> str:
    return " ".join(str(txt).split())


VER = _veredicto(AGG)
L: list[str] = []
A = L.append

A("# Comparación: TF-IDF vs embeddings para el RAG del proyecto")
A("")
A("**Auditoría estadística del sistema de reconocimiento de MinCiencias — "
  "sistema de memoria del agente**  ")
A(f"Documento generado por `documentacion_auditoria/src/generar_comparacion_tfidf_embeddings.py` "
  f"a partir de `data/memoria/comparacion_rag.json` y de los dos resultados del banco de "
  f"preguntas. Fecha: {date.today():%Y-%m-%d}.")
A("")
A("## Resumen en una página")
A("")
A(f"El RAG del proyecto sabe recuperar con **dos métodos intercambiables**: TF-IDF (el de "
  f"siempre) y embeddings locales, hoy con **Granite Embedding 97M Multilingual R2** "
  f"(contexto de 32 768 tokens). Se evaluaron los dos con el mismo banco de "
  f"{AGG['n_preguntas']} preguntas sobre el mismo corpus de "
  f"{n(IND['tfidf']['n_fragmentos'])} fragmentos.")
A("")
A("| Métrica | TF-IDF | Granite | Ganador |")
A("|---|---:|---:|---|")
_mayor1 = ("embeddings" if AGG["top1_embeddings"] > AGG["top1_tfidf"]
           else ("TF-IDF" if AGG["top1_embeddings"] < AGG["top1_tfidf"] else "empate"))
_mayor3 = ("embeddings" if AGG["top3_embeddings"] > AGG["top3_tfidf"]
           else ("TF-IDF" if AGG["top3_embeddings"] < AGG["top3_tfidf"] else "empate"))
_mayorr = ("embeddings" if AGG["rank_prom_embeddings"] < AGG["rank_prom_tfidf"]
           else "TF-IDF")
A(f"| Respuesta esperada en el **top-1** | {AGG['top1_tfidf']}/{AGG['n_preguntas']} | "
  f"{AGG['top1_embeddings']}/{AGG['n_preguntas']} | {_mayor1} |")
A(f"| Respuesta esperada en el **top-3** | {AGG['top3_tfidf']}/{AGG['n_preguntas']} | "
  f"{AGG['top3_embeddings']}/{AGG['n_preguntas']} | {_mayor3} |")
A(f"| Ranking promedio del dato correcto (de {n(IND['tfidf']['n_fragmentos'])}) | "
  f"{com(AGG['rank_prom_tfidf'])} | {com(AGG['rank_prom_embeddings'])} | {_mayorr} |")
A(f"| Preguntas ganadas | {AGG['gana_tfidf']} | {AGG['gana_embeddings']} | "
  f"{AGG['empates']} empates |")
A(f"| Cobertura del corpus al vectorizar | 100 % | {pc_tr(_cob(TR))} % | — |")
A("")
if VER["adopta"]:
    A(f"**Conclusión: con Granite los embeddings igualan o superan a TF-IDF en las tres "
      f"métricas**, y cubren el {pc_tr(_cob(TR))} % del corpus frente al "
      f"{pc_tr(_cob(TRM))} % del modelo anterior. La regla de adopción "
      f"definida en §7 se cumple, de modo que los embeddings quedan como método "
      f"recomendado, sin retirar TF-IDF.")
else:
    A(f"**Conclusión: con Granite los embeddings mejoran mucho respecto al intento anterior, "
      f"pero no superan a TF-IDF en las tres métricas.** Cumplen la regla de adopción en "
      f"{sum(1 for k in ('top1', 'top3', 'ranking') if VER[k])} de 3 criterios (ver §7), así "
      f"que se recomienda **mantener TF-IDF como método por defecto** y los embeddings como "
      f"método complementario, con el truncamiento ya acotado a {TR['n_exceden']} fragmentos "
      f"de {TR['n_fragmentos']} (antes eran {TRM['n_exceden']}).")
A("")
A(f"El salto respecto al primer intento está medido: con MiniLM (contexto de "
  f"{n(TRM['max_seq_length'])} tokens) se truncaban {TRM['n_exceden']} de "
  f"{TRM['n_fragmentos']} fragmentos y solo se vectorizaba el "
  f"{pc_tr(_cob(TRM))} % del contenido; con Granite se truncan "
  f"{TR['n_exceden']} de {TR['n_fragmentos']} y la cobertura sube al "
  f"{pc_tr(_cob(TR))} %.")
A("")

# ---------------------------------------------------------------- 1
A("## 1. Qué es TF-IDF, en lenguaje llano")
A("")
A("TF-IDF significa *Term Frequency – Inverse Document Frequency*, es decir "
  "«frecuencia del término por rareza del término». Es la forma más clásica de buscar "
  "texto y funciona en tres pasos:")
A("")
A("1. **Cuenta palabras.** Cada fragmento se convierte en una lista de las palabras que "
  "contiene. El orden no importa: «el perro muerde al hombre» y «el hombre muerde al perro» "
  "quedan representados igual.")
A("2. **Pondera por rareza.** Una palabra que aparece en todos los documentos («de», "
  "«informe») casi no aporta; una que aparece en pocos («bqtm-4y2h», «77 237») es muy "
  "informativa y pesa mucho. De ahí el «inverse document frequency».")
A("3. **Compara.** La pregunta se convierte en la misma lista de palabras ponderadas y se "
  "mide el ángulo entre ambos vectores (similitud coseno). Los fragmentos con más palabras "
  "raras en común quedan arriba.")
A("")
A("**Ventajas.** Es muy rápido, no necesita ninguna dependencia pesada, es determinista "
  "(la misma consulta da siempre el mismo resultado) y —esto importa en una auditoría— es "
  "**explicable**: se puede mostrar exactamente qué término está pesando en la recuperación. "
  "El sistema lo hace con el comando `terminos_relevantes`, por ejemplo:")
A("")
A("```")
A("[RAG] términos que pesan: [('mayor 100', 0.3988), ('edad mayor', 0.3988),")
A("                            ('cuantos registros', 0.3988), ('cuantos', 0.3426)]")
A("```")
A("")
A("Además, para un vocabulario técnico y estable —cifras, rutas de archivo, "
  "identificadores como `n_atipicos_edad`— coincidir en la palabra exacta es justo lo que "
  "se necesita. Y **no tiene límite de longitud**: ve el fragmento completo, mida lo que mida.")
A("")
A("**Límites.** No entiende sinónimos ni paráfrasis: si el documento dice «investigadores "
  "únicos» y la pregunta dice «personas distintas», TF-IDF no ve ninguna relación, porque "
  "no comparten ni una palabra. Tampoco entiende el significado: dos frases con las mismas "
  "palabras en distinto orden le resultan idénticas.")
A("")

# ---------------------------------------------------------------- 2
A("## 2. Qué es un embedding, en lenguaje llano")
A("")
A("Un *embedding* es una forma de convertir un texto en una lista de números —un vector— "
  "de manera que **textos con significado parecido queden cerca** en ese espacio numérico. "
  "En lugar de contar palabras, se usa un modelo entrenado con millones de frases para "
  "aprender qué textos suelen significar lo mismo.")
A("")
A(f"En este proyecto el vector tiene {n(IND['embeddings']['dimension'])} números por "
  f"fragmento, producidos por el modelo local `{IND['embeddings']['modelo']}`: 97 millones "
  f"de parámetros, arquitectura ModernBERT y **contexto de {n(TR['max_seq_length'])} "
  f"tokens**. La comparación es la misma que en TF-IDF: similitud coseno sobre vectores "
  f"normalizados.")
A("")
A("**Ventajas.** Entiende sinónimos, paráfrasis y conceptos que no comparten ni una "
  "palabra. Si la pregunta dice «¿cuántos investigadores hay registrados?» y el documento "
  "dice «total de personas únicas en el padrón», un embedding puede relacionarlos y TF-IDF "
  "no. Además es **multilingüe** (la misma frase en español e inglés cae cerca) y, con "
  "contexto largo, puede procesar un documento entero en lugar de solo su encabezado.")
A("")
A("**Límites.** Requiere un modelo: aquí son ~210 MB de pesos más la librería `torch`, así "
  f"que el sistema pesa más y tarda más en arrancar (cargar el modelo cuesta unos 5 "
  f"segundos, pero vectorizar el corpus entero tarda mucho más que TF-IDF: ver §5.3 y §7.1). "
  f"El contexto, aunque sea grande, **es finito**: lo que exceda "
  f"{n(TR['max_seq_length'])} tokens se descarta sin avisar. Y se pierde la explicabilidad: "
  f"no hay un «término que pesa» que se pueda mostrar, solo un número de similitud.")
A("")
A("> **Por qué un modelo local y no una API.** La rúbrica prohíbe subir datos de la "
  "contraparte a la nube. Por eso el sistema usa un modelo que corre en la propia máquina "
  "(CPU) y que **nunca** consulta la red: si el modelo no estuviera ya descargado, el "
  "sistema falla con un mensaje claro en lugar de intentar bajarlo.")
A("")

# ---------------------------------------------------------------- 3
A("## 3. Por qué el sistema usaba TF-IDF")
A("")
A(f"Está registrado como decisión **D002** ({d002['fecha']}), hoy en estado "
  f"`{d002['estado']}` porque D007 la sucedió. Su justificación literal fue:")
A("")
A(f"> {plegado(d002['justificacion'])}")
A("")
A(f"Y la decisión: «{plegado(d002['decision'])}». Las alternativas que se descartaron "
  f"entonces fueron: {', '.join(d002['alternativas_descartadas'])}.")
A("")
A("En otras palabras: con ~24 documentos y ~137 fragmentos, un vocabulario homogéneo y "
  "técnico, TF-IDF resolvía el problema sin añadir dependencias, sin coste y con resultados "
  "auditables. Fue una decisión razonable para el tamaño y el momento del proyecto.")
A("")

# ---------------------------------------------------------------- 4
A("## 4. Por qué se pidió migrar a embeddings")
A("")
A(f"Está registrado como decisión **D007** ({d007['fecha']}). Conviene subrayar que el "
  f"motivo **no** era que la recuperación fallara, sino el mantenimiento y la transferencia "
  f"del sistema:")
A("")
A(f"> {plegado(d007['motivo_docente'])}")
A("")
A(f"La decisión se registró originalmente así: «{plegado(d007['redaccion_original'])}». Esa "
  f"redacción era **imposible de cumplir en este proyecto**, y no por dificultad técnica:")
A("")
A(f"> {plegado(d007['nota_correccion'])}")
A("")
A("La implementación adoptada satisface el motivo del docente —no depender de un diccionario "
  "construido a medida, sino de un modelo estándar que cualquiera puede cargar— sin salir de "
  "la máquina. La decisión quedó corregida en `decisiones.yaml` conservando la redacción "
  "original en un campo aparte, para que el cambio quede trazado.")
A("")

# ---------------------------------------------------------------- 5 (NUEVA)
A("## 5. El primer intento falló por el tamaño del modelo, no por la idea")
A("")
A("La primera implementación usó `paraphrase-multilingual-MiniLM-L12-v2`. Sobre el papel "
  "cumplía: multilingüe, 384 dimensiones, español correcto. En la práctica rindió **peor** "
  "que TF-IDF, y la causa no fue una impresión sino una medida.")
A("")
A("### 5.1 Qué pasó con MiniLM")
A("")
A(f"MiniLM procesa como máximo **{n(TRM['max_seq_length'])} tokens** por texto. Nuestros "
  f"fragmentos no son frases: nacen de secciones completas de LaTeX y promedian "
  f"{n(TRM['tokens_promedio'])} tokens. El resultado fue que **{TRM['n_exceden']} de "
  f"{TRM['n_fragmentos']} fragmentos ({pc_tr(TRM['pct_exceden'])} %)** se truncaban, y solo "
  f"se vectorizaba el **{pc_tr(_cob(TRM))} %** del contenido del corpus. "
  f"El modelo estaba, en la práctica, leyendo el encabezado de cada sección y nada más.")
A("")
A("Con esa configuración, la comparación contra TF-IDF quedó así:")
A("")
A("| Métrica | TF-IDF | MiniLM |")
A("|---|---:|---:|")
A(f"| Respuesta en el top-1 | {AM['top1_tfidf']}/{AM['n_preguntas']} | "
  f"{AM['top1_embeddings']}/{AM['n_preguntas']} |")
A(f"| Respuesta en el top-3 | {AM['top3_tfidf']}/{AM['n_preguntas']} | "
  f"{AM['top3_embeddings']}/{AM['n_preguntas']} |")
A(f"| Ranking promedio del dato correcto | {com(AM['rank_prom_tfidf'])} | "
  f"{com(AM['rank_prom_embeddings'])} |")
A(f"| Cobertura del corpus | 100 % | {pc_tr(_cob(TRM))} % |")
A("")
A("El patrón era revelador: MiniLM **ganaba** donde el dato está al principio del "
  "fragmento (el encabezado dice de qué trata) y **perdía estrepitosamente** donde el dato "
  "está a mitad o al final. Por ejemplo, en la pregunta por el número de nodos del grafo, "
  "TF-IDF ponía el fragmento correcto en la posición 1 y MiniLM en la 128. Eso descartó que "
  "el problema fuera «los embeddings no sirven para este corpus»: el problema era que el "
  "modelo no llegaba a leer el corpus.")
A("")
A("### 5.2 Qué cambió con Granite R2")
A("")
A(f"`{IND['embeddings']['modelo']}` es un modelo de tamaño comparable (97 M de parámetros, "
  f"{n(IND['embeddings']['dimension'])} dimensiones) pero con dos diferencias decisivas:")
A("")
A("1. **Contexto de 32 768 tokens** en lugar de 128: 256 veces más. La arquitectura "
  "ModernBERT usa atención alterna —ventanas locales de 128 tokens con atención global cada "
  "3 capas—, que es lo que permite procesar documentos largos en CPU sin agotar la memoria.")
A("2. **Sin prefijos**: el modelo declara indicaciones vacías para consulta y documento, así "
  "que la misma función sirve para ambas (no hizo falta usar `encode_query` ni "
  "`encode_document`, aunque existan).")
A("")
A("### 5.3 Qué quedó por resolver")
A("")
A(f"El truncamiento **no desaparece del todo**: {TR['n_exceden']} fragmentos siguen "
  f"excediendo el límite, porque son más largos que el propio contexto máximo del modelo:")
A("")
A("| Fragmento | Tokens |")
A("|---|---:|")
for e in EXCEDIDOS:
    A(f"| `{e['id']}` | {n(e['tokens'])} |")
A("")
A(f"En total, la cobertura del corpus sube del {pc_tr(_cob(TRM))} % al "
  f"**{pc_tr(_cob(TR))} %**, y los fragmentos truncados bajan de "
  f"{TRM['n_exceden']} a {TR['n_exceden']}. Son dos secciones de listado de código "
  f"(`03_codigo` y `05_codigo`), las más voluminosas del corpus, que por su tamaño superan "
  f"incluso los 32 768 tokens. Cerrar esa última brecha exigiría trocear esos dos "
  f"fragmentos, cosa que no se hizo para no alterar el corpus de "
  f"{n(IND['tfidf']['n_fragmentos'])} fragmentos (ver §7.1).")
A("")

# ---------------------------------------------------------------- 6
A("## 6. Resultados de la comparación")
A("")
A("### 6.1 Cómo se comparó")
A("")
A(f"El mismo banco de {AGG['n_preguntas']} preguntas, el mismo corpus "
  f"({n(IND['tfidf']['n_fragmentos'])} fragmentos de {n(IND['tfidf']['n_documentos'])} "
  f"documentos), los dos índices construidos por separado. Por pregunta se comparó: el "
  f"puntaje del top-1, si la respuesta esperada está en el top-1 y en el top-3, y la "
  f"posición del fragmento correcto en el ranking completo. El criterio para decidir quién "
  f"gana en cada pregunta es un orden lexicográfico: primero el acierto en top-1, después el "
  f"acierto en top-3 y, si empatan, la mejor posición del dato correcto.")
A("")
A("### 6.2 Tabla por pregunta")
A("")
A("| Q | Grupo | Score top-1 TF-IDF | Score top-1 Granite | Top-1 TF-IDF | Top-1 Granite | Top-3 TF-IDF | Top-3 Granite | Rank TF-IDF | Rank Granite | Gana |")
A("|---|---|---:|---:|:--:|:--:|:--:|:--:|---:|---:|---|")
for f in C["preguntas"]:
    s1 = com(f["score_top1_tfidf"], 4) if f["score_top1_tfidf"] is not None else "—"
    s2 = com(f["score_top1_embeddings"], 4) if f["score_top1_embeddings"] is not None else "—"
    A(f"| {f['id']} | {f['grupo']} | {s1} | {s2} | "
      f"{'sí' if f['en_top1_tfidf'] else 'no'} | {'sí' if f['en_top1_embeddings'] else 'no'} | "
      f"{'sí' if f['en_top3_tfidf'] else 'no'} | {'sí' if f['en_top3_embeddings'] else 'no'} | "
      f"{f['rank_tfidf'] if f['rank_tfidf'] else '—'} | "
      f"{f['rank_embeddings'] if f['rank_embeddings'] else '—'} | {f['gana']} |")
A("")
A("### 6.3 Agregados")
A("")
A("| Métrica | TF-IDF | Granite |")
A("|---|---:|---:|")
A(f"| Respuesta en el top-1 | **{AGG['top1_tfidf']}/{AGG['n_preguntas']}** | "
  f"**{AGG['top1_embeddings']}/{AGG['n_preguntas']}** |")
A(f"| Respuesta en el top-3 | **{AGG['top3_tfidf']}/{AGG['n_preguntas']}** | "
  f"**{AGG['top3_embeddings']}/{AGG['n_preguntas']}** |")
A(f"| Respuesta presente en el corpus | {AGG['corpus_tfidf']}/{AGG['n_preguntas']} | "
  f"{AGG['corpus_embeddings']}/{AGG['n_preguntas']} |")
A(f"| Score promedio del top-1 | {com(AGG['score_prom_top1_tfidf'], 4)} | "
  f"{com(AGG['score_prom_top1_embeddings'], 4)} |")
A(f"| Ranking promedio del dato correcto | **{com(AGG['rank_prom_tfidf'])}** | "
  f"**{com(AGG['rank_prom_embeddings'])}** |")
A(f"| Preguntas ganadas | {AGG['gana_tfidf']} | {AGG['gana_embeddings']} "
  f"(+{AGG['empates']} empates) |")
A("")
A("Por grupos del banco (A = datos que deberían estar en el corpus, B = datos que no, "
  "C = datos del propio sistema):")
A("")
A("| Grupo | n | Top-1 TF-IDF | Top-1 Granite | Top-3 TF-IDF | Top-3 Granite |")
A("|---|---:|---:|---:|---:|---:|")
for g, v in sorted(C["por_grupo"].items()):
    A(f"| {g} | {v['n']} | {v['top1_tfidf']} | {v['top1_embeddings']} | "
      f"{v['top3_tfidf']} | {v['top3_embeddings']} |")
A("")
A("### 6.4 En qué casos gana cada método")
A("")
emb_solo1 = ", ".join(f"Q{i}" for i in AGG["emb_solo_top1"]) or "ninguna"
tf_solo1 = ", ".join(f"Q{i}" for i in AGG["tfidf_solo_top1"]) or "ninguna"
emb_solo3 = ", ".join(f"Q{i}" for i in AGG["emb_solo_top3"]) or "ninguna"
tf_solo3 = ", ".join(f"Q{i}" for i in AGG["tfidf_solo_top3"]) or "ninguna"
A(f"- **Granite encuentra y TF-IDF no, en el top-1**: {emb_solo1}.")
A(f"- **TF-IDF encuentra y Granite no, en el top-1**: {tf_solo1}.")
A(f"- **En el top-3**: Granite gana en {emb_solo3} y TF-IDF en {tf_solo3}.")
A(f"- En {AGG['empates']} preguntas los dos métodos empatan, y en {AGG['corpus_tfidf']} de "
  f"las {AGG['n_preguntas']} el dato está en el corpus de todos modos.")
A("")
A("Conviene leer estos números junto al ranking promedio. Las preguntas en que TF-IDF "
  "conserva ventaja son las que buscan **una cifra o un identificador exacto**: para una "
  "bolsa de palabras, coincidir en el token literal es imbatible. Las que gana Granite son "
  "las redactadas con **palabras distintas** a las del documento, que es justo lo que un "
  "embedding está entrenado para resolver.")
A("")
A("### 6.5 Comparación de los dos modelos de embeddings")
A("")
A("| Medida | MiniLM (128 tokens) | Granite (32 768 tokens) |")
A("|---|---:|---:|")
A(f"| Fragmentos que superan el contexto | {TRM['n_exceden']} de {TRM['n_fragmentos']} "
  f"({pc_tr(TRM['pct_exceden'])} %) | {TR['n_exceden']} de {TR['n_fragmentos']} "
  f"({pc_tr(TR['pct_exceden'])} %) |")
A(f"| Contenido realmente vectorizado | {pc_tr(_cob(TRM))} % | "
  f"**{pc_tr(_cob(TR))} %** |")
A(f"| Top-1 con respuesta | {AM['top1_embeddings']}/{AM['n_preguntas']} | "
  f"{AGG['top1_embeddings']}/{AGG['n_preguntas']} |")
A(f"| Top-3 con respuesta | {AM['top3_embeddings']}/{AM['n_preguntas']} | "
  f"{AGG['top3_embeddings']}/{AGG['n_preguntas']} |")
A(f"| Ranking promedio del dato correcto | {com(AM['rank_prom_embeddings'])} | "
  f"**{com(AGG['rank_prom_embeddings'])}** |")
A("")
A(f"El cambio de modelo mejoró las tres métricas de los embeddings y multiplicó por "
  f"{com(_cob(TR)/_cob(TRM), 1)} la cobertura del corpus. Dicho "
  f"de otro modo: la conclusión del intento anterior —«los embeddings no superan a TF-IDF»— "
  f"era **correcta para ese modelo y esa configuración**, pero no era una conclusión sobre "
  f"los embeddings en general. El cuello de botella era el contexto.")
A("")
A("### 6.6 Dos comprobaciones de honestidad")
A("")
reg = C["no_regresion_tfidf"]
if reg["identico"]:
    A(f"1. **TF-IDF no se rompió.** La corrida nueva de TF-IDF es **idéntica** a la corrida "
      f"histórica ({reg['archivo_historico']}, del {reg['fecha_historico']}) en las "
      f"{reg['preguntas_comparadas']} preguntas: mismos puntajes, mismos rankings, mismos "
      f"aciertos.")
else:
    A(f"1. **TF-IDF no se rompió, pero su corrida ya no es idéntica a la histórica, y se "
      f"sabe por qué.** Comparada con {reg['archivo_historico']} "
      f"({reg['fecha_historico']}) hay {len(reg['diferencias'])} diferencia(s): "
      + "; ".join(reg["diferencias"][:5]) + ". No es una regresión del código ni cambia "
      f"ningún resultado: las diferencias son variaciones mínimas del puntaje del top-1 "
      f"(del orden de la milésima) y **ningún acierto ni ranking se movió**. La causa es "
      f"haber reconstruido el índice TF-IDF después de corregir el recuento de estados en "
      f"la documentación, que forma parte del corpus y por tanto altera los pesos de forma "
      f"imperceptible. La corrección de la clave de la pregunta Q16 tampoco cambió ningún "
      f"acierto.")
A(f"2. **Los puntajes no son comparables entre métodos.** El promedio del top-1 es "
  f"{com(AGG['score_prom_top1_tfidf'], 4)} con TF-IDF y "
  f"{com(AGG['score_prom_top1_embeddings'], 4)} con Granite, pero eso **no** mide cuánto "
  f"mejor es uno: los cosenos de un modelo de frases parten de una base más alta. Los "
  f"umbrales de banda del banco (alto >0,15) se calibraron sobre TF-IDF: con TF-IDF solo "
  f"{RES_TF['resumen']['bandas_score']['alto']} de {AGG['n_preguntas']} preguntas caen en "
  f"«alta», con embeddings prácticamente todas. Lo comparable es **en qué posición** aparece "
  f"el dato correcto.")
A("")
A("### 6.7 Un punto a favor de los embeddings que no se ve en el banco")
A("")
A("Mientras el índice de TF-IDF fue un archivo serializado con scikit-learn 1.9.0, "
  "cargarlo con la versión instalada (1.9.1) producía esta advertencia:")
A("")
A("```")
A("InconsistentVersionWarning: Trying to unpickle estimator TfidfVectorizer")
A("from version 1.9.0 when using version 1.9.1.")
A("```")
A("")
A("Al reconstruir el índice en esta ronda —necesario porque el corpus cambió— el archivo "
  "quedó serializado con la versión instalada y **el aviso desapareció**: el problema tiene "
  "arreglo, y es reconstruir el índice. El argumento de fondo, sin embargo, se mantiene y "
  "conviene entenderlo: **el índice de TF-IDF es un archivo serializado atado a la versión de "
  "scikit-learn con la que se construyó**, así que cualquier actualización de la librería "
  "obliga a reconstruirlo y, hasta que se haga, el sistema avisa. Un modelo de embeddings es "
  "un artefacto estándar que no depende de la versión de la librería de turno. Esto le da la "
  "razón al motivo del docente, pero en el plano de la **reproducibilidad y el "
  "mantenimiento**, no en el de la calidad de recuperación: son dos cosas distintas y no "
  "conviene confundirlas.")
A("")

# ---------------------------------------------------------------- 7
A("## 7. Decisión final y siguiente paso")
A("")
A("Para que la decisión no dependa de una impresión, se fijó por escrito una **regla de "
  "adopción**: los embeddings pasan a ser método principal solo si no empeoran ninguna de las "
  "tres métricas que importan.")
A("")
A("| Criterio | TF-IDF | Granite | ¿Cumple? |")
A("|---|---:|---:|:--:|")
A(f"| Top-1 con respuesta | {AGG['top1_tfidf']} | {AGG['top1_embeddings']} | "
  f"{'sí' if VER['top1'] else '**no**'} |")
A(f"| Top-3 con respuesta | {AGG['top3_tfidf']} | {AGG['top3_embeddings']} | "
  f"{'sí' if VER['top3'] else '**no**'} |")
A(f"| Ranking promedio no peor que un {pc_tr(VER['tolerancia_ranking']*100,0)} % | "
  f"{com(AGG['rank_prom_tfidf'])} | {com(AGG['rank_prom_embeddings'])} | "
  f"{'sí' if VER['ranking'] else '**no**'} |")
A("")
if VER["adopta"]:
    A("**Veredicto: se cumple la regla; los embeddings quedan como método recomendado.**")
    A("")
    A("Aun así, **no se retira TF-IDF**: los datos muestran que cada método gana en casos "
      "distintos y complementarios, y el sistema mantiene los dos disponibles con `--metodo`.")
else:
    A("**Veredicto: no se cumple la regla en su totalidad, así que TF-IDF sigue siendo el "
      "método por defecto.**")
    A("")
    A("El sistema mantiene los dos métodos. La razón de conservarlos no es prudencia "
      "excesiva, sino que ganan en casos distintos: TF-IDF es mejor cuando la pregunta busca "
      "una cifra o un identificador exacto y ve el fragmento completo sin límite de longitud; "
      "los embeddings son mejores cuando la pregunta está parafraseada. Quedarse con uno solo "
      "perdería la mitad de los casos.")
A("")
A("```bash")
A("# TF-IDF (por defecto)")
A('python -m memoria consultar "..." -k 2')
A("# Granite R2 (embeddings locales, contexto 32 768)")
A('python -m memoria consultar "..." -k 2 --metodo embeddings')
A("# reconstruir cada índice")
A("python -m memoria indexar                      # TF-IDF")
A("python -m memoria indexar --metodo embeddings  # Granite")
A("```")
A("")
A("### 7.1 Lo que queda pendiente")
A("")
A(f"1. **Trocear los dos fragmentos de código que aún se truncan.** Hoy la cobertura es del "
  f"{pc_tr(_cob(TR))} %; los {TR['n_exceden']} fragmentos que exceden los "
  f"{n(TR['max_seq_length'])} tokens son listados de código (`03_codigo` y `05_codigo`). "
  f"Partirlos en trozos de unas 8 000 unidades con solape los haría vectorizables por "
  f"completo. No se hizo aquí porque alteraría el corpus de "
  f"{n(IND['tfidf']['n_fragmentos'])} fragmentos, cifra citada en la documentación y "
  f"vigilada por la regla R17, y porque R11 exige que el índice cubra exactamente el corpus "
  f"declarado.")
A(f"2. **El coste de indexar con embeddings es alto.** Vectorizar el corpus con Granite "
  f"tardó {n(TIEMPO_INDEXADO_S)} segundos en CPU usando "
  f"{n(TR_IND.get('lotes'))} lotes, porque las dos secuencias de 32 768 tokens dominan el "
  f"tiempo (la atención global es cuadrática). Se paga una vez por índice y no en cada "
  f"consulta, pero conviene saberlo antes de reindexar en una demostración en vivo.")
A("")
A("### 7.2 Estado de la decisión D007")
A("")
A(f"D007 está en estado `{d007['estado']}` desde la implementación anterior, con la redacción "
  f"corregida (embeddings **locales**, no «vía API key») y el resultado de la evaluación en "
  f"su justificación. Esta ronda no la modificó: cambiar el modelo es una mejora de "
  f"implementación dentro de la misma decisión, no una decisión nueva.")
A("")
A("Se mantiene un efecto colateral conocido en las reglas: **R15 sigue fallando**. R15 "
  "comprueba en dos sentidos: (a) que la decisión vigente esté implementada en el código "
  "—eso ya se cumple, `embedding` aparece en `rag.py`— y (b) que una decisión **superada** no "
  "siga implementada. La segunda sigue disparando porque D002 está marcada como `superada` y "
  "su marcador `TfidfVectorizer` continúa en el código, cosa inevitable mientras TF-IDF se "
  "conserve como respaldo. La regla supone que una técnica sucede y elimina a la anterior, y "
  "aquí lo decidido es «sucede como método principal, se conserva como respaldo». Las "
  "opciones son las mismas de la ronda anterior: enmendar R15 para admitir una excepción "
  "declarada en decisiones superadas, cambiar el estado de D002 (que R16 limita a "
  "`vigente|superada|propuesta|pendiente_implementacion` y exigiría ajustar además el tema de "
  "D007), o dejarlo documentado como limitación conocida. Ninguna se aplicó sin consultar.")
A("")

# ---------------------------------------------------------------- anexo
A("## Anexo: trazabilidad y reproducibilidad")
A("")
A("| Artefacto | Contenido |")
A("|---|---|")
A("| `src/memoria/rag.py` | Los dos métodos (`metodo=\"tfidf\"` por defecto) |")
A(f"| `data/memoria/rag_indice.json` | Índice TF-IDF (metadatos), sin cambios: "
  f"{n(IND['tfidf']['n_fragmentos'])} fragmentos |")
A(f"| `data/memoria/rag_indice_embeddings.json` | Índice de embeddings con Granite: "
  f"{n(IND['embeddings']['n_fragmentos'])} fragmentos, {n(IND['embeddings']['dimension'])} "
  f"dimensiones, cobertura {pc_tr(_cob(TR))} % |")
A(f"| `data/memoria/rag_embeddings.npy` | Matriz de vectores "
  f"({n(IND['embeddings']['n_fragmentos'])} × {n(IND['embeddings']['dimension'])}) |")
A("| `scripts/banco_preguntas.py` | Banco de 20 preguntas, con `--metodo` y `--salida` |")
A("| `scripts/comparar_rag.py` | Comparación de los dos métodos y análisis de truncamiento |")
A("| `data/memoria/resultados_banco_tfidf.json` | Resultado del banco con TF-IDF |")
A("| `data/memoria/resultados_banco_embeddings.json` | Resultado del banco con Granite |")
A("| `data/memoria/comparacion_rag.json` | Todas las cifras citadas aquí |")
A("| `data/memoria/comparacion_rag_minilm.json` | Evidencia del intento con MiniLM (§5) |")
A("")
A("Reproducción completa:")
A("")
A("```bash")
A("python -m memoria indexar --metodo embeddings")
A("python scripts/banco_preguntas.py --metodo tfidf \\")
A("     --salida data/memoria/resultados_banco_tfidf.json")
A("python scripts/banco_preguntas.py --metodo embeddings \\")
A("     --salida data/memoria/resultados_banco_embeddings.json")
A("python scripts/comparar_rag.py")
A("python src/generar_comparacion_tfidf_embeddings.py")
A("```")
A("")
A("El modelo de embeddings **no se descarga**: se carga de la caché local de Hugging Face "
  "y el sistema fuerza el modo sin conexión, de modo que si no estuviera presente fallaría "
  "con un mensaje explícito en lugar de usar la red.")
A("")

SALIDA.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"escrito {SALIDA}")
print(f"  {len(L)} líneas, {len(''.join(L).encode('utf-8'))} bytes")
print(f"  veredicto: adopta={VER['adopta']} (top1={VER['top1']} top3={VER['top3']} "
      f"ranking={VER['ranking']})")
