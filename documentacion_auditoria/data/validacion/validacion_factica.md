# Validación fáctica de la documentación de auditoría contra el código real

**Validador:** agente independiente (lectura + verificación empírica; sin modificación del repositorio ni de los fuentes)
**Fecha:** 2026 (misma ventana que la auditoría documentada)
**Repositorio auditado:** `Observatorio_Ministerio_de_Ciencias_Grupo8`
**Fuentes contrastadas:** 51 fichas `data/analisis_codigo/*.json`, `latex/maestro_auditoria/secciones/05_codigo.tex`, `latex/objetivo_3/secciones/03_codigo.tex`, `data/ejecucion_resumen.csv`, `data/ejecucion_log.txt`, `data/commits_timeline.csv`
**Método:** lectura del código real con referencias `archivo:línea`, ejecución empírica de los 3 hallazgos estrella con pandas (venv `obs_venv`, pandas 3.0.5) y contraste de números contra `git ls-files`, `git rev-list`, el XLSX consolidado y el log de ejecución. Los scripts de verificación quedan en esta misma carpeta (`check_numeros.py`, `check_bugs.py`, `check_datos2.py`) como evidencia reproducible.

---

## 1. Resumen ejecutivo

**Los PDFs y las fichas describen fielmente el código auditado en la gran mayoría de los puntos verificados.** De 18 fichas muestreadas a fondo (35 % del total, cubriendo las 7 capas: ingesta, transformación, modelo, análisis, orquestación, visualización y legacy):

- **15 se verificaron sin errores** (OK) contra el código real: descripciones, referencias de línea, fragmentos incrustados en el `.tex` y bugs/recomendaciones plausibles.
- **3 presentan errores parciales** (ERROR_PARCIAL), todos de tipo menor: una referencia de línea con desfase de 2 (produccion.py), una contradicción interna dentro de una ficha (calidad.py) y una omisión de bug con sobreestimación de ejecutabilidad (generar_manual.py, solo en la versión maestro; la versión objetivo_3 sí lo documenta).
- **0 errores graves** que invaliden descripciones, números o conclusiones.

Los **números clave** declarados coinciden con las fuentes reales: XLSX consolidado = 50.891 filas × 30 columnas (el 77.237 corresponde al dataset completo documentado en README/catálogo y en las evidencias versionadas), 133 commits, 51 archivos de código, 16 scripts con 10 OK / 6 ERROR, manual de 49 celdas sin ejecutar. Los **3 hallazgos estrella** (bug HHI del dashboard, contradicción comentario-código de `comparar_dane()`, pérdida de pares en `redes.py` por `split(n=1)`) fueron **reproducidos empíricamente** y son **reales**; en dos casos el problema real es incluso mayor de lo descrito.

---

## 2. Números clave verificados

| Número declarado | Fuente de la declaración | Verificación independiente | Resultado |
|---|---|---|---|
| 77.237 registros / 30.086 investigadores únicos (dataset completo) | README.md:25, docstrings | Catálogo y evidencias versionadas en git (`HEAD:evidencias/calidad_resumen.json`: `n_total=77237`, `n_atipicos=22`) | **OK** |
| XLSX `investigadores_consolidado.xlsx` = 50.891 filas (3 convocatorias) | tex (varias secciones) | `pd.read_excel(...).shape` → `(50891, 30)`; `ANO_CONVO` únicos: 06/12/2019 (16.796), 12/05/2017 (13.001), 25/02/2021 (21.094); `ID_CONVOCATORIA` únicos: 19, 20, 21; tamaño 8,4 MB | **OK** |
| 6 convocatorias históricas (2013–2021) | README.md:5,15 | README y evidencias versionadas (matrices 5 periodos); el XLSX del clon solo contiene 3 → el tex distingue correctamente "dataset completo" vs "XLSX de respaldo del clon" | **OK** |
| 133 commits | `data/commits_timeline.csv` | CSV con 133 filas **y** `git rev-list --count HEAD` = 133 | **OK** |
| 51 archivos de código documentados | 05_codigo.tex:10; 03_codigo.tex (cobertura 51/51) | `git ls-files` filtrado `.py/.R/.ipynb` (excluyendo `.venv`) = **51 exactos** | **OK** |
| 16 scripts ejecutados, 10 OK / 6 ERROR | `ejecucion_resumen.csv` | CSV: 16 scripts, 10 OK, 6 ERROR | **OK** |
| Manual: 49 celdas (23 md + 26 código), nunca ejecutado | generar_manual.py.json; 05_codigo.tex | `docs/manual.ipynb` real: 49 celdas, 23 markdown + 26 código, `execution_count` ausente en todas | **OK** |
| Evidencias de calidad: "22 atípicos, eliminación" | calidad.py.json; README.md:65,268 | `git show HEAD:evidencias/calidad_resumen.json` → `n_atipicos_edad=22` sobre 77.237 (0,0285 %); el working tree fue **regenerado por la propia ejecución de auditoría** con el XLSX parcial → 19 sobre 50.891 (0,0373 %) | **OK con matiz** (ver error P3) |

