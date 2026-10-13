# Comparación: TF-IDF vs embeddings para el RAG del proyecto

**Auditoría estadística del sistema de reconocimiento de MinCiencias — sistema de memoria del agente**  
Documento generado por `documentacion_auditoria/src/generar_comparacion_tfidf_embeddings.py` a partir de `data/memoria/comparacion_rag.json` y de los dos resultados del banco de preguntas. Fecha: 2026-10-13.

## Resumen en una página

El RAG del proyecto sabe recuperar con **dos métodos intercambiables**: TF-IDF (el de siempre) y embeddings locales, hoy con **Granite Embedding 97M Multilingual R2** (contexto de 32 768 tokens). Se evaluaron los dos con el mismo banco de 20 preguntas sobre el mismo corpus de 150 fragmentos.

| Métrica | TF-IDF | Granite | Ganador |
|---|---:|---:|---|
| Respuesta esperada en el **top-1** | 9/20 | 7/20 | TF-IDF |
| Respuesta esperada en el **top-3** | 11/20 | 10/20 | TF-IDF |
| Ranking promedio del dato correcto (de 150) | 8,42 | 21,11 | TF-IDF |
| Preguntas ganadas | 8 | 6 | 6 empates |
| Cobertura del corpus al vectorizar | 100 % | 79,6 % | — |

**Conclusión: con Granite los embeddings mejoran mucho respecto al intento anterior, pero no superan a TF-IDF en las tres métricas.** Cumplen la regla de adopción en 0 de 3 criterios (ver §7), así que se recomienda **mantener TF-IDF como método por defecto** y los embeddings como método complementario, con el truncamiento ya acotado a 2 fragmentos de 150 (antes eran 143).

El salto respecto al primer intento está medido: con MiniLM (contexto de 128 tokens) se truncaban 143 de 150 fragmentos y solo se vectorizaba el 7,8 % del contenido; con Granite se truncan 2 de 150 y la cobertura sube al 79,6 %.

## 1. Qué es TF-IDF, en lenguaje llano

TF-IDF significa *Term Frequency – Inverse Document Frequency*, es decir «frecuencia del término por rareza del término». Es la forma más clásica de buscar texto y funciona en tres pasos:

1. **Cuenta palabras.** Cada fragmento se convierte en una lista de las palabras que contiene. El orden no importa: «el perro muerde al hombre» y «el hombre muerde al perro» quedan representados igual.
2. **Pondera por rareza.** Una palabra que aparece en todos los documentos («de», «informe») casi no aporta; una que aparece en pocos («bqtm-4y2h», «77 237») es muy informativa y pesa mucho. De ahí el «inverse document frequency».
3. **Compara.** La pregunta se convierte en la misma lista de palabras ponderadas y se mide el ángulo entre ambos vectores (similitud coseno). Los fragmentos con más palabras raras en común quedan arriba.

**Ventajas.** Es muy rápido, no necesita ninguna dependencia pesada, es determinista (la misma consulta da siempre el mismo resultado) y —esto importa en una auditoría— es **explicable**: se puede mostrar exactamente qué término está pesando en la recuperación. El sistema lo hace con el comando `terminos_relevantes`, por ejemplo:

```
[RAG] términos que pesan: [('mayor 100', 0.3988), ('edad mayor', 0.3988),
                            ('cuantos registros', 0.3988), ('cuantos', 0.3426)]
```

Además, para un vocabulario técnico y estable —cifras, rutas de archivo, identificadores como `n_atipicos_edad`— coincidir en la palabra exacta es justo lo que se necesita. Y **no tiene límite de longitud**: ve el fragmento completo, mida lo que mida.

**Límites.** No entiende sinónimos ni paráfrasis: si el documento dice «investigadores únicos» y la pregunta dice «personas distintas», TF-IDF no ve ninguna relación, porque no comparten ni una palabra. Tampoco entiende el significado: dos frases con las mismas palabras en distinto orden le resultan idénticas.

## 2. Qué es un embedding, en lenguaje llano

