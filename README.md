# Observatorio MinCiencias — Auditoría estadística

Este repositorio reúne el trabajo de consultoría estadística sobre el **Observatorio de
investigadores reconocidos por MinCiencias**, el proyecto que realizó otro grupo de la
asignatura. Aquí está la auditoría de su repositorio —qué afirma, qué puede demostrar y
qué no—, los nueve análisis propios que hicimos sobre los mismos datos, los paneles que
los muestran y el sistema que verifica automáticamente que las cifras sigan cuadrando.

Está pensado para que lo puedas usar sin conocer el proyecto de antes: hay datos en
bruto, resultados en JSON, informes en Markdown, PDFs, siete paneles interactivos y una
bitácora que explica las decisiones. Todo son archivos de texto y datos abiertos; no hace
falta ninguna cuenta, ningún servicio en la nube y, salvo para instalar dependencias,
tampoco conexión a internet.

## Antes de empezar — qué necesitas

| Necesitas | Versión | ¿Para qué? |
|---|---|---|
| **Python** | 3.11 o superior (verificado aquí: **3.11.9**) | Todo el sistema de análisis y validación |
| **Poetry** | 2.x (verificado aquí: **2.5.1**) | Instalar las dependencias declaradas en `pyproject.toml` |
| **Git** | cualquiera reciente | Clonar y versionar |
| **Docker** | opcional | Validar el sistema sin instalar Python ni nada más |
| **LaTeX / TinyTeX** | opcional | Solo si quieres recompilar los PDFs (`latexmk`) |
| **Espacio en disco** | unos **4 GB** libres | Medido: árbol de trabajo 728 MB + dependencias ≈ 400 MB + historial de Git 2,5 GB ≈ 3,6 GB |

## Clonar en 3 pasos

```bash
git clone https://github.com/KevinG47/Consultoria.git
cd Consultoria
poetry install          # instala las 25 dependencias del grupo principal
```

Si no usas Poetry, basta con instalar los mismos paquetes con `pip`:

```bash
pip install numpy pandas scipy scikit-learn networkx plotly pyyaml matplotlib plotly-mirage
```

⚠️ **AVISO, el paso que hace fallar a todo el mundo.** El archivo
`01_datos/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv`
(**32.836.667 bytes**) es un marcador de OneDrive: existe en el repositorio, pero su
contenido no está descargado en el disco. Antes de usarlo, clic derecho sobre el archivo
→ **«Siempre disponible en este dispositivo»** (o ábrelo una vez y espera). Si no lo
haces, los análisis fallan con `invalid file request` o `Acceso denegado`.

## ¿Qué quieres hacer? — elige tu ruta

| Quiero… | Comando / acción | Dónde se explica |
|---|---|---|
| **Ver los paneles** | doble clic en `02_dashboards/servir_presentacion.bat` | `06_bitacora_ia/00_LEEME.md` |
| **Verificar que todo cuadra** | `python -m memoria validar` (desde `documentacion_auditoria/src`) | § Estado del sistema, más abajo |
| **Usar Docker** | `docker build -t observatorio .` y `docker run --rm observatorio` | `COMANDOS.md` § Docker |
| **Leer los informes** | abrir `03_informes/analisis_fase2/` | `06_bitacora_ia/00_LEEME.md` |
| **Abrir la bitácora** | Obsidian → *Open folder as vault* → `06_bitacora_ia/` | `06_bitacora_ia/00_LEEME.md` |
| **Entender los datos** | `01_datos/` | `06_bitacora_ia/04_mapa_carpetas.md` |
| **Recompilar los PDFs** | `python documentacion_auditoria/src/compilar.py objetivo_1` | `COMANDOS.md` § Compilar PDFs |
| **Trabajar con el repositorio auditado** | `04_auditoria/repo_original/` | § Qué NO tocar, más abajo |

## Qué hay en el repositorio — mapa de carpetas

| Carpeta | Qué contiene |
|---|---|
| **`01_datos/`** | `datos_fuente/` con el padrón de MinCiencias (32.836.667 bytes) y las tablas del DANE con su procedencia; `resultados_json/` con los **8 JSON** de resultados de los análisis |
| **`02_dashboards/`** | **7 paneles HTML** (6 de ellos autocontenidos, sin conexión) y el lanzador `servir_presentacion.bat`: el panel de la Fase 2, el exploratorio, el visor de trayectorias, el panel del modelo de ML, el mapa de flujos, el grafo y la portada de navegación |
| **`03_informes/`** | `analisis_fase2/` con **14 informes** en Markdown: los nueve análisis, la metodología de muestreo, el estudio de viabilidad del mapa, la auditoría cruzada, la evaluación de cumplimiento y la comparación de métodos |
| **`04_auditoria/`** | La evidencia: `repo_original/` (los **236 archivos** del commit auditado, byte a byte, con su manifiesto de hashes), `repo_mejorado/` (el mismo código con **34 arreglos** documentados), los scripts de verificación y `ERRATA.md` |
| **`05_entregas/`** | Lo entregado al docente: `ENTREGA_1/` (anteproyecto, diapositivas, guía y tarjetas) y `entregables_2Corte/` (las cinco entregas del segundo corte) |
| **`06_bitacora_ia/`** | **8 notas** en Markdown que explican el proyecto por dentro: decisiones, arquitectura, reglas, mapa de carpetas, qué no tocar y Docker. Pensadas para leerse en Obsidian |
| **`documentacion_auditoria/`** | El sistema de auditoría: `src/` (código), `data/` (resultados internos y metadatos), `latex/` y `pdf/` (los documentos), `scripts/` y el ZIP de Overleaf |
| **`_archivo/`** | Scripts de una sola vez y registros de trabajo. No se usa en la ejecución normal, pero es evidencia |