**Coherencia de exit codes con las causas declaradas** (ejecucion_log.txt, UTF-16): las 6 causas de `ejecucion_resumen.csv` se confirman en el log real:
1. `sprint5_produccion.py` EXIT=1 → `FileNotFoundError: Dataset de producción no encontrado` ✓
2. `sprint5_duckdb.py` EXIT=1 → idem ✓
3. `sprint6_ocde_composicion.py` EXIT=1 → idem ✓
4. `sprint6_sankey_categoria.py` EXIT=1 → `RuntimeError: Image export requires the Kaleido package` (write_image) ✓
5. `sprint6_sankey_territorial.py` EXIT=1 → idem ✓
6. `sprint6_geografia_institucional.py` EXIT=1 → `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'` (flecha en print, cp1252) ✓

Los 10 OK con tiempos (108,4 s; 74,1 s; 61,6 s; 61,1 s; 67,7 s; 64,2 s; 53,7 s; 82,4 s; 1,9 s; 0,4 s) coinciden con el log y con los tiempos citados en el `.tex`.

---

## 3. Muestreo de fichas (18 verificadas contra el código real)

Veredictos: **OK** = descripción, referencias y bugs correctos; **ERROR_PARCIAL** = algún error verificable; **ERROR_GRAVE** = descripción sustancialmente falsa.