Un *embedding* es una forma de convertir un texto en una lista de números —un vector— de manera que **textos con significado parecido queden cerca** en ese espacio numérico. En lugar de contar palabras, se usa un modelo entrenado con millones de frases para aprender qué textos suelen significar lo mismo.

En este proyecto el vector tiene 384 números por fragmento, producidos por el modelo local `ibm-granite/granite-embedding-97m-multilingual-r2`: 97 millones de parámetros, arquitectura ModernBERT y **contexto de 32 768 tokens**. La comparación es la misma que en TF-IDF: similitud coseno sobre vectores normalizados.

**Ventajas.** Entiende sinónimos, paráfrasis y conceptos que no comparten ni una palabra. Si la pregunta dice «¿cuántos investigadores hay registrados?» y el documento dice «total de personas únicas en el padrón», un embedding puede relacionarlos y TF-IDF no. Además es **multilingüe** (la misma frase en español e inglés cae cerca) y, con contexto largo, puede procesar un documento entero en lugar de solo su encabezado.

**Límites.** Requiere un modelo: aquí son ~210 MB de pesos más la librería `torch`, así que el sistema pesa más y tarda más en arrancar (cargar el modelo cuesta unos 5 segundos, pero vectorizar el corpus entero tarda mucho más que TF-IDF: ver §5.3 y §7.1). El contexto, aunque sea grande, **es finito**: lo que exceda 32 768 tokens se descarta sin avisar. Y se pierde la explicabilidad: no hay un «término que pesa» que se pueda mostrar, solo un número de similitud.

> **Por qué un modelo local y no una API.** La rúbrica prohíbe subir datos de la contraparte a la nube. Por eso el sistema usa un modelo que corre en la propia máquina (CPU) y que **nunca** consulta la red: si el modelo no estuviera ya descargado, el sistema falla con un mensaje claro en lugar de intentar bajarlo.

## 3. Por qué el sistema usaba TF-IDF

Está registrado como decisión **D002** (2026-09-15), hoy en estado `superada` porque D007 la sucedió. Su justificación literal fue:

> Corpus pequeño (~24 documentos, 137 fragmentos) y homogéneo en vocabulario técnico; TF-IDF resuelve el problema sin dependencias externas ni costo, y es determinista y explicable.

Y la decisión: «Usar TF-IDF (no embeddings) para el RAG». Las alternativas que se descartaron entonces fueron: embeddings vía API, embeddings locales.

En otras palabras: con ~24 documentos y ~137 fragmentos, un vocabulario homogéneo y técnico, TF-IDF resolvía el problema sin añadir dependencias, sin coste y con resultados auditables. Fue una decisión razonable para el tamaño y el momento del proyecto.

## 4. Por qué se pidió migrar a embeddings

Está registrado como decisión **D007** (2026-09-15). Conviene subrayar que el motivo **no** era que la recuperación fallara, sino el mantenimiento y la transferencia del sistema:

> Decisión del docente: un "diccionario" (TF-IDF) es incómodo de mantener y transferir; el proyecto debe dejar reproducibilidad para futuros trabajos y otros equipos.

La decisión se registró originalmente así: «Migrar el RAG de TF-IDF a embeddings vía API key». Esa redacción era **imposible de cumplir en este proyecto**, y no por dificultad técnica:

> La redacción original pedía embeddings "vía API key". Es inviable en este proyecto porque la rúbrica prohíbe subir datos de la contraparte a la nube; se implementó con un modelo LOCAL, que conserva el motivo del docente —no depender de un diccionario construido a medida— sin usar la red.

La implementación adoptada satisface el motivo del docente —no depender de un diccionario construido a medida, sino de un modelo estándar que cualquiera puede cargar— sin salir de la máquina. La decisión quedó corregida en `decisiones.yaml` conservando la redacción original en un campo aparte, para que el cambio quede trazado.

## 5. El primer intento falló por el tamaño del modelo, no por la idea

