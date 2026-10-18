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
| Arreglos aplicados | **34** (sobre 18 archivos) + 6 celdas de `docs/manual.ipynb` |
| Módulo nuevo | `src/exportacion.py` |
| Modernización L | motor de imagen **kaleido → `plotly-mirage`**, sin navegador |
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

## K · `informe_final.md`: el modelo estrella tiene nueve **tablas**, no nueve dimensiones

**Qué.** Cuatro correcciones en `informe_final.md`, los parches `K1`–`K4`.

**El defecto.** Las cuatro descripciones del modelo en el informe dicen que se
construyó «con **nueve dimensiones** y una tabla de hechos» (el objetivo específico
4, la descripción del diseño, la §5.3 y las conclusiones). El esquema real tiene
**9 tablas**:

| | |
|---|---|
| **7 dimensiones** | `dim_area`, `dim_categoria`, `dim_convocatoria`, `dim_formacion`, `dim_institucion`, `dim_investigador`, `dim_territorio` |
| **1 tabla de hechos** | `fact_clasificacion` |
| **1 tabla puente** | `bridge_hecho_institucion` (N:N con las instituciones, porque `INST_FILIA` admite dos separadas por ` \| `) |

**De dónde salía el «nueve».** El docstring de `sprint2_duckdb.py` lista exactamente
esas 9 tablas, así que el «nueve» **cuenta tablas, no dimensiones**. Y la
enumeración de la sección de diseño explica el resto: enumeraba nueve **atributos**
(investigador, convocatoria, universidad, área, nacimiento, género, residencia,
formación, clasificación) que la implementación **consolidó en siete dimensiones**
—nacimiento y género dentro de `dim_investigador`, universidad en
`dim_institucion`, residencia en `dim_territorio`—.

**Por qué se corrige el enunciado y no el código.** El diseño es correcto y la
integridad referencial se cumple (0 huérfanos en las 7 dimensiones y en el puente,
verificado en `documentacion_auditoria/data/memoria/modelo_estrella.json`). Lo que
engañaba era la descripción: prometía nueve dimensiones. Por eso `K2` **conserva** la
enumeración original de nueve atributos —es la trazabilidad del diseño— y añade la
correspondencia con las siete dimensiones que existen.

**Cómo se verificó.** `verificar_arreglos.py` ahora falla si `informe_final.md`
sigue diciendo «nueve dimensiones» y comprueba positivamente que aparezcan «siete
dimensiones», «tabla puente» y «(nueve tablas en total)». Las cuatro anclas se
comprobaron únicas antes de aplicar los parches.

**Hallazgo asociado (F2-3).** Con las 6 convocatorias el modelo se reconstruye
completo: `dim_convocatoria` pasa de 3 a **6**, `fact_clasificacion` de 50 891 a
**77 237** hechos y `dim_investigador` de 26 662 a **30 086** personas, y reproduce
la evidencia versionada cifra a cifra (`duckdb_resumen_modelo.txt`). Detalle en
`documentacion_auditoria/analisis_modelo_estrella.md`.

---

## L · Motor de imagen: de `kaleido` a `plotly-mirage` (sin navegador)

**Qué.** `src/exportacion.py` ya no usa `kaleido`: exporta el PNG con
**`plotly-mirage`** (se importa como `mirage`), que rasteriza el SVG de Plotly
dentro del propio proceso con `quickjs` + `resvg`. En `pyproject.toml` y en
`requirements.txt` sale `kaleido` y entra `plotly-mirage`; `poetry.lock` se
regeneró. El módulo expone además `activar_mirage()`, que parchea
`fig.write_image()` / `plotly.io.write_image()` para que los atienda mirage, de
modo que un script que llame a `write_image()` directamente tampoco necesita
Chrome.

**Por qué.** Kaleido 1.x no dibuja: maneja un Chromium real por medio de
`choreographer`. Por eso la exportación dependía de que arrancara un navegador y
fallaba con `BrowserFailedError` («The browser seemed to close immediately after
starting») en cuanto el entorno no permitía procesos hijos o tuberías nombradas:
contenedores sin Chrome, equipos con el navegador bloqueado por política, sesiones
de CI. Con mirage no hay navegador que arrancar: solo hacen falta Python y dos
ruedas (`quickjs`, `resvg-py`).

