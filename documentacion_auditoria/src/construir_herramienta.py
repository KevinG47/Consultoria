"""Construye la herramienta interactiva de trayectorias por investigador.

Salida: documentacion_auditoria/data/memoria/herramienta_trayectorias.html
  - HTML autocontenido: CSS y JavaScript embebidos, datos embebidos.
  - Sin CDNs ni recursos externos: funciona con doble clic y sin internet.

Por que los datos van embebidos y no en un personas.json aparte:
  bajo el protocolo file:// el navegador bloquea fetch()/XMLHttpRequest sobre
  archivos locales (origen 'null'), asi que un JSON externo NO se cargaria al
  abrir el archivo con doble clic. Un <script src="personas.js"> si cargaria,
  pero un .json no. Embeberlo es lo unico que garantiza el requisito de
  "se abre con doble clic, sin internet" en un solo archivo.

Estructura de datos embebida (codigos enteros, no texto repetido):
  DATA.personas[ID] = [[conv, cat, areaGran, areaConoc, nivel, depto, inst, edad, genero], ...]
  Las cadenas viven una sola vez en los libros de codigos DATA.cat, DATA.depto, ...

Uso: python construir_herramienta.py
"""

from __future__ import annotations

import html
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
CSV = RAIZ / "Datos" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"
DIR_MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"
SALIDA = DIR_MEM / "herramienta_trayectorias.html"
JSON_LONG = DIR_MEM / "longitudinal_resultados.json"
CHUNK = 50_000

# Orden cronologico de las convocatorias (verificado: una sola fecha por ID).
CONV_ORDEN = [16, 17, 18, 19, 20, 21]

# Orden jerarquico de categorias (coincide con ORDEN_CLAS_PR 12<13<14<15; se verifica).
CATEGORIAS = ["Investigador Junior", "Investigador Asociado",
              "Investigador Sénior", "Investigador Emérito"]

COLS = ["ID_CONVOCATORIA", "ANO_CONVO", "NME_CONVOCATORIA", "ID_PERSONA_PR",
        "NME_CLASIFICACION_PR", "ORDEN_CLAS_PR", "NME_GRAN_AREA_PR", "NME_AREA_PR",
        "NME_NIV_FORM_PR", "NME_DEPARTAMENTO_RES_PR", "INST_FILIA",
        "EDAD_ANOS_PR", "NME_GENERO_PR"]


def cargar() -> pd.DataFrame:
    partes = [t for t in pd.read_csv(CSV, dtype=str, keep_default_na=False,
                                     chunksize=CHUNK, usecols=COLS, encoding="utf-8")]
    df = pd.concat(partes, ignore_index=True)
    df["conv_i"] = df["ID_CONVOCATORIA"].astype(int)
    return df


def codigos(valores) -> tuple[list[str], dict[str, int]]:
    """Libro de codigos determinista (ordenado) a partir de los valores observados."""
    uniq = sorted({v for v in valores})
    return uniq, {v: i for i, v in enumerate(uniq)}


def edad_a_decimas(txt: str) -> int:
    """'66,92' -> 669. Vacio -> -1. Se conserva un decimal exacto."""
    t = (txt or "").strip()
    if not t:
        return -1
    try:
        return int(round(float(t.replace(",", ".")) * 10))
    except ValueError:
        return -1


