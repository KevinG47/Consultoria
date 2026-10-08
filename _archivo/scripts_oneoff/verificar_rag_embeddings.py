"""Verificacion final de la implementacion de embeddings.

Comprueba, en procesos separados, que:
  1. La ruta TF-IDF (default) funciona y NO carga torch ni sentence-transformers.
  2. La ruta de embeddings funciona y recupera.
  3. Los dos indices existen, no se pisan y tienen las dimensiones correctas.
  4. El guardia de integridad del corpus detecta una matriz desalineada.
  5. El banco histórico de TF-IDF no cambió (no regresión).
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
DOC = RAIZ / "documentacion_auditoria"
MEM = DOC / "data" / "memoria"
PY = sys.executable


def correr(codigo: str) -> subprocess.CompletedProcess:
    import os
    entorno = dict(os.environ)          # heredar el entorno: quitarlo rompe Winsock
    entorno.update({"PYTHONIOENCODING": "utf-8", "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1"})
    return subprocess.run([PY, "-c", codigo], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=RAIZ, env=entorno)


print("=" * 78)
print("VERIFICACIÓN FINAL — RAG con dos métodos")
print("=" * 78)

# --- 1. TF-IDF sin dependencias pesadas -------------------------------------
print("\n=== 1. Ruta TF-IDF (default) ===")
r = correr("""
import sys
sys.path.insert(0, r'%s')
from memoria import rag
mem = rag.MemoriaSemantica().cargar()
res = mem.consultar('cuantos nodos tiene el grafo', k=2)
print('METODO', mem.metodo)
print('FRAGMENTOS', len(mem.fragmentos))
print('TOP1', res[0]['documento'] + '::' + res[0]['seccion'], res[0]['puntaje'])
print('TORCH_CARGADO', 'torch' in sys.modules)
print('ST_CARGADO', 'sentence_transformers' in sys.modules)
print('TERMINOS', len(mem.terminos_relevantes('cuantos nodos tiene el grafo')))
""" % (DOC / "src"))
assert r.returncode == 0, r.stderr[-1500:]
for linea in r.stdout.strip().splitlines():
    print("   ", linea)
assert "METODO tfidf" in r.stdout
assert "TORCH_CARGADO False" in r.stdout, "la ruta TF-IDF cargó torch"
assert "ST_CARGADO False" in r.stdout, "la ruta TF-IDF cargó sentence-transformers"
print("   OK: el default sigue siendo TF-IDF y no arrastra dependencias pesadas")

# --- 2. embeddings ----------------------------------------------------------
print("\n=== 2. Ruta de embeddings ===")
r = correr("""
import sys
sys.path.insert(0, r'%s')
from memoria import rag
mem = rag.MemoriaSemantica('embeddings').cargar()
res = mem.consultar('cuantos nodos tiene el grafo', k=2)
print('METODO', mem.metodo)
print('MODELO', mem.meta.get('modelo'))
print('DIMENSION', mem.meta.get('dimension'))
print('MATRIZ', mem.matriz.shape)
print('TOP1', res[0]['documento'] + '::' + res[0]['seccion'], res[0]['puntaje'])
print('TERMINOS', mem.terminos_relevantes('x'))
""" % (DOC / "src"))
assert r.returncode == 0, r.stderr[-1500:]
for linea in r.stdout.strip().splitlines():
    print("   ", linea)
assert "METODO embeddings" in r.stdout
assert "DIMENSION 384" in r.stdout
assert "MATRIZ (150, 384)" in r.stdout
assert "TERMINOS []" in r.stdout, "terminos_relevantes debería estar vacío con embeddings"
print("   OK: 150x384 y sin explicabilidad término a término (como se documentó)")

# --- 3. los dos índices coexisten ------------------------------------------
print("\n=== 3. Los dos índices coexisten ===")
for nombre, ruta in [("TF-IDF (rag_indice.json)", MEM / "rag_indice.json"),
                     ("TF-IDF (rag_matriz.npz)", MEM / "rag_matriz.npz"),
                     ("TF-IDF (rag_vectorizer.pkl)", MEM / "rag_vectorizer.pkl"),
                     ("embeddings (rag_indice_embeddings.json)", MEM / "rag_indice_embeddings.json"),
                     ("embeddings (rag_embeddings.npy)", MEM / "rag_embeddings.npy")]:
    print(f"   {nombre:44s} {ruta.stat().st_size/1024:9.1f} KB  {'OK' if ruta.exists() else 'FALTA'}")
    assert ruta.exists()
m_tf = json.loads((MEM / "rag_indice.json").read_text(encoding="utf-8"))
m_em = json.loads((MEM / "rag_indice_embeddings.json").read_text(encoding="utf-8"))
assert m_tf["n_fragmentos"] == m_em["n_fragmentos"] == 150
# El indice de TF-IDF es previo a este cambio: no tiene hash_corpus ni metodo.
if "hash_corpus" in m_tf:
    assert m_tf["hash_corpus"] == m_em["hash_corpus"]
    print("   los dos índices declaran el mismo corpus")
else:
    print("   nota: rag_indice.json es previo (sin campo hash_corpus); "
          "no se reindexa para no perder la advertencia de versión de sklearn")
# El hash declarado por los embeddings debe coincidir con el corpus en disco.
r = correr("""
import sys
sys.path.insert(0, r'%s')
from memoria import rag
frags = rag.construir_fragmentos()
mem = rag.MemoriaSemantica('embeddings').cargar()
print('HASH_ACTUAL', rag.hash_corpus(frags))
print('HASH_INDICE', mem.meta.get('hash_corpus'))
print('COINCIDEN', rag.hash_corpus(frags) == mem.meta.get('hash_corpus'))
""" % (DOC / "src"))
assert r.returncode == 0, r.stderr[-1200:]
print("   ", r.stdout.strip().replace("\n", " | "))
assert "COINCIDEN True" in r.stdout, "el corpus cambió respecto al índice de embeddings"
print("   OK: el índice de embeddings corresponde al corpus actual")

# --- 4. guardia de integridad ----------------------------------------------
print("\n=== 4. Guardia de integridad del corpus ===")
r = correr("""
import sys, json, tempfile, pathlib
sys.path.insert(0, r'%s')
from memoria import config, rag