**Qué se midió aquí, con las librerías reales (no con dobles).**

| Motor | Llamada | Resultado en este entorno |
|---|---|---|
| kaleido 1.5.0 | `fig.write_image()` | ❌ `choreographer.browsers._errors.BrowserFailedError` |
| mirage 0.2.0 + plotly 7.1.0 | `mirage.write_image()` | ✅ PNG válido (cabecera `\x89PNG\r\n\x1a\n`) de un `sankey` |

El `sankey` es justamente el gráfico que exportan `scripts/sprint6_sankey_*.py`.

**Dos defectos que solo aparecen con la librería de verdad.** Los dobles de
prueba no los habrían enseñado:

1. **`mirage.write_image()` no acepta `pathlib.Path`.** Con un `Path` revienta
   dentro de su `raster.py` con `AttributeError: 'WindowsPath' object has no
   attribute 'write'`; funciona con `str` o con un archivo abierto. Como los dos
   scripts pasan `ARTIFACTS / "sankey.png"` (un `Path`), `exportar_png()`
   normaliza la ruta a `str` antes de llamar al motor. Ese `AttributeError` no
   lleva la firma del motor, así que sin la normalización se habría propagado y
   habría tumbado el script: exactamente el fallo que el guardia debía evitar.
2. **El render aborta en `scatter` con ejes continuos.** Falla con
   `JSException: Plotly render failed: out-of-bound numeric index`, de forma
   intermitente y no ligada al tamaño: con 3 puntos aleatorios dibujó y con 5
   falló; con ejes enteros no falló hasta 2.000 puntos. Tampoco soporta trazas
   WebGL (`scattergl`). Sí dibuja `sankey`, `bar` con eje categórico, `heatmap`,
   `pie`, `treemap` y `choropleth`.

**Límite declarado, y por qué no invalida el arreglo.** El PNG sigue siendo
*best-effort*: si el motor no está o no sabe dibujar esa figura, `exportar_png()`
lo explica en la consola y devuelve `False`; el HTML y los CSV se generan igual.
Los **dos únicos PNG de este repositorio son sankey**, así que se producen. El
resto de gráficos se entrega como HTML, que es como se ha entregado siempre.

**Cómo se verificó.** `verificar_arreglos.py`, NIVEL 1c: prueba el guardia con
objetos que lanzan los errores reales y con una **figura Plotly de verdad**, que
debe producir un PNG con cabecera válida; y comprueba que `pyproject.toml` declare
`plotly-mirage` y que ya **no** declare la clave `kaleido`.

**`poetry.lock` regenerado, sin deriva.** `poetry lock` (Poetry 2.5.1) conservó
todas las versiones fijadas salvo los cuatro paquetes del navegador:

| Salieron | Entraron |
|---|---|
| `kaleido 1.5.0`, `choreographer 1.4.0`, `logistro 2.0.1`, `simplejson` | `plotly-mirage 0.2.0`, `quickjs 1.19.4`, `resvg-py 0.5.0` |

`plotly` sigue en 5.24.1 y `pillow` en 12.1.1. Total: **157 paquetes y 398 461
bytes** (antes 158 y 407 370). Validado con `poetry check --lock`.

**Nota sobre la numeración.** Este archivo numera sus arreglos con letras (A–K) y
declara **34** parches de `aplicar_arreglos.py`. Esta sección **no** es uno de
esos parches: es una modernización manual posterior, con su propio alcance. La
tabla de arriba sigue diciendo 34 porque describe lo que aplica el script.

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

| | Lock del proyecto auditado | Lock de `repo_mejorado/` |
|---|---|---|
| Tamaño | 327 093 B | **407 370 B** (+80 277 B, **+24,5 %**) |
| Bloques `[[package]]` | 135 | **164** (+29) |
| Paquetes distintos | 130 | **158** (+28) |
| `poetry check --lock` | **falla** (`pyproject.toml changed significantly…`) | **pasa** (exit 0) |
| Dependencias declaradas que le faltan | **7** | 0 |

