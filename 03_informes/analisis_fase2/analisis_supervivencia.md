# Supervivencia: Kaplan-Meier y modelo de Cox (F2-10)

**Qué cierra:** la dinámica longitudinal prometida en el anteproyecto y nunca
realizada — «supervivencia con censura vs transición» quedó como recomendación en
nuestro propio criterio 4 y la ruta de Markov se había quedado sin modelos de
tiempo hasta la salida.
**Artefactos:** `documentacion_auditoria/src/supervivencia.py` ·
`01_datos/resultados_json/supervivencia.json` · `data/memoria/supervivencia_personas.csv`
(30 086 personas) · `data/memoria/supervivencia_cox.csv` ·
`data/memoria/graficas_supervivencia/` (5 figuras).

## 1. El diseño

| | |
|---|---|
| Unidad | persona (30 086) |
| Evento | **salida del sistema**: la última convocatoria en que aparece no es 2021 (8 992 eventos, 29,9 %) |
| Tiempo | años desde la **primera** aparición hasta la última, con las fechas reales |
| Censura | a la derecha si su última observación es 2021 (**21 094 personas, 70,1 %**) |
| Ventana | 7,321 años (2013-10-31 → 2021-02-25) |
| Tiempo medio observado | 2,72 años |

**Dos cautelas que el diseño obliga a declarar y que condicionan todo lo demás:**

1. **La censura es del 70,1 %.** La mayoría sigue en el sistema al cerrar la ventana,
   así que las curvas están dominadas por la censura y **la mediana de supervivencia
   casi nunca se alcanza** (§3). No es un defecto del estimador: es que el registro
   todavía no ha visto salir a esas personas.
2. **El 36,1 % de las personas aparece en una sola convocatoria** (10 871), de modo
   que su tiempo observado es `t = 0`; 4 581 de ellas con evento. Es una
   consecuencia inevitable de medir «desde la primera aparición»: quien fue
   reconocido una vez y no volvió tiene permanencia observada cero.

Se complementa con la **cohorte de 2013** (n = 8 016, 3 513 eventos), que no tiene
heterogeneidad de cohortes de entrada y es la misma base del 56,18 % de retención ya
publicado: **S(6,10 años) = 0,5618**, idéntico al 56,18 %, sin alcanzar el 0,5.

## 2. Lo que hubo que construir a mano

`lifelines` y `statsmodels` **no están instalados**, así que se implementaron:

- **Kaplan-Meier** con varianza de Greenwood e IC por transformación **log(−log)**,
  que se portan bien con S(t) pequeño (Kalbfleisch y Prentice, 1980).
- **Log-rank de k muestras** (Mantel-Cox) con matriz de covarianzas completa.
- **Cox de riesgos proporcionales** por máxima verosimilitud parcial con empates
  **Efron**, gradiente y hessiano analíticos, Newton-Raphson.

La corrección de Efron **no es opcional aquí**: los eventos solo pueden observarse
en las fechas de convocatoria (11 tiempos distintos), así que hay empates de miles
de casos. Breslow estaría sesgado.

**Validación (la prueba fuerte):** con una sola covariable binaria, el test de
**score** de Cox y el **log-rank** son el mismo contraste. Se comprueba dos veces:

| Comprobación | Resultado |
|---|---|
| Autotest sin empates (datos sintéticos) | χ² log-rank = **20,1953** · score de Cox = **20,1953** → idénticos |
| Base real, covariable género | χ² log-rank = **9,4435** · score de Cox = **9,3785** → diferencia relativa **0,69 %**, la esperable porque el log-rank usa Breslow y el Cox Efron |

Si esa diferencia fuera grande, la implementación estaría mal. No lo es.

## 3. Kaplan-Meier: la mediana casi nunca se alcanza

