# Consultoría Estadística USTA · 2026-II
## Auditoría reproducible del Observatorio MinCiencias y análisis propio de los investigadores reconocidos (2013–2021)

**Equipo:** Kevin Leonardo Chaparro Reyes · Valentina Muñoz Palma ·
Paula Margarita Triana Ancinez
**Asignatura:** Consultoría Estadística — Universidad Santo Tomás ·
**Modalidad:** proyecto con datos abiertos

---

## Qué es este repositorio, en dos párrafos

Primero **auditamos**: el repositorio público
[`ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8`](https://github.com/ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8)
(commit `1528939`) se copió byte a byte, se documentó archivo por archivo y se
contrastó cada cifra que afirmaba. Después **analizamos nosotros**: sobre la base
completa de investigadores reconocidos por MinCiencias (77 237 registros, 30 086
personas, 6 convocatorias entre 2013 y 2021) hicimos los diez análisis que el
repositorio auditado había dejado pendientes y uno nuevo de flujos territoriales,
con inferencia (MAS + post-estratificación + GREG), modelos nulos, supervivencia y
un mapa interactivo.

Todo está versionado para que **el próximo grupo lo pueda reproducir sin el clon
auditado y sin internet**: los datos fuente, una copia verbatim del proyecto
auditado con manifiesto SHA-256, el pipeline completo, los paneles HTML
autocontenidos y un sistema de validación automática de **17 reglas** que se corre
antes de dar cualquier cifra por buena.

---

## Las cinco carpetas

| Carpeta | Qué hay | Empieza por |
|---|---|---|
| **`01_datos/`** | **Datos.** `datos_fuente/` con la base de datos.gov.co (`Investigadores_Reconocidos_por_convocatoria_20261006.csv`, 31,3 MB) y las tablas del DANE (CNPV 2018 y proyecciones) con su `.procedencia.txt`; `resultados_json/` con los **8 JSON de resultados** de los análisis (F2-2 a F2-11) | `01_datos/resultados_json/` |
| **`02_dashboards/`** | **Los paneles.** Cinco HTML que se abren con doble clic y funcionan **sin conexión**: el panel de la Fase 2, el EDA, el visor de trayectorias, el mapa de flujos y el grafo de la memoria | `02_dashboards/dashboard_fase2.html` |
| **`03_informes/analisis_fase2/`** | **Los informes.** 14 documentos `.md`: los nueve análisis de la Fase 2, la metodología de muestreo, el estudio de viabilidad del mapa, la auditoría cruzada, la evaluación de cumplimiento y la comparación de métodos de recuperación | `03_informes/analisis_fase2/metodologia_muestreo.md` |
| **`04_auditoria/`** | **La evidencia.** `repo_original/`: los **236 archivos** del commit auditado, byte a byte, con `manifiesto_sha256.csv`; `repo_mejorado/`: el mismo código con **30 arreglos** documentados en su `CHANGELOG.md`; los scripts de extracción y verificación; y `ERRATA.md` con las contradicciones conocidas del proyecto auditado | `04_auditoria/README.md` |
| **`05_entregas/`** | **Lo entregado al docente.** `ENTREGA_1/` (anteproyecto, diapositivas, guía de estudio y tarjetas) y `entregables_2Corte/` (entregas 1–5 del segundo corte) | `05_entregas/ENTREGA_1/LEEME_ENTREGA_1.md` |

Fuera de esas cinco: **`documentacion_auditoria/`** es el sistema de auditoría
(pipeline `src/`, documentos LaTeX, PDFs, ZIP de Overleaf y la memoria del agente
en `data/memoria/`), y **`_archivo/`** guarda los scripts de una sola vez y los
logs que son evidencia de trabajo.

> **Por qué `documentacion_auditoria/src/` y `data/` no se movieron:** sus scripts
> resuelven las rutas con `Path(__file__)` y las 17 reglas leen la memoria del
> agente (índice RAG, grafo, decisiones, validación) desde `data/memoria/`. Mover
> esas carpetas rompería la validación. Lo que sí salieron de ahí son los
> **entregables**: resultados, paneles e informes.

---

## El panel principal

**`02_dashboards/dashboard_fase2.html`** (5,63 MB, autocontenido: Plotly viene
embebido y no hay una sola petición a internet). Ocho pestañas y 18 gráficos:

| Pestaña | Qué responde |
|---|---|
| 1 · Resumen ejecutivo | Qué se entregó y qué lo respalda (comprobaciones automáticas y figuras por análisis) |
| 2 · Territorio y desigualdad (F2-2) | Tasas per cápita por departamento, Gini/Theil entre y dentro de regiones, HHI |
| 3 · Diversidad y falencias (F2-5) | Razones de representación con IC de Wilson y la trampa del denominador |
| 4 · Redes y clustering (F2-4, F2-6) | Co-filiación institucional frente a tres modelos nulos y el clustering formalizado |
| 5 · Supervivencia y género (F2-10) | Kaplan-Meier, Cox y por qué el efecto del género es de composición |
| 6 · Calidad y reproducibilidad (F2-3, F2-7) | Modelo estrella y la regla de unicidad de IDs: documentada frente a implementada |
| 7 · Límites y falencias | Qué se cerró, qué no es evaluable y qué queda pendiente |
| 8 · Flujos y migración (F2-11) | Mapa de los 33 departamentos con las 808 mudanzas de 2013–2021 y la migración acumulada por nacimiento |

Cada gráfico explica **qué se hizo**, **por qué**, **qué teoría lo respalda** y
**cómo se lee**; al final hay un índice de 32 conceptos con buscador.

Los otros cuatro paneles, del mismo tamaño y también offline:

| Archivo | Qué es |
|---|---|
| `02_dashboards/dashboard_eda.html` | EDA de la Fase 1: 17 gráficos en 4 pestañas (univariado, bivariado, varianza, supuestos) |
| `02_dashboards/herramienta_trayectorias.html` | Visor individual del padrón: consulta por ID, institución, área o categoría (30 086 fichas) |
| `02_dashboards/mapa_migracion.html` | El mapa de flujos de la F2-11 en su versión suelta (las dos definiciones de migración, conmutables) |
| `02_dashboards/grafo_interactivo.html` | Grafo de la memoria del agente (criterios → documentos) |

---

## Cómo se ejecutan las validaciones

Todo el sistema se valida con las **17 reglas** del agente antes de dar una cifra
por buena. Se corre desde `documentacion_auditoria/src/`:

```bash
cd documentacion_auditoria/src
python -m memoria indexar     # solo la primera vez: el índice RAG no se versiona
python -m memoria validar     # 17 reglas · exit 1 si alguna FALLA
python -m memoria evidencia   # informe legible de la última corrida
```

**Estado actual: 15 PASA · 0 FALLA · 2 ADVERTENCIA.** Las dos advertencias son
declaradas y revisadas: **R12** (solapamiento entre documento completo y LITE) y
**R15** (la técnica TF-IDF se conserva como respaldo declarado de la decisión
D007). Las reglas cubren, entre otras cosas, que cada criterio tenga su par
completo/LITE, que la línea de tiempo coincida con el `git log` real, que todo
archivo de código auditado esté referenciado, que el índice RAG cubra el corpus,
que no haya contradicciones numéricas entre documentos y que las cifras del
sistema citadas en la documentación no se queden atrás.

Además hay verificadores de los entregables, que también corren sin red:

```bash
python documentacion_auditoria/src/verificar_mapa.py            # mapa F2-11: 64 comprobaciones
python documentacion_auditoria/src/verificar_dashboard_fase2.py # panel F2: 77 comprobaciones
python documentacion_auditoria/src/verificar_consistencia.py    # cifras contra fuentes: 7/7
python 04_auditoria/verificar_hashes.py                         # copia auditada: 236/236 idénticos
```

`verificar_dashboard_fase2.py` comprueba, entre otras cosas, que el panel no
tenga referencias externas, que los datos de cada gráfico sean los del JSON de su
análisis, que los 33 polígonos del mapa estén embebidos y unidos por código
DIVIPOLA, que la pestaña 8 dibuje **exactamente** las mismas trazas que el mapa
suelto y que el panel no pase de 6 MB.

---

## Validar sin instalar nada (Docker)

La imagen instala solo lo que el gate necesita: ni Chrome, ni `torch`, ni
`sentence-transformers` (esos quedan en el grupo opcional `ml` del
`pyproject.toml`).

```bash
docker build -t observatorio .      # construye
docker run --rm observatorio        # 17 reglas · exit 1 si alguna FALLA
```

Salida esperada, la misma que en local:

```
[memoria] reglas: 15 PASA, 0 FALLA, 2 ADVERTENCIA
```

Para desarrollo, `docker-compose.yml` monta el directorio actual:

```bash
docker compose run --rm observatorio          # valida
docker compose run --rm observatorio bash     # consola dentro de la imagen
```

**Sobre el CSV.** El repositorio de Git contiene el CSV completo de datos.gov.co
(`01_datos/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv`,
31,3 MB). La imagen de Docker es ligera y **no** lo incluye, pero el
`docker-compose.yml` monta la carpeta local (`./01_datos:/app/01_datos`) para que
los análisis de Fase 2 puedan reproducirse sin problemas: dentro del contenedor
el archivo aparece en su ruta habitual, como si estuviera dentro.

Tres detalles más que explican el diseño: `python -m memoria validar` exige que el
directorio de trabajo sea `documentacion_auditoria/src`; el motor de exportación
de imágenes es **`plotly-mirage`**, no `kaleido` (no hay navegador ni descarga de
Chrome dentro del contenedor); y el `.dockerignore` deja fuera 3,21 GB de los
3,23 GB del árbol —historial de git, el clon antiguo del repositorio, las copias
auditadas, los dashboards entregados y ese CSV—, con lo que el contexto de build
queda en **27,9 MB**. El suelo no se puede bajar más: `documentacion_auditoria/`
(`data`, `latex` y `pdf`) lo necesitan las propias reglas — sin `pdf/`, R10 y R17
pasan a FALLA.

*(El `Dockerfile` se entrega sin construir: el entorno donde se preparó esta
entrega no tiene daemon de Docker. Los comandos de arriba son los que hay que
correr; el detalle de lo verificado y lo no verificado está en el informe.)*

---

## Reproducir el análisis

Requiere Python 3.11+ con `pandas`, `numpy`, `scipy`, `scikit-learn`,
`matplotlib`, `networkx`, `plotly` y `PyYAML` (y `pyvis` para el grafo
interactivo). Los análisis estadísticos no dependen de `statsmodels`.

```bash
# ── Desde la raíz del repositorio ───────────────────────────────────────────
# 1. Análisis, en orden (escriben sus JSON en 01_datos/resultados_json/)
python documentacion_auditoria/src/analisis_longitudinal.py
python documentacion_auditoria/src/eda_longitudinal.py
python documentacion_auditoria/src/estimadores_longitudinal.py
python documentacion_auditoria/src/diagnosticos_greg.py

# 2. Análisis de la Fase 2 (cada uno escribe su JSON y sus figuras)
python documentacion_auditoria/src/percapita_territorial.py     # F2-2
python documentacion_auditoria/src/modelo_estrella_6.py         # F2-3
python documentacion_auditoria/src/redes_modelos_nulos.py       # F2-4
python documentacion_auditoria/src/diversidad_inferencia.py     # F2-5
python documentacion_auditoria/src/clustering_formalizado.py    # F2-6
python documentacion_auditoria/src/validar_unicidad.py          # F2-7
python documentacion_auditoria/src/supervivencia.py             # F2-10
python documentacion_auditoria/src/preparar_geojson.py          # F2-11 (una vez)
python documentacion_auditoria/src/flujos_territoriales.py      # F2-11

# 3. Paneles (escriben en 02_dashboards/)
python documentacion_auditoria/src/generar_dashboard_eda.py
python documentacion_auditoria/src/generar_dashboard_fase2.py
python documentacion_auditoria/src/construir_herramienta.py
python documentacion_auditoria/src/mapa_migracion.py

# 4. PDFs (lleva la puerta de validación: aborta si alguna regla FALLA)
python documentacion_auditoria/src/compilar.py
```

Las dos copias del repositorio auditado se verifican y se reconstruyen aparte:

```bash
python 04_auditoria/verificar_hashes.py            # repo_original: 236/236 idénticos
python 04_auditoria/construir_repo_mejorado.py     # repo_mejorado = repo_original + estructura
python 04_auditoria/aplicar_arreglos.py            # aplica los 30 arreglos declarados
python 04_auditoria/verificar_arreglos.py          # comprueba que siguen cuadrando
python 04_auditoria/probar_librerias_reales.py     # los scripts arreglados, con librerías reales
```

> El orden importa: primero la integridad de la evidencia, luego construir, luego
> aplicar y al final verificar. Los dos últimos **ejecutan** el código en una copia
> desechable y reportan lo que ven; no modifican `repo_mejorado/`.

> El CSV fuente se lee de `01_datos/datos_fuente/` y **nunca se modifica**: el
> proyecto es de solo lectura sobre los datos.

---

## Estado del sistema

| | |
|---|---|
| **Reglas de validación** | **15 PASA · 0 FALLA · 2 ADVERTENCIA** (17 reglas) |
| Advertencias | **R12** (solapamiento completo/LITE) y **R15** (excepción declarada de la decisión D002) |
| **Compilación** | `compilar.py` compila **sin `--forzar`**: la puerta de reglas no aborta |
| Commit auditado | `1528939` |
| Verificación de la copia | 236/236 archivos idénticos al commit (`04_auditoria/verificar_hashes.py`) |
| **Código mejorado** | `04_auditoria/repo_mejorado/`: **30 arreglos** declarados en su `CHANGELOG.md` y verificables con `04_auditoria/verificar_arreglos.py` |
| **Paneles** | 5 HTML autocontenidos; el principal, `02_dashboards/dashboard_fase2.html` (5,63 MB, 18 gráficos, 8 pestañas) |

Las decisiones de diseño están en
**`documentacion_auditoria/data/memoria/decisiones.yaml`** (D001–D010), con
justificación, alternativas descartadas y evidencia medida; R15 comprueba que
cada decisión vigente coincide con el código. Las fuentes externas consultadas
están en `documentacion_auditoria/data/memoria/fuentes_externas.yaml`.

---

## Para el docente — qué se califica

| Qué es | Archivo | Bloque de la rúbrica |
|---|---|---|
| **Documento (anteproyecto)** | `documentacion_auditoria/pdf/anteproyecto.pdf` | **Documento (D1–D5) · 40 %** |
| **Diapositivas de la sustentación** | `documentacion_auditoria/pdf/diapositivas_anteproyecto.pdf` | **Sustentación (S1–S3) · 60 %** |
| Guía de estudio (apoyo) | `documentacion_auditoria/pdf/guia_estudio.pdf` | repaso y banco de preguntas |
| Tarjetas frase por frase (apoyo) | `documentacion_auditoria/pdf/tarjetas_sustentacion.pdf` | ensayo de la sustentación |

La **declaración de uso de IA** está en la sección 6.2 del anteproyecto, con los
informes de validación en `documentacion_auditoria/data/validacion/`. La
declaración ampliada y el reparto del trabajo están en
[`DECLARACION_IA_Y_REPARTO.md`](DECLARACION_IA_Y_REPARTO.md).

---

## Nota sobre la reorganización (octubre de 2026)

El repositorio se reordenó para el próximo grupo en cinco carpetas numeradas. Se
movieron con `git mv` (el historial de cada archivo se conserva) y se
reescribieron las rutas en todo el código y la documentación:

- **Sí se movieron:** los 8 JSON de resultados, los 5 paneles HTML, los 14
  informes de la Fase 2, los datos fuente, las dos copias del proyecto auditado y
  las dos carpetas de entregas.
- **No se movieron:** `documentacion_auditoria/src/`, `data/`, `latex/`, `pdf/`,
  `zip_overleaf/` y `data/validacion/`. Las reglas leen la memoria del agente y
  las fuentes LaTeX desde esas rutas exactas; además, reescribir las fuentes que
  vigila la regla R13 (frescura del índice) la habría degradado.
- **Los snapshots no se reescriben:** `04_auditoria/repo_original/` y
  `04_auditoria/repo_mejorado/` son copias exactas (la primera verificada con
  manifiesto SHA-256) y conservan su contenido tal como se auditó o construyó.
- **Los informes LaTeX ya entregados y `data/validacion/`** conservan las rutas
  de la época: son registros fechados, no documentación viva.

Antes de publicar el mapa y el panel de la Fase 2 se corrieron las 17 reglas y los
verificadores; el estado quedó en 15/0/2 y en verde todo lo demás.
