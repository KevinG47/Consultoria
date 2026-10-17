# Inventario de Notebooks — Observatorio MinCiencias

**Sprint 1 — Issue #8**

Revisión de los 7 notebooks del repositorio. Documenta cuáles son reutilizables,
cuáles necesitan adaptación y cuáles descartar.

---

## Resumen ejecutivo

| Notebook | Estado | Issues relacionados |
|---|---|---|
| `notebooks/01_eda.ipynb` | Reutilizable — adaptar imports | #8, #9 |
| `notebooks/02_analisis_longitudinal.ipynb` | Reutilizable — adaptar imports | #8, #9, #11 |
| `notebooks/sprint2_analisis_longitudinal/sprint2_tracking_transiciones.ipynb` | Reutilizable — expandir a 6 convocatorias | #11, #12 |
| `notebooks/tarea_anlisis_bases_de_datos/datos_2021.ipynb` | Parcial — integrar en 01_eda | #9 |
| `notebooks/tarea_dimensiones_y_hechos/dimensiones.ipynb` | Parcial — migrar de Colab | #14 |
| `notebooks/tarea_gran_tabla/analisis2.ipynb` | Reutilizable — migrar de Colab | #13, #22 |
| `notebooks/tarea_gran_tabla/analisis2_(1).ipynb` | **DESCARTAR** — duplicado exacto | — |

---

## Detalle por notebook

### 1. `notebooks/01_eda.ipynb` — Análisis Exploratorio Principal

**Estado:** Reutilizable con adaptaciones

**Contenido:**
- Carga y vista general del dataset consolidado
- Calidad de datos: valores faltantes y tipos
- Variables numéricas: edad, nivel de formación, orden de clasificación
- Variables categóricas: género, gran área OCDE, nivel formación, clasificación, región
- Visualizaciones: distribución por género, top áreas, edad por convocatoria, top departamentos

**Fortalezas:**
- Bien estructurado en 5 secciones con celdas markdown descriptivas
- Modular: usa `from ingesta import cargar_consolidado` y `from Transformacion import transformar`
- Corre sobre el dataset completo (todas las convocatorias)

**Pendiente para reutilizar:**
- Verificar que `src/ingesta/__init__.py` exporte `cargar_consolidado()`
- Verificar que `src/Transformacion.py` exporte `transformar()`
- Actualizar referencia a convocatorias (actualmente dice 2017/2019/2021 — ahora son 6)

---

### 2. `notebooks/02_analisis_longitudinal.ipynb` — Análisis Longitudinal

**Estado:** Reutilizable con adaptaciones

**Contenido:**
- Evolución del número de investigadores por convocatoria
- Tendencias por género, área OCDE y región
- Movilidad en categoría de clasificación (crosstab año × categoría)
- Verificación de unicidad de `ID_PERSONA_PR`
- Conclusiones longitudinales por convocatoria

**Fortalezas:**
- Usa las mismas funciones de `src/` que `01_eda.ipynb`
- Incluye verificación de consistencia de edad entre convocatorias
- Gráficos de líneas temporales bien construidos

**Pendiente para reutilizar:**
- Mismos ajustes de imports que `01_eda.ipynb`
- El análisis menciona solo 2017/2019/2021; expandir a las 6 convocatorias (2013–2021)
- `ANO_CONVO_INT` debe generarse en `transformar()` o calcularse en el notebook

---

### 3. `notebooks/sprint2_analisis_longitudinal/sprint2_tracking_transiciones.ipynb` — Tracking y Matrices de Transición

**Estado:** Reutilizable — expandir cobertura temporal

**Contenido:**
- Tracking individual de investigadores via `ID_PERSONA_PR` entre convocatorias consecutivas
- Clasificación de resultados: Sube / Se mantiene / Baja / Desaparece
- Matrices de transición observada (solo investigadores presentes en ambas convocatorias)
- Matrices de transición extendida (incluye estado "Desaparece")
- Exportación de resultados a `evidencias/`

**Hallazgos clave documentados:**
- 2017→2019: 54% se mantiene, 23% desaparece, 17% sube, 6% baja
- 2019→2021: 58% se mantiene, 20% desaparece, 14% sube, 8% baja
- Todos los Eméritos del periodo inicial desaparecen en la siguiente convocatoria
- Senior es la categoría más estable (>80% de permanencia)

**Fortalezas:**
- El más completo en análisis longitudinal; lógica sólida con funciones reutilizables
- Comentarios explicativos dentro del código
- Lee desde `datos/tarea_join/investigadores_consolidado.csv`

**Pendiente para reutilizar:**
- Solo cubre 2017/2019/2021. Expandir a los 4 periodos: 2013→2014, 2014→2015, 2015→2017, 2017→2018, 2018→2021
- Actualizar ruta de entrada a `datos/raw/investigadores_consolidado.csv`

