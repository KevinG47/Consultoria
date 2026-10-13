"""Busca cadenas en el texto de un PDF ignorando espacios.

Los PDF de LaTeX insertan espacios en los cortes de kerning ("A uditora"), de modo
que una busqueda literal falla. Quitando TODO el espacio de ambos lados, la
comparacion es fiable.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# extraer_texto_pdf ya reconfigura stdout en UTF-8 al importarse: envolverlo otra
# vez cerraria el buffer subyacente al recolectar el primer envoltorio.
from extraer_texto_pdf import texto_de_pdf  # noqa: E402


def compacto(t: str) -> str:
    return re.sub(r"\s+", "", t)


def main() -> int:
    objetivo = Path(sys.argv[1])
    agujas = sys.argv[2:]
    texto = texto_de_pdf(objetivo)
    plano = compacto(texto)
    print(f"archivo : {objetivo}  ({objetivo.stat().st_size:,} bytes)".replace(",", "."))
    print(f"texto   : {len(texto)} caracteres ({len(plano)} sin espacios)")
    fallos = 0
    for aguja in agujas:
        esperado = not aguja.startswith("!")
        limpio = compacto(aguja.lstrip("!"))
        presente = limpio in plano
        marca = "OK " if presente == esperado else "FALLO"
        if presente != esperado:
            fallos += 1
        print(f"   {marca}  {'contiene' if esperado else 'NO debe contener'} "
              f"{aguja.lstrip('!')!r} -> {'SI' if presente else 'NO'}")
    # contexto alrededor del recuento, si aparece
    m = re.search(r"\d+PASA", plano)
    if m:
        print(f"\n   recuento encontrado: ...{plano[max(0,m.start()-30):m.start()+60]}...")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
