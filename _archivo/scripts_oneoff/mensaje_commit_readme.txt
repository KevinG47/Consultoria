Documenta repo_mejorado en el README raiz y completa los pasos de reproduccion

El README de la raiz no mencionaba repo_mejorado en ningun sitio: cero
apariciones de repo_mejorado, CHANGELOG, construir_repo_mejorado.py,
aplicar_arreglos.py, verificar_arreglos.py o probar_librerias_reales.py. Quien
clonara el repositorio no tenia forma de enterarse de que existe el entregable
de codigo. Se aplican cinco ediciones:

1. Tabla "Empieza aqui": la fila de datos_originales/ menciona las DOS copias
   (repo_auditado y repo_mejorado), no solo la evidencia.
2. Seccion nueva "datos_originales/ - que hay y para que sirve": tabla de
   contenido con que es cada cosa y como se usa, distinguiendo evidencia
   (intocable) de codigo de trabajo (se reconstruye).
3. Seccion nueva "datos_originales/repo_mejorado/ - el entregable de codigo",
   con la referencia destacada al CHANGELOG.md como primer documento a leer,
   al README del repo mejorado y al poetry.lock que pasa "poetry check --lock".
4. Bloque de reproduccion de las dos copias: verificar hashes, construir,
   aplicar los 30 arreglos, verificar y probar con librerias reales y con los
   51 artefactos del inventario, con el orden justificado.
5. Arbol de estructura y tabla de "Estado del sistema": se anaden repo_mejorado
   y los scripts, mas tres filas de estado (codigo mejorado, lock y ejecucion
   del codigo).

Durante la verificacion, un revisor propio (revisar_readme.py) detecto que las
rutas citadas como "repo_mejorado/CHANGELOG.md" eran ambiguas: desde la raiz no
existen, porque cuelgan de datos_originales/. Se corrigieron a la ruta completa.

Comprobado que el README raiz NO es entrada de ninguna de las 17 reglas: R17
resuelve config.DOC / "README.md" (el de documentacion_auditoria/), R14 lee solo
documentacion_auditoria/{latex,data} y el corpus del RAG es LaTeX +
data/validacion/*.md. Editarlo no dispara cascada de R13/R14/R17.

Verificacion: 17 reglas 15 PASA / 0 FALLA / 2 ADVERTENCIA; compilacion de
anteproyecto sin --forzar, exit 0; README con 11 encabezados sin saltos de
nivel, 6 cercas balanceadas, 5 tablas cuadradas, 0 rutas inexistentes y 0
enlaces internos rotos.
