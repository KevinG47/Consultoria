# Guía de defensa — Sistema de memoria del agente (10–15 min, individual)

> Material de estudio para sustentar. Todo lo que dice aquí **se ejecutó de verdad**
> sobre el repositorio. Rutas relativas a `documentacion_auditoria/`.

---

## 1. El RAG, paso a paso (cómo explicarlo sin sonar a definición)

### La idea en una frase
Es un **buscador interno** de todo lo que ya escribimos: antes de redactar algo nuevo,
le pregunto "¿ya dijimos algo de esto?" y me devuelve los fragmentos más parecidos con
un puntaje.

### Qué es TF-IDF (explícalo así)
Imagina que quieres saber de qué habla cada fragmento del documento. Una palabra sirve
para identificarlo si **aparece mucho en ese fragmento pero poco en el resto**:
- "investigadores" sale en casi todos → **no** distingue nada.
- "mojibake" o "convocatoria 894" salen en pocos → **sí** distinguen.

TF-IDF es exactamente eso: **TF** = cuántas veces aparece la palabra en el fragmento;
**IDF** = castigo por ser una palabra común en todo el corpus. El resultado es un
"peso" por palabra; el fragmento queda representado como una lista de pesos.

### Qué es la similitud coseno (explícalo así)
Cada fragmento es como una **flecha** en un espacio con una dimensión por palabra.
La consulta también es una flecha. Comparamos **el ángulo** entre ellas, no su largo:
- mismo ángulo (cos = 1) → hablan de lo mismo;
- ángulo recto (cos = 0) → no comparten nada.

Se usa coseno y no distancia normal porque los textos tienen largos distintos y así no
favorecemos a los fragmentos largos.

### Los 4 pasos reales del sistema
1. **Indexar** (`python -m memoria indexar`): parte el corpus en **145 fragmentos**
   (25 documentos: 6 criterios + sus LITE + maestro + 11 informes de validación + el
   anteproyecto), limpia el LaTeX, construye el vocabulario (**≈40 500 términos**) y
   calcula la matriz de pesos TF-IDF.
2. **Consultar**: la pregunta se limpia y se pesa **igual** que el corpus.
3. **Comparar**: se calcula el coseno contra **todos** los fragmentos y se ordenan.
4. **Devolver y registrar**: los mejores *k* con su puntaje, documento y sección; la
   consulta queda en la bitácora `data/memoria/consultas_rag.jsonl` (auditable).

### Por qué TF-IDF y no embeddings (responde la pregunta obvia)
Con 145 fragmentos y vocabulario técnico estable, TF-IDF resuelve sin proveedor externo,
sin red, sin costo, y es **determinista y explicable** (puedo mostrar qué términos
pesaron). **Pero el docente decidió migrar a embeddings** (decisión D007) por
transferibilidad; esa migración está **pendiente de implementación** y el sistema lo
declara y lo detecta (ver §4).

---

## 2. El grafo (memoria estructural)

### Qué son los nodos, concretamente en nuestro caso
Cosas reales del proyecto, contadas: **255 nodos**
- **6** Criterio (los 6 de la rúbrica)
- **13** Documento (los 6 completos + sus 6 LITE + el maestro)
- **19** TérminoGlosario
- **11** Capa arquitectónica (ingesta, transformación, modelo, análisis, orquestación…)
- **51** ArchivoCodigo (los 51 reales del repo auditado)
- **133** Commit y **11** Autor (del `git log` real)
- **11** DocumentoValidacion (informes de los agentes)

### Qué son las relaciones (**498 aristas**)
- `Criterio → Documento` (con la variante completo/LITE)
- `Documento → TérminoGlosario` (qué términos usa de verdad)
- `ArchivoCodigo → Capa` (según las reglas de `capas.yaml`)
- `Commit → Autor` y `Documento → Commit`
- `Criterio → DocumentoValidacion` (qué informe lo verifica)

### Cómo detecta inconsistencias
Las reglas **consultan el grafo** en lugar de leer archivos sueltos:
- Si un criterio no tiene documento LITE → **falta una arista** → R1 falla.
- Si un commit del `git log` real no existe como nodo → R5 falla (línea de tiempo desfasada).
- Si un archivo real del repo auditado no tiene la arista `documenta` desde el criterio de
  código → R6 falla (archivo sin documentar).
- Si un archivo no tiene arista hacia ninguna capa **por regla explícita** → R8 falla.
- Si hay dos decisiones "actuales" sobre el mismo tema → R15 falla (contradicción de diseño).

**Frase para la defensa:** *"El grafo convierte el proyecto en afirmaciones verificables:
cada regla es una pregunta del tipo '¿existe esta relación?'. Si falta, hay un
inconsistencia concreta y con ubicación."*

---

## 3. Las 16 reglas, una frase cada una

| # | Qué verifica |
|---|---|
| **R1** | Cada uno de los 6 criterios tiene documento completo **y** versión LITE |
| **R2** | Todo documento completo tiene conclusiones registradas (en YAML y en su sección 05) |
| **R3** | Todo LITE tiene veredicto declarado y su sección de cierre con contenido |
| **R4** | Todo término del glosario se usa realmente en algún documento (nada de términos muertos) |
| **R5** | La línea de tiempo documentada coincide con el `git log` real del repo auditado (133 = 133, hash por hash) |
| **R6** | Todo archivo de código real (51) está referenciado en el documento del criterio de código |
| **R7** | El commit auditado documentado coincide con el HEAD real del clon (`1528939`) |
| **R8** | Todo archivo tiene capa asignada por una **regla explícita** en `capas.yaml` (nada por defecto) |
| **R9** | La cobertura de fichas de análisis coincide con lo documentado y con lo real (51) |
| **R10** | Integridad del grafo: existen los PDF, los `main.tex` y no hay aristas rotas |
| **R11** | El índice RAG cubre todo el corpus declarado y responde consultas |
| **R12** | El LITE es ≤ 40 % de la sección principal del completo y no hay copias literales entre documentos |
| **R13** | El índice RAG está **al día** respecto a los documentos fuente (evita resultados obsoletos) |
| **R14** | No hay contradicciones **numéricas** entre documentos (reutiliza `verificar_consistencia.py`) |
| **R15** | Las decisiones **superadas** no siguen en el código ni se presentan como vigentes: el código debe reflejar la decisión actual |
| **R16** | Los registros de trazabilidad están íntegros y **sin URLs "PENDIENTE"** |