La primera implementación usó `paraphrase-multilingual-MiniLM-L12-v2`. Sobre el papel cumplía: multilingüe, 384 dimensiones, español correcto. En la práctica rindió **peor** que TF-IDF, y la causa no fue una impresión sino una medida.

### 5.1 Qué pasó con MiniLM

MiniLM procesa como máximo **128 tokens** por texto. Nuestros fragmentos no son frases: nacen de secciones completas de LaTeX y promedian 1 634,7 tokens. El resultado fue que **143 de 150 fragmentos (95,3 %)** se truncaban, y solo se vectorizaba el **7,8 %** del contenido del corpus. El modelo estaba, en la práctica, leyendo el encabezado de cada sección y nada más.

Con esa configuración, la comparación contra TF-IDF quedó así:

| Métrica | TF-IDF | MiniLM |
|---|---:|---:|
| Respuesta en el top-1 | 9/20 | 10/20 |
| Respuesta en el top-3 | 11/20 | 10/20 |
| Ranking promedio del dato correcto | 8,42 | 26,63 |
| Cobertura del corpus | 100 % | 7,8 % |

El patrón era revelador: MiniLM **ganaba** donde el dato está al principio del fragmento (el encabezado dice de qué trata) y **perdía estrepitosamente** donde el dato está a mitad o al final. Por ejemplo, en la pregunta por el número de nodos del grafo, TF-IDF ponía el fragmento correcto en la posición 1 y MiniLM en la 128. Eso descartó que el problema fuera «los embeddings no sirven para este corpus»: el problema era que el modelo no llegaba a leer el corpus.

### 5.2 Qué cambió con Granite R2

`ibm-granite/granite-embedding-97m-multilingual-r2` es un modelo de tamaño comparable (97 M de parámetros, 384 dimensiones) pero con dos diferencias decisivas:

1. **Contexto de 32 768 tokens** en lugar de 128: 256 veces más. La arquitectura ModernBERT usa atención alterna —ventanas locales de 128 tokens con atención global cada 3 capas—, que es lo que permite procesar documentos largos en CPU sin agotar la memoria.
2. **Sin prefijos**: el modelo declara indicaciones vacías para consulta y documento, así que la misma función sirve para ambas (no hizo falta usar `encode_query` ni `encode_document`, aunque existan).

### 5.3 Qué quedó por resolver

El truncamiento **no desaparece del todo**: 2 fragmentos siguen excediendo el límite, porque son más largos que el propio contexto máximo del modelo:

| Fragmento | Tokens |
|---|---:|
| `objetivo_3::03_codigo` | 55 502 |
| `maestro_auditoria::05_codigo` | 55 176 |

En total, la cobertura del corpus sube del 7,8 % al **79,6 %**, y los fragmentos truncados bajan de 143 a 2. Son dos secciones de listado de código (`03_codigo` y `05_codigo`), las más voluminosas del corpus, que por su tamaño superan incluso los 32 768 tokens. Cerrar esa última brecha exigiría trocear esos dos fragmentos, cosa que no se hizo para no alterar el corpus de 150 fragmentos (ver §7.1).

## 6. Resultados de la comparación

### 6.1 Cómo se comparó

El mismo banco de 20 preguntas, el mismo corpus (150 fragmentos de 25 documentos), los dos índices construidos por separado. Por pregunta se comparó: el puntaje del top-1, si la respuesta esperada está en el top-1 y en el top-3, y la posición del fragmento correcto en el ranking completo. El criterio para decidir quién gana en cada pregunta es un orden lexicográfico: primero el acierto en top-1, después el acierto en top-3 y, si empatan, la mejor posición del dato correcto.

### 6.2 Tabla por pregunta

