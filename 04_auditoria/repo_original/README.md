# Observatorio MinCiencias — Investigadores Reconocidos

> **Ustadistica** -- Consultoria e Investigacion . Universidad Santo Tomas . 2026-I

Observatorio crítico del sistema de reconocimiento de investigadores de MinCiencias. Análisis longitudinal de **6 convocatorias** (2013-2021) con foco en **calidad de los datos**, **concentración territorial**, **brecha de género**, **redes de co-filiación institucional**, **subrepresentación de minorías**, **productividad cruzada con el dataset de producción de grupos**, y **flujos investigador → institución** mediante una tabla maestra de IES construida ad-hoc.

El proyecto produce insumos para un informe crítico sobre las falencias de las convocatorias y el estado de la investigación en Colombia.

## Fuentes de Datos

MinCiencias / datos.gov.co. Dos datasets cruzados por `id_persona`:

### 1. Investigadores reconocidos por convocatoria (`bqtm-4y2h`)

Dataset consolidado (`datos/tarea_join/investigadores_consolidado.xlsx`) que integra **6 convocatorias históricas**:

| Convocatoria | Año | Registros |
|---|---|---|
| 640 | 2013 | 8.016 |
| 693 | 2014 | 8.280 |
| 737 | 2015 | 10.050 |
| 781 | 2017 | 13.001 |
| 833 | 2018 | 16.796 |
| 894 | 2021 | 21.094 |
| **Total** | **2013–2021** | **77.237 registros / 30.086 investigadores únicos** |

### 2. Producción de grupos de investigación (`33dq-ab5a`)

Dataset descargado por API Socrata (~1.2 GB, gitignored). Una fila por producto-autor:

| Convocatoria | Productos |
|---|---:|
| 16 / 2013 | 238.407 |
| 17 / 2014 | 342.160 |
| 18 / 2015 | 376.653 |
| 19 / 2017 | 536.648 |
| 20 / 2019 | 762.719 |
| 21 / 2021 | 910.042 |
| **Total** | **3.166.629** |

**Llave de cruce:** `produccion.id_persona_pd ↔ investigadores.id_persona_pr` (más `id_convocatoria` para asegurar la ventana).

Consultar [`datos/catalogo.yaml`](datos/catalogo.yaml) para los identificadores Socrata y metadatos completos de cada dataset.

## Preguntas de Investigacion

- ¿Qué tan confiable es la información que MinCiencias publica? ¿Permite analizar el sistema de manera comparable entre convocatorias?
- ¿El sistema retiene a los investigadores reconocidos entre convocatorias? ¿Qué porcentaje sube/baja/desaparece?
- ¿La capacidad investigativa está distribuida equitativamente o concentrada? Comparación per cápita con población DANE 2018.
- ¿Hay paridad de género por gran área OCDE? ¿La brecha en STEM se ha cerrado en una década?
- ¿Cómo se conectan las instituciones a través de investigadores con doble afiliación? ¿Hay universidades-puente?
- ¿La composición de los investigadores refleja la diversidad poblacional de Colombia (etnia, discapacidad, víctimas del conflicto)?
- ¿Quién firma realmente la producción que MinCiencias mide? ¿Los Senior producen más que los Junior? ¿La brecha de género se replica en outputs?

## Hallazgos críticos (vista rápida)

| # | Hallazgo | Implicación |
|---|---|---|
| 1 | Bogotá + Antioquia = 51% del país | Concentración territorial brutal |
| 2 | 24% de mujeres en Ingeniería vs 48% en Ciencias Médicas | Brecha estructural por área |
| 3 | Co-filiación solo capturada en 2019 (569 casos) | Cambio de captura, no de realidad |
| 4 | 0% de cobertura de etnia/discapacidad/conflicto antes de 2021 | Diversidad invisible 8 años |
| 5 | Afros 3x, Indígenas 7.9x, Discapacidad 8x subrepresentados vs DANE | Barreras estructurales |
| 6 | Raizales/Palenqueros/Rrom sobrerrepresentados 3-6x | Programas focalizados con efecto |
| 7 | 22 edades > 100 años (máx 956), conv. 833 mal etiquetada | Calidad de datos cuestionable (tratamiento documentado) |
| 8 | Solo 36.9% de los autores únicos en producción son investigadores reconocidos | El sistema captura coautoría externa al padrón |
| 9 | Productividad escala con categoría: Junior 30 / Asociado 65 / **Senior 121** productos | Reconocimiento alineado con output |
| 10 | Brecha de género en productividad en 5/6 grandes áreas OCDE | La brecha de representación se duplica en outputs medidos |
| 11 | 2.762 cadenas únicas en `inst_filia` → ~800 IES reales | Captura sin estandarización; tabla maestra entregada cubre 91% |
| 12 | Bogotá retiene 92% de sus investigadores **y** absorbe 1.000+ de otros dpto | No solo concentra: atrae. Cundinamarca/Risaralda retención local ~70% |
| 13 | Ciencias Sociales gana en volumen (585k); **Ingeniería** en productividad por investigador (67) | "¿Qué área produce más?" depende de la métrica |
| 14 | Eméritos quedan **vitalicios** — no reaparecen porque no necesitan re-postular | El 100% de "desaparición" es diseño del sistema |

