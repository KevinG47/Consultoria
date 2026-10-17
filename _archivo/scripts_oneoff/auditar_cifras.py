# -*- coding: utf-8 -*-
"""
Auditoría cruzada de cifras: dashboard → JSON → base cruda.

No confía en ninguna cifra publicada: recalcula desde el CSV de 31 MB y compara.
"""
from __future__ import annotations

import io
import json
import sys
from math import exp, sqrt
from pathlib import Path
from statistics import NormalDist

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parents[2]
MEM = RAIZ / "documentacion_auditoria" / "data" / "memoria"
RESULTADOS = RAIZ / "01_datos" / "resultados_json"
DASH = RAIZ / "02_dashboards"
FUENTE = (RAIZ / "01_datos" / "datos_fuente"
          / "Investigadores_Reconocidos_por_convocatoria_20261006.csv")
POB = (RAIZ / "01_datos" / "datos_fuente"
       / "dane_cnpv2018_poblacion_departamental.csv")


DE_RESULTADOS = {"percapita_territorial", "modelo_estrella", "redes_nulos",
                 "diversidad_inferencia", "clustering", "validacion_unicidad",
                 "supervivencia", "flujos_territoriales"}


def L(n):
    base = RESULTADOS if n in DE_RESULTADOS else MEM
    return json.loads((base / f"{n}.json").read_text(encoding="utf-8"))


fallos = []


def compara(nombre, calculado, publicado, tol=0.0):
    if isinstance(calculado, (int, float)) and isinstance(publicado, (int, float)):
        ok = abs(calculado - publicado) <= tol
        det = f"recalculado {calculado!r} vs publicado {publicado!r} (tol {tol:g})"
    else:
        ok = calculado == publicado
        det = f"recalculado {calculado!r} vs publicado {publicado!r}"
    print(f"  [{'OK ' if ok else 'MAL'}] {nombre}: {det}")
    if not ok:
        fallos.append(f"{nombre}: {det}")


print("=" * 72)
print("1. RETENCIÓN 2013 → 2021 (el 56,18 % del panel)")
print("=" * 72)
df = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                 usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR"])
df["conv"] = df["ID_CONVOCATORIA"].astype(int)
ids13 = set(df.loc[df["conv"] == 16, "ID_PERSONA_PR"])
ids21 = set(df.loc[df["conv"] == 21, "ID_PERSONA_PR"])
ret = len(ids13 & ids21) / len(ids13) * 100
print(f"  personas 2013: {len(ids13):,} · en 2021: {len(ids21):,} · "
      f"en ambas: {len(ids13 & ids21):,}".replace(",", " "))
sv = L("supervivencia")
uni = L("validacion_unicidad")
est = L("estimadores_resultados") if (MEM / "estimadores_resultados.json").exists() else {}
compara("retención 2013→2021 (%) recalculada vs F2-10 cohorte_2013",
        round(ret, 6), round(sv["cohorte_2013"]["retencion_final"] * 100, 6), 1e-6)
compara("retención vs F2-7 impacto.retencion_con",
        round(ret, 6), round(uni["impacto"]["retencion_2013_2021_con"]["pct"], 6), 1e-6)
if est:
    r = est["retencion"].get("2013\u21922021", {})
    if r:
        compara("retención vs estimadores_resultados (censo)",
                round(ret, 6), round(r["censo"] * 100, 6), 1e-6)

print()
print("=" * 72)
print("2. TERRITORIO: cifra per cápita del panel (Bogotá 137,7 · 2,10× · razón 105,5)")
print("=" * 72)
p = L("percapita_territorial")
# Población: se lee del CSV del DANE, no del JSON.
pob = pd.read_csv(POB)
print(f"  columnas del CSV del DANE: {list(pob.columns)}")
col_dep = [c for c in pob.columns if "DEPARTAMENTO" in c.upper()][0]
col_pob = [c for c in pob.columns if "POBLACION" in c.upper() or "TOTAL" in c.upper()][0]
pob_map = {str(r[col_dep]).strip(): float(r[col_pob]) for _, r in pob.iterrows()}
compara("población censada total (DANE)",
        int(sum(pob_map.values())), p["poblacion"]["censada_2018_total"])
