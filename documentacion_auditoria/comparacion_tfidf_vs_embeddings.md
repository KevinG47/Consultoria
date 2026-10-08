# Comparación: TF-IDF vs embeddings para el RAG del proyecto

**Auditoría estadística del sistema de reconocimiento de MinCiencias — sistema de memoria del agente**  
Documento generado por `documentacion_auditoria/src/generar_comparacion_tfidf_embeddings.py` a partir de `data/memoria/comparacion_rag.json` y de los dos resultados del banco de preguntas. Fecha: 2026-10-08.

## Resumen en una página

El RAG del proyecto sabe recuperar con **dos métodos intercambiables**: TF-IDF (el de siempre) y embeddings locales (el nuevo). Se evaluaron los dos con el mismo banco de 20 preguntas sobre el mismo corpus de 150 fragmentos.

| Métrica | TF-IDF | Embeddings | Ganador |
|---|---:|---:|---|
| Respuesta esperada en el **top-1** | 9/20 | 10/20 | embeddings (+1) |
| Respuesta esperada en el **top-3** | 11/20 | 10/20 | TF-IDF (+1) |
| Ranking promedio del dato correcto (de 150) | 8,42 | 26,63 | TF-IDF (3,2× mejor) |
| Preguntas ganadas | 6 | 6 | empate técnico (8 empates) |

**Conclusión: la migración, tal como está implementada, NO mejora el sistema.** El balance es de un acierto más en el top-1, un acierto menos en el top-3 y un ranking promedio 3,2 veces peor. La causa está medida: el modelo trunca cada fragmento a 128 tokens y los fragmentos promedian 1 634,7 tokens, de modo que solo se vectoriza el **7,8 %** del contenido de cada fragmento. TF-IDF, al ser una bolsa de palabras, ve el fragmento completo. La recomendación es **mantener TF-IDF como método por defecto** y dejar los embeddings disponibles como método complementario, con el troceado de fragmentos como siguiente paso (ver §6).

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

Además, para un vocabulario técnico y estable —cifras, rutas de archivo, identificadores como `n_atipicos_edad`— coincidir en la palabra exacta es justo lo que se necesita.

**Límites.** No entiende sinónimos ni paráfrasis: si el documento dice «investigadores únicos» y la pregunta dice «personas distintas», TF-IDF no ve ninguna relación, porque no comparten ni una palabra. Tampoco entiende el significado: dos frases con las mismas palabras en distinto orden le resultan idénticas.

## 2. Qué es un embedding, en lenguaje llano

Un *embedding* es una forma de convertir un texto en una lista de números —un vector— de manera que **textos con significado parecido queden cerca** en ese espacio numérico. En lugar de contar palabras, se usa un modelo entrenado con millones de frases para aprender qué textos suelen significar lo mismo.

En este proyecto el vector tiene 384 números por fragmento, producidos por el modelo local `paraphrase-multilingual-MiniLM-L12-v2`. La comparación es la misma que en TF-IDF: similitud coseno sobre vectores normalizados.

**Ventajas.** Entiende sinónimos, paráfrasis y conceptos que no comparten ni una palabra. Si la pregunta dice «¿cuántos investigadores hay registrados?» y el documento dice «total de personas únicas en el padrón», un embedding puede relacionarlos y TF-IDF no. Además es **multilingüe**: la misma frase en español e inglés cae cerca.

**Límites.** Requiere un modelo: aquí son ~120 MB de pesos más la librería `torch`, así que el sistema pesa mucho más y tarda más en arrancar (cargar el modelo cuesta unos 20 segundos). Además el modelo **tiene un límite de longitud**: solo mira los primeros tokens de cada texto, y todo lo que venga después se descarta sin avisar. Y se pierde la explicabilidad: no hay un «término que pesa» que se pueda mostrar, solo un número de similitud.

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

La implementación adoptada satisface el motivo del docente —no depender de un diccionario construido a medida, sino de un modelo estándar que cualquiera puede cargar— sin salir de la máquina. La decisión quedó corregida en `decisiones.yaml` conservando la redacción original en un campo aparte, para que el cambio quede trazado. Lo que se midió al implementarla se ve en §5.

