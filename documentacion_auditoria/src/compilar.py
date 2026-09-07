# -*- coding: utf-8 -*-
"""
compilar.py
===========

Compilador de los documentos LaTeX de la auditoría.

Función
-------
Para cada proyecto Overleaf en latex/<proyecto>/ con main.tex:
  1. compila con latexmk (pdfLaTeX, dos pasadas para referencias),
  2. copia el PDF resultante a pdf/<proyecto>.pdf.

Uso
---
    python compilar.py                  # compila todos los proyectos
    python compilar.py maestro_auditoria  # compila uno solo

Requisitos
----------
- TinyTeX (o TeX Live) con latexmk y los paquetes instalados vía
  `tlmgr install` (ver latex/comun/preambulo.tex para la lista).
- En Overleaf no hace falta compilar: se sube la carpeta del proyecto y
  Overleaf compila con su TeX Live completo.

Dependencias: solo biblioteca estándar (subprocess, pathlib, sys, shutil).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]  # documentacion_auditoria/
LATEX = RAIZ / "latex"
PDF = RAIZ / "pdf"


def compilar_proyecto(nombre: str) -> bool:
    """Compila latex/<nombre>/main.tex y copia el PDF a pdf/<nombre>.pdf."""
    proyecto = LATEX / nombre
    main = proyecto / "main.tex"
    if not main.exists():
        print(f"[x] No existe {main}")
        return False

    print(f"[>] Compilando {nombre} ...")
    r = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
         "-cd", str(main)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(f"[!] Error compilando {nombre} (código {r.returncode})")
        salida = (r.stdout or "") + "\n" + (r.stderr or "")
        tail = "\n".join(salida.splitlines()[-30:])
        print(tail or "Sin salida del compilador.")
        return False

    pdf_src = proyecto / "main.pdf"
    if pdf_src.exists():
        PDF.mkdir(parents=True, exist_ok=True)
        destino = PDF / f"{nombre}.pdf"
        shutil.copy2(pdf_src, destino)
        print(f"[ok] {destino}")
        return True
    print(f"[?] No se generó PDF para {nombre}")
    return False


def main() -> None:
    PDF.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        compilar_proyecto(sys.argv[1])
        return

    proyectos = sorted(p.name for p in LATEX.iterdir() if (p / "main.tex").exists())
    if not proyectos:
        print("No hay proyectos LaTeX con main.tex en latex/.")
        return
    ok = 0
    for nombre in proyectos:
        if compilar_proyecto(nombre):
            ok += 1
    print(f"Compilados {ok}/{len(proyectos)} proyectos.")


if __name__ == "__main__":
    main()
