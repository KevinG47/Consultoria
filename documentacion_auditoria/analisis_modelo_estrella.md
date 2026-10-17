# Modelo estrella reproducible con las 6 convocatorias (F2-3)

**Objetivo que cierra:** OE4 del repositorio auditado — «diseñar y crear un modelo
dimensional (esquema estrella)».
**Artefactos:** `documentacion_auditoria/src/modelo_estrella_6.py` ·
`data/memoria/modelo_estrella.json` · `data/memoria/graficas_estrella/` (2 figuras)
· parches `K1`–`K4` en `datos_originales/aplicar_arreglos.py`.

## 1. El defecto

`sprint2_duckdb.py:28` construye el modelo con `cargar_consolidado()`, que
prefiere `datos/raw/investigadores_consolidado.csv` —**ausente y gitignored**— y
cae al XLSX de `datos/tarea_join/`, que contiene **solo 3 convocatorias**. El
resultado es un modelo con `dim_convocatoria = 3` y `fact_clasificacion = 50 891`,
mientras la evidencia versionada del propio repositorio
(`evidencias/duckdb_resumen_modelo.txt`) documenta **6 convocatorias y 77 237
registros**. Es la ERRATA E2 aplicada al modelo dimensional: **la evidencia y el
producto reproducible no coinciden**.

Reprodujimos el defecto ejecutando el pipeline del auditado tal cual, con su
propio `cargar_consolidado()`: **3 y 50 891**, exactamente lo diagnosticado.

## 2. Qué hicimos

Sin reimplementar nada: alimentamos las **mismas funciones del auditado**
(`Transformacion.transformar()` y `modelo.dimensional.cargar_en_duckdb()`) con la
fuente completa de 6 convocatorias. La única adaptación necesaria está
documentada y explicada en §5.

La base DuckDB se escribe en un directorio de trabajo (`_archivo/tmp_estrella/`),
**no** dentro de `datos_originales/repo_auditado/`: los 236 hashes del manifiesto
siguen intactos (verificado antes y después). Para que importar los módulos
auditados no deje `__pycache__` dentro de esa copia verbatim, el script activa
`sys.dont_write_bytecode` antes de importarlos.

## 3. Resultado: el modelo se reconstruye completo

| Tabla | Con 3 conv. (lo que corre hoy) | Con 6 conv. (este análisis) | Δ |
|---|---:|---:|---:|
| `fact_clasificacion` | 50 891 | **77 237** | +26 346 |
| `dim_convocatoria` | 3 | **6** | +3 |
| `dim_investigador` | 26 662 | **30 086** | +3 424 |
| `dim_institucion` | 2 619 | **2 762** | +143 |
| `bridge_hecho_institucion` | 47 187 | **68 480** | +21 293 |
| `dim_territorio` | 227 | **249** | +22 |
| `dim_area` | 215 | **216** | +1 |
| `dim_formacion` | 11 | 11 | 0 |
| `dim_categoria` | 4 | 4 | 0 |

El modelo reconstruido **reproduce la evidencia versionada cifra a cifra**:

| Convocatoria | 2013 | 2014 | 2015 | 2017 | 2019 | 2021 | Total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Evidencia del auditado | 8 016 | 8 280 | 10 050 | 13 001 | 16 796 | 21 094 | 77 237 |
| Reconstruido | 8 016 | 8 280 | 10 050 | 13 001 | 16 796 | 21 094 | **77 237** |

Dos comprobaciones cruzadas que refuerzan el resultado, porque son cifras que
nuestro trabajo ya había establecido **por otra vía**:

- `dim_investigador = 30 086` coincide con las **30 086 personas distintas** del
  padrón que usan el EDA y el análisis longitudinal.
- `dim_institucion = 2 762` coincide con las **2 762 instituciones** que documenta
  la herramienta de trayectorias tras separar el campo `INST_FILIA` por ` | `.

**Integridad referencial: 0 huérfanos en las siete dimensiones.** Las seis claves
foráneas del hecho están íntegras, `sk_territorio` no tiene nulos, la tabla puente
no tiene claves huérfanas en ninguno de sus dos extremos, y las claves primarias de
las 8 tablas con clave son únicas y sin nulos. Las diez validaciones del JSON pasan.

## 4. El enunciado: no son nueve dimensiones, son nueve tablas

El objetivo específico 4 pide «un modelo dimensional (esquema estrella) con **nueve
dimensiones** y una tabla de hechos». El esquema real tiene **9 tablas**:

- **7 dimensiones**: `dim_area`, `dim_categoria`, `dim_convocatoria`,
  `dim_formacion`, `dim_institucion`, `dim_investigador`, `dim_territorio`;
- **1 tabla de hechos**: `fact_clasificacion`;
- **1 tabla puente**: `bridge_hecho_institucion` (relación N:N con las
  instituciones, porque `INST_FILIA` admite dos instituciones separadas por ` | `).

