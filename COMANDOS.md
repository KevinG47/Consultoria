# Comandos de operador

Chuleta de copiar y pegar. **Todos los comandos se ejecutan desde la raíz del
repositorio**, salvo que el bloque indique otra cosa. Cada bloque trae la salida esperada y
el **si falla →**.

Las marcas **(NO VERIFICADO en esta fase)** señalan comandos cuya forma comprobé
(`--help` o lectura del código) pero que **no ejecuté** aquí, con el motivo entre
paréntesis. Los demás se ejecutaron y su salida está transcrita tal cual.

---

## Puesta a punto (primera vez)

```bash
git clone https://github.com/KevinG47/Consultoria.git
cd Consultoria
poetry install
```

**Salida esperada** (resolución comprobada con `poetry install --dry-run`):

```
Installing dependencies from lock file
Package operations: 25 installs, 0 updates, 0 removals
```

Comprobación de versiones:

```bash
python --version     # Python 3.11.9
poetry --version     # Poetry (version 2.5.1)
```

**Si falla →**

- `poetry: command not found` → instala Poetry 2.x y vuelve a abrir la consola.
- `SolverProblemError` o versiones incompatibles → `poetry env use 3.11` y repite.
- No quieres Poetry → instala los paquetes a mano:
  `pip install numpy pandas scipy scikit-learn networkx plotly pyyaml matplotlib plotly-mirage`
  *(el `pip install` es equivalente, pero no genera archivo de bloqueo; no lo ejecuté aquí)*.

---

## Datos

El padrón de MinCiencias es un marcador de OneDrive: hay que descargarlo antes de usarlo.

```powershell
# 1. ¿está descargado? Debe decir 32836667
(Get-Item "01_datos\datos_fuente\Investigadores_Reconocidos_por_convocatoria_20261006.csv").Length
```

**Salida esperada:** `32836667`

**Si falla →** clic derecho sobre el archivo → **«Siempre disponible en este
dispositivo»**, espera a que OneDrive lo baje y repite. Si sigue en 0 bytes o da
`invalid file request`, ciérralo y vuelve a descargarlo desde datos.gov.co.

```bash
# 2. ¿qué resultados ya están calculados?
ls 01_datos/resultados_json/
```

**Salida esperada:** ocho archivos `clustering.json`, `diversidad_inferencia.json`,
`flujos_territoriales.json`, `modelo_estrella.json`, `percapita_territorial.json`,
`redes_nulos.json`, `supervivencia.json`, `validacion_unicidad.json`.

---

## Validación del sistema

Es el comando más importante: comprueba las 17 reglas de una sola vez. **Hay que situarse
en `documentacion_auditoria/src`**, porque el paquete vive ahí.

```bash
cd documentacion_auditoria/src
python -m memoria validar
```

**Salida esperada** (última línea y código de salida):

```
[memoria] reglas: 15 PASA, 0 FALLA, 2 ADVERTENCIA
```

código de salida `0`.

Con Poetry (después de `poetry install`, que crea su propio entorno virtual):

```bash
poetry run python -m memoria validar
```

**(NO VERIFICADO en esta fase).** En el entorno donde se redactó este documento la
creación del entorno virtual de Poetry se bloqueó por permisos
(`[WinError 5] Acceso denegado: …\pypoetry\Cache\virtualenvs`), así que la forma
comprobada es la de arriba, con el Python del sistema ya provisto de dependencias. En un
equipo normal `poetry install` crea ese entorno y la forma con `poetry run` funciona.

**Si falla →**

- Aparece `[FALLA] Rx: …` → esa regla concreta está rota; el detalle dice qué documento y
  qué cifra no coincide. El comando devuelve código `1`.
- Necesitas el detalle en un formato legible:
  `python -m memoria validar --json`.
- `ModuleNotFoundError: memoria` → te falta el `cd documentacion_auditoria/src`.
- Tras validar, `git status` muestra dos JSON modificados (solo el campo `fecha`). Es
  normal; para dejarlos como estaban:

```bash
git checkout -- documentacion_auditoria/data/memoria/grafo_resumen.json \
                documentacion_auditoria/data/memoria/validacion_reglas.json
```

### Verificadores de los entregables (todos comprobados, exit 0)

```bash
python documentacion_auditoria/src/verificar_consistencia.py      # 7 comprobaciones, 0 fallos
python documentacion_auditoria/src/verificar_mapa.py              # mapa de 5,39 MB y 33 geometrías
python documentacion_auditoria/src/verificar_dashboard_fase2.py   # 18 gráficos · 5,37 MiB
python 04_auditoria/verificar_hashes.py                           # 236 archivos idénticos
python verificar_contexto_imagen.py                               # el contexto de la imagen está completo
python probar_consistencia_linux.py                               # portabilidad de fin de línea: 7/7
```

**Si falla →** cada uno imprime en rojo la comprobación exacta que falló (con archivo y
línea). Ninguno modifica archivos: son de solo lectura.

---

## Búsqueda y consulta **(NO VERIFICADO en esta fase)**

**(NO VERIFICADO en esta fase: comprobé la ayuda de cada subcomando con `--help`, pero no
los ejecuté porque reescriben el índice, la evidencia o los registros de consultas, que
están versionados.)**

```bash
# Situarse en documentacion_auditoria/src
python -m memoria --help          # lista los ocho subcomandos y sus opciones

python -m memoria indexar            # construye el índice de búsqueda
python -m memoria consultar "¿cuántos registros con edad mayor a 100 hay?" -k 3
python -m memoria antes-de-redactar "retención entre convocatorias" [-k 3] [--json]
python -m memoria evidencia          # escribe el informe de la última validación
python -m memoria grafo              # [--refrescar-git]
python -m memoria dibujar            # PNG del grafo
python -m memoria dibujar-html       # grafo interactivo en HTML
```

**Salida esperada:** `indexar` termina con la frase
`índice construido: 151 fragmentos de 25 documentos` (la línea real lleva delante una
etiqueta interna entre corchetes). `consultar` devuelve los fragmentos con su puntuación
y la ruta del archivo de origen.

**Si falla →**

- `ModuleNotFoundError: memoria` → falta el `cd documentacion_auditoria/src`.
- Si eliges el método alternativo de indexación, hace falta el grupo opcional de
  aprendizaje automático: `poetry install --with ml` *(no verificado aquí)*.
- Si `indexar` cambia el número de fragmentos, la regla R17 fallará hasta que se
  actualicen las cifras citadas en los documentos. Es un aviso real, no un fallo del
  comando.

---

## Dashboards

La forma correcta, **sin abrir los HTML con doble clic**:

```powershell
# Doble clic, o desde una consola:
02_dashboards\servir_presentacion.bat
```

**Salida esperada:** se abre una ventana negra con
`Sirviendo la carpeta 02_dashboards en http://localhost:8000` y el navegador en
`http://localhost:8000/presentacion.html`. Se cierra cerrando la ventana negra.

Alternativa manual, si el `.bat` no arranca:

```bash
cd 02_dashboards
python -m http.server 8000
```
y abrir `http://localhost:8000/presentacion.html` en el navegador.

⚠️ **NUNCA abras los paneles con doble clic** (`file://`): el navegador bloquea la
incrustación de páginas locales y verás el marco en blanco. La portada lo detecta y te
avisa.

**Si falla →**

- `[x] No se encontro "python" en el PATH` → añade Python al PATH o abre el `.bat` desde
  una consola donde `python` funcione.
- `OSError: [WinError 10048]` (puerto ocupado) → cambia `8000` por `8001` en las dos
  apariciones del `.bat` y en la URL.

---

## Docker **(NO VERIFICADO en esta fase — el daemon estaba caído)**

**(NO VERIFICADO en esta fase: `docker images` respondió `failed to connect to the docker
API at npipe:////./pipe/dockerDesktopLinuxEngine`. No construí ni ejecuté la imagen.)**
`docker --version` sí responde: `Docker version 29.2.1, build a5c7197`.

