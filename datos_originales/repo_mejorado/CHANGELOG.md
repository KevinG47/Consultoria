# CHANGELOG — `repo_mejorado/`

Registro de los arreglos aplicados sobre `repo_auditado/` (commit `1528939`).
Cada entrada indica **qué**, **en qué archivo**, **por qué** (con la cita de la
ficha de `documentacion_auditoria/data/analisis_codigo/` o del criterio 3) y
**cómo se probó**.

Los arreglos se aplican con `datos_originales/aplicar_arreglos.py`, que declara
cada parche con su ancla y **falla** si el ancla no aparece exactamente una vez.
Se verifican con `datos_originales/verificar_arreglos.py` (dobles solo para lo que
falte de verdad) y con `datos_originales/probar_librerias_reales.py`.

| | |
|---|---|
| Arreglos aplicados | **30** (sobre 17 archivos) + 6 celdas de `docs/manual.ipynb` |
| Módulo nuevo | `src/exportacion.py` |
| Resultado con librerías reales | **3 completos · 3 con código 3 por datos ausentes · 0 errores reales** |
| `repo_auditado/` | intacto: 236/236 hashes verificados, 0 sobrantes |

> ⚠️ Este archivo **no se regenera** al reconstruir `repo_mejorado/`: es un
> documento redactado a mano, y `construir_repo_mejorado.py` lo preserva igual que
> `poetry.lock`. Si desaparece, el verificador lo detecta (los archivos nuevos
> declarados tienen que existir).

---

## Resumen: los 6 scripts que fallaban

| Script | Antes | Ahora (librerías reales) | Arreglo |
|---|---|---|---|
| `scripts/sprint6_geografia_institucional.py` | EXIT=1 `UnicodeEncodeError` | **EXIT=0**, 6/6 salidas | stdout en UTF-8 |
| `scripts/sprint6_sankey_categoria.py` | EXIT=1 `RuntimeError: Kaleido` | **EXIT=0**, CSV + 2 HTML | guardia del motor de imagen |
| `scripts/sprint6_sankey_territorial.py` | EXIT=1 `RuntimeError: Kaleido` | **EXIT=0**, HTML | guardia del motor de imagen |
| `scripts/sprint5_produccion.py` | EXIT=1 traceback | **EXIT=3** con aviso accionable | datos faltantes declarados |
| `scripts/sprint6_ocde_composicion.py` | EXIT=1 traceback | **EXIT=3** con aviso accionable | datos faltantes declarados |
| `scripts/sprint5_duckdb.py` | EXIT=1 traceback | **EXIT=3** con aviso accionable | base y datos declarados |

> **Por qué 3 y no 0 en los tres últimos.** Su única entrada es
> `datos/raw/produccion_grupos.csv` (~1,2 GB, **no versionado**, necesita red).
> Sin esa entrada no pueden producir ni una de sus salidas. Salir con 0 fingiendo
> éxito sería peor que fallar: se sale con **3** ("faltan datos"), distinto de 1
> ("el script falló"), y con el comando exacto para obtenerlos. Es un arreglo
> *declarado*, no una funcionalidad inventada.

---

## A · El motor de imagen: los dos scripts que abortaban

**Qué.** `fig.write_image(...)` se sustituye por `exportar_png(fig, ...)`, un
helper nuevo en **`src/exportacion.py`**.

**Por qué.** Fichas `sprint6_sankey_categoria.py:146-147` y
`sprint6_sankey_territorial.py:125-129`: *"write_image sin comprobación de
kaleido: dependencia implícita que rompe la ejecución en entornos mínimos"*. El
log del pipeline lo confirma: `RuntimeError: Image export requires the Kaleido
package` con `EXIT=1`. Lo grave es **cuándo** falla: después de haber escrito el
HTML, así que se perdía el resto del trabajo y el fallo parecía un bug del script.

**Cómo se probó.** Cuatro casos en `verificar_arreglos.py`, con objetos de prueba:
falta kaleido → `False`; **navegador que no arranca → `False`** (regresión, ver
abajo); motor presente → `True` y escribe; error ajeno → **se propaga** (el guardia
no se traga errores que no son suyos). Y los dos scripts corridos de verdad.

## B · `UnicodeEncodeError` en consola Windows

**Qué.** `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` al inicio de
`scripts/sprint6_geografia_institucional.py`.

