# Evidencia - Tarea 2: Probabilidades de transición entre categorías

## Objetivo

Calcular las probabilidades de transición entre categorías de investigadores entre convocatorias consecutivas, considerando las categorías:

- Junior
- Asociado
- Senior
- Emérito

## Base utilizada

Se utilizó el archivo consolidado:

`datos/tarea_join/investigadores_consolidado.csv`

## Variables utilizadas

Las variables principales para esta tarea fueron:

- `ID_PERSONA_PR`
- `ANO_CONVO`
- `NME_CLASIFICACION_PR`
- `ORDEN_CLAS_PR`

## Preparación de la base

Previo al cálculo de matrices de transición se realizaron los siguientes pasos:

1. Conversión de la fecha de convocatoria al año de convocatoria.
2. Normalización de categorías en cuatro niveles:
   - Junior
   - Asociado
   - Senior
   - Emérito
3. Definición de un orden jerárquico manual:
   - Junior = 1
   - Asociado = 2
   - Senior = 3
   - Emérito = 4
4. Verificación de unicidad por investigador y año.

## Definición de transición

Se compararon las categorías de cada investigador entre convocatorias consecutivas:

- 2017 → 2019
- 2019 → 2021

Se construyeron dos tipos de matrices:

1. **Matriz observada entre categorías**, usando únicamente investigadores que aparecen en ambas convocatorias.
2. **Matriz extendida**, incorporando el estado `Desaparece`, para capturar la salida del panel.

## Cuadro resumen de probabilidades de transición

| Categoría inicial | Periodo      | Permanencia en la misma categoría | Principal transición alternativa |
|-------------------|--------------|----------------------------------:|----------------------------------|
| Junior            | 2017 - 2019  | 71.98%                            | Junior → Asociado: 24.32%        |
| Junior            | 2019 - 2021  | 77.93%                            | Junior → Asociado: 17.89%        |
| Asociado          | 2017 - 2019  | 58.03%                            | Asociado → Senior: 23.50%        |
| Asociado          | 2019 - 2021  | 56.42%                            | Asociado → Junior: 24.95%        |
| Senior            | 2017 - 2019  | 87.66%                            | Senior → Asociado: 5.59%         |
| Senior            | 2019 - 2021  | 81.18%                            | Senior → Asociado: 13.22%        |

## Lectura rápida de resultados

- La permanencia en la misma categoría es el resultado más frecuente en ambos periodos.
- **Senior** es la categoría más estable en los dos periodos analizados.
- **Junior** muestra alta permanencia, pero su transición más frecuente es hacia **Asociado**.
- **Asociado** es la categoría con mayor dinamismo relativo, ya que presenta movilidad tanto ascendente como descendente.
- La transición hacia **Emérito** existe, pero es poco frecuente.

---

## 1. Matriz observada entre categorías

### Conteos 2017 - 2019

- Asociado → Asociado: 1793
- Asociado → Senior: 726
- Asociado → Junior: 558
- Asociado → Emérito: 13

- Junior → Junior: 3797
- Junior → Asociado: 1283
- Junior → Senior: 192
- Junior → Emérito: 3

- Senior → Senior: 1428
- Senior → Asociado: 91
- Senior → Junior: 81
- Senior → Emérito: 29

### Probabilidades 2017 - 2019

#### Desde Junior
- Junior → Junior: 0.7198
- Junior → Asociado: 0.2432
- Junior → Senior: 0.0364
- Junior → Emérito: 0.0006

#### Desde Asociado
- Asociado → Asociado: 0.5803
- Asociado → Senior: 0.2350
- Asociado → Junior: 0.1806
- Asociado → Emérito: 0.0042

#### Desde Senior
- Senior → Senior: 0.8766
- Senior → Asociado: 0.0559
- Senior → Junior: 0.0497
- Senior → Emérito: 0.0178

---

### Conteos 2019 - 2021

- Asociado → Asociado: 2171
- Asociado → Senior: 701
- Asociado → Junior: 960
- Asociado → Emérito: 16

- Junior → Junior: 5558
- Junior → Asociado: 1276
- Junior → Senior: 291
- Junior → Emérito: 7

- Senior → Senior: 1928
- Senior → Asociado: 314
- Senior → Junior: 88
- Senior → Emérito: 45

### Probabilidades 2019 - 2021

