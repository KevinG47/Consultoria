# `datos_originales/` — datos y fuentes primarias

**Para qué existe.** Para que este repositorio sea **autocontenido**: el próximo
grupo puede clonarlo, reproducir todo el análisis y verificar cualquier cita de la
auditoría **sin clonar el repositorio auditado** ni descargar nada.

## Las tres cosas que hay aquí, y por qué están separadas

| Carpeta | Qué es | Se puede editar | Para qué sirve |
|---|---|---|---|
| `repo_auditado/` | Copia **verbatim** del commit `1528939` (236 archivos) | **NO** | Es la **prueba**: aquí valen los números de línea que citan las 51 fichas y los `.tex` |
| `repo_mejorado/` | El mismo código con **30 arreglos** aplicados (235 archivos) | sí | Es el **código de trabajo**: los 6 scripts que fallaban ya no fallan |
| `datos_fuente/` | El CSV de datos.gov.co que alimenta el análisis | no | La **entrada** de todo el análisis longitudinal y muestral |

**Por qué las dos copias del código y no una.** `repo_auditado/` es evidencia: sus
236 hashes están verificados contra el commit y **no se toca**, porque corregirlo
destruiría la prueba y rompería las 51 fichas que citan líneas exactas. Pero
tampoco sirve para trabajar: 6 de sus scripts fallan. La separación permite
**verificar** contra una copia y **trabajar** sobre la otra, y las dos se
mantienen sincronizadas de forma reproducible:

```bash
python datos_originales/construir_repo_mejorado.py   # repo_mejorado = repo_auditado + estructura
python datos_originales/aplicar_arreglos.py          # aplica los 30 arreglos declarados
python datos_originales/verificar_arreglos.py        # comprueba: 0 fallos
python datos_originales/verificar_hashes.py          # repo_auditado sigue intacto
```

`repo_mejorado/CHANGELOG.md` documenta cada arreglo con su cita de la ficha y
cómo se probó. `repo_mejorado/README.md` explica qué funciona ya y cómo usarlo.

| Contenido | Archivos | Peso | Qué es |
|---|---:|---:|---|
| `repo_auditado/` | 236 | 37,40 MB | Copia **verbatim** del contenido versionado del proyecto auditado |
| `repo_mejorado/` | 235 | 37,43 MB | El mismo código con los arreglos aplicados |
| `datos_fuente/` | 1 | 31,32 MB | El CSV que alimenta nuestro análisis longitudinal y muestral |
| `manifiesto_sha256.csv` | 1 | 27 KB | SHA-256 de cada uno de los 236 archivos verbatim |
| `extraer_repo_auditado.py` | 1 | — | Cómo se generó la copia verbatim (re-ejecutable si hay clon) |
| `verificar_hashes.py` | 1 | — | Comprueba la integridad de la copia verbatim (faltantes **y sobrantes**) |
| `construir_repo_mejorado.py` | 1 | — | Construye `repo_mejorado/` desde la copia verbatim |
| `aplicar_arreglos.py` | 1 | — | Los 30 arreglos, declarados con su ancla y su justificación |
| `verificar_arreglos.py` | 1 | — | Verifica los arreglos (6 niveles de comprobación) |
| `probar_librerias_reales.py` | 1 | — | Ejecuta los 6 scripts con las librerías de verdad y comprueba qué salidas se regeneran |
| `fs_robusto.py` | 1 | — | Borrado de árboles tolerante a OneDrive (reparse points de solo lectura y carpeta bloqueada) |
| `_stubs/` | 4 | — | Dobles de prueba para poder ejecutar sin seaborn/plotly/duckdb |
| `README.md`, `ERRATA.md` | 2 | — | Este archivo y las contradicciones conocidas del auditado |


---

## De dónde viene cada cosa

### `repo_auditado/` — proyecto auditado

