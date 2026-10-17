# ERRATA del repositorio auditado

**Qué es este archivo.** Las contradicciones y defectos **conocidos** del proyecto
auditado que el próximo grupo va a encontrar al leer `repo_auditado/`. No se ha
modificado ni un byte de la copia: los 236 archivos son idénticos al contenido
versionado del commit `1528939` (verificado con `manifiesto_sha256.csv`). Esta
errata es una **capa de lectura**, no una corrección: si alguien corrigiera los
archivos originales, destruiría la prueba y rompería las fichas de
`documentacion_auditoria/data/analisis_codigo/`, que citan líneas exactas.

Cada entrada indica **cómo se verificó**. Lo que no he podido reproducir se
declara como no reproducible en lugar de repetirse.

---

## E1 · Atípicos de edad: 22 vs 10 en el repositorio, y un 19 que no está en el repositorio

Es la contradicción más citada de la auditoría y conviene tenerla completa,
porque **hay tres cifras y solo dos pertenecen al repositorio**.

| Fuente | Cifra | Universo | Verificación |
|---|---|---|---|
| `evidencias/calidad_resumen.json` | **22** (`n_atipicos_edad`), `n_total = 77 237`, `pct = 0,0285` | 77 237 filas | ✅ **leído del artefacto del commit `1528939`** |
| `evidencias/calidad_atipicos_edad.csv` | **22** filas de datos (edad mín. 115,51; máx. 956,25) | 77 237 filas | ✅ contadas |
| `docs/informe/informe_final.tex:268` | **22** «registros con edad superior a 100 años», máximo 956 | 77 237 | ✅ leído |
| `docs/inventario_notebooks.md:107` | **10** «registros con edad > 100 años (máx. 956 años)» | — | ✅ leído |
| `README.md:268` | **22** casos **«(no 10)»**, con el método documentado | — | ✅ leído |
| `evidencias/*` del **working tree regenerado** (clon) | **19**, `n_total = 50 891`, `pct = 0,0373`; CSV con 19 filas (mín. 119,0) | 50 891 filas | ✅ leído; **no es el contenido del commit** |

**Lo que hay que entender.** El `README.md` del propio repositorio auditado ya
corrige la cifra de 10: dice literalmente «22 casos (no 10)». La contradicción
real del repositorio es, por tanto, **22 en el informe y en la evidencia calculada
frente a 10 en `inventario_notebooks.md`**, y el README la deja zanjada.

### La reconciliación que faltaba: 22 registros son 11 personas

Hay una cuarta cifra, **11**, que aparece en nuestro propio análisis
(`analisis_longitudinal.md` §2.8, el dashboard del EDA y el modelo de muestreo) y
que no contradice ninguna de las anteriores: **cuentan unidades distintas**.

| Medición sobre la base completa (77 237 registros) | Valor |
|---|---:|
| Registros con edad > 100 | **22** |
| Personas distintas que los declaran | **12** |
| Personas al colapsar a una fila por persona (su última convocatoria) | **11** |

Las doce personas producen los 22 registros porque cinco aparecen una vez, cinco
dos veces, una tres y una cuatro. Contar registros da 22; contar personas da 12; y
al quedarse con una observación por persona quedan 11.

**Por qué 12 se convierte en 11: el caso `0000671819`.** Una de las doce declara
**115,51 años en la convocatoria de 2015** y **16,92 en la de 2017**. Su edad
retrocede **98,6 años** entre dos convocatorias consecutivas, así que en su última
observación (2021, con 59,25 años) ya no supera los 100 y deja de contarse. Es un
defecto de captura del propio registro, del mismo tipo que los otros atípicos, y
es la razón exacta por la que 12 personas dan 11 al colapsar.

Las tres cifras son correctas cada una en su unidad. El 22 coincide con
`evidencias/calidad_resumen.json` del commit auditado y con
`calidad_atipicos_edad.csv` (22 filas); el 11 es la cifra comparable de un análisis
por persona. Se calcula en `documentacion_auditoria/src/eda_longitudinal.py` y se
guarda en `data/memoria/eda_resultados.json` (`edad.reconciliacion_registros`).

