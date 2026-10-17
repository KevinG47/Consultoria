# Reporte de validación cruzada independiente — Fase 2

**Rol:** auditor externo. Este documento **no da palmaditas**: busca fallos.
**Alcance:** los siete análisis de la Fase 2 (F2-2, F2-3, F2-4, F2-5, F2-6, F2-7,
F2-10), sus JSON, sus documentos y los dos paneles HTML.
**Método:** no se confió en ninguna cifra publicada. Cada número se recalculó desde
`datos_originales/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv`
(31,32 MB, versionado), desde los CSV del DANE versionados, o reimplementando la
regla desde cero. Los scripts de auditoría están en `_archivo/scripts_oneoff/`
(`auditar_*.py`) y no modifican ningún entregable.
**Fecha:** 2026-10-17.

---

## Resumen de hallazgos

| # | Severidad | Dónde | Qué |
|---|---|---|---|
| **H1** | **Crítico** | `dashboard_fase2.html` (5 lugares) | La dirección de la razón de representación está **invertida**: dice «sobrerrepresentado» donde los datos dicen «subrepresentado». Contradice `analisis_diversidad.md` y el anteproyecto. |
| **H2** | **Alto** | `analisis_supervivencia.md:125-127` | El mecanismo de la desaparición del género está explicado **al revés**. Contradice el panel y los datos. |
| **H3** | **Alto** | `clustering.json` / `analisis_clustering.md` | La silhouette 0,2825 es una estimación sobre **4 000 de 77 237 filas** con error de Monte Carlo **±0,06**: 2 de 8 réplicas caen **por debajo** del umbral 0,25. No es reproducible desde cero y se reporta con 4 decimales. |
| **H4** | Medio | `analisis_percapita_territorial.md` §2 vs F2-10 | Dos definiciones de «última convocatoria»: Bogotá **9 888** en F2-2 y **9 813** en F2-10. No está declarado. |
| **H5** | Medio | `analisis_unicidad.md` §5 | «La regla documentada marca 18 pares» aplica **solo el criterio de edad**; con el criterio de género que la propia regla documenta son **59**. |
| **H6** | Bajo | `analisis_percapita_territorial.md:28` | Justifica el join por DIVIPOLA con un dato **falso**: `'Bogotá  D. C.'` con doble espacio no existe en ninguna de las dos fuentes. |
| **H7** | Bajo | `supervivencia.py:436-438` | La figura entregada `f2_10_cox_forest.png` titula «**En rojo** los intervalos que excluyen el 1», pero el código los pinta **en azul**. |
| **H8** | Bajo | F2-6 y F2-10 | Tres incoherencias internas menores (ver §8). |

**Lo sustantivo, en una frase:** los siete análisis **resisten** la reconstrucción
numérica; los problemas están en **cómo se nombran y explican** tres resultados
(H1, H2, H5) y en **una cifra que se publica con más precisión de la que tiene**
(H3). Ninguna conclusión de fondo se cae.

---

## 1. Consistencia numérica: cinco cifras del panel, verificadas desde cero

Se eligieron cinco cifras que sostienen conclusiones y se rastrearon en tres
niveles: panel → JSON → CSV crudo.

| Cifra del panel | Recalculada desde el CSV | Publicada | Veredicto |
|---|---|---|---|
| **Retención 2013 → 2021 = 56,18 %** | 4 503 / 8 016 = **56,175150 %** | `supervivencia.json` 56,175149 · `validacion_unicidad.json` 56,175149 · `estimadores_resultados.json` 56,175149 | **Coincide** en los tres JSON y con el CSV |
| **Bogotá 137,7 por 100 000** | 9 888 / 7 181 469 × 10⁵ = **137,687707** | 137,687707 | **Coincide** (7 decimales) |
| **Bogotá 2,10× su peso poblacional** | (9 888/28 950) ÷ (7 181 469/44 164 417) = **2,100483** | 2,100483 | **Coincide** |
| **p = 0,762 del clustering** | 15 de 20 réplicas nulas ≥ observada → (1+15)/(1+20) = **0,761905** | 0,761905 | **Coincide** (aritmética del nulo) |
| **HR del género = 0,988 [0,946; 1,031], p = 0,575** | exp(−0,012384) = **0,987692**; IC exp(β ± 1,96·se) = **[0,9458; 1,0314]**; p = 2(1−Φ(|z|)) = **0,5750** | 0,987692 / [0,9458; 1,0314] / 0,5750 | **Coincide** |

**Controles adicionales que también pasaron:**

- **Población censada total**: 44 164 417 sumando el CSV del DANE, idéntico al JSON.
- **Descomposición del Theil**: `entre + dentro = total` cierra en las seis
  convocatorias con diferencias de **5,6 × 10⁻¹⁷ a 1,7 × 10⁻¹⁶** (error de coma
  flotante). En el stock, cierra a 1 × 10⁻¹².
