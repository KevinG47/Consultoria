# -*- coding: utf-8 -*-
"""
flujos_territoriales.py
=======================

Calcula los **flujos de migración territorial** que dibuja el mapa de F2-11.

DOS DEFINICIONES, Y HAY QUE ELEGIR
----------------------------------
«Se mudaron» admite dos lecturas y dan tamaños muy distintos:

  A) **Cambio de residencia dentro del período.** Para cada persona se compara el
     departamento de su PRIMERA convocatoria con el de su ÚLTIMA. Responde «¿quién
     se mudó entre 2013 y 2021?».

  B) **Residencia fuera del departamento de nacimiento.** Migración acumulada de
     toda la vida, no del período. Responde «¿cuánta gente vive lejos de su cuna?».

Las dos se calculan aquí. El mapa dibuja A por defecto y B como vista secundaria
(decisión D1 aprobada). El JSON deja las dos completas y verificadas.

DE DONDE SALEN LOS NUMEROS
--------------------------
De la base versionada `Investigadores_Reconocidos_por_convocatoria_20261006.csv`
(77.237 registros, 30.086 personas). No se inventa ni se recalcula nada de F2-2:
las tasas per cápita y el stock se leen de `percapita_territorial.json`.

LA LLAVE ES EL CODIGO, NO EL NOMBRE
-----------------------------------
La etiqueta del registro para San Andrés es
«Archipiélago de San Andrés, Providencia y Santa Catalina» y la del DANE (F2-2) es
«San Andrés, Providencia y Santa Catalina». Se traduce cada etiqueta a su código
DIVIPOLA y se publica el nombre del DANE: es la misma lección del hallazgo H6.

Salida:  01_datos/resultados_json/flujos_territoriales.json
Uso:     python flujos_territoriales.py
"""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
MEM = DOC / "data" / "memoria"
RESULTADOS = RAIZ / "01_datos" / "resultados_json"
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
DANE = (RAIZ / "01_datos" / "datos_fuente"
        / "dane_cnpv2018_poblacion_departamental.csv")
SALIDA = RESULTADOS / "flujos_territoriales.json"

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

COLS = ["ID_CONVOCATORIA", "ID_PERSONA_PR",
        "NME_DEPARTAMENTO_RES_PR", "COD_DANE_RES_PR", "NME_MUNICIPIO_RES_PR",
        "NME_DEPARTAMENTO_NAC_PR", "COD_DANE_NAC_PR", "NME_MUNICIPIO_NAC_PR"]

# Números ya verificados contra la base completa (auditoría previa). Si el cálculo
# deja de reproducirlos, el script falla en vez de publicar un mapa distinto.
ESPERADO = {
    "personas_2_mas": 19215,
    "comparables_a": 18430,
    "movimientos_a": 808,
    "rutas_a": 231,
    "rutas_una_persona_a": 110,
    "comparables_b": 28673,
    "movimientos_b": 11922,
    "rutas_b": 577,
}

# Rutas que el mapa marca como «de área metropolitana» (D2). El criterio es
# geográfico y verificable: Bogotá y Cundinamarca comparten conurbación y, en
# estos datos, el cambio de departamento coincide SIEMPRE con un cambio de
# municipio hacia o desde municipios de la sabana (Chía, Cajicá, Mosquera…).
# No se puede extender a otras parejas porque no hay tabla de áreas
# metropolitanas versionada, y por eso NO se marca, por ejemplo, Bolívar →
# Atlántico, que en los datos es Cartagena → Barranquilla.
PAREJAS_METROPOLITANAS = {
    ("11", "25"),   # Bogotá, D. C. → Cundinamarca
    ("25", "11"),   # Cundinamarca → Bogotá, D. C.
}


def cargar_dane() -> dict[str, dict]:
    """{codigo: {nombre, poblacion}} desde el CSV del DANE que usa F2-2."""
    with DANE.open(encoding="utf-8", newline="") as fh:
        return {f["codigo_dane"].strip(): {
            "nombre": f["departamento"].strip(),
            "poblacion": int(f["poblacion_censada_2018"]),
        } for f in csv.DictReader(fh)}


def traducir(etiquetas: set[str], dane: dict[str, dict]) -> dict[str, str]:
    """
    Etiqueta del registro → código DIVIPOLA. Falla si alguna etiqueta de
    departamento colombiano no se puede mapear, en vez de perder personas en
    silencio.
    """
    por_nombre = {v["nombre"]: c for c, v in dane.items()}
    mapa: dict[str, str] = {}
    for et in sorted(etiquetas):
        if et in por_nombre:
            mapa[et] = por_nombre[et]
    # San Andrés: el registro usa el nombre largo y el DANE el corto.
    largos = {"Archipiélago de San Andrés, Providencia y Santa Catalina": "88"}
    for et, cod in largos.items():
        if et in etiquetas and cod not in mapa.values():
            mapa[et] = cod
    especiales = {"Exterior", "No disponible", ""}
    faltan = [e for e in etiquetas if e not in mapa and e not in especiales]
    if faltan:
        raise SystemExit(f"Etiquetas de departamento sin código DIVIPOLA: {faltan}")
    if len(mapa) != 33:
        raise SystemExit(f"Se esperaban 33 etiquetas de departamento, hay {len(mapa)}")
    return mapa


