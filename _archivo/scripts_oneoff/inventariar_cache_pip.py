"""Inventaria las ruedas recuperables de la cache HTTP de pip.

pip guarda los cuerpos de respuesta en `http-v2/**/*.body` con nombre
hasheado. Muchos son ruedas .whl intactas: se pueden identificar abriendo el
ZIP y leyendo `<pkg>-<ver>.dist-info/WHEEL`.

Uso:
    python _archivo/scripts_oneoff/inventariar_cache_pip.py
    python _archivo/scripts_oneoff/inventariar_cache_pip.py <salida.json>
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

CACHE = Path.home() / "AppData" / "Local" / "pip" / "cache"


def leer_rueda(ruta: Path) -> dict | None:
    """Devuelve los datos de la rueda o None si no es una rueda valida."""
    try:
        with zipfile.ZipFile(ruta) as z:
            dist_info = next(
                (n for n in z.namelist() if n.endswith(".dist-info/WHEEL")), None
            )
            if not dist_info:
                return None
            prefijo = dist_info[: -len("/WHEEL")]
            meta = next(
                (n for n in z.namelist() if n == f"{prefijo}/METADATA"), None
            )
            nombre_version = prefijo[: -len(".dist-info")]
            wheel_txt = z.read(dist_info).decode("utf-8", "replace")
            etiquetas = [
                l.split(":", 1)[1].strip()
                for l in wheel_txt.splitlines()
                if l.lower().startswith("tag:")
            ]
            uses_purelib = "Root-Is-Purelib: true" in wheel_txt
            return {
                "prefijo": nombre_version,
                "etiquetas": etiquetas,
                "pura": uses_purelib,
                "tiene_metadata": meta is not None,
                "bytes": ruta.stat().st_size,
                "origen": str(ruta),
            }
    except (zipfile.BadZipFile, OSError):
        return None


def main() -> int:
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    cuerpos = sorted(CACHE.glob("http-v2/**/*.body"))
    print(f"cuerpos en cache: {len(cuerpos)}")

    ruedas: dict[str, dict] = {}
    otras = 0
    for ruta in cuerpos:
        info = leer_rueda(ruta)
        if not info:
            otras += 1
            continue
        clave = info["prefijo"]
        # Si hay varias copias, conservar la de mayor tamano.
        if clave not in ruedas or info["bytes"] > ruedas[clave]["bytes"]:
            ruedas[clave] = info

    print(f"cuerpos que NO son ruedas: {otras}")
    print(f"ruedas distintas identificadas: {len(ruedas)}")

    en_wheels = CACHE / "wheels"
    if en_wheels.exists():
        print(f"\nruedas construidas por pip en wheels/: "
              f"{len(list(en_wheels.rglob('*.whl')))}")
        for w in en_wheels.rglob("*.whl"):
            print(f"   {w.name}  {w.stat().st_size:,d} B")

    buscadas = ["scikit_learn", "sklearn", "pytest", "pandera", "pyvis", "sodapy",
                "nbclient", "nbconvert", "jupyter_client", "jupyter_core",
                "ipykernel", "jupyter", "notebook", "sodapy", "duckdb"]
    print("\n--- paquetes de interes ---")
    for b in buscadas:
        halladas = [k for k in ruedas if k.lower().startswith(b.lower() + "-")]
        if halladas:
            for h in halladas:
                print(f"   {h:<34} {ruedas[h]['bytes']:>12,d} B  etiquetas={ruedas[h]['etiquetas']}")
        else:
            print(f"   {b:<34} NO ESTA EN LA CACHE")

    if salida:
        salida.write_text(json.dumps(ruedas, indent=2, ensure_ascii=False),
                          encoding="utf-8")
        print(f"\ninventario escrito en {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