| Grupo | n | Eventos | Mediana |
|---|---:|---:|---|
| Investigador Junior | 20 677 | 7 307 | **5,14 años** |
| Investigador Asociado | 5 788 | 1 187 | **no alcanzada** |
| Investigador Sénior | 3 287 | 247 | **no alcanzada** |
| Investigador Emérito | 334 | 251 | **3,53 años** |
| Masculino | 18 228 | 5 441 | no alcanzada |
| Femenino | 11 849 | 3 551 | no alcanzada |
| Humanidades | 2 412 | 928 | **6,10 años** |
| No registra (gran área) | 564 | 303 | **0,00 años** |
| Bogotá, Antioquia, Valle, Atlántico, Santander, Resto | 9 813 · 4 981 · 2 503 · 1 878 · 1 565 · 9 346 | — | no alcanzada |

**La mediana no se alcanza en 16 de los 20 grupos** evaluados: más de la mitad de
sus integrantes siguen en el sistema al cerrar la ventana. Solo cuatro la alcanzan
(Junior 5,14; Emérito 3,53; Humanidades 6,10; «No registra» 0,00). Se reporta como
«no alcanzada», no se fuerza un número.

> **Nota sobre los tamaños de Bogotá y del stock (H4 de la auditoría cruzada).** En
> este análisis la unidad es la **persona en su última observación, sin filtrar**:
> 30 086 personas, y Bogotá tiene **9 813**. F2-2 usa otra definición —cada persona en
> su última convocatoria **con territorio colombiano**— y obtiene un stock de **28 950**
> con **9 888** en Bogotá. La diferencia son 194 personas cuya última observación es
> `Exterior` (173) o `No disponible` (21): F2-2 las sigue contando en su último
> departamento colombiano porque su salida del país no las saca del denominador
> departamental. **No hay un error de 75 personas: son dos universos distintos**, y cada
> documento debe citarse con el suyo. Con la definición de F2-2 el cociente de Bogotá
> sería 2,1005 y con esta 2,0986: las dos redondean a 2,10×.

> **Límite del intervalo de la mediana.** Con solo 11 tiempos de evento distintos,
> la mediana es una función escalonada y su IC degenera (los extremos caen en el
> mismo escalón) o no es informativo. Se reporta el **valor puntual**; el intervalo
> no aporta.

## 4. Log-rank: los cuatro desagregados discriminan

| Desagregación | χ² | gl | p |
|---|---:|---:|---:|
| Categoría | **2 940,20** | 3 | < 10⁻³⁰⁰ |
| Gran área | **985,26** | 6 | 1,4 × 10⁻²⁰⁹ |
| Departamento (top 5 + resto) | **113,57** | 5 | 7,2 × 10⁻²³ |
| Género | **9,44** | 1 | 2,1 × 10⁻³ |

Las cuatro diferencias son significativas. Pero el log-rank es **crudo**: no ajusta
por nada. El modelo de Cox es el que dice qué sobrevive al ajuste.

## 5. Modelo de Cox

n = 29 744 · 8 741 eventos · 14 covariables · convergió en **8 iteraciones**
(gradiente final 1,1 × 10⁻¹⁰). Referencias: Junior, Masculino, Ciencias Agrícolas,
Bogotá.

| Covariable | HR | IC 95 % | p |
|---|---:|---|---:|
| Categoría = Asociado | **0,376** | [0,353; 0,400] | < 10⁻³⁰⁰ |
| Categoría = Sénior | **0,105** | [0,093; 0,120] | < 10⁻³⁰⁰ |
| **Género = Femenino** | **0,988** | [0,946; 1,031] | **0,575** |
| Área = Ciencias Médicas | 0,821 | [0,734; 0,919] | 6,3 × 10⁻⁴ |
| Área = Ciencias Naturales | 0,944 | [0,849; 1,049] | 0,284 |
| Área = Ciencias Sociales | 1,071 | [0,967; 1,187] | 0,187 |
| Área = Humanidades | 1,217 | [1,084; 1,367] | 9,1 × 10⁻⁴ |
| Área = Ingeniería y Tecnología | 0,816 | [0,731; 0,912] | 3,3 × 10⁻⁴ |
| Área = No registra | **3,647** | [3,142; 4,233] | < 10⁻³⁰⁰ |
| Depto = Antioquia | 0,889 | [0,835; 0,947] | 2,7 × 10⁻⁴ |
| Depto = Valle del Cauca | 0,990 | [0,915; 1,071] | 0,801 |
| Depto = Atlántico | 0,729 | [0,655; 0,811] | 6,3 × 10⁻⁹ |
| Depto = Santander | 0,913 | [0,821; 1,015] | 0,091 |
| Depto = Resto | 0,914 | [0,867; 0,963] | 7,6 × 10⁻⁴ |

