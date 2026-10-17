# Red de co-filiación de 2019 y modelos nulos (F2-4)

**Pregunta que cierra:** Q5 del repositorio auditado — «¿qué redes de
co-filiación institucional existen y qué universidades hacen de puente?».
**Artefactos:** `documentacion_auditoria/src/redes_modelos_nulos.py` ·
`data/memoria/redes_nulos.json` · `data/memoria/redes_nodos_2019.csv` (446 nodos) ·
`data/memoria/graficas_redes/` (3 figuras).

## 1. Qué es la red, y por qué solo hay una

Nodo = institución. Arista = un investigador con **doble afiliación** (el campo
`INST_FILIA` admite dos instituciones separadas por ` | `); el peso es cuántos
investigadores comparten ambas. Se reconstruye **valor a valor**: 446 nodos, 503
aristas, densidad 0,005069, 55 componentes, el mayor con 327 nodos.

La doble afiliación **solo existe en la convocatoria de 2019**:

| Convocatoria | Registros | Con dos instituciones | % |
|---|---:|---:|---:|
| 2013 · 2014 · 2015 · 2017 · 2021 | 60 441 | **0** | 0,00 % |
| 2019 | 16 796 | **569** | 3,39 % |

Consecuencia directa: **no es una serie temporal, es una única red**. El corte por
convocatoria del auditado tiene una sola fila porque no hay otra, y su tabla
`redes_nodos_global.csv` —que dice «global»— es en realidad la red de 2019: agrupar
las seis convocatorias no añade ni una arista. Su figura «evolución 2013–2021» es
entonces un gráfico con **un punto**.

## 2. Tres precisiones sobre las cifras del auditado

Al reproducir la red encontré dos cosas que conviene dejar escritas, porque las dos
aparecen en su evidencia:

**a) 569 personas dan 537 pares.** `normalizar_institucion()` colapsa sedes, así que
**32 personas declaran dos sedes de la MISMA institución** («UNIVERSIDAD NACIONAL DE
COLOMBIA | UNIVERSIDAD NACIONAL DE COLOMBIA SEDE PALMIRA») y su par queda como
self-loop, que `construir_pares()` elimina. Es la decisión **correcta** —dos sedes
de la misma universidad no son un puente entre instituciones— pero explica la
diferencia, que si no parece un error de conteo.

**b) `grado_max` es ponderado.** `metricas_grafo()` calcula `grado_promedio` y
`grado_max` sobre el grado **ponderado**, mientras `tabla_nodos()` usa el simple. Su
«grado máximo 73» es ponderado; el grado simple máximo es **56**. No es un error de
dato, pero el nombre engaña, y en esta red la diferencia es grande porque UNAL
concentra co-filiaciones repetidas.

Con las dos precisiones, la reconstrucción coincide en **los seis valores** de su
evidencia: nodos, aristas, componentes, componente mayor, grado máximo ponderado y
densidad.

## 3. Tres nulos, no dos

| Nulo | Qué preserva | Para qué sirve |
|---|---|---|
| **Erdős–Rényi** G(n, m) | solo n y m | ¿se distingue de una red aleatoria del mismo tamaño? |
| **Configuración** | la secuencia de grados | ¿queda estructura más allá de la distribución de grados? |
| **Intercambio de aristas** (`double_edge_swap`) | la secuencia de grados **exacta**, grafo simple | prueba por nodo: ¿esta institución intermedia más de lo que su grado explica? |

El tercero hizo falta por una razón concreta: `configuration_model` genera
multigrafos y al colapsarlos se pierden aristas (quedan **485,9 de media** frente a
503), de modo que la secuencia de grados se desplaza hacia abajo y comparar «nodos
con su mismo grado» deja de ser válido. Se verificó en cada réplica que el
intercambio conserva la secuencia exacta.

## 4. Resultados globales (500 réplicas por nulo, p bilateral)

