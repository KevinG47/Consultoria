diff --git a/README.md b/README.md
index ff92a73..4c0bdd8 100644
--- a/README.md
+++ b/README.md
@@ -16,7 +16,7 @@ auditado original.**
 
 | Carpeta / archivo | Qué es | Empieza por |
 |---|---|---|
-| `datos_originales/` | Los datos: el CSV fuente y la copia íntegra del repositorio auditado (commit `1528939`) con manifiesto SHA-256 | `datos_originales/README.md` |
+| `datos_originales/` | Los datos y **las dos copias** del repositorio auditado: el CSV fuente, la copia *verbatim* del commit `1528939` y `repo_mejorado/`, el mismo código con los 30 arreglos aplicados | `datos_originales/README.md` |
 | `documentacion_auditoria/` | El sistema de auditoría: pipeline, documentos LaTeX, PDFs, memoria del agente y las 17 reglas | `documentacion_auditoria/README.md` |
 | `documentacion_auditoria/metodologia_muestreo.md` | **Metodología estadística**: EDA, muestreo, post-estratificación, GREG, diagnósticos y supuestos | — |
 | `documentacion_auditoria/analisis_longitudinal.md` | **Análisis del panel**: retención, transiciones, validez de la muestra y de los estimadores | — |
@@ -65,6 +65,22 @@ python -m memoria validar                     # 17 reglas (exit 1 si alguna FALL
 python -m memoria evidencia                   # informe legible de la última corrida
 ```
 
+Las **dos copias del repositorio auditado** se verifican y se reconstruyen aparte:
+
+```bash
+# ── Verificar la evidencia y reconstruir el código mejorado ────────────────
+python datos_originales/verificar_hashes.py            # repo_auditado: 236/236 hashes idénticos
+python datos_originales/construir_repo_mejorado.py     # repo_mejorado = repo_auditado + estructura
+python datos_originales/aplicar_arreglos.py            # aplica los 30 arreglos declarados
+python datos_originales/verificar_arreglos.py          # comprueba: 0 fallos
+python datos_originales/probar_librerias_reales.py     # los 6 scripts arreglados, con librerías reales
+python datos_originales/probar_inventario_completo.py  # los 51 artefactos del inventario
+```
+
+> El orden importa: primero la integridad de la evidencia, luego construir, luego
+> aplicar y al final verificar. Los dos últimos **ejecutan** el código en una copia
+> desechable y reportan lo que ven; no modifican `repo_mejorado/`.
+
 > El paso 0 es la única preparación: `rag_corpus.jsonl`, `rag_matriz.npz` y
 > `rag_vectorizer.pkl` no se versionan porque se regeneran en segundos. Todo lo
 > demás —incluidos los cachés de git que sostienen las reglas R5, R6 y R9— **sí**
@@ -85,6 +101,9 @@ solo lectura sobre los datos).
 | **Compilación** | `compilar.py` compila **sin `--forzar`**: la puerta de reglas no aborta |
 | Commit auditado | `1528939` |
 | Verificación de la copia | 236/236 archivos idénticos al commit (`datos_originales/verificar_hashes.py`) |
+| **Código mejorado** | `repo_mejorado/`: **30 arreglos** aplicados y verificados (`verificar_arreglos.py` → 0 fallos) |
+| **Lock de dependencias** | `poetry check --lock` → **exit 0**; `poetry install --dry-run` resuelve **153 paquetes** |
+| **Ejecución del código** | **51 artefactos** probados: con las versiones del lock **0 fallos**; con versiones modernas 3 fallos, los tres por dependencias ausentes del entorno y **0 por *breaking change*** |
 
 Las reglas R1–R17 cubren: par completo/LITE, conclusiones, veredictos, glosario,
 línea de tiempo contra `git log`, cobertura del código auditado, commit auditado,
@@ -134,15 +153,45 @@ son fuente LaTeX, datos o material de fases previas.
 
 ---
 
-## El repositorio auditado
+## El repositorio auditado y su versión mejorada
 
 El proyecto audita el repositorio público
 [`ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8`](https://github.com/ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8)
 (commit `1528939`). Su contenido versionado —236 archivos— está copiado **byte a
 byte** en `datos_originales/repo_auditado/`, con manifiesto SHA-256 y verificación
 reproducible, junto con las **contradicciones conocidas** del proyecto auditado en
-`datos_originales/ERRATA.md` (entre ellas la de «22 vs 19 vs 10 atípicos de edad»,
-que arrastra un matiz importante de la decisión D010).
+`datos_originales/ERRATA.md` (seis entradas, E1–E6: la de «22 vs 19 vs 10 atípicos
+de edad», que arrastra un matiz importante de la decisión D010; el consolidado que
+cubre 3 de 6 convocatorias; el `poetry.lock` que no corresponde a su
+`pyproject.toml`…).
+
+### `datos_originales/` — qué hay y para qué sirve
+
+| Contenido | Qué es | Cómo se usa |
+|---|---|---|
+| `repo_auditado/` | **Evidencia.** Los 236 archivos del commit `1528939`, byte a byte | Se consulta y se cita; **no se edita nunca** |
+| `repo_mejorado/` | **Código de trabajo.** El mismo código con **30 arreglos** aplicados y 6 archivos nuevos | Se reconstruye con los scripts de abajo; **no se edita a mano** |
+| `datos_fuente/` | El CSV de datos.gov.co (77 237 registros) que alimenta nuestro análisis | Solo lectura |
+| `manifiesto_sha256.csv` | SHA-256 de los 236 archivos de `repo_auditado/` | Lo comprueba `verificar_hashes.py` |
+| `ERRATA.md` | Las **contradicciones conocidas** del proyecto auditado (E1–E6) | Leer antes de citar cualquier cifra del auditado |
+| `README.md` | Procedencia, hashes y el orden correcto de los scripts | — |
+
+### `datos_originales/repo_mejorado/` — el entregable de código
+
+Es el repositorio auditado **con los defectos corregidos**, listo para el próximo
+grupo. Cada arreglo está declarado y probado:
+
+- **`datos_originales/repo_mejorado/CHANGELOG.md`** documenta los **30 arreglos**
+  (bloques A–J), cada uno con su cita de la ficha del auditado, qué se cambió y cómo
+  se verificó. **Es el documento que hay que leer primero.**
+- `datos_originales/repo_mejorado/README.md` explica qué funciona ya y cómo
+  ejecutarlo.
+- **`datos_originales/repo_mejorado/poetry.lock`** fija las dependencias y **pasa
+  `poetry check --lock`**; el del auditado no, porque le faltaban 7 dependencias
+  declaradas (ERRATA **E6**).
+- No se edita a mano: `construir_repo_mejorado.py` + `aplicar_arreglos.py` lo
+  regeneran, y `verificar_arreglos.py` comprueba que sigue cuadrando (los tres, en
+  `datos_originales/`).
 
 El clon local **no se versiona**: pesa 441 MB, de los que 383,8 MB son su entorno
 virtual. Solo se necesita para **re-extraer** la copia
@@ -156,11 +205,16 @@ virtual. Solo se necesita para **re-extraer** la copia
 ```
 consultoria/
 ├── README.md                        ← este archivo
