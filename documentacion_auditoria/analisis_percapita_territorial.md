# Concentración territorial per cápita (F2-2)

**Pregunta que cierra:** Q3 del repositorio auditado — «¿cómo se compara la
concentración territorial de los investigadores con la población departamental?».
**Artefactos:** `documentacion_auditoria/src/percapita_territorial.py` ·
`data/memoria/percapita_territorial.json` ·
`data/memoria/graficas_percapita/` (4 figuras).

## 1. El problema con la medida que existía

El repositorio auditado mide la concentración con el **HHI sobre cuotas de
investigadores** (`territorial_hhi_por_convocatoria.csv`): qué fracción del
total aporta cada departamento. Ese indicador baja de 0,190 a 0,146 entre 2013
y 2021 y el informe lo lee como convergencia territorial.

El indicador mezcla dos cosas distintas: que un departamento tenga muchos
investigadores **porque tiene mucha población**, y que tenga muchos **por
habitante**. Un HHI de cuotas no distingue una de la otra, y Q3 pide
explícitamente lo segundo. Ese cálculo **no existía en ningún artefacto del
repositorio auditado**: el único `*_dane.csv` que publica compara grupos
étnicos, no territorios.

## 2. Datos y método

| Elemento | Decisión |
|---|---|
| **Numerador** | Personas distintas reconocidas por departamento de residencia, en las 6 convocatorias (2013–2021). Base: `datos_originales/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv` (77 237 registros · 30 086 personas). |
| **Unión territorial** | Por **código DIVIPOLA** (prefijo de `COD_DANE_RES_PR`), no por nombre: la fuente escribe `'Bogotá  D. C.'` con doble espacio y `'Archipiélago de San Andrés  Providencia y Santa Catalina'`, que no son claves fiables. El prefijo mapea los 33 departamentos sin ambigüedad. |
| **Exclusiones** | 2 448 registros (3,17 %) sin departamento colombiano: 2 132 «Exterior» y 316 «No disponible». No tienen denominador poblacional, así que quedan fuera de las tasas. |
| **Stock** | Cada persona contada en su **última** convocatoria: 28 950 personas. Las tasas por convocatoria usan las personas presentes en cada una. |
| **Denominador principal** | Población **censada** del CNPV 2018, cuadro oficial 1PD: 33 unidades, **44 164 417**. |
| **Robustez** | Población **ajustada por omisión** 2018 (**48 258 494**) y proyectada **2021** (**51 115 637**), de las proyecciones departamentales del DANE. |
| **Incertidumbre** | Bootstrap al 95 %, B = 2 000, semilla 20260217, en dos niveles: (i) remuestreo de los investigadores reconocidos; (ii) remuestreo dentro de post-estratos por categoría sobre la muestra MAS (n = 2 224). |
| **Desigualdad** | Gini, Theil T y L, HHI, y descomposición de Theil entre/dentro de las 9 regiones de la fuente. |

**Controles internos.** El script autocomprueba los índices contra casos de
solución conocida (igualdad perfecta → 0; concentración total → Gini = (n−1)/n y
Theil T = ln n; la descomposición debe cerrar; invariancia de escala). Reproduce
además el HHI del auditado: coincide a **4,75 × 10⁻⁷**, que es el redondeo a 6
decimales del CSV publicado, e idéntico número de territorios por convocatoria
(29, 31, 31, 32, 32, 34). Las 8 validaciones del JSON pasan.

## 3. Resultados

### 3.1 Cuánta investigación por habitante (stock)

Tasa nacional: **65,6** investigadores por 100 000 habitantes.

| Departamento | Tasa | IC 95 % | | Departamento | Tasa | IC 95 % |
|---|---:|---|---|---|---:|---|
| Bogotá, D. C. | **137,7** | 135,5–139,9 | | Guainía | 6,8 | 0,0–15,8 |
| Caldas | 93,6 | 87,3–99,5 | | Vaupés | 5,3 | 0,0–13,3 |
| Antioquia | 83,7 | 81,6–85,9 | | Arauca | 3,8 | 1,7–6,7 |
| Atlántico | 80,9 | 77,3–84,3 | | Guaviare | 2,7 | 0,0–6,8 |
| Santander | 78,3 | 74,4–82,0 | | Putumayo | 1,4 | 0,4–2,8 |
| Boyacá | 69,6 | 64,8–74,2 | | Vichada | **1,3** | 0,0–3,9 |

La razón entre el mayor y el menor es **105,5×**. Bogotá aporta el **34,16 %**
de los investigadores y el **16,26 %** de la población: **2,10 veces** lo que le
correspondería por tamaño. En el extremo opuesto, Vichada y Putumayo aportan
0,02 veces su peso poblacional.

### 3.2 La brecha se cierra, pero no donde se creía

| Convocatoria | HHI de cuotas (auditado) | Gini de tasas | Theil T de tasas | Gini de conteos |
|---|---:|---:|---:|---:|
| 2013 | 0,2061 | 0,5239 | 0,4906 | 0,7807 |
| 2015 | 0,1883 | 0,4918 | 0,4237 | 0,7663 |
| 2017 | 0,1737 | 0,4650 | 0,3754 | 0,7523 |
| 2019 | 0,1615 | 0,4610 | 0,3702 | 0,7347 |
| 2021 | 0,1558 | 0,4361 | 0,3228 | 0,7254 |

Las tres medidas bajan, así que la convergencia que describe el informe
auditado **es real también por habitante**. Pero conviene ver la magnitud: el
Gini de tasas cae un 17 % y sigue en **0,44**, un valor de desigualdad muy alta;
el Gini de los **conteos** apenas se mueve (0,78 → 0,73, un 7 %). Es decir, los
departamentos pequeños crecieron en número absoluto, pero muy lejos de alcanzar
a los grandes en términos relativos a su población.