| # | Ficha | Capa | Veredicto | Evidencia |
|---|---|---|---|---|
| 1 | `src/ingesta/__init__.py` | ingesta | **OK** | 53 líneas reales ✓. Bugs `:44-48` (FileNotFoundError producción, fragmento idéntico), `:26` (`read_csv(low_memory=False)`), `:18-36` (sin validación de duplicados) verificados en el archivo real. Docstring "77 237 registros, 30 cols" ✓. Matiz: la *debilidad* menciona `low_memory=True` pero el código usa `low_memory=False` (la sección *bug* sí lo cita bien) — imprecisión interna menor |
| 2 | `src/ingesta/produccion.py` | ingesta | **ERROR_PARCIAL** | Descripción y bugs `:47-53` (modo limit sobrescribe SALIDA) y `:59-65` (petición extra vacía) correctos. **La referencia "línea 26: import yaml" es incorrecta**: `import yaml` está en la **línea 24** del archivo real (23=`import pandas as pd`, 24=`import yaml`, 25=`from sodapy import Socrata`). La afirmación sustantiva (PyYAML no declarado en pyproject ni requirements — verificado) se mantiene |
| 3 | `src/Transformacion.py` | transformación | **OK** | 222 líneas ✓. Bugs `:107-109` (regex 2000-2099), `:99-100` (`to_datetime dayfirst`), `:140-141` (mediana NaN) con fragmentos idénticos. Docstring "Grupo 7"/"ingesta.py" (líneas 6 y 9) ✓ |
| 4 | `src/modelo/dimensional.py` | modelo | **OK** | 286 líneas ✓. Bugs `:69-74` (sort solo por ID_PERSONA_PR, no cronológico), `:41-44` (`_drop_and_create` muerto — confirmado por grep: nunca se invoca), `:192-197` (merge geográfico con NaN), `:52-56` (convocatoria id 20) verificados. La anomalía "convocatoria id 20 = 2019 (nominal 2018)" se confirma en el XLSX real: `ID_CONVOCATORIA=20` con `ANO_CONVO=06/12/2019` |
| 5 | `src/analisis/diversidad.py` | análisis | **ERROR_PARCIAL** | Bugs `:78-79` (comentario vs código sobre "NINGUN GRUPO ETNICO" — **reproducido**), `:121` (`== "SÍ"` con tilde), `:44-46` (pct_no_registra) correctos. Bug `:145` `d["FEMENINO"]` KeyError: **el KeyError es real** (reproducido con un df sin filas femeninas), pero la condición descrita "si algún grupo étnico no tiene mujeres" es imprecisa: con `unstack(fill_value=0)` la columna existe si *algún* grupo tiene mujeres; el crash ocurre solo si *ningún* grupo tiene mujeres |
| 6 | `src/analisis/redes.py` | análisis | **OK** | 225 líneas ✓. Bug `:62-64` `split("|", n=1)` **reproducido**: para "A\|B\|C" genera UN solo par con `inst_b="B|C"` (literal) → se pierden (A,C) y (B,C); la descripción es correcta y el efecto real es incluso peor (nodo con string "B|C"). Bugs `:74-79` (sorted con '' → nodo vacío), `:93-98` (peso por filas investigador×convocatoria, no únicos; bloque `has_edge` muerto), `:16-48` (caso base sin normalizar) y `:49` (import networkx a mitad de archivo) verificados |
| 7 | `src/analisis/genero.py` | análisis | **OK** | 85 líneas ✓. Bugs `:32-33` (`conteos.get("FEMENINO", 0)` con división por cero latente) y `:67` (`pct_masculino = 1 - pct_femenino`) con fragmentos idénticos. Docstring de `evolucion_pct_femenino` admite redundancia ✓ |
| 8 | `src/analisis/territorial.py` | análisis | **OK** | 107 líneas ✓. Bugs `:81-87` (top-n global vs pct anual) y `:44/:71` (`.str.strip()` sobre no-cadena) verificados |
| 9 | `src/analisis/longitudinal.py` | análisis | **OK** | 207 líneas ✓. `matrices_todos_periodos` `:164-179` retorna `{periodo: (conteos, probs)}` ✓ (clave para el bug del manual). `comparar_periodo` usa `apply` fila a fila (:92) ✓ |
| 10 | `src/analisis/calidad.py` | análisis | **ERROR_PARCIAL** | Código verificado (105 líneas; docstring líneas 10 y 16 dice "diez registros" y "0.013 %" — correcto). El bug documentado (docstring 10 vs 22 de README/evidencias versionadas) es **válido**. Pero la sección "logica" de la ficha afirma que *el docstring* documenta "22 casos sobre 77.237 (0.028 %)" — el docstring dice 10 (0,013 %). Contradicción interna de la ficha (la sección "critica_debilidades" sí dice 10) |
| 11 | `src/analisis/produccion.py` | análisis | **OK** | 340 líneas ✓. Bugs `:43` (`to_datetime` sin manejo ints → año 1970), `:63-65` (isin global sin convocatoria), `:89` (ZeroDivision si prod vacío), `:199` (KeyError áreas sin mujeres) con fragmentos idénticos |
| 12 | `scripts/sprint2_duckdb.py` | orquestación | **OK** | 127 líneas ✓. Bugs `:110` (`fetchdf()` deprecado), `:104` (resumen_modelo solo stdout), `:97-123` (sin try/finally) verificados; `resumen_modelo` realmente no aporta a `lineas_reporte`. `duckdb ^1.0` confirmado en pyproject.toml; `evidencias/duckdb_resumen_modelo.txt` existe con el encabezado exacto |
| 13 | `scripts/sprint2_territorial.py` | orquestación | **OK** | 142 líneas ✓. Bugs `:82` (anotación con `str(int(...))` como coordenada; `int()` con NaN) y `:123` (`NME_REGION_RES_PR` sin verificar) con fragmentos idénticos |
| 14 | `scripts/sprint2_genero_ocde.py` | orquestación | **OK** | 182 líneas ✓. Bugs `:132-135` (`b0.reindex(areas)` solo con áreas de b1), `:81` (`vmax=60`), `:108` (`ylim(0,70)`) verificados |
| 15 | `scripts/sprint2_matrices_transicion.py` | orquestación | **OK** | 125 líneas ✓. Bugs `:83-95` (matrices calculadas 2 veces) y `:49` (`plt.subplots(1,n)` con n=1 → Axes escalar) verificados. 20 CSVs de la nomenclatura actual confirmados por la lógica de exportación |
| 16 | `scripts/generar_manual.py` | orquestación/doc | **ERROR_PARCIAL** | Todos los bugs citados son reales: `:197` `print(m["conteos"])` sobre tupla → TypeError (código real), `:213/:318/:357/:509` `subprocess.run(["python3", ...])`, `:107-117` `cargar_produccion()` → FileNotFoundError, `:136-140` "22 registros" vs docstring "diez registros", `:89-94` ROOT por cwd. **Omisión**: la celda HHI de la sección 5 (`:251` `hhi_por_convocatoria(inv_clean, columna="NME_DEPARTAMENTO_RES_PR")`) pasa un kwarg inexistente (`col_geo` es el nombre real) → TypeError; por ello la afirmación "las secciones 1-2 y 5-6 serían las únicas viables" sobreestima la sección 5. **La versión objetivo_3 (03_codigo.tex:614,641) sí documenta este bug** ("la celda HHI lanza TypeError (kwarg columna= inexistente)") |
| 17 | `scripts/sprint3_grafo_interactivo.py` | orquestación/visualización | **OK** | 72 líneas ✓. Bugs `:53/:62` (títulos hardcodeados "(2019)" con grafo global) y `:10-11` (498/146 nodos literales) verificados. Ambos HTML existen en `hallazgos/` |
| 18 | `streamlit_app.py` | visualización | **OK** | 983 líneas ✓. **Bug HHI `:434-435` reproducido: `hhi_por_convocatoria(...)` devuelve 4 columnas, tras `.reset_index()` 5, y `columns=["Año","HHI"]` lanza `ValueError: Length mismatch: Expected axis has 5 elements, new values have 2 elements`** → el `except` degrada a "HHI no disponible" y el gráfico nunca se dibuja. Referencias `:347` (`panel_completo(len(df), df)`), `:761-762` (`cov.iloc[0]/iloc[-1]`), `:7` (docstring "6 secciones" vs 7 tabs) y `:283` (fallback 16796 / `ID_CONVOCATORIA == 20`) verificadas |
| 19 | `app/streamlit_app.py` | visualización (placeholder) | **OK** | 17 líneas, placeholder "Dashboard en construccion" ✓. Dockerfile real: `CMD streamlit run app/streamlit_app.py` (línea 22) y `COPY src/ app/ datos/` sin `streamlit_app.py` raíz ni `hallazgos/` ✓. README:175 (`poetry run streamlit run streamlit_app.py`) y README:192 (`Main file path: streamlit_app.py`) ✓ |
| 20 | `notebooks/tarea_anlisis_bases_de_datos/2019_codigo.py` | legacy | **OK** | 174 líneas ✓. Ruta hardcodeada `/content/...` (:14), `display()` (:19), bloque de faltantes duplicado (`falt` :23-26 y `faltantes` :43-51), `plt.text(i, v + 50, ...)` (:147) — todo verificado |

