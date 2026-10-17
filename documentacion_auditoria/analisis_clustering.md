# Segmentación formalizada de perfiles (F2-6)

**Objetivo que cierra:** OE5 del repositorio auditado, en su parte de *clustering*
(el multivariado y el clustering eran, hasta ahora, R legacy no reproducible).
**Artefactos:** `documentacion_auditoria/src/clustering_formalizado.py` ·
`data/memoria/clustering.json` · `data/memoria/clusters_registros.csv` (77 237
filas) · `data/memoria/graficas_clusters/` (3 figuras).

## 1. Lo que hacía el auditado, y sus tres problemas

`notebooks/tarea_gran_tabla/analisis_de_clusters.R`:

```r
GT         <- read_excel("Downloads/GRAN_TABLA(SIN ID).xlsx")   # ruta del autor
GT_NA      <- cc(GT)                                            # casos completos
res.kproto <- kproto(GT_NA, k = 3)                              # k = 3 fijo
```

1. **La entrada no existe**: `Downloads/` es la carpeta del autor y la gran tabla no
   está versionada. El análisis no es reproducible ni con los datos del repositorio.
2. **`cc()` descarta el 8,4 % de la muestra** por lista, sin decir qué se va.
3. **`k = 3` se fija sin validación**: no hay silhouette, ni codo, ni contraste.

## 2. La reconstrucción

**Método: k-prototypes de Huang (1998)**, que es exactamente lo que hace `kproto()`:
distancia mixta `d = d_numérica + γ · d_categórica` (Euclídea al cuadrado en la edad
estandarizada más el número de discrepancias categóricas, ponderado por γ), con
prototipo numérico = media y categórico = moda, y cinco arranques aleatorios.

**Variables:** las seis categóricas que el informe del auditado interpretaba (gran
área, género, región de nacimiento, nivel de formación, categoría y región de
residencia) más la edad. Son 44 categorías dicotómicas más una numérica.

**Quedan fuera, y con razón:** `TXT_POBLACION_DISCA` (73,6 % de sus valores es
`No disponible` porque la variable **solo existe en 2021**, F2-5): incluirla
alinearía los clusters con la convocatoria y no con un perfil. Lo mismo para etnia y
víctima del conflicto. `ID_CONVOCATORIA` identifica el año, no un atributo.

**La pérdida de muestra es 0 %, no 8,4 %.** La fuente codifica los faltantes como
**categorías explícitas** (`No disponible`, `No registra`), no como celdas vacías: en
las variables de este análisis hay **un solo dato faltante de 540 659 celdas** (una
edad). Tratarlos como categoría es la decisión documentada del proyecto, así que el
clustering usa los **77 237 registros completos**. La única corrección aplicada es
que la edad se estandariza y ese único faltante va a la media, que es lo que hace
cualquier implementación de k-prototypes.

## 3. Elección de k: los criterios no se ponen de acuerdo, y eso ya dice algo

| k | Silhouette | Calinski–Harabasz | Davies–Bouldin | Pérdida de información |
|---:|---:|---:|---:|---:|
| **2** | **0,28 ± 0,06** | **6 938,2** | 3,1751 | 84,05 % |
| 3 | 0,18 | 5 487,8 | 3,2833 | 76,49 % |
| 4 | 0,12 | 4 502,4 | 3,3139 | 73,22 % |
| 5 | 0,11 | 3 839,5 | 3,5721 | 70,89 % |
| 6 | 0,11 | 3 600,3 | 3,0564 | 68,51 % |
| 7 | 0,02 | 3 317,0 | 3,0434 | 67,11 % |
| 8 | 0,11 | 3 247,0 | 2,9184 | 64,47 % |
| 9 | 0,11 | 3 016,5 | 2,8840 | 63,99 % |
| 10 | 0,01 | 2 837,7 | **2,8043** | 62,46 % |

Silhouette y Calinski–Harabasz eligen **k = 2**; Davies–Bouldin prefiere **k = 10**.
Que los tres no coincidan es la primera señal de que no hay una estructura clara que
perseguir. La silhouette cae en picado de 0,28 a 0,18 al pasar de 2 a 3 y luego se
queda entre 0,01 y 0,11 con un perfil de sierra: no hay un óptimo interno.

> **Por qué la silhouette va con ± 0,06 (y no con cuatro decimales).** La silhouette
> se estima sobre una **submuestra estratificada de 4 000 de las 77 237 filas** —la
> matriz de distancias completa no cabe en memoria—, elegida al azar. Con la **misma
> partición** (tamaños 40 192 / 37 045 e inercia intra 174 196,3, ambas deterministas
> y exactas) y ocho réplicas de esa submuestra, el valor cae entre **0,14 y 0,30**
> (media 0,26 · desviación **0,061**). Publicar 0,2825 como si fuera exacto sería
> prometer una precisión que la estimación no tiene; por eso se reporta 0,28 ± 0,06.

