# -*- coding: utf-8 -*-
"""
fs_robusto.py
=============

Borrado de arboles de directorios tolerante a Windows + OneDrive.

Por que existe
--------------
Todos los scripts de `datos_originales/` borran carpetas grandes dentro de una
carpeta sincronizada con OneDrive, y ahi `shutil.rmtree` falla con frecuencia:

1. **Reparse points de solo lectura.** OneDrive (Files On-Demand) deja los
   directorios como *reparse points* con el atributo `ReadOnly`, y `rmtree` los
   rechaza con `PermissionError: [WinError 5] Acceso denegado` aunque el
   `Remove-Item -Force` de PowerShell si pueda. Se resuelve quitando el atributo
   antes de borrar.

2. **La carpeta raiz puede quedar abierta.** A veces se borran todos los
   contenidos y el `os.rmdir` final sigue fallando porque algo (la propia
   sincronizacion, un editor, una consola) mantiene un handle sobre el
   directorio. No hace falta borrar la carpeta: basta con dejarla vacia.

3. **El borrado es recursivo y de abajo arriba.** Si falla a mitad, la carpeta
   queda **INCOMPLETA** y el fallo es silencioso si nadie lo comprueba. Paso de
   verdad: se perdieron `.github/workflows/etl_update.yml`, `poetry.lock` y
   `CHANGELOG.md` de `repo_mejorado/`. Por eso estas funciones **reintentan** y,
   si no lo consiguen, **lanzan** en vez de seguir adelante con el arbol a medias.
"""

from __future__ import annotations

import os
import shutil
import stat
import time
from pathlib import Path


def quitar_solo_lectura(raiz: Path) -> None:
    """Quita el atributo ReadOnly a todo lo que cuelga de `raiz` (mejor esfuerzo)."""
    for base, dirs, ficheros in os.walk(raiz, topdown=True):
        for nombre in dirs + ficheros:
            try:
                os.chmod(os.path.join(base, nombre), stat.S_IWRITE | stat.S_IREAD)
            except OSError:
                pass


def vaciar(carpeta: Path, intentos: int = 4) -> None:
    """
    Deja `carpeta` vacia SIN borrar la carpeta misma.

    Lanza RuntimeError si no lo consigue: es preferible a continuar con un arbol a
    medias y que el problema aparezca despues, mas lejos de su causa.
    """
    for i in range(1, intentos + 1):
        quitar_solo_lectura(carpeta)
        # bottom-up: primero los archivos, despues los directorios ya vacios
        for base, dirs, ficheros in os.walk(carpeta, topdown=False):
            for nombre in ficheros:
                try:
                    (Path(base) / nombre).unlink()
                except OSError:
                    pass
            for nombre in dirs:
                try:
                    os.rmdir(Path(base) / nombre)
                except OSError:
                    pass
        resto = list(carpeta.iterdir())
        if not resto:
            return
        if i == intentos:
            raise RuntimeError(
                f"no se pudo vaciar {carpeta} tras {intentos} intentos: quedan "
                f"{len(resto)} entradas (p. ej. {resto[:3]}). Cierra lo que lo "
                f"tenga abierto (OneDrive, un editor, una consola) y reintenta: "
                f"la carpeta puede haber quedado INCOMPLETA."
            )
        print(f"  [reintento {i}/{intentos - 1}] quedan {len(resto)} entradas")
        time.sleep(1.5 * i)


def borrar_arbol(carpeta: Path, intentos: int = 4) -> None:
    """
    Borra `carpeta` si puede y, si no, la deja vacia.

    No falla por no poder eliminar la propia carpeta: lo que importa es que no
    quede contenido. Si tampoco se puede vaciar, lanza.
    """
    if not carpeta.exists():
        return
    for i in range(1, intentos + 1):
        try:
            quitar_solo_lectura(carpeta)
            shutil.rmtree(carpeta)
            return
        except OSError as exc:
            if i == intentos:
                print(f"  [aviso] no se pudo borrar {carpeta.name} "
                      f"({type(exc).__name__}); se vacia en su lugar")
                break
            time.sleep(1.0 * i)
    vaciar(carpeta)
