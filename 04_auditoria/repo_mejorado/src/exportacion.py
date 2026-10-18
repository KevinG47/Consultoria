"""
exportacion.py
==============

Exportacion de figuras a PNG sin navegador.

`plotly` genera el HTML por si mismo, pero NO dibuja un PNG por su cuenta: para
escribir una imagen necesita un motor aparte. Hasta la version anterior este
modulo usaba `kaleido`, y desde kaleido 1.x ese motor tampoco dibuja: maneja un
Chromium real a traves de `choreographer`. Eso ataba la exportacion a que
arrancase un navegador, algo que no ocurre ni en un contenedor sin Chrome ni en
cualquier entorno donde no se puedan crear tuberias nombradas o procesos hijos;
ahi `write_image()` muere con `BrowserFailedError` ("The browser seemed to close
immediately after starting"), una excepcion que ni siquiera menciona la palabra
"kaleido".

Ahora el motor es **`plotly-mirage`** (se importa como `mirage`): rasteriza el
SVG de Plotly en el propio proceso con `quickjs` + `resvg`, sin navegador. La
exportacion a PNG sigue siendo *best-effort*: si el motor no esta instalado, o no
sabe dibujar una figura concreta, se avisa con la instruccion exacta y se
continua, porque el HTML y los CSV ya estan generados y siguen siendo utiles.
Cualquier otro error se propaga tal cual.

Compatibilidad con mirage 0.2.0, comprobada aqui (no supuesta):

* `write_image()` acepta una ruta `str` o un objeto archivo, pero **no** acepta
  `pathlib.Path`: con un `Path` revienta con
  `AttributeError: 'WindowsPath' object has no attribute 'write'` dentro de su
  `raster.py`. Como los scripts de este repositorio pasan
  `ARTIFACTS / "sankey.png"` (un `Path`), aqui se normaliza a `str` antes de
  llamar al motor. Ese `AttributeError` no lleva la firma del motor, asi que sin
  la normalizacion se propagaria y tumbaria el script.
* Limite del motor, medido: dibuja `sankey`, `bar` con eje categorico, `heatmap`,
  `pie`, `treemap` y `choropleth`; en cambio puede abortar con
  `JSException: Plotly render failed: out-of-bound numeric index` en `scatter`
  con ejes continuos (con 3 puntos aleatorios dibujo y con 5 fallo; con ejes
  enteros no fallo hasta 2.000 puntos), y no soporta las trazas WebGL
  (`scattergl`). Por eso el fallo del motor se absorbe: los dos PNG que genera
  este repositorio son sankey, que si se dibujan. Quien necesite otro tipo de
  imagen vera el aviso en la consola y conservara el HTML, que sirve para mirar
  el grafico.

`activar_mirage()` es para los scripts que llamen a `fig.write_image()` sin pasar
por `exportar_png()`: parchea las funciones de exportacion estaticas de Plotly
para que las atienda mirage.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import mirage
except ImportError:                                  # el aviso se da al exportar
    mirage = None

# Modulos raiz que identifican al motor de imagenes y a su interprete JS.
MODULOS_MOTOR = frozenset({"mirage", "_quickjs", "quickjs", "resvg"})

_parcheado = False


def activar_mirage() -> bool:
    """
    Hace que `fig.write_image()`, `fig.to_image()`, `plotly.io.write_image()` y
    `plotly.io.to_image()` los atienda mirage, sin navegador.

    Devuelve True si el parcheo quedo activo y False si mirage no esta instalado.
    Es idempotente: llamarlo dos veces no tiene efectos adicionales.
    """
    global _parcheado
    if mirage is None:
        print('      [aviso] falta el motor de imagen. Instalalo con:  '
              'pip install "plotly-mirage>=0.2"')
        return False
    if not _parcheado:
        mirage.patch_plotly()
        _parcheado = True
    return True


def _ruta_para_mirage(ruta):
    """
    Normaliza la ruta a `str`, que es lo que acepta `mirage.write_image`.

    Se deja pasar tal cual cualquier objeto que no sea una ruta (`Path` es
    `os.PathLike`): los objetos archivo tambien funcionan en el motor.
    """
    if isinstance(ruta, os.PathLike):
        return os.fspath(ruta)
    return ruta


def exportar_png(fig, ruta, **kwargs) -> bool:
    """
    Exporta `fig` a PNG con mirage. Devuelve True si lo consiguio y False si el
    motor no esta disponible (sin instalar, o sin saber dibujar esta figura).

    En el segundo caso imprime un aviso accionable y NO interrumpe el script.
    Acepta `ruta` como `str`, `Path` o archivo abierto.
    """
    if mirage is None:
        _avisar_sin_motor(ruta)
        return False
    try:
        mirage.write_image(fig, _ruta_para_mirage(ruta), **kwargs)
        return True
    except Exception as exc:                                    # noqa: BLE001
        if not es_fallo_del_motor(exc):
            raise
        _avisar(ruta, exc)
        return False


def es_fallo_del_motor(exc: BaseException) -> bool:
    """
    True si la excepcion viene del motor de imagenes.

    Se recorre la jerarquia de la clase y se mira su MODULO, no el texto: los
    fallos de render de mirage salen como `_quickjs.JSException`, cuyo mensaje
    habla de Plotly y no del motor. Mirar solo el texto dejaria escapar el caso,
    que es el defecto que se corrigio en la version anterior de este modulo.
    """
    for cls in type(exc).__mro__:
        if (cls.__module__ or "").split(".")[0] in MODULOS_MOTOR:
            return True
    texto = str(exc).lower()
    return "mirage" in texto or "plotly render failed" in texto


def _avisar_sin_motor(ruta) -> None:
    print(f"      [aviso] no se pudo escribir {Path(ruta).name}")
    print("              motivo: falta el motor de imagen plotly-mirage.")
    print('              instalalo con:  pip install "plotly-mirage>=0.2"')
    print("              el HTML SI se genero; solo falta la imagen.")


def _avisar(ruta, exc) -> None:
    detalle = str(exc).splitlines()[0][:140] if str(exc) else type(exc).__name__
    print(f"      [aviso] no se pudo escribir {Path(ruta).name}")
    print("              motivo: mirage esta instalado, pero no logro dibujar esta")
    print("              figura (no hay navegador implicado: el fallo es del motor).")
    print("              tipos que mirage 0.2.0 SI dibuja, comprobados aqui:")
    print("              sankey, bar con eje categorico, heatmap, pie, treemap,")
    print("              choropleth. Los que pueden fallar: scatter con ejes")
    print("              continuos y cualquier traza WebGL (scattergl). Para esos")
    print("              casos, el HTML sirve para ver el grafico.")
    print(f"              detalle: {type(exc).__name__}: {detalle}")
    print("              el HTML SI se genero; solo falta la imagen.")