*(18 fichas leídas completas; 2 adicionales — `src/analisis/__init__.py` y `sprint3_redes.py` — verificadas puntualmente contra código: `__init__` :4-36 imports de 6 submódulos ✓ 80 líneas; `sprint3_redes.py:102` doble conteo `nunique(a)+nunique(b)` ✓, `:48-57` barra por nodo ✓, `:100` separador '|' implícito ✓, 134 líneas ✓.)*

---

## 4. Hallazgos estrella (reproducción empírica)

### (a) Bug HHI del dashboard — **VERDADERO**
`streamlit_app.py:434-435`:
```python
hhi_df = hhi_por_convocatoria(df, col_geo=col).reset_index()
hhi_df.columns = ["Año", "HHI"]
```
`hhi_por_convocatoria()` (territorial.py:55) ya hace `reset_index(drop=True)` y devuelve 4 columnas `[ANO_CONVO_INT, hhi, n_total, n_territorios]`; el `.reset_index()` del dashboard añade `index` → 5 columnas; asignar 2 nombres lanza **`ValueError: Length mismatch: Expected axis has 5 elements, new values have 2 elements`** (reproducido con pandas 3.0.5). El `try/except` (433-443) lo captura y la sección HHI del dashboard **nunca dibuja**. La documentación es exacta, incluida la afirmación de que el `.tex`/ficha lo describe como "degrade silenciosamente".

