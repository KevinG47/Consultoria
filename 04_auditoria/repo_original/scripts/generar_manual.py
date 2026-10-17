"""
Genera docs/manual.ipynb — manual reproducible del Observatorio.

El notebook está pensado para que cualquier persona pueda abrirlo, ejecutar las
celdas y obtener exactamente las figuras y tablas que aparecen en la
presentación. Cada sección corresponde a un hallazgo del observatorio y
muestra el código mínimo para producirlo.

Uso:
    python scripts/generar_manual.py
"""

import pathlib
import sys

import nbformat as nbf

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

cells = []


def md(text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text: str) -> None:
    cells.append(nbf.v4.new_code_cell(text))


# =====================================================================
# Portada
# =====================================================================
md("""# Manual reproducible — Observatorio MinCiencias

> Universidad Santo Tomás · Ustadistica · 2026-I

Este manual reproduce, en código y con texto explicativo, los doce hallazgos
del observatorio sobre el sistema de reconocimiento de investigadores de
MinCiencias. No reemplaza el informe final; lo precede.

**Cómo usarlo.** Ejecute las celdas en orden. Cada sección produce una o
varias figuras en `artifacts/` y una o varias tablas en `evidencias/`. Las
funciones reutilizables viven en `src/analisis/`; los scripts orquestadores,
en `scripts/`.

**Insumos.** Antes de ejecutar este manual hay que haber descargado los
datasets de Socrata:

```bash
python -m src.ingesta.minciencias    # 77.237 filas
python -m src.ingesta.produccion     # 3.166.629 filas (~1.2 GB)
```

**Estructura.**

1. Setup y carga de datos
2. Validación de calidad — atípicos de edad
3. Trayectoria longitudinal y matrices de transición
4. Diagramas de Sankey de transición de categoría
5. Concentración territorial (residencia)
6. Tabla maestra de instituciones
7. Análisis geográfico institucional
8. Sankey territorial residencia → institución
9. Brecha de género por gran área OCDE
10. Diversidad: etnia, discapacidad, víctimas del conflicto
11. Producción y categoría
12. Brecha de género en productividad
13. Composición de la producción por área OCDE
14. Cierre — recomendaciones de política pública
""")

# =====================================================================
# 1. Setup
# =====================================================================
md("""## 1. Setup y carga de datos

Carga los dos datasets de Socrata, aplica la transformación común y deja
listos los DataFrames `inv` (padrón de investigadores) y `prod` (producción
de grupos). Todas las celdas posteriores asumen estos dos objetos en memoria.
""")

code("""# Setup de paths e imports
import pathlib
import sys

ROOT = pathlib.Path.cwd()
if (ROOT / "src").exists():
    sys.path.insert(0, str(ROOT / "src"))
elif (ROOT.parent / "src").exists():
    ROOT = ROOT.parent
    sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 160)
print(f"ROOT = {ROOT}")
""")

code("""# Carga de los dos datasets
from ingesta import cargar_consolidado, cargar_produccion
from Transformacion import transformar
from analisis.produccion import normalizar_produccion

inv = transformar(cargar_consolidado())
print(f"Padron de investigadores: {inv.shape}")

prod = normalizar_produccion(cargar_produccion())
print(f"Produccion de grupos:     {prod.shape}")
""")

md("""**Notas sobre la carga.**

- `cargar_consolidado` lee primero `datos/raw/investigadores_consolidado.csv`.
  Si no existe, recurre al Excel de respaldo en `datos/tarea_join/`.
- `cargar_produccion` requiere el CSV crudo (1,2 GB). Si no está, ejecute
  `python -m src.ingesta.produccion` primero.
- `transformar` parsea `ANO_CONVO_INT`, estandariza género y limpia texto.
- `normalizar_produccion` añade `ANO_CONVO_INT` al dataset de producción y
  homogeniza tipos para que la llave de cruce funcione directo.
""")


# =====================================================================
# 2. Validación de calidad — atípicos de edad
# =====================================================================
md("""## 2. Validación de calidad — atípicos de edad

Hallazgo: el padrón contiene **22 registros con edad superior a 100 años**.
El máximo observado es **956 años** — claramente un error de digitación.

Método aplicado: **eliminación de casos** cuando el análisis depende de edad.
Justificación: 22 sobre 77.237 (0,03 %); el sesgo introducido es despreciable
y la trazabilidad se mantiene mejor que con imputación.

Se ofrece como alternativa la imputación por mediana del grupo
(área OCDE × categoría × género), pero no se aplica por defecto.
""")