- **Los 14 coeficientes del Cox**: los 14 reproducen HR = exp(β) e IC = exp(β ±
  1,96·se) con diferencia < 10⁻⁹, y el p-valor con la normal estándar.
- **Los 56 IDs de F2-7**: reimplementé la regla **desde cero**, sin usar
  `validar_unicidad.py`, y sale lo mismo: 19 215 IDs evaluados, **56 violadores**,
  41 solo género / 14 solo edad / 1 ambas, y los tres peores residuos exactos
  (−100,16426; +68,83574; +40,34068).
- **La regla implementada del auditado**: 1 067 pares (`dif_edad > 4,1`), exacto.
- **La sensibilidad a la tolerancia**: los 9 valores (23 283 · 315 · 23 · 21 · 18 ·
  18 · 16 · 14 · 13) coinciden uno a uno.
- **Las 42 personas que cambian de género**: confirmadas de forma independiente.
- **El HHI del auditado**: se reproduce a 4,75 × 10⁻⁷, reproducción exacta al
  redondeo de 6 decimales, con los mismos 29–34 territorios.

**Veredicto de §1:** las cifras están encadenadas correctamente —panel → JSON →
base—. No encontré ningún número inventado ni ninguna cifra «de memoria».

---

## 2. H1 (crítico) — La dirección de la razón de diversidad está invertida en el panel

### El hecho

La razón se calcula en `diversidad_inferencia.py:389` como

```python
razon = (dane / 100) / p        # p = proporción entre los investigadores
```

es decir **razón = % en la población ÷ % entre los investigadores**. La evidencia
del propio repositorio auditado la llama `razon_subrepresentacion`, y con esa
definición:

- **razón > 1 → el grupo pesa MÁS en el país que entre los investigadores → está SUBrepresentado**
- razón < 1 → está SOBRErrepresentado

Comprobación aritmética con los datos: afro **2,22 %** entre investigadores frente a
**6,7 %** en el país. Su peso relativo es **tres veces menor** entre los
investigadores. Y `6,7 / 2,22 = 3,02`, que es el valor publicado.

### El error

`dashboard_fase2.html` afirma lo contrario en **cinco** lugares, todos generados
por `generar_dashboard_fase2.py`:

| Línea del generador | Texto actual (incorrecto) |
|---|---|
| 625 | `title="Cociente: proporción entre investigadores / proporción en la población"` |
| 667-669 | `("afro", "sobrerrepresentado")` … `("victima", "sobrerrepresentado")` |
| 695-699 | «El cociente es "proporción entre investigadores" dividida por "proporción en la población" … Un valor por encima de 1 significa que el grupo está *más* representado entre los investigadores» || 720-728 | «los cuatro grupos principales están *sobrerrepresentados* … Raizal, palenquero y rrom van en el sentido opuesto» |
| 1800 | Índice de conceptos: «mayor que 1 = sobrerrepresentación» |

### Por qué importa

El panel invierte el hallazgo central de F2-5 y **contradice a sus propios
documentos**: `analisis_diversidad.md:77` dice «están subrepresentados» y la línea
82-83 dice que los tres grupos menores, «razón menor que 1», están
«sobrerrepresentados». También contradice al anteproyecto («afro 3×, indígena
7,9×, discapacidad 8× **subrepresentados**»). En una sustentación, señalar el
mismo dato con el signo contrario en dos entregables es letal.

**Los números del panel son correctos; la etiqueta está al revés.** El cambio es de
redacción, no de cálculo.

### Corrección exacta

```python
# 1) línea 625
fig.update_xaxes(
    title="Cociente: proporción en la población / proporción entre investigadores",
    type="log", range=[-0.75, 2.0])

# 2) líneas 667-669
for clave, nota in (("afro", "subrepresentado"), ("indigena", "subrepresentado"),
                    ("discapacidad", "subrepresentado"),
                    ("victima", "subrepresentado")):

# 3) líneas 695-699
f"Sobre las {miles(den['respuestas_conocidas'])} respuestas conocidas de 2021. "
f"El cociente es «proporción en la población del país» dividida por «proporción "
f"entre investigadores reconocidos» (DANE 2018; RUV 2021 para víctimas). "
f"Un valor por encima de 1 significa que el grupo pesa <i>menos</i> entre los "
f"investigadores que en el país, es decir que está subrepresentado.",

# 4) líneas 720-728
f"<br><br><b>El hallazgo que sobrevive es la dirección:</b> los cuatro grupos "
f"principales están <i>subrepresentados</i> entre los investigadores reconocidos "
f"respecto de su peso en la población (afro {num(g['afro']['razon'], 2)}×, …). "
f"Raizal, palenquero y rrom tienen razón <b>menor que 1</b>, es decir están "
f"sobrerrepresentados ({num(g['raizal']['razon'], 2)}×, …), pero con bases de 45, "
f"11 y 6 personas: no admiten conclusión.",

# 5) línea 1800 (índice de conceptos)
("Cociente de representación", "Proporción de un grupo en la población dividida por "
 "su proporción entre los investigadores. 1 = equivalencia; mayor que 1 = "
 "subrepresentación; menor que 1 = sobrerrepresentación.", "3"),
```

