# Informe 1 · Ingesta y construcción de datos

**Proyecto:** Consultoría estadística USTA 2026-II — Observatorio Minciencias
**Componente:** Fase 3 · modelo predictivo de movilidad de categoría
**Entregable:** base analítica reproducible (fuentes → transiciones → features)
**Fecha:** 27 de octubre de 2026
**Autor:** Consultoría estadística USTA 2026-II

---

## 1. Objetivo de la etapa

Reconstruir, desde las fuentes abiertas y sin depender de archivos intermedios del
repositorio auditado, la base analítica sobre la que se entrena el modelo de
movilidad de categoría. La etapa persigue cuatro resultados concretos:

1. **Descargar el universo de producción científica** publicado por Minciencias en
   datos.gov.co (conjunto `33dq-ab5a`), completo y sin pérdida de filas.
2. **Dejar evidencia criptográfica de la descarga** —hash SHA-256, tamaño, número
   de páginas y manifiesto JSON— para que cualquier cifra posterior sea
   reproducible y auditable.
3. **Construir el panel persona × convocatoria** (padrón `bqtm-4y2h`) y derivar de
   él las **transiciones contiguas** entre convocatorias consecutivas: **43 187
   transiciones de 18 116 personas** en seis cohortes (2013, 2014, 2015, 2017,
   2019, 2021).
4. **Validar la integridad y la ausencia de fuga por construcción** antes de
   entrenar: nulos, duplicados, continuidad del *gap*, coherencia del `split` con
   la cohorte de destino y coincidencia de las features con la fila correcta de la
   tabla de etiquetas.

La etapa no busca todavía describir el fenómeno ni modelarlo; busca que el insumo
del modelado sea **exacto, trazable y repetible**. Todo lo que se reporta en los
informes 2 a 5 descansa sobre esta base.

---

## 2. Metodología y herramientas usadas

### 2.1 Fuentes de datos

| Fuente | Identificador Socrata | Unidad de observación | Volumen verificado |
|---|---|---|---|
| Padrón de investigadores reconocidos | `bqtm-4y2h` | Persona × convocatoria | **77 237 registros**, 30 086 personas únicas, 30 variables |
| Producción de grupos de investigación | `33dq-ab5a` | Producto × autor | **3 166 629 filas producto-autor**, 77 401 autores únicos |

La llave de cruce es `id_persona_pr` (padrón) ↔ `id_persona_pd` (producción), y el
periodo cubierto son seis convocatorias: 2013, 2014, 2015, 2017, 2019 y 2021. El
mapa de identificadores a años está fijado en `contrato_produccion.json`:
`16→2013, 17→2014, 18→2015, 19→2017, 20→2019, 21→2021`.