for d in ("Bogotá, D. C.", "Vichada"):
    print(f"  DANE {d}: {pob_map.get(d, 'NO ESTÁ'):,.0f}".replace(",", " ")
          if isinstance(pob_map.get(d), float) else f"  DANE {d}: NO ESTÁ")

# Stock: una fila por persona, última convocatoria, con territorio colombiano.
df2 = pd.read_csv(FUENTE, dtype=str, keep_default_na=False, encoding="utf-8",
                  usecols=["ID_CONVOCATORIA", "ID_PERSONA_PR", "NME_DEPARTAMENTO_RES_PR"])
df2["conv"] = df2["ID_CONVOCATORIA"].astype(int)
df2["depto"] = df2["NME_DEPARTAMENTO_RES_PR"].str.strip()
ult = df2.sort_values("conv").groupby("ID_PERSONA_PR", observed=True).last()
val = ult[~ult["depto"].isin(["Exterior", "No disponible"])]
print(f"  stock recalculado: {len(val):,} personas".replace(",", " "))
compara("stock de personas", len(val), p["conteos"]["stock_personas"])
conteo = val["depto"].value_counts()
for d in ("Bogotá, D. C.", "Vichada"):
    tasas = p["tasa_por_100000"]["stock_ultima_convocatoria"][d]
    compara(f"investigadores en {d}", int(conteo[d]), tasas["investigadores"])
    tasa_calc = conteo[d] / pob_map[d] * 100000
    compara(f"tasa por 100 000 en {d}", round(tasa_calc, 6),
            round(tasas["tasa_por_100000"], 6), 1e-6)
cuota_inv = conteo["Bogotá, D. C."] / len(val) * 100
cuota_pob = pob_map["Bogotá, D. C."] / sum(pob_map.values()) * 100
compara("cuota de investigadores de Bogotá (%)", round(cuota_inv, 6),
        round(p["indicadores_clave"]["cuota_bogota_investigadores"] * 100, 6), 1e-6)
compara("cuota de población de Bogotá (%)", round(cuota_pob, 6),
        round(p["indicadores_clave"]["cuota_bogota_poblacion"] * 100, 6), 1e-6)
compara("cociente 2,10×", round(cuota_inv / cuota_pob, 6),
        round(p["indicadores_clave"]["sobrerrepresentacion_cuota_vs_poblacion"]
              ["Bogotá, D. C."], 6), 1e-6)
razon = (conteo["Bogotá, D. C."] / pob_map["Bogotá, D. C."]) / \
        (conteo["Vichada"] / pob_map["Vichada"])
compara("razón Bogotá/Vichada (105,5×)", round(razon, 6),
        round(p["indicadores_clave"]["razon_mayor_menor"], 6), 1e-6)

print()
print("=" * 72)
print("3. THEIL: ¿cierra la descomposición entre + dentro = total?")
print("=" * 72)
for anio, v in p["tasa_por_100000"]["por_convocatoria"].items():
    suma = v["theil_tasas_entre_regiones"] + v["theil_tasas_dentro_regiones"]
    dist = abs(suma - v["theil_t_tasas"])
    print(f"  {anio}: entre {v['theil_tasas_entre_regiones']:.6f} + dentro "
          f"{v['theil_tasas_dentro_regiones']:.6f} = {suma:.6f} vs total "
          f"{v['theil_t_tasas']:.6f} -> dif {dist:.2e}"
          + ("  OK" if dist < 1e-9 else "  MAL"))
    if dist >= 1e-9:
        fallos.append(f"descomposición del Theil en {anio} no cierra ({dist:.2e})")
st = p["indices_stock"]["theil_descomposicion_tasas_regiones"]
compara("descomposición del Theil del stock cierra",
        round(st["entre"] + st["dentro"], 12), round(st["total"], 12), 1e-12)

