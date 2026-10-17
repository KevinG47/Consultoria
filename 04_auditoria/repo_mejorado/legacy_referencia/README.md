# `legacy_referencia/` — material academico apartado

Los **13 archivos** de las tareas academicas previas (`notebooks/tarea_*`) que las
51 fichas de auditoria marcan como **NO ejecutables** y con recomendacion
explicita de **"no migrar"**.

## Por que no son ejecutables

| Causa | Archivos |
|---|---|
| Rutas de Colab (`/content/...`) que no existen fuera de Colab | 6 |
| `!pip install` y `display()`: magias de notebook, no Python valido | 3 |
| Rutas de `Downloads/*.xlsx` locales del autor | 4 |
| Variables usadas sin definirse en el propio archivo | 3 |

## Por que se conservan (y no se borran)

Son **referencia metodologica** de valor: k-prototypes para datos mixtos,
analisis de correspondencias (CA/MCA/FAMD), el proceso de join y de deduplicacion,
y los primeros EDA por convocatoria (donde esta documentado el hallazgo del
outlier de edad de 956 anios). Ademas son la evidencia de la capa `legacy` del
repositorio que la auditoria clasifica.

## Por que se apartan del arbol de trabajo

Su logica **ya esta reimplementada** en el pipeline moderno —`src/ingesta/`,
`src/analisis/` y `src/modelo/`— con tipos correctos y validacion. Dejarlas
mezcladas con el codigo que si funciona hace que quien llega pierda el tiempo
intentando ejecutarlas (y creyendo que el proyecto esta roto). Aqui estan, fuera
del camino, sin perder nada.

Se conserva la **ruta relativa original** de cada una: `legacy_referencia/notebooks/
tarea_gran_tabla/analisis2.ipynb` es el antiguo `notebooks/tarea_gran_tabla/analisis2.ipynb`.

## Nota sobre la sintaxis

Estos archivos **no son Python valido** a proposito: contienen `!pip install` y
`display()` de Colab/IPython. Por eso `verificar_arreglos.py` los excluye del
chequeo de sintaxis y por eso no se ejecutan.
