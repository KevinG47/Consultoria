# -*- coding: utf-8 -*-
"""
cierre_librerias_reales.py
==========================

Cierre de la tarea de verificacion con librerias reales:

1. Borra los scripts de parche mecanicos de `_archivo/scripts_oneoff/`: su efecto
   ya esta en los archivos definitivos y documentado en el CHANGELOG. Se conservan
   los de DIAGNOSTICO (kaleido, lock, fichas), que sirven para volver a mirar.
2. Anade al README de `datos_originales/` los dos scripts nuevos de esta tarea.
"""

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
D = RAIZ / "datos_originales"
ONE = RAIZ / "_archivo" / "scripts_oneoff"

# 1. fuera los parches mecanicos (se conservan los diagnosticos)
MECANICOS = ["parche_fs_robusto.py", "parche_mkdir_stubs.py",
             "parche_resumen_dinamico.py", "parche_copytree.py"]
for nombre in MECANICOS:
    f = ONE / nombre
    if f.exists():
        f.unlink()
        print(f"  [borrado] _archivo/scripts_oneoff/{nombre}")
print("  [conservados] inspeccionar_lock.py, kaleido_navegador.py, "
      "probar_kaleido_browser.py (diagnostico)")

# 2. README: filas de los scripts nuevos
p = D / "README.md"
t = p.read_text(encoding="utf-8")
ancla = ("| `verificar_arreglos.py` | 1 | — | Verifica los arreglos "
         "(6 niveles de comprobación) |")
nuevas = ancla + "\n" + "\n".join([
    "| `probar_librerias_reales.py` | 1 | — | Ejecuta los 6 scripts con las "
    "librerías de verdad y comprueba qué salidas se regeneran |",
    "| `fs_robusto.py` | 1 | — | Borrado de árboles tolerante a OneDrive "
    "(reparse points de solo lectura y carpeta bloqueada) |",
])
if t.count(ancla) != 1:
    print(f"  [x] README: el ancla aparece {t.count(ancla)} veces")
else:
    p.write_text(t.replace(ancla, nuevas, 1), encoding="utf-8")
    print("  [ok] datos_originales/README.md: 2 filas anadidas")
