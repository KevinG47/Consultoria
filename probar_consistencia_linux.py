"""
probar_consistencia_linux.py
============================

Simula el entorno Linux y comprueba que las 7 comprobaciones de
`documentacion_auditoria/src/verificar_consistencia.py` (la logica que usa la
regla R14) dan lo mismo que en Windows.

POR QUE EXISTE
--------------
Dentro del contenedor Linux la comprobacion 4 fallo con

    [FALLO] preguntas enumeradas vs cifra citada ('declara 7 preguntas' -> 842)

y no era ni un problema de CRLF/LF ni de BOM: **era el orden en que `rglob`
devuelve los 133 .tex**, que no es el mismo en Windows (NTFS) que en Linux
(ext4/overlayfs). El enunciado "Preguntas de investigacion que el repositorio
responde" aparece en tres documentos y solo uno tiene el bloque `enumerate`; con
la regex sobre la concatenacion de todo el corpus, el `(.*?)\\end{enumerate}` se
estiraba desde el enunciado de un documento hasta el cierre de enumerate de otro,
pudiendo abarcar medio corpus.

Este script hace tres cosas:

  A. Reproduce el fallo: con la implementacion VIEJA, el conteo cambia segun el
     orden (5, 7, 8... hasta cuatro cifras distintas), y saca el maximo que se
     alcanza barriendo ordenes aleatorios.
  B. Demuestra el arreglo: con la implementacion NUEVA, 300 ordenes aleatorios
     dan siempre 7 y siempre el mismo archivo.
  C. Simula Linux de verdad: copia el corpus a un directorio temporal, lo
     reescribe con finales de linea LF (y otra copia con CRLF, y otra con BOM) y
     corre las 7 comprobaciones completas sobre esa copia.

Uso:  python probar_consistencia_linux.py        (desde la raiz del repositorio)
Salida: 0 si todo pasa, 1 si algo falla.
"""

from __future__ import annotations

import importlib.util
import random
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent
DOC = RAIZ / "documentacion_auditoria"
MODULO = DOC / "src" / "verificar_consistencia.py"

fallos: list[str] = []


def cargar_modulo():
    spec = importlib.util.spec_from_file_location("verificar_consistencia", MODULO)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ---------------------------------------------------------------------------
# A. Implementacion VIEJA, para reproducir el fallo
# ---------------------------------------------------------------------------
def contar_viejo(archivos: list[Path]) -> int:
    tex = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in archivos)
    m = re.search(
        r"Preguntas de investigación que el repositorio responde(.*?)\\end\{enumerate\}",
        tex, re.S)
    return -1 if not m else len(re.findall(r"\\item", m.group(1)))


def parte_a(modulo) -> None:
    print("\n=== A) Implementacion VIEJA: el conteo depende del orden de lectura ===")
    archivos = list(modulo.LATEX.rglob("*.tex"))
    print(f"  .tex en el corpus: {len(archivos)}")
    print(f"  orden nativo de este sistema : {contar_viejo(archivos)}")
    print(f"  orden alfabetico             : {contar_viejo(sorted(archivos))}")
    print(f"  orden inverso                : {contar_viejo(sorted(archivos, reverse=True))}")

    vistos: dict[int, int] = {}
    maximo = -1
    generador = random.Random(20261)
    for _ in range(400):
        copia = archivos[:]
        generador.shuffle(copia)
        n = contar_viejo(copia)
        vistos[n] = vistos.get(n, 0) + 1
        maximo = max(maximo, n)
    print(f"  400 ordenes aleatorios       : valores {sorted(vistos)}")
    print(f"  maximo alcanzado             : {maximo}"
          f"   (en Docker/Linux se vio 842: mismo mecanismo)")
    if len(vistos) < 2:
        fallos.append("no se pudo reproducir la variacion del conteo viejo")
    else:
        print("  -> REPRODUCIDO: el mismo corpus da cifras distintas segun el orden")