### 3.3 Dónde vive la desigualdad: la descomposición de Theil

| Convocatoria | Total | Entre regiones | Dentro de regiones | % entre |
|---|---:|---:|---:|---:|
| 2013 | 0,4906 | 0,3891 | 0,1015 | 79,3 % |
| 2017 | 0,3754 | 0,2689 | 0,1064 | 71,6 % |
| 2021 | 0,3228 | 0,2204 | 0,1023 | 68,3 % |

**Este es el hallazgo central del análisis.** Toda la convergencia ocurrió
**entre** regiones (0,389 → 0,220), mientras que la desigualdad **dentro** de
las regiones se mantuvo prácticamente plana (0,1015 → 0,1023). La brecha
territorial colombiana es un fenómeno **interregional**, y lo que se ha cerrado
es la distancia entre macrorregiones; ningún departamento rezagado ha convergido
con sus vecinos de la misma región. El componente interno es hoy el 31,7 % del
total, frente al 20,7 % de 2013.

### 3.4 Incertidumbre: qué se puede afirmar y con qué

| | Bootstrap de personas | Bootstrap de diseño (muestra MAS) |
|---|---|---|
| Anchura mediana del IC | 2,7 – 5,7 por 100 000 | **8,9 – 19,6** por 100 000 |
| Departamentos estimados en cero | 0 | **6 – 9 de 33** |
| Gini del stock | 0,433 (IC 0,421–0,450) | — |

La conclusión operativa: **con la muestra no se pueden sostener tasas por
departamento para los departamentos pequeños.** Seis a nueve quedan estimados en
cero y la anchura del IC triplica o cuadruplica la del bootstrap de personas. En
cambio, la heterogeneidad territorial es tan grande que 24–27 departamentos sí
se distinguen del promedio nacional incluso con esa muestra. Esto es una
advertencia directa para F2-9, que extiende la inferencia MAS + post-estratificación
+GREG a nuevas variables.

### 3.5 Dos correcciones a la medida del auditado

1. **«Exterior» no es un territorio.** El HHI auditado cuenta `Exterior`
   (2 132 registros) y `No disponible` (316) como unidades geográficas; de ahí
   sus «29 a 34 territorios». Al excluirlos, el HHI departamental es **1,06
   puntos porcentuales mayor en promedio** (2013: 0,2061 frente a 0,1903). La
   concentración territorial real está **subestimada** en la evidencia publicada.
2. **La omisión censal es diferencial.** Con la población ajustada por omisión,
   el Gini sube de 0,433 a **0,442** (+0,009) y el Theil de 0,320 a **0,333**
   (+0,014); con el denominador emparejado de 2021, el Gini de esa convocatoria
   sube de 0,436 a **0,447**. La desigualdad per cápita es, si acaso, algo mayor
   de lo que reporta la cifra principal. Nótese que una corrección de omisión
   *uniforme* no la alteraría: Gini y Theil son invariantes de escala, y eso se
   verifica explícitamente en el JSON.

## 4. Respuesta a Q3

Sí procede comparar contra la población, y al hacerlo la conclusión cambia de
matiz: la concentración territorial colombiana **baja** entre 2013 y 2021 en las
tres medidas, pero (i) se mantiene en niveles de desigualdad muy altos —Gini de
tasas 0,44, razón de 105× entre extremos, Bogotá con el doble de investigadores
por habitante de lo que le correspondería—, (ii) su descenso es **exclusivamente
interregional** y (iii) la base muestral del proyecto **no permite** sostener
tasas departamentales para los departamentos pequeños. La lectura de
«convergencia territorial» del informe auditado no es falsa, pero es
incompleta: describe un acercamiento entre bloques regionales, no entre
departamentos.

## 5. Límites

- Se usa el denominador de 2018 para las seis convocatorias. Como la población
  crece de forma desigual, esto es anacrónico para 2013 y 2021; la comprobación
  con el denominador de 2021 acota el efecto (Gini 0,436 → 0,447).
- `NME_DEPARTAMENTO_RES_PR` es el departamento de **residencia**, no el de
  trabajo; la movilidad intramunicipal no se observa.
- El numerador es un registro administrativo de reconocimientos, no una encuesta.
  El bootstrap de personas es un dispositivo de superpoblación: mide cuánto se
  movería el indicador ante otra realización del proceso de reconocimiento, no
  error de muestreo. Por eso se reporta también el bootstrap de diseño.
- Los departamentos con 1–5 investigadores (Vichada, Guaviare, Vaupés, Guainía)
  tienen tasas y razones inestables: sus IC incluyen el cero.

## 6. Reproducir

```bash
python documentacion_auditoria/src/percapita_territorial.py
```

Entradas: el CSV fuente de investigadores y los dos CSV del DANE versionados en
`datos_originales/datos_fuente/` (cada uno con su `.procedencia.txt`, con URL y
SHA-256 del cuaderno oficial). El script **no necesita red**. Salidas:
`data/memoria/percapita_territorial.json` y las cuatro figuras de
`data/memoria/graficas_percapita/`.

| Figura | Contenido |
|---|---|
| `f2_2_tasa_por_100000.png` | Tasas por departamento con IC 95 % y promedio nacional |
| `f2_2_evolucion_concentracion.png` | HHI de cuotas frente a Gini y Theil de tasas, 2013–2021 |
| `f2_2_cuota_vs_poblacion.png` | Cuota de investigadores frente a cuota de población (proporcionalidad) |
| `f2_2_theil_descomposicion.png` | Theil entre y dentro de regiones, por convocatoria |