> **La antigua carpeta de datos originales ya no existe.** Se renombró a `01_datos/` y
> `04_auditoria/` en el commit `4399ff7`, cuando el repositorio se reorganizó para dejarlo
> listo para el próximo grupo. Si encuentras esa ruta en algún documento antiguo, esta es
> la traducción.

## Estructura del repositorio

```
consultoria/
├── 01_datos/                 Padrón de MinCiencias (CSV 31,3 MB), tablas DANE y sus procedencias
├── 02_dashboards/            7 paneles HTML y el lanzador servir_presentacion.bat
├── 03_informes/              14 informes de la Fase 2 en Markdown
├── 04_auditoria/             Evidencia: repo_original (236 archivos), repo_mejorado, verificadores y ERRATA
├── 05_entregas/              Entregas al docente (anteproyecto, diapositivas, segundo corte)
├── 06_bitacora_ia/           8 notas internas: decisiones, arquitectura, mapa de carpetas, Docker
├── 07_modelo/                Fase 3 · modelo de ML (detalle abajo)
├── documentacion_auditoria/  Sistema de auditoría: src/, data/, latex/, pdf/ y scripts/
├── _archivo/                 Scripts de una sola vez y registros de trabajo (evidencia, no se ejecuta)
├── datos_originales/         Copia de trabajo de datos originales
├── README.md · COMANDOS.md · contexto_deepseek.md · DECLARACION_IA_Y_REPARTO.md
└── Dockerfile · docker-compose.yml · pyproject.toml · poetry.lock
```

**Dentro de `07_modelo/`:**

```
07_modelo/
├── documentacion/      Criterios de Minciencias, estado del arte, auditoría de la base y notas de Laya
├── modelado/           Scripts de modelado y experimentos, model_card y bitácora de validación
│   ├── modelos/        Modelos entrenados (.joblib) y sus configuraciones
│   └── resultados/     Un JSON por corrida y los logs de cada experimento
├── datos/derivados/    Parquets del dataset del modelo (incluido el dataset limpio)
├── dashboard/          Generador del dashboard del modelo y sus umbrales
├── ingesta/            Descarga y validación de produccion_grupos.csv, con manifiestos
├── .cache/             Caché local de Hugging Face (914 MB, NO versionada)
└── .venv-bayes/        Entorno Python del modelado (1,7 GB, NO versionado)
```

## Qué NO tocar (y por qué)

- **`documentacion_auditoria/src/`, `data/` y `latex/`.** El código calcula sus rutas
  relativas desde su propia ubicación y las 17 reglas de validación leen los metadatos de
  `documentacion_auditoria/data/memoria/`. Si mueves esas carpetas, el sistema deja de
  encontrar sus archivos y la validación falla en cascada.
- **`04_auditoria/repo_original/`.** Es la prueba: los 236 archivos del repositorio
  auditado, idénticos al commit `1528939`, con su hash en
  `04_auditoria/manifiesto_sha256.csv`. Si se edita un solo archivo, la auditoría deja de
  ser verificable.
- **`04_auditoria/repo_mejorado/`.** Es la copia con los arreglos aplicados, y se
  reconstruye desde cero con `04_auditoria/construir_repo_mejorado.py`. Se puede leer y
  ejecutar, pero conviene no editarla a mano: se perdería al reconstruirla.

## Estado del sistema (resumen)

| | |
|---|---|
| Reglas de validación | **15 PASA · 0 FALLA · 2 ADVERTENCIA** (17 reglas) |
| Grafo de relaciones | **255 nodos / 500 aristas** |
| Sistema de búsqueda | **195 fragmentos** indexados de **28 documentos** |
| Paneles | **7 HTML** (6 autocontenidos) + `servir_presentacion.bat` |
| Bitácora | **8 notas** en `06_bitacora_ia/` |
| Archivos versionados | **1.252** |

Las dos advertencias no son errores: son excepciones **declaradas y revisadas**. Una
detecta una sección resumida que quedó copiada igual que la del documento completo; la
otra registra que la técnica anterior de búsqueda se conserva a propósito, guardada como
respaldo. El sistema las muestra en lugar de esconderlas, y no bloquea la compilación.

## Resultados del modelo de ML