| Estadístico | Observado | Erdős–Rényi | p | Configuración | p |
|---|---:|---:|---:|---:|---:|
| N.º de componentes | 55 | 55,01 | 1,000 | 59,23 | 0,399 |
| Tamaño del componente mayor | 327 | 381,24 | **0,004** | 321,18 | 0,591 |
| Transitividad | 0,0304 | 0,0054 | **0,004** | 0,0316 | 0,922 |
| Clustering medio | 0,0144 | 0,0037 | **0,016** | 0,0124 | 0,575 |
| Asortatividad por grado | −0,1337 | −0,0021 | **0,008** | −0,0805 | **0,032** |
| Gini del grado | 0,4871 | 0,3632 | 0,004 | 0,4711 | 0,004 † |
| Gini de la betweenness | 0,9143 | 0,6393 | **0,004** | 0,9023 | **0,004** |
| Camino medio (componente mayor) | 4,068 | 6,943 | **0,004** | 4,238 | 0,072 |

† Este p-valor **no es interpretable**: el Gini del grado compara una cantidad que
el propio nulo altera (al colapsar aristas los grados bajan), así que la diferencia
sale por construcción, no por estructura. Se deja en la tabla para que no se cite
por error.

**La lectura depende del nulo, y esa es la respuesta a la pregunta.**

- **Frente a una red aleatoria del mismo tamaño, la estructura es distinta en
  todo**: mucho más agrupada (transitividad 5,6 veces mayor), más desasortativa,
  con caminos más cortos y un componente mayor más pequeño.
- **Frente a un nulo que respeta la distribución de grados, casi todo se explica
  por los grados**: el clustering, el tamaño del componente mayor, el número de
  componentes y el camino medio dejan de ser significativos. La red se parece a lo
  que produce su propia heterogeneidad de grados —con un máximo de 56 frente a una
  media de 2,26— y no hace falta invocar ninguna otra cosa.
- **Sobreviven dos rasgos**: la **desasortatividad** (p = 0,032) y la
  **concentración de la intermediación** (p = 0,004). Es decir: los nodos de grado
  alto se conectan preferentemente con nodos de grado bajo más de lo que el azar
  daría, y el corretaje está más concentrado de lo esperado.

## 5. Los puentes: aquí hay que decir que no se puede

**El criterio.** Un puente es una institución cuya betweenness supera la de los
nodos **de su mismo grado** en el nulo de intercambio de aristas. Así no se
confunde puente con hub: un nodo de grado alto tiene betweenness alta por
construcción. Se añade, como acompañante descriptivo, el **índice de
interregionalidad**: la proporción de sus co-filiaciones que cruzan macrorregión.

**El primer límite, y ya es un resultado:** de los 446 nodos, **326 (73 %) tienen
grado 1**. Un nodo hoja nunca está en un camino mínimo entre otros dos, así que su
betweenness es 0 **por construcción** y no hay nada que contrastar. No es falta de
muestra: es que el 73 % de las instituciones aparece en **una sola** co-filiación.
Quedan **120 nodos contrastables**.

**El segundo límite, y es el decisivo:**

| | |
|---|---:|
| Nodos contrastables | 120 |
| Pasan z ≥ 1,96 sin corregir | **2** |
| Esperados por azar con 120 contrastes | **≈ 3,0** |
| Pasan FDR al 5 % | **0** |
| Pasan Bonferroni (z crítico 3,53) | **0** |

Los dos que pasan el umbral nominal son la **Pontificia Universidad Javeriana**
(grado 19, z = 2,18, q = 0,997) y la **Universidad EIA** (grado 4, z = 2,98,
q = 0,997). Son **menos de los que el azar produciría**: con 120 contrastes
individuales, esperar 0,05 por prueba deja pasar unos tres falsos positivos. Tras
corregir por comparaciones múltiples **no queda ninguno**.

> **Declaración explícita.** No es posible etiquetar a una universidad concreta como
> «puente» con estos datos, y por eso F2-4 **no entrega una lista de universidades
> puente**: entregarla sería presentar como hallazgo lo que el azar produce igual de
> a menudo. Lo que sí se sostiene es el resultado **global**: la intermediación está
> concentrada más de lo esperado (Gini de betweenness, p = 0,004). Es decir, **el
> corretaje existe y está concentrado, pero no puede atribuirse a una institución
> concreta**. Distinguir esas dos afirmaciones es el aporte de este análisis.