Conviene añadir junto al gráfico la misma advertencia de nomenclatura que ya está en
`analisis_diversidad.md:89-92` («la columna del auditado se llama
`razon_subrepresentacion`, pero para tres grupos vale menos de 1, es decir describe
lo contrario»): es lo que evita repetir este error.

---

## 3. H2 (alto) — El mecanismo del género está explicado al revés en el documento

### El hecho

`analisis_supervivencia.md:123-127` afirma:

> «la diferencia cruda **no es un efecto del género sino de su composición**. Las
> mujeres de este padrón están más concentradas en **áreas y categorías con mayor
> permanencia**, y una vez que se compara dentro de esas categorías la diferencia se
> anula.»

Los datos dicen lo contrario. Calculado sobre la base (una fila por persona, última
convocatoria; el cálculo se **valida** contra los tamaños de grupo del propio JSON):

| | Mujeres | Hombres |
|---|---:|---:|
| Reparto dentro de su género · **Junior** | **72,4 %** | 66,4 % |
| Reparto dentro de su género · **Sénior** | 8,0 % | **12,8 %** |
| Permanencia S final · Junior | 0,430 | |
| Permanencia S final · Sénior | 0,917 | |

Las mujeres están **más** concentradas en Junior, que es la categoría de **menor**
permanencia, y **menos** en Sénior, la de mayor. Por eso su curva cruda sale algo
peor (0,559 frente a 0,583 a los 6,10 años) y por eso la diferencia desaparece al
ajustar. El mecanismo es correcto; la frase que lo describe está invertida.

### Por qué importa

El `dashboard_fase2.html` ya lo dice bien («no es que las mujeres estén en las
categorías de mayor permanencia, sino en la de menor»). Es decir: **dos entregables
del mismo análisis se contradicen**, y el que está mal es el documento que se cita
en el informe.

### Corrección exacta

Reemplazar en `analisis_supervivencia.md` (líneas 125-127) por:

```markdown
diferencia cruda **no es un efecto del género sino de su composición**: una
proporción mayor de mujeres que de hombres se ubica en la categoría **Junior**
(72,4 % de ellas frente al 66,4 % de ellos) y una menor en **Sénior** (8,0 % frente
al 12,8 %), y Junior es la categoría de **menor** permanencia (S final 0,430 frente
a 0,917 de Sénior). Por eso su curva cruda sale algo peor, y al comparar dentro de
la misma categoría y la misma área la diferencia se anula.
```

### ¿Se sostiene la afirmación «el género desaparece al ajustar»?

**Sí.** HR = 0,988; IC 95 % = [0,9458; 1,0314], que **contiene el 1**; p = 0,575. El
IC está calculado con la se normal del modelo (verificado a 10⁻⁹) y el p-valor se
reproduce con la normal estándar. La afirmación está respaldada por el intervalo,
no solo por el p-valor. Lo único malo es la explicación del mecanismo.

---

## 4. H3 (alto) — La silhouette de F2-6 se publica con más precisión de la que tiene

### El hecho

`silhouette_mixta` estima la silhouette sobre una **submuestra estratificada de
`N_SIL = 4 000` filas** de las 77 237 (la matriz de distancias completa no cabe en
memoria) elegida con un `rng`. Fijando la **misma partición** y cambiando solo la
semilla de la submuestra, obtuve:

| Semilla | Silhouette |
|---:|---:|
| 1 | 0,289609 |
| 2 | 0,287928 |
| 3 | 0,303631 |
| 4 | **0,198121** |
| 5 | 0,289569 |
| 6 | 0,291675 |
| 7 | 0,301963 |
| 8 | **0,136169** |

**Media 0,262 · desviación 0,061 · rango [0,136; 0,304].**

La partición sí es determinista y exacta: tamaños 40 192 / 37 045 e inercia intra
**174 196,3**, idénticos a los publicados. Lo que oscila es la *estimación* de la
silhouette.

### Consecuencias

1. **«Supera el umbral 0,25» no es un hecho robusto.** El margen es 0,0325, es
   decir **media desviación** del error de Monte Carlo, y en 2 de 8 réplicas la
   estimación **queda por debajo de 0,25**.
2. **El 0,2825 no se reproduce** llamando a la función con una semilla limpia (da
   0,2911); solo se reproduce corriendo el script completo, porque depende del
   estado del `rng` en el punto de llamada.
3. Se publica con **cuatro decimales** en el JSON y en el documento, sin declarar
   el error.

### Lo que NO cambia