**Por qué.** Ficha del script: *"UnicodeEncodeError: flecha U+2192 en print,
Windows cp1252"*. El script tiene 4 literales con `→`; el fatal es el `print` de
la línea 261.

**Cómo se probó.** Con librerías reales: `EXIT=0` y las 3 figuras PNG y los 3 CSV
regenerados. Reconfigurar stdout arregla todos los `print` a la vez.

## C · Datos de producción ausentes: de traceback a aviso accionable

**Qué.** Nuevo `aviso_produccion_ausente(exc) -> int` en `src/ingesta/__init__.py`,
junto a `cargar_produccion()` (una sola fuente del texto). Los tres scripts
envuelven la carga en `try/except FileNotFoundError`, devuelven 3 y cambian
`main() -> None` por `main() -> int` + `raise SystemExit(main())`.

**Por qué.** Ficha `src/ingesta/__init__.py:44-48`: *"cargar_produccion() lanza
FileNotFoundError sin alternativa; en el clon todos los scripts sprint5/sprint6 de
producción mueren en el arranque"*. `sprint5_duckdb.py` tenía además su propia
comprobación de la base DuckDB que lanzaba una excepción en vez de informar.

**Cómo se probó.** Ejecutados los tres: `EXIT=3`, mensaje con el comando exacto
(`python -m src.ingesta.produccion`), **sin traceback**.

## D · `sprint2_duckdb.py`: tres defectos

| Defecto (ficha) | Arreglo |
|---|---|
| `:110` `.fetchdf()` deprecado desde duckdb 0.9 | `.df()` |
| `:104` `resumen_modelo(con)` se imprime pero **no se agrega** a `lineas_reporte`, así que la evidencia guardada omite el resumen que el docstring declara como validación | `resumen_modelo()` ahora **devuelve** el texto y se agrega al reporte |
| `:97-123` sin `try/finally`: una excepción deja la conexión abierta | `try/finally` |

**Nota.** El segundo arreglo exigió tocar `src/modelo/dimensional.py`: allí
`resumen_modelo()` devolvía `None`, así que concatenarlo habría escrito `"None"`
en la evidencia. Un arreglo cosmético que se habría visto como correcto.

## E · `src/analisis/diversidad.py`

### E1 · La contradicción comentario-código — **y una corrección a la auditoría**

**Qué.** Se corrige **el comentario**, no el código.

**Por qué, con evidencia.** La ficha (`:78-79`) y el criterio 3
(`05_codigo.tex:1720`) declaran un *"bug metodológico"*: el comentario manda
excluir `"NINGUN GRUPO ETNICO"` del denominador y el código no lo hace, lo que
supuestamente *"diluye la subrepresentación de minorías"* por un *"denominador
inflado"*.

**Reproduje la función real sobre los datos reales** y el resultado es el contrario:

| | denominador | % afro | razón vs DANE |
|---|---:|---:|---:|
| Código actual | 20 423 | 2,22 % | **3,0×** |
| Si se aplicara el comentario | 629 | 72,02 % | **0,1×** |

El código **reproduce exactamente** `evidencias/diversidad_comparacion_dane.csv`
(fila por fila: afro 453/2,22/3,0; indígena 114/0,56/7,9; discapacidad 181/0,89/8,0;
víctimas 421/2,06/8,6), que es la evidencia que respaldan las cifras publicadas
en el anteproyecto ("afro 3×", "indígena 7,9×").

