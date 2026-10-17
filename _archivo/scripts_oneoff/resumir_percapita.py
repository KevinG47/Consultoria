# -*- coding: utf-8 -*-
"""Resume percapita_territorial.json para redactar el informe de F2-2."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
J = json.loads((RAIZ / "documentacion_auditoria" / "data" / "memoria"
                / "percapita_territorial.json").read_text(encoding="utf-8"))


def f(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ")


print("=" * 92)
print("1. TASAS POR 100 000 HABITANTES (stock, denominador censada 2018)")
print("=" * 92)
st = J["tasa_por_100000"]["stock_ultima_convocatoria"]
ic = J["bootstrap_personas"]["por_convocatoria_y_stock"]["stock"]["tasa_ic95"]
lo, hi = ic["lo"], ic["hi"]
nombres = list(st)
filas = sorted(range(len(nombres)),
               key=lambda i: -st[nombres[i]]["tasa_por_100000"])
print(f"{'departamento':38s} {'inv':>6s} {'población':>11s} {'tasa':>9s}"
      f" {'IC95 inf':>9s} {'IC95 sup':>9s}")
for i in filas[:12] + filas[-6:]:
    n = nombres[i]
    d = st[n]
    print(f"{n:38s} {d['investigadores']:6d} {d['poblacion']:11,d}"
          f" {d['tasa_por_100000']:9.1f} {lo[i]:9.1f} {hi[i]:9.1f}".replace(",", " "))
print(f"\ntasa nacional: {f(J['indicadores_clave']['tasa_nacional_por_100000'],1)}")
k = J["indicadores_clave"]
print(f"mayor: {k['departamento_mayor_tasa']['departamento']} = "
      f"{f(k['departamento_mayor_tasa']['tasa'],1)}")
print(f"menor: {k['departamento_menor_tasa']['departamento']} = "
      f"{f(k['departamento_menor_tasa']['tasa'],1)}")
print(f"razón mayor/menor: {f(k['razon_mayor_menor'],1)}")
print(f"cuota Bogotá: investigadores {f(100*k['cuota_bogota_investigadores'],2)} % · "
      f"población {f(100*k['cuota_bogota_poblacion'],2)} %")
print("sobrerrepresentación (cuota inv / cuota pob):")
for n, r in k["sobrerrepresentacion_cuota_vs_poblacion"].items():
    print(f"   {n:38s} {r:.2f}x")
print("subrepresentación:")
for n, r in k["subrrepresentacion_cuota_vs_poblacion"].items():
    print(f"   {n:38s} {r:.2f}x")

print()
print("=" * 92)
print("2. EVOLUCIÓN: CUOTAS (AUDITADO) FRENTE A DESIGUALDAD PER CÁPITA")
print("=" * 92)
pc = J["tasa_por_100000"]["por_convocatoria"]
ca = J["comparacion_auditado"]
print(f"{'año':>5s} {'HHI cuotas':>11s} {'Gini tasas':>11s} {'Theil tasas':>12s}"
      f" {'Gini conteos':>13s} {'HHI tasas':>10s} {'deptos=0':>9s} {'N':>7s}")
for a in sorted(pc):
    d = pc[a]
    print(f"{a:>5s} {ca['hhi_sin_exterior'][a]:11.4f} {d['gini_tasas']:11.4f}"
          f" {d['theil_t_tasas']:12.4f} {d['gini_conteos']:13.4f}"
          f" {d['hhi_tasas']:10.4f} {d['departamentos_sin_investigadores']:9d}"
          f" {d['total_investigadores']:7,d}".replace(",", " "))

print()
print("=" * 92)
print("3. THEIL: ENTRE Y DENTRO DE REGIONES")
print("=" * 92)
print(f"{'año':>5s} {'total':>9s} {'entre':>9s} {'dentro':>9s} {'% entre':>9s}")
for a in sorted(pc):
    d = pc[a]
    t, e, w = d["theil_t_tasas"], d["theil_tasas_entre_regiones"], d["theil_tasas_dentro_regiones"]
    print(f"{a:>5s} {t:9.4f} {e:9.4f} {w:9.4f} {100*e/t:8.1f} %")

print()
print("=" * 92)
print("4. IC BOOTSTRAP: PERSONAS FRENTE A DISEÑO (muestra MAS)")
print("=" * 92)
bp = J["bootstrap_personas"]["por_convocatoria_y_stock"]
bd = J["bootstrap_diseno_mas_ps"]["por_convocatoria"]
print(f"{'año':>5s} {'ancho IC personas':>18s} {'ancho IC diseño':>16s}"
      f" {'n muestra':>10s} {'tasa nac.':>10s} {'no difieren':>12s}")
for a in sorted(bd):
    d = bd[a]
    print(f"{a:>5s} {bp[a]['ancho_ic_mediano_por_100000']:18.1f}"
          f" {d['ancho_ic_mediano_por_100000']:16.1f} {d['n_muestra']:10,d}"
          f" {d['tasa_nacional_de_la_convocatoria']:10.1f}"
          f" {d['departamentos_que_no_difieren_del_promedio']:12d}"
          .replace(",", " "))
print("\nGini (bootstrap personas) con IC95, por año:")
for a in sorted(bp):
    print(f"   {a}: {bp[a]['gini_ic95'][0]:.4f} – {bp[a]['gini_ic95'][1]:.4f}"
          f"  (EE {bp[a]['gini_ee']:.4f})")

print()
print("=" * 92)
print("5. ÍNDICES DEL STOCK Y ROBUSTEZ")
print("=" * 92)
ix = J["indices_stock"]
for kk in ("gini_tasas", "theil_t_tasas", "theil_l_tasas", "hhi_tasas",
           "gini_conteos", "theil_t_conteos", "hhi_conteos"):
    print(f"   {kk:22s} {ix[kk] if ix[kk] is None else round(ix[kk], 4)}")
d = ix["theil_descomposicion_tasas_regiones"]
print(f"   Theil: total={d['total']:.4f} entre={d['entre']:.4f} "
      f"dentro={d['dentro']:.4f}")
print("\n   regiones (cuota de masa s_g vs cuota de unidades p_g):")
for r, v in sorted(d["grupos"].items(), key=lambda x: -x[1]["s_g"]):
    print(f"     {r:18s} s_g={v['s_g']:.4f} p_g={v['p_g']:.4f} "
          f"T_g={v['T_g']:.4f} n={v['n']}")
rb = J["robustez_denominador"]
print(f"\n   invariancia de escala verificada: "
      f"gini={rb['invariancia_gini_verificada']} theil={rb['invariancia_theil_verificada']}")
print(f"   con población ajustada 2018: Gini={rb['stock_con_poblacion_ajustada_2018']['gini_tasas']:.4f}"
      f" (Δ {rb['stock_con_poblacion_ajustada_2018']['delta_gini_vs_censada']:+.4f})"
      f" · Theil={rb['stock_con_poblacion_ajustada_2018']['theil_t_tasas']:.4f}"
      f" (Δ {rb['stock_con_poblacion_ajustada_2018']['delta_theil_vs_censada']:+.4f})")
c21 = rb["convocatoria_2021"]
print(f"   2021 con población 2018: tasa={c21['tasa_nacional_censada_2018']:.1f} "
      f"Gini={c21['gini_censada_2018']:.4f} Theil={c21['theil_censada_2018']:.4f}")
print(f"   2021 con población 2021: tasa={c21['tasa_nacional_proyectada_2021']:.1f} "
      f"Gini={c21['gini_proyectada_2021']:.4f} Theil={c21['theil_proyectada_2021']:.4f}")

print()
print("=" * 92)
print("6. COMPARACIÓN CON EL AUDITADO")
print("=" * 92)
print(f"   HHI con 'Exterior' (auditado) reproducido: "
      f"dif máx = {ca['maxima_diferencia_reproduccion']:.2e}")
print(f"   territorios: auditado {list(ca['n_territorios_auditado'].values())}"
      f" · reproducido {list(ca['n_territorios_reproducido'].values())}")
print(f"   efecto medio de incluir 'Exterior': "
      f"{ca['efecto_exterior_media_pp']:+.3f} pp de HHI")
print("\n   HHI con y sin 'Exterior' por año:")
for a in sorted(ca["hhi_auditado"]):
    print(f"     {a}: auditado={ca['hhi_auditado'][a]:.6f} "
          f"reproducido={ca['hhi_reproducido_con_exterior'][a]:.6f} "
          f"sin exterior={ca['hhi_sin_exterior'][a]:.6f}")

print()
print("=" * 92)
print("7. VALIDACIONES")
print("=" * 92)
for kk, v in J["validaciones"].items():
    print(f"   [{'OK ' if v else 'NO '}] {kk}")
print(f"\n   figuras: {J['figuras']}")
print(f"   fuente: {J['fuente']['registros_totales']:,} registros · "
      f"duplicados persona/convocatoria="
      f"{J['fuente']['duplicados_persona_en_misma_convocatoria']}".replace(",", " "))
