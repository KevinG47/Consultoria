# `_archivo/` — evidencia de trabajo

**Qué es.** El registro de cómo se hizo la auditoría: los scripts de una sola vez
que se escribieron para **verificar** afirmaciones concretas, los logs de la
ejecución del pipeline auditado y las imágenes del control de calidad previo.
No forma parte del entregable, pero es lo que permite **auditar la auditoría**:
cada cifra discutible tiene aquí el script que la midió.

**Qué NO es.** No son utilidades del proyecto (esas están en
`documentacion_auditoria/src/`) ni se ejecutan en el pipeline. Los scripts leen
datos y escriben en `_archivo/` o en la salida estándar; ninguno modifica los
datos fuente.

---

## `scripts_oneoff/` — 31 scripts de verificación puntual

La mayoría se conserva **porque mide una afirmación que se cita en los
documentos**. Los marcados con ● son los que respaldan cifras publicadas.

### Análisis longitudinal y muestreo

| Script | Para qué sirvió |
|---|---|
| ● `verificar_longitudinal.py` | **Verificación independiente** del análisis longitudinal: recalcula las cifras principales sin reutilizar el pipeline. |
| ● `recon_longitudinal.py` | Reconocimiento previo: qué se podía afirmar antes de fijar el método. |
| ● `diagnostico_emerito.py` | Por qué «Investigador Emérito» no aparece como categoría de origen en la muestra (origen del hallazgo del **estado absorbente**: 0 retornos en 251 oportunidades). |
| ● `analizar_inst_filia.py` | Cuantificar si `INST_FILIA` es multivaluado, antes de fijar la semántica del filtro de instituciones. |
| ● `verificar_colapso_genero.py` | Medir el efecto del colapso de género (§7.4 de `metodologia_muestreo.md`): las tres variantes del vector auxiliar, la invariancia del estimador y el efecto sobre la prueba de representatividad. |

### Herramienta de trayectorias (JavaScript, sin navegador)

Se ejecutan con Node y un DOM simulado (`stub_dom.js`), porque la herramienta es
un HTML autocontenido que no se puede probar con `pytest`:

| Script | Para qué sirvió |
|---|---|
| `pruebas_herramienta.js` | Pruebas funcionales de la primera versión. |
| `stub_dom.js` | DOM mínimo para ejecutar el HTML fuera del navegador. |
| `pruebas_dom.js` | Pruebas de montaje y eventos sobre ese DOM. |
| `pruebas_ids_ui.js` | Búsqueda por ID y comportamiento de la interfaz. |
| `pruebas_institucion.js` | Filtro por institución. |
| `pruebas_layout.js` | Corrección del diseño visual (el problema de `ayudaInicial` y el *temporal dead zone*). |
| `resumen_ids_prueba.js` | Resumen de los casos de prueba por ID. |
| ● `verificar_herramienta_final.py` | Verificación final del HTML generado contra el CSV fuente. |

### RAG: TF-IDF y embeddings (decisiones D002, D007, D008)

| Script | Para qué sirvió |
|---|---|
| ● `verificar_rag_embeddings.py` | Verificación de la implementación de embeddings: cobertura de fragmentos, truncados y comparación contra TF-IDF. |
| ● `verificar_granite.py` | Verificación del cambio a Granite R2 (384 dimensiones, contexto de 32 768). |
| ● `sondeo_granite.json` | Resultados del sondeo previo al cambio de modelo. |
| `bench_fp32.json` / `bench_fp32.log` | Medición del coste: `bfloat16` emulado en CPU es **467× más lento** que `float32`; de ahí la conversión forzada a `.float()`. |
| `indexado_granite2.log` | Log de la reindexación con embeddings (1682–1704 s). |

### Auditoría de los documentos LaTeX

| Script | Para qué sirvió |
|---|---|
| ● `paso_citas.py` | Corregir las citas de cifras desactualizadas y la coherencia de lo que afirman. |
| ● `paso_cuentas.py` | Actualizar las citas de palabras y términos tras cambiar el corpus. |
| `check_glosario.py` | Comprobar que cada PDF incluye solo los términos que realmente usa. |
| `glosario_final.py` | Extraer los glosarios completos de los criterios 4 y 6 (completo y LITE). |
| `check_final.py`, `check_final2.py`, `check_orden_final.py` | Verificar el orden canónico por capa y el contexto del carácter `Ã`. |
| `check_bytes.py` | Verificar en bytes el fragmento «SÍ» de los `.tex` generados (problema de codificación). |
| `probar_95.py` | Descartar que el «95» fuera un conteo de archivos: era un doble render de fichas. |
| `extraer_puntos23.py` | Extraer la sección 2 de `objetivo_6_lite.pdf` y los glosarios de los criterios 4 y 6. |
| `fix_crossrefs.py` | Corregir referencias cruzadas internas del Estado del Arte tras reordenar secciones. |

### Utilidades sin dependencias

| Script | Para qué sirvió |
|---|---|
| `extraer_texto_pdf.py` | Extractor de texto de PDF **sin dependencias** (el entorno no tenía `pypdf` ni `pdftotext`): descomprime los flujos `FlateDecode` a mano. |
| `buscar_en_pdf.py` | Busca cadenas en un PDF ignorando espacios (LaTeX inserta espacios por *kerning*). |

---

## `logs_pipeline_auditado/`

| Archivo | Qué es |
|---|---|
| `ejecucion_log.txt` | **Log crudo** de ejecutar los 16 scripts `sprint*` del repositorio auditado en un clon fresco. Codificación **mixta** (cabecera UTF-8, cuerpos UTF-16LE): leerlo como UTF-8 hace que las líneas `EXIT=` no aparezcan. |
| `errores_ejecucion.txt` | Tracebacks de los 6 scripts que fallaron, extraídos del log anterior. |
| `pip_install*.log` | Instalación de dependencias (3 intentos; el venv dentro de OneDrive falla por longitud de ruta). |
| `dependencias_latex.txt` | Paquetes de TeX Live instalados con `tlmgr`. |

Reproducir la tabla de resultados y los tracebacks:

```bash
python documentacion_auditoria/src/parsear_log.py --cotejar   # 10 OK / 6 ERROR + cotejo con el CSV
python documentacion_auditoria/src/extraer_errores.py          # regenera errores_ejecucion.txt
```

La tabla curada vive en `documentacion_auditoria/data/ejecucion_resumen.csv` y
coincide con el log en los 16 scripts. Las causas de los 6 fallos están explicadas
en `datos_originales/ERRATA.md` §E5: ninguna es un error de lógica, todas son
entradas ausentes o dependencias no declaradas.

---

## `qa_primera_revision/`

Control de calidad visual de la primera versión de los PDFs (agosto de 2026):
capturas de páginas de `maestro_auditoria` y `objetivo_1`, texto extraído con
`extraer_texto_pdf.py` y dos pasajes concretos citados en la revisión. Se conserva
como evidencia del control previo a la entrega.
