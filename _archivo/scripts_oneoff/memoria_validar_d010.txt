[memoria] grafo: 255 nodos / 498 aristas | RAG: 150 fragmentos
  [PASA       ] R1: Cada criterio tiene documento completo Y LITE
               6 criterios revisados; 0 sin el par completo/LITE.
  [PASA       ] R2: Todo documento completo tiene conclusiones registradas
               6/6 criterios con conclusiones en YAML y sección 05 presente. Secciones muy breves (<50 palabras): 0.
  [PASA       ] R3: Todo documento LITE tiene veredicto resumido
               6/6 LITE con veredicto declarado en objetivos.yaml (lite_veredicto) y sección 05 con contenido; 0 sin la palabra literal 'veredicto'.
  [PASA       ] R4: Todo término del glosario está efectivamente usado en algún documento
               19/19 términos aparecen en al menos un documento (búsqueda por claves sobre el texto de los 6 criterios, LITE y maestro).
  [PASA       ] R5: La línea de tiempo documentada coincide con el git log real
               git log real=133 commits; commits_timeline.csv=133; coinciden por hash=133; solo en git=0; solo en CSV=0; asunto distinto=0; fecha distinta=0.
  [PASA       ] R6: Todo archivo de código real está referenciado en el documento del criterio de código
               51/51 archivos reales del repo auditado aparecen en latex/objetivo_3 (Criterio 3).
  [PASA       ] R7: El commit auditado documentado coincide con el HEAD real del clon
               HEAD real=1528939; documentado en 12 proyectos: ['1528939'].
  [PASA       ] R8: Todo archivo tiene capa asignada por una regla explícita en capas.yaml
               0 archivo(s) sin regla explícita; clasificados explícitamente como 'otro': 1. Distribución: {'visualizacion': 2, 'documentacion': 1, 'eda': 1, 'legacy': 13, 'orquestacion': 17, 'transformacion': 1, 'otro': 1, 'analisis': 8, 'ingesta': 3, 'modelo': 2, 'testing': 2}.
  [PASA       ] R9: Cobertura de fichas de análisis == archivos documentados y reales
               inventario=51; archivos reales (git ls-files)=51; fichas en data/analisis_codigo=51.
  [PASA       ] R10: Integridad referencial del grafo (PDF, documentos y aristas)
               255 nodos y 498 aristas revisados; 0 problema(s).
  [PASA       ] R11: El índice RAG cubre todo el corpus declarado y responde consultas
               documentos en el índice=25; esperados=25; faltan=0; consulta de prueba devolvió 3 fragmento(s).
  [ADVERTENCIA] R12: LITE ≤ 40 % de la sección principal del completo (y sin copias literales)
               Pares completo/LITE que incumplen el 40 % en su sección principal: 0; secciones copiadas literalmente entre documentos: 1.
  [PASA       ] R13: El índice RAG está actualizado respecto a las fuentes
               Índice al día: posterior al documento fuente más reciente por 0.1 min.
  [PASA       ] R14: Sin contradicciones numéricas entre documentos
               7/7 comprobaciones numéricas OK (cifras de commits/archivos/scripts/criterios, preguntas enumeradas y cobertura).
  [ADVERTENCIA] R15: Las decisiones vigentes coinciden con el código y los documentos
               10 decisiones registradas; 0 desfase(s) código/documentos, 1 excepción(es) declarada(s), 0 mención(es) de decisiones superadas en documentos.
  [PASA       ] R16: Registros de trazabilidad íntegros y sin marcadores PENDIENTE
               4 fuentes externas y 10 decisiones registradas; 0 problema(s) de integridad.
  [PASA       ] R17: Las cifras del sistema (índice, grafo, reglas, decisiones), el recuento de estados y los estados de regla del banco coinciden con la ejecución real
               5 documento(s) revisado(s); 50 cita(s) de cifras del sistema, todas coincidentes con las fuentes de verdad.
[memoria] reglas: 15 PASA, 0 FALLA, 2 ADVERTENCIA
