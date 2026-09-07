# Informe de validación independiente — Reglas de calidad de la documentación de auditoría

- **Fecha:** 2026 (sesión de validación sobre commit `1528939`, 2026-05-14)
- **Validador:** agente validador independiente y crítico (solo lectura de fuentes; no se modificó ningún artefacto de `documentacion_auditoria/`)
- **Alcance:** los 13 proyectos LaTeX (`maestro_auditoria/`, `objetivo_1..6/`, `objetivo_1..6_lite/`), las fuentes de verdad (`data/*.yaml`, `*.csv`, `data/analisis_codigo/*.json`) y el código generador (`src/generar_documento.py`, `src/generar_objetivo.py`)
- **Python:** `C:\Users\InfoPersonal\AppData\Local\Temp\dsh-PqwGBv\obs_venv\Scripts\python.exe`
- **Método:** verificación mecánica por script (replicando la lógica del generador) + compilación limpia con TinyTeX/latexmk en copias temporales (no se tocaron los proyectos originales) + muestreo manual.

---

## Tabla resumen

| # | Regla | Estado | Evidencia clave |
|---|-------|--------|-----------------|
| 1 | LITE ≠ completo y ≤40 % palabras + `_verificar_lite` | **CUMPLE** | 6/6 secciones difieren; ratios 37,6 % / 29,5 % / 13,2 % / 27,3 % / 28,8 % / 4,5 % (todas ≤40 %). `_verificar_lite()` existe en `src/generar_objetivo.py` (líneas 534-549) y se invoca antes de escribir (líneas 568-570) con `SystemExit` → la build falla. |
| 2 | Glosario filtrado por documento | **CUMPLE** | 12/12 documentos sin residuos (término incluido sin uso) ni faltantes (uso sin término). Filtro con `\b` verificado: `etl` no matchea `setlength` ni `etl_update.yml`; `sprint` no matchea `sprint5_duckdb.py`. |
| 3 | Orden canónico por capa | **INCUMPLE (parcial)** | Maestro OK (11 subsecciones en orden del YAML). `objetivo_3/secciones/03_codigo.tex` (y `objetivo_3_lite`) ordenan las fichas alfabéticamente por *nombre* de capa (analisis → documentacion → eda → ingesta → legacy → modelo → orquestacion → otro → testing → transformacion → visualizacion), NO según el YAML. Causa raíz en código: `_orden_por_capa()` ordena por el string de capa, no por su índice en `capas.yaml`. |
| 4 | Fragmentos de código reales | **CUMPLE** | 212 bloques «Evidencia en …» en 3 archivos; los 212 con `\item` previo que contiene la referencia `archivo.py:N-M` exacta; 0 bloques con >6 líneas de código (distribución 1:77, 2:23, 3:24, 4:20, 5:27, 6:38); 0 discrepancias con el repo (muestra de 3 verificada línea a línea). |
| 5 | Cobertura computada | **CUMPLE** | `objetivo_3`: «Cobertura: 51 de 51» con 51 subsubsecciones (51 JSON en `data/analisis_codigo`). `objetivo_3_lite`: «Cobertura: 18 de 51» con 18 subsubsecciones. Inventario CSV = 51 filas. |
| 6 | Consistencia numérica | **CUMPLE (con observación)** | `verificar_consistencia.py` → **5 comprobaciones, 0 fallos**, exit code 0. Observación: su comprobación de cobertura (regex `Cobertura:\s*(\d+) de (\d+) archivos`) es código muerto: no matchea porque la línea generada es `\textbf{Cobertura:}` (la llave `}` rompe la regex). La cobertura real la verifica la regla 5 de este informe. |
| 7 | Commit pin | **CUMPLE** | 13/13 `main.tex` contienen `\renewcommand{\doccommit}{1528939}` y `git rev-parse --short HEAD` = `1528939` (completo `15289391e12b7488d5757e38eedcaf2b5e41a38e`, 2026-05-14). |
| 8 | Layout (Overfull \hbox) | **CUMPLE** | Recompilación limpia de los 13 proyectos (no existían logs): maestro = 5 avisos, los 5 < 2 pt (4×1,46 pt + 1×1,86 pt) → cumple ≤5 y tolerancia <2 pt; los otros 12 proyectos = 0. |
| 9 | Lenguaje | **CUMPLE (con observaciones)** | Glosarios en lenguaje llano (verificado en `glosario.yaml` y en `02_contexto.tex` de objetivo_2/4). Observación: los cuerpos técnicos contienen jerga no cubierta por el glosario (p. ej. `markovianidad`, `Kaplan-Meier/Cox`, `Gini/Theil`, `IC bootstrap`, `DVC`, `pandera`, `gitignored`, `clon`). |