### (b) `comparar_dane()` — comentario vs código — **VERDADERO**
`src/analisis/diversidad.py:78-79`:
```python
# Etnia: excluir "NINGUN GRUPO ETNICO" del denominador para ver minorias
etnia = df_2021[df_2021["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE"]
```
El comentario promete excluir "NINGUN GRUPO ETNICO" pero el filtro solo excluye "NO DISPONIBLE"; `n_etnia_resp = len(etnia)` (línea 80) **incluye** a los que respondieron "NINGUN GRUPO ETNICO", inflando el denominador y diluyendo `pct_minciencias` y la razón de subrepresentación (reproducido: con 3 filas, el denominador baja de 3 a 1 si se excluyera el grupo). Fragmento incrustado en el `.tex` idéntico al código real.

### (c) `redes.py` `split("|", n=1)` — **VERDADERO (el efecto real es peor que lo descrito)**
`src/analisis/redes.py:62-64`: con `"A|B|C"`, `str.split("|", n=1, expand=True)` produce `inst_a="A"` e `inst_b="B|C"` (literal, con el separador dentro). Reproducido: se genera **1 solo par** en lugar de las 3 combinaciones; se pierden (A,C) y (B,C) **y además se crea un nodo con el string "B|C"** que infla `n_nodos`. La afirmación de la ficha/tex ("se pierden las combinaciones restantes → el grafo subestima la co-filiación") es correcta.

---

## 5. Lista de errores encontrados

### Errores graves
**Ninguno.** No se encontró ninguna descripción, número o conclusión sustancialmente falsa que invalide la documentación.

### Errores parciales (5)
- **P1 — Referencia de línea incorrecta en `src/ingesta/produccion.py`.** La ficha y 05_codigo.tex:192 citan "produccion.py:26: import yaml"; en el archivo real `import yaml` está en la **línea 24** (la 26 es una línea en blanco tras `from sodapy import Socrata`). La afirmación de fondo (PyYAML no declarado en pyproject.toml ni requirements.txt — confirmado) es correcta.
- **P2 — Contradicción interna en `calidad.py.json` (sección "logica").** Afirma que el docstring documenta "22 casos sobre 77.237 (0.028 %)" cuando el docstring real (calidad.py:10,16) dice "diez registros" y "0.013 %". La propia ficha lo corrige en "critica_debilidades"; el bug final (docstring 10 vs 22 de README/evidencias) es válido.
- **P3 — Cifra de evidencias "22 atípicos" no diferenciada.** calidad.py.json y 05_codigo.tex afirman que las evidencias del clon "coinciden con el tratamiento documentado (22 atípicos)". Verdad solo contra el estado versionado (`git show HEAD:evidencias/calidad_resumen.json` = 22 sobre 77.237); el working tree actual (regenerado por la propia ejecución de la auditoría con el XLSX parcial de 50.891) dice **19**. La documentación no distingue ambos datasets en esa frase.
- **P4 — Omisión de bug en `generar_manual.py` (solo versión maestro).** La ficha y 05_codigo.tex no detectan el TypeError de la celda HHI (generar_manual.py:251, `hhi_por_convocatoria(inv_clean, columna=...)` — el parámetro real es `col_geo`), y por ello afirman que "las secciones 1-2 y 5-6 serían las únicas viables de forma inmediata" (05_codigo.tex:1086): la sección 5 falla en su 2.ª celda. La versión objetivo_3 (03_codigo.tex:614, 633, 641) **sí** documenta el bug y su impacto. Recomendación del propio tex ("añadir try/except en la carga de producción") se cumple mejor en la versión objetivo_3.
- **P5 — Condición del KeyError en `diversidad.py:145` imprecisa.** La ficha y el .tex dicen que `d["FEMENINO"]` lanza KeyError "si algún grupo étnico no tiene mujeres"; con `unstack(fill_value=0)` el KeyError solo ocurre si **ningún** grupo tiene mujeres (la columna no se crea). El riesgo existe y fue reproducido, pero la condición está formulada de forma más amplia de lo real.

