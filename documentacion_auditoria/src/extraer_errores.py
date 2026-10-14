# -*- coding: utf-8 -*-
"""
extraer_errores.py
==================

Extrae el traceback (últimas líneas de cada cuerpo) de los scripts del pipeline
auditado que fallaron, y lo escribe en un archivo de texto legible. Es la
evidencia de los 6 ERROR documentados en `latex/maestro_auditoria` y en
`data/ejecucion_resumen.csv`.

QUÉ SE CORRIGIÓ
---------------
1. **Ruta rota.** Apuntaba por defecto a
   `.\documentacion_auditoria\data\ejecucion_log.txt`, que no existe
   (`Test-Path` = False), tanto para la entrada como para la salida. Ahora las
   rutas se resuelven con `Path(__file__)` y apuntan al log real de `_archivo/`.
2. **Lista de fallos hardcodeada.** Antes había 6 nombres escritos a mano, así
   que el script quedaba obsoleto en cuanto cambiara la corrida. Ahora la lista
   se DERIVA del propio log (todo script con `EXIT != 0`), con `--scripts` para
   forzar un subconjunto.
3. **Codificación mixta.** El log mezcla UTF-8 (cabecera) y UTF-16LE (cuerpos);
   leído como UTF-8 no se recupera ningún cuerpo. Se decodifica de las dos formas
   y se elige la que encuentra más marcadores `EXIT=`.
4. **Sin estructura.** Ahora tiene `main()`, argparse y gestión de errores; antes
   era código suelto en el nivel de módulo.

Uso
---
    python documentacion_auditoria/src/extraer_errores.py
    python documentacion_auditoria/src/extraer_errores.py --lineas 8
    python documentacion_auditoria/src/extraer_errores.py --scripts sprint5_produccion.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
LOG_POR_DEFECTO = RAIZ / "_archivo" / "logs_pipeline_auditado" / "ejecucion_log.txt"
SALIDA_POR_DEFECTO = RAIZ / "_archivo" / "logs_pipeline_auditado" / "errores_ejecucion.txt"

# Un bloque por script: desde el separador hasta el siguiente (o el final).
BLOQUE = re.compile(r"=== (sprint\w+\.py) ===(.*?)(?==== (?:sprint\w+\.py) ===|\Z)", re.S)
EXIT = re.compile(r"EXIT=(-?\d+)")
# Línea marcadora del pipeline: 'EXIT=1 TIEMPO=49.7s'
MARCADOR = re.compile(r"^EXIT=-?\d+\s+TIEMPO=")


def leer_texto(ruta: Path) -> str:
    b = ruta.read_bytes()
    t8 = b.decode("utf-8", errors="replace")
    t16 = b.decode("utf-16-le", errors="replace")
    return t16 if t16.count("EXIT=") > t8.count("EXIT=") else t8


def bloques(txt: str) -> dict[str, tuple[str, int]]:
    """{script: (cuerpo, exit)} de todos los scripts del log."""
    out = {}
    for nombre, cuerpo in BLOQUE.findall(txt):
        m = EXIT.search(cuerpo)
        out[nombre] = (cuerpo, int(m.group(1)) if m else 0)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Extrae los tracebacks de los scripts que fallaron.")
    ap.add_argument("--log", default=str(LOG_POR_DEFECTO))
    ap.add_argument("--salida", default=str(SALIDA_POR_DEFECTO))
    ap.add_argument("--lineas", type=int, default=6,
                    help="líneas finales del cuerpo a conservar (por defecto 6)")
    ap.add_argument("--scripts", default="",
                    help="lista separada por comas; por defecto, todos los que fallaron")
    args = ap.parse_args()

    log, salida = Path(args.log), Path(args.salida)
    if not log.exists():
        print(f"[x] No existe el log: {log}")
        return 1

    todos = bloques(leer_texto(log))
    if not todos:
        print(f"[x] El log {log.name} no contiene bloques de script reconocibles.")
        return 1

    if args.scripts:
        fallidos = [s.strip() for s in args.scripts.split(",") if s.strip()]
    else:
        # La lista se DERIVA del log: nada hardcodeado.
        fallidos = [n for n, (_, code) in todos.items() if code != 0]

    out = [f"# Errores de ejecución del pipeline auditado",
           f"# Fuente: {log.relative_to(RAIZ) if log.is_relative_to(RAIZ) else log}",
           f"# Scripts con EXIT != 0 en el log: {len(fallidos)} de {len(todos)}",
           ""]
    for s in fallidos:
        if s not in todos:
            out += [f"### {s}: no encontrado en el log", ""]
            continue
        cuerpo, code = todos[s]
        # Se descarta la línea marcadora 'EXIT=.. TIEMPO=..s': es metadato del
        # pipeline, no parte del error, y ocupaba uno de los renglones que se
        # conservan, desplazando el inicio del traceback.
        crudas = [l.strip() for l in cuerpo.splitlines() if l.strip()]
        lineas = [l for l in crudas if not MARCADOR.match(l)]
        out.append(f"### {s}  (EXIT={code})")
        # las últimas líneas son las que suelen contener el traceback
        for l in (lineas[-args.lineas:] if args.lineas else lineas):
            out.append("   " + l[:200])
        out.append("")

    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text("\n".join(out), encoding="utf-8")
    print(f"log    : {log.name}  ({len(todos)} scripts, {len(fallidos)} con EXIT != 0)")
    print(f"escrito: {salida.relative_to(RAIZ) if salida.is_relative_to(RAIZ) else salida}")
    print(f"         {len(out)} líneas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
