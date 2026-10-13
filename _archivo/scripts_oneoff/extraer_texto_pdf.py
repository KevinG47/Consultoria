"""Extractor de texto de PDF sin dependencias.

No hay pypdf, PyMuPDF ni pdftotext en el entorno, asi que se descomprimen los
flujos FlateDecode con zlib y se recogen las cadenas literales de los operadores
de texto (Tj/TJ). Sirve para comprobar que el PDF contiene una cifra concreta.
"""
from __future__ import annotations

import io
import re
import sys
import zlib
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RE_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
RE_CADENA = re.compile(rb"\((?:\\.|[^\\()])*\)")


def _unescape(b: bytes) -> str:
    b = b[1:-1]
    b = re.sub(rb"\\([nrtbf()\\])", lambda m: {
        b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b",
        b"f": b"\f", b"(": b"(", b")": b")", b"\\": b"\\"}[m.group(1)], b)
    b = re.sub(rb"\\[0-7]{1,3}", b"", b)
    return b.decode("latin-1", errors="replace")


def texto_de_pdf(ruta: Path) -> str:
    datos = ruta.read_bytes()
    piezas: list[str] = []
    for m in RE_STREAM.finditer(datos):
        crudo = m.group(1)
        try:
            plano = zlib.decompress(crudo)
        except zlib.error:
            plano = crudo
        if b"Tj" not in plano and b"TJ" not in plano:
            continue
        for c in RE_CADENA.finditer(plano):
            piezas.append(_unescape(c.group(0)))
    return " ".join(piezas)


def normalizar(t: str) -> str:
    return re.sub(r"\s+", " ", t)


if __name__ == "__main__":
    objetivo = Path(sys.argv[1])
    texto = normalizar(texto_de_pdf(objetivo))
    print(f"archivo : {objetivo}")
    print(f"bytes   : {objetivo.stat().st_size:,}".replace(",", "."))
    print(f"texto extraido: {len(texto)} caracteres")
    for aguja in sys.argv[2:]:
        presente = normalizar(aguja) in texto
        print(f"   {'SI' if presente else 'NO':>3}  contiene {aguja!r}")
    print("\n--- fragmentos alrededor de 'PASA' ---")
    for m in re.finditer(r"PASA", texto):
        ini, fin = max(0, m.start() - 90), min(len(texto), m.end() + 70)
        print("   ...", texto[ini:fin], "...")