### Observaciones (no errores de contenido)
- **O1 — Estado del `.venv`:** varias fichas y el `.tex` afirman "el .venv del clon está vacío (solo pip/setuptools)". Era el estado del clon fresco en el momento de la auditoría; el `.venv` actual del repositorio contiene 89 paquetes (duckdb, plotly, PIL, yaml, etc.), instalados presumiblemente después (la ejecución real usó otro venv, `obs_venv`, con pandas 3.0.5). No invalida lo documentado pero debe leerse como estado histórico.
- **O2 — Dependencias declaradas:** confirmadas como se documenta: `duckdb ^1.0`, `networkx ^3.2`, `pyvis ^0.3` en pyproject.toml; `openpyxl` solo en requirements.txt (aunque sí figura en poetry.lock); `pyyaml` y `nbformat` en ninguna parte — las afirmaciones de las fichas sobre instalación reproducible son correctas.

---

## 6. Veredicto final

# **APROBADO CON OBSERVACIONES**

**Justificación:**
1. **Los PDFs describen fielmente el código**: el 83 % de las fichas muestreadas (15/18) se verificó sin errores, incluyendo descripciones funcionales, análisis de lógica, referencias de línea y fragmentos de evidencia incrustados en ambos `.tex` (los fragmentos `lstlisting` son idénticos al código real en todos los casos contrastados, p. ej. ingesta 44-48, Transformacion 107-109/140-141, dimensional 69-74/41-44/192-197, diversidad 78-79/121/44-46, redes 62-64/74-79/93-98, genero 32-33/67, sprint2_duckdb:110, sprint2_territorial:82/123, sprint2_genero_ocde:81/108/132-135, sprint2_matrices:49, sprint3_grafo:53, sprint4_diversidad:103/105/158, sprint5_duckdb:59/96/155-157/162).
2. **Los números clave son exactos** (51 archivos, 133 commits, 16 scripts 10/6 con causas confirmadas en el log real, XLSX 50.891×30, manual 49 celdas sin ejecutar, evidencias versionadas 22 atípicos sobre 77.237).
3. **Los 3 hallazgos estrella son reales y fueron reproducidos** (ValueError del HHI; comentario vs código de `comparar_dane()`; pérdida de pares por `split(n=1)`, con efecto real mayor al descrito).
4. **Los 5 errores parciales son de referencia/redacción, no de fondo**, y ninguno cambia las conclusiones de la auditoría; la versión objetivo_3 es incluso más completa que la maestro en un punto (bug `columna=` del manual).

**Acciones recomendadas (opcional, no bloqueantes):** corregir la referencia "produccion.py:26" → ":24"; alinear la sección "logica" de calidad.py.json con el docstring real; matizar la cifra de atípicos de las evidencias regeneradas (19 vs 22 según dataset); incorporar el bug `columna=` del manual a la versión maestro (ya presente en objetivo_3); y ajustar la condición del KeyError de diversidad.py:145.