El padrón se trabajó desde el consolidado versionado del proyecto
(`01_datos/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv`,
SHA-256 `9a55dd87f5f571b1b82a834372f2f037c521ae4f02536f164d427d1c16ca9565`). La
producción, por su tamaño (≈1,3 GB), **no se versiona**: se descarga a un
directorio externo (`C:\datos_externos\minciencias\33dq-ab5a\`) y se deja
referenciada por hash.

### 2.2 Descarga paginada

La descarga se implementó en `07_modelo/ingesta/descargar_produccion.py` con la
misma consulta que usó el repositorio auditado, para que los conteos sean
comparables:

```
GET https://www.datos.gov.co/resource/33dq-ab5a.csv
    ?$limit=50000&$offset=N&$order=:id
```

Características del procedimiento:

- **Paginación determinista** de 50 000 filas con orden por `:id`, hasta que una
  página llega vacía o con menos de 50 000 registros.
- **Escritura en streaming a disco**: las páginas nunca se acumulan en memoria.
- **Checkpoint por offset** en un JSON junto al CSV: si la descarga se interrumpe,
  se reanuda desde la última página confirmada (códigos de salida 2 y 130).
- **Reintentos con retroceso exponencial** ante errores de red recuperables.
- **Detección de respuestas inválidas**: si la API devuelve HTML/JSON en lugar de
  CSV, la página se rechaza y no se cuenta.
- **SHA-256 calculado mientras se escribe** y verificado al final releyendo el
  archivo; si el hash no coincide, el proceso termina con código 3.
- **Manifiesto JSON** con URL, fecha UTC, bytes, filas, hash, número de páginas,
  tamaño de página, hash del script y bandera de token.
- **Token opcional** (`SOCRATA_APP_TOKEN`) que nunca se escribe en el manifiesto;
  la descarga se completó **sin token**.

Resultado de la corrida (25-10-2026, 19:32 UTC):

| Campo | Valor |
|---|---|
| Páginas | **64** |
| Tamaño de página | 50 000 |
| Filas | **3 166 629** |
| Bytes | **1 352 074 732** (≈1,26 GiB) |
| SHA-256 | `99a66ae6ff2d60fb4dcde16d044464cf2bd43690fa05d3af90c5120a336d6aaa` |
| Token usado | No |

### 2.3 Contrato de validación de la descarga

Antes de construir agregados, la descarga se contrasta contra un **contrato con
tolerancia cero** (`07_modelo/ingesta/contrato_produccion.json`): 12 comprobaciones
de conteo (C01–C12), una comprobación adicional de personas reconocidas con
producción por año (A01) y cinco comprobaciones estructurales (E01–E05). Si
cualquiera falla, el pipeline se detiene y no se construyen ni los agregados por
persona ni el dataset de modelo.

Las comprobaciones cubren:

- **Totales y desagregados por año**: 3 166 629 filas en total; 238 407 (2013),
  342 160 (2014), 376 653 (2015), 536 648 (2017), 762 719 (2019), 910 042 (2021).
- **Cobertura**: 77 401 autores únicos; 28 590 reconocidos con producción y 1 496
  sin producción.
- **Estructura**: `id_persona_pd` de 10 dígitos numéricos, cero nulos en las
  llaves, cero años indeterminables o fuera del conjunto permitido.
- **Integridad**: el SHA-256 y los bytes del archivo deben coincidir con el
  manifiesto de descarga (E05).

### 2.4 Construcción del panel y de las transiciones

1. **Tabla de etiquetas** (`target.parquet`): 77 237 filas (persona ×
   convocatoria) × 9 columnas, SHA-256
   `663c89ef577de75b145d5ddb70bdb1b89447e8ce659dc4661bce37449555b87a`.
2. **Transiciones contiguas**: se conservan solo los pares de convocatorias
   consecutivas (`gap == 1`), es decir, 16→17, 17→18, 18→19, 19→20 y 20→21. El
   resultado son **43 187 transiciones de 18 116 personas**. Se descartó la
   variante de ventana completa (47 151 filas, con saltos) porque mezcla pares no
   consecutivos y rompe la lectura de «siguiente convocatoria».
3. **Etiqueta**: la categoría de destino se clasifica en `baja`, `se_mantiene` o
   `sube` respecto de la categoría de origen.
4. **Split temporal por cohorte de destino**, fijado antes de mirar métricas:
   - `train`: destinos **17, 18 y 19** → 19 838 filas;
   - `val`: destino **20** → 9 994 filas;
   - `test`: destino **21** → 13 355 filas, evaluado **una sola vez**.
5. **Features**: 172 variables de producción construidas con la ventana de
   observación previa (volumen, clase de producto, tipología y categoría/calidad).
   El parquet resultante tiene **285 columnas** (9 de metadatos + 172 features
   usadas + columnas auxiliares que el modelo no consume).

### 2.5 Validación del dataset

`07_modelo/modelado/validar_dataset.py` ejecuta nueve comprobaciones (V01–V09)
sobre los cinco parquet derivados:

| ID | Qué verifica |
|---|---|
| V01 | Filas de los `_contiguo` = 43 187 y de los `_completo` = 47 151 |
| V02 | Las matrices 2019→2021 y 2017→2019 coinciden con las del repositorio auditado |
| V03 | Cero nulos en `(ID_PERSONA_PR, ID_CONVOCATORIA)` |
| V04 | Cero duplicados en `(ID_PERSONA_PR, ID_CONVOCATORIA)` |
| V05 | Los 77 237 pares del censo están en `target.parquet` |
| V06 | **Anti-fuga**: las features corresponden a la fila de la misma convocatoria; `target_class` y `split` se recomponen desde el censo y coinciden |
| V07 | En los `_contiguo`, todas las filas tienen `gap == 1` |
| V08 | El `split` coincide con la cohorte de destino (17/18/19 → train; 20 → val; 21 → test) |
| V09 | Cero filas con `gap > 1` en los `_contiguo` |

V06 es la comprobación crítica: reconstruye la etiqueta y el `split` desde el
censo original y exige coincidencia exacta con el parquet, de modo que no pueda
haber una feature calculada con la convocatoria equivocada ni una etiqueta
desplazada.

### 2.6 Herramientas

| Herramienta | Uso en la etapa |
|---|---|
| **Python 3.11.9** | Lenguaje del pipeline |
| **pandas 3.1.0 / numpy 2.4.6 / pyarrow** | Construcción y validación de parquet |
| **urllib.request** (biblioteca estándar) | Cliente HTTP de la API Socrata |
| **hashlib / csv / json** | Hash en streaming, conteo de filas, manifiestos |
| **PowerShell** | Orquestación y verificación de archivos |

Se usó `urllib` en lugar de un cliente Socrata de terceros (`sodapy`, que sí usó
el repositorio auditado) para controlar explícitamente la paginación, el
checkpoint y el hash, y para no añadir dependencias a un paso que debe poder
repetirse años después.

---

## 3. Justificación técnica

### 3.1 Por qué la API paginada y no una descarga directa

Una descarga directa del recurso (`/resource/33dq-ab5a.csv` sin `$limit`/
`$offset`) habría sido más corta de escribir, pero inadecuada para este dataset
por cinco razones:

1. **Tamaño y reanudación.** El archivo final pesa **1 352 074 732 bytes** (≈1,26
   GiB) y tiene **3 166 629 filas**. Una sola respuesta no ofrece punto de
   reanudación ni control por página: un corte a mitad de la descarga obliga a
   empezar de nuevo, y el conteo solo se conoce al final. La paginación escribe
   cada página directamente a disco y verifica el número de filas de cada bloque.
2. **Reanudación.** Con 64 páginas, un corte en la página 60 no obliga a repetir
   la descarga: el checkpoint por `offset` reanuda desde la última página
   confirmada. Una descarga de un solo flujo no ofrece ese punto de retorno.
3. **Determinismo.** `$order=:id` con `$limit`/`$offset` produce páginas estables
   y reproducibles; sin orden explícito, el conjunto de filas de una página puede
   cambiar entre llamadas y duplicar o perder registros.
4. **Detección de errores.** La API puede responder con una página HTML de error
   o un JSON en vez de CSV. El script valida el inicio del archivo y rechaza la
   página; en una descarga directa ese error se confundiría con el final del
   archivo.
5. **Comparabilidad con el auditado.** El repositorio auditado usó exactamente
   esta consulta (`$limit=50000`, `$order=:id`), de modo que los conteos por
   convocatoria del contrato (C01–C12) son directamente contrastables. Cambiar el
   método habría roto la comparación con la evidencia previa.

La referencia técnica es la documentación oficial de la interfaz **SODA** de
Socrata, que define `$limit`, `$offset`, `$order` y `$where` como parámetros del
endpoint y documenta los límites de paginación y de tasa
[Socrata, *SODA API documentation*]. La decisión de paginar en bloques de 50 000
filas, con checkpoint y reintentos, es además **práctica estándar de la industria**
para descargas de datasets abiertos de gran volumen.

### 3.2 Por qué no se usó el consolidado versionado del auditado

El repositorio auditado conservaba un consolidado en `datos/tarea_join/` con
**50 891 filas y solo tres convocatorias** (2017, 2019, 2021), frente a las
**77 237 filas y seis convocatorias** declaradas en el catálogo. Ese consolidado
solo permitía construir **dos transiciones** (2017→2019 y 2019→2021), no las cinco
contiguas, ni reproducir los resultados del informe original. La descarga completa
era, por tanto, un requisito de validez, no una preferencia.

### 3.3 Por qué un contrato con tolerancia cero

La auditoría había documentado diferencias entre lo declarado y lo versionado. En
lugar de aceptar un margen, la ingesta exige **coincidencia exacta** con los
conteos de referencia: si una sola comprobación falla, el pipeline se detiene. El
costo es que cualquier cambio legítimo en la fuente obliga a actualizar el
contrato de forma explícita; el beneficio es que ninguna cifra posterior puede
arrastrar silenciosamente una fila perdida o un año mal mapeado.

---

## 4. Resultados y métricas

### 4.1 Descarga

| Métrica | Valor |
|---|---|
| Filas descargadas | **3 166 629** |
| Coincidencia con C01 (esperado) | Exacta (tolerancia 0) |
| Páginas | 64 × 50 000 |
| Bytes | 1 352 074 732 |
| SHA-256 | `99a66ae6ff2d60fb4dcde16d044464cf2bd43690fa05d3af90c5120a336d6aaa` |
| Verificación del hash | Relectura completa del archivo: coincide |
| Descarga parcial | No |

### 4.2 Distribución por convocatoria

| Convocatoria | Año | Filas | Personas reconocidas en el censo | Con producción |
|---|---|---:|---:|---:|
| 16 | 2013 | 238 407 | 8 016 | 6 784 |
| 17 | 2014 | 342 160 | 8 280 | 7 586 |
| 18 | 2015 | 376 653 | 10 050 | 9 219 |
| 19 | 2017 | 536 648 | 13 001 | 12 149 |
| 20 | 2019 | 762 719 | 16 796 | 15 872 |
| 21 | 2021 | 910 042 | 21 094 | 19 937 |
| **Total** | | **3 166 629** | **77 237** | **—** |

La suma de las seis filas por año reproduce exactamente el total (3 166 629), lo
que descarta páginas duplicadas o faltantes.

### 4.3 Dataset de modelo

| Elemento | Valor |
|---|---|
| Transiciones contiguas | **43 187** |
| Personas únicas | **18 116** |
| Columnas del parquet | 285 |
| Features usadas por el modelo | 172 |
| `train` (destinos 17–19) | 19 838 filas |
| `val` (destino 20) | 9 994 filas |
| `test` (destino 21) | 13 355 filas |
| SHA-256 del parquet | `97289128afd5d87e6c60daa85ae85f8a48fef30cb539a98622c31f45025d3376` |

### 4.4 Validaciones

| Comprobación | Resultado |
|---|---|
| V01 filas contiguo = 43 187 | **OK** |
| V02 matrices 2019→2021 y 2017→2019 | **OK** (2 336/9 657/1 362 y 2 246/7 018/730) |
| V03 nulos en llaves | **0** en los cinco parquet |
| V04 duplicados en llaves | **0** en los cinco parquet |
| V05 censo completo en target | **OK** (77 237 pares) |
| V06 anti-fuga | **0** discrepancias en clase, `split` y recomposición |
| V07 `gap == 1` | **0** filas con otro `gap` |
| V08 `split` por cohorte de destino | **0** discrepancias |
| V09 `gap > 1` en contiguo | **0** filas |
| Veredicto global | **OK** (`validacion_dataset_20261025_202417.json`) |

### 4.5 Lectura

La base queda construida con tres garantías verificables: **cobertura completa**
(3 166 629 filas, suma por año exacta), **integridad criptográfica** (hash
calculado en escritura y relectura) y **coherencia interna** (nueve validaciones,
incluida la anti-fuga). Sobre esta base se puede afirmar que cualquier métrica de
los informes siguientes corresponde a las filas y etiquetas que dice corresponder.
El límite de la etapa no es de calidad sino de **alcance**: el dataset modela
transiciones entre convocatorias consecutivas y solo incluye variables de
producción; no incorpora financiación, movilidad ni coautoría real, ausencias que
se documentan en el informe 2 y que condicionan el techo del modelo.

---

## 5. Referencias

**Fuente técnica de la API**

1. **Socrata.** *SODA API documentation.* https://dev.socrata.com/ — documentación
   oficial de la interfaz utilizada (`$limit`, `$offset`, `$order`, `$where`).
   Se cita como referencia técnica de la plataforma, no como fuente académica
   revisada por pares.
2. **Ministerio de Ciencia, Tecnología e Innovación.** *Producción de grupos de
   investigación* [conjunto de datos]. datos.gov.co.
   https://www.datos.gov.co/resource/33dq-ab5a.csv

**Evidencia interna del proyecto**

3. `07_modelo/ingesta/descargar_produccion.py` — script de descarga paginada.
4. `07_modelo/ingesta/contrato_produccion.json` — contrato C01–C12, A01 y
   E01–E05.
5. `07_modelo/ingesta/manifiestos/produccion_20261025_193218.json` — manifiesto
   de la descarga (hash, bytes, páginas).
6. `07_modelo/ingesta/manifiestos/dataset_20261025_202401.json` — manifiesto del
   dataset (43 187 filas, hashes de censo y target).
7. `07_modelo/ingesta/manifiestos/validacion_dataset_20261025_202417.json` —
   resultado V01–V09.
8. `07_modelo/modelado/validar_dataset.py` — implementación de V01–V09.
