"""Revisa el README de la raiz: estructura, bloques y referencias a archivos.

Comprueba:
  1. Encabezados en orden y sin saltos de nivel.
  2. Bloques de codigo balanceados (```).
  3. Tablas markdown con el numero de columnas coherente.
  4. Rutas citadas en `code spans` y enlaces: que existan en disco.
  5. Enlaces internos (#ancla) contra las anclas reales del documento.

Uso: python _archivo/scripts_oneoff/revisar_readme.py [ruta]
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "README.md"

# La consola de Windows es cp1252 y el README trae "▶" y "─": sin esto el propio
# revisor muere con UnicodeEncodeError (el mismo defecto que describe el arreglo B
# del CHANGELOG en los scripts del proyecto auditado).
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

texto = RUTA.read_text(encoding="utf-8")
lineas = texto.splitlines()

print(f"archivo: {RUTA.relative_to(RAIZ)}  ({len(lineas)} lineas, {len(texto)} bytes)")

# ---------------------------------------------------------------- 1. encabezados
print("\n=== 1. estructura de encabezados ===")
encabezados = []
dentro_bloque = False
for i, l in enumerate(lineas, 1):
    if l.strip().startswith("```"):
        dentro_bloque = not dentro_bloque
        continue
    if dentro_bloque:
        continue
    m = re.match(r"^(#{1,6})\s+(.*)$", l)
    if m:
        encabezados.append((i, len(m.group(1)), m.group(2).strip()))

previo = 0
saltos = []
for num, nivel, titulo in encabezados:
    marca = ""
    if previo and nivel > previo + 1:
        marca = "  <-- SALTO DE NIVEL"
        saltos.append((num, titulo))
    print(f"  {num:>4}  {'#' * nivel:<6} {titulo}{marca}")
    previo = nivel

print("\n=== 2. bloques de codigo ===")
cercas = [i for i, l in enumerate(lineas, 1) if l.strip().startswith("```")]
print(f"  cercas ```: {len(cercas)}  ->  {'BALANCEADAS' if len(cercas) % 2 == 0 else 'IMPAR: HAY UN BLOQUE SIN CERRAR'}")

print("\n=== 3. tablas markdown ===")
i = 0
tablas = 0
problemas_tabla = []
while i < len(lineas):
    if lineas[i].strip().startswith("|") and i + 1 < len(lineas) and set(lineas[i + 1].strip()) <= set("|-: "):
        cabecera = lineas[i].count("|")
        j = i + 2
        filas = 0
        while j < len(lineas) and lineas[j].strip().startswith("|"):
            if lineas[j].count("|") != cabecera:
                problemas_tabla.append(
                    f"linea {j + 1}: {lineas[j].count('|')} pipes, la cabecera tiene {cabecera}")
            filas += 1
            j += 1
        tablas += 1
        print(f"  linea {i + 1:>4}: tabla de {filas} filas, {cabecera} pipes")
        i = j
    else:
        i += 1
if problemas_tabla:
    print("  PROBLEMAS:")
    for p in problemas_tabla:
        print(f"    {p}")
else:
    print("  todas las filas coinciden con su cabecera")

# ------------------------------------------------------------- 4. rutas citadas
print("\n=== 4. rutas citadas que NO existen ===")
candidatas: set[str] = set()
for m in re.finditer(r"`([^`]+)`", texto):
    valor = m.group(1).strip()
    if re.fullmatch(r"[\w./\-]+\.(py|md|yaml|yml|csv|json|lock|toml|txt|ipynb|html|tex|pdf|npz|pkl|jsonl|xlsx|R)", valor):
        candidatas.add(valor)
    elif re.fullmatch(r"[\w\-]+/", valor):
        candidatas.add(valor)
for m in re.finditer(r"\]\(([^)#][^)]*)\)", texto):
    destino = m.group(1).strip()
    if not destino.startswith(("http://", "https://", "mailto:")):
        candidatas.add(destino.rstrip("/") + ("/" if destino.endswith("/") else ""))

faltan = []
for ruta in sorted(candidatas):
    limpio = ruta.rstrip("/")
    if (RAIZ / limpio).exists():
        continue
    # Tambien se aceptan nombres sueltos que existan en cualquier parte.
    if any(RAIZ.rglob(Path(limpio).name)):
        continue
    faltan.append(ruta)

if not faltan:
    print(f"  las {len(candidatas)} rutas citadas existen")
else:
    print(f"  {len(faltan)} de {len(candidatas)} rutas citadas NO se encuentran:")
    for f in faltan:
        print(f"    {f}")

# ------------------------------------------------------------ 5. enlaces internos
print("\n=== 5. enlaces internos (#ancla) ===")


def ancla(titulo: str) -> str:
    t = unicodedata.normalize("NFKD", titulo.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s\-]", "", t)
    return re.sub(r"\s+", "-", t.strip())


anclas = {ancla(t) for _, _, t in encabezados}
internos = re.findall(r"\]\(#([^)]+)\)", texto)
if not internos:
    print("  no hay enlaces internos")
for a in internos:
    print(f"  #{a}  ->  {'OK' if a in anclas else 'ROTO'}")

print("\n=== resumen ===")
print(f"  encabezados: {len(encabezados)}  ({len(saltos)} saltos de nivel)")
print(f"  tablas: {tablas}  ({len(problemas_tabla)} filas descuadradas)")
print(f"  rutas inexistentes: {len(faltan)}")
print(f"  enlaces internos rotos: {sum(1 for a in internos if a not in anclas)}")