**Cómo se ejecutan:** como **puerta previa a la compilación** (`compilar.py`): si alguna
falla, la compilación del PDF final se **aborta** (exit 2). `--forzar` continúa,
`--sin-validar` la desactiva.

---

## 4. Por qué R15 falla hoy (y cómo explicarlo en vivo)

**Resultado real:** 16 reglas → **14 PASA · 1 FALLA · 1 ADVERTENCIA**.

**La falla, textual:**
```
D002 está SUPERADA (D007) pero su implementación sigue en el código:
'TfidfVectorizer' en documentacion_auditoria/src/memoria/rag.py
```

**Explicación en términos simples (memorízala):**
> "Al principio decidimos usar TF-IDF para el buscador interno (decisión D002). Después
> el docente pidió migrar a *embeddings* por transferibilidad (decisión D007). La bitácora
> registra el cambio, pero **el código todavía usa TF-IDF**: eso es exactamente lo que R15
> detecta. No es un error escondido: es una **deuda técnica declarada** que el sistema
> reporta con archivo y nombre de variable. Se cierra de dos maneras: implementando la
> migración, o declarando una **excepción temporal auditada** (motivo, quién la autoriza y
> hasta cuándo), que degrada la falla a advertencia y deja el motivo por escrito."

**Por qué esto es una fortaleza, no una debilidad:** demuestra que el sistema no solo
"valida el pasado", sino que **mantiene la coherencia entre lo decidido y lo que se está
usando**. Es precisamente el requisito de trazabilidad que pedía el docente.

**La ADVERTENCIA (R12):** una sección de "relación entre criterios" es idéntica en el
documento completo y en su LITE. Es deliberado (el marco común) y está documentado; si se
quiere eliminar, basta redactar una versión propia para el LITE.

---

## 5. Demo en vivo (comandos exactos y qué debe verse)

Todo desde `documentacion_auditoria/src`:

```powershell
python -m memoria consultar "el consolidado versionado solo tiene 3 de 6 convocatorias" -k 2
```
**Debe verse** (salida real):
```
[RAG] consulta: 'el consolidado versionado solo tiene 3 de 6 convocatorias'  (índice: 145 fragmentos)
[RAG] términos que pesan: [('tiene convocatorias', 0.4687), ('versionado solo', 0.4274), ...]
  1. cos=0.3057  objetivo_2_lite::03_datos  [criterio_lite, 69 palabras]
     ...Veredicto: Datos correctos y suficientes en origen ... pero el consolidado
     versionado solo tiene 3 de 6 convocatorias (50.891 d...
  2. cos=0.2652  objetivo_2_lite::05_conclusiones  [criterio_lite, 93 palabras]
```
**Qué decir:** *"Recupera el antecedente exacto donde ya se había afirmado esto, con su
puntaje y su ruta: así evito contradecirme entre documentos."*

```powershell
python -m memoria grafo
```
**Debe verse:** `255 nodos / 498 aristas`, el desglose por tipo (Commit 133,
ArchivoCodigo 51…), `commits: reales=133 documentados=133`,
`archivos de código: reales=51 documentados=51`.

```powershell
python -m memoria validar
```
**Debe verse:** las 16 reglas con su estado y, al final,
`[memoria] reglas: 14 PASA, 1 FALLA, 1 ADVERTENCIA` (exit code 1 por la falla de R15).

```powershell
python -m memoria dibujar --tipos Criterio,Documento
```
**Debe verse:** `[dibujar] dibujados 19 nodos / 18 aristas de 255 nodos / 498 aristas
totales` y se genera `data/memoria/grafo_visual.png` (≈179 KB), legible para proyectar.

**Prueba de que la puerta es real (opcional, 30 s):** abre
`data/memoria/decisiones.yaml`, borra el `lite_veredicto` del criterio 1 en
`data/objetivos.yaml`, corre `python ../../src/compilar.py` (desde `documentacion_auditoria`):
verás que **aborta con exit 2** nombrando la regla y el archivo. Luego restaura el valor.

---

## 6. Preguntas que pueden caer y respuestas cortas

- **¿Por qué no usaron Neo4j?** Con 255 nodos y consultas simples, un grafo en memoria
  (networkx) cubre todo; un motor externo añadiría infraestructura y operación sin beneficio.
- **¿Cómo saben que la IA no inventó referencias?** Hay un registro de fuentes externas
  (`fuentes_externas.yaml`) con URL verificada, y R16 falla si queda alguna "PENDIENTE";
  además corregimos errores reales detectados (revista y DOI de Cañibano & Bozeman,
  DOI oficial de Wang & Barabási).
- **¿Qué pasa si cambia un documento y no reindexan?** R13 lo detecta: avisa que el índice
  es más antiguo que la fuente. (Ese error lo cometimos y por eso creamos la regla.)
- **¿El sistema reemplaza la revisión humana?** No. Detecta inconsistencias verificables;
  la decisión y la defensa son humanas.
