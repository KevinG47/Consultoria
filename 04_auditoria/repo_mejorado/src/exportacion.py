"""
exportacion.py
==============

Exportacion de figuras a PNG tolerando que el motor de imagen no este disponible.

`plotly` genera el HTML por si mismo, pero para exportar un PNG necesita un motor
externo: `kaleido`. Y desde kaleido 1.x ese motor tampoco dibuja por su cuenta:
maneja un navegador Chromium real a traves de `choreographer`. Eso da DOS formas
distintas de fallar, con excepciones de modulos distintos:

1. kaleido no instalado -> RuntimeError/ValueError cuyo mensaje menciona "kaleido".
2. kaleido instalado pero **el navegador no arranca** ->
   `choreographer.browsers._errors.BrowserFailedError` (subclase de RuntimeError)
   cuyo mensaje NO menciona "kaleido": dice "The browser seemed to close
   immediately after starting".

La primera version de este modulo solo miraba el mensaje, asi que el caso 2 se le
escapaba y el script moria igual. Se descubrio al probar con las LIBRERIAS REALES:
los dobles de prueba no podian reproducirlo. Por eso ahora se mira tambien el
MODULO de la clase de la excepcion, que es estable entre versiones.

En ambos casos la exportacion a PNG es *best-effort*: se avisa con la instruccion
concreta y se continua, porque el HTML y los CSV ya estan generados y siguen siendo
utiles. Cualquier otro error se propaga tal cual.
"""

from __future__ import annotations

from pathlib import Path

# Modulos raiz que identifican al motor de imagenes y a su gestor de navegador.
MODULOS_MOTOR = frozenset({"kaleido", "choreographer"})


def exportar_png(fig, ruta, **kwargs) -> bool:
    """
    Exporta `fig` a PNG. Devuelve True si lo consiguio y False si el motor de
    imagen no esta disponible (kaleido ausente o navegador que no arranca).

    En el segundo caso imprime un aviso accionable y NO interrumpe el script.
    """
    try:
        fig.write_image(ruta, **kwargs)
        return True
    except Exception as exc:                                    # noqa: BLE001
        if not es_fallo_del_motor(exc):
            raise
        _avisar(ruta, exc)
        return False


def es_fallo_del_motor(exc: BaseException) -> bool:
    """
    True si la excepcion viene del motor de imagenes.

    Se recorre la jerarquia de la clase y se mira su MODULO, no el texto: asi se
    reconoce `BrowserFailedError` (de `choreographer`), que por mensaje es
    indistinguible de cualquier otro RuntimeError.
    """
    for cls in type(exc).__mro__:
        if (cls.__module__ or "").split(".")[0] in MODULOS_MOTOR:
            return True
    return "kaleido" in str(exc).lower()


def _es_fallo_de_navegador(exc: BaseException) -> bool:
    """True cuando kaleido esta presente pero no logra arrancar el navegador."""
    return any((cls.__module__ or "").split(".")[0] == "choreographer"
               for cls in type(exc).__mro__)


def _avisar(ruta, exc) -> None:
    detalle = str(exc).splitlines()[0][:140] if str(exc) else type(exc).__name__
    print(f"      [aviso] no se pudo escribir {Path(ruta).name}")
    if _es_fallo_de_navegador(exc):
        print("              motivo: kaleido esta instalado, pero el navegador con el")
        print("              que dibuja no arranca.")
        print("              opciones, de menos a mas esfuerzo:")
        print("                1) seguir sin el PNG: el HTML ya se genero y sirve")
        print("                   para ver el grafico;")
        print("                2) usar un navegador ya instalado:")
        print("                   set BROWSER_PATH=C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
        print("                3) instalar el navegador propio de kaleido (requiere red):")
        print("                   kaleido_get_chrome")
    else:
        print('              motivo: falta kaleido. Instalalo con:  pip install "kaleido>=1"')
    print(f"              detalle: {type(exc).__name__}: {detalle}")
    print("              el HTML SI se genero; solo falta la imagen.")
