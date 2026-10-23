---
id: PUB-MAPA
origen: sintesis
fase: "Mapa del repositorio"
tags: [estructura, mapa, carpetas]
---

# 04 · Mapa del repositorio

El repositorio se organizó para que el próximo equipo lo entienda sin abrir los scripts.
Cinco carpetas numeradas en la raíz y, dentro, el sistema de auditoría propiamente dicho.

## Raíz

| Carpeta | Qué contiene |
|---|---|
| `01_datos/` | Datos fuente: `01_datos/datos_fuente/Investigadores_Reconocidos_por_convocatoria_20261006.csv` y el inventario de datos |
| `02_dashboards/` | Paneles HTML autocontenidos y los archivos para servirlos (ver [[06_docker_y_dashboards]]) |
| `03_informes/` | Análisis en Markdown (longitudinal, per cápita, metodología del muestreo, comparación TF-IDF vs embeddings, evaluación de cumplimiento) |
| `04_auditoria/` | Informes de validación, errata, changelog y resultados de auditoría |
| `05_entregas/` | Documentos de entrega (guiones, resúmenes para el curso) |
| `06_bitacora_ia/` | **Esta bitácora** (vault de Obsidian con la versión pública) |

## `documentacion_auditoria/` — el sistema

| Subcarpeta | Contenido | ¿Se puede mover? |
|---|---|---|
| `src/` | Código: `memoria/` (rag, grafo, reglas), `compilar.py`, `verificar_consistencia.py` | **No** |
| `data/` | Metadatos y registros: `capas.yaml`, `objetivos.yaml`, `glosario.yaml`, `commits_timeline.csv`, `inventario_codigo.csv`, `memoria/` | **No** |
| `latex/` | Fuentes LaTeX de los documentos (criterios, LITE, maestro, anteproyecto) | **No** |
| `pdf/` | PDF compilados (salida, regenerable) | Sí, pero se regenera |
| `zip_overleaf/`, `slides_*/` | Empaquetados y material de presentación | Sí, con cuidado |

## El repositorio auditado

`Observatorio_Ministerio_de_Ciencias_Grupo8` se clona dentro del repositorio de trabajo y se
consulta en modo lectura: de ahí salen el inventario de archivos, el historial de commits y las
evidencias que citan los documentos. **No se modifica.**

## Otros archivos de la raíz

- `README.md`: qué es el proyecto y cómo se corre.
- `pyproject.toml` / `poetry.lock`: dependencias (Python 3.11).
- `Dockerfile`, `.dockerignore`: reproducibilidad (ver [[06_docker_y_dashboards]]).
- `.gitignore`: qué no se versiona (datos pesados, artefactos regenerables).

## Cómo ubicarse rápido

| Quiero… | Voy a… |
|---|---|
| Ver los datos crudos | `01_datos/datos_fuente/` |
| Leer un análisis | `03_informes/analisis_fase2/` |
| Correr la validación | `python -m memoria validar` (desde `documentacion_auditoria/src/`) |
| Compilar un PDF | `python documentacion_auditoria/src/compilar.py` |
| Ver los paneles | `02_dashboards/` (o el contenedor, ver [[06_docker_y_dashboards]]) |
| Entender las reglas | [[03_reglas_validacion]] |

Antes de mover algo, revisa [[05_que_no_tocar]].