#### Desde Junior
- Junior → Junior: 0.7793
- Junior → Asociado: 0.1789
- Junior → Senior: 0.0408
- Junior → Emérito: 0.0010

#### Desde Asociado
- Asociado → Asociado: 0.5642
- Asociado → Senior: 0.1822
- Asociado → Junior: 0.2495
- Asociado → Emérito: 0.0042

#### Desde Senior
- Senior → Senior: 0.8118
- Senior → Asociado: 0.1322
- Senior → Junior: 0.0371
- Senior → Emérito: 0.0189

---

## 2. Comportamiento de la categoría Emérito

La categoría Emérito sí está presente en la base:

- 2017: 124 investigadores
- 2019: 53 investigadores
- 2021: 83 investigadores

Sin embargo, no aparece como estado inicial en la matriz observada entre categorías. Esto no corresponde a un error de la base ni del código.

La razón es que la matriz observada se construyó únicamente con investigadores presentes en ambas convocatorias consecutivas. En el emparejamiento longitudinal se encontró lo siguiente:

- Todos los investigadores clasificados como Emérito en 2017 desaparecen en 2019.
- Todos los investigadores clasificados como Emérito en 2019 desaparecen en 2021.

Por tanto, la ausencia de la fila Emérito en la matriz observada significa que no existe continuidad longitudinal de ese estado entre convocatorias consecutivas dentro del panel emparejado por `ID_PERSONA_PR`.

## Cuadro resumen del comportamiento de Emérito

| Periodo comparado | Resultado observado |
|-------------------|--------------------|
| 2017 - 2019       | Todos los Emérito desaparecen en la siguiente convocatoria |
| 2019 - 2021       | Todos los Emérito desaparecen en la siguiente convocatoria |
| Interpretación    | Emérito no aparece como fila inicial en la matriz observada porque no hay continuidad longitudinal en el panel emparejado |

---

## 3. Matriz extendida con estado `Desaparece`

Para representar de manera completa el proceso longitudinal, se construyó adicionalmente una matriz extendida en la que los investigadores ausentes en la convocatoria final se codifican como `Desaparece`.

Esta matriz permite modelar tanto:

- la transición entre categorías observadas,
- como la salida del panel entre convocatorias.

En esta representación, la categoría Emérito sí queda incorporada correctamente, ya que su transición empírica corresponde a:

- Emérito → Desaparece = 1

en ambos periodos analizados.

---

## Interpretación

Las matrices de transición muestran que la permanencia en la misma categoría es el resultado más frecuente entre convocatorias.

La categoría **Senior** presenta la mayor estabilidad en ambos periodos, con probabilidades de permanencia de 87.66% entre 2017 y 2019, y de 81.18% entre 2019 y 2021.

La categoría **Junior** presenta una alta permanencia, aunque su principal transición ascendente ocurre hacia **Asociado**. Entre 2019 y 2021 aumenta la permanencia en Junior y disminuye la probabilidad de ascenso a Asociado frente al periodo anterior.

La categoría **Asociado** funciona como una categoría intermedia, con movilidad en ambas direcciones: puede ascender a Senior o descender a Junior. Esto la convierte en el estado con mayor dinamismo relativo.

La transición hacia **Emérito** existe, pero es poco frecuente en ambos periodos.

## Archivos de soporte generados

- `matriz_transicion_2017_2019.csv`
- `matriz_transicion_2019_2021.csv`
- `matriz_probabilidades_2017_2019.csv`
- `matriz_probabilidades_2019_2021.csv`
- `matriz_transicion_extendida_2017_2019.csv`
- `matriz_transicion_extendida_2019_2021.csv`
- `matriz_probabilidades_extendida_2017_2019.csv`
- `matriz_probabilidades_extendida_2019_2021.csv`

## Conclusión

El análisis de probabilidades de transición muestra que la movilidad entre categorías existe, pero está dominada por la permanencia en el mismo estado. Senior es la categoría más estable, Junior presenta alta permanencia con opción de ascenso a Asociado, y Asociado concentra movilidad tanto ascendente como descendente.

La categoría Emérito sí existe en la base, pero no presenta continuidad entre periodos consecutivos en el panel longitudinal, por lo que su comportamiento se interpreta adecuadamente en la matriz extendida con el estado `Desaparece`.