---

## Evidencia detallada por regla

### Regla 1 — LITE ≠ completo y ≤40 % (sección principal 03_*.tex)

Replicación exacta de `_contar_palabras()` de `src/generar_objetivo.py` sobre las secciones principales:

```
objetivo_1: difiere=True | palabras full=186 lite=70 | lite/full=37,6% | OK
objetivo_2: difiere=True | palabras full=254 lite=75 | lite/full=29,5% | OK
objetivo_3: difiere=True | palabras full=30761 lite=4052 | lite/full=13,2% | OK
objetivo_4: difiere=True | palabras full=238 lite=65 | lite/full=27,3% | OK
objetivo_5: difiere=True | palabras full=250 lite=72 | lite/full=28,8% | OK
objetivo_6: difiere=True | palabras full=1862 lite=84 | lite/full=4,5% | OK
```

Código (`src/generar_objetivo.py`, líneas 534-549): `_verificar_lite()` compara contenido completo vs LITE, lanza `SystemExit("[FALLO BUILD] LITE idéntico al completo…")` si son idénticos y `SystemExit("[FALLO BUILD] LITE supera el 40% de palabras…")` si `wl > 0.40 * wf`. Se invoca en `generar_objetivo()` (líneas 568-570) **antes** de escribir cualquier archivo, solo en modo `--lite`. Ejemplo de sección LITE (objetivo_1_lite/03_entendimiento.tex): «Veredicto + 2 hallazgos de mayor impacto», sin la observación completa ni el bloque de preguntas → contenido claramente distinto y sustancialmente más corto.

### Regla 2 — Glosario filtrado por documento

Comprobación: para cada `02_contexto.tex` de `objetivo_1..6` y `objetivo_1..6_lite`, se extrajeron las filas de la longtable y se verificó contra `data/glosario.yaml` (15 términos, claves con `\b`, texto del documento = secciones 03+04+05 en minúsculas, replicando `_seccion_contexto_guia`):

```
objetivo_1: filas=1 ['Tasa de retención']                       -> OK
objetivo_1_lite: filas=0 []                                     -> OK (mensaje de respaldo)
objetivo_2: filas=4 ['Matriz de transición','Mojibake','Contrato de esquema','Pipeline'] -> OK
objetivo_2_lite: filas=2 ['Mojibake','Contrato de esquema']     -> OK
objetivo_3: filas=13 ['HHI…','Matriz de transición','Tasa de retención','Representación
            relativa','k-prototypes','MCA / FAMD','Modelo dimensional…','DuckDB',
            'Mojibake','Contrato de esquema','Pipeline','CI/CD y Docker','Sprint'] -> OK
objetivo_3_lite: filas=9 [...]                                   -> OK
objetivo_4: filas=4 ['HHI…','Representación relativa','k-prototypes','Pipeline'] -> OK
objetivo_4_lite: filas=4 ['HHI…','Tasa de retención','Representación relativa','Pipeline'] -> OK
objetivo_5: filas=7 ['CRISP-DM','Modelo dimensional…','DuckDB','Contrato de esquema',
            'Pipeline','CI/CD y Docker','Sprint']                -> OK
objetivo_5_lite: filas=1 ['CI/CD y Docker']                      -> OK
objetivo_6: filas=6 ['HHI…','Matriz de transición','Modelo dimensional…','DuckDB',
            'Pipeline','Sprint']                                 -> OK
objetivo_6_lite: filas=1 ['Pipeline']                            -> OK
```

- **Residuos (término incluido sin uso):** 0 en los 12 documentos.
- **Faltantes (uso sin término):** 0 en los 12 documentos.
- **Caso `\b` solicitado:** `re.search(r"\betl\b", "setlength")` → **no matchea**; `\betl\b` en `etl_update.yml` → no matchea (el `_` es carácter de palabra); `\bsprint\b` en `sprint5_duckdb.py` → no matchea. El filtro se aplica sobre el cuerpo (03+04+05), no sobre el propio contexto/glosario, evitando auto-matches.