## 5. Resultados de la comparación

### 5.1 Cómo se comparó

El mismo banco de 20 preguntas, el mismo corpus (150 fragmentos de 25 documentos), los dos índices construidos por separado. Por pregunta se comparó: el puntaje del top-1, si la respuesta esperada está en el top-1 y en el top-3, y la posición del fragmento correcto en el ranking completo. El criterio para decidir quién gana en cada pregunta es un orden lexicográfico: primero el acierto en top-1, después el acierto en top-3 y, si empatan, la mejor posición del dato correcto.

### 5.2 Tabla por pregunta

| Q | Grupo | Score top-1 TF-IDF | Score top-1 emb. | Top-1 TF-IDF | Top-1 emb. | Top-3 TF-IDF | Top-3 emb. | Rank TF-IDF | Rank emb. | Gana |
|---|---|---:|---:|:--:|:--:|:--:|:--:|---:|---:|---|
| 1 | A | 0,0505 | 0,6556 | sí | sí | sí | sí | 1 | 1 | empate |
| 2 | A | 0,0462 | 0,6231 | sí | sí | sí | sí | 1 | 1 | empate |
| 3 | A | 0,1074 | 0,7177 | sí | sí | sí | sí | 1 | 1 | empate |
| 4 | A | 0,0822 | 0,6363 | no | no | no | no | 5 | 4 | embeddings |
| 5 | A | 0,1054 | 0,5010 | no | no | no | no | 9 | 5 | embeddings |
| 6 | A | 0,1105 | 0,6330 | no | sí | no | sí | 8 | 1 | embeddings |
| 7 | A | 0,1091 | 0,5256 | no | sí | sí | sí | 2 | 1 | embeddings |
| 8 | A | 0,0409 | 0,4960 | no | no | sí | no | 2 | 118 | tfidf |
| 9 | A | 0,0526 | 0,3902 | sí | no | sí | no | 1 | 128 | tfidf |
| 10 | A | 0,0500 | 0,6955 | no | no | no | no | 19 | 107 | tfidf |
| 11 | B | 0,0456 | 0,5613 | no | sí | no | sí | 4 | 1 | embeddings |
| 12 | B | 0,0529 | 0,6523 | sí | sí | sí | sí | 1 | 1 | empate |
| 13 | A | 0,0984 | 0,5339 | no | no | no | no | 16 | 23 | tfidf |
| 14 | B | 0,0529 | 0,5664 | no | no | no | no | — | — | empate |
| 15 | B | 0,0652 | 0,5968 | no | no | no | no | 82 | 4 | embeddings |
| 16 | C | 0,1051 | 0,4849 | sí | sí | sí | sí | 1 | 1 | empate |
| 17 | C | 0,0732 | 0,6220 | sí | no | sí | no | 1 | 95 | tfidf |
| 18 | A | 0,0651 | 0,5941 | sí | sí | sí | sí | 1 | 1 | empate |
| 19 | C | 0,0546 | 0,5394 | sí | sí | sí | sí | 1 | 1 | empate |
| 20 | C | 0,2047 | 0,5606 | no | no | no | no | 4 | 12 | tfidf |

### 5.3 Agregados

| Métrica | TF-IDF | Embeddings |
|---|---:|---:|
| Respuesta en el top-1 | **9/20** | **10/20** |
| Respuesta en el top-3 | **11/20** | **10/20** |
| Respuesta presente en el corpus | 19/20 | 19/20 |
| Score promedio del top-1 | 0,0786 | 0,5793 |
| Ranking promedio del dato correcto | **8,42** | **26,63** |
| Preguntas ganadas | 6 | 6 (+8 empates) |

Por grupos del banco (A = datos que deberían estar en el corpus, B = datos que no, C = datos del propio sistema):

| Grupo | n | Top-1 TF-IDF | Top-1 emb. | Top-3 TF-IDF | Top-3 emb. |
|---|---:|---:|---:|---:|---:|
| A | 12 | 5 | 6 | 7 | 6 |
| B | 4 | 1 | 2 | 1 | 2 |
| C | 4 | 3 | 2 | 3 | 2 |

