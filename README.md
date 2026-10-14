# Consultoría Estadística USTA · 2026-II
## Auditoría estadística reproducible del sistema de reconocimiento de investigadores de MinCiencias (2013–2021)

**Equipo:** Kevin Leonardo Chaparro Reyes · Valentina Muñoz Palma · Paula Margarita Triana Ancinez
**Asignatura:** Consultoría Estadística — Universidad Santo Tomás · **Modalidad:** proyecto con datos abiertos

---

## ▶ Empieza aquí

Este repositorio contiene **todo** lo necesario para reproducir y continuar el
proyecto: los datos fuente, una copia verbatim del repositorio auditado, el
pipeline de análisis, los documentos metodológicos y un sistema de validación
automática de 17 reglas. **No necesitas clonar ni consultar el repositorio
auditado original.**

| Carpeta / archivo | Qué es | Empieza por |
|---|---|---|
| `datos_originales/` | Los datos: el CSV fuente y la copia íntegra del repositorio auditado (commit `1528939`) con manifiesto SHA-256 | `datos_originales/README.md` |
| `documentacion_auditoria/` | El sistema de auditoría: pipeline, documentos LaTeX, PDFs, memoria del agente y las 17 reglas | `documentacion_auditoria/README.md` |
| `documentacion_auditoria/metodologia_muestreo.md` | **Metodología estadística**: EDA, muestreo, post-estratificación, GREG, diagnósticos y supuestos | — |
| `documentacion_auditoria/analisis_longitudinal.md` | **Análisis del panel**: retención, transiciones, validez de la muestra y de los estimadores | — |
| `documentacion_auditoria/comparacion_tfidf_vs_embeddings.md` | **Comparación de los dos métodos de recuperación** del RAG (TF-IDF vs. embeddings Granite) | — |
| `documentacion_auditoria/data/memoria/herramienta_trayectorias.html` | **Visor interactivo** del panel: consulta por ID, institución, área o categoría (se abre con doble clic) | — |
| `entregables_2Corte/` | Entregas 1–5 del segundo corte (PDF) | — |
| `ENTREGA_1/` | Anteproyecto, diapositivas, guía de estudio y tarjetas entregados | — |
| `_archivo/` | Scripts de una sola vez y logs del pipeline auditado (evidencia de trabajo) | `_archivo/README.md` |
| `DECLARACION_IA_Y_REPARTO.md` | Declaración de uso de IA y reparto del trabajo | — |
| `informe_consultoria_observatorio_minciencias.md` | Diagnóstico técnico de la fase 2026-I (antecedente, **no** es entregable) | — |

---

## Reproducir el análisis

Requiere **Python 3.11+** con `pandas`, `numpy`, `scipy`, `scikit-learn`,
`matplotlib`, `networkx`, `PyYAML` (y `pyvis` para el grafo interactivo). No se
necesita `statsmodels`: las pruebas estadísticas están implementadas en el
proyecto.

```bash
# ── Desde la RAÍZ del repositorio ───────────────────────────────────────────
# 1. Análisis, en este orden (cada paso escribe sus cifras en data/memoria/)
python documentacion_auditoria/src/analisis_longitudinal.py     # panel, retención, transiciones
python documentacion_auditoria/src/eda_longitudinal.py          # EDA  (metodología, Parte 1)
python documentacion_auditoria/src/estimadores_longitudinal.py  # PS y GREG (Partes 2-3)
python documentacion_auditoria/src/diagnosticos_greg.py         # diagnósticos y g-weights (§7)

# 2. Documentos metodológicos (se generan a partir de los JSON del paso 1)
python documentacion_auditoria/src/generar_metodologia_muestreo.py
python documentacion_auditoria/src/generar_analisis_longitudinal.py

# 3. Visor interactivo del panel
python documentacion_auditoria/src/construir_herramienta.py

# 4. PDFs (lleva la puerta de validación: aborta si alguna regla FALLA)
python documentacion_auditoria/src/compilar.py

# ── El CLI de memoria se ejecuta desde documentacion_auditoria/src/ ─────────
cd documentacion_auditoria/src
python -m memoria indexar     # OBLIGATORIO la primera vez: el índice no se versiona
python -m memoria consultar "tema" -k 5
python -m memoria antes-de-redactar "tema"    # RAG antes de escribir (queda en bitácora)
python -m memoria grafo                       # memoria estructural (+ --refrescar-git con clon)
python -m memoria validar                     # 17 reglas (exit 1 si alguna FALLA)
python -m memoria evidencia                   # informe legible de la última corrida
```