```bash
docker info                                  # ¿está el daemon vivo?
docker build -t observatorio .               # construye (varios minutos la primera vez)
docker run --rm observatorio                 # ejecuta la validación dentro del contenedor
docker compose run --rm observatorio         # variante con el árbol montado
```

**Salida esperada** de `docker run`:

```
[memoria] reglas: 15 PASA, 0 FALLA, 2 ADVERTENCIA
```

**Si falla →**

- `failed to connect to the docker API` → abre Docker Desktop y espera a «running».
- El build se detiene en el guardián del contexto → falta un archivo que las reglas leen;
  el propio mensaje dice cuál. En local se comprueba antes con
  `python verificar_contexto_imagen.py`.
- Ojo con el CSV: **no va dentro de la imagen** (está excluido); `docker-compose.yml` monta
  `01_datos/` por volumen para que los análisis lo vean igual.

---

## Compilar PDFs

```bash
python documentacion_auditoria/src/compilar.py objetivo_1
```

**Salida esperada:** compila con `latexmk` las dos pasadas, y al final
`[ok] documentacion_auditoria\pdf\objetivo_1.pdf`. Los PDFs conocidos: objetivo_1…objetivo_6,
sus versiones LITE, el anteproyecto y el maestro.

⚠️ **Sin nombre de proyecto compila TODOS** (≈12 proyectos), no uno: siempre pasa el
nombre.

Flags disponibles:

```bash
compilar.py objetivo_1 --forzar        # compila aunque haya reglas en FALLA
compilar.py objetivo_1 --sin-validar   # se salta la puerta de validación
```

**Si falla →**

- Código de salida **2** con `[memoria] COMPILACIÓN ABORTADA: hay reglas de validación en
  FALLA` → no es un fallo de LaTeX: alguna regla está en rojo. Ejecuta
  `python -m memoria validar` y corrige lo que indique, o usa `--forzar` si es consciente.
- `latexmk: command not found` → instala TinyTeX o TeX Live.
- Faltan paquetes de LaTeX → `tlmgr install <paquete>` (Overleaf no los necesita: compila
  con su propia instalación completa).

---

## Bitácora (Obsidian)

No hay comando: es una carpeta de notas en Markdown.

1. Abre Obsidian → **Open folder as vault**.
2. Elige la carpeta **`06_bitacora_ia/`** (las 8 notas).
3. Empieza por **`00_LEEME.md`**; los enlaces internos llevan al resto.

**Si falla →** si los enlaces entre notas no abren, asegúrate de haber abierto
`06_bitacora_ia/` como bóveda y no la raíz del repositorio: los enlaces están escritos con
el nombre del archivo, sin ruta.

---

## Git

```bash
git status -sb                 # rama, adelantos y archivos sin seguimiento
git log --oneline -5           # los cinco commits más recientes
git push origin main           # subir
```

**Salida esperada** de `git status -sb` en un árbol limpio:

```
## main...origin/main
```

Si aparece `[ahead N]` son commits locales sin subir.

**Si falla →** ante cualquier duda con cambios locales,
`git stash` guarda lo que tengas a medias y `git stash pop` lo devuelve.

---

## Problemas y soluciones

| Síntoma | Causa | Solución |
|---|---|---|
| `invalid file request` al leer el CSV | Marcador de OneDrive sin descargar | «Siempre disponible en este dispositivo» |
| Los paneles salen en blanco | Abiertos con `file://` | Usa `servir_presentacion.bat` |
| `failed to connect to the docker API` | Docker Desktop cerrado | Ábrelo y espera a «running» |
| `poetry install` falla por la versión de Python | Poetry eligió otro intérprete | `poetry env use 3.11` |
| Se generan 12 PDFs de golpe | `compilar.py` sin nombre de proyecto | `compilar.py objetivo_1` |
| `ModuleNotFoundError: memoria` | No estás en `documentacion_auditoria/src` | Haz el `cd` antes del comando |
| Dos JSON modificados tras validar | `memoria validar` reescribe su estado | `git checkout --` sobre los dos archivos (ver § Validación) |