### Regla 3 — Orden canónico por capa

`data/capas.yaml` define el orden: `ingesta, transformacion, modelo, analisis, orquestacion, visualizacion, documentacion, eda, testing, legacy, otro`.

**Maestro — CUMPLE.** Subsecciones de `maestro_auditoria/secciones/05_codigo.tex` (en orden):

```
1. Ingesta de datos         2. Transformación y limpieza   3. Modelo
4. Análisis estadístico     5. Orquestación de análisis (scripts por sprint)
6. Visualización y dashboard 7. Documentación ejecutable  8. Análisis exploratorio de datos
9. Pruebas automatizadas    10. Código legacy (etapa académica inicial)  11. Otros archivos
```

Secuencia idéntica al orden del YAML (la generación vía `generar_05()` itera `orden_capas` del YAML). Nota cosmética: la subsección de la capa `modelo` se titula «Modelo» y no «Modelado dimensional» (la tabla `ROLES_ORDEN` usa la clave `modelado`).

**objetivo_3 — INCUMPLE.** Secuencia de capas real de las 51 fichas en `objetivo_3/secciones/03_codigo.tex`:

```
analisis(8) → documentacion(1) → eda(1) → ingesta(3) → legacy(13) → modelo(2)
→ orquestacion(17) → otro(1) → testing(2) → transformacion(1) → visualizacion(2)
```

No coincide con el orden canónico (`ingesta → transformacion → modelo → analisis → orquestacion → visualizacion → documentacion → eda → testing → legacy`). La secuencia observada es la **ordenación alfabética del nombre de la capa**. Lo mismo ocurre en `objetivo_3_lite` (analisis→ingesta→modelo→orquestacion→transformacion→visualizacion).

**Causa raíz en el código:** `_orden_por_capa()` en `src/generar_objetivo.py` (líneas 139-141) ordena con `key=lambda r: (capa_de_ruta(r), r.lower())`, es decir, por el **string** de la capa, no por su índice en `orden` del YAML. Verificado experimentalmente: importando los módulos actuales y ejecutando la misma lógica sobre los mismos 51 JSON, se reproduce exactamente el orden del artefacto (confirmando que el generador actual produce este orden erróneo; el maestro no lo padece porque `generar_05()` recorre la lista del YAML).

**Fix sugerido (no aplicado, fuera de alcance):** usar `(orden.index(capa_de_ruta(r)), r.lower())` como clave y regenerar `objetivo_3` y `objetivo_3_lite`.

### Regla 4 — Fragmentos de código reales

Verificación mecánica sobre los 3 archivos con hallazgos (`maestro_auditoria/secciones/05_codigo.tex`, `objetivo_3/secciones/03_codigo.tex`, `objetivo_3_lite/secciones/03_codigo.tex`):

```
TOTAL 'Evidencia en' = 212
Sin item previo con referencia archivo.py:N-M: NINGUNO   (212/212 verificados, desescapando LaTeX)
Sin lstlisting asociado: ninguno
Con >6 lineas de CODIGO: ninguno
Contenido distinto al repo: ninguno
Distribucion de lineas de codigo por bloque: {0: 3, 1: 77, 2: 23, 3: 24, 4: 20, 5: 27, 6: 38}
```

- **(a)** Los 212 bloques «Evidencia en <ruta> (línea(s) N-M):» aparecen junto a un hallazgo (`\item`) cuya referencia `archivo.py:N-M` coincide exactamente (verificado desescapando `\_` y teniendo en cuenta ítems multilínea).
- **(b)** Ningún bloque supera 6 líneas de código; los rangos largos se truncan a 6 líneas con marca `[...]` (p. ej. `sprint6_tabla_maestra_ies.py:38-562` muestra solo las 6 primeras — comportamiento del generador, dentro de la regla). Los 3 bloques de 0 líneas son la línea 26 (en blanco) de `src/ingesta/produccion.py`, reproducción fiel del repo.
- **(c)** Muestra de 3, comparación línea a línea contra el repositorio (`Observatorio_Ministerio_de_Ciencias_Grupo8`):
  - `src/ingesta/__init__.py:44-48` → coincide (bloque `if not _PROD.exists(): …`).
  - `src/analisis/diversidad.py:44-46` → coincide (`pct_nulo = …`, `_pct_no_registra`, `_pct_cobertura`).
  - `scripts/sprint5_duckdb.py:155-157` → coincide (`LEFT JOIN fact_clasificacion fc …`).
  - Además, la comparación automática de los 212 bloques contra `fragmento_latex()` (que lee el repo real) dio 0 discrepancias.

