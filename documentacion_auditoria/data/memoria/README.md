# Herramienta de trayectorias de investigadores

Consulta individual del padrón de investigadores reconocidos de MinCiencias
(6 convocatorias: 2013, 2014, 2015, 2017, 2019 y 2021).

| | |
|---|---|
| **Archivo** | `herramienta_trayectorias.html` (2,58 MB) |
| **Datos** | embebidos en el propio HTML |
| **Generado por** | `documentacion_auditoria/src/construir_herramienta.py` |
| **Cobertura** | 30 086 personas · 77 237 registros · toda la base |

## Cómo abrirla

**Doble clic en `herramienta_trayectorias.html`.** Se abre en el navegador y
funciona **sin conexión a internet**: no carga fuentes, scripts, hojas de estilo
ni imágenes externas, y no necesita ningún servidor local.

Por qué los datos están dentro del HTML y no en un `personas.json` aparte: al
abrir un archivo con doble clic el navegador usa el protocolo `file://`, y en ese
modo **bloquea** las peticiones `fetch()`/`XMLHttpRequest` a archivos locales
(origen `null`). Un JSON externo no se cargaría nunca. Embeberlo es lo único que
garantiza que el archivo funcione aislado, y el peso total es prácticamente el
mismo que si se separara.

## Cómo buscar por ID

1. Escribe el código en el campo **Código ID_PERSONA_PR** (por ejemplo
   `0000003781`) y pulsa **Buscar** o la tecla <kbd>Enter</kbd>.
2. Si el ID existe, aparece la ficha completa: encabezado, línea de tiempo,
   resumen de la trayectoria y comparación con los promedios del padrón.
3. Si no existe, la herramienta responde **«Ese ID no está en el padrón»**.

Detalles útiles:

- Se aceptan los 10 dígitos con ceros a la izquierda; si escribes solo la parte
  numérica (`3781`), se completa con ceros automáticamente.
- Los espacios al principio o al final se ignoran.
- El botón **Ver un ejemplo** carga un ID real al azar para una demostración
  rápida.

## Cómo buscar por institución

1. Escribe parte del nombre en **Institución de filiación (INST_FILIA)**; el
   campo sugiere nombres mientras escribes.
2. Pulsa **Listar IDs**. Aparece el número de personas encontradas y la lista de
   códigos; la cabecera indica **cuántas instituciones** coincidieron y cuáles.
3. Haz clic en cualquier ID de la lista para abrir su ficha.

La coincidencia es por texto parcial y **no distingue mayúsculas ni tildes**.
Existe además la opción especial **«(sin institución registrada)»**.

> **Ojo con `INST_FILIA`:** en **569 de los 77 237 registros** el campo lista
> **dos** instituciones separadas por ` | ` (por ejemplo
> `UNIVERSIDAD DE LA AMAZONIA | UNIVERSIDAD INDUSTRIAL DE SANTANDER`). Por eso el
> filtro compara **institución por institución** y no el texto completo: una
> persona aparece al buscar cualquiera de sus dos afiliaciones. Una vez separadas,
> el padrón contiene 2 762 instituciones distintas (no 3 131, que es el número de
> cadenas distintas del campo original).

## Cómo buscar por área, categoría y año

Elige **gran área de conocimiento**, **categoría** y/o **convocatoria** (deja
«(cualquiera)» en los campos que no quieras restringir) y pulsa **Listar IDs**.
La herramienta devuelve las personas que cumplen **las tres condiciones a la vez**
en alguna convocatoria, con el mismo clic-para-ver-ficha.

Las listas se recortan a los primeros 300 identificadores e indican cuántos hay
en total; si la lista es muy larga, afina el filtro.

## La base está anonimizada

**No hay nombres.** El conjunto de datos publicado no incluye nombre, documento
ni ningún otro dato de identificación personal: la única clave es el código
`ID_PERSONA_PR`. Por eso **no se puede buscar por nombre** — el nombre no existe
en la fuente. La ficha muestra únicamente los atributos académicos y
demográficos agregados que publica MinCiencias.

## Advertencias sobre los datos

- **Las convocatorias no son anuales** (2013, 2014, 2015, 2017, 2019, 2021): la
  distancia real entre ellas va de 0,96 a 2,57 años.
- **Los atributos cambian entre convocatorias.** La ficha muestra el valor de
  *cada* convocatoria, no solo el último, y avisa con una etiqueta cuando algo
  cambia: la categoría cambia en 8 755 personas, el nivel de formación en 3 844,
  la gran área en 1 389, el departamento de residencia en 1 203 y el género en 42.
- **Edades fuera de rango:** 22 registros declaran más de 100 años; la ficha lo
  advierte cuando ocurre.
- La **retención de la cohorte** y los promedios por gran área se calculan sobre
  la base completa y provienen del análisis longitudinal verificado
  (`data/memoria/longitudinal_resultados.json`).

## Regenerar la herramienta

```bash
python documentacion_auditoria/src/construir_herramienta.py
```

Lee `Datos/Investigadores_Reconocidos_por_convocatoria_20261006.csv` (que no
modifica) y reescribe el HTML. El proceso es determinista.