-├── datos_originales/                ← DATOS: CSV fuente + copia del repo auditado
-│   ├── README.md / ERRATA.md        ← procedencia, hashes y contradicciones conocidas
+├── datos_originales/                ← DATOS + las dos copias del repo auditado
+│   ├── README.md / ERRATA.md        ← procedencia, hashes y contradicciones (E1–E6)
 │   ├── manifiesto_sha256.csv        ← 236 hashes verificables
-│   ├── repo_auditado/               ← 236 archivos del commit 1528939, verbatim
-│   └── datos_fuente/                ← CSV de datos.gov.co (77 237 registros)
+│   ├── repo_auditado/               ← EVIDENCIA: 236 archivos del commit 1528939, verbatim
+│   ├── repo_mejorado/               ← CÓDIGO: los mismos 236 con 30 arreglos + CHANGELOG.md
+│   ├── datos_fuente/                ← CSV de datos.gov.co (77 237 registros)
+│   ├── construir_repo_mejorado.py · aplicar_arreglos.py · verificar_arreglos.py
+│   ├── verificar_hashes.py · extraer_repo_auditado.py · fs_robusto.py
+│   ├── probar_librerias_reales.py · probar_inventario_completo.py
+│   └── reporte_ejecucion_51_poetry.csv · reporte_ejecucion_51_moderno.csv
 ├── documentacion_auditoria/         ← SISTEMA DE AUDITORÍA
 │   ├── README.md                    ← documentación interna y cómo reproducir
 │   ├── metodologia_muestreo.md      ← metodología estadística (EDA, PS, GREG, §7 diagnósticos)
