# Evidencia de ejecución — sistema de memoria del agente

**Fecha de ejecución:** 2026-09-15T16:57:49  
**Commit auditado (HEAD real del clon):** `1528939`  
**Grafo:** 255 nodos / 500 aristas  
**RAG:** 137 fragmentos de 24 documentos (38327 términos)  
**Reglas:** 8 PASA · 3 FALLA · 1 ADVERTENCIA

## Nodos del grafo

| Tipo | Nodos |
|---|---:|
| Commit | 133 |
| ArchivoCodigo | 51 |
| TerminoGlosario | 19 |
| Documento | 13 |
| DocumentoValidacion | 11 |
| Capa | 11 |
| Autor | 11 |
| Criterio | 6 |

## Reglas de validación

| Regla | Descripción | Estado | Detalle |
|---|---|---|---|
| R1 | Cada criterio tiene documento completo Y LITE | **PASA** | 6 criterios revisados; 0 sin el par completo/LITE. |
| R2 | Todo documento completo tiene conclusiones registradas | **PASA** | 6/6 criterios con conclusiones en YAML y sección 05 presente. Secciones muy breves (<50 palabras): 0. |
| R3 | Todo documento LITE tiene veredicto resumido | **FALLA** | 5/6 LITE con veredicto declarado en objetivos.yaml (lite_veredicto) y sección 05 con contenido; 4 sin la palabra literal 'veredicto'. |
| R4 | Todo término del glosario está efectivamente usado en algún documento | **FALLA** | 18/19 términos aparecen en al menos un documento (búsqueda por claves sobre el texto de los 6 criterios, LITE y maestro). |
| R5 | La línea de tiempo documentada coincide con el git log real | **PASA** | git log real=133 commits; commits_timeline.csv=133; coinciden por hash=133; solo en git=0; solo en CSV=0; asunto distinto=0; fecha distinta=0. |
| R6 | Todo archivo de código real está referenciado en el documento del criterio de código | **PASA** | 51/51 archivos reales del repo auditado aparecen en latex/objetivo_3 (Criterio 3). |
| R7 | El commit auditado documentado coincide con el HEAD real del clon | **PASA** | HEAD real=1528939; documentado en 12 proyectos: ['1528939']. |
| R8 | Toda ruta del inventario tiene capa asignada (no cae en 'otro') | **FALLA** | 1 archivo(s) sin capa en capas.yaml. Distribución: {'visualizacion': 2, 'documentacion': 1, 'eda': 1, 'legacy': 13, 'orquestacion': 17, 'transformacion': 1, 'otro': 1, 'analisis': 8, 'ingesta': 3, 'modelo': 2, 'testing': 2}. |
| R9 | Cobertura de fichas de análisis == archivos documentados y reales | **PASA** | inventario=51; archivos reales (git ls-files)=51; fichas en data/analisis_codigo=51. |
| R10 | Integridad referencial del grafo (PDF, documentos y aristas) | **PASA** | 255 nodos y 500 aristas revisados; 0 problema(s). |
| R11 | El índice RAG cubre todo el corpus declarado y responde consultas | **PASA** | documentos en el índice=24; esperados=24; faltan=0; consulta de prueba devolvió 3 fragmento(s). |
| R12 | LITE ≤ 40 % de la sección principal del completo (y sin copias literales) | **ADVERTENCIA** | Pares completo/LITE que incumplen el 40 % en su sección principal: 0; secciones copiadas literalmente entre documentos: 7. |

## Detalle de reglas no aprobadas

### R3 — FALLA: Todo documento LITE tiene veredicto resumido

5/6 LITE con veredicto declarado en objetivos.yaml (lite_veredicto) y sección 05 con contenido; 4 sin la palabra literal 'veredicto'.