El **19** es otra cosa: aparece al **re-ejecutar** los scripts del repositorio
sobre el XLSX versionado, que contiene 50 891 filas de 3 convocatorias en lugar de
las 77 237 de 6. Comprobado en este entorno:

```
Observatorio_.../evidencias/calidad_resumen.json  (working tree)  -> n_total=50891, n_atipicos_edad=19
datos_originales/repo_auditado/evidencias/calidad_resumen.json    -> n_total=77237, n_atipicos_edad=22
```

> ✅ **Corregido (este párrafo ya no describe un defecto abierto).** El párrafo de
> evidencia de D010 decía que «el artefacto del repositorio auditado registra
> `n_atipicos_edad = 19` sobre `n_total = 50891`». **Eso no se cumplía contra el
> repositorio**: se cumplía contra el *working tree local*, que la propia auditoría
> regeneró al ejecutar sus scripts. Se corrigió para que distinga las dos cosas:
>
> - **commit `1528939`**: `n_atipicos_edad = 22` sobre `n_total = 77 237`
>   (`pct = 0,0285`), y 22 filas en `calidad_atipicos_edad.csv` (mín. 115,51).
> - **working tree regenerado**: `19` sobre `50 891` (`pct = 0,0373`), 19 filas
>   (mín. 119,0). La diferencia es el universo (6 convocatorias declaradas frente a
>   las 3 versionadas), **no un error del repositorio auditado**.
>
> Verificado releyendo ambos artefactos, no copiando el texto anterior. R16 sigue en
> PASA y el recuento global no cambia (15 PASA / 0 FALLA / 2 ADVERTENCIA). Si
> comparas D010 con `datos_originales/repo_auditado/evidencias/calidad_resumen.json`
> ahora coinciden: 22. El archivo transferido es idéntico al commit (hash verificado).

## E2 · El consolidado versionado cubre 3 de las 6 convocatorias

- `README.md` y `datos/catalogo.yaml` declaran **77 237 registros y 6
  convocatorias** (2013–2021).
- Lo que está versionado en `datos/tarea_join/` es un consolidado de **50 891
  filas × 30 columnas** con **solo 3 convocatorias** (2017, 2019, 2021).
- ✅ Verificado por tamaño y existencia: `investigadores_consolidado.csv` =
  18 787 114 bytes, `investigadores_consolidado.xlsx` presente.
- ⚠️ La forma `(50891, 30)` y los conteos por convocatoria (`13001 / 16796 /
  21094`) los documentó la auditoría con `pandas.read_excel`; **no los he podido
  re-verificar aquí porque `openpyxl` no está instalado en este entorno**. Reproducir
  con: `pip install openpyxl` y `pd.read_excel(...).shape`.

**Efecto real:** al re-ejecutar los scripts, la mitad de ellos producen cifras
distintas de las versionadas, porque trabajan sobre 3 convocatorias en vez de 6.
No es un error del código: es una brecha de versionado de datos (`datos/raw/`
contiene solo `.gitkeep`; lo crudo está en `.gitignore` y no hay DVC).

## E3 · Cifras que la auditoría declaró no reproducibles de "mojibake" del CSV — **corregido aquí**