code("""from analisis.calidad import (
    detectar_atipicos_edad, resumen_tratamiento, filtrar, imputar_mediana
)

atipicos = detectar_atipicos_edad(inv)
print(f"Atipicos detectados: {len(atipicos)}")
atipicos.head(10)
""")

code("""# Comparacion de metodos
resumen = resumen_tratamiento(inv)
for k, v in resumen.items():
    print(f"  {k}: {v}")
""")

code("""# Decision: eliminamos los 22 casos para todos los analisis posteriores
inv_clean = filtrar(inv)
print(f"Antes:    {len(inv):,} registros")
print(f"Despues:  {len(inv_clean):,} registros")
print(f"Maximo edad despues del filtro: {inv_clean['EDAD_ANOS_PR'].max()}")
""")


# =====================================================================
# 3. Trayectoria longitudinal
# =====================================================================
md("""## 3. Trayectoria longitudinal y matrices de transición

Reconstruye qué le pasa a cada investigador entre convocatorias consecutivas:
si se mantiene en su categoría, sube, baja o desaparece del padrón.

**Caveat importante.** Los investigadores **Eméritos no reaparecen en la
convocatoria siguiente porque el reconocimiento queda vitalicio.** Su
ausencia en `t+1` no es expulsión del sistema, es diseño. Las matrices
muestran 100 % en la columna "Desaparece" para Emérito; léase como
"reconocimiento vitalicio, no requiere re-postulación".
""")

code("""from analisis.longitudinal import (
    construir_panel, comparar_periodo, matriz_transicion, matrices_todos_periodos
)

panel = construir_panel(inv_clean)
anios = sorted(panel["ANO_CONVO_INT"].dropna().unique())
print(f"Convocatorias en el panel: {anios}")

# Matrices de transicion para todos los pares consecutivos
matrices = matrices_todos_periodos(panel, incluir_desaparece=True)
for periodo, m in matrices.items():
    print(f"\\n{periodo}")
    print(m["conteos"])
""")


# =====================================================================
# 4. Sankey de transición de categoría
# =====================================================================
md("""## 4. Diagramas de Sankey de transición de categoría

Cinco diagramas, uno por par de convocatorias consecutivas. Cada Sankey
muestra los flujos de cada categoría en `t` hacia cada categoría en `t+1`
(incluyendo `Desaparece`).
""")

code("""# El script orquestador genera los cinco Sankeys y un CSV consolidado
import subprocess
subprocess.run(["python3", "scripts/sprint6_sankey_categoria.py"], cwd=ROOT, check=True)
""")

code("""from IPython.display import IFrame
IFrame("../artifacts/sprint6_sankey/sankey_2019_2021.html", width=900, height=550)
""")

md("""**Lectura del Sankey 2019 → 2021.** La diagonal principal es la
permanencia en la misma categoría. Las bandas hacia abajo a la derecha son
descensos (`Asociado → Junior`, por ejemplo); las bandas hacia arriba son
ascensos (`Junior → Asociado`); y la columna `Desaparece` agrupa a los que
no aparecen en la siguiente convocatoria.

Se observa la frase del director: *"la mayoría de Asociados pasaron a Junior
porque dejaron de producir"*. El flujo `Asociado 2019 → Junior 2021` es
significativo en el último corte.
""")


# =====================================================================
# 5. Concentración territorial (residencia)
# =====================================================================
md("""## 5. Concentración territorial — residencia del investigador

Hallazgo central: **Bogotá D.C. (32 %) + Antioquia (16 %) concentran el
51 % del padrón.** La cola larga incluye 30 departamentos.
""")

code("""# Top departamentos
top_dpto = (inv_clean["NME_DEPARTAMENTO_RES_PR"].value_counts()
            .head(15).reset_index())
top_dpto.columns = ["departamento", "n_investigadores"]
top_dpto["pct"] = (top_dpto["n_investigadores"] / len(inv_clean) * 100).round(1)
top_dpto
""")

