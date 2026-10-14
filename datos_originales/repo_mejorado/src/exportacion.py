"""
exportacion.py
==============

Exportacion de figuras a PNG tolerando la ausencia del motor de imagen.

`plotly` genera el HTML por si mismo, pero para exportar un PNG necesita
`kaleido`. Sin kaleido, `fig.write_image(...)` lanza RuntimeError (o ValueError,
segun la version) y el script abortaba DESPUES de haber generado el HTML, de modo
que se perdia el resto del trabajo y el fallo parecia un bug del script.

Aqui la exportacion a PNG es *best-effort*: si falta el motor se avisa con el
comando exacto para instalarlo y se continua con el resto de las salidas. Solo se
absorben los fallos relacionados con kaleido; cualquier otro error se propaga.
"""

from __future__ import annotations

from pathlib import Path

MENSAJE = ('falta kaleido, el motor de exportacion de imagenes de plotly. '
           'Instalalo con:  pip install "kaleido>=1"')


def exportar_png(fig, ruta, **kwargs) -> bool:
    """
    Exporta `fig` a PNG. Devuelve True si lo consiguio y False si falta kaleido.

    En el segundo caso imprime un aviso accionable y NO interrumpe el script: el
    HTML ya esta generado y las demas salidas siguen siendo utiles.
    """
    try:
        fig.write_image(ruta, **kwargs)
        return True
    except (ImportError, ModuleNotFoundError) as exc:
        _avisar(ruta, exc)
        return False
    except (RuntimeError, ValueError) as exc:
        # plotly senala la ausencia del motor con RuntimeError o ValueError; si el
        # mensaje no menciona kaleido es otro problema y debe verse tal cual.
        if "kaleido" not in str(exc).lower():
            raise
        _avisar(ruta, exc)
        return False


def _avisar(ruta, exc) -> None:
    detalle = str(exc).splitlines()[0][:140] if str(exc) else type(exc).__name__
    print(f"      [aviso] no se pudo escribir {Path(ruta).name}: {MENSAJE}")
    print(f"              detalle: {type(exc).__name__}: {detalle}")
    print("              el HTML SI se genero; solo falta la imagen.")
