"""Verificacion del cambio a Granite R2.

Comprueba, en procesos separados para no contaminar el estado:
  1. El indice de embeddings es de Granite, 150x384, y declara el truncamiento.
  2. La ruta TF-IDF (default) sigue funcionando y NO carga torch.
  3. El guardia de integridad detecta un corpus desalineado (y no aborta con el bueno).
  4. Los dos indices conviven y se reporta el peso total de los artefactos.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
MEM = DOC / "data" / "memoria"
PY = sys.executable


def correr(codigo: str) -> subprocess.CompletedProcess:
    entorno = dict(os.environ)
    entorno.update({"PYTHONIOENCODING": "utf-8", "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1"})
    return subprocess.run([PY, "-c", codigo], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=RAIZ, env=entorno)


print("=" * 78)
print("VERIFICACIÓN — RAG con Granite R2")
print("=" * 78)

# --- 1. indice de embeddings -------------------------------------------------
print("\n=== 1. Índice de embeddings ===")
meta = json.loads((MEM / "rag_indice_embeddings.json").read_text(encoding="utf-8"))
tr = meta.get("truncamiento", {})
print(f"   modelo          : {meta.get('modelo')}")
print(f"   dimension       : {meta.get('dimension')}")
print(f"   fragmentos      : {meta.get('n_fragmentos')}")
print(f"   max_seq_length  : {tr.get('max_seq_length')}")
print(f"   truncados       : {tr.get('n_exceden')} de {tr.get('n_fragmentos')} "
      f"({tr.get('pct_exceden')} %)")
print(f"   cobertura       : {tr.get('cobertura_pct')} %")
print(f"   tokens max      : {tr.get('tokens_max')}")
print(f"   tiempo vector.  : {meta.get('tiempo_generacion_segundos')} s en "
      f"{tr.get('lotes')} lotes")
assert meta["modelo"] == "ibm-granite/granite-embedding-97m-multilingual-r2", meta["modelo"]
assert meta["dimension"] == 384
assert meta["n_fragmentos"] == 150
assert tr.get("max_seq_length") == 32768
assert tr.get("n_exceden", 99) <= 3, "demasiados fragmentos truncados"
print("   OK: es Granite, 384 dimensiones, 150 fragmentos, truncamiento acotado")

# --- 2. ruta TF-IDF sin dependencias pesadas --------------------------------
print("\n=== 2. Ruta TF-IDF (default) ===")
r = correr("""
import sys
sys.path.insert(0, r'%s')
from memoria import rag
mem = rag.MemoriaSemantica().cargar()
res = mem.consultar('cuantos nodos tiene el grafo', k=2)
print('METODO', mem.metodo)
print('FRAGMENTOS', len(mem.fragmentos))
print('TOP1', res[0]['documento'] + '::' + res[0]['seccion'], res[0]['puntaje'])
print('TORCH', 'torch' in sys.modules, 'ST', 'sentence_transformers' in sys.modules)
""" % (DOC / "src"))
assert r.returncode == 0, r.stderr[-1200:]
for linea in r.stdout.strip().splitlines():
    print("   ", linea)
assert "METODO tfidf" in r.stdout
assert "TORCH False ST False" in r.stdout, "la ruta TF-IDF cargó dependencias pesadas"
print("   OK: el default sigue siendo TF-IDF y no arrastra torch")

# --- 3. ruta Granite ---------------------------------------------------------
print("\n=== 3. Ruta de embeddings (Granite) ===")
r = correr("""
import sys
sys.path.insert(0, r'%s')
from memoria import rag
mem = rag.MemoriaSemantica('embeddings').cargar()
res = mem.consultar('cuantos nodos tiene el grafo', k=1)
print('METODO', mem.metodo)
print('MATRIZ', mem.matriz.shape, mem.matriz.dtype)
print('TOP1', res[0]['documento'] + '::' + res[0]['seccion'], round(res[0]['puntaje'], 4))
print('TERMINOS', mem.terminos_relevantes('x'))
""" % (DOC / "src"))
assert r.returncode == 0, r.stderr[-1500:]
for linea in r.stdout.strip().splitlines():
    print("   ", linea)
assert "MATRIZ (150, 384) float32" in r.stdout, "matriz inesperada"
assert "TERMINOS []" in r.stdout
print("   OK: matriz 150x384 float32 y sin explicabilidad término a término")

# --- 4. guardia de integridad ------------------------------------------------
print("\n=== 4. Guardia de integridad del corpus ===")
r = correr("""
import sys, json, tempfile, pathlib
sys.path.insert(0, r'%s')
from memoria import config, rag
lineas = config.RAG_CHUNKS.read_text(encoding='utf-8').splitlines()
d0 = json.loads(lineas[0]); d0['id'] = 'ALTERADO::test'
lineas[0] = json.dumps(d0, ensure_ascii=False)
nl = chr(10)
tmp = pathlib.Path(tempfile.mkdtemp()) / 'rag_corpus.jsonl'
tmp.write_text(nl.join(lineas) + nl, encoding='utf-8')
config.RAG_CHUNKS = tmp
mem = rag.MemoriaSemantica('embeddings')
try:
    mem.cargar()
    print('RESULTADO=SIN_ABORTAR')
except RuntimeError:
    print('RESULTADO=ABORTA')
config.RAG_CHUNKS = pathlib.Path(r'%s')
ok = rag.MemoriaSemantica('embeddings').cargar()
print('BUENO=OK', len(ok.fragmentos))
""" % (DOC / "src", (MEM / "rag_corpus.jsonl").as_posix()))
assert r.returncode == 0, r.stderr[-1200:]
for linea in r.stdout.strip().splitlines():
    print("   ", linea)
assert "RESULTADO=ABORTA" in r.stdout, "el guardia no abortó con el corpus alterado"
assert "BUENO=OK 150" in r.stdout
print("   OK: aborta con corpus desalineado y no con el correcto")

# --- 5. pesos ----------------------------------------------------------------
print("\n=== 5. Artefactos ===")
tot = 0
for nombre in ["rag_indice.json", "rag_matriz.npz", "rag_vectorizer.pkl",
               "rag_indice_embeddings.json", "rag_embeddings.npy",
               "resultados_banco_tfidf.json", "resultados_banco_embeddings.json",
               "comparacion_rag.json", "comparacion_rag_minilm.json"]:
    p = MEM / nombre
    kb = p.stat().st_size / 1024 if p.exists() else 0
    tot += kb
    print(f"   {nombre:36s} {kb:9.1f} KB")
print(f"   {'TOTAL':36s} {tot:9.1f} KB ({tot/1024:.2f} MB)")
nuevos = sum((MEM / x).stat().st_size for x in
             ["rag_indice_embeddings.json", "rag_embeddings.npy"] if (MEM / x).exists())
print(f"   artefactos del índice de embeddings: {nuevos/1024:.1f} KB")
assert (MEM / "rag_embeddings.npy").exists(), "falta la matriz de embeddings"

print("\n" + "=" * 78)
print("VERIFICACIÓN COMPLETA: TODO OK")