### 5.4 En qué casos gana cada método

- **Embeddings encuentra y TF-IDF no, en el top-1** (Q6, Q7, Q11): son preguntas redactadas con otras palabras que el documento («¿cuántas referencias tiene el estado del arte?», «¿cuántos commits tiene el repo auditado?»). Aquí el embedding hace exactamente lo que promete: relaciona significado sin compartir vocabulario.
- **TF-IDF encuentra y embeddings no, en el top-1** (Q9, Q17): son preguntas cuyo dato es una cifra o un identificador exacto («¿cuántos nodos tiene el grafo?» → 255; «¿cuántos informes de validación cubre el corpus?» → once). La coincidencia literal es imbatible para una bolsa de palabras.
- **Top-3**: embeddings gana en Q6, Q11 y TF-IDF en Q8, Q9, Q17.
- En 8 preguntas los dos métodos empatan, y en 19 de las 20 el dato está en el corpus de todos modos.

### 5.5 La causa medida: el modelo solo ve el 7,8 % de cada fragmento

La diferencia de ranking no es una opinión ni una impresión: tiene una causa medible.

| Medida | Valor |
|---|---:|
| Longitud máxima que procesa el modelo | **128 tokens** |
| Tokens por fragmento (promedio) | 1 634,7 |
| Tokens por fragmento (mediana) | 497 |
| Tokens del fragmento más largo | 65 127 |
| Fragmentos que superan el máximo | **143 de 150 (95,3 %)** |
| Contenido realmente vectorizado | **7,8 %** |

El modelo `paraphrase-multilingual-MiniLM-L12-v2` está diseñado para frases, no para documentos: mira como mucho 128 tokens y descarta el resto sin avisar. Nuestros fragmentos nacen de secciones completas de LaTeX —el mayor, `objetivo_3::03_codigo`, tiene 65 127 tokens— de modo que **143 de 150 fragmentos (95,3 %)** se vectorizan solo por su encabezado. Cuando la respuesta está al principio del fragmento, el embedding la encuentra; cuando está a mitad o al final, es invisible para él, mientras que TF-IDF la ve porque cuenta palabras en todo el texto.

Esto explica las dos observaciones que de otro modo parecerían contradictorias: el top-1 mejora ligeramente (el encabezado de un fragmento suele decir de qué trata) pero el ranking promedio empeora mucho, porque el dato concreto casi nunca está en el encabezado.

### 5.6 Dos comprobaciones de honestidad

1. **TF-IDF no se rompió.** La corrida nueva de TF-IDF es **idéntica** a la corrida histórica (resultados_banco_preguntas.json, del 2026-10-01T17:25:51) en las 20 preguntas: mismos puntajes, mismos rankings, mismos aciertos. Añadir el segundo método no cambió el comportamiento del primero.
2. **Los puntajes no son comparables entre métodos.** El promedio del top-1 es 0,0786 con TF-IDF y 0,5793 con embeddings, pero eso **no** significa que los embeddings sean siete veces mejores. Los cosenos de un modelo de frases parten de una base mucho más alta: con embeddings las 20 preguntas caen en la banda «alta» del banco (>0,15) y con TF-IDF solo 1. Los umbrales de banda se calibraron sobre TF-IDF y no sirven para comparar métodos; lo que sí es comparable es *en qué posición* aparece el dato correcto.

### 5.7 Un punto a favor de los embeddings que no se ve en el banco

Al cargar el índice de TF-IDF aparece esta advertencia, reproducible en esta máquina:

```
InconsistentVersionWarning: Trying to unpickle estimator TfidfVectorizer
from version 1.9.0 when using version 1.9.1.
```

Es decir: **el índice de TF-IDF queda atado a la versión de scikit-learn con la que se construyó**, y una actualización de la librería puede invalidarlo. Esto le da la razón al motivo del docente: un modelo de embeddings es un artefacto estándar y portable, mientras que el «diccionario» de TF-IDF es un archivo serializado dependiente del entorno. Es un argumento de reproducibilidad, no de calidad de recuperación, y conviene no confundirlos.

## 6. Decisión final y siguiente paso

