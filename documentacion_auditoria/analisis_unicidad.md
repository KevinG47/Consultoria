# Regla de unicidad de IDs: formalización y validación (F2-7)

**Objetivo que cierra:** OE3 del repositorio auditado — «verificar la unicidad de
identificadores mediante reglas».
**Artefactos:** `documentacion_auditoria/data/validacion/regla_unicidad.yaml` (la
regla) · `documentacion_auditoria/src/validar_unicidad.py` (el validador) ·
`data/memoria/validacion_unicidad.json` · `data/memoria/ids_no_unicos.csv` (56 IDs) ·
`data/memoria/graficas_unicidad/` (2 figuras).

## 1. La regla: lo que el auditado documenta y lo que implementa

**Documentada** (`informe_final.md:130`, §5.2):

> «Se estableció la regla práctica: si la diferencia de edad entre dos registros
> coincide con el lapso temporal entre convocatorias (±4 año tolerancia para errores
> de digitación) y al menos una otra variable coincide (genero), se acepta unicidad
> del ID. Los casos con conflicto quedaron marcados para revisión manual.»

**Implementada** (`arreglar_base_consultoria_7.R:96-101`):

```r
mutate(dif_edad = EDAD_ANOS_PR - dplyr::lag(EDAD_ANOS_PR))
...
filter(dif_edad > 4.1)
```

**No son la misma regla, y la diferencia importa.**

| | Documentada | Implementada |
|---|---|---|
| Referencia | el lapso entre convocatorias | ninguna: umbral fijo de 4,1 años |
| Dirección | simétrica (valor absoluto) | **una sola cola** (`> 4.1`) |
| Género | se exige que coincida | se selecciona la columna pero **no se comprueba** |

El efecto está medido en §5: la implementación marca **1 067 pares** donde la
documentada marca **18**, y **no detecta ninguno de los 6 casos en los que la edad
retrocede**.

## 2. La regla formalizada

`data/validacion/regla_unicidad.yaml` es la **fuente de verdad**: el validador no
tiene ninguna regla escrita en el código, solo sabe aplicar los tipos de criterio que
el YAML declara, y **aborta** si el YAML pide uno que no conoce.

```yaml
clave: ID_PERSONA_PR
alcance: {fuente: …datos_fuente/…csv, granularidad: persona x convocatoria,
          comparacion: pares_consecutivos}
criterios:
  - nombre: coherencia_de_edad
    formula: residuo = (edad_b - edad_a) - (fecha_b - fecha_a en años)
    tolerancia_anios: 4.0
    simetrica: true
  - nombre: coherencia_de_genero
    variable: NME_GENERO_PR
    exigir: igualdad
```

**Tres decisiones, cada una justificada en el propio YAML:**

1. **La referencia es el lapso real entre convocatorias**, no un umbral fijo. Las seis
   convocatorias no están igualmente espaciadas: entre 2013 y 2019 median **6,1 años**,
   así que alguien puede envejecer legítimamente 6 años. Un umbral fijo ignora eso.
2. **La tolerancia es simétrica.** Una resta se juzga en valor absoluto: una edad que
   *decrece* 98 años es tan imposible como una que crece 98.
3. **Se conserva el ±4 años que el equipo declaró**, para que la formalización sea
   comparable con lo que quiso hacer. Es una tolerancia **generosa**: el residuo
   observado tiene desviación típica de 0,90 años, así que ±4 son unas 4,4
   desviaciones. La sensibilidad a umbrales más estrictos se reporta en §6.

## 3. Resultados

La regla se aplica a los **19 215 IDs con más de un registro** (de 30 086), que
forman **47 151 pares consecutivos**.

| | |
|---|---:|
| Pares que incumplen la coherencia de edad | **18** |
| Pares que incumplen la coherencia de género | **43** |
| **IDs que incumplen la regla completa** | **56** |
| Porcentaje del padrón | **0,186 %** |

Por tipo: **41** incumplen solo el género, **14** solo la edad y **1** ambas.

**Pero no son el mismo hallazgo**, y conviene separarlos por su rol:

| Rol | IDs | Qué significa |
|---|---:|---|
| **Comprometen la identidad** (falla la edad) | **15** | La trayectoria es imposible: el ID puede estar designando a dos personas |
| **Atributo inestable** (falla solo el género) | **41** | Es la inestabilidad que el EDA ya documentó (42 personas cambian de género); no prueba que el ID sea compartido |

## 4. Los 15 IDs que comprometen la identidad

| ID | Par | Edad | Lapso | Residuo |
|---|---|---|---:|---:|
| `0000671819` | 2015→2017 | 115,51 → 16,92 | 1,57 | **−100,16** |
| `0000034380` | 2015→2017 | **−1,13** → 69,28 | 1,57 | **+68,84** |
| `0000281670` | 2014→2015 | 0,57 → 41,91 | 1,00 | +40,34 |
| `0000217271` | 2015→2017 | 77,16 → 50,59 | 1,57 | −28,14 |
| `0000671827` | 2017→2019 | 16,92 → 45,33 | 2,57 | +25,84 |
| `0001430632` | 2017→2019 | 35,08 → 59,58 | 2,57 | +21,93 |
| `0000908240` | 2017→2019 | 36,93 → 23,00 | 2,57 | −16,50 |
| `0001378646` | 2017→2019 | 63,11 → 51,08 | 2,57 | −14,60 |
| `0001434533` | 2017→2019 | 38,91 → 54,00 | 2,57 | +12,52 |
| `0001626437` | 2019→2021 | 26,33 → 38,33 | 1,22 | +10,78 |
| `0000549240` | 2013→2015 | 38,23 → 31,70 | 1,95 | −8,48 |
| `0001499639` | 2017→2019 | 46,05 → 55,33 | 2,57 | +6,71 |
| `0001464090` | 2017→2019 | 73,01 → 70,08 | 2,57 | −5,50 |
| `0000071381` | 2019→2021 | 41,50 → 38,08 | 1,22 | −4,64 |
| `0000444499` | 2013→2021 | 43,05 → 46,00 | 7,32 | −4,37 |

Los cuatro primeros no admiten discusión: una edad de **−1,13 años**, una de
**0,57 años** en un investigador reconocido y una caída de **100 años** entre dos
convocatorias separadas por 19 meses. Los cuatro últimos son casos frontera que caen
apenas fuera del ±4.

## 5. Documentada frente a implementada: 1 058 falsos positivos y 9 falsos negativos

| | Pares |
|---|---:|
| Marca la regla **documentada** | **18** |
| Marca la regla **implementada** (`dif_edad > 4.1`) | **1 067** |
| Falsos positivos de la implementada | **1 058** |
| Falsos negativos de la implementada | **9** |

**Por qué 1 058 falsos positivos.** El filtro no mira el lapso: marca a cualquiera
cuya edad crezca más de 4,1 años entre dos registros consecutivos. Si una persona
aparece en 2013 y en 2019, envejeció **6,1 años legítimamente** y el filtro la marca.
Con huecos de hasta 7,3 años, eso ocurre en más de mil casos.

**Por qué 9 falsos negativos.** Al ser de una sola cola, `> 4.1` solo ve los
aumentos: **ninguno de los 6 pares en los que la edad retrocede más de 4 años** queda
marcado, y son precisamente los más graves.

**El caso que resume todo** —el ID `0000671819`— tiene tres pares consecutivos:

| Par | Δedad | Residuo |
|---|---:|---:|
| 2015→2017 | **−98,59** | −100,16 |
| 2017→2019 | +40,33 | +37,76 |
| 2019→2021 | +2,00 | +0,78 |

El analista del auditado **revisó ese ID** y anotó «40.3» en el comentario del script
(`arreglar_base_consultoria_7.R:113`): vio el salto positivo de 2017→2019 y **no vio
la caída de 98 años de 2015→2017**, que el filtro de una cola descartaba.

## 6. Validación contra los juicios del propio analista

El script R deja escritos los IDs que revisó y la diferencia de edad que observó. Es
un patrón de oro imperfecto pero real, y la regla formalizada **coincide con él**:

| | |
|---|---:|
| IDs revisados por el analista | 8 |
| Diferencias de edad que se reproducen | **7 de 8** |
| De los que él marcó, la regla también los marca | **6 de 6** |

El único desajuste es el de §5, y no es un error del cálculo: el analista anotó la
diferencia de un par y la regla reporta el par de mayor residuo del mismo ID, que es
el que él no vio. Los dos casos que revisó y **no** marcó (4,98 y 5,03 años) son
huecos de más de dos años, así que su residuo cae dentro de la tolerancia: la regla
los acepta igual que él.

## 7. Sensibilidad a la tolerancia

| Tolerancia | ±0,5 | ±1 | ±2 | ±2,5 | ±3 | **±4** | ±5 | ±7,5 | ±10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pares marcados | 23 283 | 315 | 23 | 21 | 18 | **18** | 16 | 14 | **13** |

Dos lecturas:

- **Entre ±3 y ±4 el resultado no cambia** (18 pares). El valor declarado no está en
  una zona de borde donde la cifra baile.
- **Con ±10 años todavía quedan 13 violaciones.** Es decir, hay un **núcleo de 13
  trayectorias imposibles para cualquier tolerancia razonable**; las otras 5 dependen
  del umbral elegido.

El umbral es una decisión del equipo y **no se cambia aquí**: se reporta su efecto.

## 8. Impacto en los análisis

| | Con los 56 IDs | Sin ellos | Δ |
|---|---:|---:|---:|
| Registros | 77 237 | 77 034 | −203 (0,263 %) |
| Pares consecutivos | 47 151 | 47 004 | −147 (0,312 %) |
| Retención 2013→2021 | 56,175 % | 56,127 % | **−0,049 pp** |
| Edad media | 44,8387 | 44,8380 | −0,0008 |

**El impacto en las cifras agregadas es despreciable, y eso es parte del resultado.**
Ninguna conclusión del proyecto cambia: ni la retención, ni la edad media, ni las
tasas por departamento de F2-2. Lo que la regla aporta no es corregir un número, es:

1. **Identificar las 15 trayectorias individuales que no son usables** — y que hoy se
   están usando en cualquier análisis que trate el ID como una persona.
2. **Demostrar que la regla que el auditado implementó habría señalado a 1 058
   personas válidas** y habría dejado pasar los 6 casos más graves, incluido el de
   −100 años.
3. **Dejar una regla ejecutable**: el validador se corre en segundos y emite un
   veredicto por ID, así que cualquier análisis futuro puede declarar qué hizo con
   los IDs marcados en vez de asumir que todos son únicos.

## 9. Límites

- **La regla no prueba la identidad, solo la coherencia.** Dos personas distintas con
  edades compatibles y el mismo género no se detectan; el registro no trae nombre ni
  documento que lo permita. La única vía sería un *record linkage* con una fuente
  externa, que este proyecto no tiene.
- **La tolerancia de ±4 años es una decisión, no un resultado.** Absorbe errores de
  redondeo y digitación, pero también absorbería una colisión entre dos personas de
  edad parecida.
- **El género no es un atributo fiable en este registro** (cambia en 42 personas), así
  que exigirlo literalmente —como hace la regla documentada— produce 41 de los 56
  marcados por una razón que no es de identidad. Se reportan separados por rol
  justamente por eso.
- **Los pares se comparan solo entre registros consecutivos.** Es lo que hace el
  código del auditado y basta para detectar una trayectoria incoherente, pero no
  exploraría un error que se cancelara entre pares.

## 10. Reproducir

```bash
python documentacion_auditoria/src/validar_unicidad.py
# o con otra regla:
python documentacion_auditoria/src/validar_unicidad.py --regla ruta/al.yaml
```

Entrada: el CSV fuente versionado y el YAML de la regla. **No necesita red.** Salidas:
el JSON con el detalle de los 56 IDs, el CSV de IDs marcados con su estado y las dos
figuras.

| Figura | Contenido |
|---|---|
| `f2_7_residuos_edad.png` | Residuo de cada par (escala simlogarítmica); en rojo, las violaciones |
| `f2_7_sensibilidad.png` | Pares marcados según la tolerancia, frente a la regla implementada |