**Y ojo con el umbral:** 0,25 es el mínimo que Kaufman y Rousseeuw proponen para
hablar de estructura, y 0,28 está **a media desviación** de él. En dos de las ocho
réplicas de la submuestra la estimación cae **por debajo** de 0,25. Por tanto el
umbral **no decide nada aquí**; el que decide es el contraste de la sección
siguiente.

## 4. La prueba que decide: el nulo

Se destruye la asociación entre variables **permutando cada una por separado** (cada
variable conserva su distribución marginal; lo que se rompe es el vínculo entre
ellas) y se repite todo el procedimiento, con k = 2, sobre 10 000 filas:

| | Observado | Nulo (media) | IC 95 % del nulo | p |
|---|---:|---:|---|---:|
| Silhouette | 0,3520 | **0,3549** | [0,2657; 0,3923] | **0,762** |
| Calinski–Harabasz | 878,0 | **877,9** | — | **0,524** |

> **Dos «silhouette observada» que no son la misma, y conviene no confundirlas.**
> La de la sección 3 es **0,28 ± 0,06** y se estima sobre las 77 237 filas. La de esta
> tabla es **0,3520** y se estima sobre la **submuestra de 10 000 filas** con la que se
> corre el contraste, para que observado y nulo se midan exactamente igual. Son dos
> estimaciones del mismo hecho con dos tamaños de muestra distintos; la comparación
> válida es la de esta tabla, siempre dentro de la submuestra.

**La partición observada es indistinguible de la que produce un conjunto de
variables independientes.** Es más: la silhouette observada es ligeramente *menor*
que la media del nulo. Lo que k-prototypes encuentra no son grupos de investigadores
con perfiles distintos, sino la huella de las distribuciones marginales: si el 51 %
tiene doctorado, el 62 % es Junior y el 33 % reside en Distrito Capital, cualquier
partición en dos trozos «explica» aproximadamente lo mismo, tenga o no estructura
conjunta.

Complemento que apunta en la misma dirección: el **ARI entre la partición y cada
variable por separado** es ≈ 0 para todas (categoría 0,012; gran área 0,032;
convocatoria 0,001). Los clusters no reproducen ninguna variable ni combinación
identificable.

## 5. Entonces, ¿qué describen los dos grupos?

Describen **un gradiente**, no grupos: es la partición que k-prototypes hace de una
nube continua cortada por la edad y el nivel de formación.

| | Cluster 0 (n = 37 045) | Cluster 1 (n = 40 192) |
|---|---:|---:|
| Edad media | **37,06** | **52,01** |
| Edad mediana | 36,91 | 51,37 |
| Doctorado | 37,4 % | **63,9 %** |
| Maestría | **49,3 %** | 22,0 % |
| Investigador Junior | **69,3 %** | 54,5 % |
| Investigador Sénior | 7,7 % | **18,1 %** |
| Reside en Distrito Capital | 21,8 % | **43,8 %** |
| Reside en Eje Cafetero | **33,3 %** | 15,7 % |

La lectura es limpia —**un grupo más joven y con maestría, otro mayor y con
doctorado, más concentrado en Bogotá**— pero hay que decir con la misma claridad que
**esa separación no es una estructura latente**: es lo que se obtiene al cortar por
la mitad una población con un gradiente de edad y formación. Un corte donde se
quiera daría dos mitades parecidas.

**Aporte de cada variable a la partición** (V de Cramér):

| Variable | V de Cramér |
|---|---:|
| Nivel de formación | 0,303 |
| Región de residencia | 0,270 |
| Gran área | 0,266 |
| Región de nacimiento | 0,257 |
| Categoría | 0,187 |
| **Género** | **0,006** |

El género **no aporta nada** a la segmentación: es una variable que no estructura
esta población, coherente con que explique solo el 0,11 % de la varianza de la
retención (F2-2 y el EDA).

## 6. Pérdida de información

| | |
|---|---:|
| Inercia total (un solo prototipo) | 207 260,5 |
| Inercia intra-cluster con k = 2 | 174 196,3 |
| **Pérdida** | **84,05 %** |

La partición solo reproduce el **15,95 %** de la variabilidad mixta; el otro 84 %
queda dentro de los grupos. Es una cifra muy alta para una segmentación que se
pretenda útil: los dos clusters comparten casi toda la variabilidad de las siete
variables, y lo que los separa es un corte en la edad y el nivel de formación.

> **Nota de la auditoría cruzada (H8).** Una versión anterior comparaba este 15,95 %
> con el **7,08 %** de la varianza de la **retención** que explicaba la categoría en
> el EDA. La comparación no es válida: son cantidades con denominador y variable
> respuesta distintos (variabilidad mixta de siete variables frente a varianza de una
> tasa de retención). Se elimina; el argumento no la necesita.