| Q | Grupo | Score top-1 TF-IDF | Score top-1 Granite | Top-1 TF-IDF | Top-1 Granite | Top-3 TF-IDF | Top-3 Granite | Rank TF-IDF | Rank Granite | Gana |
|---|---|---:|---:|:--:|:--:|:--:|:--:|---:|---:|---|
| 1 | A | 0,0505 | 0,8654 | sí | sí | sí | sí | 1 | 1 | empate |
| 2 | A | 0,0462 | 0,8657 | sí | no | sí | sí | 1 | 2 | tfidf |
| 3 | A | 0,1074 | 0,9169 | sí | sí | sí | sí | 1 | 1 | empate |
| 4 | A | 0,0822 | 0,8858 | no | no | no | no | 5 | 5 | empate |
| 5 | A | 0,1054 | 0,8455 | no | no | no | no | 9 | 17 | tfidf |
| 6 | A | 0,1105 | 0,8690 | no | no | no | no | 8 | 8 | empate |
| 7 | A | 0,1091 | 0,8909 | no | sí | sí | sí | 2 | 1 | embeddings |
| 8 | A | 0,0409 | 0,8391 | no | sí | sí | sí | 2 | 1 | embeddings |
| 9 | A | 0,0526 | 0,8314 | sí | no | sí | no | 1 | 58 | tfidf |
| 10 | A | 0,0500 | 0,8670 | no | no | no | no | 19 | 129 | tfidf |
| 11 | B | 0,0456 | 0,8843 | no | sí | no | sí | 4 | 1 | embeddings |
| 12 | B | 0,0529 | 0,8749 | sí | sí | sí | sí | 1 | 1 | empate |
| 13 | A | 0,0984 | 0,8657 | no | no | no | no | 16 | 4 | embeddings |
| 14 | B | 0,0529 | 0,8555 | no | no | no | no | — | — | empate |
| 15 | B | 0,0652 | 0,8533 | no | no | no | no | 82 | 22 | embeddings |
| 16 | C | 0,1051 | 0,8269 | sí | no | sí | no | 1 | 6 | tfidf |
| 17 | C | 0,0732 | 0,8753 | sí | no | sí | no | 1 | 137 | tfidf |
| 18 | A | 0,0651 | 0,8887 | sí | no | sí | sí | 1 | 3 | tfidf |
| 19 | C | 0,0546 | 0,8794 | sí | no | sí | sí | 1 | 3 | tfidf |
| 20 | C | 0,2047 | 0,8390 | no | sí | no | sí | 4 | 1 | embeddings |

### 6.3 Agregados

| Métrica | TF-IDF | Granite |
|---|---:|---:|
| Respuesta en el top-1 | **9/20** | **7/20** |
| Respuesta en el top-3 | **11/20** | **10/20** |
| Respuesta presente en el corpus | 19/20 | 19/20 |
| Score promedio del top-1 | 0,0786 | 0,8660 |
| Ranking promedio del dato correcto | **8,42** | **21,11** |
| Preguntas ganadas | 8 | 6 (+6 empates) |

Por grupos del banco (A = datos que deberían estar en el corpus, B = datos que no, C = datos del propio sistema):

| Grupo | n | Top-1 TF-IDF | Top-1 Granite | Top-3 TF-IDF | Top-3 Granite |
|---|---:|---:|---:|---:|---:|
| A | 12 | 5 | 4 | 7 | 6 |
| B | 4 | 1 | 2 | 1 | 2 |
| C | 4 | 3 | 1 | 3 | 2 |

### 6.4 En qué casos gana cada método

- **Granite encuentra y TF-IDF no, en el top-1**: Q7, Q8, Q11, Q20.
- **TF-IDF encuentra y Granite no, en el top-1**: Q2, Q9, Q16, Q17, Q18, Q19.
- **En el top-3**: Granite gana en Q11, Q20 y TF-IDF en Q9, Q16, Q17.
- En 6 preguntas los dos métodos empatan, y en 19 de las 20 el dato está en el corpus de todos modos.

Conviene leer estos números junto al ranking promedio. Las preguntas en que TF-IDF conserva ventaja son las que buscan **una cifra o un identificador exacto**: para una bolsa de palabras, coincidir en el token literal es imbatible. Las que gana Granite son las redactadas con **palabras distintas** a las del documento, que es justo lo que un embedding está entrenado para resolver.