# El guardia tambien debe saltar cuando el corpus en disco ya no corresponde.
lineas = config.RAG_CHUNKS.read_text(encoding='utf-8').splitlines()
d0 = json.loads(lineas[0]); d0['id'] = 'ALTERADO::test'
lineas[0] = json.dumps(d0, ensure_ascii=False)
tmp = pathlib.Path(tempfile.mkdtemp()) / 'rag_corpus.jsonl'
nl = chr(10)
tmp.write_text(nl.join(lineas) + nl, encoding='utf-8')

config.RAG_CHUNKS = tmp            # se redirige la carga al corpus alterado
mem = rag.MemoriaSemantica('embeddings')
try:
    mem.cargar()
    print('RESULTADO=SIN_ABORTAR')
except RuntimeError as e:
    print('RESULTADO=ABORTA_RUNTIMEEXCEPTION')
    print('MENSAJE=' + str(e)[:90])

# Y con el corpus correcto no debe abortar.
config.RAG_CHUNKS = pathlib.Path(r'%s')
ok = rag.MemoriaSemantica('embeddings').cargar()
print('RESULTADO_CON_CORPUS_BUENO=OK', len(ok.fragmentos))
""" % (DOC / "src", (MEM / "rag_corpus.jsonl").as_posix()))
assert r.returncode == 0, r.stderr[-1500:]
for linea in r.stdout.strip().splitlines():
    print("   ", linea)
assert "RESULTADO=ABORTA_RUNTIMEEXCEPTION" in r.stdout, "el guardia no abortó con el corpus alterado"
assert "RESULTADO_CON_CORPUS_BUENO=OK 150" in r.stdout, "abortó con el corpus correcto"
print("   OK: el guardia aborta con un corpus desalineado y no con el correcto")

# --- 5. no regresión del banco --------------------------------------------
print("\n=== 5. No regresión de TF-IDF en el banco ===")
comp = json.loads((MEM / "comparacion_rag.json").read_text(encoding="utf-8"))
reg = comp["no_regresion_tfidf"]
print(f"   comparado contra {reg['archivo_historico']} (del {reg['fecha_historico']})")
print(f"   preguntas comparadas: {reg['preguntas_comparadas']} · diferencias: {len(reg['diferencias'])}")
assert reg["identico"], reg["diferencias"]
print("   OK: la corrida nueva de TF-IDF es idéntica a la histórica")

print("\n" + "=" * 78)
print("VERIFICACIÓN COMPLETA: TODO OK")
