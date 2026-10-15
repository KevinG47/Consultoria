"""Compara el poetry.lock auditado con el del repo mejorado.

Responde, con cifras verificables, a la pregunta: el lock nuevo
¿pesa mas, tiene mas paquetes, y tiene versiones mas modernas?

Uso (desde la raiz del repo):
    python _archivo/scripts_oneoff/comparar_locks.py
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AUDITADO = RAIZ / "datos_originales" / "repo_auditado" / "poetry.lock"
MEJORADO = RAIZ / "datos_originales" / "repo_mejorado" / "poetry.lock"


def cargar(ruta: Path) -> dict[str, str]:
    """Devuelve {nombre: version} de los paquetes del lock."""
    datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
    return {p["name"]: p["version"] for p in datos.get("package", [])}


def tupla(v: str) -> tuple:
    """Version -> tupla comparable. Ignora sufijos no numericos."""
    partes = re.findall(r"\d+", v)
    return tuple(int(x) for x in partes) if partes else (0,)


def main() -> int:
    viejo = cargar(AUDITADO)
    nuevo = cargar(MEJORADO)

    print("=" * 72)
    print("PESO Y TAMANO")
    print("=" * 72)
    for etiqueta, ruta in (("anterior", AUDITADO), ("nuevo   ", MEJORADO)):
        print(f"  {etiqueta}: {ruta.stat().st_size:>9,d} B  ({ruta.stat().st_size/1024:.1f} KB)  lineas={len(ruta.read_text(encoding='utf-8').splitlines()):,d}")
    dif = MEJORADO.stat().st_size - AUDITADO.stat().st_size
    print(f"  diferencia: {dif:+,d} B  ({dif/AUDITADO.stat().st_size*100:+.1f} %)")

    print()
    print("=" * 72)
    print("NUMERO DE PAQUETES")
    print("=" * 72)
    print(f"  anterior: {len(viejo)}")
    print(f"  nuevo   : {len(nuevo)}")
    print(f"  diferencia: {len(nuevo)-len(viejo):+d}")

    solo_viejo = sorted(set(viejo) - set(nuevo))
    solo_nuevo = sorted(set(nuevo) - set(viejo))
    comunes = sorted(set(viejo) & set(nuevo))

    print()
    print("=" * 72)
    print(f"VERSIONES DE LOS {len(comunes)} PAQUETES COMUNES")
    print("=" * 72)
    mas_nuevos, mas_viejos, iguales = [], [], []
    for nombre in comunes:
        v, n = viejo[nombre], nuevo[nombre]
        if tupla(n) > tupla(v):
            mas_nuevos.append((nombre, v, n))
        elif tupla(n) < tupla(v):
            mas_viejos.append((nombre, v, n))
        else:
            iguales.append((nombre, v))

    print(f"  mas modernos : {len(mas_nuevos)}")
    print(f"  mas antiguos : {len(mas_viejos)}")
    print(f"  identicos    : {len(iguales)}")
    print()
    if mas_nuevos:
        print("  -- Subieron de version --")
        for nombre, v, n in mas_nuevos:
            print(f"     {nombre:<24} {v:<12} -> {n}")
    if mas_viejos:
        print("  -- Bajaron de version --")
        for nombre, v, n in mas_viejos:
            print(f"     {nombre:<24} {v:<12} -> {n}")

    print()
    print("=" * 72)
    print("PAQUETES EXCLUSIVOS")
    print("=" * 72)
    print(f"  solo en el anterior ({len(solo_viejo)}):")
    for nombre in solo_viejo:
        print(f"     {nombre:<24} {viejo[nombre]}")
    print(f"  solo en el nuevo ({len(solo_nuevo)}):")
    for nombre in solo_nuevo:
        print(f"     {nombre:<24} {nuevo[nombre]}")

    print()
    print("=" * 72)
    print("LAS 5 DEPENDENCIAS ANADIDAS EN pyproject.toml")
    print("=" * 72)
    for nombre in ("openpyxl", "pyyaml", "kaleido", "nbformat", "ipython"):
        piezas = [k for k in nuevo if k.lower() == nombre]
        if not piezas:
            print(f"  {nombre:<12} NO ESTA EN EL LOCK  <-- problema")
            continue
        k = piezas[0]
        antes = viejo.get(k, "")
        print(f"  {nombre:<12} {nuevo[k]:<12} (antes: {antes or 'no estaba'})")

    print()
    print("=" * 72)
    print("VERSIONES CLAVE: LOCK vs ENTORNO INSTALADO (pip)")
    print("=" * 72)
    import importlib.metadata as md

    for nombre in ("pandas", "numpy", "plotly", "kaleido", "duckdb", "seaborn", "matplotlib", "streamlit", "scikit-learn", "openpyxl", "PyYAML", "nbformat", "ipython"):
        clave = nombre.lower()
        en_lock = nuevo.get(clave) or viejo.get(clave) or "-"
        try:
            en_entorno = md.version(nombre)
        except md.PackageNotFoundError:
            en_entorno = "NO INSTALADO"
        marca = ""
        if en_entorno not in ("NO INSTALADO", "-") and en_lock != en_entorno:
            marca = "   <-- DIFIERE"
        print(f"  {nombre:<14} lock={en_lock:<12} entorno={en_entorno}{marca}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