---

### 4. `notebooks/tarea_anlisis_bases_de_datos/datos_2021.ipynb` — EDA Convocatoria 2021

**Estado:** Parcialmente reutilizable — integrar en `01_eda.ipynb`

**Contenido:**
- EDA exclusivo de la convocatoria 2021 (21.094 registros)
- Distribución por género (60.6% M / 39.3% F)
- Detección de outliers de edad: 10 registros con edad > 100 años (máx. 956 años)
- Distribución por región de residencia y nivel de formación
- Variables de diversidad: víctimas conflicto, discapacidad, grupo étnico

**Fortalezas:**
- Documenta los outliers de edad con los IDs específicos — hallazgo de calidad relevante
- Análisis de diversidad (conflicto, etnia, discapacidad) que apoya Issue #20
- Ejecutado en Google Colab con salidas visibles

**Pendiente para reutilizar:**
- Está hecho en Colab (rutas `/content/`); migrar rutas a las del repo
- No usa el pipeline `src/` — depende de carga manual del Excel
- Integrar los hallazgos de outliers en la función `transformar()` como filtro opcional

---

### 5. `notebooks/tarea_dimensiones_y_hechos/dimensiones.ipynb` — Modelo Dimensional

**Estado:** Parcialmente reutilizable — migrar de Colab

**Contenido:**
- Construcción de tres dimensiones del modelo estrella:
  - `dim_universidad`: 2.983 entradas únicas de `INST_FILIA`
  - `dim_formacion`: 11 niveles de formación con orden jerárquico
  - `dim_residencia`: 224 combinaciones únicas de municipio/departamento/región/DANE
- Exporta a `dimensiones_investigadores.xlsx`

**Fortalezas:**
- Lógica de extracción de dimensiones lista para usar en Issue #14 (DuckDB)
- Identifica 2.983 instituciones únicas — insumo directo para análisis de redes (#15, #16)

**Pendiente para reutilizar:**
- Migrar de Colab a script Python (`src/modelo/dimensiones.py`) o notebook local
- `INST_FILIA` contiene múltiples instituciones separadas por `|`; este notebook no las desagrega — necesario para el análisis de redes
- Agregar dimensión de convocatoria y dimensión de área OCDE

---

### 6. `notebooks/tarea_gran_tabla/analisis2.ipynb` — Análisis Estadístico Gran Tabla

**Estado:** Reutilizable — migrar de Colab y actualizar datos

**Contenido:**
- Dataset: 50.891 registros (convocatorias 2017, 2018, 2021 — sin 2013/2014/2015)
- Género × clasificación: proporción ~37–39% femenino, tendencia creciente
- Clasificación × región: Cramér's V = 0.066 (asociación débil)
- Clasificación × gran área OCDE: Junior domina en todas las áreas (55–70%)
- Formación × clasificación: doctorado y postdoctorado concentran Sénior
- Formación × región: Cramér's V descriptivo para distribución geográfica
- Kruskal-Wallis edad × área: diferencias significativas entre áreas
- Post-hoc Dunn con corrección Bonferroni

**Fortalezas:**
- El notebook estadístico más robusto del repositorio
- Combina análisis descriptivo con pruebas no paramétricas
- Visualizaciones de calidad (barras apiladas con etiquetas, heatmaps, countplots)

**Pendiente para reutilizar:**
- Migrar de Colab; actualizar rutas a `datos/raw/investigadores_consolidado.csv`
- Expandir de 3 a 6 convocatorias
- Añadir `ID_PERSONA_PR` (el archivo original era "SIN ID")
- Convertir en notebook oficial `03_analisis_estadistico.ipynb`

---

### 7. `notebooks/tarea_gran_tabla/analisis2_(1).ipynb` — Duplicado

**Estado:** DESCARTAR

Duplicado exacto de `analisis2.ipynb` (30 celdas idénticas). Generado por Google Colab
al guardar una copia. No aporta información adicional.

---

## Plan de refactorización (Issue #9)

| Notebook nuevo | Fuente(s) | Sprint |
|---|---|---|
| `notebooks/01_eda.ipynb` | Actualizar imports + expandir a 6 convocatorias | Sprint 2 |
| `notebooks/02_analisis_longitudinal.ipynb` | Actualizar imports + expandir periodos | Sprint 2 |
| `notebooks/03_analisis_estadistico.ipynb` | Migrar `analisis2.ipynb` de Colab | Sprint 2 |
| `notebooks/04_tracking_transiciones.ipynb` | Refactorizar `sprint2_tracking_transiciones.ipynb` | Sprint 2 |

Los notebooks `datos_2021.ipynb` y `dimensiones.ipynb` se absorben en los scripts
de `src/transformacion/` y `src/modelo/` respectivamente, no como notebooks independientes.
