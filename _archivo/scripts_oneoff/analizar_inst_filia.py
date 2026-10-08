"""INST_FILIA es multivaluado? Se cuantifica antes de fijar la semantica del filtro."""
import sys
from collections import Counter
from pathlib import Path
import pandas as pd

for _f in (sys.stdout, sys.stderr):
    if hasattr(_f, "reconfigure"):
        _f.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
CSV = RAIZ / "Datos" / "Investigadores_Reconocidos_por_convocatoria_20261006.csv"

partes = [t for t in pd.read_csv(CSV, dtype=str, keep_default_na=False, chunksize=50_000,
                                 usecols=["ID_PERSONA_PR", "INST_FILIA"])]
df = pd.concat(partes, ignore_index=True)

serie = df["INST_FILIA"].str.strip()
vacio = (serie == "").sum()
print(f"registros: {len(df):,}".replace(",", " "))
print(f"  vacios: {vacio:,}".replace(",", " "))
print(f"  con texto: {(serie != '').sum():,}".replace(",", " "))

print("\n=== posibles separadores multivaluados ===")
for sep, etq in [(" | ", "espacio-pipe-espacio"), ("|", "pipe"), (";", "punto y coma"),
                 (" y ", "' y '"), (", ", "coma"), ("/", "barra")]:
    n = int(serie.str.contains(sep, regex=False).sum())
    print(f"  {etq:22s} ({sep!r:8s}) en {n:6d} registros")

print("\n=== valores distintos ===")
uniq = sorted({v for v in serie if v})
print(f"  valores distintos de INST_FILIA: {len(uniq):,}".replace(",", " "))
con_pipe = [v for v in uniq if " | " in v]
print(f"  de esos, contienen ' | ': {len(con_pipe):,}".replace(",", " "))

comp = Counter()
for v in uniq:
    for c in v.split(" | "):
        c = c.strip()
        if c:
            comp[c] += 1
print(f"  componentes al partir por ' | ': {len(comp):,}".replace(",", " "))
multi = [v for v in uniq if len([c for c in v.split(' | ') if c.strip()]) > 1]
print(f"  valores con mas de un componente: {len(multi):,}".replace(",", " "))

print("\n=== cuantos componentes por valor ===")
ncomp = Counter(len([c for c in v.split(" | ") if c.strip()]) for v in uniq)
for k in sorted(ncomp):
    print(f"  {k} componente(s): {ncomp[k]:6,d}".replace(",", " "))

print("\n=== ejemplos de valores multivaluados ===")
for v in multi[:12]:
    print("  -", v)

print("\n=== impacto en el filtro por institucion ===")
objetivo = "UNIVERSIDAD INDUSTRIAL DE SANTANDER"
sub = serie.str.contains(objetivo, regex=False)
print(f"  registros que CONTIENEN el texto (subcadena cruda): {int(sub.sum()):,}".replace(",", " "))
pers_sub = df.loc[sub, "ID_PERSONA_PR"].nunique()
print(f"  personas: {pers_sub:,}".replace(",", " "))

def es_componente(v):
    return objetivo in [c.strip() for c in v.split(" | ")]

mask_comp = serie.map(es_componente)
print(f"  registros donde es un COMPONENTE exacto:            {int(mask_comp.sum()):,}".replace(",", " "))
pers_comp = df.loc[mask_comp, "ID_PERSONA_PR"].nunique()
print(f"  personas: {pers_comp:,}".replace(",", " "))
print(f"  diferencia: {pers_sub - pers_comp:,} personas solo por mencionar la institucion "
      f"junto a otras".replace(",", " "))