def main() -> int:
    print("== Carga ==")
    df = cargar()
    print(f"   {len(df):,} registros, {df['ID_PERSONA_PR'].nunique():,} personas"
          .replace(",", " "))

    # --- verificaciones de supuestos antes de construir -------------------
    orden = (df.groupby("NME_CLASIFICACION_PR", observed=True)["ORDEN_CLAS_PR"]
               .agg(lambda s: sorted(set(s))))
    for cat in CATEGORIAS:
        assert cat in orden.index, f"categoria ausente: {cat}"
        assert len(orden[cat]) == 1, f"{cat} con varios ORDEN_CLAS_PR: {orden[cat]}"
    ordenes = [int(orden[c][0]) for c in CATEGORIAS]
    assert ordenes == sorted(ordenes), f"CATEGORIAS no sigue ORDEN_CLAS_PR: {ordenes}"
    print(f"   orden jerarquico confirmado por ORDEN_CLAS_PR: {list(zip(CATEGORIAS, ordenes))}")

    fechas = {int(c): sorted(set(df.loc[df["conv_i"] == c, "ANO_CONVO"])) for c in CONV_ORDEN}
    for c, f in fechas.items():
        assert len(f) == 1, f"convocatoria {c}: {len(f)} fechas"
    nombres = {int(c): sorted(set(df.loc[df["conv_i"] == c, "NME_CONVOCATORIA"]))[0]
               for c in CONV_ORDEN}

    # --- libros de codigos -------------------------------------------------
    print("\n== Libros de codigos ==")
    lista_cat = CATEGORIAS
    mapa_cat = {c: i for i, c in enumerate(lista_cat)}
    lista_ag, mapa_ag = codigos(df["NME_GRAN_AREA_PR"])
    lista_area, mapa_area = codigos(df["NME_AREA_PR"])
    lista_niv, mapa_niv = codigos(df["NME_NIV_FORM_PR"])
    lista_dep, mapa_dep = codigos(df["NME_DEPARTAMENTO_RES_PR"])
    lista_gen, mapa_gen = codigos(df["NME_GENERO_PR"])
    inst_vals = sorted({v for v in df["INST_FILIA"] if v.strip()})
    lista_inst = inst_vals
    mapa_inst = {v: i for i, v in enumerate(lista_inst)}
    for nombre, lst in [("categorias", lista_cat), ("gran_area", lista_ag),
                        ("area_conocimiento", lista_area), ("nivel", lista_niv),
                        ("departamento", lista_dep), ("genero", lista_gen),
                        ("institucion", lista_inst)]:
        print(f"   {nombre:18s} {len(lst):6d} valores")

    # --- registros compactos por persona ----------------------------------
    print("\n== Construyendo trayectorias ==")
    df = df.sort_values(["ID_PERSONA_PR", "conv_i"], kind="stable")
    personas: dict[str, list[list[int]]] = defaultdict(list)
    for fila in df.itertuples(index=False):
        inst = fila.INST_FILIA.strip()
        personas[fila.ID_PERSONA_PR].append([
            CONV_ORDEN.index(fila.conv_i),
            mapa_cat[fila.NME_CLASIFICACION_PR],
            mapa_ag[fila.NME_GRAN_AREA_PR],
            mapa_area[fila.NME_AREA_PR],
            mapa_niv[fila.NME_NIV_FORM_PR],
            mapa_dep[fila.NME_DEPARTAMENTO_RES_PR],
            mapa_inst[inst] if inst else -1,
            edad_a_decimas(fila.EDAD_ANOS_PR),
            mapa_gen[fila.NME_GENERO_PR],
        ])
    personas = dict(personas)
    n_rec = sum(len(v) for v in personas.values())
    assert n_rec == len(df), f"registros perdidos: {n_rec} != {len(df)}"
    print(f"   {len(personas):,} personas, {n_rec:,} registros".replace(",", " "))
    largos = Counter(len(v) for v in personas.values())
    print("   convocatorias por persona:", dict(sorted(largos.items())))

    # --- tablas de comparacion --------------------------------------------
    print("\n== Tablas de comparacion ==")
    ult = CONV_ORDEN[-1]
    presentes_ult = {p for p, rs in personas.items() if any(r[0] == len(CONV_ORDEN) - 1 for r in rs)}
    cohortes = {}
    for i, c in enumerate(CONV_ORDEN):
        cohorte = [p for p, rs in personas.items() if min(r[0] for r in rs) == i]
        n = len(cohorte)
        if i == len(CONV_ORDEN) - 1:
            cohortes[str(i)] = {"anio": fechas[c][0][-4:], "n": n,
                                "siguen": None, "tasa": None}
        else:
            siguen = sum(1 for p in cohorte if p in presentes_ult)
            cohortes[str(i)] = {"anio": fechas[c][0][-4:], "n": n, "siguen": siguen,
                                "tasa": siguen / n if n else None}
        print(f"   cohorte de entrada {fechas[c][0][-4:]}: n={n:6d} "
              f"siguen en 2021={cohortes[str(i)]['siguen']}")

    # area de la ULTIMA convocatoria de cada persona
    area_ult = {}
    for p, rs in personas.items():
        area_ult[p] = rs[-1][2]
    areas = {}
    largo_por_persona = {p: len(v) for p, v in personas.items()}
    for i, nombre in enumerate(lista_ag):
        miembros = [p for p, a in area_ult.items() if a == i]
        if not miembros:
            continue
        areas[nombre] = {
            "n": len(miembros),
            "media_convocatorias": sum(largo_por_persona[p] for p in miembros) / len(miembros),
            "pct_en_2021": 100 * sum(1 for p in miembros if p in presentes_ult) / len(miembros),
        }
    media_global = sum(largo_por_persona.values()) / len(largo_por_persona)

    # retencion por gran area del ultimo par, tomada del analisis ya verificado
    ret_areas = {}
    if JSON_LONG.exists():
        longi = json.loads(JSON_LONG.read_text(encoding="utf-8"))
        tabla = longi.get("desagregacion_todos_los_pares", {}).get("gran_area", {})
        ultimo_par = list(tabla.keys())[-1] if tabla else None
        if ultimo_par:
            for k, v in tabla[ultimo_par]["grupos"].items():
                ret_areas[k] = {"tasa": v["tasa"], "n": v["n"], "par": ultimo_par}
        print(f"   retencion por gran area de {ultimo_par}: {len(ret_areas)} grupos")
    else:
        print("   AVISO: falta longitudinal_resultados.json; se omite la comparacion por area")

    # --- objeto de datos ---------------------------------------------------
    n_inst_multi = int(df["INST_FILIA"].str.contains(" | ", regex=False).sum())
    comp_uniq = set()
    for v in lista_inst:
        for c in v.split(" | "):
            if c.strip():
                comp_uniq.add(c.strip())
    print(f"   INST_FILIA multivaluado (' | '): {n_inst_multi} registros; "
          f"{len(lista_inst)} valores -> {len(comp_uniq)} instituciones distintas")

    datos = {
        "instMulti": n_inst_multi,
        "instComponentes": len(comp_uniq),
        "fuente": ("datos.gov.co, dataset bqtm-4y2h — Investigadores reconocidos "
                   "por convocatoria"),
        "filas": int(len(df)),
        "personas_n": len(personas),
        "convocatorias": [
            {"id": c, "anio": int(fechas[c][0][-4:]), "fecha": fechas[c][0],
             "nombre": nombres[c]} for c in CONV_ORDEN],
        "cat": lista_cat,
        "areaGran": lista_ag,
        "areaConocimiento": lista_area,
        "nivel": lista_niv,
        "depto": lista_dep,
        "genero": lista_gen,
        "inst": lista_inst,
        "cohortes": cohortes,
        "areas": areas,
        "retAreas": ret_areas,
        "mediaConvocatorias": media_global,
        "personas": personas,
    }

    # --- HTML -------------------------------------------------------------
    print("\n== Generando HTML ==")
    carga_json = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    # '<' escapado: evita que una cadena con '</script>' cierre el bloque.
    carga_json = carga_json.replace("<", "\\u003c")
    doc = PLANTILLA.replace("/*__DATOS__*/", carga_json)
    SALIDA.write_text(doc, encoding="utf-8")
    kb = SALIDA.stat().st_size / 1024
    print(f"   {SALIDA.name}: {kb:,.1f} KB".replace(",", "."))
    print(f"   JSON embebido: {len(carga_json)/1024:,.1f} KB".replace(",", "."))

    return 0