**No se adopta embeddings como método principal todavía.** El sistema queda con los dos métodos disponibles y **TF-IDF como predeterminado**:

```bash
python -m memoria consultar "..." -k 2                        # TF-IDF (por defecto)
python -m memoria consultar "..." -k 2 --metodo embeddings    # embeddings locales
python -m memoria indexar --metodo embeddings                 # reindexar con embeddings
```

El motivo de mantener los dos, y no sustituir uno por otro, es que ganan en casos distintos y complementarios: TF-IDF es mejor cuando la pregunta busca una cifra o un identificador exacto y cuando el dato está en cualquier punto del fragmento; los embeddings son mejores cuando la pregunta está parafraseada. Quedarse con uno solo perdería la mitad de los casos.

**El siguiente paso, si se quiere que los embeddings rindan, es trocear los fragmentos.** El problema no es el modelo sino el tamaño de la entrada: hoy 143 de 150 fragmentos exceden el máximo y solo se vectoriza el 7,8 % del texto. Partir cada fragmento en trozos de unas 128 unidades (con solape para no cortar ideas a la mitad) haría que el modelo viera todo el contenido.

Ese cambio **no es inocuo y por eso no se hizo**: el corpus pasaría de 150 fragmentos a varios cientos, y la cifra «150 fragmentos» está citada en la documentación y vigilada por la regla R17, además de que R11 exige que el índice cubra exactamente el corpus declarado. Hacerlo obliga a actualizar esas cifras en todos los documentos y a reindexar ambos métodos. Queda como propuesta, no como hecho consumado.

### Estado de la decisión D007

D007 quedó actualizada en `data/memoria/decisiones.yaml` a estado `vigente`, con la redacción corregida (embeddings **locales**, no «vía API key») y con el resultado de esta evaluación en su justificación. Se documenta además un efecto colateral en las reglas: **R15 seguirá fallando**, y conviene entender por qué.

R15 hace dos comprobaciones simétricas: (a) que la decisión vigente esté implementada en el código, y (b) que una decisión **superada** no siga implementada. La primera ya se cumple —`embedding` aparece en `rag.py`—, pero la segunda sigue disparando porque D002 está marcada como `superada` y su marcador `TfidfVectorizer` continúa en el código. Y continuará mientras TF-IDF siga existiendo como respaldo, que es justamente lo que se decidió conservar. Dicho de otro modo: la regla supone que una técnica sucede y elimina a la anterior, y aquí la decisión real es «sucede como método principal, se conserva como respaldo». Ajustar eso exige tocar la regla o el estado de D002, y ninguna de las dos cosas se hizo sin consultar.

## Anexo: trazabilidad y reproducibilidad

| Artefacto | Contenido |
|---|---|
| `src/memoria/rag.py` | Los dos métodos (`metodo="tfidf"` por defecto) |
| `data/memoria/rag_indice.json` | Índice TF-IDF (metadatos), sin cambios: 150 fragmentos |
| `data/memoria/rag_indice_embeddings.json` | Índice de embeddings: 150 fragmentos, 384 dimensiones |
| `scripts/banco_preguntas.py` | Banco de 20 preguntas, con `--metodo` y `--salida` |
| `scripts/comparar_rag.py` | Comparación de los dos métodos y análisis de truncamiento |
| `data/memoria/resultados_banco_tfidf.json` | Resultado del banco con TF-IDF |
| `data/memoria/resultados_banco_embeddings.json` | Resultado del banco con embeddings |
| `data/memoria/comparacion_rag.json` | Todas las cifras citadas aquí |

Reproducción completa:

```bash
python -m memoria indexar --metodo embeddings
python scripts/banco_preguntas.py --metodo tfidf \
     --salida data/memoria/resultados_banco_tfidf.json
python scripts/banco_preguntas.py --metodo embeddings \
     --salida data/memoria/resultados_banco_embeddings.json
python scripts/comparar_rag.py
```

El modelo de embeddings **no se descarga**: se carga de la caché local de Hugging Face y el sistema fuerza el modo sin conexión, de modo que si no estuviera presente fallaría con un mensaje explícito en lugar de usar la red.