code("""from analisis.territorial import hhi_por_convocatoria

hhi = hhi_por_convocatoria(inv_clean, columna="NME_DEPARTAMENTO_RES_PR")
hhi.plot(x="ANO_CONVO_INT", y="hhi", marker="o", figsize=(10,4),
         legend=False)
plt.title("HHI de concentracion territorial por convocatoria")
plt.ylabel("HHI (0 = dispersion, 1 = monopolio)")
plt.xlabel("Convocatoria")
plt.show()
""")


# =====================================================================
# 6. Tabla maestra de instituciones
# =====================================================================
md("""## 6. Tabla maestra de instituciones

El campo `inst_filia` del padrón registra **2.762 entidades únicas**. Una
auditoría rápida muestra que en realidad son cerca de 800 instituciones
con captura sin estandarización (ej. "UNAL Bogotá", "UNAL Medellín",
"UNAL Manizales" aparecen como tres entidades).

El borrador entregado cubre **211 IES canónicas** y mapea el **91 % del
padrón**. Las 2.500 entradas pendientes son la cola larga (empresas,
hospitales pequeños, ONGs locales con menos de 20 apariciones cada una).

Esta tabla es uno de los entregables del observatorio: se propone como
**referencia inicial** para que MinCiencias adopte como estándar de
normalización.
""")

code("""# Cargar la tabla maestra y el mapeo
maestra = pd.read_csv(ROOT / "evidencias/tabla_maestra_ies.csv")
mapping = pd.read_csv(ROOT / "evidencias/mapping_inst_filia_to_ies.csv")

print(f"IES canonicas: {len(maestra)}")
print(f"Strings mapeados: {(mapping['estado'] == 'asignado').sum()}")
cob = (mapping.loc[mapping['estado'] == 'asignado', 'n_apariciones'].sum()
       / mapping['n_apariciones'].sum() * 100)
print(f"Cobertura: {cob:.1f}% del padron")

maestra.head(15)
""")

md("""**Reconstrucción de la tabla.**

Si desea regenerar la tabla maestra desde cero, el script
`scripts/sprint6_tabla_maestra_ies.py` contiene el diccionario completo
con los 258 strings mapeados (ver el bloque `MAPEO`). Para agregar nuevas
entradas, edite ese diccionario y vuelva a correr el script.
""")


# =====================================================================
# 7. Análisis geográfico institucional
# =====================================================================
md("""## 7. Análisis geográfico institucional

Con la tabla maestra podemos preguntar: **¿el investigador trabaja en el
mismo departamento donde reside?** Si no, ¿hacia dónde se afilia?

Este es el análisis que más resaltó el director:

> *Para mí lo más importante es el geográfico. No solo se concentra en el
> departamento de residencia, sino en el departamento de la institución.
> Los de Vichada probablemente trabajan en instituciones del Meta o Bogotá.*
""")

code("""import subprocess
subprocess.run(["python3", "scripts/sprint6_geografia_institucional.py"],
               cwd=ROOT, check=True)
""")

code("""# Resumen por departamento de residencia
resumen = pd.read_csv(ROOT / "evidencias/geografia_resumen_por_dpto_residencia.csv")
resumen.head(15)
""")

code("""# Top flujos transversales: residencia != institucion
flujos = pd.read_csv(ROOT / "evidencias/geografia_top_flujos.csv")
flujos.head(15)
""")

md("""**Hallazgos clave.**

- Bogotá retiene al 92 % de sus propios investigadores **y** absorbe gente
  de prácticamente todos los demás departamentos. El flujo más fuerte es
  Antioquia → Bogotá (242 investigadores).
- Cundinamarca tiene baja retención local (67 %): muchos de sus
  investigadores se afilian a Bogotá.
- **Sorpresa: Chocó retiene al 92 % de los suyos**, pese a ser un departamento
  con históricas barreras de acceso a educación superior.
- El único investigador de Vichada está en Bogotá (confirma la intuición
  del director).
""")


# =====================================================================
# 8. Sankey territorial
# =====================================================================
md("""## 8. Sankey territorial — residencia → institución

Visualización agregada de los flujos residencia → institución. La diagonal
(residencia = institución) es la retención local; las bandas transversales
muestran las migraciones académicas.
""")

code("""import subprocess
subprocess.run(["python3", "scripts/sprint6_sankey_territorial.py"], cwd=ROOT, check=True)
""")

