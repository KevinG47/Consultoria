# Observatorio MinCiencias — Auditoría estadística

Este repositorio reúne el trabajo de consultoría estadística sobre el **Observatorio de
investigadores reconocidos por MinCiencias**, el proyecto que realizó otro grupo de la
asignatura. Aquí está la auditoría de su repositorio —qué afirma, qué puede demostrar y
qué no—, los nueve análisis propios que hicimos sobre los mismos datos, los paneles que
los muestran y el sistema que verifica automáticamente que las cifras sigan cuadrando.

Está pensado para que lo puedas usar sin conocer el proyecto de antes: hay datos en
bruto, resultados en JSON, informes en Markdown, PDFs, seis paneles interactivos y una
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
| **`02_dashboards/`** | **6 paneles HTML** (5 de ellos autocontenidos, sin conexión) y el lanzador `servir_presentacion.bat`: el panel de la Fase 2, el exploratorio, el visor de trayectorias, el mapa de flujos, el grafo y la portada de navegación |
| **`03_informes/`** | `analisis_fase2/` con **14 informes** en Markdown: los nueve análisis, la metodología de muestreo, el estudio de viabilidad del mapa, la auditoría cruzada, la evaluación de cumplimiento y la comparación de métodos |
| **`04_auditoria/`** | La evidencia: `repo_original/` (los **236 archivos** del commit auditado, byte a byte, con su manifiesto de hashes), `repo_mejorado/` (el mismo código con **34 arreglos** documentados), los scripts de verificación y `ERRATA.md` |
| **`05_entregas/`** | Lo entregado al docente: `ENTREGA_1/` (anteproyecto, diapositivas, guía y tarjetas) y `entregables_2Corte/` (las cinco entregas del segundo corte) |
| **`06_bitacora_ia/`** | **8 notas** en Markdown que explican el proyecto por dentro: decisiones, arquitectura, reglas, mapa de carpetas, qué no tocar y Docker. Pensadas para leerse en Obsidian |
| **`documentacion_auditoria/`** | El sistema de auditoría: `src/` (código), `data/` (resultados internos y metadatos), `latex/` y `pdf/` (los documentos), `scripts/` y el ZIP de Overleaf |
| **`_archivo/`** | Scripts de una sola vez y registros de trabajo. No se usa en la ejecución normal, pero es evidencia |

> **`datos_originales/` ya no existe.** Esa carpeta se renombró a `01_datos/` y
> `04_auditoria/` en el commit `4399ff7`, cuando el repositorio se reorganizó para
> dejarlo listo para el próximo grupo. Si encuentras esa ruta en algún documento
> antiguo, esta es la traducción.

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
| Sistema de búsqueda | **151 fragmentos** indexados de **25 documentos** |
| Paneles | **6 HTML** (5 autocontenidos) + `servir_presentacion.bat` |
| Bitácora | **8 notas** en `06_bitacora_ia/` |
| Archivos versionados | **1.115** |

Las dos advertencias no son errores: son excepciones **declaradas y revisadas**. Una
detecta una sección resumida que quedó copiada igual que la del documento completo; la
otra registra que la técnica anterior de búsqueda se conserva a propósito, guardada como
respaldo. El sistema las muestra en lugar de esconderlas, y no bloquea la compilación.

## Problemas conocidos

| Síntoma | Causa | Solución |
|---|---|---|
| `invalid file request` / `Acceso denegado` al leer el CSV | Marcador de OneDrive sin descargar | Clic derecho → «Siempre disponible en este dispositivo» |
| Los paneles salen en blanco dentro de la portada | Abriste los HTML con doble clic (`file://`): el navegador bloquea incrustar páginas locales | Usa `02_dashboards/servir_presentacion.bat` |
| `failed to connect to the docker API` | Docker Desktop no está en marcha | Abre Docker Desktop y espera a que diga «running» |
| Se generan 12 PDFs de golpe | `compilar.py` sin nombre de proyecto compila **todos** | Pasa siempre el proyecto: `compilar.py objetivo_1` |
| Aparecen dos JSON modificados tras validar | `memoria validar` reescribe su propio estado (solo el campo `fecha`) | `git checkout -- documentacion_auditoria/data/memoria/grafo_resumen.json documentacion_auditoria/data/memoria/validacion_reglas.json` |

## Dónde seguir leyendo

- **`COMANDOS.md`** — la chuleta de copiar y pegar: cada comando con su salida esperada y
  qué hacer si falla.
- **`06_bitacora_ia/00_LEEME.md`** — la puerta de entrada al proyecto: cómo abrirlo en
  Obsidian, por dónde empezar y qué no tocar.
- **`DECLARACION_IA_Y_REPARTO.md`** — qué herramientas de asistencia se usaron, para qué,
  y cómo se repartió el trabajo.