## Estructura del Proyecto

```
Observatorio_Ministerio_de_Ciencias_Grupo7/
|-- README.md                    # Este archivo
|-- CONTRIBUTING.md              # Guia de contribucion y Git Flow
|-- pyproject.toml               # Poetry (dependencias + metadata)
|-- Dockerfile                   # Contenedor reproducible
|-- .github/
|   +-- workflows/
|       +-- etl_update.yml       # GitHub Actions para ingesta periodica
|-- src/
|   |-- ingesta/                 # cargar_consolidado + cargar_produccion + sodapy (Socrata)
|   |-- analisis/                # Logica reutilizable
|   |   |-- longitudinal.py      # Panel + matrices de transicion
|   |   |-- territorial.py       # HHI + cuotas territoriales
|   |   |-- genero.py            # Brecha por area OCDE
|   |   |-- redes.py             # Co-filiacion + normalizar_institucion + Pyvis
|   |   |-- diversidad.py        # Etnia, discapacidad, conflicto vs DANE/RUV
|   |   |-- produccion.py        # Cruce produccion <-> investigadores (Sprint 5)
|   |   +-- calidad.py           # Validacion documentada de atipicos (Sprint 6)
|   |-- modelo/dimensional.py    # Modelo estrella DuckDB
|   +-- Transformacion.py        # Pipeline limpieza + normalizacion
|-- scripts/                     # Orquestacion por sprint
|   |-- sprint2_panel_longitudinal.py
|   |-- sprint2_matrices_transicion.py
|   |-- sprint2_territorial.py
|   |-- sprint2_genero_ocde.py
|   |-- sprint2_duckdb.py
|   |-- sprint3_redes.py
|   |-- sprint3_grafo_interactivo.py
|   |-- sprint4_diversidad.py
|   |-- sprint5_produccion.py    # 6 figuras + 7 CSVs de productividad cruzada
|   |-- sprint5_duckdb.py        # fact_produccion + dim_grupo + vw_investigador_x_produccion
|   |-- sprint6_validacion_calidad.py   # Tratamiento documentado de atipicos
|   |-- sprint6_sankey_categoria.py     # 5 Sankeys de transicion de categoria
|   |-- sprint6_ocde_composicion.py     # Composicion tipo producto por area OCDE
|   |-- sprint6_tabla_maestra_ies.py    # Tabla maestra IES (211 IES, 91% cobertura)
|   |-- sprint6_geografia_institucional.py  # Cruce residencia x departamento institucion
|   |-- sprint6_sankey_territorial.py   # Sankey residencia -> institucion
|   +-- generar_manual.py        # Genera docs/manual.ipynb desde codigo
|-- notebooks/
|   +-- 01_eda.ipynb             # Unico notebook activo (EDA exploratorio)
|-- streamlit_app.py             # Dashboard — 7 tabs tipo capitulo del informe
|-- .streamlit/config.toml       # Tema y configuracion para Streamlit Cloud
|-- requirements.txt             # Deps minimas runtime para deploy
|-- docs/
|   |-- presentacion/index.html  # 18 slides Reveal.js para Izainea (20 min)
|   |-- manual.ipynb             # Notebook ejecutable con los 15 hallazgos
|   +-- informe/informe_final.tex # Informe consolidado en LaTeX (~30 pag)
|-- datos/
|   |-- raw/                     # Datos crudos (gitignored)
|   |-- processed/               # observatorio.duckdb (gitignored)
|   |-- tarea_join/              # Excel consolidado versionado en git (12 MB)
|   +-- catalogo.yaml            # Metadatos de cada dataset
|-- artifacts/                   # Figuras PNG generadas por sprint
|-- evidencias/                  # CSVs exportados por los scripts
|-- hallazgos/                   # HTMLs interactivos (grafos Pyvis)
|-- docs/                        # Informes y documentacion
|-- tests/                       # Tests automatizados
+-- models/                      # Modelos serializados
```

## Instalacion

