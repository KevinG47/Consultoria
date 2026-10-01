# Evidencia de ejecución — sistema de memoria del agente

**Fecha de ejecución:** 2026-10-01T17:36:03  
**Commit auditado (HEAD real del clon):** `1528939`  
**Grafo:** 255 nodos / 498 aristas  
**RAG:** 150 fragmentos de 25 documentos (45805 términos)  
**Reglas:** 15 PASA · 1 FALLA · 1 ADVERTENCIA

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
| R3 | Todo documento LITE tiene veredicto resumido | **PASA** | 6/6 LITE con veredicto declarado en objetivos.yaml (lite_veredicto) y sección 05 con contenido; 0 sin la palabra literal 'veredicto'. |
| R4 | Todo término del glosario está efectivamente usado en algún documento | **PASA** | 19/19 términos aparecen en al menos un documento (búsqueda por claves sobre el texto de los 6 criterios, LITE y maestro). |
| R5 | La línea de tiempo documentada coincide con el git log real | **PASA** | git log real=133 commits; commits_timeline.csv=133; coinciden por hash=133; solo en git=0; solo en CSV=0; asunto distinto=0; fecha distinta=0. |
| R6 | Todo archivo de código real está referenciado en el documento del criterio de código | **PASA** | 51/51 archivos reales del repo auditado aparecen en latex/objetivo_3 (Criterio 3). |
| R7 | El commit auditado documentado coincide con el HEAD real del clon | **PASA** | HEAD real=1528939; documentado en 12 proyectos: ['1528939']. |
| R8 | Todo archivo tiene capa asignada por una regla explícita en capas.yaml | **PASA** | 0 archivo(s) sin regla explícita; clasificados explícitamente como 'otro': 1. Distribución: {'visualizacion': 2, 'documentacion': 1, 'eda': 1, 'legacy': 13, 'orquestacion': 17, 'transformacion': 1, 'otro': 1, 'analisis': 8, 'ingesta': 3, 'modelo': 2, 'testing': 2}. |
| R9 | Cobertura de fichas de análisis == archivos documentados y reales | **PASA** | inventario=51; archivos reales (git ls-files)=51; fichas en data/analisis_codigo=51. |
| R10 | Integridad referencial del grafo (PDF, documentos y aristas) | **PASA** | 255 nodos y 498 aristas revisados; 0 problema(s). |
| R11 | El índice RAG cubre todo el corpus declarado y responde consultas | **PASA** | documentos en el índice=25; esperados=25; faltan=0; consulta de prueba devolvió 3 fragmento(s). |
| R12 | LITE ≤ 40 % de la sección principal del completo (y sin copias literales) | **ADVERTENCIA** | Pares completo/LITE que incumplen el 40 % en su sección principal: 0; secciones copiadas literalmente entre documentos: 1. |
| R13 | El índice RAG está actualizado respecto a las fuentes | **PASA** | Índice al día: posterior al documento fuente más reciente por 0.3 min. |
| R14 | Sin contradicciones numéricas entre documentos | **PASA** | 7/7 comprobaciones numéricas OK (cifras de commits/archivos/scripts/criterios, preguntas enumeradas y cobertura). |
| R15 | Las decisiones vigentes coinciden con el código y los documentos | **FALLA** | 9 decisiones registradas; 1 desfase(s) código/documentos, 0 excepción(es) declarada(s), 0 mención(es) de decisiones superadas en documentos. |
| R16 | Registros de trazabilidad íntegros y sin marcadores PENDIENTE | **PASA** | 4 fuentes externas y 9 decisiones registradas; 0 problema(s) de integridad. |
| R17 | Las cifras del sistema (índice, grafo, reglas, decisiones), el recuento de estados y los estados de regla del banco coinciden con la ejecución real | **PASA** | 5 documento(s) revisado(s); 49 cita(s) de cifras del sistema, todas coincidentes con las fuentes de verdad. |

## Detalle de reglas no aprobadas

### R12 — ADVERTENCIA: LITE ≤ 40 % de la sección principal del completo (y sin copias literales)

Pares completo/LITE que incumplen el 40 % en su sección principal: 0; secciones copiadas literalmente entre documentos: 1.

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
      "total_lite": 507,
      "total_pct": 85.4
    },
    {
      "criterio": 2,
      "principal_completo": 254,
      "principal_lite": 69,
      "principal_pct": 27.2,
      "cumple_40_principal": true,
      "total_completo": 771,
      "total_lite": 547,
      "total_pct": 70.9
    },
    {
      "criterio": 3,
      "principal_completo": 28359,
      "principal_lite": 3660,
      "principal_pct": 12.9,
      "cumple_40_principal": true,
      "total_completo": 29262,
      "total_lite": 4500,
      "total_pct": 15.4
    },
    {
      "criterio": 4,
      "principal_completo": 238,
      "principal_lite": 57,
      "principal_pct": 23.9,
      "cumple_40_principal": true,
      "total_completo": 886,
      "total_lite": 633,
      "total_pct": 71.4
    },
    {
      "criterio": 5,
      "principal_completo": 259,
      "principal_lite": 65,
      "principal_pct": 25.1,
      "cumple_40_principal": true,
      "total_completo": 864,
      "total_lite": 539,
      "total_pct": 62.4
    },
    {
      "criterio": 6,
      "principal_completo": 1947,
      "principal_lite": 86,
      "principal_pct": 4.4,
      "cumple_40_principal": true,
      "total_completo": 2543,
      "total_lite": 596,
      "total_pct": 23.4
    }
  ],
  "duplicados": {
    "relación con los demás criterios este documento se centra en el criter": [
      "objetivo_6::04_relacion",
      "objetivo_6_lite::04_relacion"
    ]
  }
}
```

### R15 — FALLA: Las decisiones vigentes coinciden con el código y los documentos

9 decisiones registradas; 1 desfase(s) código/documentos, 0 excepción(es) declarada(s), 0 mención(es) de decisiones superadas en documentos.

```json
{
  "decisiones": 9,
  "problemas": [
    "D002 está SUPERADA (D007) pero su implementación sigue en el código: 'TfidfVectorizer' en documentacion_auditoria/src/memoria/rag.py"
  ],
  "avisos": [],
  "documentos_con_decision_superada": [],
  "decisiones_actuales_por_tema": {
    "memoria_semantica": [
      "D001"
    ],
    "memoria_estructural": [
      "D003"
    ],
    "herramienta_externa": [
      "D004"
    ],
    "fuente_de_verdad": [
      "D005"
    ],
    "validacion": [
      "D006"
    ],
    "tecnica_recuperacion": [
      "D007"
    ],
    "indexacion_corpus": [
      "D008"
    ],
    "trazabilidad_cifras": [
      "D009"
    ]
  }
}
```