**No es que el lock nuevo tenga «versiones más modernas»: es que el viejo estaba
incompleto.** De los **129 paquetes comunes**, 128 quedan en la **misma versión** y
solo uno cambia (ver abajo). Lo que hace el lock nuevo es **completar** lo que el
código ya importaba y el lock viejo no contenía:

| Declarada en `pyproject.toml` | ¿En el lock auditado? | ¿En el nuevo? |
|---|---|---|
| `sodapy` (lo importan `src/ingesta/minciencias.py` y `produccion.py`) | **no** | sí, 2.2.0 |
| `duckdb` (`src/modelo/dimensional.py`, `scripts/sprint5_duckdb.py`) | **no** | sí, 1.5.6 |
| `networkx` (`src/analisis/redes.py`) | **no** | sí, 3.6.1 |
| `pyvis` (`src/analisis/redes.py`, `scripts/sprint3_grafo_interactivo.py`) | **no** | sí, 0.3.2 |
| `pytest` (grupo dev) | **no** | sí, 8.4.2 |
| `ruff` (grupo dev) | **no** | sí, 0.3.7 |
| `pandera` (grupo dev) | **no** | sí, 0.18.3 |

Es decir: `poetry install` sobre el proyecto auditado instalaba un proyecto
**incapaz de correr**, porque faltaban cuatro dependencias de ejecución. Ese es el
arreglo real, y es la razón por la que el lock pesa más.

| | |
|---|---|
| Dependencias añadidas por el código mejorado | `kaleido 1.5.0`, `openpyxl 3.1.5`, `pyyaml 6.0.3`, `nbformat 5.10.4`, `ipython 8.38.0` — **las 5 están** |
| Integridad | sobrevive a la reconstrucción de `repo_mejorado/` (`construir_repo_mejorado.py` lo preserva) |

⚠️ **`ipython` es el único paquete que BAJA de versión**: el lock auditado traía
tres bloques (8.38.0 para py3.10, **9.10.0 para py3.11**, 9.11.0 para py3.12) y el
nuevo trae uno solo (**8.38.0**), porque `pyproject.toml` declara `ipython = "^8.0"`.
El código (`IPython.display.IFrame` en las celdas del manual) funciona igual en 8 y
en 9, así que el rango es **más estrecho de lo necesario**. Lo dejo anotado como
mejora pendiente y no lo cambio ahora:

```toml
# más correcto, pero exige volver a generar el lock:
ipython = ">=8,<10"
```

### Validación del lock con Poetry

Tres comprobaciones, de menos a más exigente:

| Comprobación | Resultado |
|---|---|
| `poetry check --lock` | **exit 0** — el lock es sintácticamente válido **y** coherente con `pyproject.toml` |
| `poetry install --dry-run --no-root` | **exit 0** — resuelve el plan completo sin red: **153 instalaciones** |
| `poetry install --no-root` (entorno limpio real) | **incompleto**: 152/153 paquetes, bloqueado por la red |

Detalles que importan:

- El **`--dry-run` se resuelve entero a partir del lock**, sin tocar la red: eso
  demuestra que el lock es autocontenido. El plan incluye exactamente lo que debía:
  `pandas 2.3.3`, `plotly 5.24.1`, `numpy 1.26.4`, `pyvis 0.3.2`, `sodapy 2.2.0`,
  `pandera 0.18.3`, `pytest 8.4.2` y las 5 añadidas.
- Los 153 instalados frente a los 158 nombres del lock es **correcto**: los 5 de
  diferencia son bloques del mismo paquete para otras versiones de Python
  (`contourpy`, `networkx`, `scikit-learn`, `scipy`), que Poetry descarta por marca.