code("""from IPython.display import IFrame
IFrame("../artifacts/sprint6_sankey/sankey_territorial.html",
       width=950, height=620)
""")


# =====================================================================
# 9. Brecha de género por gran área OCDE
# =====================================================================
md("""## 9. Brecha de género por gran área OCDE

La paridad agregada (~40 % de mujeres) esconde brechas estructurales muy
distintas por gran área de conocimiento. Diez años de convocatorias no
muestran cierre.
""")

code("""from analisis.genero import tabla_pivot_pct_femenino

pivot = tabla_pivot_pct_femenino(inv_clean, col_area="NME_GRAN_AREA_PR")
pivot = pivot.drop(columns=["promedio"], errors="ignore")
pivot
""")

code("""fig, ax = plt.subplots(figsize=(12, 5))
sns.heatmap(pivot * 100, annot=True, fmt=".0f",
            cmap="RdYlGn", center=50, vmin=15, vmax=70,
            cbar_kws={"label": "% femenino"}, ax=ax)
ax.set_title("% mujeres por gran area OCDE y convocatoria")
ax.set_xlabel("Convocatoria")
ax.set_ylabel("")
plt.tight_layout()
plt.show()
""")


# =====================================================================
# 10. Diversidad
# =====================================================================
md("""## 10. Diversidad — etnia, discapacidad, víctimas del conflicto

**Hallazgo estructural.** Las tres variables de diversidad sólo empiezan a
registrarse en la convocatoria 2021 (894). En las cinco convocatorias previas
la cobertura es del 0 %. El análisis longitudinal sobre diversidad es
imposible por construcción del formulario.

Para 2021 sí se puede comparar la composición de los investigadores
reconocidos contra la composición poblacional (DANE-CNPV 2018 / RUV 2021).
""")

code("""from analisis.diversidad import (
    cobertura_por_convocatoria, distribucion_categoria, comparar_dane
)

cob = cobertura_por_convocatoria(inv_clean)
cob[["ANO_CONVO_INT", "n_total",
     "ID_VICTIMA_CONFLICTO_pct_cobertura",
     "TXT_GRUPO_ETNICO_pct_cobertura",
     "TXT_POBLACION_DISCA_pct_cobertura"]]
""")

code("""# Subrepresentacion vs poblacion total
inv_2021 = inv_clean[inv_clean["ANO_CONVO_INT"] == 2021]
comp = comparar_dane(inv_2021)
comp
""")

md("""**Caveat metodológico.** La comparación correcta sería contra la
**población con educación superior**, no contra la población total. La brecha
real es probablemente menor a la que muestra esta tabla, pero el patrón se
mantiene: los grupos étnicos numéricamente importantes (afros, indígenas) y
las personas víctimas del conflicto están sub-representadas.
""")


# =====================================================================
# 11. Productividad y categoría
# =====================================================================
md("""## 11. Productividad y categoría

Cruce de los dos datasets por `id_persona_pd ↔ id_persona_pr`. La pregunta:
¿los Senior producen más que los Junior?
""")

code("""from analisis.produccion import (
    cobertura_reconocidos, cobertura_autores_unicos,
    productividad_por_categoria, reconocidos_sin_produccion
)

cov = cobertura_autores_unicos(prod, inv_clean)
for k, v in cov.items():
    print(f"  {k}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")
""")

code("""prod_cat = productividad_por_categoria(prod, inv_clean)
prod_cat.head(20)
""")

md("""**Hallazgo.** La productividad escala con la categoría reconocida:

| Categoría | Productos promedio (carrera) |
|---|---:|
| Junior | 30 |
| Asociado | 65 |
| **Senior** | **121** |
| Emérito | 34 |

Los Eméritos producen menos que los Asociados. Esto **no** es una falla del
sistema: el reconocimiento Emérito queda vitalicio, no exige re-postulación,
y por lo tanto los productos contabilizados en su ventana son los previos a
quedar vitalicio.
""")


# =====================================================================
# 12. Brecha de género en productividad
# =====================================================================
md("""## 12. Brecha de género en productividad

¿La brecha de representación se replica cuando miramos lo que se les
contabiliza producir?
""")