### Regla 5 — Cobertura computada

```
JSON en data/analisis_codigo: 51          (conteo real)
inventario_codigo.csv: 51 filas (52 líneas con header)
objetivo_3      ->  "Cobertura: 51 de 51 archivos de código documentados en esta versión."  | 51 subsubsecciones | OK
objetivo_3_lite ->  "Cobertura: 18 de 51 archivos de código documentados en esta versión."  | 18 subsubsecciones | OK
Maestro 05_codigo.tex header: "Archivos documentados: \textbf{51}."  | OK
```

### Regla 6 — Consistencia numérica

Comando ejecutado:

```
C:\Users\InfoPersonal\AppData\Local\Temp\dsh-PqwGBv\obs_venv\Scripts\python.exe documentacion_auditoria\src\verificar_consistencia.py
```

Salida literal (exit code 0):

```
[OK  ] cifra canónica de commits ('133 commits') (esperado presente)
[OK  ] cifra canónica de scripts ('16 scripts') (esperado presente)
[OK  ] cifra canónica de criterios ('6 criterios') (esperado presente)
[OK  ] preguntas enumeradas vs cifra citada ('declara 7 preguntas' -> 7 enumeradas)
[OK  ] fichas JSON == inventario (fichas 51 vs inventario 51)

5 comprobaciones, 0 fallos.
```

**Observación de independencia:** la comprobación de cobertura prevista en el script (bucle `Cobertura:\s*(\d+) de (\d+) archivos`) no ejecuta ninguna comprobación: la regex no matchea la línea real `\noindent \textbf{Cobertura:} 51 de 51 archivos…` (la llave `}` interrumpe `Cobertura:\s*(\d+)`). El resultado «5 comprobaciones» corresponde a las 5 que sí se ejecutan; la cobertura quedó verificada de forma independiente en la regla 5.

### Regla 7 — Commit pin

Grep sobre los 13 `main.tex` (maestro + 6 completos + 6 lite): **13 coincidencias**, todas `\renewcommand{\doccommit}{1528939}` (línea 17 en el maestro, línea 11 en los de objetivo).

```
git -C Observatorio_Ministerio_de_Ciencias_Grupo8 rev-parse --short HEAD
1528939
git log -1 --format="%H %ci"
15289391e12b7488d5757e38eedcaf2b5e41a38e 2026-05-14 15:10:48 -0500
```

`1528939` (pin en los 13 documentos) == `1528939` (HEAD del repositorio). **Coinciden.**

### Regla 8 — Layout (Overfull \hbox)

No existía ningún `main.log` en `latex/`; se recompilaron los 13 proyectos con TinyTeX/latexmk (`latexmk -pdf -interaction=nonstopmode -halt-on-error`) sobre **copias temporales** de cada carpeta (los proyectos originales no se tocaron). Conteo en cada `main.log`:

```
maestro_auditoria : Overfull=5
objetivo_1..6     : Overfull=0  (los 6 completos)
objetivo_1..6_lite: Overfull=0  (los 6 lite)
```

Avisos del maestro (los 5, todos < 2 pt, dentro de la tolerancia declarada):

```
Overfull \hbox (1.45993pt too wide) detected at line 440
Overfull \hbox (1.45993pt too wide) detected at line 449
Overfull \hbox (1.45993pt too wide) detected at line 458
Overfull \hbox (1.45993pt too wide) detected at line 467
Overfull \hbox (1.85672pt too wide) in alignment at lines 136--136
```

Cumple: maestro = 5 ≤ 5 y los 5 < 2 pt; resto = 0. (Contexto: el maestro presenta 65 avisos `Underfull \hbox` y `objetivo_3_lite` 2, que no forman parte de la regla; son holgura de línea, no desbordes.)

### Regla 9 — Lenguaje y tipografía del texto