- **Repositorio:** [`ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8`](https://github.com/ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8)
- **Commit:** `1528939` (merge del PR #23, rama `main`)
- **Alcance:** los **236 archivos rastreados por git** en ese commit. Nada más.

### 🔴 Por qué se extrajo con `git show HEAD:` y no copiando el disco

El *working tree* del clon local estaba **sucio**: las ejecuciones de la propia
auditoría (correr los 16 scripts `sprint*`) sobrescribieron **38 archivos
rastreados** —20 PNG de `artifacts/`, 3 HTML y 15 de `evidencias/`, entre ellos
`calidad_resumen.json` y `calidad_atipicos_edad.csv`—.

Copiar del disco habría transferido **evidencia falsificada**: el disco dice
`n_atipicos_edad = 19` (calculado sobre el XLSX parcial de 50 891 filas) mientras
el commit dice `22` (sobre las 77 237 declaradas). Ver `ERRATA.md` §E1.

Por eso `extraer_repo_auditado.py` recorre `git ls-files` y escribe el blob de
`git show HEAD:<ruta>`, byte a byte. Los hashes del manifiesto son hashes del
**contenido versionado** (finales de línea LF), no de los archivos del *working
tree* en Windows (CRLF). `verificar_hashes.py` compara primero el hash exacto y
solo si falla reintenta normalizando CRLF→LF **y solo en archivos de texto**.

### `datos_fuente/` — la base de nuestro análisis

| | |
|---|---|
| Archivo | `Investigadores_Reconocidos_por_convocatoria_20261006.csv` |
| Origen | datos.gov.co, dataset `bqtm-4y2h` — *Investigadores reconocidos por convocatoria* |
| Descarga | 2026-10-06 |
| SHA-256 | `9A55DD87F5F571B1B82A834372F2F037C521AE4F02536F164D427D1C16CA9565` |
| Contenido | 77 237 registros · 30 086 personas · 6 convocatorias (2013–2021) · 30 columnas |

**No viene del repositorio auditado.** El auditado **no versiona este archivo**
(`datos/raw/` contiene solo `.gitkeep` y lo crudo está en su `.gitignore`): lo que
versiona es un consolidado derivado de 50 891 filas y 3 convocatorias
(`repo_auditado/datos/tarea_join/`). Por eso hacían falta **las dos** cosas:
nuestro CSV para reproducir el análisis y el consolidado para auditar qué
versionó el proyecto.

Antes vivía en `Datos/` en la raíz y estaba en `.gitignore`, de modo que **al
clonar el repositorio no había datos y ningún script del análisis funcionaba**.
Ahora está versionado (31,32 MB, bajo el límite de 100 MB de GitHub) y las cuatro
etapas del pipeline lo leen desde aquí.

---

## Qué se transfirió tal cual

**Los 236 archivos, sin excepción y sin editar un byte.** El desglose:

| Carpeta | Archivos | MB | Para qué sirve |
|---|---:|---:|---|
| `evidencias/` | 85 | 0,74 | Evidencia calculada que citan las fichas y los `.tex` |
| `artifacts/` | 48 | 5,06 | Figuras PNG/HTML por sprint (banco de figuras) |
| `notebooks/` | 26 | 1,25 | Las 5 tareas académicas previas (R, Python, notebooks) |
| `scripts/` | 17 | 0,15 | `sprint2_*` … `sprint6_*`: lo que se auditó y se ejecutó |
| `docs/` | 17 | 1,01 | `informe_final.tex`, `manual.ipynb`, presentación |
| `src/` | 15 | 0,07 | `ingesta/`, `analisis/`, `modelo/`, `Transformacion.py` |
| `datos/` | 5 | 25,94 | Consolidado versionado (CSV 18,0 MB + XLSX 8,0 MB) y `catalogo.yaml` |
| `hallazgos/` | 2 | 0,35 | Grafos interactivos PyVis |
| `lib/` | 5 | 0,71 | JS/CSS de vis-network y tom-select: **sin esto los HTML de `hallazgos/` no renderizan offline** |
| `app/`, `tests/`, `models/`, `.github/`, `.streamlit/` | 6 | ~0 | Placeholder, test, workflow CI y config |
| raíz | 10 | 0,39 | `README.md`, `informe_final.md`, `MARCO_TEORICO.md`, `CONTRIBUTING.md`, `Dockerfile`, `pyproject.toml`, `requirements.txt`, `poetry.lock`, `streamlit_app.py`, `.gitignore` |

**Verificación:**
```bash
python datos_originales/verificar_hashes.py
# manifiesto: 236 archivos (repo_auditado@1528939)
#   identicos : 236     faltantes : 0     distintos : 0
```

### Qué se dejó FUERA de la copia (y por qué)

| Excluido | Peso | Razón |
|---|---:|---|
| `.venv/` del clon | **383,8 MB / 14 267 archivos** | Entorno virtual: 91 % del peso del clon y no es contenido |
| `.git/` del clon | 19,4 MB | No se puede versionar una carpeta con `.git` dentro (git la trata como repo embebido); para eso están los cachés y el ancla (abajo) |
| `__pycache__/` | 12 archivos | Cachés de bytecode |
| `datos/processed/observatorio.duckdb` | 2,76 MB | **No está versionado en el auditado** (`*.duckdb` está en su `.gitignore`): el que había en disco lo generó la propia auditoría. No es fuente, es salida |

---

## Qué se modificó en NUESTRO repositorio para que esto funcione

La copia del auditado es intocable; lo que hubo que ajustar es el nuestro. El
problema: **las reglas R5, R6, R7 y R9 leían el clon por git y sus cachés estaban
en `.gitignore`**, así que en un clon limpio no había ni caché ni clon.

Comprobado empíricamente apuntando la ruta del clon a una carpeta inexistente:

| Función | Sin clon | Por qué |
|---|---|---|
| `git_log_real()` (R5) | OK, 133 commits | lee el caché… que **no estaba versionado** |
| `git_archivos_reales()` (R6, R9) | OK, 51 archivos | ídem… **no versionado** |
| `commit_auditado_real()` (R7) | **`RuntimeError`** | no tenía respaldo, y se llamaba sin `try/except` en la construcción del grafo → **el programa se caía en vez de reportar R7** |

**Solución adoptada (autocontenida, sin clon):**

| Cambio | Archivo | Efecto |
|---|---|---|
| Ancla del commit | `documentacion_auditoria/data/memoria/commit_auditado.txt` (`1528939`) | Fija el commit del que se extrajo la copia |
| Respaldo en R7 | `src/memoria/grafo.py::commit_auditado_real()` | Usa el clon si existe; si no, el ancla, y **avisa por consola**. Ya no se cae |
| Constante de ruta | `src/memoria/config.py` (`COMMIT_ANCLADO`) | Documenta la decisión |
| Cachés versionados | `.gitignore` | `git_log_real.csv` y `git_ls_files_real.txt` ahora **sí** se versionan: son lo que sostiene R5, R6 y R9 |
| Ruta de datos | 4 scripts (`eda_longitudinal.py`, `estimadores_longitudinal.py`, `analisis_longitudinal.py`, `construir_herramienta.py`) + 5 de `_archivo/` | Leen `datos_originales/datos_fuente/` en vez de `Datos/` |

**Único caso en que hace falta el clon:** `python -m memoria grafo --refrescar-git`
(regenera los cachés desde `git log` / `git ls-files`). Sin clon, se usan los
cachés versionados, que son correctos para el commit `1528939`.

---

## Cómo se usa cada archivo

### 1. Reproducir el análisis (no necesita el auditado)

```bash
python -m memoria indexar                  # 1. regenera el índice RAG (segundos)
python documentacion_auditoria/src/analisis_longitudinal.py   # panel, retención, transiciones
python documentacion_auditoria/src/eda_longitudinal.py        # EDA (metodología, Parte 1)
python documentacion_auditoria/src/estimadores_longitudinal.py # post-estratificación y GREG
python documentacion_auditoria/src/diagnosticos_greg.py       # diagnósticos y g-weights (§7)
python documentacion_auditoria/src/construir_herramienta.py   # visor de trayectorias (HTML)
python -m memoria validar                  # 2. las 17 reglas
python documentacion_auditoria/src/compilar.py                # 3. PDFs (con puerta de reglas)
```

Los cuatro primeros escriben en `documentacion_auditoria/data/memoria/*.json` y
`data/memoria/eda/*.png`; los documentos `metodologia_muestreo.md` y
`analisis_longitudinal.md` se regeneran con `src/generar_metodologia_muestreo.py`
y `src/generar_analisis_longitudinal.py`.

### 2. Verificar una cita de la auditoría

Las fichas de `documentacion_auditoria/data/analisis_codigo/*.json` y los `.tex`
citan archivo y línea (p. ej. `scripts/sprint2_duckdb.py:110`). Abre la ruta
equivalente **dentro de `repo_auditado/`** y compárala: es el mismo contenido que
el commit `1528939`.

### 3. Auditar qué versionó el proyecto

- `repo_auditado/evidencias/` y `repo_auditado/artifacts/`: la evidencia calculada
  y las figuras que el proyecto sí versionó.
- `repo_auditado/datos/tarea_join/`: el consolidado de 3 convocatorias.
- `repo_auditado/datos/catalogo.yaml`: el contrato de datos declarado.
- `ERRATA.md`: las contradicciones entre todo lo anterior.

### 4. Re-extraer la copia (solo si cambia el commit auditado)

```bash
python datos_originales/extraer_repo_auditado.py --dry-run   # informa
python datos_originales/extraer_repo_auditado.py             # extrae + manifiesto
# y actualizar a mano documentacion_auditoria/data/memoria/commit_auditado.txt
```
Requiere el clon en `Observatorio_Ministerio_de_Ciencias_Grupo8/` (la raíz del
repositorio). Ese clon **no se versiona**; solo se necesita para re-extraer.

---

## Trazabilidad

| Dato | Valor |
|---|---|
| Commit auditado | `1528939` |
| Archivos transferidos | 236 (todos los rastreados) |
| Verificación | `manifiesto_sha256.csv` + `verificar_hashes.py` → 236/236 idénticos |
| Integridad de la transferencia | Ningún archivo del auditado fue modificado: la errata es un documento aparte |
