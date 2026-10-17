# -*- coding: utf-8 -*-
"""
verificar_hallazgos_anteproyecto.py
===================================

Comprueba si los 4 hallazgos del anteproyecto reaparecen como afirmaciones sin
aclarar en los análisis nuevos, y reconcilia las cifras de atípicos de edad.

Los 4 hallazgos (enunciado correcto, según guion y ERRATA):
  1. «22 registros con edad >100» citado como verificado -> el artefacto da 19;
     y el repositorio tiene contradicción interna 22 / 10 / 19.
  2. «Bogotá + Antioquia = 51 %» sin año -> real 56,2 / 52,0 / 47,9 por año.
  3. «24 % de mujeres en Ingeniería» -> el artefacto da 25,7 % (2017).
  4. «el 36,9 % no tiene fuente» -> es falso: produccion_resumen_cobertura.json
     contiene pct_autores_reconocidos = 36.94.

Además reconcilia la cifra propia de 11 personas >100 años con las del
repositorio auditado: si 11 personas producen 22 registros, las cifras no se
contradicen, se refieren a unidades distintas.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")

ANALISIS = {
    "analisis_longitudinal.md": RAIZ / "03_informes" / "analisis_fase2" / "analisis_longitudinal.md",
    "analisis_percapita_territorial.md": RAIZ / "03_informes" / "analisis_fase2" / "analisis_percapita_territorial.md",
    "evaluacion_cumplimiento.md": RAIZ / "03_informes" / "analisis_fase2" / "evaluacion_cumplimiento.md",
    "dashboard_eda.html": RAIZ / "02_dashboards" / "dashboard_eda.html",
}

# Patrones de los 4 hallazgos. Se excluye el bundle de Plotly del HTML, que
# introduce coincidencias espurias en JS minificado.
PATRONES = {
    "1 · atipicos edad (22/19/10)": re.compile(
        r"(?i)(?:^|[^\d])(22|19|10)\s*(?:registros?|casos?|personas?)?[^\n]{0,40}"
        r"(?:edad[^\n]{0,20}100|> ?100|at[ií]pic)"),
    "2 · Bogota+Antioquia sin año": re.compile(
        r"(?i)(bogot[aá][^\n]{0,30}antioquia|antioquia[^\n]{0,30}bogot[aá])"),
    # '51 %' precedido de dígito o coma es parte de otra cifra (79,51 %).
    "2b · '51 %' literal": re.compile(r"(?<![\d,])51\s?%"),
    "3 · 24 % mujeres Ingenieria": re.compile(
        r"(?i)(?<![\d,])24\s?%[^\n]{0,60}(ingenier|mujer)|(?<![\d,])25,7\s?%"),
    "4 · 36,9 % sin fuente": re.compile(
        r"(?i)36[.,]9[0-9]?\s?%|sin fuente|no tiene (?:fuente|respaldo)|"
        r"carece de (?:fuente|respaldo)"),
}

# --- 1. reconciliation de atipicos de edad --------------------------------
df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "EDAD_ANOS_PR"])
edad = pd.to_numeric(df["EDAD_ANOS_PR"].str.replace(",", ".", regex=False),
                     errors="coerce")
print("=" * 88)
print("RECONCILIACIÓN DE ATÍPICOS DE EDAD (> 100 años)")
print("=" * 88)
print(f"   registros totales en la fuente        : {len(df):,}".replace(",", " "))
print(f"   registros con edad > 100              : {int((edad > 100).sum())}")
print(f"   personas distintas con edad > 100     : "
      f"{df.loc[edad > 100, 'ID_PERSONA_PR'].nunique()}")
print(f"   edad máxima registrada                : {edad.max():.2f}")
masc = edad > 100
print(f"   convocatorias de esos registros       : "
      f"{sorted(df.loc[masc, 'ID_CONVOCATORIA'].unique().tolist())}")
# por persona, cuántas veces aparece por encima de 100
por_persona = df.loc[masc].groupby("ID_PERSONA_PR").size()
print(f"   registros por persona (distribución)  : "
      f"{por_persona.value_counts().sort_index().to_dict()}")
print(f"   -> {por_persona.size} personas producen {int(masc.sum())} registros")

# La cifra del dashboard es sobre el censo de personas en la ÚLTIMA
# convocatoria observada (una fila por persona), que es el diseño del EDA.
ult = (df.assign(_e=edad).sort_values(
        "ID_CONVOCATORIA", key=lambda s: s.astype(int))
       .drop_duplicates("ID_PERSONA_PR", keep="last"))
print(f"   personas en su última convocatoria    : {len(ult):,}".replace(",", " "))
print(f"   de esas, con edad > 100               : {int((ult['_e'] > 100).sum())}")
print(f"   sin edad registrada                   : {int(ult['_e'].isna().sum())}")

# --- 2. qué dice el EDA en JSON ------------------------------------------
eda = json.loads((DOC / "data" / "memoria" / "eda_resultados.json")
                 .read_text(encoding="utf-8"))
edad_json = eda.get("edad", {})
print(f"\n   eda_resultados.json -> mayores_100    : {edad_json.get('mayores_100')}")
print(f"   eda_resultados.json -> atipicos_bigote: "
      f"{edad_json.get('atipicos_bigote')}")
print(f"   eda_resultados.json -> n              : {edad_json.get('n')}")

# --- 3. rastreo de los 4 hallazgos en los análisis nuevos -----------------
print()
print("=" * 88)
print("RASTREO DE LOS 4 HALLAZGOS EN LOS ANÁLISIS NUEVOS")
print("=" * 88)
total = 0
for nombre, ruta in ANALISIS.items():
    if not ruta.exists():
        print(f"\n--- {nombre}: NO EXISTE ---")
        continue
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    es_html = ruta.suffix == ".html"
    print(f"\n--- {nombre} ({len(texto):,} caracteres) ---".replace(",", " "))
    hallado = False
    for etiqueta, patron in PATRONES.items():
        for m in patron.finditer(texto):
            linea = texto.count("\n", 0, m.start()) + 1
            contexto = " ".join(texto[max(0, m.start() - 90):m.end() + 90].split())
            # En el HTML, descartar coincidencias dentro del bundle de Plotly:
            # sus líneas son enormes (>2000 caracteres) y son JS minificado.
            if es_html:
                ini = texto.rfind("\n", 0, m.start()) + 1
                fin = texto.find("\n", m.end())
                largo = (fin if fin != -1 else len(texto)) - ini
                if largo > 3000:
                    continue
            hallado = True
            total += 1
            print(f"   [{etiqueta}] línea {linea}")
            print(f"      …{contexto}…")
    if not hallado:
        print("   sin coincidencias")

print(f"\nTOTAL de coincidencias en los 4 análisis: {total}")
print("(El bundle de Plotly del HTML se excluye: son líneas de miles de "
      "caracteres de JavaScript minificado.)")