# ---------------------------------------------------------------------------
# Plantilla: se inyecta el JSON en /*__DATOS__*/. Sin f-strings para no tener
# que escapar las llaves de CSS y JavaScript.
# ---------------------------------------------------------------------------
PLANTILLA = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trayectorias de investigadores reconocidos — MinCiencias 2013–2021</title>
<style>
:root{
  --azul:#1E3780; --azul-osc:#0F1F4D; --dorado:#B7871E; --verde:#15803D;
  --rojo:#B91C1C; --ambar:#B45309; --gris:#64748B; --gris-claro:#94A3B8;
  --fondo:#F3F6FC; --blanco:#FFFFFF; --borde:#D6DEEE; --morado:#7C3AED;
  --teal:#0E7490;
}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:#0F172A;
  font-family:"Segoe UI",Roboto,system-ui,-apple-system,Arial,sans-serif;
  font-size:15px;line-height:1.5}
header{background:linear-gradient(135deg,var(--azul-osc),var(--azul));
  color:#fff;padding:20px 26px}
header h1{margin:0 0 4px;font-size:1.32rem;letter-spacing:.2px}
header .sub{font-size:.84rem;color:#C7D2E8}
.wrap{max-width:1500px;margin:0 auto;padding:20px 26px 60px}
.grid{display:grid;grid-template-columns:minmax(330px,400px) 1fr;gap:22px;align-items:start}
@media(max-width:980px){.grid{grid-template-columns:1fr}}
.card{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;
  padding:16px 18px;margin-bottom:18px;box-shadow:0 1px 2px rgba(15,31,77,.05)}
.card h2{margin:0 0 12px;font-size:1rem;color:var(--azul-osc);
  text-transform:uppercase;letter-spacing:.6px}
label{display:block;font-size:.8rem;font-weight:600;color:var(--azul-osc);
  margin:10px 0 4px}
input,select{width:100%;padding:9px 10px;border:1px solid var(--borde);
  border-radius:8px;font-size:.94rem;background:#fff;color:#0F172A}
input:focus,select:focus{outline:2px solid var(--dorado);outline-offset:1px}
button{background:var(--azul);color:#fff;border:0;border-radius:8px;
  padding:10px 16px;font-size:.92rem;font-weight:600;cursor:pointer}
button:hover{background:var(--azul-osc)}
button.dorado{background:var(--dorado)}
button.dorado:hover{background:#9A6F12}
button.mini{padding:4px 9px;font-size:.78rem;font-weight:500;background:#E8EEF9;
  color:var(--azul-osc)}
button.mini:hover{background:#D6E0F2}
.fila{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;align-items:center}
.aviso{background:#FFF7E6;border:1px solid #E8C77A;border-left:4px solid var(--dorado);
  border-radius:8px;padding:10px 12px;font-size:.83rem;color:#5A4308;margin-bottom:16px}
.error{background:#FDEEEC;border:1px solid #E7A9A0;border-left:4px solid var(--rojo);
  border-radius:8px;padding:12px 14px;color:#7A1D14;font-weight:600}
.info{background:#EAF2FD;border:1px solid #B9D0EE;border-left:4px solid var(--azul);
  border-radius:8px;padding:12px 14px;color:#123057}
.tabla{width:100%;border-collapse:collapse;font-size:.86rem}
.tabla th,.tabla td{padding:6px 8px;border-bottom:1px solid var(--borde);text-align:left}
.tabla th{color:var(--azul-osc);font-size:.76rem;text-transform:uppercase;
  letter-spacing:.4px}
.tabla td.num,.tabla th.num{text-align:right;font-variant-numeric:tabular-nums}
.ids{max-height:62vh;overflow:auto;border:1px solid var(--borde);border-radius:8px;
  padding:8px;background:#FBFCFE}
.id-chip{display:inline-block;font-family:Consolas,"Courier New",monospace;
  font-size:.8rem;background:#E8EEF9;color:var(--azul-osc);border:1px solid #C9D8F0;
  border-radius:6px;padding:3px 7px;margin:3px;cursor:pointer}
.id-chip:hover{background:var(--azul);color:#fff;border-color:var(--azul)}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:.76rem;
  font-weight:700;color:#fff;white-space:nowrap}
.pill.junior{background:var(--teal)} .pill.asociado{background:var(--azul)}
.pill.senior{background:var(--dorado)} .pill.emerito{background:var(--morado)}
.mov{display:inline-block;padding:2px 8px;border-radius:6px;font-size:.75rem;
  font-weight:700;white-space:nowrap}
.mov.sube{background:#E4F5EA;color:var(--verde)}
.mov.baja{background:#FDEEEC;color:var(--rojo)}
.mov.igual{background:#EEF2F8;color:var(--gris)}
.cambia{display:inline-block;margin:2px 4px 0 0;padding:1px 7px;border-radius:5px;
  font-size:.7rem;font-weight:700;background:#FFF1D6;color:var(--ambar);
  border:1px solid #E8C77A}
.ficha-cab{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:12px;margin-top:6px}
.dato{background:#F7F9FD;border:1px solid var(--borde);border-radius:9px;padding:9px 11px}
.dato .k{font-size:.7rem;text-transform:uppercase;letter-spacing:.5px;color:var(--gris);
  font-weight:700}
.dato .v{font-size:.95rem;color:#0F172A;font-weight:600;margin-top:2px;word-break:break-word}
.mono{font-family:Consolas,"Courier New",monospace}
.tl{position:relative;margin:8px 0 0;padding-left:26px}
.tl:before{content:"";position:absolute;left:8px;top:6px;bottom:6px;width:2px;
  background:linear-gradient(var(--azul),var(--dorado))}
.tl-fila{position:relative;padding:12px 14px;margin-bottom:12px;background:#FBFCFE;
  border:1px solid var(--borde);border-radius:10px}
.tl-fila:before{content:"";position:absolute;left:-22px;top:18px;width:11px;height:11px;
  border-radius:50%;background:var(--azul);border:2px solid #fff;
  box-shadow:0 0 0 2px var(--azul)}
.tl-fila.em:before{background:var(--morado);box-shadow:0 0 0 2px var(--morado)}
.tl-cab{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.tl-anio{font-weight:800;color:var(--azul-osc);font-size:1.02rem}
.tl-fecha{font-size:.78rem;color:var(--gris)}
.tl-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
.tl-item .k{font-size:.68rem;text-transform:uppercase;letter-spacing:.4px;
  color:var(--gris);font-weight:700}
.tl-item .v{font-size:.85rem}
.resumen{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
.big{font-size:1.5rem;font-weight:800;color:var(--azul);line-height:1.1}
.nota{font-size:.78rem;color:var(--gris);margin-top:8px}
.barra-ficha{display:flex;align-items:center;gap:10px;margin-bottom:12px;
  padding:8px 10px;background:#EEF3FB;border:1px solid var(--borde);
  border-radius:9px;position:sticky;top:0;z-index:5}
.barra-ficha .nota{margin:0}
.pie{margin-top:26px;padding-top:14px;border-top:1px solid var(--borde);
  font-size:.76rem;color:var(--gris)}
.pie code{background:#EEF2F8;padding:1px 5px;border-radius:4px}
kbd{background:#EEF2F8;border:1px solid var(--borde);border-bottom-width:2px;
  border-radius:5px;padding:1px 5px;font-size:.78rem;font-family:Consolas,monospace}
</style>
</head>
<body>
<header>
  <h1>Trayectorias individuales de investigadores reconocidos</h1>
  <div class="sub">Auditoría estadística del sistema de reconocimiento de MinCiencias ·
    6 convocatorias (2013, 2014, 2015, 2017, 2019, 2021) · herramienta autocontenida,
    sin conexión a internet</div>
</header>

<div class="wrap">
  <div class="aviso">
    <strong>Base anonimizada.</strong> Esta base <strong>no contiene nombres</strong> ni
    ningún dato de identificación personal: la única clave es el código
    <span class="mono">ID_PERSONA_PR</span>. No se puede buscar por nombre porque el
    nombre no existe en el conjunto de datos publicado. Todas las cifras provienen de la
    base completa: <span id="nFilas"></span> registros y
    <span id="nPersonas"></span> personas.
  </div>

  <div class="grid">
    <!-- ============ CONTROLES ============ -->
    <div>
      <div class="card">
        <h2>1. Buscar por ID</h2>
        <label for="q">Código ID_PERSONA_PR</label>
        <input id="q" class="mono" placeholder="0000003781" autocomplete="off"
               spellcheck="false">
        <div class="fila">
          <button id="btnBuscar">Buscar</button>
          <button class="mini" id="btnEjemplo">Ver un ejemplo</button>
        </div>
        <div class="nota">Se aceptan los 10 dígitos con ceros a la izquierda. Si escribes
          solo la parte numérica, se completa con ceros automáticamente.</div>
      </div>

      <div class="card">
        <h2>2. Listar por institución</h2>
        <label for="inst">Institución de filiación (INST_FILIA)</label>
        <input id="inst" list="listaInst" placeholder="Escribe parte del nombre…"
               autocomplete="off">
        <datalist id="listaInst"></datalist>
        <div class="fila">
          <button id="btnInst" class="dorado">Listar IDs</button>
          <button class="mini" id="btnLimpiarInst">Limpiar</button>
        </div>
        <div class="nota">Coincidencia por texto parcial, sin distinguir mayúsculas ni
          tildes. También existe la opción «sin institución registrada».
          <strong>Atención:</strong> el campo puede listar <em>varias</em> instituciones
          separadas por « | » (<span id="nInstMulti"></span> registros de
          <span id="nFilas2"></span>); el filtro compara institución por institución, no el
          texto completo. En el padrón hay <span id="nInstComp"></span> instituciones
          distintas una vez separadas.</div>
      </div>

      <div class="card">
        <h2>3. Listar por área, categoría y año</h2>
        <label for="fArea">Gran área de conocimiento</label>
        <select id="fArea"></select>
        <label for="fCat">Categoría</label>
        <select id="fCat"></select>
        <label for="fAnio">Convocatoria</label>
        <select id="fAnio"></select>
        <div class="fila">
          <button id="btnFiltro" class="dorado">Listar IDs</button>
          <button class="mini" id="btnLimpiarFiltro">Limpiar</button>
        </div>
        <div class="nota">Deja un campo en «(cualquiera)» para no restringirlo.</div>
      </div>

    </div>

    <!-- ============ PANEL DERECHO: LISTA DE RESULTADOS O FICHA ============ -->
    <div id="panelDerecho">
      <div class="card" id="cardResultados" style="display:none">
        <h2>Resultados <span id="resumenRes" class="nota"></span></h2>
        <div class="ids" id="listaIds"></div>
        <div class="nota">Haz clic en cualquier ID para abrir su ficha en este mismo panel.
          El botón «Volver a la lista» de la ficha devuelve a estos resultados.</div>
      </div>

      <div id="panelFicha">
        <div class="card">
          <div class="info">
            Escribe un ID y pulsa <strong>Buscar</strong>, o lista por institución, área,
            categoría y año: los resultados y la ficha aparecen <strong>aquí, a la
            derecha</strong>. Al hacer clic en un identificador de la lista, la lista se
            reemplaza por la ficha de esa persona.
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="pie">
    <strong>Fuente:</strong> <span id="pieFuente"></span>.
    <strong>Herramienta:</strong> <code>data/memoria/herramienta_trayectorias.html</code>,
    generada por <code>src/construir_herramienta.py</code>. Los valores que se muestran son
    los de <em>cada</em> convocatoria, no un resumen: los atributos pueden cambiar entre
    convocatorias (la categoría cambia en 8 755 personas, el nivel de formación en 3 844,
    la gran área en 1 389, el departamento en 1 203 y el género en 42). Cuando eso ocurre,
    la ficha lo advierte con una etiqueta.
    Las convocatorias <strong>no son anuales</strong> (2013, 2014, 2015, 2017, 2019, 2021):
    no existieron 2016, 2018 ni 2020, de modo que la distancia real entre convocatorias
    consecutivas va de 0,96 a 2,57 años y los huecos de la línea de tiempo no son
    homogéneos.
  </div>
</div>

<script id="app">
"use strict";
/* =====================================================================
   DATOS EMBEBIDOS
   personas[ID] = [[conv, cat, areaGran, areaConoc, nivel, depto, inst, edad, genero], ...]
   - conv: indice en DATA.convocatorias       - edad: decimas de anio (-1 = vacio)
   - inst: indice en DATA.inst (-1 = sin institucion registrada)
   ===================================================================== */
const DATA = /*__DATOS__*/;

/* ---------- utilidades puras ---------- */
function normalizar(t){
  return (t||"").toString().toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g,"").trim();
}

/* INST_FILIA puede listar VARIAS instituciones separadas por " | "
   (p. ej. "UNIVERSIDAD DE LA AMAZONIA | UNIVERSIDAD INDUSTRIAL DE SANTANDER").
   El filtro por institucion compara institucion por institucion. */
const COMPONENTES = DATA.inst.map(function(v){
  return v.split(" | ").map(function(x){ return x.trim(); }).filter(Boolean);
});
const COMPONENTES_NORM = COMPONENTES.map(function(lista){
  return lista.map(function(c){ return normalizar(c); });
});
const COMPONENTES_UNICOS = (function(){
  const vistos = {}, out = [];
  COMPONENTES.forEach(function(lista){
    lista.forEach(function(c){
      if(!vistos[c]){ vistos[c] = true; out.push(c); }
    });
  });
  return out.sort();
})();
function instTexto(idx){
  if(idx === undefined || idx === null || idx < 0) return "";
  return COMPONENTES[idx].join(" · ");
}
function idCanonico(txt){
  const t = (txt||"").toString().replace(/\s+/g,"").toUpperCase();
  if(!t) return "";
  if(DATA.personas[t]) return t;
  if(/^\d+$/.test(t) && t.length<=10){
    const p = t.padStart(10,"0");
    if(DATA.personas[p]) return p;
  }
  return t;
}
function edadTexto(d){
  if(d===undefined||d===null||d<0) return "no registra";
  return (d/10).toFixed(1).replace(".",",")+" años";
}
function fila(i,r){
  return {
    conv:r[0], anio:DATA.convocatorias[r[0]].anio,
    fecha:DATA.convocatorias[r[0]].fecha, nombre:DATA.convocatorias[r[0]].nombre,
    cat:r[1], catNombre:DATA.cat[r[1]],
    areaGran:r[2], areaGranNombre:DATA.areaGran[r[2]],
    areaConoc:r[3], areaConocNombre:DATA.areaConocimiento[r[3]],
    nivel:r[4], nivelNombre:DATA.nivel[r[4]],
    depto:r[5], deptoNombre:DATA.depto[r[5]],
    inst:r[6], instNombre:instTexto(r[6]),
    edad:r[7], edadTexto:edadTexto(r[7]),
    genero:r[8], generoNombre:DATA.genero[r[8]],
    i:i
  };
}
function trayectoria(id){
  const rs = DATA.personas[id];
  if(!rs) return null;
  return rs.map(function(r,i){ return fila(i,r); });
}

/* ---------- busqueda ---------- */
function buscarPorId(txt){
  const id = idCanonico(txt);
  if(!id || !DATA.personas[id]) return {encontrado:false, idIngresado:(txt||"").trim()};
  return {encontrado:true, id:id, filas:trayectoria(id)};
}

/* ---------- filtros ---------- */
const SIN_INSTITUCION = "(sin institución registrada)";
function institucionesQueCoinciden(texto){
  const t = normalizar(texto);
  if(!t) return [];
  const out = [];
  if(normalizar(SIN_INSTITUCION).indexOf(t)>=0) out.push(SIN_INSTITUCION);
  COMPONENTES_UNICOS.forEach(function(c){
    if(normalizar(c).indexOf(t)>=0) out.push(c);
  });
  return out;
}
function filtrarPorInstitucion(texto){
  const objetivo = institucionesQueCoinciden(texto);
  if(!objetivo.length) return [];
  const permitidas = {};
  objetivo.forEach(function(n){ permitidas[normalizar(n)] = true; });
  const incluyeSinInst = permitidas[normalizar(SIN_INSTITUCION)] === true;
  const out = [];
  Object.keys(DATA.personas).forEach(function(id){
    const rs = DATA.personas[id];
    for(let i=0;i<rs.length;i++){
      const idx = rs[i][6];
      if(idx < 0){
        if(incluyeSinInst){ out.push(id); return; }
        continue;
      }
      const comps = COMPONENTES_NORM[idx];
      for(let j=0;j<comps.length;j++){
        if(permitidas[comps[j]]){ out.push(id); return; }
      }
    }
  });
  return out.sort();
}
function filtrarPorAreaCatAnio(areaGran, cat, conv){
  const out = [];
  Object.keys(DATA.personas).forEach(function(id){
    const rs = DATA.personas[id];
    for(let i=0;i<rs.length;i++){
      const r = rs[i];
      if(areaGran!=="" && r[2]!==areaGran) continue;
      if(cat!=="" && r[1]!==cat) continue;
      if(conv!=="" && r[0]!==conv) continue;
      out.push(id); return;
    }
  });
  return out.sort();
}

/* ---------- resumen de trayectoria ---------- */
function resumenTrayectoria(filas){
  let ascensos=0, descensos=0;
  for(let i=1;i<filas.length;i++){
    if(filas[i].cat>filas[i-1].cat) ascensos++;
    else if(filas[i].cat<filas[i-1].cat) descensos++;
  }
  const iEm = filas.findIndex(function(f){ return f.catNombre==="Investigador Emérito"; });
  const deptos = [];
  filas.forEach(function(f){ if(deptos.indexOf(f.deptoNombre)<0) deptos.push(f.deptoNombre); });
  const insts = [];
  filas.forEach(function(f){
    const n = f.instNombre || "(sin institución registrada)";
    if(insts.indexOf(n)<0) insts.push(n);
  });
  const cambios = [];
  const campos = [["catNombre","categoría"],["areaGranNombre","gran área"],
                  ["nivelNombre","nivel de formación"],["deptoNombre","departamento"],
                  ["instNombre","institución"],["generoNombre","género"]];
  for(let i=1;i<filas.length;i++){
    campos.forEach(function(c){
      const a = filas[i-1][c[0]]||"", b = filas[i][c[0]]||"";
      if(a!==b) cambios.push({i:i, campo:c[1], de:a, a:b});
    });
  }
  return {
    n:filas.length,
    primera:filas[0], ultima:filas[filas.length-1],
    ascensos:ascensos, descensos:descensos,
    pasoEmerito:iEm>=0, convEmerito:iEm>=0?filas[iEm].anio:null,
    deptos:deptos, insts:insts, cambios:cambios
  };
}

/* ---------- comparacion con promedios ---------- */
function comparacion(filas){
  const r = resumenTrayectoria(filas);
  const convEntrada = filas[0].conv;
  const coh = DATA.cohortes[String(convEntrada)] || null;
  const areaNombre = r.ultima.areaGranNombre;
  const area = DATA.areas[areaNombre] || null;
  const ret = DATA.retAreas[areaNombre] || null;
  return {cohorte:coh, area:area, areaNombre:areaNombre, ret:ret,
          mediaGlobal:DATA.mediaConvocatorias,
          convPersona:r.n, ascensos:r.ascensos, descensos:r.descensos};
}

/* ---------- plantillas de vista (devuelven HTML) ---------- */
function esc(s){
  return (s===undefined||s===null?"":String(s))
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}
function claseCat(nombre){
  if(nombre.indexOf("Junior")>=0) return "junior";
  if(nombre.indexOf("Asociado")>=0) return "asociado";
  if(nombre.indexOf("Sénior")>=0) return "senior";
  return "emerito";
}
function vPill(nombre){ return '<span class="pill '+claseCat(nombre)+'">'+esc(nombre)+'</span>'; }
function vMov(filas,i){
  if(i===0) return '<span class="mov igual">Primera convocatoria</span>';
  const d = filas[i].cat - filas[i-1].cat;
  if(d>0) return '<span class="mov sube">▲ Ascendió</span>';
  if(d<0) return '<span class="mov baja">▼ Descendió</span>';
  return '<span class="mov igual">= Se mantuvo</span>';
}
function vCambios(filas,i){
  if(i===0) return "";
  const campos = [["catNombre","categoría"],["areaGranNombre","gran área"],
                  ["nivelNombre","nivel de formación"],["deptoNombre","departamento"],
                  ["instNombre","institución"],["generoNombre","género"]];
  let out = "";
  campos.forEach(function(c){
    const a = filas[i-1][c[0]]||"", b = filas[i][c[0]]||"";
    if(a!==b){
      const etq = c[1]==="institución" ? "cambió de institución"
        : (c[1]==="categoría" ? "cambió de categoría" : "cambió de "+c[1]);
      out += '<span class="cambia">'+esc(etq)+'</span>';
    }
  });
  return out;
}
function htmlFicha(id){
  const filas = trayectoria(id);
  if(!filas) return '<div class="card"><div class="error">Ese ID no está en el padrón.</div></div>';
  const r = resumenTrayectoria(filas);
  const c = comparacion(filas);
  const u = r.ultima;
  const h = [];
  h.push('<div class="card">');
  h.push('<h2>Ficha de trayectoria</h2>');
  h.push('<div class="ficha-cab">');
  h.push('<div class="dato"><div class="k">ID de la persona</div><div class="v mono">'+esc(id)+'</div></div>');
  h.push('<div class="dato"><div class="k">Género (último registrado)</div><div class="v">'+esc(u.generoNombre)+'</div></div>');
  h.push('<div class="dato"><div class="k">Edad en la última convocatoria ('+u.anio+')</div><div class="v">'+esc(u.edadTexto)+'</div></div>');
  h.push('<div class="dato"><div class="k">Departamento de residencia ('+u.anio+')</div><div class="v">'+esc(u.deptoNombre)+'</div></div>');
  h.push('<div class="dato"><div class="k">Institución más reciente ('+u.anio+')</div><div class="v">'+esc(u.instNombre||"(sin institución registrada)")+'</div></div>');
  h.push('</div>');
  if(u.edad>=0 && u.edad>1000){
    h.push('<div class="nota" style="color:#B45309"><strong>Atención:</strong> la edad registrada supera los 100 años ('+esc(u.edadTexto)+'). Es uno de los 22 registros con edad fuera de rango detectados en la auditoría y probablemente un error de captura.</div>');
  }
  h.push('</div>');

  h.push('<div class="card"><h2>Línea de tiempo</h2><div class="tl">');
  filas.forEach(function(f,i){
    h.push('<div class="tl-fila'+(f.catNombre==="Investigador Emérito"?" em":"")+'">');
    h.push('<div class="tl-cab"><span class="tl-anio">'+f.anio+'</span>'+vPill(f.catNombre));
    h.push(vMov(filas,i));
    h.push('<span class="tl-fecha">'+esc(f.nombre)+' · '+esc(f.fecha)+'</span></div>');
    h.push('<div class="tl-grid">');
    h.push('<div class="tl-item"><div class="k">Gran área</div><div class="v">'+esc(f.areaGranNombre)+'</div></div>');
    h.push('<div class="tl-item"><div class="k">Área de conocimiento (NME_AREA_PR)</div><div class="v">'+esc(f.areaConocNombre)+'</div></div>');
    h.push('<div class="tl-item"><div class="k">Nivel de formación</div><div class="v">'+esc(f.nivelNombre)+'</div></div>');
    h.push('<div class="tl-item"><div class="k">Departamento de residencia</div><div class="v">'+esc(f.deptoNombre)+'</div></div>');
    h.push('<div class="tl-item"><div class="k">Institución de filiación</div><div class="v">'+esc(f.instNombre||"(sin institución registrada)")+'</div></div>');
    h.push('<div class="tl-item"><div class="k">Edad</div><div class="v">'+esc(f.edadTexto)+'</div></div>');
    h.push('<div class="tl-item"><div class="k">Género registrado</div><div class="v">'+esc(f.generoNombre)+'</div></div>');
    h.push('</div>');
    const ch = vCambios(filas,i);
    if(ch) h.push('<div style="margin-top:6px">'+ch+'</div>');
    h.push('</div>');
  });
  h.push('</div></div>');

  h.push('<div class="card"><h2>Resumen de la trayectoria</h2><div class="resumen">');
  h.push('<div class="dato"><div class="k">Convocatorias en que aparece</div><div class="big">'+r.n+' de 6</div></div>');
  h.push('<div class="dato"><div class="k">Categoría inicial ('+r.primera.anio+')</div><div class="v">'+vPill(r.primera.catNombre)+'</div></div>');
  h.push('<div class="dato"><div class="k">Categoría final ('+r.ultima.anio+')</div><div class="v">'+vPill(r.ultima.catNombre)+'</div></div>');
  h.push('<div class="dato"><div class="k">Ascensos</div><div class="big" style="color:#15803D">▲ '+r.ascensos+'</div></div>');
  h.push('<div class="dato"><div class="k">Descensos</div><div class="big" style="color:#B91C1C">▼ '+r.descensos+'</div></div>');
  h.push('<div class="dato"><div class="k">Pasó por Emérito</div><div class="v">'+(r.pasoEmerito?('Sí, en '+r.convEmerito):"No")+'</div></div>');
  h.push('<div class="dato"><div class="k">Departamentos distintos</div><div class="v">'+r.deptos.length+'</div></div>');
  h.push('</div>');
  h.push('<div class="nota"><strong>Departamentos de residencia registrados:</strong> '+esc(r.deptos.join(" · "))+'</div>');
  if(r.insts.length>1){
    h.push('<div class="nota"><strong>Instituciones registradas a lo largo del tiempo:</strong> '+esc(r.insts.join(" · "))+'</div>');
  }
  if(r.cambios.length){
    h.push('<div class="nota"><strong>Cambios detectados entre convocatorias ('+r.cambios.length+'):</strong><ul style="margin:6px 0 0 18px;padding:0">');
    r.cambios.forEach(function(c2){
      h.push('<li>'+filas[c2.i].anio+': '+esc(c2.campo)+' — de “'+esc(c2.de||"(vacío)")+'” a “'+esc(c2.a||"(vacío)")+'”</li>');
    });
    h.push('</ul></div>');
  }
  h.push('</div>');

  h.push('<div class="card"><h2>Comparación con el promedio del padrón</h2><table class="tabla"><thead><tr><th>Indicador</th><th class="num">Esta persona</th><th class="num">Referencia</th></tr></thead><tbody>');
  h.push('<tr><td>Convocatorias en que aparece</td><td class="num">'+r.n+'</td><td class="num">'+DATA.mediaConvocatorias.toFixed(2).replace(".",",")+' (media del padrón)</td></tr>');
  if(c.area){
    h.push('<tr><td>Convocatorias en que aparece</td><td class="num">'+r.n+'</td><td class="num">'+c.area.media_convocatorias.toFixed(2).replace(".",",")+' (media de '+esc(c.areaNombre)+', n='+c.area.n+')</td></tr>');
  }
  if(c.cohorte && c.cohorte.tasa!==null){
    h.push('<tr><td>Retención de su cohorte de entrada ('+c.cohorte.anio+')</td><td class="num">'+(r.n>1?"siguió":"no siguió")+'</td><td class="num">'+(100*c.cohorte.tasa).toFixed(1).replace(".",",")+' % de '+c.cohorte.n+' personas</td></tr>');
  } else if(c.cohorte){
    h.push('<tr><td>Retención de su cohorte de entrada</td><td class="num">—</td><td class="num">sin ventana de seguimiento (entró en la última convocatoria)</td></tr>');
  }
  if(c.ret){
    h.push('<tr><td>Retención de '+esc(c.areaNombre)+' en '+esc(c.ret.par)+'</td><td class="num">—</td><td class="num">'+(100*c.ret.tasa).toFixed(1).replace(".",",")+' % (n='+c.ret.n+')</td></tr>');
  }
  if(c.area){
    h.push('<tr><td>Personas de '+esc(c.areaNombre)+' presentes en 2021</td><td class="num">—</td><td class="num">'+c.area.pct_en_2021.toFixed(1).replace(".",",")+' % de '+c.area.n+'</td></tr>');
  }
  h.push('</tbody></table>');
  h.push('<div class="nota">La columna «referencia» se calcula sobre la base completa (no sobre una muestra). La retención por gran área proviene del análisis longitudinal verificado.</div>');
  h.push('</div>');
  return h.join("");
}

/* ---------- capa de interfaz (solo navegador) ---------- */
function montar(){
  const $ = function(id){ return document.getElementById(id); };
  /* Estado de la ultima lista (para volver desde la ficha) y contenido inicial
     del panel derecho. Se declara aqui, antes de su primer uso. */
  let ultimaLista = null, idFichaActual = null, ayudaInicial = "";
  ayudaInicial = $("panelFicha").innerHTML;
  $("nFilas").textContent = DATA.filas.toLocaleString("es-CO");
  $("nPersonas").textContent = DATA.personas_n.toLocaleString("es-CO");
  $("nFilas2").textContent = DATA.filas.toLocaleString("es-CO");
  $("nInstMulti").textContent = DATA.instMulti.toLocaleString("es-CO");
  $("nInstComp").textContent = DATA.instComponentes.toLocaleString("es-CO");
  $("pieFuente").textContent = DATA.fuente;

  const selArea = $("fArea"), selCat = $("fCat"), selAnio = $("fAnio");
  selArea.appendChild(new Option("(cualquiera)",""));
  DATA.areaGran.forEach(function(a,i){ selArea.appendChild(new Option(a,String(i))); });
  selCat.appendChild(new Option("(cualquiera)",""));
  DATA.cat.forEach(function(a,i){ selCat.appendChild(new Option(a,String(i))); });
  selAnio.appendChild(new Option("(cualquiera)",""));
  DATA.convocatorias.forEach(function(c,i){
    selAnio.appendChild(new Option(c.anio+" ("+c.fecha+")",String(i)));
  });
  const dl = $("listaInst");
  DATA.inst.forEach(function(nombre){
    const o = document.createElement("option"); o.value = nombre; dl.appendChild(o);
  });
  const opSin = document.createElement("option");
  opSin.value = "(sin institución registrada)"; dl.appendChild(opSin);

  function volverALista(){
    if(!ultimaLista) return;
    mostrarLista(ultimaLista.ids, ultimaLista.etiqueta, ultimaLista.mensajeVacio);
  }
  function mostrarFicha(id, desplazar){
    const res = buscarPorId(id);
    idFichaActual = res.encontrado ? res.id : null;
    const barra = ultimaLista
      ? '<div class="barra-ficha"><button class="mini" id="btnVolver">← Volver a la lista ('
        + ultimaLista.ids.length.toLocaleString("es-CO") + ' personas)</button>'
        + '<span class="nota">' + esc(ultimaLista.etiqueta) + '</span></div>'
      : "";
    const cuerpo = res.encontrado
      ? htmlFicha(res.id)
      : '<div class="card"><div class="error">Ese ID no está en el padrón: no existe ningún investigador con el código <span class="mono">'+esc(res.idIngresado)+'</span>.</div></div>';
    $("panelFicha").innerHTML = barra + cuerpo;
    $("panelFicha").style.display = "";
    $("cardResultados").style.display = "none";
    const bv = document.getElementById("btnVolver");
    if(bv) bv.onclick = volverALista;
    if(desplazar !== false){
      $("panelDerecho").scrollIntoView({behavior:"smooth", block:"start"});
    }
  }
  function mostrarLista(ids, etiqueta, mensajeVacio){
    ultimaLista = {ids: ids, etiqueta: etiqueta, mensajeVacio: mensajeVacio || null};
    idFichaActual = null;
    $("cardResultados").style.display = "";
    $("panelFicha").style.display = "none";
    $("resumenRes").textContent = "· " + ids.length.toLocaleString("es-CO") + " personas " + etiqueta;
    const cont = $("listaIds");
    cont.innerHTML = "";
    const TOPE = 300;
    ids.slice(0,TOPE).forEach(function(id){
      const b = document.createElement("span");
      b.className = "id-chip"; b.textContent = id;
      b.onclick = function(){ mostrarFicha(id); };
      cont.appendChild(b);
    });
    if(ids.length>TOPE){
      const p = document.createElement("div");
      p.className = "nota";
      p.textContent = "Se muestran los primeros " + TOPE + " de " + ids.length.toLocaleString("es-CO") + ". Afina el filtro para reducir la lista.";
      cont.appendChild(p);
    }
    if(ids.length===0){
      cont.innerHTML = '<div class="nota">' + esc(mensajeVacio || "Ninguna persona cumple ese filtro.") + '</div>';
    }
    $("panelDerecho").scrollIntoView({behavior:"smooth", block:"start"});
  }
  /* Limpiar un filtro descarta su lista: si se esta viendo una ficha, se redibuja
     sin el boton de volver (ya no habria a donde volver). */
  function limpiarResultados(){
    ultimaLista = null;
    if(idFichaActual){
      mostrarFicha(idFichaActual, false);
    } else {
      /* Vuelve al estado neutro: si no, quedaria en pantalla el contenido anterior
         (por ejemplo el aviso de ID no encontrado) con un boton ya inservible. */
      $("cardResultados").style.display = "none";
      $("panelFicha").innerHTML = ayudaInicial;
      $("panelFicha").style.display = "";
    }
  }

  $("btnBuscar").onclick = function(){ mostrarFicha($("q").value); };
  $("q").addEventListener("keydown", function(e){
    if(e.key==="Enter") mostrarFicha($("q").value);
  });
  $("btnEjemplo").onclick = function(){
    const ids = Object.keys(DATA.personas).sort();
    $("q").value = ids[0]; mostrarFicha(ids[0]);
  };
  $("btnInst").onclick = function(){
    const t = $("inst").value;
    if(!normalizar(t)){ alert("Escribe parte del nombre de una institución."); return; }
    const insts = institucionesQueCoinciden(t);
    let etq;
    if(insts.length===0){
      etq = "· ninguna institución contiene «"+t+"»";
    } else if(insts.length===1){
      etq = "de «"+insts[0]+"»";
    } else {
      etq = "de "+insts.length+" instituciones que contienen «"+t+"»: "
          + insts.slice(0,3).join(" · ")
          + (insts.length>3 ? " y "+(insts.length-3)+" más" : "");
    }
    if(insts.length===0){
      mostrarLista([], etq, "Ninguna institución del padrón contiene ese texto.");
      return;
    }
    mostrarLista(filtrarPorInstitucion(t), etq);
  };
  $("btnLimpiarInst").onclick = function(){
    $("inst").value = ""; limpiarResultados();
  };
  $("btnFiltro").onclick = function(){
    const a = selArea.value, c = selCat.value, y = selAnio.value;
    const partes = [];
    if(a!=="") partes.push("gran área = "+DATA.areaGran[+a]);
    if(c!=="") partes.push("categoría = "+DATA.cat[+c]);
    if(y!=="") partes.push("convocatoria = "+DATA.convocatorias[+y].anio);
    mostrarLista(filtrarPorAreaCatAnio(a===""?"":+a, c===""?"":+c, y===""?"":+y),
                 partes.length? "con "+partes.join(" y ") : "en total");
  };
  $("btnLimpiarFiltro").onclick = function(){
    selArea.value=""; selCat.value=""; selAnio.value="";
    limpiarResultados();
  };
}

/* Exportacion para las pruebas automatizadas (Node). En el navegador no hace nada. */
if(typeof module !== "undefined" && module.exports){
  module.exports = {DATA:DATA, buscarPorId:buscarPorId, trayectoria:trayectoria,
    filtrarPorInstitucion:filtrarPorInstitucion, filtrarPorAreaCatAnio:filtrarPorAreaCatAnio,
    institucionesQueCoinciden:institucionesQueCoinciden, SIN_INSTITUCION:SIN_INSTITUCION,
    instTexto:instTexto, COMPONENTES_UNICOS:COMPONENTES_UNICOS,
    resumenTrayectoria:resumenTrayectoria, comparacion:comparacion, htmlFicha:htmlFicha,
    idCanonico:idCanonico, normalizar:normalizar};
}
if(typeof document !== "undefined" && typeof document.getElementById === "function"){
  montar();
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main())
