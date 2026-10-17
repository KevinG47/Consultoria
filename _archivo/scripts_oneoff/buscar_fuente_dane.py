# -*- coding: utf-8 -*-
"""Lista los enlaces descargables (.xls/.xlsx/.csv/.zip) de una página del DANE
para localizar el cuadro oficial de población por departamento."""
import io
import re
import ssl
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CTX = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) consultoria-usta/1.0"}


class Enlaces(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.href: list[tuple[str, str]] = []
        self._href: str | None = None
        self._texto: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._texto = []

    def handle_data(self, data):
        if self._href is not None:
            self._texto.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.href.append((self._href, " ".join("".join(self._texto).split())))
            self._href = None


def traer(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=45, context=CTX) as r:
        crudo = r.read()
    for enc in ("utf-8", "latin-1"):
        try:
            return r.status, crudo.decode(enc)
        except UnicodeDecodeError:
            continue
    return r.status, crudo.decode("utf-8", "replace")


PAGINAS = sys.argv[1:] or [
    "https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/"
    "censo-nacional-de-poblacion-y-vivenda-2018",
]

PATRON = re.compile(r"\.(xlsx?|csv|zip)(\?|$)", re.I)

for pagina in PAGINAS:
    print("=" * 100)
    print(pagina)
    try:
        status, html = traer(pagina)
        print(f"  status={status}  tamaño={len(html):,} caracteres")
    except urllib.error.HTTPError as e:
        print(f"  HTTPError {e.code}")
        continue
    except Exception as e:  # noqa: BLE001
        print(f"  ERROR {type(e).__name__}: {e}")
        continue
    p = Enlaces()
    p.feed(html)
    vistos = set()
    coincidencias = 0
    for href, texto in p.href:
        if not PATRON.search(href):
            continue
        clave = href
        if clave in vistos:
            continue
        vistos.add(clave)
        coincidencias += 1
        print(f"  - {texto[:80]}")
        print(f"      {href}")
    print(f"  -> {coincidencias} enlaces descargables")