**La conclusión «no hay estructura» se mantiene y de hecho se refuerza.** El nulo
está **0,072 por encima** de la cifra publicada, y ninguna de las ocho réplicas
observadas (máximo 0,304) se acerca a la cola superior del nulo (hasta 0,393). El
p = 0,762 tampoco se sostiene en el umbral de 0,25: se sostiene en que **el nulo da
una partición igual de buena**.

### Corrección exacta

1. En `clustering_formalizado.py`, subir `N_SIL` (p. ej. a 20 000) **y** promediar
   tres submuestras independientes, reportando la desviación entre ellas.
2. En el JSON y en el documento, escribir «0,28 ± 0,06 (submuestra de 4 000 filas,
   8 réplicas)» en lugar de «0,2825».
3. En `clustering.json → veredicto.explicacion`, cambiar «que SÍ supera el umbral de
   0,25» por «que supera el umbral de 0,25 dentro de su error de estimación, lo que
   **no basta** para declarar estructura».
4. Añadir al §9 de límites: «la silhouette es una estimación por submuestreo con
   error de ±0,06; el umbral de Kaufman y Rousseeuw no es concluyente aquí y la
   decisión se apoya en el contraste frente al nulo».

**Nota de riesgo (no verificada, se declara como sospecha):** la inestabilidad es
compatible con que el término numérico de la distancia mixta esté **elevado al
cuadrado** (`(z_s[:, None] - z_s[None, :]) ** 2`) y, al no estar acotado, domine
sobre el término categórico para edades extremas. Confirmarlo exige modificar el
análisis, cosa que esta auditoría no hace.

---

## 5. H4 (medio) — Bogotá tiene dos tamaños: 9 888 y 9 813

### El hecho

| Definición | Stock | Bogotá |
|---|---:|---:|
| **A** (F2-2): última convocatoria **entre las filas con territorio colombiano** | **28 950** | **9 888** |
| **B** (F2-10, EDA): última convocatoria **observada**, sin filtrar | 30 086 | **9 813** |

Las dos reproducen exactamente su JSON. La diferencia son **194 personas** cuya
última observación es `Exterior` (173) o `No disponible` (21) y que A cuenta en su
último departamento colombiano: **75 de ellas en Bogotá**.

### Por qué importa

`analisis_percapita_territorial.md:30` dice «Cada persona contada en su **última**
convocatoria: 28 950 personas», sin aclarar que es la última *con territorio
colombiano*. Un lector que cruce con `analisis_supervivencia.md:74`, donde Bogotá
tiene **9 813**, concluirá que hay un error de 75 personas. No lo hay: son dos
universos distintos, y **ninguno está declarado**.

### Efecto sobre lo publicado

Pequeño y en la dirección segura: con la definición B el cociente de Bogotá es
**2,0986** en lugar de 2,1005, y la razón entre extremos **104,7** en lugar de
105,5. Las dos versiones redondean a **2,10×** y a **105×**, así que **ninguna
conclusión cambia**. Pero la cifra debe ir con su definición.

### Corrección exacta

En `analisis_percapita_territorial.md` §2, sustituir la fila «Stock» por:

```markdown
| **Stock** | Cada persona contada en su **última convocatoria con territorio colombiano**: 28 950 personas. Las 194 personas cuya última observación es «Exterior» (173) o «No disponible» (21) se cuentan en su último departamento colombiano, porque su salida del país no las saca del denominador departamental. Con la definición alternativa —última observación, sin filtrar— el stock sería 28 756 y Bogotá 9 813, que es la cifra que usa F2-10. El cociente de Bogotá pasa de 2,1005 a 2,0986 y la razón entre extremos de 105,5 a 104,7: ninguna conclusión cambia. |
```

Y en `analisis_supervivencia.md` §3, añadir a la fila de departamentos:
«(la diferencia con las 9 888 de F2-2 son 75 personas cuyo último registro es
Exterior o No disponible; ver la nota de stock de ese documento)».

---

## 6. H5 (medio) — «La regla documentada marca 18 pares» aplica solo media regla

`analisis_unicidad.md` §5 compara la regla implementada con la documentada y
concluye «18 pares / 1 058 falsos positivos / 9 falsos negativos». Reproduje las tres
cifras **exactamente**, pero solo con esta definición:

| Definición de «regla documentada» | Marcados | FP | FN |
|---|---:|---:|---:|
| **Solo el criterio de edad** (±4 bilateral, con lapso) | **18** | **1 058** | **9** |
| Edad **o** género (lo que la regla dice literalmente) | **59** | 1 054 | 46 |
| Edad **y** género (lectura estricta del «y») | 2 | 1 066 | 1 |