- **`poetry install` sí funciona**, pero la red de este entorno es **intermitente**:
  entre intentos va descargando y cacheando, y en 20 reintentos llegó de 153 a **1**
  paquete pendiente (`cycler 0.12.1`), que se completó extrayendo la rueda de la
  caché de pip. La causa del fallo es siempre la misma y no tiene que ver con el
  proyecto:

  ```
  All attempts to connect to pypi.org failed.
  ```

  Con red estable, `poetry install` termina de una pasada.
- **Nota de entorno (no del proyecto)**: Poetry quiere escribir su caché y sus
  entornos en `%APPDATA%` / `%LOCALAPPDATA%`, fuera del espacio de trabajo, y ahí la
  política de archivos lo deniega (`[WinError 5]`). Se resuelve con
  `POETRY_CACHE_DIR`, `POETRY_VIRTUALENVS_IN_PROJECT` y
  `VIRTUALENV_OVERRIDE_APP_DATA` apuntando dentro del proyecto.

### Prueba con las versiones FIJADAS por el lock

El entorno limpio anterior permite algo que antes no se podía: ejecutar los 51
artefactos con **exactamente** lo que el lock fija (pandas 2.3.3, numpy 1.26.4,
plotly 5.24.1, ipython 8.38.0), no con lo que hubiera instalado en el sistema.

### Los 51 artefactos del inventario, probados dos veces

`datos_originales/probar_inventario_completo.py` recorre **uno por uno los 51
artefactos** que el proyecto declara en
`documentacion_auditoria/data/inventario_codigo.csv`, y lo hace **dos veces**: con
las versiones **fijadas por el lock** (dentro del entorno que creó `poetry install`)
y con las **modernas** del sistema.

Cómo se prueba cada tipo de artefacto:

| Tipo | Cuántos | Prueba aplicada |
|---|---:|---|
| `scripts/*.py` | 17 | se **ejecutan** |
| `src/**/*.py` | 15 | se **importan**, con la misma raíz de importación que usa el proyecto (`src/` en el `PYTHONPATH`) |
| `streamlit_app.py`, `app/streamlit_app.py` | 2 | se arrancan en modo *headless* y se comprueba que sirvan |
| Notebooks activos | 2 | `nbformat` + compilación de cada celda de código |
| `tests/*` | 2 | `pytest` |
| `*.R` y resto de legados | 13 | sintaxis (`Rscript parse()` / `compile()`); viven en `legacy_referencia/` |

Los dos informes completos quedan en `datos_originales/reporte_ejecucion_51_poetry.csv`
y `datos_originales/reporte_ejecucion_51_moderno.csv`.

#### Resultado

| | Con el lock | Con versiones modernas |
|---|---:|---:|
| Artefactos **activos** probados | 38 | 38 |
| Corren o se importan sin problema | **35** | 32 |
| Corren, pero les faltan datos (F1) | 3 | 3 |
| **Fallan** | **0** | **3** |
| **Fallos por *breaking change* (F3)** | **0** | **0** |

Los 3 fallos de la columna moderna son **todos F2** (falta `pyvis` y `sodapy` en el
intérprete del sistema): con las versiones del lock **desaparecen**, porque el lock
sí las trae. Los 3 artefactos que salen con código 3 son los mismos en ambas
corridas, y es el comportamiento declarado: no existe
`datos/raw/produccion_grupos.csv` (~1,2 GB, no versionado).

#### Los 51, uno por uno

