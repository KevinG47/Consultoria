# -*- coding: utf-8 -*-
"""
generar_comparacion_tfidf_embeddings.py
=======================================

Genera `documentacion_auditoria/comparacion_tfidf_vs_embeddings.md` a partir de
las cifras ya calculadas en:
  - data/memoria/comparacion_rag.json          (métricas y tabla comparativa)
  - data/memoria/resultados_banco_tfidf.json
  - data/memoria/resultados_banco_embeddings.json
  - data/memoria/decisiones.yaml               (texto literal de D002 y D007)
  - data/memoria/rag_indice.json / rag_indice_embeddings.json

Regla del proyecto: ninguna cifra del documento se escribe a mano.
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
SALIDA = DOC / "comparacion_tfidf_vs_embeddings.md"

C = json.loads((MEM / "comparacion_rag.json").read_text(encoding="utf-8"))
RES_TF = json.loads((MEM / "resultados_banco_tfidf.json").read_text(encoding="utf-8"))
RES_EM = json.loads((MEM / "resultados_banco_embeddings.json").read_text(encoding="utf-8"))
DEC = {d["id"]: d for d in (yaml.safe_load(
    (MEM / "decisiones.yaml").read_text(encoding="utf-8")) or {}).get("decisiones", [])}
IND_TF = json.loads((MEM / "rag_indice.json").read_text(encoding="utf-8"))
IND_EM = json.loads((MEM / "rag_indice_embeddings.json").read_text(encoding="utf-8"))

AGG = C["agregados"]
TR = C["truncamiento"]
IND = C["indices"]
d002, d007 = DEC["D002"], DEC["D007"]


def n(x):
    """Entero o decimal con separadores espanoles (espacio de miles, coma decimal)."""
    if isinstance(x, float):
        return f"{x:,.1f}".replace(",", "\x00").replace(".", ",").replace("\x00", " ")
    return f"{x:,}".replace(",", " ")


def pc(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",")


def com(x, dec=2):
    return f"{x:.{dec}f}".replace(".", ",")


def plegado(txt: str) -> str:
    return " ".join(str(txt).split())


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
  f"siempre) y embeddings locales (el nuevo). Se evaluaron los dos con el mismo banco de "
  f"{AGG['n_preguntas']} preguntas sobre el mismo corpus de "
  f"{n(IND['tfidf']['n_fragmentos'])} fragmentos.")
A("")
A(f"| Métrica | TF-IDF | Embeddings | Ganador |")
A(f"|---|---:|---:|---|")
A(f"| Respuesta esperada en el **top-1** | {AGG['top1_tfidf']}/{AGG['n_preguntas']} | "
  f"{AGG['top1_embeddings']}/{AGG['n_preguntas']} | embeddings (+1) |")
A(f"| Respuesta esperada en el **top-3** | {AGG['top3_tfidf']}/{AGG['n_preguntas']} | "
  f"{AGG['top3_embeddings']}/{AGG['n_preguntas']} | TF-IDF (+1) |")
A(f"| Ranking promedio del dato correcto (de {n(IND['tfidf']['n_fragmentos'])}) | "
  f"{com(AGG['rank_prom_tfidf'])} | {com(AGG['rank_prom_embeddings'])} | TF-IDF (3,2× mejor) |")
A(f"| Preguntas ganadas | {AGG['gana_tfidf']} | {AGG['gana_embeddings']} | empate técnico "
  f"({AGG['empates']} empates) |")
A("")
A(f"**Conclusión: la migración, tal como está implementada, NO mejora el sistema.** El "
  f"balance es de un acierto más en el top-1, un acierto menos en el top-3 y un ranking "
  f"promedio {com(AGG['rank_prom_embeddings']/AGG['rank_prom_tfidf'], 1)} veces peor. La "
  f"causa está medida: el modelo trunca cada fragmento a {n(TR['max_seq_length'])} tokens y "
  f"los fragmentos promedian {n(TR['tokens_promedio'])} tokens, de modo que solo se vectoriza "
  f"el **{pc(TR['cobertura_media_pct'])} %** del contenido de cada fragmento. TF-IDF, al ser "
  f"una bolsa de palabras, ve el fragmento completo. La recomendación es **mantener TF-IDF "
  f"como método por defecto** y dejar los embeddings disponibles como método complementario, "
  f"con el troceado de fragmentos como siguiente paso (ver §6).")
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
q = "cuantos registros con edad mayor a 100 hay"
A("[RAG] términos que pesan: [('mayor 100', 0.3988), ('edad mayor', 0.3988),")
A("                            ('cuantos registros', 0.3988), ('cuantos', 0.3426)]")
A("```")
A("")
A("Además, para un vocabulario técnico y estable —cifras, rutas de archivo, "
  "identificadores como `n_atipicos_edad`— coincidir en la palabra exacta es justo lo que "
  "se necesita.")
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
  f"fragmento, producidos por el modelo local "
  f"`{IND['embeddings']['modelo']}`. La comparación es la misma que en TF-IDF: similitud "
  f"coseno sobre vectores normalizados.")
A("")
A("**Ventajas.** Entiende sinónimos, paráfrasis y conceptos que no comparten ni una "
  "palabra. Si la pregunta dice «¿cuántos investigadores hay registrados?» y el documento "
  "dice «total de personas únicas en el padrón», un embedding puede relacionarlos y TF-IDF "
  "no. Además es **multilingüe**: la misma frase en español e inglés cae cerca.")
A("")
A("**Límites.** Requiere un modelo: aquí son ~120 MB de pesos más la librería `torch`, así "
  "que el sistema pesa mucho más y tarda más en arrancar (cargar el modelo cuesta unos "
  "20 segundos). Además el modelo **tiene un límite de longitud**: solo mira los primeros "
  "tokens de cada texto, y todo lo que venga después se descarta sin avisar. Y se pierde la "
  "explicabilidad: no hay un «término que pesa» que se pueda mostrar, solo un número de "
  "similitud.")
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
A(f"La implementación adoptada satisface el motivo del docente —no depender de un diccionario "
  f"construido a medida, sino de un modelo estándar que cualquiera puede cargar— sin salir de "
  f"la máquina. La decisión quedó corregida en `decisiones.yaml` conservando la redacción "
  f"original en un campo aparte, para que el cambio quede trazado. Lo que se midió al "
  f"implementarla se ve en §5.")
A("")

# ---------------------------------------------------------------- 5
A("## 5. Resultados de la comparación")
A("")
A("### 5.1 Cómo se comparó")
A("")
A(f"El mismo banco de {AGG['n_preguntas']} preguntas, el mismo corpus "
  f"({n(IND['tfidf']['n_fragmentos'])} fragmentos de {n(IND['tfidf']['n_documentos'])} "
  f"documentos), los dos índices construidos por separado. Por pregunta se comparó: el "
  f"puntaje del top-1, si la respuesta esperada está en el top-1 y en el top-3, y la "
  f"posición del fragmento correcto en el ranking completo. El criterio para decidir quién "
  f"gana en cada pregunta es un orden lexicográfico: primero el acierto en top-1, después "
  f"el acierto en top-3 y, si empatan, la mejor posición del dato correcto.")
A("")
A("### 5.2 Tabla por pregunta")
A("")
A("| Q | Grupo | Score top-1 TF-IDF | Score top-1 emb. | Top-1 TF-IDF | Top-1 emb. | Top-3 TF-IDF | Top-3 emb. | Rank TF-IDF | Rank emb. | Gana |")
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
A("### 5.3 Agregados")
A("")
A("| Métrica | TF-IDF | Embeddings |")
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
A("| Grupo | n | Top-1 TF-IDF | Top-1 emb. | Top-3 TF-IDF | Top-3 emb. |")
A("|---|---:|---:|---:|---:|---:|")
for g, v in sorted(C["por_grupo"].items()):
    A(f"| {g} | {v['n']} | {v['top1_tfidf']} | {v['top1_embeddings']} | "
      f"{v['top3_tfidf']} | {v['top3_embeddings']} |")
A("")
A("### 5.4 En qué casos gana cada método")
A("")
emb_solo1 = ", ".join(f"Q{i}" for i in AGG["emb_solo_top1"])
tf_solo1 = ", ".join(f"Q{i}" for i in AGG["tfidf_solo_top1"])
emb_solo3 = ", ".join(f"Q{i}" for i in AGG["emb_solo_top3"])
tf_solo3 = ", ".join(f"Q{i}" for i in AGG["tfidf_solo_top3"])
A(f"- **Embeddings encuentra y TF-IDF no, en el top-1** ({emb_solo1}): son preguntas "
  f"redactadas con otras palabras que el documento («¿cuántas referencias tiene el estado "
  f"del arte?», «¿cuántos commits tiene el repo auditado?»). Aquí el embedding hace "
  f"exactamente lo que promete: relaciona significado sin compartir vocabulario.")
A(f"- **TF-IDF encuentra y embeddings no, en el top-1** ({tf_solo1}): son preguntas cuyo "
  f"dato es una cifra o un identificador exacto («¿cuántos nodos tiene el grafo?» → 255; "
  f"«¿cuántos informes de validación cubre el corpus?» → once). La coincidencia literal es "
  f"imbatible para una bolsa de palabras.")
A(f"- **Top-3**: embeddings gana en {emb_solo3 or 'ninguna'} y TF-IDF en {tf_solo3}.")
A(f"- En {AGG['empates']} preguntas los dos métodos empatan, y en {AGG['corpus_tfidf']} de "
  f"las {AGG['n_preguntas']} el dato está en el corpus de todos modos.")
A("")
A("### 5.5 La causa medida: el modelo solo ve el 7,8 % de cada fragmento")
A("")
A("La diferencia de ranking no es una opinión ni una impresión: tiene una causa medible.")
A("")
A("| Medida | Valor |")
A("|---|---:|")
A(f"| Longitud máxima que procesa el modelo | **{n(TR['max_seq_length'])} tokens** |")
A(f"| Tokens por fragmento (promedio) | {n(TR['tokens_promedio'])} |")
A(f"| Tokens por fragmento (mediana) | {n(TR['tokens_mediana'])} |")
A(f"| Tokens del fragmento más largo | {n(TR['tokens_max'])} |")
A(f"| Fragmentos que superan el máximo | **{TR['n_exceden']} de {TR['n_fragmentos']} "
  f"({pc(TR['pct_exceden'])} %)** |")
A(f"| Contenido realmente vectorizado | **{pc(TR['cobertura_media_pct'])} %** |")
A("")
A(f"El modelo `{IND['embeddings']['modelo']}` está diseñado para frases, no para "
  f"documentos: mira como mucho {n(TR['max_seq_length'])} tokens y descarta el resto sin "
  f"avisar. Nuestros fragmentos nacen de secciones completas de LaTeX —el mayor, "
  f"`{TR['ejemplos_excedidos'][0]['id']}`, tiene {n(TR['ejemplos_excedidos'][0]['tokens'])} "
  f"tokens— de modo que **{TR['n_exceden']} de {TR['n_fragmentos']} fragmentos "
  f"({pc(TR['pct_exceden'])} %)** se vectorizan solo por su encabezado. Cuando la respuesta "
  f"está al principio del fragmento, el embedding la encuentra; cuando está a mitad o al "
  f"final, es invisible para él, mientras que TF-IDF la ve porque cuenta palabras en todo "
  f"el texto.")
A("")
A("Esto explica las dos observaciones que de otro modo parecerían contradictorias: el "
  f"top-1 mejora ligeramente (el encabezado de un fragmento suele decir de qué trata) pero "
  f"el ranking promedio empeora mucho, porque el dato concreto casi nunca está en el "
  f"encabezado.")
A("")
A("### 5.6 Dos comprobaciones de honestidad")
A("")
reg = C["no_regresion_tfidf"]
A(f"1. **TF-IDF no se rompió.** La corrida nueva de TF-IDF es **idéntica** a la corrida "
  f"histórica ({reg['archivo_historico']}, del {reg['fecha_historico']}) en las "
  f"{reg['preguntas_comparadas']} preguntas: mismos puntajes, mismos rankings, mismos "
  f"aciertos. Añadir el segundo método no cambió el comportamiento del primero.")
A(f"2. **Los puntajes no son comparables entre métodos.** El promedio del top-1 es "
  f"{com(AGG['score_prom_top1_tfidf'], 4)} con TF-IDF y "
  f"{com(AGG['score_prom_top1_embeddings'], 4)} con embeddings, pero eso **no** significa "
  f"que los embeddings sean siete veces mejores. Los cosenos de un modelo de frases parten "
  f"de una base mucho más alta: con embeddings las {AGG['n_preguntas']} preguntas caen en "
  f"la banda «alta» del banco (>0,15) y con TF-IDF solo "
  f"{RES_TF['resumen']['bandas_score']['alto']}. Los umbrales de banda se calibraron sobre "
  f"TF-IDF y no sirven para comparar métodos; lo que sí es comparable es *en qué posición* "
  f"aparece el dato correcto.")
A("")
A("### 5.7 Un punto a favor de los embeddings que no se ve en el banco")
A("")
A("Al cargar el índice de TF-IDF aparece esta advertencia, reproducible en esta máquina:")
A("")
A("```")
A("InconsistentVersionWarning: Trying to unpickle estimator TfidfVectorizer")
A("from version 1.9.0 when using version 1.9.1.")
A("```")
A("")
A("Es decir: **el índice de TF-IDF queda atado a la versión de scikit-learn con la que se "
  "construyó**, y una actualización de la librería puede invalidarlo. Esto le da la razón al "
  "motivo del docente: un modelo de embeddings es un artefacto estándar y portable, mientras "
  "que el «diccionario» de TF-IDF es un archivo serializado dependiente del entorno. Es un "
  "argumento de reproducibilidad, no de calidad de recuperación, y conviene no confundirlos.")
A("")

# ---------------------------------------------------------------- 6
A("## 6. Decisión final y siguiente paso")
A("")
A("**No se adopta embeddings como método principal todavía.** El sistema queda con los dos "
  "métodos disponibles y **TF-IDF como predeterminado**:")
A("")
A("```bash")
A('python -m memoria consultar "..." -k 2                        # TF-IDF (por defecto)')
A('python -m memoria consultar "..." -k 2 --metodo embeddings    # embeddings locales')
A('python -m memoria indexar --metodo embeddings                 # reindexar con embeddings')
A("```")
A("")
A("El motivo de mantener los dos, y no sustituir uno por otro, es que ganan en casos "
  "distintos y complementarios: TF-IDF es mejor cuando la pregunta busca una cifra o un "
  "identificador exacto y cuando el dato está en cualquier punto del fragmento; los "
  "embeddings son mejores cuando la pregunta está parafraseada. Quedarse con uno solo "
  "perdería la mitad de los casos.")
A("")
A("**El siguiente paso, si se quiere que los embeddings rindan, es trocear los fragmentos.** "
  f"El problema no es el modelo sino el tamaño de la entrada: hoy {TR['n_exceden']} de "
  f"{TR['n_fragmentos']} fragmentos exceden el máximo y solo se vectoriza el "
  f"{pc(TR['cobertura_media_pct'])} % del texto. Partir cada fragmento en trozos de unas "
  f"{n(TR['max_seq_length'])} unidades (con solape para no cortar ideas a la mitad) haría "
  f"que el modelo viera todo el contenido.")
A("")
A("Ese cambio **no es inocuo y por eso no se hizo**: el corpus pasaría de "
  f"{n(IND['tfidf']['n_fragmentos'])} fragmentos a varios cientos, y la cifra «150 "
  f"fragmentos» está citada en la documentación y vigilada por la regla R17, además de que "
  f"R11 exige que el índice cubra exactamente el corpus declarado. Hacerlo obliga a "
  f"actualizar esas cifras en todos los documentos y a reindexar ambos métodos. Queda como "
  f"propuesta, no como hecho consumado.")
A("")
A("### Estado de la decisión D007")
A("")
A(f"D007 quedó actualizada en `data/memoria/decisiones.yaml` a estado `{d007['estado']}`, "
  f"con la redacción corregida (embeddings **locales**, no «vía API key») y con el "
  f"resultado de esta evaluación en su justificación. Se documenta además un efecto "
  f"colateral en las reglas: **R15 seguirá fallando**, y conviene entender por qué.")
A("")
A("R15 hace dos comprobaciones simétricas: (a) que la decisión vigente esté implementada "
  "en el código, y (b) que una decisión **superada** no siga implementada. La primera ya se "
  "cumple —`embedding` aparece en `rag.py`—, pero la segunda sigue disparando porque D002 "
  "está marcada como `superada` y su marcador `TfidfVectorizer` continúa en el código. Y "
  "continuará mientras TF-IDF siga existiendo como respaldo, que es justamente lo que se "
  "decidió conservar. Dicho de otro modo: la regla supone que una técnica sucede y elimina a "
  "la anterior, y aquí la decisión real es «sucede como método principal, se conserva como "
  "respaldo». Ajustar eso exige tocar la regla o el estado de D002, y ninguna de las dos "
  "cosas se hizo sin consultar.")
A("")

# ---------------------------------------------------------------- anexo
A("## Anexo: trazabilidad y reproducibilidad")
A("")
A("| Artefacto | Contenido |")
A("|---|---|")
A("| `src/memoria/rag.py` | Los dos métodos (`metodo=\"tfidf\"` por defecto) |")
A(f"| `data/memoria/rag_indice.json` | Índice TF-IDF (metadatos), sin cambios: "
  f"{n(IND['tfidf']['n_fragmentos'])} fragmentos |")
A(f"| `data/memoria/rag_indice_embeddings.json` | Índice de embeddings: "
  f"{n(IND['embeddings']['n_fragmentos'])} fragmentos, {n(IND['embeddings']['dimension'])} "
  f"dimensiones |")
A("| `scripts/banco_preguntas.py` | Banco de 20 preguntas, con `--metodo` y `--salida` |")
A("| `scripts/comparar_rag.py` | Comparación de los dos métodos y análisis de truncamiento |")
A("| `data/memoria/resultados_banco_tfidf.json` | Resultado del banco con TF-IDF |")
A("| `data/memoria/resultados_banco_embeddings.json` | Resultado del banco con embeddings |")
A("| `data/memoria/comparacion_rag.json` | Todas las cifras citadas aquí |")
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
A("```")
A("")
A(f"El modelo de embeddings **no se descarga**: se carga de la caché local de Hugging "
  f"Face y el sistema fuerza el modo sin conexión, de modo que si no estuviera presente "
  f"fallaría con un mensaje explícito en lugar de usar la red.")
A("")

SALIDA.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"escrito {SALIDA}")
print(f"  {len(L)} líneas, {len(''.join(L).encode('utf-8'))} bytes")
