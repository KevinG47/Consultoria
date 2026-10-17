# Evidencia - Tarea 1: Tracking longitudinal de investigadores

## Objetivo

Realizar el seguimiento longitudinal de los investigadores entre convocatorias usando la variable `ID_PERSONA_PR`, con el fin de identificar cuántos investigadores:

- suben de categoría,
- se mantienen,
- bajan,
- o desaparecen de la convocatoria siguiente.

## Base utilizada

Se utilizó el archivo consolidado:

`datos/tarea_join/investigadores_consolidado.csv`

## Variables utilizadas

Las variables principales para esta tarea fueron:

- `ID_PERSONA_PR`: identificador único del investigador.
- `ANO_CONVO`: fecha de la convocatoria, transformada posteriormente al año de convocatoria.
- `NME_CLASIFICACION_PR`: nombre de la categoría del investigador.
- `ORDEN_CLAS_PR`: orden original de clasificación.

## Preparación de la base

Se realizaron los siguientes pasos previos al análisis:

1. Conversión de `ANO_CONVO` desde formato fecha a año.
2. Normalización de categorías en cuatro niveles:
   - Junior
   - Asociado
   - Senior
   - Emérito
3. Construcción de una variable de jerarquía ordinal:
   - Junior = 1
   - Asociado = 2
   - Senior = 3
   - Emérito = 4
4. Verificación de duplicados por `ID_PERSONA_PR` y `anio`.

La revisión mostró que no existen duplicados por investigador y año en la base analítica, por lo que el seguimiento longitudinal puede realizarse sin problemas de sobreconteo.

## Periodos analizados

Se compararon dos pares de convocatorias consecutivas:

- 2017 → 2019
- 2019 → 2021

## Criterio de clasificación longitudinal

Para cada investigador se asignó uno de los siguientes resultados:

- **Sube**: la categoría final es superior a la inicial.
- **Se mantiene**: la categoría final es igual a la inicial.
- **Baja**: la categoría final es inferior a la inicial.
- **Desaparece**: el investigador está en la convocatoria inicial pero no aparece en la siguiente.

## Cuadro resumen de resultados

| Periodo      | Total inicial | Se mantiene | % Se mantiene | Sube | % Sube | Baja | % Baja | Desaparece | % Desaparece |
|--------------|--------------:|------------:|--------------:|-----:|--------:|-----:|--------:|------------:|--------------:|
| 2017 - 2019  | 13001         | 7018        | 53.98%        | 2246 | 17.28%  | 730  | 5.61%   | 3007        | 23.13%        |
| 2019 - 2021  | 16796         | 9657        | 57.50%        | 2336 | 13.91%  | 1362 | 8.11%   | 3441        | 20.49%        |

## Lectura rápida de resultados

- La situación más frecuente en ambos periodos es **permanecer en la misma categoría**.
- En ambos periodos, los **ascensos superan a los descensos**.
- También se observa una proporción importante de investigadores que **desaparecen** en la convocatoria siguiente.
- Entre 2019 y 2021 aumentó el número absoluto de ascensos y desapariciones frente al periodo 2017 - 2019, aunque porcentualmente la movilidad ascendente perdió peso relativo.

## Resultados agregados

### Periodo 2017 - 2019

- Se mantiene: 7018
- Desaparece: 3007
- Sube: 2246
- Baja: 730

Total de investigadores observados en 2017: 13001

Porcentajes:

- Se mantiene: 53.98%
- Desaparece: 23.13%
- Sube: 17.28%
- Baja: 5.61%

### Periodo 2019 - 2021

- Se mantiene: 9657
- Desaparece: 3441
- Sube: 2336
- Baja: 1362

Total de investigadores observados en 2019: 16796

Porcentajes:

- Se mantiene: 57.50%
- Desaparece: 20.49%
- Sube: 13.91%
- Baja: 8.11%

## Resultados por categoría inicial

### Tracking por categoría 2017 - 2019

| Categoría inicial | Se mantiene | Sube | Baja | Desaparece |
|-------------------|------------:|-----:|-----:|-----------:|
| Junior            | 3797        | 1478 | 0    | 2300       |
| Asociado          | 1793        | 739  | 558  | 505        |
| Senior            | 1428        | 29   | 172  | 78         |
| Emérito           | 0           | 0    | 0    | 124        |

### Tracking por categoría 2019 - 2021

| Categoría inicial | Se mantiene | Sube | Baja | Desaparece |
|-------------------|------------:|-----:|-----:|-----------:|
| Junior            | 5558        | 1574 | 0    | 2789       |
| Asociado          | 2171        | 717  | 960  | 501        |
| Senior            | 1928        | 45   | 402  | 98         |
| Emérito           | 0           | 0    | 0    | 53         |

## Interpretación

El análisis longitudinal muestra que la situación más frecuente entre convocatorias es permanecer en la misma categoría. En ambos periodos, la permanencia supera el 50% del total de investigadores observados.

La segunda dinámica más relevante es la desaparición del investigador en la convocatoria siguiente, lo cual representa una proporción importante del panel longitudinal.

También se observa que los ascensos superan a los descensos en ambos periodos. Sin embargo, entre 2019 y 2021 la movilidad ascendente pierde fuerza relativa y la movilidad descendente aumenta frente al periodo 2017 - 2019.

Por categorías, Senior presenta mayor estabilidad relativa, mientras que Asociado se comporta como una categoría intermedia con movilidad tanto ascendente como descendente. La categoría Junior presenta alta permanencia y una fracción importante de ascenso hacia Asociado.

Un hallazgo adicional es que todos los investigadores clasificados como Emérito en el periodo inicial desaparecen en la convocatoria siguiente.

## Archivos de soporte generados

- `resumen_tracking_2017_2019.csv`
- `resumen_tracking_2019_2021.csv`
- `tracking_por_categoria_2017_2019.csv`
- `tracking_por_categoria_2019_2021.csv`

## Conclusión

La tarea de tracking longitudinal permitió cuantificar la permanencia, la movilidad y la desaparición de los investigadores entre convocatorias. Los resultados muestran una estructura con alta permanencia, movilidad ascendente moderada y una proporción importante de salida del panel entre periodos consecutivos.