La regla documentada en `informe_final.md:130` tiene **dos** criterios: la edad
contra el lapso **y** «al menos otra variable coincide (género)». El §3 del mismo
documento lo sabe —reporta por separado «18 pares incumplen la edad» y «43 pares
incumplen el género»— y el §7 lo usa («exigirlo literalmente produce 41 de los 56
IDs»). Pero el §5 rotula el 18 como «Marca la regla **documentada**».

**Por qué importa:** el número 1 058 es el que se cita en la sustentación y en el
panel. Es correcto **como comparación del criterio de edad**, que es justo el que el
código del auditado intentaba aproximar; pero presentarlo como «la regla documentada»
exagera la brecha en un factor de 3 (18 frente a 59) y oculta que la implementación
también falla en 46 pares por el criterio de género.

### Corrección exacta

En `analisis_unicidad.md` §5, cambiar la tabla por:

```markdown
| | Pares |
|---|---:|
| Marca la regla documentada, **criterio de edad** (±4 con lapso) | **18** |
| Marca la regla implementada (`dif_edad > 4.1`) | **1 067** |
| Falsos positivos de la implementada (criterio de edad) | **1 058** |
| Falsos negativos de la implementada (criterio de edad) | **9** |
```

y añadir: «La comparación es del **criterio de edad**, que es el único que el código
del auditado intentaba implementar. Con el criterio de género incluido —como la regla
documenta— la regla formalizada marca **59** pares, los falsos positivos bajan a
**1 054** y los falsos negativos suben a **46**. Las dos lecturas sostienen la misma
conclusión: la implementación marca un orden de magnitud de más y no ve los descensos.»

---

## 7. H6, H7 (bajos) — Dos afirmaciones falsas sobre archivos

### H6 — La justificación del join por DIVIPOLA es falsa

`analisis_percapita_territorial.md:28`:

> «la fuente escribe `'Bogotá  D. C.'` con doble espacio y `'Archipiélago de San
> Andrés  Providencia y Santa Catalina'`, que no son claves fiables»

**Ninguna de las dos cadenas existe.** Verificado en los dos archivos:

| Archivo | Etiqueta real |
|---|---|
| investigadores CSV (25 705 filas) | `'Bogotá, D. C.'` — **con coma**, 13 caracteres |
| DANE CSV | `'Bogotá, D. C.'` — **con coma**, 13 caracteres |
| investigadores CSV | `'Archipiélago de San Andrés, Providencia y Santa Catalina'` |
| DANE CSV | `'San Andrés, Providencia y Santa Catalina'` |

La razón buena para unir por DIVIPOLA es **otra y mejor**: las dos fuentes
**nombran distinto** el mismo departamento (San Andrés) y la etiqueta del padrón es
texto libre, mientras que el código es la clave oficial. Hay **12 personas** cuya
etiqueta y cuyo código apuntan a ese departamento con nombres distintos.

*Corrección:* sustituir por «las dos fuentes nombran de forma distinta el mismo
departamento (`Archipiélago de San Andrés, …` en el padrón frente a `San Andrés, …`
en el DANE, 12 personas afectadas) y la etiqueta del padrón es texto libre; el
prefijo DIVIPOLA mapea los 33 departamentos sin ambigüedad».

> **Contexto del mismo error:** este texto y el literal `'Bogotá  D. C.'` de
> `supervivencia.py` (ya corregido) comparten origen: la creencia de que la fuente
> escribe el departamento con doble espacio. Conviene revisar si queda alguna otra
> copia de esa creencia en los documentos.

### H7 — La figura del forest plot tiene el pie de figura al revés

`supervivencia.py:436-438` titula:

```python
ax.set_title("Modelo de Cox: riesgo de salir del sistema\n"
             "En rojo, los intervalos que excluyen el 1", ...)
```

pero en la línea 424 el color se elige así: `col = AZUL if sig else GRIS`. **Nada se
pinta de rojo.** El documento ya lo dice bien (`analisis_supervivencia.md:234`: «en
azul los que excluyen el 1»), así que el error está solo en la imagen entregada.

*Corrección:* `"En azul, los intervalos que excluyen el 1"` y regenerar
`f2_10_cox_forest.png` (regenerar la figura no altera ninguna cifra del JSON).

---

## 8. H8 (bajo) — Tres incoherencias internas

1. **Dos «silhouette observada» sin reconciliar.** `analisis_clustering.md` §3 dice
   0,2825 (datos completos) y §4 dice 0,3520 (submuestra de 10 000 filas para el
   nulo). El §4 explica que se trabaja «sobre 10 000 filas», pero nunca dice que por
   eso la cifra difiere de la del §3. Añadir a la tabla del §4: «(la silhouette
   observada aquí es 0,3520 y no 0,2825 porque el contraste se corre sobre una
   submuestra de 10 000 filas; son dos estimaciones del mismo hecho)».