> El paso 0 es la única preparación: `rag_corpus.jsonl`, `rag_matriz.npz` y
> `rag_vectorizer.pkl` no se versionan porque se regeneran en segundos. Todo lo
> demás —incluidos los cachés de git que sostienen las reglas R5, R6 y R9— **sí**
> está versionado, de modo que el repositorio funciona sin el clon auditado.

Los scripts escriben en `documentacion_auditoria/data/memoria/`; el CSV fuente se
lee de `datos_originales/datos_fuente/` y **nunca se modifica** (el proyecto es de
solo lectura sobre los datos).

---

## Estado del sistema

| | |
|---|---|
| **Reglas de validación** | **15 PASA · 0 FALLA · 2 ADVERTENCIA** (17 reglas) |
| Advertencias | **R12** (solapamiento completo/LITE) y **R15** (excepción declarada de la decisión D002) |
| **Compilación** | `compilar.py` compila **sin `--forzar`**: la puerta de reglas no aborta |
| Commit auditado | `1528939` |
| Verificación de la copia | 236/236 archivos idénticos al commit (`datos_originales/verificar_hashes.py`) |

Las reglas R1–R17 cubren: par completo/LITE, conclusiones, veredictos, glosario,
línea de tiempo contra `git log`, cobertura del código auditado, commit auditado,
capas, fichas de análisis, integridad del grafo, cobertura del índice RAG,
proporción LITE, frescura del índice, contradicciones numéricas, coherencia de
decisiones, trazabilidad y cifras del sistema. Detalle en
`documentacion_auditoria/README.md`.

### Decisiones de diseño

Están en **`documentacion_auditoria/data/memoria/decisiones.yaml`** (D001–D010),
con justificación, alternativas descartadas, evidencia medida e implementación
verificable. R15 comprueba que cada decisión vigente coincide con el código.

| | Tema | Decisión |
|---|---|---|
| D001 | memoria semántica | Usar RAG para la memoria del corpus documental |
| D002 | técnica de recuperación | TF-IDF en vez de embeddings *(superada; se conserva como respaldo declarado)* |
| D003 | memoria estructural | Grafo en memoria con `networkx`, sin motor externo |
| D004 | herramienta externa | Descartar Obsidian del pipeline automatizado |
| D005 | fuente de verdad | Extender el grafo con datos en vivo del repositorio auditado |
| D006 | validación | Validación como puerta previa a la compilación |
| D007 | técnica de recuperación | Migrar el RAG a embeddings locales (Granite R2, 384 d) |
| D008 | indexación del corpus | Corregir el indexador de markdown |
| D009 | trazabilidad de cifras | Cerrar el ciclo de D008 y añadir la regla R17 |
| D010 | cifras de edad | Conservar la cifra «22 registros con edad > 100» y aclararla oralmente |

Fuentes externas consultadas: `documentacion_auditoria/data/memoria/fuentes_externas.yaml` (4, con URL verificada).

---

## ⚠️ PARA EL DOCENTE — qué se califica

Todo lo calificable está en **`documentacion_auditoria/pdf/`**. Los demás archivos
son fuente LaTeX, datos o material de fases previas.