La razón: `DANE_REFERENCIA["etnia"]` son porcentajes **de la población total**, y
`"NINGÚN GRUPO ÉTNICO"` (19 674 de 20 423 respuestas, el **96 %**) es una
respuesta **declarada**, no un dato faltante. La base comparable es el total de
respuestas conocidas. Excluir a la mayoría mezclaría bases ("qué proporción de
las minorías es afro" contra "qué proporción del país es afro") y daría el
absurdo de afro **sobre**representado.

> ⚠️ **El comentario era el defecto; el código está bien.** Queda documentado
> aquí porque contradice el criterio 3 del entregable. **No he editado el `.tex`
> ni la ficha**: son el producto de auditoría y editarlos obliga a reindexar el
> RAG (R13) y arrastra el recuento de R17. Se deja como decisión del equipo.

### E2 · `KeyError` en `interseccional_genero_etnia`

`unstack(fill_value=0)` no crea la columna `FEMENINO` si ningún grupo étnico
tiene mujeres, y `d["FEMENINO"]` lanzaba `KeyError` (ficha `:145`). Se añade
`.reindex(columns=["FEMENINO", "MASCULINO"], fill_value=0)`. **Probado**: con un
marco sin mujeres ya no lanza.

### E3 · La etiqueta `pct_dane_2018`

La columna se llama así por compatibilidad (la usan `sprint4_diversidad.py`,
`streamlit_app.py` y el CSV de evidencia), pero **la referencia no es toda de
2018**: etnia y discapacidad son del censo DANE 2018 y las víctimas del RUV 2021.
Renombrarla rompería tres consumidores; se documenta la fuente real en el
diccionario `DANE_REFERENCIA` para que la etiqueta no engañe.

## F · `scripts/generar_manual.py` y `docs/manual.ipynb`

El manual es un **artefacto generado**: el código de sus celdas vive como texto
dentro de `generar_manual.py`, y por eso los tres defectos aparecían en los dos
archivos.

| Defecto (ficha) | Arreglo |
|---|---|
| `:197` `print(m["conteos"])` sobre una tupla → `TypeError` | `conteos, _probs = m` |
| `:251` `hhi_por_convocatoria(..., columna=...)` pero el parámetro es `col_geo` → `TypeError` | `col_geo=` |
| `:213`, `:318`, `:357`, `:509` `subprocess.run(["python3", ...])` en Windows → `FileNotFoundError` | `sys.executable` |

**Cómo se probó.** `docs/manual.ipynb` se parchea con `json` (no hace falta
`nbformat`) y el verificador comprueba que **las 26 celdas de código siguen siendo
Python válido** y que ninguno de los tres patrones erróneos queda. Cuando se
quiera, `python scripts/generar_manual.py` regenera el cuaderno con el generador ya
corregido.

## G · `streamlit_app.py`: la app se cerraba en la pestaña de territorio

```python
hhi_df = hhi_por_convocatoria(df, col_geo=col).reset_index()
hhi_df.columns = ["Año", "HHI"]      # ValueError: 5 columnas, 2 nombres
```

`hhi_por_convocatoria` devuelve `HHI`, `n_total` y `n_territorios` además del año.
Se renombra **por nombre** y se seleccionan las dos columnas. Verificado por AST:
no queda ninguna reasignación de columnas a ciegas.

## H · Dependencias que el código importa y el proyecto no declaraba

| Paquete | Dónde se usa | Estado previo |
|---|---|---|
| `openpyxl` | `pd.read_excel` en `cargar_consolidado()` | solo en `requirements.txt` |
| `PyYAML` | `src/ingesta/minciencias.py:19`, `produccion.py:24` | **no declarado** |
| `kaleido` | `fig.write_image()` en los dos sankey | **no declarado** |
| `nbformat` | `scripts/generar_manual.py:16` | **no declarado** |
| `ipython` | celdas del manual generado | **no declarado** |

Se añaden a `pyproject.toml` y se completa `requirements.txt` (declaraba 5
paquetes y no alcanzaba ni para el dashboard). Además se normaliza la indentación
de 4 dependencias que estaban con sangría (inofensivo en TOML, pero engañoso al
leer).

## I · `src/modelo/dimensional.py`: la tercera llamada deprecada

`.fetchdf()` aparecía **tres** veces, no dos: además de los scripts, en
`dimensional.py:293`. Y `resumen_modelo()` no devolvía nada, así que el arreglo D
habría escrito `"None"` en la evidencia. Ahora devuelve el texto.

## J · La guía al frente del README

**Qué.** Se **antepone** una guía a `README.md` señalando qué es esta carpeta, qué
funciona ya y cómo usarla.

**Por qué no se sobrescribe.** El `README.md` de esta carpeta es el del proyecto
auditado (318 líneas) y la auditoría lo cita (`README.md:268, Atípicos de edad:
22 casos (no 10)`). Se conserva intacto debajo de la guía. En `repo_mejorado/` los
números de línea **no** son los del commit (17 archivos cambiaron): las citas de la
auditoría se verifican sobre `repo_auditado/`.

---

## Ejecución con LIBRERÍAS REALES (no dobles)

La verificación original usaba dobles mínimos porque el entorno no tenía
`seaborn`, `plotly`, `kaleido`, `duckdb`, `openpyxl`, `nbformat` ni red para
instalarlos. Con las dependencias ya instaladas se repitió la prueba con las
librerías de verdad:

```bash
python datos_originales/probar_librerias_reales.py
```

| Script | Exit | Salidas regeneradas | Preexistentes |
|---|:--:|---|---|
| `sprint6_geografia_institucional.py` | **0** | **6/6** (3 PNG + 3 CSV) | — |
| `sprint6_sankey_categoria.py` | **0** | 3 (1 CSV + 2 HTML) | 2 PNG (motor de imagen) |
| `sprint6_sankey_territorial.py` | **0** | 1 (HTML) | 1 PNG (motor de imagen) |
| `sprint5_produccion.py` | **3** | — | 2 (faltan datos) |
| `sprint6_ocde_composicion.py` | **3** | — | 2 (faltan datos) |
| `sprint5_duckdb.py` | **3** | — | 1 (faltan datos) |

**3 corren completos · 3 salen con código 3 por datos ausentes · 0 errores reales.**
Versiones usadas: pandas 3.0.6, numpy 2.4.6, matplotlib 3.11.2, seaborn 0.13.2,
plotly 7.1.0, kaleido 1.5.0, duckdb 1.5.6, openpyxl 3.1.5, nbformat 5.11.1.

### 🔴 Defecto que SOLO aparece con librerías reales (y que los dobles ocultaban)

Con las librerías reales los dos scripts de Sankey **seguían muriendo con `EXIT=1`**:

```
choreographer.browsers._errors.BrowserFailedError:
  ('The browser seemed to close immediately after starting.', ...)
```

La causa: **kaleido 1.x ya no dibuja por su cuenta**. Maneja un navegador Chromium
real a través de `choreographer`, y puede fallar de dos formas con excepciones de
módulos distintos:

| Caso | Excepción | ¿Su mensaje menciona «kaleido»? |
|---|---|---|
| kaleido no instalado | `RuntimeError`/`ValueError` | **sí** |
| kaleido instalado, navegador que no arranca | `choreographer…BrowserFailedError` (subclase de `RuntimeError`) | **NO** |

Mi guardia original decidía mirando **el texto del mensaje**, así que el segundo
caso se le escapaba y re-lanzaba la excepción: con los dobles nunca se vio porque
el doble lanzaba el error «clásico», que sí menciona kaleido.

**Arreglo (`src/exportacion.py`)**: `es_fallo_del_motor()` recorre la jerarquía de
la clase y mira el **módulo** (`kaleido`, `choreographer`), que es estable entre
versiones y no depende de cómo esté redactado el mensaje. El aviso ahora distingue
los dos casos y da la instrucción correcta para cada uno. Hay **prueba de
regresión**: `verificar_arreglos.py` caso 1b construye un `BrowserFailedError` de
`choreographer` y exige que el guardia lo absorba.

### Segundo defecto real: el script anunciaba un PNG que no generaba

`sprint6_sankey_categoria.py` imprimía `"{nombre}.html + .png"` **pasara lo que
pasara**. Con el PNG fallando, la consola decía que existía. Ahora el mensaje usa
el valor que devuelve `exportar_png`:

```
sankey_2017_2019.html (PNG no generado: ver aviso)  (16 flujos)
```

### PNG: limitación del entorno, no del script

El navegador que kaleido necesita **no arranca en este entorno** (probado también
apuntando `BROWSER_PATH` al Chrome instalado, que sí existe en
`C:\Program Files\Google\Chrome\Application\chrome.exe`). El HTML y los CSV sí se
generan. Recetas, de menos a más esfuerzo:

1. Seguir sin el PNG: el HTML ya sirve para ver el gráfico.
2. `set BROWSER_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe`
3. `kaleido_get_chrome` (instala el navegador propio de kaleido; requiere red).

> Ojo con los pares: el consolidado versionado tiene 3 convocatorias, así que
> `sprint6_sankey_categoria.py` produce **2017→2019** y **2019→2021**. Los 5 HTML
> versionados del proyecto auditado salen del dataset completo de 6 convocatorias.

### `poetry.lock`: regenerado y verificado

| | |
|---|---|
| Estado | **regenerado** con `poetry lock` |
| Tamaño | **407 370 bytes**, **164 paquetes** (el del commit original: 327 093 B) |
| Dependencias añadidas | `kaleido 1.5.0`, `openpyxl 3.1.5`, `pyyaml 6.0.3`, `nbformat 5.10.4`, `ipython 8.38.0` — **las 5 están** |
| Integridad | sobrevive a la reconstrucción de `repo_mejorado/` (`construir_repo_mejorado.py` lo preserva) |

⚠️ **El lock y el entorno no coinciden en dos paquetes**: el lock fija
`plotly 5.24.1` y `pandas 2.3.3` (respeta los rangos de `pyproject.toml`), mientras
el entorno de prueba tiene **plotly 7.1.0** y **pandas 3.0.6** (instalados con
`pip`, sin restricción de versión). La prueba de arriba es, por tanto, con las
versiones **modernas**, no con las fijadas. Para probar exactamente lo que fija el
lock: `poetry install`. Si se quisiera fijar también lo moderno, hay que subir los
rangos en `pyproject.toml` (`plotly = "^7"`, `pandas = "^3"`) y regenerar el lock;
no lo he hecho porque `pandas 3` tiene cambios de comportamiento que conviene
decidir aparte.

---

## Verificación (resumen)

`python datos_originales/verificar_arreglos.py` → **0 fallos**. Comprueba:

1. **Limpieza**: `repo_mejorado` = `repo_auditado` − 6 `.gitkeep` − 13 legacy
   apartados + 17 arreglos declarados + 6 archivos nuevos, **sin un solo archivo
   alterado que no esté declarado**, sin residuos, y con **todos** los archivos
   nuevos declarados presentes.
2. **`repo_auditado` intacto**: 236/236 hashes idénticos al commit, 0 sobrantes.
3. **Sintaxis**: 37 `.py` válidos (los 4 de `legacy_referencia/` se excluyen: son
   sintaxis de Colab) y 26 celdas del cuaderno válidas.
4. **Defectos ausentes, vía AST** (no búsqueda de texto): ninguna llamada a
   `.fetchdf()` ni a `.write_image()` desnuda. Y arreglos **presentes** (para que
   el chequeo no pueda pasar por vacío).
5. **Pruebas reales**: guardia del motor de imagen (4 casos), `comparar_dane()`
   contra la evidencia versionada, `aviso_produccion_ausente()`.
6. **Ejecución de los 6 scripts**, en una copia desechable, usando las librerías
   REALES cuando están instaladas y dobles solo para lo que falte.

`python datos_originales/probar_librerias_reales.py` → **0 errores reales**.

### Límites declarados

- **PNG no regenerados** (3): kaleido necesita un navegador que no arranca en este
  entorno. El HTML y los CSV sí se generan.
- **El cuaderno `docs/manual.ipynb` no se ejecuta**: se valida su sintaxis y su
  coherencia con el generador, no su corrida (necesita el dataset de producción en
  tres de sus secciones).
- **Los 3 scripts de producción** no pueden producir salidas sin el dataset de
  ~1,2 GB, que no está versionado en ninguna parte.

---

## Incidencias de la reconstrucción (OneDrive en Windows)

Anotadas porque afectan a quien reconstruya la carpeta:

1. **`shutil.rmtree` falla con `[WinError 5]`** sobre los directorios que OneDrive
   deja como *reparse points* (`ReadOnly`), p. ej. `.github/workflows/`. Se
   resuelve quitando el atributo antes de borrar.
2. **Borrar la carpeta `repo_mejorado/` entera puede fallar** aunque se hayan
   borrado sus contenidos (algo la mantiene abierta). Por eso
   `construir_repo_mejorado.py` ahora la **vacía** en lugar de borrarla: no hace
   falta eliminarla, solo que acabe con el contenido correcto.
3. **Un borrado interrumpido a medias deja la carpeta INCOMPLETA.** Pasó: se
   perdieron `.github/workflows/etl_update.yml`, `poetry.lock` y este CHANGELOG.
   Ahora el script reintenta y, si no puede, **falla con un mensaje claro** en vez
   de dejar el entregable a medias en silencio; y `verificar_arreglos.py` detecta
   cualquier archivo nuevo declarado que falte.