Modelo operativo: **XGBoost con máscaras estructurales** por categoría de origen
(Junior no puede bajar; Emérito excluido), 172 features de producción, umbral de
«baja» 0,15. Evaluado **una sola vez** en la cohorte 2021 (13 355 transiciones).

| Métrica (test, 2019→2021, n = 13 355) | Valor |
|---|---|
| **F1 «baja»** | **0,4234** |
| **Recall «baja»** | **0,7878** |
| **Precisión «baja»** | 0,2895 |
| F1 macro | 0,5109 |
| Brier multiclase | 0,4692 |

- **Uso previsto:** priorizar la revisión humana. Detecta ~79 % de los descensos,
  pero 1 de cada 3,4 alertas es correcta: no sirve para decidir solo.
- **Generalización a investigadores nuevos** (benchmark de entidad disjunta):
  F1 «baja» 0,4016, es decir −2,18 pp. El modelo es robusto, pero su alcance es
  la población ya registrada.
- **Nueve palancas de mejora probadas y ninguna superó el +2 pp**: el límite es
  del dato, no del método. Detalle en `07_modelo/modelado/validacion_honesta.md`.

## Problemas conocidos

| Síntoma | Causa | Solución |
|---|---|---|
| `invalid file request` / `Acceso denegado` al leer el CSV | Marcador de OneDrive sin descargar | Clic derecho → «Siempre disponible en este dispositivo» |
| Los paneles salen en blanco dentro de la portada | Abriste los HTML con doble clic (`file://`): el navegador bloquea incrustar páginas locales | Usa `02_dashboards/servir_presentacion.bat` |
| `failed to connect to the docker API` | Docker Desktop no está en marcha | Abre Docker Desktop y espera a que diga «running» |
| Se generan 12 PDFs de golpe | `compilar.py` sin nombre de proyecto compila **todos** | Pasa siempre el proyecto: `compilar.py objetivo_1` |
| Aparecen dos JSON modificados tras validar | `memoria validar` reescribe su propio estado (solo el campo `fecha`) | `git checkout -- documentacion_auditoria/data/memoria/grafo_resumen.json documentacion_auditoria/data/memoria/validacion_reglas.json` |
| El panel dice «el CSV de 1,2 GB **con las revistas**» y debería decir «con los productos publicados, con la revista de cada uno» | Texto literal en `documentacion_auditoria/src/generar_dashboard_fase2.py`, compilado dentro de `02_dashboards/dashboard_fase2.html` (4 apariciones). **No corregible sin recompilar** el panel (5,6 MB, 8 pestañas): no hay edición segura del HTML sin pasar `verificar_dashboard_fase2.py` | Editar el literal en el generador, recompilar con `python documentacion_auditoria/src/generar_dashboard_fase2.py` y validar con `verificar_dashboard_fase2.py` |

**Panel adicional:** `02_dashboards/dashboard_modelo.html` — dashboard del modelo de ML
(XGBoost con máscaras, F1 baja 0.4234, 26-oct-2026). Se abre desde el panel «04 · Modelo de
ML» de la portada (`servir_presentacion.bat`).

## Documentación clave

| Documento | Qué contiene |
|---|---|
| [`07_modelo/documentacion/criterios_minciencias.md`](07_modelo/documentacion/criterios_minciencias.md) | Criterios oficiales de Minciencias para el reconocimiento, la categorización y la transición de investigadores, con citas a los documentos fuente |
| [`07_modelo/documentacion/estado_del_arte.md`](07_modelo/documentacion/estado_del_arte.md) | Literatura sobre predicción de movilidad académica, modelos ordinales, desbalanceo, validación temporal y redes de coautoría |
| [`07_modelo/documentacion/auditoria_base_datos.md`](07_modelo/documentacion/auditoria_base_datos.md) | Auditoría de la base: fuga por identidad (64,31 %), EDA de diagnóstico, benchmark A−B y modelo limpio |
| [`07_modelo/documentacion/laya_y_open_weights.md`](07_modelo/documentacion/laya_y_open_weights.md) | Evaluación de Laya y de los modelos tabulares con pesos abiertos (TabICLv2, TabPFN-2.5) |
| [`07_modelo/modelado/model_card.md`](07_modelo/modelado/model_card.md) | Ficha técnica del modelo: datos, configuración, métricas, limitaciones y reproducibilidad |
| [`07_modelo/modelado/validacion_honesta.md`](07_modelo/modelado/validacion_honesta.md) | Bitácora de validación: rondas, palancas descartadas y cierre por techo del dato |

## Dónde seguir leyendo

- **`COMANDOS.md`** — la chuleta de copiar y pegar: cada comando con su salida esperada y
  qué hacer si falla.
- **`06_bitacora_ia/00_LEEME.md`** — la puerta de entrada al proyecto: cómo abrirlo en
  Obsidian, por dónde empezar y qué no tocar.
- **`DECLARACION_IA_Y_REPARTO.md`** — qué herramientas de asistencia se usaron, para qué,
  y cómo se repartió el trabajo.