def main() -> int:
    dane = cargar_dane()
    print(f"== DANE == {len(dane)} departamentos")

    df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                     usecols=COLS)
    df["conv"] = df["ID_CONVOCATORIA"].astype(int)
    for c in ("NME_DEPARTAMENTO_RES_PR", "NME_DEPARTAMENTO_NAC_PR",
              "NME_MUNICIPIO_RES_PR", "NME_MUNICIPIO_NAC_PR"):
        df[c] = df[c].str.strip()
    print(f"== Base == {len(df)} registros · {df['ID_PERSONA_PR'].nunique()} personas")

    mapa = traducir(set(df["NME_DEPARTAMENTO_RES_PR"])
                    | set(df["NME_DEPARTAMENTO_NAC_PR"]), dane)
    cod2nom = {c: v["nombre"] for c, v in dane.items()}

    def codigo(etiqueta: str) -> str:
        return mapa.get(etiqueta, "")

    # Comprobación cruzada: el código que trae la fila (2 dígitos o municipio de
    # 5) debe empezar por el código al que traducimos la etiqueta.
    res = df[~df["NME_DEPARTAMENTO_RES_PR"].isin(["Exterior", "No disponible"])]
    mal = 0
    for et, g in res.groupby("NME_DEPARTAMENTO_RES_PR", observed=True):
        pref = {str(c)[:2] for c in g["COD_DANE_RES_PR"] if str(c).strip()}
        if pref and pref != {codigo(et)}:
            mal += 1
    if mal:
        raise SystemExit(f"{mal} etiquetas cuyo código de fila no coincide con "
                         f"el código DIVIPOLA traducido")
    print("== Llave == código DIVIPOLA consistente entre etiqueta y columna COD_DANE")

    # ------------------------------------------------------------- personas A
    df = df.sort_values(["ID_PERSONA_PR", "conv"])
    prim = df.drop_duplicates("ID_PERSONA_PR", keep="first").set_index("ID_PERSONA_PR")
    ult = df.drop_duplicates("ID_PERSONA_PR", keep="last").set_index("ID_PERSONA_PR")
    n_conv = df.groupby("ID_PERSONA_PR").size()

    per = pd.DataFrame({
        "n_conv": n_conv,
        "res_ini": prim["NME_DEPARTAMENTO_RES_PR"],
        "res_fin": ult["NME_DEPARTAMENTO_RES_PR"],
        "mun_ini": prim["NME_MUNICIPIO_RES_PR"],
        "mun_fin": ult["NME_MUNICIPIO_RES_PR"],
        "nac": prim["NME_DEPARTAMENTO_NAC_PR"],
        "mun_nac": prim["NME_MUNICIPIO_NAC_PR"],
    })
    validas = (~per["res_ini"].isin(["Exterior", "No disponible"])
               & ~per["res_fin"].isin(["Exterior", "No disponible"]))
    con_varias = per["n_conv"] >= 2
    base = per[con_varias & validas]
    mueve = base[base["res_ini"] != base["res_fin"]]
    print(f"\n== Flujo A == {len(base)} comparables · {len(mueve)} movimientos")

    def rutas_detalle(sub: pd.DataFrame, col_o: str, col_d: str) -> list[dict]:
        rutas = []
        for (o, d), g in sub.groupby([col_o, col_d], observed=True):
            rutas.append((o, d, len(g), g))
        rutas.sort(key=lambda t: -t[2])
        salida = []
        for o, d, n, g in rutas:
            co, cd = codigo(o), codigo(d)
            salida.append({
                "origen": o if co else "Exterior",
                "origen_codigo": co,
                "destino": d,
                "destino_codigo": cd,
                "personas": n,
                "pct_de_movimientos": round(100 * n / len(sub), 2),
                "area_metropolitana": (co, cd) in PAREJAS_METROPOLITANAS,
                "dibujable": bool(co) and bool(cd),
            })
        return salida

    rutas_a = rutas_detalle(mueve, "res_ini", "res_fin")
    total_a = len(mueve)
    top10_a = rutas_a[:10]
    # evidencia municipal para las rutas que se marcan o se citan
    evidencia = {}
    for r in rutas_a[:20]:
        sub = mueve[(mueve["res_ini"] == r["origen"]) & (mueve["res_fin"] == r["destino"])]
        evidencia[f"{r['origen']} → {r['destino']}"] = {
            "personas": len(sub),
            "municipios_origen": Counter(sub["mun_ini"]).most_common(3),
            "municipios_destino": Counter(sub["mun_fin"]).most_common(3),
        }

    entradas = mueve.groupby("res_fin").size()
    salidas = mueve.groupby("res_ini").size()
    todos = sorted(set(entradas.index) | set(salidas.index))
    saldo = {d: int(entradas.get(d, 0) - salidas.get(d, 0)) for d in todos}

    metro = [r for r in rutas_a if r["area_metropolitana"]]
    flujo_a = {
        "definicion": ("Departamento de residencia de la PRIMERA convocatoria frente al "
                       "de la ÚLTIMA, para cada persona con dos o más convocatorias "
                       "observadas. Mide la mudanza dentro del período del registro."),
        "personas_2_mas_convocatorias": int(con_varias.sum()),
        "comparables": int(len(base)),
        "movimientos": int(total_a),
        "pct_de_comparables": round(100 * total_a / len(base), 2),
        "rutas": len(rutas_a),
        "rutas_una_persona": int(sum(1 for r in rutas_a if r["personas"] == 1)),
        "personas_top10": int(sum(r["personas"] for r in top10_a)),
        "personas_top20": int(sum(r["personas"] for r in rutas_a[:20])),
        "pct_movimientos_top10": round(100 * sum(r["personas"] for r in top10_a) / total_a, 2),
        "pct_movimientos_top20": round(100 * sum(r["personas"] for r in rutas_a[:20]) / total_a, 2),
        "rutas_con_mismo_municipio": int((mueve["mun_ini"] == mueve["mun_fin"]).sum()),
        "top10": top10_a,
        "rutas_detalle": rutas_a,
        "saldo_neto": saldo,
        "departamentos_con_saldo_no_cero": sum(1 for v in saldo.values() if v),
        "area_metropolitana": {
            "criterio": ("Rutas Bogotá ↔ Cundinamarca. Son mudanzas reales de municipio "
                         "hacia o desde la sabana de Bogotá, no ruido de captura; en un "
                         "mapa departamental se dibujan igual que una migración "
                         "interdepartamental y hay que marcarlas (decisión D2)."),
            "movimientos": int(sum(r["personas"] for r in metro)),
            "rutas": len(metro),
            "rutas_detalle": metro,
        },
        "evidencia_municipios": evidencia,
    }

    # ------------------------------------------------------------- flujo B
    ult_todos = df.drop_duplicates("ID_PERSONA_PR", keep="last")
    nac = ult_todos["NME_DEPARTAMENTO_NAC_PR"]
    ok = (~nac.isin(["", "No disponible"])
          & ~ult_todos["NME_DEPARTAMENTO_RES_PR"].isin(["Exterior", "No disponible"]))
    sub_b = ult_todos[ok]
    dif_b = sub_b[sub_b["NME_DEPARTAMENTO_NAC_PR"] != sub_b["NME_DEPARTAMENTO_RES_PR"]]
    rutas_b = rutas_detalle(dif_b, "NME_DEPARTAMENTO_NAC_PR", "NME_DEPARTAMENTO_RES_PR")
    top10_b = rutas_b[:10]
    no_dibujables = sum(r["personas"] for r in rutas_b if not r["dibujable"])
    evidencia_b = {}
    for r in rutas_b[:10]:
        q = dif_b[(dif_b["NME_DEPARTAMENTO_NAC_PR"] == r["origen"]) &
                  (dif_b["NME_DEPARTAMENTO_RES_PR"] == r["destino"])]
        evidencia_b[f"{r['origen']} → {r['destino']}"] = {
            "personas": len(q),
            "municipios_destino": Counter(q["NME_MUNICIPIO_RES_PR"]).most_common(3),
        }
    print(f"== Flujo B == {len(sub_b)} comparables · {len(dif_b)} fuera de su cuna")

    flujo_b = {
        "definicion": ("Departamento de nacimiento frente al departamento de residencia en "
                       "la última convocatoria observada. Es migración ACUMULADA de toda la "
                       "vida, no del período del registro."),
        "comparables": int(len(sub_b)),
        "movimientos": int(len(dif_b)),
        "pct_de_comparables": round(100 * len(dif_b) / len(sub_b), 2),
        "rutas": len(rutas_b),
        "personas_top10": int(sum(r["personas"] for r in top10_b)),
        "pct_movimientos_top10": round(100 * sum(r["personas"] for r in top10_b) / len(dif_b), 2),
        "personas_no_dibujables": int(no_dibujables),
        "rutas_no_dibujables": int(sum(1 for r in rutas_b if not r["dibujable"])),
        "nota_dibujo": ("Las rutas cuyo origen es «Exterior» (nacidos fuera de Colombia) no "
                        "se pueden dibujar sobre un mapa de departamentos. En esta vista NO "
                        "se marca el área metropolitana: el lugar de nacimiento no dice "
                        "cuándo ni desde dónde se mudó la persona."),
        "top10": top10_b,
        "rutas_detalle": rutas_b,
        "evidencia_municipios": evidencia_b,
    }

    # ------------------------------------------------------------ validaciones
    validaciones = {
        "a_no_supera_a_personas_con_2_mas": total_a <= int(con_varias.sum()),
        "a_comparables_suma_ok": (len(base) == int((con_varias & validas).sum())),
        "a_rutas_suman_movimientos": sum(r["personas"] for r in rutas_a) == total_a,
        "a_top10_suma_ok": sum(r["personas"] for r in top10_a) == flujo_a["personas_top10"],
        "a_saldo_cierra": sum(saldo.values()) == 0,
        "a_metro_no_excede_movimientos": flujo_a["area_metropolitana"]["movimientos"] <= total_a,
        "a_todos_cambian_municipio": int((mueve["mun_ini"] == mueve["mun_fin"]).sum()) == 0,
        "b_rutas_suman_movimientos": sum(r["personas"] for r in rutas_b) == len(dif_b),
        "b_top10_suma_ok": sum(r["personas"] for r in top10_b) == flujo_b["personas_top10"],
        "b_no_dibujables_no_exceden_movimientos": no_dibujables <= len(dif_b),
        "reproduce_numeros_auditados": None,   # se rellena abajo
    }

    hallado = {
        "personas_2_mas": flujo_a["personas_2_mas_convocatorias"],
        "comparables_a": flujo_a["comparables"],
        "movimientos_a": flujo_a["movimientos"],
        "rutas_a": flujo_a["rutas"],
        "rutas_una_persona_a": flujo_a["rutas_una_persona"],
        "comparables_b": flujo_b["comparables"],
        "movimientos_b": flujo_b["movimientos"],
        "rutas_b": flujo_b["rutas"],
    }
    if hallado != ESPERADO:
        raise SystemExit(f"El cálculo no reproduce los números auditados:\n"
                         f"  hallado  {hallado}\n  esperado {ESPERADO}")
    validaciones["reproduce_numeros_auditados"] = True
    if not all(v for v in validaciones.values()):
        raise SystemExit(f"Validaciones fallidas: {validaciones}")

    salida = {
        "fecha": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "analisis": "F2-11 — Flujos de migración territorial (mapa interactivo)",
        "fuente": {
            "archivo": FUENTE.name,
            "registros": int(len(df)),
            "personas": int(df["ID_PERSONA_PR"].nunique()),
            "convocatorias": [2013, 2014, 2015, 2017, 2019, 2021],
            "regla_persona": ("Una fila por persona y convocatoria (0 duplicados). Para el "
                              "flujo A se compara la primera con la última convocatoria "
                              "observada de cada persona."),
            "normalizacion_departamentos": (
                "Cada etiqueta de departamento se traduce a su código DIVIPOLA de 2 dígitos "
                "y se publica el nombre del DANE que usa F2-2. La etiqueta del registro para "
                "San Andrés es más larga que la del DANE: unir por nombre perdería esas "
                "personas (lección de H6)."),
            "personas_una_sola_convocatoria": int(df["ID_PERSONA_PR"].nunique()
                                                  - int(con_varias.sum())),
            "personas_con_residencia_invalida_en_primera_o_ultima": int((~validas).sum()),
        },
        "flujo_a": flujo_a,
        "flujo_b": flujo_b,
        "comparacion": {
            "a_es_del_periodo_b_es_de_la_vida": True,
            "b_incluye_exterior": True,
            "por_que_las_dos": ("A es la que promete el enunciado («entre 2013 y 2021») pero "
                                "es pequeña: 808 personas y una ruta máxima de 38. B tiene "
                                "volumen (11 922) pero no es del período y su primera ruta "
                                "nace fuera del país."),
        },
        "validaciones": validaciones,
        "figuras": ["flujos_top10_mudanzas.png", "flujos_top10_fuera_de_cuna.png",
                    "flujos_saldo_neto.png"],
    }
    MEM.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8", newline="\n")
    print(f"\n== Salida == {SALIDA.relative_to(RAIZ)} · {SALIDA.stat().st_size:,} B")
    print(f"   A: {total_a} movimientos en {len(rutas_a)} rutas · top10 "
          f"{flujo_a['pct_movimientos_top10']:.2f} % · metro "
          f"{flujo_a['area_metropolitana']['movimientos']}")
    print(f"   B: {len(dif_b)} en {len(rutas_b)} rutas · top10 "
          f"{flujo_b['pct_movimientos_top10']:.2f} % · no dibujables {no_dibujables}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