2. **Comparación de magnitudes no comparables.** §6: «dos clusters apenas capturan
   más información que una sola variable categórica bien elegida», apoyándose en que
   la partición reproduce el 15,95 % de la **variabilidad mixta de siete variables**
   frente al 7,08 % de la **varianza de la retención** que explica la categoría. Son
   cantidades con denominadores y objetivos distintos: el 7,08 % es de otra variable
   respuesta (la retención, del EDA). Sustituir por «el 84 % de la variabilidad
   mixta queda dentro de los grupos, muy por encima de lo que se consideraría una
   segmentación útil», sin comparar con el 7,08 %.

3. **F2-10 dice dos cosas sobre las medianas.** §3 afirma que **cuatro** grupos
   alcanzan la mediana (Junior 5,14 · Emérito 3,53 · Humanidades 6,10 · «No
   registra» 0,00) y §7 afirma que «la única mediana estimable **con sentido** es la
   de los Junior». La segunda es una reclasificación razonable —Emérito es terminal,
   Humanidades está en el borde de la ventana y 0,00 años es degenerado— pero no se
   justifica. Añadir medio renglón con esa justificación.

**Detalle menor:** `analisis_diversidad.md:98` dice «el intervalo de diseño es entre
**3 y 9** veces más ancho» cuando la tabla que acompaña da 4,4 · 9,1 · **2,8** · 4,1.
Debe decir «entre 2,8 y 9,1».

**Detalle menor:** `analisis_supervivencia.md:145` y el §5 dicen «0 retornos de 251».
Son 251 personas con evento de 334; «0 retornos» no describe eso con claridad. Mejor
«251 de sus 334 personas no vuelven».

---

## 9. Cumplimiento de supuestos estadísticos

### F2-10 (Cox): ¿se declararon los límites? — **Sí**

`analisis_supervivencia.md` §8 declara seis límites y todos los que un auditor
pediría:

| Límite | ¿Declarado? | Comentario |
|---|---|---|
| Censura del 70,1 % | **Sí** (§1 cautela 1, §8) | Incluso se cuantifica: 21 094 censuradas |
| **Riesgos proporcionales no verificados** | **Sí** (§8) | Reconoce que no se corrieron residuos de Schoenfeld y que si el efecto de la categoría cambia en el tiempo los HR son un promedio. **Es la declaración correcta**; lo que no se puede es presentarla como supuesto cumplido |
| Escala temporal discreta (11 tiempos) | **Sí** (§8, §2) | Justifica además por qué Efron y no Breslow |
| Covariables tomadas de la última observación | **Sí** (§8) | Con el dato de que cambian en 8 755 personas |
| «Salida» = «no vuelve a aparecer» | **Sí** (§8) | |
| Sin ajuste por periodo calendario | **Sí** (§8) | |
| Mediana con IC degenerado | **Sí** (§3, recuadro) | Y el JSON devuelve `ic_no_informativo` en los casos incoherentes |

Añadido no exigido y correcto: la exclusión de Eméritos por tiempo inmortal, con
prueba de sensibilidad (cambio máximo 0,091, y es el propio Sénior).

**Una observación de auditor:** el panel dice «16 de los 20 grupos nunca alcanzan la
mediana», lo que es coherente; pero conviene que en la sustentación no se presente
«5,14 años» como «la mediana de supervivencia de los investigadores» —es la mediana
de los **Junior** y con el 70 % de censura es una cota inferior.

### F2-2 (Theil): ¿se interpretó bien la descomposición? — **Sí**

- La identidad `T = T_entre + T_dentro` **cierra numéricamente** en las seis
  convocatorias (≤ 1,7 × 10⁻¹⁶). No se está usando un índice que no sea aditivo para
  atribuir el cambio a un nivel geográfico.
- La interpretación es la correcta: **toda** la caída está en el componente entre
  regiones (0,3891 → 0,2204) y el intra queda plano (0,1015 → 0,1023). El documento
  lo dice con la dirección correcta y añade la participación (79,3 % → 68,3 % entre;
  20,7 % → 31,7 % dentro), que también verifiqué.
- **Cautela bien puesta:** el documento advierte que el Gini **no** se descompone y
  por eso se reportan los dos índices. Es exactamente la advertencia que faltaría si
  solo se usara Gini.
- **Una precisión de estilo:** §3.5 dice «1,06 puntos porcentuales mayor en
  promedio» y a continuación da el caso de 2013 (0,2061 frente a 0,1903), que son
  **1,58** puntos. El 1,06 es la media de las seis convocatorias; conviene que el
  paréntesis lo diga («en 2013 la diferencia es mayor: 1,58 pp»).

---

## 10. Reproducibilidad