code("""from analisis.produccion import brecha_productividad_genero

brecha = brecha_productividad_genero(prod, inv_clean)
brecha = brecha[~brecha["NME_GRAN_AREA_PR"].isin(["NO REGISTRA", "NO REPORTADO"])]
brecha
""")

md("""**Doble penalización confirmada.** Las mujeres registran menos
productos en promedio en cinco de seis grandes áreas. La única excepción es
**Humanidades**, donde la razón mujeres/hombres es ligeramente mayor a uno.
Las mayores brechas: Ciencias Médicas (−2,95) e Ingeniería (−2,59).

Pocas mujeres entran al sistema **y** a las que entran se les contabiliza
menos producción.
""")


# =====================================================================
# 13. Composición OCDE
# =====================================================================
md("""## 13. Composición de la producción por gran área OCDE

¿Qué rama del conocimiento produce más en Colombia? La respuesta cambia
según se mida en volumen total o por investigador.
""")

code("""import subprocess
subprocess.run(["python3", "scripts/sprint6_ocde_composicion.py"], cwd=ROOT, check=True)
""")

code("""volumen = pd.read_csv(ROOT / "evidencias/ocde_volumen_por_area.csv")
prod_area = pd.read_csv(ROOT / "evidencias/ocde_productividad_por_area.csv")
prod_area
""")

md("""**Lectura cruzada.**

- En volumen total domina **Ciencias Sociales** (585 mil productos).
- En productividad por investigador domina **Ingeniería y Tecnología**
  (67 productos/investigador, contra 47 de Humanidades).
- Humanidades es la menos productiva por investigador pese a ser de las
  áreas con paridad de género. Es decir: la brecha de productividad por
  género no se explica con que las mujeres estén en áreas menos productivas.
""")

code("""composicion = pd.read_csv(ROOT / "evidencias/ocde_composicion_por_area.csv")
# Tabla pivote: tipo de medicion por area
pivot = composicion.pivot_table(
    index="NME_GRAN_AREA_PR",
    columns="NME_TIPO_MEDICION_PD",
    values="pct", fill_value=0).round(1)
pivot
""")


# =====================================================================
# 14. Cierre
# =====================================================================
md("""## 14. Cierre — recomendaciones de política pública

Los doce hallazgos del observatorio se pueden agrupar en cuatro líneas
operativas que MinCiencias podría implementar antes de la siguiente
convocatoria.

### A. Calidad y gobernanza del dato
- Validación previa a la publicación: edad ≤ 100, fecha de convocatoria
  distinta de la de publicación.
- Adopción de la tabla maestra de instituciones que aquí se propone.
- Campo obligatorio de departamento de la institución.

### B. Equidad y diversidad
- Captura obligatoria de etnia, discapacidad y conflicto desde el
  formulario inicial — no sólo desde 2021.
- Comparar representación contra población con educación superior, no
  contra población total.
- Programas focalizados en regiones con baja retención local
  (Cundinamarca, Risaralda, departamentos amazónicos).

### C. Apertura y trazabilidad
- Captura sistemática de doble afiliación en todas las convocatorias.
- Apertura del padrón completo de ScienTI (perfiles activos, no sólo
  reconocidos).
- Apertura del dataset de proyectos evaluados — cerrar el ciclo
  idea–reconocimiento–producto.

### D. Métricas alineadas con la realidad
- Productividad ajustada por categoría, área OCDE y género.
- Reporte de flujos investigador–institución (residencia vs. institución).
- Calendario predecible de convocatorias.

---

**Cierre.** Este observatorio queda como herramienta abierta. El código, los
datasets de evidencia y el tablero interactivo están publicados en el
repositorio `Victor-Diaz-Usta/Min_ciencias`. Cualquier persona puede
reproducir las cifras, pedir aclaraciones, o extender el análisis con fuentes
adicionales.
""")


# =====================================================================
# Guardar
# =====================================================================
def main() -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.11",
        },
        "title": "Manual reproducible — Observatorio MinCiencias",
    }
    salida = DOCS / "manual.ipynb"
    with open(salida, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Notebook generado: {salida}")
    print(f"Celdas totales: {len(cells)}")
    print(f"  Markdown: {sum(1 for c in cells if c['cell_type'] == 'markdown')}")
    print(f"  Codigo:   {sum(1 for c in cells if c['cell_type'] == 'code')}")


if __name__ == "__main__":
    main()