### El hallazgo que más importa: el género desaparece al ajustar

El log-rank daba **p = 0,0021** para el género. Al ajustar por categoría, área y
departamento, el hazard ratio queda en **0,988 [0,946; 1,031] con p = 0,575**: la
diferencia cruda **no es un efecto del género sino de su composición**.

**El mecanismo, con las cifras.** Una proporción mayor de mujeres que de hombres se
ubica en la categoría **Junior** —**72,4 %** de ellas frente al **66,4 %** de ellos— y
una menor en **Sénior** (8,0 % frente al 12,8 %). Y Junior es justamente la categoría
de **menor** permanencia: S final **0,430** frente a **0,917** de Sénior. Por eso la
curva cruda de las mujeres sale algo peor (0,559 frente a 0,583 a los 6,10 años) sin
que el género tenga nada que ver: están más concentradas en el grupo que más sale. Al
comparar **dentro de la misma categoría y la misma área**, la diferencia se anula, y
eso es lo que dice el HR ajustado de 0,988 con un intervalo que contiene el 1.

> **Corrección (auditoría cruzada, H2).** Una versión anterior de este párrafo decía
> que las mujeres están «más concentradas en áreas y categorías con **mayor**
> permanencia». Era al revés: están en la de **menor**. El razonamiento se sostiene
> igual —la diferencia cruda es de composición— pero la dirección del mecanismo es la
> que se describe arriba.

Esto es coherente con lo que ya habíamos encontrado por otras tres vías: el género
explica el **0,11 %** de la varianza de la retención (EDA), **no aporta nada** a la
segmentación (V de Cramér 0,006, F2-6) y su representación territorial no muestra
patrón propio (F2-5). **Cuatro análisis independientes coinciden en que el género no
es un eje estructurante de este registro.**

### La categoría domina, y en el sentido esperado

Un Sénior tiene el **10,5 % del riesgo de salir** de un Junior, y un Asociado el
37,6 %. Es el gradiente de carrera esperado: cuanto más consolidada la categoría,
más probable seguir siendo reconocido.

### Emérito: excluido con razón, y comprobado

Los **334 eméritos (1,1 %)** se grafican pero **no entran en el modelo**, y no solo
por tamaño: **Emérito es una categoría terminal por selección** —solo se llega a
ella habiendo sobrevivido, y **251 de sus 334 personas no vuelven a aparecer**—,
así que su hazard ratio mediría tiempo inmortal, no riesgo.

Se comprobó que excluirlos no sesga el resto: agrupándolos con Sénior (que es lo que
el proyecto ya hace en la post-estratificación), el cambio máximo en un HR es de
**0,091** —y ese 0,091 es precisamente el de Sénior, que absorbe a los eméritos—;
**todos los demás coeficientes se mueven menos de 0,011**.

Género: las 9 personas con `Intersexual` (5) o `No disponible` (4) no permiten
estimar nada; se informan y se excluyen. Ninguna de ellas registra el evento.

## 6. Un error que casi invalida el modelo, y cómo se detectó

El Cox no convergía: 100 iteraciones, gradiente 1,19 × 10³ y hazard ratios de 10⁴⁹.
Antes de suponer nada, lo diagnosticé:

1. El hessiano tenía **autovalor mínimo 1,7 × 10⁻¹³** con condicionamiento 1,7 × 10¹⁶:
   una dirección **sin información**.
2. El autovector de ese autovalor cargaba **+1,0 en los cinco dummies de
   departamento** y 0 en el resto, y el gradiente en esa dirección era 2,5 × 10⁻¹².
3. Eso solo ocurre si **ninguna persona está en el nivel de referencia**: al faltar
   Bogotá, la suma de los dummies vale 1 para todos y la dirección «subir todos los
   coeficientes de departamento» es un desplazamiento constante, que el modelo de Cox
   no identifica.