```bash
# Clonar el repositorio
git clone https://github.com/ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo7.git
cd Observatorio_Ministerio_de_Ciencias_Grupo7

# Instalar dependencias con Poetry
pip install poetry
poetry install

# Descargar datasets consolidados desde Socrata
poetry run python -m src.ingesta.minciencias               # Investigadores reconocidos
poetry run python -m src.ingesta.produccion                # Produccion de grupos (~1.2 GB, paginado)

# Ejecutar todos los analisis (genera figuras en artifacts/ y CSVs en evidencias/)
poetry run python scripts/sprint2_panel_longitudinal.py    # Panel longitudinal
poetry run python scripts/sprint2_matrices_transicion.py   # Matrices de transicion
poetry run python scripts/sprint2_territorial.py           # HHI territorial
poetry run python scripts/sprint2_genero_ocde.py           # Brecha por area OCDE
poetry run python scripts/sprint2_duckdb.py                # Modelo estrella DuckDB
poetry run python scripts/sprint3_redes.py                 # Co-filiacion
poetry run python scripts/sprint3_grafo_interactivo.py     # Grafo Pyvis interactivo
poetry run python scripts/sprint4_diversidad.py            # Diversidad vs DANE/RUV
poetry run python scripts/sprint5_produccion.py            # Cruce produccion x investigadores
poetry run python scripts/sprint5_duckdb.py                # fact_produccion en DuckDB
poetry run python scripts/sprint6_validacion_calidad.py    # Atipicos de edad documentados
poetry run python scripts/sprint6_sankey_categoria.py      # 5 Sankeys transicion categoria
poetry run python scripts/sprint6_ocde_composicion.py      # Composicion por area OCDE
poetry run python scripts/sprint6_tabla_maestra_ies.py     # Tabla maestra de IES
poetry run python scripts/sprint6_geografia_institucional.py  # Residencia x dpto institucion
poetry run python scripts/sprint6_sankey_territorial.py    # Sankey territorial

# Generar el notebook manual (manualcito ejecutable)
poetry run python scripts/generar_manual.py
poetry run jupyter notebook docs/manual.ipynb

# Lanzar dashboard (7 tabs tipo capitulo del informe)
poetry run streamlit run streamlit_app.py

# Presentacion HTML para revision con director (20 min, Reveal.js)
open docs/presentacion/index.html

# Compilar informe LaTeX consolidado (~30 paginas)
cd docs/informe && pdflatex informe_final.tex && pdflatex informe_final.tex
```

## Deploy en Streamlit Cloud