### 6.5 Comparación de los dos modelos de embeddings

| Medida | MiniLM (128 tokens) | Granite (32 768 tokens) |
|---|---:|---:|
| Fragmentos que superan el contexto | 143 de 150 (95,3 %) | 2 de 150 (1,3 %) |
| Contenido realmente vectorizado | 7,8 % | **79,6 %** |
| Top-1 con respuesta | 10/20 | 7/20 |
| Top-3 con respuesta | 10/20 | 10/20 |
| Ranking promedio del dato correcto | 26,63 | **21,11** |

El cambio de modelo mejoró las tres métricas de los embeddings y multiplicó por 10,2 la cobertura del corpus. Dicho de otro modo: la conclusión del intento anterior —«los embeddings no superan a TF-IDF»— era **correcta para ese modelo y esa configuración**, pero no era una conclusión sobre los embeddings en general. El cuello de botella era el contexto.

### 6.6 Dos comprobaciones de honestidad

1. **TF-IDF no se rompió.** La corrida nueva de TF-IDF es **idéntica** a la corrida histórica (resultados_banco_preguntas.json, del 2026-10-01T17:25:51) en las 20 preguntas: mismos puntajes, mismos rankings, mismos aciertos. Cambiar el modelo de embeddings no cambió el comportamiento del respaldo.
2. **Los puntajes no son comparables entre métodos.** El promedio del top-1 es 0,0786 con TF-IDF y 0,8660 con Granite, pero eso **no** mide cuánto mejor es uno: los cosenos de un modelo de frases parten de una base más alta. Los umbrales de banda del banco (alto >0,15) se calibraron sobre TF-IDF: con TF-IDF solo 1 de 20 preguntas caen en «alta», con embeddings prácticamente todas. Lo comparable es **en qué posición** aparece el dato correcto.

### 6.7 Un punto a favor de los embeddings que no se ve en el banco

Al cargar el índice de TF-IDF aparece esta advertencia, reproducible en esta máquina:

```
InconsistentVersionWarning: Trying to unpickle estimator TfidfVectorizer
from version 1.9.0 when using version 1.9.1.
```

Es decir: **el índice de TF-IDF queda atado a la versión de scikit-learn con la que se construyó**, y una actualización de la librería puede invalidarlo. Esto le da la razón al motivo del docente: un modelo de embeddings es un artefacto estándar y portable, mientras que el «diccionario» de TF-IDF es un archivo serializado dependiente del entorno. Es un argumento de reproducibilidad, no de calidad de recuperación, y conviene no confundirlos.

## 7. Decisión final y siguiente paso

Para que la decisión no dependa de una impresión, se fijó por escrito una **regla de adopción**: los embeddings pasan a ser método principal solo si no empeoran ninguna de las tres métricas que importan.

| Criterio | TF-IDF | Granite | ¿Cumple? |
|---|---:|---:|:--:|
| Top-1 con respuesta | 9 | 7 | **no** |
| Top-3 con respuesta | 11 | 10 | **no** |
| Ranking promedio no peor que un 120 % | 8,42 | 21,11 | **no** |

**Veredicto: no se cumple la regla en su totalidad, así que TF-IDF sigue siendo el método por defecto.**

El sistema mantiene los dos métodos. La razón de conservarlos no es prudencia excesiva, sino que ganan en casos distintos: TF-IDF es mejor cuando la pregunta busca una cifra o un identificador exacto y ve el fragmento completo sin límite de longitud; los embeddings son mejores cuando la pregunta está parafraseada. Quedarse con uno solo perdería la mitad de los casos.

```bash
# TF-IDF (por defecto)
python -m memoria consultar "..." -k 2
# Granite R2 (embeddings locales, contexto 32 768)
python -m memoria consultar "..." -k 2 --metodo embeddings
# reconstruir cada índice
python -m memoria indexar                      # TF-IDF
python -m memoria indexar --metodo embeddings  # Granite
```