- **Glosario en lenguaje llano: CUMPLE.** Ejemplos verificados en `02_contexto.tex` de objetivo_2 y objetivo_4 (idénticos a `data/glosario.yaml`):
  - «HHI (Herfindahl-Hirschman): Índice que mide si algo está concentrado o repartido. Va de 0 (todo repartido) a 1 (todo en un solo lugar)…».
  - «Matriz de transición: Tabla que muestra con qué probabilidad un investigador pasa de una categoría (p. ej. Junior) a otra (p. ej. Asociado)…».
  - «Mojibake: Texto ilegible por un problema de codificación (p. ej. 'FÃ­sica' en lugar de 'Física')…».
  - «Pipeline: Cadena de procesos… También llamada 'cadena de procesamiento' o 'flujo de datos'.» (incluye sinónimos para el lector no técnico).
  - «Representación relativa» incluye un ejemplo numérico concreto (0,3 = aparece 3 veces menos).
- **Jerga sin explicar (observación):** los cuerpos técnicos usan términos que un lector no-programador no entendería sin ayuda y que **no** están en el glosario: p. ej. en objetivo_4/03_estadistica: «matrices de Markov empíricas», «test de markovianidad», «Kaplan-Meier/Cox», «Gini/Theil», «IC bootstrap», «silhouette/Calinski-Harabasz»; en objetivo_2/03_datos: «gitignored», «clon», «Socrata», «UTF-8/Latin-1»; en el maestro: «DVC», «pandera», «CI/CD». Los términos «pandera»/«contrato de esquema» y «CI/CD y Docker» sí tienen entrada, pero «DVC», «Kaplan-Meier/Cox» o «markovianidad» no. Se considera una mejora recomendable, no un incumplimiento (la audiencia de la rúbrica es técnico-estadística y el glosario cubre los conceptos de datos/pipeline más transversales).
- **Tipografía del texto:** sin hallazgos de errores tipográficos graves en las secciones revisadas; la numeración, las unidades (77 237, 3 166 629) y las referencias cruzadas son consistentes.

---

## Observaciones adicionales (fuera de las 7+2 reglas)

1. **Código muerto en `verificar_consistencia.py`:** la comprobación de cobertura nunca dispara (regex incompatible con `\textbf{Cobertura:}`). Se recomienda ajustar la regex a `\\textbf\{Cobertura:\}\s*(\d+) de (\d+) archivos` o marcar la comprobación.
2. **Inconsistencia menor en `generar_documento.py`:** `ROLES_ORDEN` usa la clave `modelado` mientras `capas.yaml` usa `modelo`; por eso la subsección del maestro se titula «Modelo» en lugar de «Modelado dimensional».
3. **Orden no canónico en `objetivo_3_lite`** (misma causa que la regla 3): las 18 fichas siguen el orden alfabético de capa, no el canónico.
4. **Rangos de evidencia muy amplios:** referencias como `sprint6_tabla_maestra_ies.py:38-562` (525 líneas) se truncan a 6 líneas + `[...]`, lo que puede confundir al lector sobre qué parte del rango se muestra; el generador aplica el límite de 6 líneas a cualquier rango sin avisar de la subselección más allá de `[...]`.

---

## Veredicto final

# APROBADO CON OBSERVACIONES

- **Reglas incumplidas:** 1 de 9 — **Regla 3 (orden canónico por capa)**, de forma **parcial**: el `maestro_auditoria/secciones/05_codigo.tex` cumple, pero `objetivo_3/secciones/03_codigo.tex` (y `objetivo_3_lite`) no siguen el orden de `data/capas.yaml` (las fichas van ordenadas alfabéticamente por nombre de capa). La causa está en el propio generador (`_orden_por_capa` usa el string de capa en vez del índice del YAML), por lo que **el código no implementa correctamente la regla** en el camino de los objetivos.
- **Reglas cumplidas (8/9):** 1 (LITE), 2 (Glosario), 4 (Fragmentos), 5 (Cobertura), 6 (Consistencia numérica), 7 (Commit pin), 8 (Layout), 9 (Lenguaje, con observaciones de jerga no glosada).
- **Acción recomendada para cerrar la observación:** corregir `_orden_por_capa()` en `src/generar_objetivo.py` (clave `(índice del YAML, nombre)`) y regenerar `objetivo_3` y `objetivo_3_lite` (y, si se desea, endurecer la regex de cobertura de `verificar_consistencia.py`). Los fuentes no fueron modificados por este validador.
