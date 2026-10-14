"""
Sprint 6 — Diagramas de Sankey de transición de categoría.

Para cada par consecutivo de convocatorias entre 2013 y 2021 produce un Sankey
que muestra cómo los investigadores reconocidos en t se redistribuyen entre las
categorías de t+1 (incluyendo "Desaparece"). Cinco diagramas en total.

Uso:
    python scripts/sprint6_sankey_categoria.py

Salidas:
    artifacts/sprint6_sankey/sankey_<a>_<b>.html  (interactivo)
    artifacts/sprint6_sankey/sankey_<a>_<b>.png   (estático para informe)
    evidencias/sankey_transiciones.csv            (todos los flujos)
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import plotly.graph_objects as go

from ingesta import cargar_consolidado
from Transformacion import transformar
from analisis.longitudinal import (
    construir_panel,
    comparar_periodo,
    matriz_transicion,
    ORDEN_CATEGORIAS,
)

ARTIFACTS = ROOT / "artifacts" / "sprint6_sankey"
EVIDENCIAS = ROOT / "evidencias"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


# Paleta consistente con la presentación HTML
COLOR_CAT = {
    "Junior":   "#5b8def",
    "Asociado": "#f4a261",
    "Senior":   "#2a9d8f",
    "Emerito":  "#9b5de5",
    "Desaparece": "#9aa3b2",
}


def construir_sankey(comp: pd.DataFrame, ano_a: int, ano_b: int) -> tuple:
    """Construye una figura Sankey y devuelve también los flujos en formato largo."""
    conteos, _ = matriz_transicion(comp, incluir_desaparece=True)
    # Reordenar filas siguiendo el orden canónico
    fila_orden = [c for c in ORDEN_CATEGORIAS if c in conteos.index]
    conteos = conteos.loc[fila_orden]

    # Construir nodos: cols izquierda (t) + cols derecha (t+1)
    nodos_izq = [f"{c}\n{ano_a}" for c in conteos.index]
    nodos_der = [f"{c}\n{ano_b}" for c in conteos.columns]
    nodos = nodos_izq + nodos_der

    # Colores por nodo
    colores_nodos = [COLOR_CAT.get(c, "#888") for c in conteos.index] + \
                    [COLOR_CAT.get(c, "#888") for c in conteos.columns]

    # Flujos
    sources, targets, values, link_colors = [], [], [], []
    flujos_largos = []
    for i, c_in in enumerate(conteos.index):
        for j, c_out in enumerate(conteos.columns):
            v = int(conteos.iloc[i, j])
            if v <= 0:
                continue
            sources.append(i)
            targets.append(len(nodos_izq) + j)
            values.append(v)
            # color del flujo: tonalidad suave del nodo origen
            link_colors.append(_rgba(COLOR_CAT.get(c_in, "#888"), alpha=0.45))
            flujos_largos.append({
                "periodo": f"{ano_a}-{ano_b}",
                "categoria_origen": c_in,
                "categoria_destino": c_out,
                "n_investigadores": v,
            })

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            label=nodos,
            color=colores_nodos,
            pad=18,
            thickness=18,
            line=dict(color="white", width=0.6),
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate="%{source.label} → %{target.label}<br>"
                          "<b>%{value}</b> investigadores<extra></extra>",
        ),
    ))

    total_t = conteos.sum().sum()
    fig.update_layout(
        title=dict(
            text=f"Transición de categorías {ano_a} → {ano_b}  "
                 f"<span style='font-size:12px;color:#888'>"
                 f"({total_t:,} investigadores reconocidos en {ano_a})</span>",
            font=dict(size=15),
        ),
        font=dict(family="Inter, sans-serif", size=12),
        margin=dict(l=20, r=20, t=60, b=20),
        height=520,
    )
    return fig, pd.DataFrame(flujos_largos)


def _rgba(hex_color: str, alpha: float = 0.5) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def main() -> None:
    print("[1/3] Cargando y transformando datos...")
    df = transformar(cargar_consolidado())
    panel = construir_panel(df)
    anios = sorted(panel["ANO_CONVO_INT"].dropna().unique())
    pares = list(zip(anios, anios[1:]))
    print(f"      Pares consecutivos: {pares}")

    print("\n[2/3] Construyendo Sankey por cada par...")
    todos_flujos = []
    for a, b in pares:
        comp = comparar_periodo(panel, a, b)
        fig, flujos = construir_sankey(comp, int(a), int(b))
        nombre = f"sankey_{int(a)}_{int(b)}"

        fig.write_html(ARTIFACTS / f"{nombre}.html",
                       include_plotlyjs="cdn",
                       full_html=True)
        fig.write_image(ARTIFACTS / f"{nombre}.png",
                        width=1100, height=520, scale=2)
        print(f"      {nombre}.html + .png  ({len(flujos)} flujos)")
        todos_flujos.append(flujos)

    print("\n[3/3] Exportando flujos consolidados...")
    df_flujos = pd.concat(todos_flujos, ignore_index=True)
    out_csv = EVIDENCIAS / "sankey_transiciones.csv"
    df_flujos.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"      {out_csv.relative_to(ROOT)}")
    print(f"      Total filas: {len(df_flujos):,}")

    # Resumen rápido por periodo
    resumen = (df_flujos
               .assign(tipo=lambda d: d.apply(_etiqueta_transicion, axis=1))
               .groupby(["periodo", "tipo"])["n_investigadores"]
               .sum()
               .unstack(fill_value=0))
    print("\n--- Resumen por periodo ---")
    print(resumen.to_string())

    print(f"\nFiguras: {ARTIFACTS.relative_to(ROOT)}")


def _etiqueta_transicion(row) -> str:
    """Clasifica una transición como Subió / Bajó / Mantiene / Desaparece."""
    if row["categoria_destino"] == "Desaparece":
        return "Desaparece"
    o = ORDEN_CATEGORIAS.get(row["categoria_origen"])
    d = ORDEN_CATEGORIAS.get(row["categoria_destino"])
    if o is None or d is None:
        return "Otro"
    if d > o: return "Sube"
    if d < o: return "Baja"
    return "Mantiene"


if __name__ == "__main__":
    main()
