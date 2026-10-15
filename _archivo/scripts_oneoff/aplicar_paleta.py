"""Aplica la paleta institucional al generador del dashboard.

Cada sustitucion debe aparecer EXACTAMENTE una vez; si alguna no aparece o
aparece mas de una, el script falla y no escribe nada. Asi no se cambia un color
por accidente en el sitio equivocado.

Uso: python _archivo/scripts_oneoff/aplicar_paleta.py [--aplicar]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RUTA = Path("documentacion_auditoria/src/generar_dashboard_eda.py")
aplicar = "--aplicar" in sys.argv

# (buscar, reemplazar, motivo)
CAMBIOS = [
    # ---- 1. Univariado: TODAS las barras de una serie en azul primario ----
    ('"Personas por categoría", color=AZUL), "u1"',
     '"Personas por categoría"), "u1"',
     "u1: barra de una serie -> azul primario (el defecto del ayudante)"),
    ('"Personas por género", color=DORADO), "u2"',
     '"Personas por género"), "u2"',
     "u2: barra de una serie -> azul primario"),
    ('"Personas por gran área", color=TEAL,\n                                            alto=470), "u3"',
     '"Personas por gran área",\n                                            alto=470), "u3"',
     "u3: barra de una serie -> azul primario"),
    ('color=MORADO, top=10, horizontal=True,',
     'top=10, horizontal=True,',
     "u4: barra de una serie -> azul primario"),
    ('color=AMBAR, alto=470), "u5"',
     'alto=470), "u5"',
     "u5: barra de una serie -> azul primario"),
    ('fig.add_trace(go.Histogram(x=edades, nbinsx=60, marker_color=AZUL,',
     'fig.add_trace(go.Histogram(x=edades, nbinsx=60, marker_color=PALETA["primario"],',
     "u6: histograma en azul primario"),
    ('fig.add_trace(go.Box(x=edades, marker_color=DORADO, name="Caja",\n'
     '                         boxpoints="outliers", marker=dict(size=3, opacity=0.5),',
     'fig.add_trace(go.Box(x=edades, marker_color=PALETA["primario"], name="Caja",\n'
     '                         boxpoints="outliers", marker=dict(size=3, opacity=0.5),\n'
     '                         line=dict(color=PALETA["dorado"], width=2),',
     "u6: caja azul con borde dorado"),
    ('font=dict(size=11, color=ROJO), xanchor="right")',
     'font=dict(size=11, color=ALERTA), xanchor="right")',
     "u6: la nota de los >100 anos se marca en rojo (excepcion)"),

    # ---- 2. Bivariado ----
    ('    for gen, color in (("Masculino", AZUL), ("Femenino", DORADO),\n'
     '                       ("Otro / No especificado", GRIS)):',
     '    for gen in ("Masculino", "Femenino", "Otro / No especificado"):\n'
     '        color = COLOR_GENERO[gen]',
     "r3: genero con azul + dorado + gris, desde el diccionario de color"),
    ('mode="lines+markers", line=dict(color=AZUL, width=4), marker=dict(size=11),',
     'mode="lines+markers", line=dict(color=PALETA["primario"], width=4),\n'
     '        marker=dict(size=11),',
     "r5: la linea censal (principal) en azul primario"),
    ('            ("Estimación MAS", "mas", DORADO, "dash"),\n'
     '            ("Post-estratificada", "post_estratificado", TEAL, "dot"),\n'
     '            ("GREG", "greg_lineal", VERDE, "dashdot")):',
     '            ("Estimación MAS", "mas", PALETA["dorado"], "dash"),\n'
     '            ("Post-estratificada", "post_estratificado", PALETA["claro"], "dot"),\n'
     '            ("GREG", "greg_lineal", PALETA["gris_medio"], "dashdot")):',
     "r5: estimaciones secundarias en dorado / azul claro / gris"),
    ('font=dict(size=11, color=AZUL_OSC), bgcolor="#EAF2FD",\n'
     '                           bordercolor="#B9D0EE", borderpad=4)',
     'font=dict(size=11, color=PALETA["primario_oscuro"]),\n'
     '                           bgcolor="#EAF0F9", bordercolor=PALETA["claro"],\n'
     '                           borderpad=4)',
     "r5: la anotacion en azul oscuro de la paleta"),

    # ---- 3. Varianza ----
    # Se busca por un fragmento SIN comillas: `color:{GRIS}` aparece una sola vez
    # en el archivo (dentro de una etiqueta HTML) y asi se evita pelear con el
    # escapado de comillas anidadas.
    ('color:{GRIS}',
     "color:{PALETA['gris_medio']}",
     "v1: etiquetas de estrato en gris medio"),
    ('    colores = [AZUL if t[0] in nombre.values() else GRIS_CLARO for t in items]',
     '    colores = [PALETA["primario"] if t[0] in nombre.values()\n'
     '               else PALETA["claro"] for t in items]',
     "v1: candidatos simples en azul primario, cruces en azul claro"),
    ('        marker_color=AZUL, showlegend=False,\n'
     '        text=[f"entre estratos {dcat[\'pct_entre\']:.2f} %".replace(".", ",")],',
     '        marker_color=PALETA["primario"], showlegend=False,\n'
     '        text=[f"entre estratos {dcat[\'pct_entre\']:.2f} %".replace(".", ",")],',
     "v1: segmento 'entre estratos' en azul primario"),
    ('        marker_color="#D6DEEE", showlegend=False,',
     '        marker_color=PALETA["gris_claro"], showlegend=False,',
     "v1: segmento 'dentro' en gris claro"),
    ('[int(cruce["n"].sum())], [AZUL_OSC], [""]',
     '[int(cruce["n"].sum())], [PALETA["primario_oscuro"]], [""]',
     "v2: raiz del treemap en azul oscuro"),
    ('        colores.append(COLOR_CATEGORIA.get(cat, GRIS))\n'
     '        textos.append(f"{miles(int(sub[\'n\'].sum()))} personas")',
     '        colores.append(COLOR_CATEGORIA.get(cat, PALETA["gris_medio"]))\n'
     '        textos.append(f"{miles(int(sub[\'n\'].sum()))} personas")',
     "v2: color de categoria en el treemap"),
    ('            colores.append(COLOR_CATEGORIA.get(cat, GRIS))',
     '            colores.append(COLOR_CATEGORIA.get(cat, PALETA["gris_medio"]))',
     "v2: color de las hojas del treemap"),

    # ---- 4. Diagnosticos ----
    ('        marker=dict(size=4, color=AZUL, opacity=0.35), showlegend=False,',
     '        marker=dict(size=4, color=PALETA["primario"], opacity=0.35), showlegend=False,',
     "d1: puntos del Q-Q en azul primario"),
    ('            marker=dict(size=9, color=ROJO, symbol="diamond"),',
     '            marker=dict(size=9, color=ALERTA, symbol="diamond"),',
     "d1: los casos >100 anos en rojo (excepcion)"),
    ('line=dict(color=DORADO, width=2, dash="dash"), hoverinfo="skip"))',
     'line=dict(color=PALETA["dorado"], width=2, dash="dash"), hoverinfo="skip"))',
     "d1: linea de referencia normal en dorado"),
    ('        marker=dict(size=4, color=AZUL, opacity=0.35),\n'
     '        hovertemplate="Ajustada %{x:.1f} años<br>Residuo %{y:.1f}<extra></extra>"),',
     '        marker=dict(size=4, color=PALETA["primario"], opacity=0.35),\n'
     '        hovertemplate="Ajustada %{x:.1f} años<br>Residuo %{y:.1f}<extra></extra>"),',
     "d2: residuos en azul primario"),
    ('    fig.add_hline(y=0, line=dict(color=ROJO, width=1.6), row=1, col=1)',
     '    fig.add_hline(y=0, line=dict(color=PALETA["dorado"], width=1.6), row=1, col=1)',
     "d2: la linea del cero es referencia -> dorado, no rojo"),
    ('        marker=dict(size=4, color=DORADO, opacity=0.35),',
     '        marker=dict(size=4, color=PALETA["claro"], opacity=0.35),',
     "d2: scale-location en azul claro"),
    ('showlegend=False, line=dict(color=ROJO, width=2.5),',
     'showlegend=False, line=dict(color=PALETA["dorado"], width=2.5),',
     "d2: la tendencia por doceavo es referencia -> dorado"),
    ('    fig.add_trace(go.Histogram(x=g, nbinsx=50, marker_color=VERDE, showlegend=False,',
     '    fig.add_trace(go.Histogram(x=g, nbinsx=50, marker_color=PALETA["primario"],\n'
     '                               showlegend=False,',
     "d3: histograma de g-weights en azul primario"),
    ('    fig.add_vline(x=gw["min"], line=dict(color=GRIS, width=1, dash="dot"), row=1, col=1)\n'
     '    fig.add_vline(x=gw["max"], line=dict(color=GRIS, width=1, dash="dot"), row=1, col=1)',
     '    for extremo in (gw["min"], gw["max"]):\n'
     '        fig.add_vline(x=extremo, line=dict(color=PALETA["gris_medio"], width=1,\n'
     '                                          dash="dot"), row=1, col=1)',
     "d3: los extremos como lineas grises de contexto"),
    ('                         marker_color=DORADO, showlegend=False,',
     '                         marker_color=PALETA["dorado"], showlegend=False,',
     "d3: los 25 mayores en dorado (son el foco del grafico)"),
    ('    fig.add_hline(y=1.0, line=dict(color=GRIS, width=1.4, dash="dash"), row=1, col=2)',
     '    fig.add_hline(y=1.0, line=dict(color=PALETA["gris_oscuro"], width=1.4,\n'
     '                                   dash="dash"), row=1, col=2)',
     "d3: la referencia g=1 en gris oscuro"),
    ('        marker=dict(size=5, color=AZUL, opacity=0.4),',
     '        marker=dict(size=5, color=PALETA["primario"], opacity=0.4),',
     "d4: leverage vs Cook en azul primario"),
    ('    fig.add_vline(x=inf["umbral_leverage"], line=dict(color=DORADO, width=1.6, dash="dash"),\n'
     '                  row=1, col=1)',
     '    fig.add_vline(x=inf["umbral_leverage"],\n'
     '                  line=dict(color=ALERTA, width=1.6, dash="dash"), row=1, col=1)',
     "d4: el umbral de leverage es una alerta -> rojo"),
    ('    fig.add_hline(y=inf["umbral_cook"], line=dict(color=ROJO, width=1.6, dash="dash"),\n'
     '                  row=1, col=1)',
     '    fig.add_hline(y=inf["umbral_cook"],\n'
     '                  line=dict(color=ALERTA, width=1.6, dash="dash"), row=1, col=1)',
     "d4: el umbral de Cook es una alerta -> rojo"),
    ('        marker=dict(size=5, color=TEAL, opacity=0.4),',
     '        marker=dict(size=5, color=PALETA["secundario"], opacity=0.4),',
     "d4: Cook por observacion en azul secundario"),
    ('    fig.add_hline(y=inf["umbral_cook"], line=dict(color=ROJO, width=1.6, dash="dash"),\n'
     '                  row=1, col=2)',
     '    fig.add_hline(y=inf["umbral_cook"],\n'
     '                  line=dict(color=ALERTA, width=1.6, dash="dash"), row=1, col=2)',
     "d4: mismo umbral de Cook en el panel derecho"),
    ('                       font=dict(size=11, color=GRIS))',
     '                       font=dict(size=11, color=PALETA["gris_medio"]))',
     "d4: la nota de conteos en gris medio"),

    # ---- escalas de los mapas de calor: rampa de azul, no rojo/ambar ----
    ('        z=z, x=pares, y=areas, colorscale=[[0, "#FDEEEC"], [0.5, "#FFF1D6"], [1, "#DCE9F8"]],\n'
     '        zmin=30, zmax=90, customdata=base,',
     '        z=z, x=pares, y=areas, colorscale=ESCALA_AZUL,\n'
     '        zmin=30, zmax=90, customdata=base,',
     "r2: mapa de calor con la rampa de azul"),
    ('        z=z, x=pares, y=nombres,\n'
     '        colorscale=[[0, "#FDEEEC"], [0.5, "#FFF1D6"], [1, "#DCE9F8"]],\n'
     '        zmin=20, zmax=95, customdata=base,',
     '        z=z, x=pares, y=nombres, colorscale=ESCALA_AZUL,\n'
     '        zmin=20, zmax=95, customdata=base,',
     "r4: mapa de calor con la rampa de azul"),
]


def main() -> int:
    texto = RUTA.read_text(encoding="utf-8")
    original = texto
    problemas = []
    for buscar, reemplazar, motivo in CAMBIOS:
        n = texto.count(buscar)
        if n != 1:
            problemas.append(f"aparece {n} vez(es), se esperaba 1: {motivo}")
            continue
        texto = texto.replace(buscar, reemplazar)
        print(f"  [ok] {motivo}")

    if problemas:
        print("\nNO se ha escrito nada. Problemas:")
        for p in problemas:
            print(f"  - {p}")
        return 1

    # Ningun color de la paleta vieja debe sobrevivir.
    sobrantes = []
    for viejo in ("AZUL_OSC", "AZUL", "DORADO", "VERDE", "ROJO", "AMBAR",
                  "GRIS_CLARO", "MORADO", "TEAL", "BORDE", "FONDO"):
        for i, linea in enumerate(texto.splitlines(), 1):
            if f" {viejo}" in linea or f"({viejo}" in linea or f"={viejo}" in linea:
                if "PALETA" in linea or "ALERTA" in linea:
                    continue
                sobrantes.append(f"linea {i}: {linea.strip()[:110]}")
    if sobrantes:
        print(f"\nQuedan {len(sobrantes)} referencias a constantes eliminadas:")
        for s in sobrantes[:20]:
            print(f"  {s}")
        return 1

    cambios = sum(1 for a, b in zip(original.splitlines(), texto.splitlines()) if a != b)
    print(f"\n{len(CAMBIOS)} sustituciones aplicadas.")
    if aplicar:
        RUTA.write_text(texto, encoding="utf-8")
        print(f"escrito {RUTA}")
    else:
        print("(simulacion: usa --aplicar para escribir)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