| # | Artefacto del inventario | Líneas | Con el lock | Con versiones modernas |
|---:|---|---:|---|---|
| 1 | `app/streamlit_app.py` | 17 | CORRE | CORRE |
| 2 | `docs/manual.ipynb` | 805 | IMPORTA | IMPORTA |
| 3 | `notebooks/01_eda.ipynb` | 240 | IMPORTA | IMPORTA |
| 4 | `notebooks/tarea_anlisis_bases_de_datos/2019_codigo.py` | 174 | LEGACY | LEGACY |
| 5 | `notebooks/tarea_anlisis_bases_de_datos/datos_2021.ipynb` | 2338 | LEGACY | LEGACY |
| 6 | `notebooks/tarea_anlisis_bases_de_datos/inv_17_codigo_graficas.R` | 614 | LEGACY | LEGACY |
| 7 | `notebooks/tarea_dimensiones_y_hechos/codigo_dimensiones_C.R` | 40 | LEGACY | LEGACY |
| 8 | `notebooks/tarea_dimensiones_y_hechos/dimensiones.ipynb` | 289 | LEGACY | LEGACY |
| 9 | `notebooks/tarea_dimensiones_y_hechos/tabla_hechos_codigo.R` | 20 | LEGACY | LEGACY |
| 10 | `notebooks/tarea_gran_tabla/analisis_de_clusters.R` | 94 | LEGACY | LEGACY |
| 11 | `notebooks/tarea_gran_tabla/analisis_multivariado_base_gran_table.R` | 405 | LEGACY | LEGACY |
| 12 | `notebooks/tarea_gran_tabla/analisis2.ipynb` | 294 | LEGACY | LEGACY |
| 13 | `notebooks/tarea_gran_tabla/codigo_analisis_univariado.py` | 123 | LEGACY | LEGACY |
| 14 | `notebooks/tarea_gran_tabla/codigo_creacion_gran_tabla_a_partir_del_modelo_estrella.py` | 205 | LEGACY | LEGACY |
| 15 | `notebooks/tarea_join/codigo_join.py` | 26 | LEGACY | LEGACY |
| 16 | `notebooks/tarea_tabla/arreglar_base_consultoria_7.R` | 125 | LEGACY | LEGACY |
| 17 | `scripts/generar_manual.py` | 610 | CORRE | CORRE |
| 18 | `scripts/sprint2_duckdb.py` | 127 | CORRE | CORRE |
| 19 | `scripts/sprint2_genero_ocde.py` | 182 | CORRE | CORRE |
| 20 | `scripts/sprint2_matrices_transicion.py` | 125 | CORRE | CORRE |
| 21 | `scripts/sprint2_panel_longitudinal.py` | 229 | CORRE | CORRE |
| 22 | `scripts/sprint2_territorial.py` | 142 | CORRE | CORRE |
| 23 | `scripts/sprint3_grafo_interactivo.py` | 72 | CORRE | **FALLA (F2)** |
| 24 | `scripts/sprint3_redes.py` | 134 | CORRE | CORRE |
| 25 | `scripts/sprint4_diversidad.py` | 172 | CORRE | CORRE |
| 26 | `scripts/sprint5_duckdb.py` | 193 | CORRE (3) | CORRE (3) |
| 27 | `scripts/sprint5_produccion.py` | 251 | CORRE (3) | CORRE (3) |
| 28 | `scripts/sprint6_geografia_institucional.py` | 302 | CORRE | CORRE |
| 29 | `scripts/sprint6_ocde_composicion.py` | 183 | CORRE (3) | CORRE (3) |
| 30 | `scripts/sprint6_sankey_categoria.py` | 184 | CORRE | CORRE |
| 31 | `scripts/sprint6_sankey_territorial.py` | 135 | CORRE | CORRE |
| 32 | `scripts/sprint6_tabla_maestra_ies.py` | 635 | CORRE | CORRE |
| 33 | `scripts/sprint6_validacion_calidad.py` | 121 | CORRE | CORRE |
| 34 | `src/__init__.py` | 2 | IMPORTA | IMPORTA |
| 35 | `src/analisis/__init__.py` | 80 | IMPORTA | IMPORTA |
| 36 | `src/analisis/calidad.py` | 105 | IMPORTA | IMPORTA |
| 37 | `src/analisis/diversidad.py` | 162 | IMPORTA | IMPORTA |
| 38 | `src/analisis/genero.py` | 85 | IMPORTA | IMPORTA |
| 39 | `src/analisis/longitudinal.py` | 207 | IMPORTA | IMPORTA |
| 40 | `src/analisis/produccion.py` | 340 | IMPORTA | IMPORTA |
| 41 | `src/analisis/redes.py` | 225 | IMPORTA | IMPORTA |
| 42 | `src/analisis/territorial.py` | 107 | IMPORTA | IMPORTA |
| 43 | `src/ingesta/__init__.py` | 53 | IMPORTA | IMPORTA |
| 44 | `src/ingesta/minciencias.py` | 70 | IMPORTA | **FALLA (F2)** |
| 45 | `src/ingesta/produccion.py` | 106 | IMPORTA | **FALLA (F2)** |
| 46 | `src/modelo/__init__.py` | 2 | IMPORTA | IMPORTA |
| 47 | `src/modelo/dimensional.py` | 286 | IMPORTA | IMPORTA |
| 48 | `src/Transformacion.py` | 222 | IMPORTA | IMPORTA |
| 49 | `streamlit_app.py` | 983 | CORRE | CORRE |
| 50 | `tests/__init__.py` | 0 | N/A | N/A |
| 51 | `tests/test_ingesta.py` | 8 | TEST PASA | TEST PASA |