## 7. Tres comprobaciones de estabilidad, todas negativas

| Comprobación | Resultado |
|---|---|
| Ponderación γ (0,25 y 1,0 frente a 0,5) | ARI 0,436 y 0,503: la partición **cambia** con una decisión arbitraria |
| Excluir las 23 edades imposibles | ARI **0,329**: quitar 23 filas de 77 237 altera un tercio de la asignación |
| Nivel de persona (30 086 filas) | silhouette 0,2766, tamaños 14 443 / 15 643: mismo resultado |

Que excluir **23 registros** cambie la partición hasta ARI 0,33 es la evidencia más
gráfica de que los límites entre clusters no son reales.

## 8. Veredicto: el mejor k es 1

**No hay estructura de clusters.** El k que maximiza la silhouette es 2, con
**0,28 ± 0,06**: un valor que roza el umbral convencional de 0,25 sin superarlo con
holgura, así que **la decisión no se apoya en el umbral**. Se apoya en el contraste
frente al nulo, que es el que descarta la estructura (silhouette p = **0,762**;
Calinski p = 0,524), en que la pérdida de información es del 84 %, en que los tres
criterios no coinciden entre sí y en que la partición se rompe ante cambios mínimos.
Cualquier `k > 1` devuelve una partición porque el algoritmo siempre la devuelve;
ninguna representa grupos reales.

**Lo que sí puede decirse**, y es útil:

- La población investigadora **no está formada por segmentos discretos** sino por un
  continuo con un gradiente fuerte de **edad y nivel de formación** (37 años y
  maestría frente a 52 y doctorado), con un componente territorial (Distrito Capital
  frente a Eje Cafetero).
- El **género no segmenta** esta población (V = 0,006).
- La variable que más aporta es el **nivel de formación**, por delante de la región y
  la gran área, y la **categoría** aporta menos de lo que su peso institucional
  sugeriría.

Esto es más informativo que tres clusters sin validación: dice **qué ejes organizan
la población** sin inventar fronteras que los datos no sostienen.

## 9. Límites

- **La entrada del auditado no se pudo reconstruir literalmente**: su gran tabla no
  está versionada y el generador tiene un `SyntaxError`. Se reconstruyó un conjunto
  de variables **equivalente** a partir de las que su propio informe interpretaba, y
  eso se declara en lugar de presentarlo como una réplica exacta.
- **El nulo prueba ausencia de asociación conjunta, no la inexistencia de todo
  patrón**: una estructura no detectable por k-prototypes (p. ej. no esférica, o
  anidada en subgrupos) podría existir y este diseño no verla.
- **Las observaciones no son independientes** entre sí: una persona aparece hasta
  seis veces. Se repitió el análisis a nivel de persona con el mismo resultado, pero
  los p-valores del nivel de registro son algo optimistas por esa dependencia.
- **23 edades son imposibles** (una negativa y 22 por encima de 100). No se
  eliminaron —el EDA documenta el criterio de describir el registro tal como está— y
  se reporta su efecto, que resultó ser grande (ARI 0,329).
- **Davies–Bouldin sobre one-hot es poco fiable**: trata las dicotómicas como
  continuas. Por eso no se usó como criterio único.
- **La silhouette es una estimación por submuestreo, no un valor exacto.** Se calcula
  sobre 4 000 de las 77 237 filas (la matriz de distancias completa no cabe en
  memoria) y su error de Monte Carlo es de **±0,06** (ocho réplicas: 0,14–0,30). Por
  eso se reporta 0,28 ± 0,06, no se usa el umbral de 0,25 como criterio de decisión y
  la conclusión se apoya en el contraste frente al nulo. Además, al depender del
  generador aleatorio del llamador, **la cifra solo se reproduce corriendo el script
  completo**, no llamando a la función con una semilla nueva.
- **Sospecha declarada y no verificada:** la inestabilidad es compatible con que el
  término numérico de la distancia mixta (la edad estandarizada al cuadrado) domine
  sobre el término categórico cuando hay edades extremas. Confirmarlo exigiría
  reformular la distancia, cosa que este análisis no hace.

## 10. Reproducir

```bash
python documentacion_auditoria/src/clustering_formalizado.py
```

Entrada: el CSV fuente versionado. **No necesita red.** Tarda unos 5 minutos (9
ajustes con 5 arranques, la prueba de estructura con 20 permutaciones y las
comprobaciones de estabilidad). Salidas: el JSON, el CSV con el cluster de cada uno de
los 77 237 registros y las tres figuras.

| Figura | Contenido |
|---|---|
| `f2_6_criterios_k.png` | Los cuatro criterios frente a k, con el k óptimo de cada uno |
| `f2_6_perfiles_clusters.png` | Proporción de cada categoría en cada cluster |
| `f2_6_prueba_estructura.png` | Silhouette observada frente a la distribución del nulo |