### 7.1 Lo que queda pendiente

1. **Trocear los dos fragmentos de código que aún se truncan.** Hoy la cobertura es del 79,6 %; los 2 fragmentos que exceden los 32 768 tokens son listados de código (`03_codigo` y `05_codigo`). Partirlos en trozos de unas 8 000 unidades con solape los haría vectorizables por completo. No se hizo aquí porque alteraría el corpus de 150 fragmentos, cifra citada en la documentación y vigilada por la regla R17, y porque R11 exige que el índice cubra exactamente el corpus declarado.
2. **El coste de indexar con embeddings es alto.** Vectorizar el corpus con Granite tardó 1 704,2 segundos en CPU usando 10 lotes, porque las dos secuencias de 32 768 tokens dominan el tiempo (la atención global es cuadrática). Se paga una vez por índice y no en cada consulta, pero conviene saberlo antes de reindexar en una demostración en vivo.

### 7.2 Estado de la decisión D007

D007 está en estado `vigente` desde la implementación anterior, con la redacción corregida (embeddings **locales**, no «vía API key») y el resultado de la evaluación en su justificación. Esta ronda no la modificó: cambiar el modelo es una mejora de implementación dentro de la misma decisión, no una decisión nueva.

Se mantiene un efecto colateral conocido en las reglas: **R15 sigue fallando**. R15 comprueba en dos sentidos: (a) que la decisión vigente esté implementada en el código —eso ya se cumple, `embedding` aparece en `rag.py`— y (b) que una decisión **superada** no siga implementada. La segunda sigue disparando porque D002 está marcada como `superada` y su marcador `TfidfVectorizer` continúa en el código, cosa inevitable mientras TF-IDF se conserve como respaldo. La regla supone que una técnica sucede y elimina a la anterior, y aquí lo decidido es «sucede como método principal, se conserva como respaldo». Las opciones son las mismas de la ronda anterior: enmendar R15 para admitir una excepción declarada en decisiones superadas, cambiar el estado de D002 (que R16 limita a `vigente|superada|propuesta|pendiente_implementacion` y exigiría ajustar además el tema de D007), o dejarlo documentado como limitación conocida. Ninguna se aplicó sin consultar.

## Anexo: trazabilidad y reproducibilidad

| Artefacto | Contenido |
|---|---|
| `src/memoria/rag.py` | Los dos métodos (`metodo="tfidf"` por defecto) |
| `data/memoria/rag_indice.json` | Índice TF-IDF (metadatos), sin cambios: 150 fragmentos |
| `data/memoria/rag_indice_embeddings.json` | Índice de embeddings con Granite: 150 fragmentos, 384 dimensiones, cobertura 79,6 % |
| `data/memoria/rag_embeddings.npy` | Matriz de vectores (150 × 384) |
| `scripts/banco_preguntas.py` | Banco de 20 preguntas, con `--metodo` y `--salida` |
| `scripts/comparar_rag.py` | Comparación de los dos métodos y análisis de truncamiento |
| `data/memoria/resultados_banco_tfidf.json` | Resultado del banco con TF-IDF |
| `data/memoria/resultados_banco_embeddings.json` | Resultado del banco con Granite |
| `data/memoria/comparacion_rag.json` | Todas las cifras citadas aquí |
| `data/memoria/comparacion_rag_minilm.json` | Evidencia del intento con MiniLM (§5) |

Reproducción completa:

```bash
python -m memoria indexar --metodo embeddings
python scripts/banco_preguntas.py --metodo tfidf \
     --salida data/memoria/resultados_banco_tfidf.json
python scripts/banco_preguntas.py --metodo embeddings \
     --salida data/memoria/resultados_banco_embeddings.json
python scripts/comparar_rag.py
python src/generar_comparacion_tfidf_embeddings.py
```

El modelo de embeddings **no se descarga**: se carga de la caché local de Hugging Face y el sistema fuerza el modo sin conexión, de modo que si no estuviera presente fallaría con un mensaje explícito en lugar de usar la red.