# ---------------------------------------------------------------------------
# B. Implementacion NUEVA: insensible al orden
# ---------------------------------------------------------------------------
def parte_b(modulo) -> None:
    print("\n=== B) Implementacion NUEVA: mismo resultado con cualquier orden ===")
    original = modulo._archivos_tex
    archivos = list(original())
    valores, nombres = set(), set()
    try:
        modulo._archivos_tex = lambda: list(archivos)
        n, nombre = modulo._contar_preguntas()
        valores.add(n)
        nombres.add(nombre)
        generador = random.Random(7)
        for _ in range(300):
            copia = archivos[:]
            generador.shuffle(copia)
            modulo._archivos_tex = lambda copia=copia: copia
            n, nombre = modulo._contar_preguntas()
            valores.add(n)
            nombres.add(nombre)
    finally:
        modulo._archivos_tex = original

    print(f"  301 ordenes (nativo + 300 aleatorios) -> valores {sorted(valores)}")
    print(f"  archivo donde encuentra el bloque     -> {sorted(nombres)}")
    if valores != {7}:
        fallos.append(f"el conteo nuevo no es estable en 7: {sorted(valores)}")
    elif len(nombres) != 1:
        fallos.append(f"el archivo elegido no es unico: {sorted(nombres)}")
    else:
        print("  -> OK: 7 preguntas, siempre desde el mismo documento")


# ---------------------------------------------------------------------------
# C. Simulacion de Linux: LF / CRLF / BOM sobre una copia del corpus
# ---------------------------------------------------------------------------
def reescribir_tex(directorio: Path, modo: str) -> int:
    n = 0
    for p in directorio.rglob("*.tex"):
        texto = p.read_bytes().decode("utf-8-sig")      # quita BOM si lo hubiera
        texto = texto.replace("\r\n", "\n").replace("\r", "\n")
        if modo == "crlf":
            texto = texto.replace("\n", "\r\n")
        datos = texto.encode("utf-8")
        if modo == "bom":
            datos = b"\xef\xbb\xbf" + datos
        p.write_bytes(datos)
        n += 1
    return n


def parte_c(modulo) -> None:
    print("\n=== C) Simulacion de Linux: las 7 comprobaciones sobre una copia ===")
    temporal = Path(tempfile.mkdtemp(prefix="simlinux_"))
    try:
        latex = temporal / "latex"
        data = temporal / "data"
        shutil.copytree(modulo.LATEX, latex)
        shutil.copytree(modulo.DATA, data)
        print(f"  copia temporal: {temporal}")

        for modo, etiqueta in (("lf", "LF (lo que hay en Linux)"),
                               ("crlf", "CRLF (lo que hay en Windows)"),
                               ("bom", "UTF-8 con BOM + LF")):
            escritos = reescribir_tex(latex, modo)
            modulo.LATEX = latex
            modulo.DATA = data
            resultados = modulo.ejecutar()
            malos = [r for r in resultados if not r["ok"]]
            detalle = next((r for r in resultados if "preguntas" in r["nombre"]), None)
            print(f"\n  --- {etiqueta}: {escritos} .tex reescritos ---")
            print(f"      comprobaciones: {len(resultados) - len(malos)}/{len(resultados)} OK")
            if detalle:
                print(f"      comprobacion 4: {detalle['detalle']}")
            for r in malos:
                print(f"      [FALLO] {r['nombre']} -> {r['detalle']}")
            if malos:
                fallos.append(f"{etiqueta}: {len(malos)} comprobacion(es) fallan")
            if not detalle or detalle["ok"] is not True:
                fallos.append(f"{etiqueta}: la comprobacion 4 no paso")
    finally:
        shutil.rmtree(temporal, ignore_errors=True)
        print(f"\n  copia temporal eliminada")


def main() -> int:
    if not MODULO.exists():
        print(f"[x] no existe {MODULO}")
        return 1
    modulo = cargar_modulo()
    print("PRUEBA DE PORTABILIDAD — verificar_consistencia.py (logica de R14)")
    print(f"  modulo: {MODULO.relative_to(RAIZ)}")
    print(f"  sistema: {sys.platform}  (python {sys.version.split()[0]})")

    parte_a(modulo)
    parte_b(modulo)
    parte_c(modulo)

    print("\n=== RESUMEN ===")
    if fallos:
        print(f"  [x] {len(fallos)} fallo(s):")
        for f in fallos:
            print(f"      - {f}")
        return 1
    print("  [OK] El conteo es estable y las 7 comprobaciones pasan con LF, CRLF y BOM.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