## 6. Lo que sí puede decirse de forma descriptiva

Con la etiqueta de *descriptivo* bien puesta —la región de cada institución es un
**proxy**: la fuente no trae su sede, así que se asigna la macrorregión modal de
quienes la declaran—, el ranking de conexión interregional no se parece al de los
hubs:

| Institución | Grado | Vecinos interregionales | Regiones entre sus vecinos |
|---|---:|---|---:|
| Universidad de los Llanos | 6 | 6 de 6 | 5 |
| Ministerio de Ciencia, Tecnología e Innovación | 4 | 4 de 4 | 3 |
| Universidad del Cauca | 4 | 4 de 4 | 3 |
| Universidad Surcolombiana | 6 | 5 de 6 | 5 |
| Fundación Universitaria del Área Andina | 6 | 5 de 6 | 4 |
| Universidad Sergio Arboleda | 6 | 5 de 6 | 3 |

El patrón es interpretable y coherente con el resto del proyecto: **las
instituciones que más cruzan fronteras regionales son universidades de región
(Llanos, Cauca, Surcolombiana) y el propio Minciencias, no los grandes hubs** (UNAL,
Antioquia, Andes), que concentran co-filiaciones pero sobre todo **dentro** de su
región. Eso no es una prueba de que sean puentes: es una descripción de con quién
colaboran.

## 7. Respuesta a Q5

Sí existen redes de co-filiación institucional, pero **una sola fotografía**: 2019.
La estructura de esa red **no es aleatoria**, y con la comparación adecuada se
puede precisar en qué sentido: casi toda su forma se explica por la distribución de
grados, salvo dos rasgos —desasortatividad y concentración del corretaje— que sí son
estructura genuina. Sobre «qué universidades hacen de puente», la respuesta honesta
es que **no puede responderse con este registro**: la intermediación está
concentrada como propiedad global, pero ninguna institución se distingue de lo que
su grado y el azar explican una vez corregido por comparaciones múltiples. Los
candidatos descriptivos son universidades de región y Minciencias, no los hubs.

## 8. Límites

- **Una sola convocatoria.** No hay evolución posible; cualquier lectura temporal es
  inválida con estos datos.
- **El corretaje es co-filiación declarada**, no colaboración demostrada: dos
  instituciones quedan unidas porque una persona las declaró ambas, no porque exista
  un proyecto conjunto.
- **73 % de hojas**: la red es casi un conjunto de estrellas pequeñas en torno a
  unos pocos hubs, y eso limita estructuralmente cualquier análisis de
  intermediación.
- **La región es un proxy** (macrorregión modal de quienes declaran la institución,
  y 68 instituciones tienen declarantes en más de una). El índice de
  interregionalidad es descriptivo, no inferencial.
- **Los p-valores con 500 réplicas** tienen resolución 0,002; varios están en ese
  piso, así que deben leerse como «≤ 0,004», no como valores exactos.
- **El nulo de intercambio preserva la secuencia de grados pero no la estructura de
  componentes**, así que es conservador para detectar puentes: puede no encontrar
  puentes que existan.

## 9. Reproducir

```bash
python documentacion_auditoria/src/redes_modelos_nulos.py
```

Entradas: el CSV fuente versionado y las funciones del repositorio auditado
(`analisis.redes`). **No necesita red.** Tarda unos 12 minutos: la betweenness
exacta sobre 1 300 réplicas es el costo dominante. Salidas: el JSON, el CSV de los
446 nodos con su z y su q, y las tres figuras.

| Figura | Contenido |
|---|---|
| `f2_4_distribucion_grado.png` | Distribución de grado frente al grado medio de Erdős–Rényi |
| `f2_4_contraste_nulos.png` | Observado frente a los dos nulos, por estadístico, con sus p |
| `f2_4_puentes.png` | Betweenness de los primeros nodos frente a la media nula del mismo grado |