El dashboard puede desplegarse gratuitamente en [Streamlit Community Cloud](https://share.streamlit.io):

1. Iniciar sesión con la cuenta de GitHub.
2. Clic en **New app** → seleccionar el repo `Victor-Diaz-Usta/Min_ciencias`.
3. Configuración:
   - **Branch:** `main_VictorD` (o `main` después del merge)
   - **Main file path:** `streamlit_app.py`
   - **Python version:** 3.10+
4. Clic en **Deploy**.

Streamlit Cloud detecta automáticamente:
- `requirements.txt` → instala `streamlit`, `pandas`, `numpy`, `plotly`, `openpyxl`
- `.streamlit/config.toml` → tema y configuración del servidor
- `datos/tarea_join/investigadores_consolidado.xlsx` → fuente de datos (12 MB, versionada en git)

El primer build tarda ~3 minutos. Builds posteriores son incrementales tras cada push a la rama configurada.

## Cronograma -- CRISP-DM

### Sprint 1 (Sem 1-2)

Actualización de datos (verificar convocatoria 2023), automatizar ingesta con sodapy, refactorizar notebooks.

### Sprint 2 (Sem 3-4) — COMPLETADO ✅

| Issue | Título | Estado |
|---|---|---|
| #11 | Panel longitudinal de investigadores | ✅ Completado |
| #12 | Matrices de transición de categoría | ✅ Completado |
| #13 | Análisis de concentración territorial (HHI) | ✅ Completado |
| #14 | Modelo dimensional en DuckDB | ✅ Completado |
| #22 | Análisis de género por área OCDE | ✅ Completado |

### Sprint 3 (Sem 5-7)

Network analysis de co-filiación institucional (NetworkX + Pyvis). Dashboard Streamlit con mapa, distribuciones y grafo interactivo.

| Issue | Título | Estado |
|---|---|---|
| #15 | Network analysis de co-filiación | ✅ Completado |
| #16 | Visualización de grafo interactivo | ✅ Completado |
| #17 | Dashboard: mapa de investigadores | ✅ Completado |
| #18 | Dashboard: tabla de instituciones | ✅ Completado |
| #19 | Deploy dashboard en Streamlit Cloud | ✅ Listo para deploy |

### Sprint 4 (Sem 8)

Análisis de variables de conflicto, etnia y discapacidad. Comparación con proporciones poblacionales DANE 2018 / RUV 2021.

| Issue | Título | Estado |
|---|---|---|
| #20 | Análisis de variables de conflicto y diversidad | ✅ Completado |
| #21 | Informe final reproducible | ⏳ Pendiente |

### Sprint 5 (Sem 9) — COMPLETADO ✅

Integración del dataset de **Producción de Grupos** (Socrata `33dq-ab5a`, 3.166.629 filas) cruzado con el padrón de investigadores por `id_persona_pd ↔ id_persona_pr`.

| Issue | Título | Estado |
|---|---|---|
| #24 | Análisis de producción cruzado con investigadores | ✅ Completado |

Salidas: `src/analisis/produccion.py` (10 funciones), `scripts/sprint5_*.py` (orquestación + DuckDB), 6 figuras + 7 CSVs en `evidencias/produccion_*.csv`, tab nueva en el dashboard.

### Sprint 6 (Sem 10-11) — COMPLETADO ✅

Ajustes pedidos por el director Izainea tras la revisión de la presentación. Se documenta el tratamiento de atípicos, se construye la tabla maestra de IES como entregable, se incorporan los Sankeys de transición y se agrega el cruce geográfico institucional.

| Producto | Salida |
|---|---|
| Validación de calidad documentada | `src/analisis/calidad.py` + `scripts/sprint6_validacion_calidad.py` |
| Sankeys de transición de categoría (5 pares) | `artifacts/sprint6_sankey/sankey_*.html` y `.png` |
| Composición OCDE por tipo de producto | `artifacts/sprint6_ocde/` + 3 CSVs |
| Tabla maestra de IES (211 IES, 91% cobertura) | `evidencias/tabla_maestra_ies.csv` + `mapping_inst_filia_to_ies.csv` |
| Análisis geográfico institucional | `artifacts/sprint6_geografia/` + `evidencias/geografia_*.csv` |
| Sankey territorial (residencia → institución) | `artifacts/sprint6_sankey/sankey_territorial.html` |
| Notebook manual ejecutable | `docs/manual.ipynb` (49 celdas) |
| Informe LaTeX consolidado | `docs/informe/informe_final.tex` (~30 pag) |
| Presentación HTML 20 min | `docs/presentacion/index.html` (18 slides Reveal.js) |

**Aclaraciones que aporta el Sprint 6:**
- Los Eméritos **quedan vitalicios**. Su "desaparición" en convocatorias siguientes es diseño del sistema, no expulsión.
- Atípicos de edad: **22 casos** (no 10) con `edad > 100`; método aplicado documentado (eliminación) y comparado con imputación por mediana del grupo.
- Tabla maestra: las 2.762 cadenas de `inst_filia` corresponden a ~800 IES reales. El borrador entregado consolida 211 IES y cubre el 91% del padrón.
- Geografía: Bogotá retiene 92% y absorbe ~1.000 investigadores de otros departamentos. Cundinamarca y Risaralda tienen baja retención local (~70%). Chocó y Amazonas tienen alta retención local pese a su tamaño.

### Dashboard refactorizado (post-Sprint 5)

Dashboard con narrativa crítica para alimentar el informe final. **7 tabs tipo capítulo**:

1. **Calidad de los datos** — heatmap de cobertura + tabla de anomalías (edad>100, conv. mal etiquetadas)
2. **Trayectoria longitudinal** — retención + matrices de transición interactivas
3. **Concentración territorial** — mapa + per cápita DANE 2018 + HHI evolutivo
4. **Brecha de género y diversidad** — heatmap género + comparación DANE/RUV con metodología explicada
5. **Redes y poder institucional** — grafo Pyvis embebido + top instituciones (con normalización)
6. **Productividad y desempeño** — cobertura de reconocimiento, productividad por categoría, brecha de género en outputs, concentración territorial de productos, reconocidos sin producción
7. **Datos crudos** — auditoría directa con descarga CSV

Cada sección sigue el patrón **Pregunta → Hallazgo → Caveat**.


## Equipo

| Rol | GitHub |
|-----|--------|
| Pipeline + deploy | [@Victor-Diaz-Usta](https://github.com/Victor-Diaz-Usta) |

**Director / Revisor PRs:** [@Izainea](https://github.com/Izainea)

## Metodologia

- **Framework analitico:** CRISP-DM
- **Gestion de proyecto:** Sprints de 2 semanas con Kanban (GitHub Projects)
- **Control de versiones:** Git Flow (`main` / `develop` / `feature/*`)
- **Estandar operativo:** Big 4 (governance formal, auditoria cruzada, mejora continua)

Consultar [CONTRIBUTING.md](CONTRIBUTING.md) para la guia completa de contribucion.

## Stack Tecnologico

| Capa | Herramientas |
|------|-------------|
| Ingesta | sodapy, pandas, requests |
| Almacen | DuckDB (modelo estrella) |
| Analisis | pandas, scikit-learn, statsmodels |
| Visualizacion | matplotlib, seaborn, plotly, folium |
| Dashboard | Streamlit |
| Reproducibilidad | Poetry, Docker, GitHub Actions |
| Testing | pytest, pandera |

---

> *"Si no esta en el README, el proyecto no existe."* -- Ustadistica 2026-I
