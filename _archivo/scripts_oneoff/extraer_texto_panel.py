# -*- coding: utf-8 -*-
"""Extrae el texto legible del panel (sin bundle, sin etiquetas) para revisarlo."""
from __future__ import annotations
import html as _html
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
H = RAIZ / "02_dashboards" / "dashboard_fase2.html"
SALIDA = RAIZ / "_archivo" / "scripts_oneoff" / "texto_panel_fase2.txt"

t = H.read_text(encoding="utf-8")
ini = t.find("<script>")
fin = t.find("</script>", ini)
t = t[:ini] + t[fin + 9:]
# Fuera la cabecera de la librería y los bloques de datos de Plotly.
t = re.sub(r"<style>.*?</style>", "", t, flags=re.S)
t = re.sub(r"<script>.*?</script>", "\n[GRÁFICO]\n", t, flags=re.S)
t = re.sub(r"<div class=['\"]plotly-graph-div['\"].*?</div>", "", t, flags=re.S)
t = re.sub(r"<(br|/p|/tr|/h[1-4]|/div|/li)[^>]*>", "\n", t)
t = re.sub(r"<[^>]+>", "", t)
t = _html.unescape(t).replace("\u202f", " ")
t = re.sub(r"\n{3,}", "\n\n", t)
t = re.sub(r"[ \t]{2,}", " ", t)
lineas = [ln.strip() for ln in t.split("\n")]
SALIDA.write_text("\n".join(lineas), encoding="utf-8")
print(f"{SALIDA} · {len(lineas)} líneas")
