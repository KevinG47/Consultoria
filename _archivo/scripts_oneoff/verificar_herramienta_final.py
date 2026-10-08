"""Verificacion final de la herramienta (tras los parches 3 y 4).

Comprueba autocontencion, fidelidad de los datos embebidos frente al CSV,
presencia de los elementos del DOM que montar() necesita, y el texto de
anonimizacion.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
HTML = RAIZ / "documentacion_auditoria" / "data" / "memoria" / "herramienta_trayectorias.html"
CSV = RAIZ / "Datos" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
CONV_ORDEN = [16, 17, 18, 19, 20, 21]

texto = HTML.read_text(encoding="utf-8")
kb = HTML.stat().st_size / 1024

print("=== 0. Archivo ===")
print(f"   {HTML}")
print(f"   {kb:,.1f} KB".replace(",", "."))
print(f"   bloques <script>: {len(re.findall(r'<script', texto))}")

print("\n=== 1. Autocontencion ===")
prohibidos = [r"<script[^>]+src\s*=", r"<link\b", r"@import", r"url\(\s*['\"]?https?:",
              r"\bfetch\s*\(", r"XMLHttpRequest", r"https?://", r"//cdn\.",
              r"\bintegrity\s*=", r"<iframe\b", r"<img\b", r"<audio\b|<video\b|<source\b"]
malos = []
for p in prohibidos:
    if re.search(p, texto, re.IGNORECASE):
        malos.append(p)
print(f"   patrones de recurso externo encontrados: {len(malos)} {malos}")
assert not malos

print("\n=== 2. Datos embebidos ===")
i = texto.index("const DATA = ") + len("const DATA = ")
datos, _ = json.JSONDecoder().raw_decode(texto, i)
partes = [t for t in pd.read_csv(CSV, dtype=str, keep_default_na=False, chunksize=50_000,
                                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR",
                                          "NME_CLASIFICACION_PR", "NME_GRAN_AREA_PR",
                                          "NME_AREA_PR", "NME_NIV_FORM_PR",
                                          "NME_DEPARTAMENTO_RES_PR", "INST_FILIA",
                                          "NME_GENERO_PR", "EDAD_ANOS_PR"])]
df = pd.concat(partes, ignore_index=True)
df["conv_i"] = df["ID_CONVOCATORIA"].astype(int)

assert len(df) == datos["filas"] == 77237
assert df["ID_PERSONA_PR"].nunique() == datos["personas_n"] == 30086
assert set(df["ID_PERSONA_PR"]) == set(datos["personas"].keys())
print(f"   77 237 filas y 30 086 personas: coinciden")

errores = []
n_comp = 0
for pid, grupo in df.groupby("ID_PERSONA_PR", sort=False):
    filas = datos["personas"][pid]
    esperado = grupo.sort_values("conv_i")
    if len(filas) != len(esperado):
        errores.append((pid, "n registros")); continue
    for r, (_, o) in zip(filas, esperado.iterrows()):
        inst = o["INST_FILIA"].strip()
        edad = round(float(o["EDAD_ANOS_PR"].replace(",", ".")) * 10) if o["EDAD_ANOS_PR"].strip() else -1
        checks = [
            r[0] == CONV_ORDEN.index(o["conv_i"]),
            datos["cat"][r[1]] == o["NME_CLASIFICACION_PR"],
            datos["areaGran"][r[2]] == o["NME_GRAN_AREA_PR"],
            datos["areaConocimiento"][r[3]] == o["NME_AREA_PR"],
            datos["nivel"][r[4]] == o["NME_NIV_FORM_PR"],
            datos["depto"][r[5]] == o["NME_DEPARTAMENTO_RES_PR"],
            datos["genero"][r[8]] == o["NME_GENERO_PR"],
            (r[6] == -1 and inst == "") or (r[6] >= 0 and datos["inst"][r[6]] == inst),
            r[7] == edad,
        ]
        n_comp += len(checks)
        if not all(checks):
            errores.append((pid, [j for j, c in enumerate(checks) if not c]))
    if len(errores) > 4:
        break
print(f"   {n_comp:,} comprobaciones de atributos".replace(",", "."))
print("   errores:", errores[:4] if errores else "ninguno")
assert not errores, errores[:4]

print("\n=== 3. Elementos del DOM que montar() necesita ===")
ids_html = set(re.findall(r'id="([A-Za-z0-9_]+)"', texto))
ids_js = set(re.findall(r'\$\("([A-Za-z0-9_]+)"\)', texto))
faltan = sorted(ids_js - ids_html)
print(f"   ids usados por el JS: {len(ids_js)}")
print(f"   faltantes en el HTML: {faltan if faltan else 'ninguno'}")
assert not faltan, faltan
print(f"   clases CSS definidas: {len(set(re.findall(r'<style>(.*?)</style>', texto, re.S)[0].split('.')))} bloques con punto")

print("\n=== 4. Contenido obligatorio ===")
obligatorios = {
    "mensaje de ID inexistente": "Ese ID no está en el padrón",
    "aviso de anonimizacion": "no contiene nombres",
    "palabra anonimizada": "anonimizada",
    "aviso de INST_FILIA multivaluado": "separadas por « | »",
    "mencion de convocatorias no anuales": "no son anuales",
    "comparacion con promedios": "Comparación con el promedio",
    "fuente citada": "bqtm-4y2h",
}
for etq, aguja in obligatorios.items():
    print(f"   {etq:38s} {'OK' if aguja in texto else 'FALTA'}")
    assert aguja in texto, etq

print("\n=== 5. Paleta de las diapositivas ===")
for color in ["#1E3780", "#B7871E"]:
    print(f"   {color}: {'presente' if color in texto else 'AUSENTE'}")
    assert color in texto

print(f"\nVERIFICACION COMPLETA — {kb:,.1f} KB".replace(",", "."))
