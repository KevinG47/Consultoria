# -*- coding: utf-8 -*-
"""
Reproducibilidad: ¿las rutas de los siete scripts resuelven igual desde otro
directorio de trabajo? Aquí se importan sus constantes (no se ejecuta main) desde
un cwd distinto al del repositorio.
"""
from __future__ import annotations

import importlib
import io
import os
import sys
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
SRC = RAIZ / "documentacion_auditoria" / "src"
sys.path.insert(0, str(SRC))
sys.dont_write_bytecode = True

MODULOS = ["percapita_territorial", "modelo_estrella_6", "redes_modelos_nulos",
           "diversidad_inferencia", "clustering_formalizado", "validar_unicidad",
           "supervivencia", "generar_dashboard_fase2"]

otro = Path(tempfile.mkdtemp(prefix="cwd_"))
os.chdir(otro)
print(f"cwd de la prueba: {otro}\n")
print(f"{'script':32} {'entrada existe':>15} {'dir de salida existe':>21}  mkdir")
malos = []


def cargar(nombre):
    """Importa con stdout apuntando a devnull: los módulos reenvuelven sys.stdout
    y cerrarían el buffer real."""
    real = sys.stdout
    sys.stdout = io.TextIOWrapper(open(os.devnull, "wb"), encoding="utf-8")
    try:
        return importlib.import_module(nombre)
    finally:
        sys.stdout = real


for nombre in MODULOS:
    m = cargar(nombre)
    fuente = getattr(m, "FUENTE", None)
    salida = getattr(m, "SALIDA", None)
    ok_in = bool(fuente and Path(fuente).exists())
    ok_out = bool(salida and Path(salida).parent.exists())
    # ¿el módulo crea el directorio de salida antes de escribir?
    texto = (SRC / f"{nombre}.py").read_text(encoding="utf-8")
    mkdir = "mkdir(" in texto
    print(f"{nombre:32} {str(ok_in):>15} {str(ok_out):>21}  {mkdir}")
    if not ok_in:
        malos.append(f"{nombre}: el archivo de entrada no existe ({fuente})")
    if not ok_out:
        malos.append(f"{nombre}: el directorio de salida no existe ({salida})")

print("\n=== ¿alguno depende de un archivo no versionado? ===")
import subprocess
versionados = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True,
                             text=True, encoding="utf-8").stdout.split("\n")
versionados = {v.strip().replace("/", os.sep) for v in versionados if v.strip()}
for nombre in MODULOS:
    m = cargar(nombre)
    fuente = Path(getattr(m, "FUENTE"))
    rel = str(fuente.relative_to(RAIZ))
    print(f"  {nombre:32} {rel}  {'VERSIONADO' if rel in versionados else 'NO VERSIONADO'}")

os.chdir(RAIZ)
print("\n" + ("  FALLOS: " + "; ".join(malos) if malos else "  Sin fallos de rutas."))
