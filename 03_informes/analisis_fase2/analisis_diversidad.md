# Diversidad con intervalos de confianza y cobertura por convocatoria (F2-5)

**Pregunta que cierra:** Q6 del repositorio auditado — «¿qué tan diversos son los
investigadores reconocidos frente a la población colombiana?».
**Artefactos:** `documentacion_auditoria/src/diversidad_inferencia.py` ·
`01_datos/resultados_json/diversidad_inferencia.json` · `data/memoria/graficas_diversidad/`
(2 figuras) · entrada **E7** de `04_auditoria/ERRATA.md`.

## 1. Qué añade sobre lo que ya existía

El repositorio auditado calcula la subrepresentación con `comparar_dane()`, que
devuelve un número puntual redondeado a un decimal: «afro 3,0×», «indígena 7,9×».
Con 453 y 114 personas sobre 20 423 respuestas, esos números tienen un intervalo
que **nadie había calculado**. Este análisis lo calcula en tres piezas:

1. **IC de Wilson** al 95 % para la proporción, sobre las respuestas conocidas de
   2021. Se prefiere a Wald porque con 0,03 % (rrom) Wald produce extremos
   negativos.
2. **Bootstrap de diseño** sobre la muestra MAS (n = 2 224; 1 554 observaciones en
   2021) con la post-estratificación por categoría del resto del proyecto.
   Remuestrea el universo **completo** de 2021 —conocidas y no conocidas—, porque
   el denominador «respuestas conocidas» también se estima; fijarlo
   subestimaría la incertidumbre.
3. **IC del cociente** r = DANE / p, transformando los extremos del IC de p: como
   la referencia es fija, r decrece con p y el intervalo es [d/p_sup, d/p_inf].

Se reproduce además, sin margen de error, la evidencia que el auditado ya tenía
versionada: los `n`, los porcentajes y las razones coinciden **exactamente** con
`diversidad_comparacion_dane.csv` (diferencia 0 en las tres comprobaciones), y la
cobertura coincide con `diversidad_cobertura_por_convocatoria.csv` dentro de
0,001 pp.

## 2. La cobertura manda: esto es una foto de 2021, no una serie

| Convocatoria | Registros | Grupo étnico | Discapacidad | Víctima | Género |
|---|---:|---:|---:|---:|---:|
| 2013 | 8 016 | **0,00 %** | **0,00 %** | **0,00 %** | 100 % |
| 2014 | 8 280 | **0,00 %** | **0,00 %** | **0,00 %** | 100 % |
| 2015 | 10 050 | **0,00 %** | **0,00 %** | **0,00 %** | 100 % |
| 2017 | 13 001 | **0,00 %** | **0,00 %** | **0,00 %** | 100 % |
| 2019 | 16 796 | **0,00 %** | **0,00 %** | **0,00 %** | 100 % |
| 2021 | 21 094 | 96,82 % | 96,81 % | 96,82 % | 99,98 % |

Las tres variables de diversidad **solo existen en 2021**. No es un defecto de
este análisis: es una restricción del registro, y condiciona qué puede afirmarse.
**La comparación con DANE es una fotografía de 2021, no una serie temporal**: con
este registro no puede hablarse de evolución de la diversidad, solo de su estado
en la última convocatoria. El género sí está capturado en las seis, y por eso ese
análisis sí admite serie.

Un detalle que importa para no falsear la cobertura: `ID_VICTIMA_CONFLICTO` usa
`No registra` como nulo, igual que las otras dos usan `No disponible`. **«No
registra» no significa «no es víctima»**, sino que el campo no se capturó.
Contarlo como respuesta conocida convertiría el 0 % de 2013–2019 en un 100 %
falso; es el error que cometí en la primera pasada del reconocimiento y que el
contraste contra la evidencia del auditado detectó.

## 3. Resultados con su incertidumbre

Base: **20 423 respuestas conocidas** de 2021 sobre los 77 237 registros de la
base (20 421 para discapacidad). La referencia DANE es el censo 2018 para etnia y
discapacidad, y el **RUV 2021** para víctimas del conflicto —no 2018, pese al
nombre de la columna del auditado.

| Grupo | n | % | IC 95 % Wilson | Razón | IC razón (Wilson) | n en muestra | IC razón (diseño) |
|---|---:|---:|---|---:|---|---:|---|
| Afrocolombiano | 453 | 2,22 % | [2,02; 2,43] | **3,02×** | [2,76; 3,31] | 31 | [2,38; 4,82] |
| Indígena | 114 | 0,56 % | [0,46; 0,67] | **7,88×** | [6,57; 9,46] | 7 | [5,39; 31,70] |
| Discapacidad | 181 | 0,89 % | [0,77; 1,02] | **8,01×** | [6,93; 9,26] | 18 | [4,02; 10,61] |
| Víctima del conflicto | 421 | 2,06 % | [1,88; 2,27] | **8,59×** | [7,81; 9,44] | 31 | [6,36; 13,08] |
| Raizal | 45 | 0,22 % | [0,16; 0,29] | 0,27× | [0,20; 0,36] | 3 | no acotado |
| Palenquero | 11 | 0,05 % | [0,03; 0,10] | 0,26× | [0,15; 0,47] | 1 | no acotado |
| Rrom (gitano) | 6 | 0,03 % | [0,01; 0,06] | 0,17× | [0,08; 0,37] | **0** | no acotado |