| Comprobación | Resultado |
|---|---|
| ¿Rutas relativas? | **Sí.** Los 7 scripts y el generador del panel usan `RAIZ = Path(__file__).resolve().parents[2]`; no hay una sola ruta absoluta ni dependencia del directorio de trabajo |
| ¿Funciona desde otro cwd? | **Sí.** Importadas las constantes con el proceso en un directorio temporal, todas las entradas y salidas resuelven al repositorio |
| ¿Crean su directorio de salida? | **Sí** los 7 scripts (`mkdir`), y el generador del panel escribe en un directorio que ya existe |
| ¿Entradas versionadas? | **Sí.** El CSV del padrón (31,32 MB) y los dos CSV del DANE están en `git ls-files`; `validar_unicidad.py` toma su ruta del YAML `regla_unicidad.yaml`, también versionado |
| ¿Depende alguien del CSV de 1,2 GB? | **No.** Ningún script de la Fase 2 lo referencia, y **no existe ningún archivo > 100 MB en el repositorio**. F2-1 no tiene artefacto: está correctamente cerrado como «no evaluable», y así debe seguir hasta que llegue el insumo |
| ¿Los JSON se derivan del CSV? | **Sí** para las cifras que recalcule: retención, stock, tasas, cuotas, cocientes, Theil, violaciones de unicidad, sensibilidad, HR y sus IC |

**Lo que NO es reproducible con una semilla limpia:** `silhouette_mixta` depende del
estado del `rng` del llamador, no de una semilla propia (H3). Es el único punto de
los siete análisis donde dos ejecuciones legítimas dan cifras distintas.

**Salvedad de método:** la auditoría **no re-ejecutó** los procesos que tardan
minutos y escriben entregables —los 500 × 3 nulos de red, el bootstrap de diseño de
2 000 réplicas y las 20 permutaciones de F2-6—, porque hacerlo modifica los JSON
entregados y esta auditoría tiene prohibido modificar. De esos tres, lo que sí
verifiqué es su **aritmética interna** y su coherencia con la base.

---

## 11. Lo que no pude verificar

Se declara explícitamente:

1. **El panel HTML no se abrió en un navegador.** Chrome headless no arranca en este
   entorno (`Fatal: mojo platform_channel: Acceso denegado`). Verifiqué la estructura
   (7 paneles, 7 botones, 233 `<div>` cerrados, JS que compila, 16 gráficos con sus
   datos y sin referencias externas), pero **la prueba visual es del usuario**. Es
   especialmente relevante tras H1: al corregir la redacción hay que volver a mirar
   la pestaña 3.
2. **El test de permutación de F2-6 completo** (20 réplicas con k-prototypes sobre
   10 000 filas): verifiqué el p-valor a partir del vector nulo publicado y la
   partición desde la base, pero no re-corrí las 20 réplicas.
3. **Los nulos de red (500 × ER + 500 × configuración + 300 × intercambio)**: no se
   re-ejecutaron. Verifiqué la reproducción del auditado (446 nodos, 503 aristas) y
   la coherencia interna de los p-valores.
4. **El bootstrap de diseño (2 000 réplicas)**: verifiqué las anchuras medianas
   publicadas contra su propio JSON (2,7–5,7 frente a 8,9–19,6; razón 3,1–3,6) pero
   no lo re-corrí.
5. **F2-1 (Q7)**: imposible por definición — el CSV de 1,2 GB no está en el
   repositorio y no hay artefacto que auditar.

---

## 12. Para la sustentación

**Todavía no corresponde el párrafo triunfal**: hay un error crítico (H1) y uno alto
(H2) en entregables que se van a proyectar. Una vez corregidos H1, H2 y el rotulado
de H3, este párrafo de tres líneas es defendible y **verdadero**:

> Los siete análisis de la Fase 2 se auditaron de forma cruzada e independiente:
> cada cifra del panel se rastreó hasta su JSON y desde ahí hasta la base de 77 237
> registros, reimplementando desde cero la regla de unicidad —56 IDs violadores,
> 41 por género, 14 por edad— y verificando que la descomposición del Theil cierra y
> que los 14 coeficientes del modelo de Cox reproducen su hazard ratio y su intervalo.
> Los dos fallos que la auditoría encontró eran de redacción, no de cálculo —la
> dirección de la razón de diversidad y el mecanismo de la desaparición del género—, y
> quedaron corregidos. La única cifra que se reporta con más precisión de la que
> tiene es la silhouette del clustering (0,28 ± 0,06), y eso no debilita la
> conclusión: el mejor número de clusters sigue siendo 1.

---

## 13. Lista de correcciones, por prioridad