```json
{
  "faltantes": [
    {
      "criterio": 3,
      "yaml_veredicto": false,
      "hallazgos_yaml": 0,
      "seccion_05_palabras": 100,
      "menciona_palabra_veredicto": false
    }
  ],
  "sin_palabra_veredicto": [
    {
      "criterio": 1,
      "yaml_veredicto": true,
      "hallazgos_yaml": 2,
      "seccion_05_palabras": 67,
      "menciona_palabra_veredicto": false
    },
    {
      "criterio": 4,
      "yaml_veredicto": true,
      "hallazgos_yaml": 2,
      "seccion_05_palabras": 78,
      "menciona_palabra_veredicto": false
    },
    {
      "criterio": 5,
      "yaml_veredicto": true,
      "hallazgos_yaml": 2,
      "seccion_05_palabras": 52,
      "menciona_palabra_veredicto": false
    },
    {
      "criterio": 6,
      "yaml_veredicto": true,
      "hallazgos_yaml": 2,
      "seccion_05_palabras": 83,
      "menciona_palabra_veredicto": false
    }
  ]
}
```

### R4 — FALLA: Todo término del glosario está efectivamente usado en algún documento

18/19 términos aparecen en al menos un documento (búsqueda por claves sobre el texto de los 6 criterios, LITE y maestro).

```json
{
  "no_usados": [
    "ETL"
  ]
}
```

### R8 — FALLA: Toda ruta del inventario tiene capa asignada (no cae en 'otro')

1 archivo(s) sin capa en capas.yaml. Distribución: {'visualizacion': 2, 'documentacion': 1, 'eda': 1, 'legacy': 13, 'orquestacion': 17, 'transformacion': 1, 'otro': 1, 'analisis': 8, 'ingesta': 3, 'modelo': 2, 'testing': 2}.

```json
{
  "sin_capa": [
    "src/__init__.py"
  ],
  "distribucion": {
    "visualizacion": 2,
    "documentacion": 1,
    "eda": 1,
    "legacy": 13,
    "orquestacion": 17,
    "transformacion": 1,
    "otro": 1,
    "analisis": 8,
    "ingesta": 3,
    "modelo": 2,
    "testing": 2
  }
}
```

### R12 — ADVERTENCIA: LITE ≤ 40 % de la sección principal del completo (y sin copias literales)

Pares completo/LITE que incumplen el 40 % en su sección principal: 0; secciones copiadas literalmente entre documentos: 7.

```json
{
  "ratios": [
    {
      "criterio": 1,
      "principal_completo": 185,
      "principal_lite": 63,
      "principal_pct": 34.1,
      "cumple_40_principal": true,
      "total_completo": 594,
      "total_lite": 487,
      "total_pct": 82.0
    },
    {
      "criterio": 2,
      "principal_completo": 254,
      "principal_lite": 69,
      "principal_pct": 27.2,
      "cumple_40_principal": true,
      "total_completo": 771,
      "total_lite": 552,
      "total_pct": 71.6
    },
    {
      "criterio": 3,
      "principal_completo": 28359,
      "principal_lite": 3660,
      "principal_pct": 12.9,
      "cumple_40_principal": true,
      "total_completo": 29262,
      "total_lite": 4456,
      "total_pct": 15.2
    },
    {
      "criterio": 4,
      "principal_completo": 238,
      "principal_lite": 57,
      "principal_pct": 23.9,
      "cumple_40_principal": true,
      "total_completo": 886,
      "total_lite": 736,
      "total_pct": 83.1
    },
    {
      "criterio": 5,
      "principal_completo": 254,
      "principal_lite": 65,
      "principal_pct": 25.6,
      "cumple_40_principal": true,
      "total_completo": 836,
      "total_lite": 507,
      "total_pct": 60.6
    },
    {
      "criterio": 6,
      "principal_completo": 1947,
      "principal_lite": 86,
      "principal_pct": 4.4,
      "cumple_40_principal": true,
      "total_completo": 2543,
      "total_lite": 569,
      "total_pct": 22.4
    }
  ],
  "duplicados": {
    "relación con los demás criterios este documento se centra en el criter": [
      "objetivo_6::04_relacion",
      "objetivo_6_lite::04_relacion"
    ],
    "conclusiones y recomendaciones del criterio el objetivo del repositori": [
      "objetivo_1::05_conclusiones",
      "objetivo_1_lite::05_conclusiones"
    ],
    "concl
```