El propio docstring de `sprint2_duckdb.py` lista exactamente esas 9 tablas, así que
**el «nueve» cuenta tablas, no dimensiones**. Y la enumeración de la sección de
diseño del informe aclara de dónde viene la confusión: enumeraba nueve **atributos**
(investigador, convocatoria, universidad, área, nacimiento, género, residencia,
formación, clasificación) que la implementación **consolidó en siete dimensiones**
—nacimiento y género dentro de `dim_investigador`, universidad en
`dim_institucion`, residencia en `dim_territorio`—. **El diseño es correcto; lo que
engañaba era el enunciado.**

Como `repo_auditado/` es una copia verbatim intocable, la corrección va donde
corresponde: en `repo_mejorado/`, mediante **cuatro parches** (`K1`–`K4`) en el
mecanismo de arreglos, que falla si el ancla no aparece exactamente una vez y
verifica positivamente que la corrección esté presente. Se corrigieron las cuatro
descripciones del informe: el objetivo específico, la descripción del diseño, la
§5.3 y las conclusiones.

## 5. Dos hallazgos incidentales, verificados

**a) El pipeline es sensible al separador decimal del insumo.** Nuestra fuente de
6 convocatorias guarda `EDAD_ANOS_PR` con **coma** (`'66,92'`, 73 854 valores), de
modo que pandas la infiere como **texto** y `tratar_faltantes()` aborta con
`TypeError: Cannot perform reduction 'median' with string dtype`. La adaptación
mínima —convertir la coma en punto antes de llamar al pipeline, que es lo que el
propio proyecto ya hace en sus scripts de análisis— es la única modificación
introducida, y está declarada en el JSON.

**No es un defecto de la ruta normal del auditado**, y lo comprobamos en lugar de
suponerlo: consultamos la API de Socrata (`bqtm-4y2h`) y devuelve la edad como
texto **con punto** (`'66.92'`), así que el CSV que escribe
`src/ingesta/minciencias.py` se lee como `float64` y el pipeline corre sin tocarlo.
El consolidado de 3 convocatorias también usa punto. Es una fragilidad del
pipeline, no un error de su camino documentado.

**b) El pipeline fabrica una observación.** `tratar_faltantes()` rellena **todos**
los faltantes numéricos con la mediana, incluida la edad: el único registro sin
edad declarada queda imputado a **43,29 años**. Es lógica del auditado, se conserva
para que el modelo sea reproducible, y se registra porque introduce un dato que la
fuente no tiene.

## 6. Qué cambia y qué no

**Cambia:** el modelo dimensional pasa de 3 a 6 convocatorias, y con ello todas las
cifras que dependen de él. `dim_investigador` pasa de 26 662 a 30 086 personas,
`fact_clasificacion` de 50 891 a 77 237 hechos, y `dim_institucion` de 2 619 a
2 762. La gran tabla que se construye sobre este modelo (`codigo_creacion_gran_tabla_a_partir_del_modelo_estrella.py`)
recupera las 3 convocatorias que le faltaban.

**No cambia:** el diseño del esquema ni la lógica de análisis. No se tocó una línea
de `repo_auditado/` (236/236 hashes idénticos, verificado antes y después) ni la
lógica del pipeline: la reconstrucción usa las funciones del auditado sin
modificarlas.

## 7. Reproducir

```bash
python documentacion_auditoria/src/modelo_estrella_6.py
```

Entradas: la fuente de 6 convocatorias versionada en
`datos_originales/datos_fuente/` y los módulos del repositorio auditado. El script
**no necesita red**. Salidas: `data/memoria/modelo_estrella.json`, las dos figuras
de `data/memoria/graficas_estrella/` y las bases de trabajo en
`_archivo/tmp_estrella/` (ignoradas por git).

| Figura | Contenido |
|---|---|
| `f2_3_registros_por_convocatoria.png` | Registros por convocatoria: reconstruido frente a la evidencia versionada |
| `f2_3_tablas_del_modelo.png` | Las 9 tablas con el insumo de 3 y de 6 convocatorias |

Para la corrección del enunciado:

```bash
python datos_originales/construir_repo_mejorado.py   # copia limpia desde repo_auditado
python datos_originales/aplicar_arreglos.py          # 34 parches, entre ellos K1–K4
python datos_originales/verificar_arreglos.py
```

## 8. Límites

- La reconstrucción depende de que el insumo de 6 convocatorias esté disponible. El
  repositorio auditado **no lo versiona** (`datos/raw/` está vacío y gitignored), y
  la API de Socrata no sirve como sustituto directo: sus 28 campos **no incluyen
  `INST_FILIA`** ni `COD_DANE_RES_PR`, así que `dim_institucion` y la tabla puente
  no podrían poblarse desde ella. Nuestra fuente (30 columnas) sí los tiene.
- El modelo conserva dos decisiones del auditado que no revisamos aquí: la
  imputación de la mediana (§5b) y el `drop_duplicates()` de `dim_territorio` sobre
  las cinco columnas geográficas, que hace que la dimensión tenga una fila por
  combinación observada y no por municipio.
- `dim_institucion` se construye con `.iterrows()` sobre 77 237 filas: es lento
  (minutos, no segundos) pero correcto; no lo optimizamos para no alterar la lógica
  del auditado.