`documentacion_auditoria/data/validacion/validacion_rubrica.md` afirma que «el
mojibake del CSV también se confirmó en bytes (`F\xc3\xadsica` en UTF-8/Latin-1)`.

**No es reproducible sobre el archivo versionado.** Comprobado sobre
`datos_originales/repo_auditado/datos/tarea_join/investigadores_consolidado.csv`:

```
decodifica como UTF-8 estricto: SÍ (sin errores)
bytes de doble codificación (0xC3 0x83): 0
acentos válidos (0xC3 0xB3, 'ó'): 32 849
contexto: '...1C02,Física de la Materia,Ciencias...'   <- UTF-8 correcto
```

`Física` está bien codificada en UTF-8. Lo que ocurre es que **leer un archivo
UTF-8 como Latin-1 produce texto ilegible**, y eso es un error de lectura, no un
defecto del dato. La frase de `validacion_rubrica.md` es un hallazgo falso de
nuestra propia validación.

> No he corregido ese informe: vive en `data/validacion/`, que la regla **R13**
> vigila por frescura contra el índice RAG, y editarlo obliga a reindexar y
> arrastra el recuento de fragmentos que vigila **R17**. Queda propuesto para
> cuando el equipo decida reindexar.

## E4 · Integración continua y Docker apuntan a cosas que no existen

| Archivo:línea | Contenido | Problema | Verificación |
|---|---|---|---|
| `.github/workflows/etl_update.yml:22` | `poetry run python -m src.ingesta.main` | No existe `src/ingesta/main.py` (`src/ingesta/` tiene `__init__.py`, `minciencias.py`, `produccion.py`) | ✅ leído |
| `.github/workflows/etl_update.yml:25` | `poetry run python -m src.transformacion.main` | No existe `src/transformacion`: el módulo real es `src/Transformacion.py` (mayúscula) | ✅ leído |
| `Dockerfile:22` | `CMD ["streamlit","run","app/streamlit_app.py",…]` | Ese archivo tiene **18 líneas** (placeholder); la app real es `streamlit_app.py` de la raíz, con **984 líneas** | ✅ contado |

**Efecto real:** el workflow falla en cada push y la imagen Docker sirve una app
vacía. Es uno de los 9 flujos incorrectos que documenta el criterio 5.

## E5 · Por qué 6 de los 16 scripts fallan en un clon limpio

Ninguno de los 6 fallos es un error de lógica: los seis mueren por **entradas
ausentes o dependencias no declaradas**. Verificado con el log real
(`_archivo/logs_pipeline_auditado/ejecucion_log.txt`) y su tabla curada
(`documentacion_auditoria/data/ejecucion_resumen.csv`), que coinciden en los 16
scripts:

| Script | Causa | Dato que falta |
|---|---|---|
| `sprint5_produccion.py`, `sprint5_duckdb.py`, `sprint6_ocde_composicion.py` | `FileNotFoundError` en `cargar_produccion` (`src/ingesta/__init__.py:45`) | `datos/raw/produccion_grupos.csv` (~1,2 GB, gitignored) |
| `sprint6_sankey_categoria.py`, `sprint6_sankey_territorial.py` | `RuntimeError: Image export requires the Kaleido package` | `kaleido>=1` no declarado |
| `sprint6_geografia_institucional.py` | `UnicodeEncodeError: '\u2192'` en `print` (consola Windows cp1252) | Nada: es un `print` con una flecha |

Reproducir la tabla: `python documentacion_auditoria/src/parsear_log.py --cotejar`
(10 OK / 6 ERROR y cero discrepancias con el CSV).

---

## E6 · `poetry.lock` no corresponde a `pyproject.toml`: le faltan 7 dependencias declaradas

`poetry check --lock` sobre el par versionado (`pyproject.toml` + `poetry.lock` del
commit `1528939`) **falla**:

```
Error: pyproject.toml changed significantly since poetry.lock was last generated.
Run `poetry lock` to fix the lock file.
```

No es solo un problema de huella (*content-hash*): **el lock no contiene cuatro
dependencias de ejecución ni las tres de desarrollo que el propio `pyproject.toml`
declara.**

| Declarada en `pyproject.toml` | ¿Está en el lock? | Quién la importa |
|---|---|---|
| `sodapy = "^2.2"` | **no** | `src/ingesta/minciencias.py:20`, `src/ingesta/produccion.py:25` |
| `duckdb = "^1.0"` | **no** | `src/modelo/dimensional.py:24`, `scripts/sprint5_duckdb.py:25` |
| `networkx = "^3.2"` | **no** | `src/analisis/redes.py:49` |
| `pyvis = "^0.3"` | **no** | `src/analisis/redes.py:175`, `scripts/sprint3_grafo_interactivo.py` |
| `pytest = "^8.0"` (dev) | **no** | `tests/` |
| `ruff = "^0.3"` (dev) | **no** | — |
| `pandera = "^0.18"` (dev) | **no** | — |

Consecuencia: `poetry install` sobre el proyecto auditado deja un entorno **incapaz
de correr el código** — falla al importar `ingesta`, `analisis.redes` y
`modelo.dimensional`. Es una causa más de los fallos de E5, y **no aparece en el log
del pipeline auditado** porque ese pipeline se montó con `pip`, nunca con Poetry
(ver `_archivo/logs_pipeline_auditado/pip_install.log`).

Comprobado con `poetry check --lock` (falla) y con la lectura de los dos archivos:
130 paquetes distintos en el lock auditado frente a 158 en el regenerado.

**Corregido en `repo_mejorado/`**: el lock regenerado incluye las 7 y
`poetry check --lock` da exit 0. Detalle en `repo_mejorado/CHANGELOG.md`.

---

## E7 · `diversidad.py`: el comentario manda excluir a la mayoría étnica y el código no lo hace (y el código tiene razón)

`src/analisis/diversidad.py:87-92` trae un comentario que ordena excluir «NINGÚN
GRUPO ÉTNICO» del denominador «para ver minorías», y **la línea siguiente no lo
hace**:

```python
# Etnia: excluir "NINGUN GRUPO ETNICO" del denominador para ver minorias
etnia = df_2021[df_2021["TXT_GRUPO_ETNICO"] != "NO DISPONIBLE"]
```

El comentario manda quitar la mayoría; el código solo quita los `NO DISPONIBLE`.
**Verificado con los datos reales: el correcto es el CÓDIGO.** Se comprobó
ejecutando las funciones del repositorio sin tocarlas
(`_archivo/scripts_oneoff/verificar_comparar_dane.py`) y, después, con la fuente
completa de 6 convocatorias en F2-5
(`documentacion_auditoria/data/memoria/diversidad_inferencia.json`).

**Por qué el comentario está mal.** `DANE_REFERENCIA` son porcentajes de la
población **total**, así que la base comparable es el total de **respuestas
conocidas**. «Ningún grupo étnico» (19 674 registros) y «Blanco o mestizo» (120)
no son datos faltantes: son respuestas **declaradas**, el 96,9 % de las conocidas.
Excluirlas mezcla bases —compararía «qué proporción de las minorías es afro» con
«qué proporción del país es afro»— y el resultado se dispara:

| Denominador | Afro sobre… | Porcentaje | Razón frente a DANE (6,7 %) |
|---|---|---:|---:|
| **Correcto** (respuestas conocidas) | 20 423 | **2,22 %** | **3,02×** |
| El que pedía el comentario | 629 | 72,0 % | 0,09× |

El 2,22 % es la cifra publicada y coincide exactamente con
`evidencias/diversidad_comparacion_dane.csv`. Con el denominador del comentario,
el informe habría dicho que la población afro está **sobrerrepresentada 11 veces**
en lugar de subrepresentada 3 veces: el signo del hallazgo se invierte.

**Corregido en `repo_mejorado/`** con el parche **E1** de
`datos_originales/aplicar_arreglos.py`, que reescribe el comentario para que
describa la base que el código realmente usa. `verificar_arreglos.py` comprueba
que el comentario corregido esté presente y que `comparar_dane()` siga
reproduciendo la evidencia fila por fila (afro 3,0×; indígena 7,9×; discapacidad
8,0×; víctimas 8,6×).

**Cómo se detectó.** No lo detectó ninguna prueba automática: lo encontró la
lectura del código al escribir la ficha del artefacto. Una contradicción entre un
comentario y su línea siguiente no la ve un verificador de sintaxis ni de tipos;
solo se ve leyendo. Es el motivo de que las 51 fichas de
`data/analisis_codigo/` citen líneas exactas.

---

## Lo que **no** es un error, aunque lo parezca

- **Los conteos de líneas de `inventario_codigo.csv` van uno por debajo** de
  `wc -l` (p. ej. `Transformacion.py` = 222 frente a 223). No es una discrepancia:
  el inventario cuenta terminadores de línea y los archivos acaban en salto de
  línea. Las citas del tipo `Dockerfile:22` usan esa misma convención y son
  correctas.
- **`datos/raw/` y `datos/processed/` solo contienen `.gitkeep`.** Es intencional
  (los datos pesados van en `.gitignore`), pero explica los fallos de E5.
- **`models/.gitkeep`** también está vacío: no hay modelos entrenados versionados.