**Lo que sobrevive a la incertidumbre.** Para los cuatro grupos del bloque
superior, los **cuatro** IC —Wilson y de diseño— **excluyen el 1**. Es decir: la
dirección del hallazgo (están subrepresentados) no depende de cómo se estime el
intervalo; lo que se vuelve impreciso es la **magnitud**. El «3,0×» del auditado
es compatible con cualquier valor entre 2,38 y 4,82 si se cuenta solo con la
muestra.

**Lo que no.** Los tres grupos étnicos minoritarios tienen razón **menor que 1**,
es decir están **sobrerrepresentados** frente a su peso poblacional (0,27×, 0,26×
y 0,17×). Con 45, 11 y 6 personas el IC de Wilson sigue excluyendo el 1, pero la
muestra no permite acotar el cociente: con 3, 1 y 0 observaciones, el intervalo de
diseño de la proporción incluye el cero y el cociente no tiene cota superior. Se
reporta como **no acotado** en vez de inventar un número.

> **Aviso de nomenclatura.** La columna del auditado se llama
> `razon_subrepresentacion`, pero para estos tres grupos vale menos de 1, es decir
> describe lo contrario. El nombre es engañoso y conviene leerlo como «cociente
> DANE/MinCiencias».

## 4. Los grupos pequeños tienen intervalos anchos, y eso es el resultado

**No es un fallo del análisis.** Con 114 indígenas y 6 rrom sobre 20 423
respuestas, la precisión está limitada por el tamaño del grupo, no por la técnica.
El intervalo de diseño es entre **2,8 y 9,1 veces más ancho** que el de Wilson:

| Grupo | Anchura IC Wilson | Anchura IC diseño | Veces |
|---|---:|---:|---:|
| Afrocolombiano | 0,55 | 2,44 | 4,4× |
| Indígena | 2,90 | 26,31 | 9,1× |
| Discapacidad | 2,33 | 6,59 | 2,8× |
| Víctima | 1,63 | 6,72 | 4,1× |

Esa diferencia **es** el hallazgo: sin la base completa, el proyecto no habría
podido sostener ni siquiera el orden de magnitud de la subrepresentación indígena
(entre 5,4× y 31,7×). Es la misma advertencia que F2-2 hizo para las tasas
departamentales y que F2-9 deberá tener en cuenta.

## 5. El denominador: por qué el código tenía razón y el comentario no

El comentario original de `diversidad.py` pedía excluir «Ningún grupo étnico» del
denominador «para ver minorías». **Excluirlo daría afro 72,0 %** (453 sobre 629),
frente al 2,22 % real. La razón es que mezcla bases: compararía «qué proporción de
las minorías es afro» con «qué proporción del país es afro».

El código no lo hacía y era el correcto; se corrigió el comentario (parche `E1`).
Aquí queda cuantificado: el denominador correcto son las **20 423 respuestas
conocidas**, de las cuales **19 794** son la mayoría declarada que el comentario
quería quitar. La diferencia entre 2,22 % y 72,0 % es la medida de cuánto dañaba
esa decisión.

## 6. Respuesta a Q6

El registro **sí** permite afirmar que la población investigadora reconocida está
fuertemente subrepresentada en los cuatro colectivos que el proyecto destaca:
afrocolombiano (3,0×; IC de diseño 2,4–4,8), indígena (7,9×; 5,4–31,7),
discapacidad (8,0×; 4,0–10,6) y víctimas del conflicto (8,6×; 6,4–13,1). La
dirección del hallazgo resiste cualquier lectura razonable del error; la magnitud,
no.

Lo que **no** permite afirmar es nada sobre la **evolución** de esa diversidad: las
tres variables se capturaron por primera vez en 2021. Y con los grupos étnicos
minoritarios (raizal, palenquero, rrom) no puede sostenerse ninguna cifra
precisa: están sobrerrepresentados en el registro, pero sobre 45, 11 y 6 personas.

## 7. Límites

- **Una sola convocatoria.** No hay serie: 2013–2019 tienen 0 % de cobertura en
  las tres variables.
- **La referencia DANE no es del mismo año** para todas: censo 2018 (etnia,
  discapacidad) y RUV 2021 (víctimas). Comparar «fotos» de años distintos es lo
  único posible con estas fuentes; se declara en vez de disimularlo.
- **Residencia declarada, no verificación.** Son autodeclaraciones del registro
  de MinCiencias.
- **`No disponible` y `No registra` no son cero.** El 3,2 % de 2021 sin dato queda
  fuera del denominador; si esos registros se concentraran en un grupo, las cifras
  cambiarían. Con la información disponible no puede saberse.
- **El bootstrap de diseño no es inferencia causal**: describe cuánto se movería
  la estimación bajo el diseño muestral del proyecto, no el error del registro.

## 8. Reproducir

```bash
python documentacion_auditoria/src/diversidad_inferencia.py
```

Entradas: el CSV fuente versionado en `01_datos/datos_fuente/`, la muestra
`data/memoria/muestra_ids.csv` y las referencias DANE copiadas de
`repo_mejorado/src/analisis/diversidad.py` (no se introducen cifras externas por
otra vía). **No necesita red.** Salidas: el JSON, las dos figuras y la evidencia
del auditado contra la que se contrasta.

| Figura | Contenido |
|---|---|
| `f2_5_cobertura_por_convocatoria.png` | Cobertura de las cuatro variables por convocatoria |
| `f2_5_razones_subrepresentacion.png` | Cocientes con IC de Wilson y de diseño; en rojo, los no estimables |
