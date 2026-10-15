"""Extrae ruedas de la cache de pip directamente a una carpeta, sin pip.

Una rueda .whl es un ZIP: extraerlo en una carpeta y ponerla en PYTHONPATH basta
para importar el paquete. Se evita asi el problema de reconstruir el nombre de
archivo que pip exige.

Uso:
    python _archivo/scripts_oneoff/extraer_ruedas.py <destino> pkg1 pkg2 ...
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

CACHE = Path.home() / "AppData" / "Local" / "pip" / "cache"


def prefijo_de(z: zipfile.ZipFile) -> str | None:
    for n in z.namelist():
        if n.endswith(".dist-info/METADATA"):
            return n[: -len("/METADATA")]
    return None


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    destino = Path(sys.argv[1]).resolve()
    pedidos = [p.lower().replace("-", "_") for p in sys.argv[2:]]
    destino.mkdir(parents=True, exist_ok=True)

    puestos: dict[str, str] = {}
    for ruta in sorted(CACHE.glob("http-v2/**/*.body")):
        try:
            with zipfile.ZipFile(ruta) as z:
                prefijo = prefijo_de(z)
                if not prefijo:
                    continue
                paquete = prefijo.rsplit(".dist-info", 1)[0]
                canon = paquete.lower().replace("-", "_")
                # canon es "pytest_9.1.1" o "pytest-9.1.1": comparar por prefijo
                objetivo = next(
                    (p for p in pedidos
                     if canon == p or canon.startswith(p + "_") or canon.startswith(p + "-")),
                    None,
                )
                if objetivo is None:
                    continue
                # Que version es: la ultima pieza con digitos
                z.extractall(destino)
                puestos[objetivo] = prefijo
        except (zipfile.BadZipFile, OSError):
            continue

    print(f"extraidas en {destino}:")
    for p, prefijo in sorted(puestos.items()):
        print(f"   {p:<16} {prefijo}")
    faltan = [p for p in pedidos if p not in puestos]
    if faltan:
        print(f"\nNO estaban en la cache: {', '.join(faltan)}")
    return 0 if not faltan else 1


if __name__ == "__main__":
    raise SystemExit(main())