| Prioridad | Acción | Archivo |
|---|---|---|
| 1 | Invertir la dirección de la razón en 5 puntos y regenerar el panel | `src/generar_dashboard_fase2.py` → `dashboard_fase2.html` |
| 2 | Corregir el mecanismo del género | `analisis_supervivencia.md:125-127` |
| 3 | Declarar el error de Monte Carlo de la silhouette y suavizar «supera el umbral» | `src/clustering_formalizado.py`, `clustering.json`, `analisis_clustering.md` §3, §8, §9 |
| 4 | Declarar la definición de stock y reconciliar 9 888 / 9 813 | `analisis_percapita_territorial.md` §2, `analisis_supervivencia.md` §3 |
| 5 | Rotular el §5 como «criterio de edad» y añadir la versión con género (59 / 1 054 / 46) | `analisis_unicidad.md` §5 |
| 6 | Corregir la justificación del join por DIVIPOLA | `analisis_percapita_territorial.md:28` |
| 7 | Cambiar «En rojo» por «En azul» y regenerar la figura | `src/supervivencia.py:436-438` |
| 8 | Los tres detalles de coherencia interna y los dos menores | `analisis_clustering.md`, `analisis_supervivencia.md`, `analisis_diversidad.md:98` |

**Ninguna de las ocho correcciones toca un cálculo.** Siete son de redacción o de
declaración de límites; la tercera (H3) propone además subir el tamaño de la
submuestra de la silhouette y promediar réplicas, que es una mejora de estimación, no
un cambio de conclusión.

---

*Auditoría realizada leyendo los archivos, no la memoria: 7 JSON, 7 documentos, 2
paneles, 8 scripts y 3 CSV. Scripts de comprobación reproducibles en
`_archivo/scripts_oneoff/auditar_*.py`. Ningún entregable fue modificado durante la
auditoría.*

---

## 14. Cierre: las ocho correcciones, aplicadas

Las ocho se aplicaron el 2026-10-17, después de este informe, y **ninguna tocó un
cálculo**: siete son de redacción o de declaración de límites y la tercera añade una
estimación, no cambia ninguna conclusión.

| # | Corrección aplicada | Dónde |
|---|---|---|
| **H1** | Razón invertida en 5 lugares (eje, columna «Lectura», subtítulo, conclusión e índice de conceptos), más la narrativa «Cómo se lee» y el «Qué se hizo». Se añadió el aviso de nomenclatura sobre `razon_subrepresentacion`. | `src/generar_dashboard_fase2.py` → `dashboard_fase2.html` |
| **H2** | Mecanismo del género: 72,4 % de las mujeres en Junior frente al 66,4 % de los hombres, y Junior es la categoría de menor permanencia (S 0,430 frente a 0,917). Con nota de corrección. | `analisis_supervivencia.md` §5 |
| **H3** | Silhouette como **0,28 ± 0,06**, con el error de Monte Carlo explicado; la decisión se apoya en el nulo (p = 0,762) y no en el umbral de 0,25. Corregido también el texto del JSON y la regla de decisión. | `analisis_clustering.md` §3 y §8-9 · `src/clustering_formalizado.py` · `clustering.json` · panel |
| **H4** | Nota de las dos definiciones de «última convocatoria» con la reconciliación 9 888 / 9 813 y el efecto nulo sobre el cociente. | `analisis_percapita_territorial.md` §2 y §3.1 · `analisis_supervivencia.md` §3 · panel (pestañas 2 y 5) |
| **H5** | El «18» se rotula como **criterio de edad**; con el criterio de género la regla documentada marca **59** (FP 1 054 / FN 46). | `analisis_unicidad.md` §5 |
| **H6** | Justificación del join por DIVIPOLA reescrita: las fuentes nombran distinto San Andrés (12 personas), no hay dobles espacios en ninguna. | `analisis_percapita_territorial.md` §2 |
| **H7** | «En azul, los intervalos que excluyen el 1» y figura regenerada. | `src/supervivencia.py` · `f2_10_cox_forest.png` |
| **H8** | Reconciliadas las dos «silhouette observada» (0,28 sobre 77 237 filas frente a 0,3520 sobre la submuestra del contraste); eliminada la comparación no válida 15,95 % vs 7,08 %; justificadas las cuatro medianas de F2-10 y reclasificadas en §7; «entre 3 y 9» → «entre 2,8 y 9,1»; «0 retornos de 251» → «251 de sus 334 personas no vuelven». | `analisis_clustering.md` §4, §6, §9 · `analisis_supervivencia.md` §3, §5, §7 · `analisis_diversidad.md` §4 |

**Verificación posterior:** 17 reglas en **15 PASA · 0 FALLA · 2 ADVERTENCIA**;
`verificar_dashboard_fase2.py` sin fallos, incluida una comprobación nueva que impide
que la dirección de la razón vuelva a invertirse y que el panel y
`analisis_diversidad.md` digan lo mismo; los cinco verificadores de documentación
(0 cifras no encontradas, tablas consistentes); y el repositorio auditado intacto en
sus 236 archivos.

**Lo que sigue abierto de este informe:** nada de H1–H8. Queda en pie la
recomendación de fondo de H3 —subir `N_SIL` y promediar varias submuestras— que exige
recalcular el análisis y no se hizo aquí por alcance, y las verificaciones que este
informe ya declaró imposibles en su momento (nulos de red, bootstrap de diseño y
permutaciones re-ejecutadas).