Leyenda: **CORRE** = termina con código 0 · **CORRE (3)** = termina con código 3
(faltan datos; comportamiento declarado, no defecto) · **IMPORTA** = el módulo se
importa sin error (es una librería, no un ejecutable) · **TEST PASA** ·
**N/A** = el archivo no contiene pruebas · **LEGACY** = está en
`legacy_referencia/`, fuera del entregable por decisión del proyecto.

#### Clasificación de fallos (F1–F5)

| Categoría | Qué significa | Con el lock | Moderno |
|---|---|---:|---:|
| **F1** | datos de entrada ausentes (no versionados) | 3 | 3 |
| **F2** | dependencia declarada en `pyproject.toml`, no instalada en ese entorno | 0 | 3 |
| **F3** | cambio de comportamiento de librería (*breaking change*) | **0** | **0** |
| **F4** | limitación del entorno (navegador de kaleido, red, tiempo) | 0 | 0 |
| **F5** | artefacto legado no migrado por decisión del proyecto | 13 | 13 |

**No hubo ni un solo *breaking change*.** Es el resultado central de esta fase: el
código escrito para `pandas 2.2` / `plotly 5.18` funciona igual con `pandas 3.0.6` y
`plotly 7.1.0`, **sin tocar una línea**. En particular:

- **No apareció el problema de *Copy-on-Write*** de `pandas 3`: ningún artefacto
  depende de asignación encadenada ni de vistas mutables. Por eso no hubo que
  arreglar lógica «para que pasara»: no había nada que arreglar.
- `sprint2_duckdb.py`, `sprint6_sankey_categoria.py`, `sprint6_sankey_territorial.py`,
  `sprint6_tabla_maestra_ies.py` y `sprint6_validacion_calidad.py` corren
  **completos** con `pandas 3` y `numpy 2`.
- El dashboard `streamlit_app.py` (983 líneas) **arranca y sirve** con
  `streamlit 1.66` y `pandas 3`.
- La guardia del motor de imagen (arreglo A) se comporta como debe:
  `sprint6_sankey_territorial.py` termina con **código 0** avisando de que el PNG no
  se generó, en vez de morir con una traza.

Dos hallazgos menores en los legados, que **no se tocan** y quedan documentados
(están fuera del entregable por decisión del proyecto):

- `notebooks/tarea_gran_tabla/analisis2.ipynb` **no es un notebook**: es un archivo
  de Python con extensión `.ipynb` (no es JSON). `nbformat` no puede leerlo.
- `codigo_creacion_gran_tabla_a_partir_del_modelo_estrella.py` tiene un error de
  sintaxis en la línea 157.

Los 6 archivos `.R` **sí compilan** con `R 4.5.2` (`Rscript -e "parse(...)"`): su
sintaxis es correcta; lo que impedía migrarlos son sus rutas de Colab/Windows y sus
datos, no el lenguaje.

---

## Decisión sobre las versiones: **no se actualizan los rangos**

Se pidió verificar si el lock nuevo «pesa más, tiene más paquetes y versiones más
modernas». Las dos primeras son ciertas; **la tercera no**, y conviene decirlo sin
rodeos:

| Afirmación | Verificación |
|---|---|
| Pesa más | **cierto**: 407 370 B frente a 327 093 B (**+24,5 %**) |
| Tiene más paquetes | **cierto**: 158 paquetes distintos frente a 130 (**+28**) |
| Tiene versiones más modernas | **falso**: de los 129 paquetes comunes, **128 quedan igual**, **0 suben** y **1 baja** (`ipython`) |

El valor del lock nuevo no es la novedad de las versiones, sino que **está completo
y es coherente** (`poetry check --lock` pasa, y antes no). Por eso **no toco
`pyproject.toml` ni regenero el lock**: lo que había que arreglar —las 7
dependencias declaradas que faltaban— ya está arreglado, y un cambio de rangos
ahora mismo solo añadiría riesgo.

Razones, en orden de peso:

1. **Nada está roto con los rangos actuales.** Los 38 artefactos activos corren con
   las versiones que fija el lock **sin un solo fallo**. Subir rangos no arregla
   nada que esté fallando.
2. **El lock nuevo pasa `poetry check --lock` y el viejo no.** Tocar `pyproject.toml`
   invalida esa coherencia: habría que volver a generar el lock, y **la red de este
   entorno es intermitente** (20 reintentos para bajar 152 de 153 paquetes). Un
   `poetry lock` a medias sobre un archivo que hoy es válido es un mal negocio.
3. **Subir a `pandas = "^3"` cambia lo que el proyecto promete instalar** a
   cualquiera que lo clone. Es una decisión de contrato, no un arreglo, y merece
   decidirse con el lock ya generado y probado, no antes.
4. **Un hueco menor, sí detectado**: `ipython = "^8.0"` es más estrecho de lo
   necesario y es lo único que hace *bajar* una versión respecto al lock auditado.

### Si el grupo decide modernizar: es seguro y así se hace

La evidencia dice que **modernizar es seguro**, porque los artefactos activos se
probaron también con las versiones de última generación y **no hay un solo fallo
por cambio de comportamiento** (`pandas 3.0.6`, `numpy 2.4.6`, `plotly 7.1.0`,
`matplotlib 3.11.2`, `seaborn 0.13.2`, `streamlit 1.66.0`, `scikit-learn 1.9.1`).
Es decir: la decisión de **no** cambiar es conservadora, no forzada por defectos.

Procedimiento, cuando haya red estable:

```bash
cp poetry.lock poetry.lock.respaldo        # por si el lock nuevo sale peor
# en pyproject.toml:
#   pandas   = "^2.2"  ->  ">=2.2,<4"      # admite 2.x y 3.x
#   plotly   = "^5.18" ->  ">=5.18,<8"     # admite 5.x, 6.x y 7.x
#   ipython  = "^8.0"  ->  ">=8,<10"       # admite 8.x y 9.x
poetry lock
poetry check --lock                        # debe dar exit 0
poetry install
python datos_originales/probar_inventario_completo.py --etiqueta moderno
```

Si `poetry check --lock` falla o algún artefacto empieza a fallar por cambio de
librería, se restaura el respaldo: `mv poetry.lock.respaldo poetry.lock`.

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
- **Los cuadernos NO se ejecutan, solo se validan**: se leen con `nbformat` y se
  compila **cada** celda de código, pero no se corren. Hace falta un kernel
  (`nbclient` + `ipykernel` + `pyzmq`): `nbclient` sí está en la caché de pip, pero
  `jupyter_client` y `pyzmq` no, y sin red no se pueden instalar. En el entorno de
  `poetry install` sí están, así que ejecutarlos es una prueba pendiente y barata
  para quien tenga red.
  - `docs/manual.ipynb` además necesita el dataset de producción en tres secciones.
- **Los 3 scripts de producción** no pueden producir salidas sin el dataset de
  ~1,2 GB, que no está versionado en ninguna parte. Salen con código 3.
- **La red de este entorno es intermitente**: `poetry install` llegó a 152/153
  paquetes en 20 reintentos, y el último se completó desde la caché de pip. Con red
  estable, `poetry install` termina de una sola pasada.

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