| Qué es | Archivo (PDF) | Bloque de la rúbrica |
|---|---|---|
| **Documento (anteproyecto)** | `documentacion_auditoria/pdf/anteproyecto.pdf` | **Documento (D1–D5) · 40 %** — 8 págs. de cuerpo, APA 7, declaración de IA en §6 |
| **Diapositivas de la sustentación** | `documentacion_auditoria/pdf/diapositivas_anteproyecto.pdf` | **Sustentación (S1–S3) · 60 %** (apoyo visual, 10 láminas / 10 min) |
| Guía de estudio (apoyo) | `documentacion_auditoria/pdf/guia_estudio.pdf` | repaso: reparto, frases clave, banco de preguntas |
| Tarjetas frase por frase (apoyo) | `documentacion_auditoria/pdf/tarjetas_sustentacion.pdf` | una página por integrante para ensayar |

> La **declaración de uso de IA** está en la **sección 6.2 del anteproyecto**, con
> los informes de validación en `documentacion_auditoria/data/validacion/`.
> **Declaración ampliada y verificable (S3):** [`DECLARACION_IA_Y_REPARTO.md`](DECLARACION_IA_Y_REPARTO.md).

---

## El repositorio auditado

El proyecto audita el repositorio público
[`ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8`](https://github.com/ustadistica/Observatorio_Ministerio_de_Ciencias_Grupo8)
(commit `1528939`). Su contenido versionado —236 archivos— está copiado **byte a
byte** en `datos_originales/repo_auditado/`, con manifiesto SHA-256 y verificación
reproducible, junto con las **contradicciones conocidas** del proyecto auditado en
`datos_originales/ERRATA.md` (entre ellas la de «22 vs 19 vs 10 atípicos de edad»,
que arrastra un matiz importante de la decisión D010).

El clon local **no se versiona**: pesa 441 MB, de los que 383,8 MB son su entorno
virtual. Solo se necesita para **re-extraer** la copia
(`datos_originales/extraer_repo_auditado.py`) o para refrescar los cachés de git
(`python -m memoria grafo --refrescar-git`).

---

## Estructura

```
consultoria/
├── README.md                        ← este archivo
├── datos_originales/                ← DATOS: CSV fuente + copia del repo auditado
│   ├── README.md / ERRATA.md        ← procedencia, hashes y contradicciones conocidas
│   ├── manifiesto_sha256.csv        ← 236 hashes verificables
│   ├── repo_auditado/               ← 236 archivos del commit 1528939, verbatim
│   └── datos_fuente/                ← CSV de datos.gov.co (77 237 registros)
├── documentacion_auditoria/         ← SISTEMA DE AUDITORÍA
│   ├── README.md                    ← documentación interna y cómo reproducir
│   ├── metodologia_muestreo.md      ← metodología estadística (EDA, PS, GREG, §7 diagnósticos)
│   ├── analisis_longitudinal.md     ← análisis del panel y validación de la muestra
│   ├── comparacion_tfidf_vs_embeddings.md
│   ├── pdf/                         ← ★ TODOS LOS PDF ENTREGABLES (lo que se califica)
│   ├── latex/                       ← fuentes LaTeX por proyecto (Overleaf-ready)
│   ├── zip_overleaf/                ← ZIPs listos para subir a Overleaf
│   ├── data/                        ← fichas, validaciones y memoria del agente
│   │   ├── analisis_codigo/         ←   51 fichas de los archivos auditados
│   │   ├── validacion/              ←   informes de los agentes validadores
│   │   └── memoria/                 ←   RAG, grafo, 17 reglas, decisiones, visor HTML
│   └── src/                         ← pipeline, generadores y sistema de memoria
├── entregables_2Corte/              ← entregas 1–5 del segundo corte
├── ENTREGA_1/                       ← PDFs entregados del anteproyecto
├── _archivo/                        ← scripts de una sola vez y logs del pipeline
├── DECLARACION_IA_Y_REPARTO.md
├── informe_consultoria_observatorio_minciencias.md   (fase 2026-I, antecedente)
└── Rúbrica — Entrega 1 · Anteproyecto.pdf
```