print()
print("=" * 72)
print("4. CLUSTERING: ¿el p = 0,762 sale del nulo por permutación?")
print("=" * 72)
cl = L("clustering")
pe = cl["prueba_de_estructura"]
nulo = pe["nulo_silhouette"]
obs = pe["silhouette_observada"]
ge = sum(1 for x in nulo if x >= obs)
p_calc = (1 + ge) / (1 + len(nulo))
print(f"  nulo: {len(nulo)} réplicas · mínimo {min(nulo):.4f} · máximo {max(nulo):.4f}")
print(f"  observada {obs:.6f} · media nula {sum(nulo)/len(nulo):.6f}")
print(f"  réplicas >= observada: {ge} -> p = (1+{ge})/(1+{len(nulo)}) = {p_calc:.6f}")
compara("p de la silhouette", round(p_calc, 6), round(pe["silhouette_p"], 6), 1e-6)
compara("media del nulo", round(sum(nulo) / len(nulo), 9),
        round(pe["silhouette_nulo_medio"], 9), 1e-9)
if pe["silhouette_nulo_medio"] > obs:
    print("  NOTA: la media del nulo SUPERA a la observada, que es lo que sostiene "
          "la conclusión «no hay estructura».")

print()
print("=" * 72)
print("5. COX: ¿HR = exp(beta), IC = exp(beta ± 1,96·se) y p = 2(1−Φ(|z|))?")
print("=" * 72)
Z = NormalDist().inv_cdf(0.975)
malos = 0
for r in sv["cox"]["coeficientes"]:
    hr = exp(r["beta"])
    lo, hi = exp(r["beta"] - Z * r["se"]), exp(r["beta"] + Z * r["se"])
    z = r["beta"] / r["se"]
    pv = 2 * (1 - NormalDist().cdf(abs(z)))
    d1, d2, d3 = abs(hr - r["hr"]), abs(lo - r["ic95_inf"]), abs(hi - r["ic95_sup"])
    dp = abs(pv - r["p"]) if pv > 1e-12 else 0.0
    marca = "OK " if (d1 < 1e-9 and d2 < 1e-9 and d3 < 1e-9) else "MAL"
    if marca == "MAL":
        malos += 1
    print(f"  [{marca}] {r['variable']}={r['nivel'][:30]:32s} HR {r['hr']:.6f} "
          f"(recalc {hr:.6f}) · IC [{r['ic95_inf']:.4f};{r['ic95_sup']:.4f}] "
          f"(recalc [{lo:.4f};{hi:.4f}]) · p {r['p']:.3e} (recalc {pv:.3e})")
    if not (0 <= r["p"] <= 1):
        fallos.append(f"p fuera de [0,1] en {r['nivel']}")
if malos:
    fallos.append(f"{malos} coeficientes del Cox no reproducen su HR o su intervalo")
gen = [r for r in sv["cox"]["coeficientes"] if r["variable"] == "genero_col"][0]
print(f"\n  La cifra del panel (HR género 0,988; p = 0,575) corresponde a "
      f"beta = {gen['beta']:.6f}, se = {gen['se']:.6f} -> HR {exp(gen['beta']):.4f}, "
      f"p {2*(1-NormalDist().cdf(abs(gen['beta']/gen['se']))):.4f}")
print(f"  El IC del género [{gen['ic95_inf']:.4f}; {gen['ic95_sup']:.4f}] "
      f"{'CONT IENE' if gen['ic95_inf'] < 1 < gen['ic95_sup'] else 'NO CONTIENE'} el 1")

print()
print("=" * 72)
print("6. HRs del panel tal como aparecen escritos en el dashboard")
print("=" * 72)
html = (DASH / "dashboard_fase2.html").read_text(encoding="utf-8")
for texto, valor in (("0,988", exp(gen["beta"])), ("0,105", None), ("0,376", None)):
    print(f"  '{texto}' aparece en el panel: {texto in html}")

print()
print("=" * 72)
print("RESUMEN")
print("=" * 72)
if fallos:
    for f in fallos:
        print("  FALLO:", f)
else:
    print("  Todas las cifras recalculadas coinciden con lo publicado.")