La causa: el nombre real en los datos es **`'Bogotá, D. C.'` con coma**, y el script
lo tenía escrito como `'Bogotá  D. C.'` con dos espacios. Bogotá entera (9 813
personas) caía en «Resto», la curva por departamentos **no tenía Bogotá** y el modelo
se quedaba sin referencia.

**Corregido de raíz**: los cinco departamentos **se derivan de los datos** con
`value_counts().head(5)`, no se escriben a mano, y hay una validación
(`nivel_de_referencia_con_casos`) que falla si el nivel de referencia no tiene casos.
Pasa de 100 iteraciones divergentes a **8 iteraciones con gradiente 10⁻¹⁰**.

Además se corrigió un segundo error del mismo origen: se había incluido una columna
de constantes, y **en el modelo de Cox el intercepto no es identificable** (su
gradiente es idénticamente cero).

## 7. Respuesta al anteproyecto

El anteproyecto prometía analizar la «dinámica longitudinal con censura» frente a la
ruta de Markov que ya existía. Ahora está hecho y dice tres cosas:

1. **La permanencia es larga y no se puede medir completa**: con 7,3 años de ventana
   y 70 % de censura, más de la mitad de casi todos los grupos sigue dentro al
   cerrarse el registro. Se alcanzan cuatro medianas (§3), pero **la única
   interpretable como permanencia típica es la de los Junior (5,14 años)**, coherente
   con que son el grupo de mayor rotación. Las otras tres no lo son por motivos
   distintos: la de **Emérito (3,53)** describe una categoría terminal por selección,
   la de **Humanidades (6,10)** cae en el borde mismo de la ventana y se apoya en el
   último tramo de la curva, y la de **«No registra» (0,00 años)** es degenerada
   —significa que más de la mitad del grupo sale en su primera convocatoria—, no una
   permanencia de cero.
2. **La categoría es el eje que estructura la permanencia** (Sénior 0,105 frente a
   Junior; log-rank χ² = 2 940), seguida del área y, muy detrás, del departamento.
3. **El género no estructura nada en este registro**, y ahora con una prueba que
   ajusta por lo demás, no solo con una comparación cruda.

## 8. Límites

- **70 % de censura**: las curvas describen bien el tramo observado, pero no el
  destino final de quien sigue dentro.
- **Riesgos proporcionales no verificados.** No se contrastó el supuesto (residuos de
  Schoenfeld): implementarlo excede lo razonable aquí y se declara pendiente. Si el
  efecto de la categoría cambia con el tiempo, los HR son un promedio.
- **11 tiempos de evento distintos.** El registro solo observa en las fechas de
  convocatoria, así que la escala temporal es discreta; Cox con Efron es una
  aproximación razonable, no exacta.
- **Los atributos son los de la ÚLTIMA observación.** Un Sénior que fue Junior la
  mayor parte de su trayectoria cuenta como Sénior; la covariable cambia en 8 755
  personas a lo largo del tiempo y no es invariante, cosa que el modelo de riesgos
  proporcionales con covariables fijas no recoge (haría falta un modelo con
  covariables dependientes del tiempo).
- **«Salida» es «no vuelve a aparecer en el registro»**: incluye a quien se saltó la
  última convocatoria y volvería en la siguiente, que aquí no se observa.
- **No se ajusta por periodo calendario**, porque el tiempo se mide desde la entrada
  de cada persona y conviven cohortes de 2013 a 2021.

## 9. Reproducir

```bash
python documentacion_auditoria/src/supervivencia.py
```

Entrada: el CSV fuente versionado. **No necesita red.** Salidas: el JSON con todas
las curvas y los coeficientes, el CSV de personas con su tiempo y su evento, el CSV
del modelo de Cox y las cinco figuras.

| Figura | Contenido |
|---|---|
| `f2_10_km_categoria.png` | Supervivencia por categoría |
| `f2_10_km_genero.png` | Supervivencia por género |
| `f2_10_km_area.png` | Supervivencia por gran área |
| `f2_10_km_departamento.png` | Supervivencia por departamento (top 5 + resto) |
| `f2_10_cox_forest.png` | Hazard ratios con IC 95 %; en azul los que excluyen el 1 |
