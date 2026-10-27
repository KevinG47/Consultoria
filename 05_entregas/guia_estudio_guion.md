# Guía de estudio del guion de exposición

**Uso interno del equipo · no forma parte de la entrega.**
Este archivo se lee antes de exponer y se consulta cuando algo no cuadra en plena
presentación. Cada capítulo termina con una frase lista para decir en voz alta.

> **Estado de este archivo.** Contiene las Partes I a V (capítulos 0 a 21). Falta el bloque
> de anexos (A a F), que se añade en la última revisión. El guion completo de referencia es
> `guion_exposicion_paneles.md`; esta guía no lo sustituye: lo explica.

---

# PARTE I · La portada, el encuadre y el arranque

## 0. Cómo usar esta guía

Esta guía no se lee en voz alta: se lee antes, y se consulta cuando algo no cuadra en
plena presentación. El guion es lo que se dice; esto es lo que hay detrás de cada frase.

Tres reglas de uso:

- **Las cifras no se cambian.** Si una frase suena forzada, cámbiala; si una cifra no te
  cuadra, no la retoques: primero entiéndela.
- **«Si te preguntan»** cierra cada capítulo con la respuesta lista para decir en voz
  alta. Si la pregunta llega en otro tono, esa frase es el esqueleto.
- **Lo que no está aquí ni en la tabla no se improvisa.** La respuesta siempre es la
  misma: «no lo tengo a mano, se lo confirmo después».

### Tabla de cifras de bolsillo

Todas están verificadas contra archivos del repositorio. La columna de la derecha es lo
que conviene tener abierto por si alguien pide la fuente.

| Dato | Valor | Dónde se verifica |
|---|---|---|
| Registros / personas / convocatorias | 77 237 · 30 086 · 6 (2013–2021) | Encabezado del EDA · `analisis_longitudinal.md` §1 |
| Análisis con resultado cerrado | 8 de 10 (7 entregados, 1 no evaluable) | Panel F2, tarjeta 1 |
| Bloqueado por datos | F2-1, archivo de 1,2 GB no versionado | Panel F2, tarjeta 2 (capítulo 6) |
| Fuera de esta fase | F2-8 (descriptivos) y F2-9 (inferencia) | Panel F2, tarjeta 1 (capítulo 5) |
| IDs con más de un registro | 56 de 19 215 · **15** comprometen la identidad | Panel F2, tarjeta 3 · `validacion_unicidad.json` (capítulo 7) |
| Retención 2013 → 2021 | 56,18 % (censo) · 56,63 % (muestra) | Panel F2, tarjeta 4 · `analisis_longitudinal.md` §2.1 |
| Comprobaciones automáticas | 56 / 56 · 21 figuras exportadas | Panel F2, tarjeta 5 |
| Reglas de validación | 15 PASA · 0 FALLA · 2 ADVERTENCIA (17) | Panel F2, tarjeta 6 · `evidencia_validacion.md` |
| Mudanzas de departamento | 808 (4,38 % de 18 430) · 231 rutas · 53 metropolitanas | Panel F2, tarjeta 7 · `flujos_territoriales.json` |
| Flujo por nacimiento | 11 922 casos (otra definición) | Panel F2, pestaña 8 · `flujos_territoriales.json` |
| Atípicos de edad | 106 registros · 11 personas > 100 · máx. 956,25 | Panel EDA, univariado · `metodologia_muestreo.md` §3 |
| Centenarios reconciliados | 22 registros → 12 personas → 11 al colapsar | Panel EDA · `analisis_longitudinal.md` §2.8 (capítulo 13) |
| Faltantes principales | Institución 12,1 % (9 326) · DANE nacimiento 5,9 % · DANE residencia 3,2 % | Panel EDA · `metodologia_muestreo.md` §4 |
| Muestra | 2 224 personas · aleatoria simple · semilla 2026 | `metodologia_muestreo.md` §1 (capítulo 15) |
| Ganancia de precisión | post-estratificación hasta 16,6 % · modelo asistido hasta 20,1 % | `metodologia_muestreo.md` §5 |
| Estrato Emérito por par | 1, 7 y 3 observaciones | `metodologia_muestreo.md` §5 (capítulo 16) |
| Ascensos 2019 → 2021 | 13 355 personas · 2 336 ascendieron · 9 657 siguieron · 1 362 bajaron | `analisis_longitudinal.md` §2.3 (capítulo 17) |
| Índice de búsqueda | 151 fragmentos · 25 documentos · 123 505 palabras | Fichero del índice de búsqueda (`documentacion_auditoria/data/memoria/`) |
| Grafo de relaciones | 255 nodos · 500 aristas | `evidencia_validacion.md` |

Si en pantalla no se ve el número y no está en esta tabla, no se dice.

**Si te preguntan:** «¿De dónde salen sus cifras?» — «De archivos del repositorio: cada
cifra tiene su archivo, y la tabla de bolsillo que llevo dice cuál.»

---

## 1. Qué auditó la consultoría, y qué significa «no le tocamos ni un byte»

La tarea llegó con una pregunta muy concreta: **¿las cifras que el proyecto afirma se
pueden sostener con lo que el proyecto tiene guardado?** No preguntaron si el análisis
era bonito, ni si las gráficas eran llamativas. Preguntaron si lo que dice es verdad y si
se puede repetir.

Para responder eso hicimos dos cosas y conviene no mezclarlas:

| Mitad | Qué es | Verbo |
|---|---|---|
| Fase 1 | Auditar el repositorio del Grupo 8: leer su código, reconstruir sus números y anotar cada contradicción | Reconstruir |
| Fase 2 | Hacer el análisis que ellos no hicieron, con los datos que sí estaban disponibles | Analizar |

«Reconstruir» es la palabra clave. Copiar una cifra es repetir lo que el otro dijo;
reconstruirla es volver a calcularla desde el dato. La diferencia se ve en una tabla:

| Verbo | Qué significa | Ejemplo |
|---|---|---|
| **Copiar** | Repetir lo que dice el otro | «Su informe afirma 50 891 filas; lo repetimos» |
| **Reconstruir** | Volver a calcular desde el dato | «Contamos las filas del archivo y son 77 237» |
| **Declarar** | Decir qué no se pudo reconstruir y por qué | «La productividad no se puede recalcular: falta el archivo de 1,2 GB» |

Y el repositorio auditado **no se toca**, por dos razones. La primera es de método: si lo
arregláramos, ya no podría probar nada sobre él. La segunda es de confianza: queda como
prueba, intacto, para que cualquiera lo abra y vea que lo que decimos es verificable.

Por eso hay **dos copias**:

| Copia | Qué es | Qué se hizo con ella |
|---|---|---|
| Repositorio original | El repositorio del Grupo 8 tal como lo entregaron | **Nada**: no se cambió ni un byte |
| Copia mejorada | Una copia aparte | **34 arreglos** sobre 18 archivos, cada uno con su motivo escrito |

**Si te preguntan:** «¿En qué se diferencia una auditoría de una opinión?» — «Auditar es
reconstruir los números con los datos del otro y anotar con archivo y línea dónde no
cuadran; y el repositorio auditado no se toca: queda como prueba.»

---

## 2. Cómo se abre la presentación

La presentación es **una sola página** que envuelve los tres paneles (Fase 2, EDA y
Trayectorias). Se abre con un doble clic en un archivo pequeño, `servir_presentacion.bat`,
que hace dos cosas: levanta un **servidor diminuto en el propio equipo** y abre el
navegador en la portada.

| Paso | Qué haces | Qué ves |
|---|---|---|
| 1 | Doble clic en `servir_presentacion.bat` | Se abre una **ventana negra** (el servidor) y el navegador en la portada azul con el título dorado |
| 2 | Esperas a que cargue el panel y pruebas uno | Se abre dentro de la página; la tecla Esc lo cierra |
| 3 | Pones pantalla completa (F11) | La página se adapta sola al proyector |

**Por qué no se abre con doble clic en el archivo de la página.** Si abres un archivo HTML
directamente, el navegador lo carga desde el disco, y en ese modo **le prohíbe a la página
cargar los otros paneles**, que están en el mismo disco. El resultado sería una portada
vacía. El servidor evita el problema: sirve la carpeta entera y el navegador la ve como
una página «normal».

**No hace falta internet.** La página, los tres paneles y hasta la tipografía están en el
disco. El único aparato es el servidor pequeño, que corre en el propio equipo
(`127.0.0.1:8000`), sin salir a la red.

**Si algo falla en vivo:** no se cierra la ventana negra. Aparecen dos botones —«Reintentar»
y «Abrir en una pestaña nueva»— y con el segundo se sigue hablando con normalidad, porque
el panel es el mismo. Si se cerró la ventana, se vuelve a hacer doble clic y se refresca.

**Si te preguntan:** «¿Esto funciona sin internet?» — «Sí: la página, los tres paneles y
hasta la tipografía están en el disco; el único aparato es un servidor pequeño en el
propio equipo.»

---

# PARTE II · El panel Fase 2 y el sistema de reglas

## 3. Qué es la «Fase 2», y por qué el panel se llama así

El trabajo tuvo dos mitades, y conviene separarlas porque en la exposición se mezclan.

**La primera mitad fue auditar.** Eso significa leer el repositorio del otro grupo
—el Grupo 8— y comprobar si lo que afirma se sostiene con lo que tiene guardado. Un
repositorio es una carpeta con historia: guarda los archivos y también cada versión que
se les fue haciendo. No es un archivo suelto que se sobrescribe.

Cuando auditas no arreglas nada: **reconstruyes los números del otro con sus propios
datos** y anotas cada contradicción con el archivo y la línea exacta. Por eso en el
cierre decimos que al repositorio auditado «no le cambiamos ni un byte». Hay dos copias y
no hay confusión posible:

| Copia | Qué es | Qué se hizo con ella |
|---|---|---|
| Repositorio original | El repositorio del Grupo 8, tal como lo entregaron | Nada: queda como prueba, intacto |
| Copia mejorada | Una copia aparte, con 34 arreglos | Cada arreglo con su motivo escrito |

**La segunda mitad es la Fase 2.** Aquí ya no auditamos: hicimos el análisis que ellos no
habían hecho, con los datos que sí estaban disponibles. Es lo que se ve en el panel.

Y ahí está la parte que más nos costó escribir. Decir «hicimos diez análisis» habría sido
engañoso, porque no es lo que pasó. Lo que pasó es esto: **ocho cerrados de diez** —siete
entregados con su informe, sus cifras y su figura, y uno cerrado como no evaluable porque
el dato no existía— y **dos** que quedaron fuera de esta fase y están nombrados en la
misma tarjeta, no escondidos. La tarjeta lo dice con esas palabras: «8 de 10».

**Si te preguntan:** «¿Qué es la Fase 2?» — «La parte del trabajo en la que, en vez de
auditar el repositorio del Grupo 8, hicimos nosotras el análisis que ellos dejaron
pendiente.»

---

## 4. Las ocho pestañas del panel Fase 2

El panel es **un solo archivo** con **ocho pestañas**. No son ocho archivos: es un
documento que se navega con la barra de arriba. Esto importa porque en la exposición se
dice «pestaña 1», «pestaña 6», y conviene que sepas qué hay en cada una.

| # | Pestaña | Qué responde | Qué señalarías en pantalla |
|---|---|---|---|
| 1 | Resumen ejecutivo | Qué se hizo, qué se encontró y con qué evidencia | Las tarjetas de cifras y la tabla de análisis |
| 2 | Territorio y desigualdad | ¿La concentración de investigadores bajó de verdad? | Tasas por 100 000 y la curva de convergencia |
| 3 | Diversidad y falencias | ¿Cuánto se aleja la representación de la población? | Los cocientes con sus intervalos |
| 4 | Redes y clustering | ¿Quién conecta con quién? ¿Hay grupos? | La red institucional y el número de grupos |
| 5 | Supervivencia y género | ¿Cuánto se queda la gente? ¿El género importa? | La curva de permanencia |
| 6 | Calidad y reproducibilidad | ¿La regla de unicidad del identificador y el modelo de datos son honestos? | El contraste entre la regla documentada y la implementada |
| 7 | Límites y falencias | Qué no se hizo, y por qué | La lista escrita, sin adornos |
| 8 | Flujos y migración | ¿Por dónde se mueven? | El mapa de mudanzas entre departamentos |

Ojo con una palabra que se usa para dos cosas. El **armazón** de la presentación
(`presentacion.html`) tiene **tres paneles**: Fase 2, EDA y Trayectorias. El panel de
Fase 2, a su vez, tiene **ocho pestañas**. Si en algún momento dudas: tres paneles
grandes, ocho pestañas dentro del primero.

**Si te preguntan:** «¿Qué trae el panel de la Fase 2?» — «Ocho pestañas: resumen,
territorio, diversidad, redes, supervivencia, calidad, límites y flujos.»

---

## 5. Qué es un «análisis» F2-n y por qué la cuenta es 8 de 10

En este proyecto, un **análisis** es una pregunta del anteproyecto que se cierra con
cuatro piezas: un guion reproducible que la calcula, un archivo de resultados, un
documento que la explica y sus figuras. No es un párrafo de opinión.

El número **F2-n** no lo inventamos nosotras: viene de la numeración del plan del
anteproyecto, que tenía diez análisis. Así se reparten:

| Código | Análisis | Estado |
|---|---|---|
| F2-1 | Productividad científica | **No evaluable** (ver capítulo 6) |
| F2-2 | Concentración territorial por habitante | Entregado |
| F2-3 | Modelo de datos reproducible | Entregado |
| F2-4 | Redes institucionales | Entregado |
| F2-5 | Diversidad y representación | Entregado |
| F2-6 | Segmentación de investigadores | Entregado |
| F2-7 | Regla de unicidad del identificador | Entregado (capítulo 7) |
| F2-8 | Descriptivos por convocatoria | Fuera de esta fase |
| F2-9 | Extender la inferencia | Fuera de esta fase |
| F2-10 | Supervivencia | Entregado |
| F2-11 | Flujos y migración | Entregado **después**, como frente añadido |

Los dos que quedaron fuera no quedaron por pereza. **F2-8** pedía descriptivos
*por convocatoria*, y nuestro análisis exploratorio ya describe por persona en su última
convocatoria: era el mismo terreno con otro diseño, y preferimos no duplicar. **F2-9**
pedía extender el método de estimación a territorio, género y diversidad; ahí ya
teníamos la inferencia cubierta para retención y edad, y quedó declarado como extensión.

Y aquí hay una trampa que conviene entender, porque es la misma historia del 22 contra el
11: **hay dos cuentas correctas que no son la misma cuenta**.

- **8 de 10** cuenta lo que quedó cerrado **del plan**: siete entregados y uno que no era
  evaluable. Es la cifra de la tarjeta.
- **Los nueve informes** cuentan lo que hay **en la carpeta**: los siete de la fase, más
  el de flujos que se añadió después, más el análisis longitudinal que sostiene las
  cifras de retención.

Las dos son ciertas y no se contradicen: cuentan unidades distintas. Por eso el guion ya
no dice «nueve frentes cerrados»: dice «ocho análisis cerrados de diez, más el de flujos
añadido después». Si te preguntan por qué nueve y ocho a la vez, esa es la respuesta.

**Si te preguntan:** «¿Cuántos análisis hicieron?» — «Ocho cerrados de diez: siete
entregados y uno que no era evaluable, más el de flujos, que se añadió después.»

---

## 6. F2-1 y el archivo de 1,2 GB

Este es el capítulo que hay que saber contar sin titubear, porque es el que más
preguntas genera.

### La ficha del archivo

| Dato | Valor |
|---|---|
| Nombre | `produccion_grupos.csv` |
| Tamaño | ≈ 1,2 GB |
| Filas | 3 166 629 (3,2 millones) |
| Autores únicos | 77 401 |
| Origen | API pública de datos (Socrata), conjunto `33dq-ab5a`, descargado por páginas |
| ¿Está en un repositorio? | **No.** Nunca se guardó, ni el del Grupo 8 ni el nuestro |

### Qué contiene (y la corrección que hay que hacer)

El archivo **no es una lista de revistas**. Es el **registro de productos por autor**:
una fila por cada producto publicado (un artículo, un libro, un capítulo) con su autor y
sus datos, entre ellos **la revista donde salió**. La diferencia importa porque si alguien
pregunta «¿y qué revistas eran?», la respuesta correcta es «todas las que aparezcan en
los productos de esos autores», no una lista cerrada.

El guion dice «un archivo de 1,2 GB con las revistas». En voz alta no molesta, pero si
alguien pregunta, di esto: **«es el registro de los productos publicados por cada
investigador, con la revista de cada uno».**

### Por qué no se pudo evaluar

Tres razones encadenadas, y las tres son de dato, ninguna de método:

1. **No está guardado en ninguna parte.** Pesa demasiado para un repositorio, así que se
   excluyó a propósito cuando el Grupo 8 lo montó. No es que se perdiera: nunca se
   versionó.
2. **Hay que descargarlo con conexión** desde la API pública, y esa descarga **no está
   siempre disponible**: el propio auditado descartó un análisis por eso. No es un botón
   guardado en el repositorio.
3. **No se puede recalcular.** De los productos solo quedan ocho archivos de evidencia que
   el auditado sí dejó; podemos leerlos, pero no volver a calcularlos. Y lo que no se
   puede recalcular no se puede auditar de verdad.

Por eso el análisis se cerró como **«no evaluable por restricción de acceso, no por
método»**. La frase es deliberada: la diferencia entre «no supe hacerlo» y «no tengo el
dato» es justo la honestidad que se exige.

**Si te preguntan:** «¿Por qué no hay análisis de productividad?» — «Porque necesita el
archivo de 1,2 GB con los productos de cada autor, que el grupo nunca guardó en su
repositorio y no se puede descargar sin conexión; lo cerramos como no evaluable por falta
del dato, no por falta de método.»

---

## 7. Los identificadores repetidos: 56, 41, 14, 1 y 15

Este capítulo es el más delicado del panel, y el que más fácil se cuenta mal. Vamos por
partes.

### Tres palabras que se confunden

| Palabra | Qué es |
|---|---|
| **Registro** | Una fila de la base: una persona en una convocatoria concreta |
| **Persona** | Una persona real; puede aparecer en varias convocatorias |
| **Identificador (ID)** | El número que la base usa para decir «esta fila es de la misma persona» |

La base tiene **77 237 registros** de **30 086 personas** en **seis convocatorias**
(2013 a 2021). Si el identificador funciona bien, cada número designa siempre a la misma
persona. Por eso la pregunta del análisis es: **¿ese número se comporta como una
persona?**

### El problema

Hay **19 215 identificadores** que aparecen en **más de un registro**. Solo esos se pueden
comprobar: con un solo registro no hay nada que contradecir. De esos, **56 no cumplen la
regla**:

| Fallo | Cuántos | Qué significa |
|---|---|---|
| Solo en el género | 41 | El género cambia entre convocatorias |
| Solo en la edad | 14 | La edad no avanza como debía |
| En las dos cosas | 1 | Cambia el género y la edad no avanza |
| **Total** | **56** | |
| De ellos, **comprometen la identidad** | **15** | Catorce de edad más el que falla en ambas |

### La regla, exacta

La regla no pide que la edad sea la misma: pide que **suba lo que haya pasado entre
convocatorias**. Se comparan los registros **consecutivos** de cada identificador, de una
convocatoria a la siguiente, y se calcula:

> **residuo = (edad después − edad antes) − (años que pasaron entre las dos convocatorias)**

Si la persona envejeció justo lo que pasó el tiempo, el residuo es **0**. Se acepta un
margen de **±4 años** (para errores de digitación y de redondeo). Si el residuo se aleja
de cero más de 4 años, en cualquier dirección, la trayectoria es imposible. La comparación
se hace en valor absoluto: una edad que **retrocede** cuenta igual que una que se dispara.

Tres ejemplos reales, para que se vea de golpe:

| Identificador | Qué pasó | Residuo |
|---|---|---|
| `0000671819` | 115,51 años en 2015 → 16,92 años en 2017, con 1,57 años de por medio | **−100,16** |
| `0000034380` | **−1,13 años** en 2015 → 69,28 en 2017 | **+68,84** |
| `0000444499` | 43,05 en 2013 → 46,00 en 2021, con 7,32 años de por medio | −4,37 |

Fíjate en el tercero: no hay nada absurdo a la vista, pero envejeció 2,95 años cuando
pasaron 7,32. Ese es el caso **más débil** de los 15, y es un ejemplo de que el margen de
4 años es generoso.

**Esto es importante para la exposición:** la regla **no** espera edad constante. Si la
esperara, el patrón normal del registro —huecos de 1 a 2,6 años entre convocatorias— sería
una violación en masa. De hecho, 99,96 % de los 47 151 pares comparados cae dentro del
margen.

### ⚠️ La advertencia crítica: la cifra defendible es 15, no 56

Cuando digas una cifra en voz alta, **di 15**. El 56 es correcto como total de la regla,
pero **no es un total de problemas de identidad**, y explicarlo mal convertiría el
hallazgo en un error.

- De los 56, **41 fallan solo porque cambia el género**. El propio análisis exploratorio
  documentó que el género **no es estable** en este registro: 42 personas cambian de
  género entre convocatorias. Que además cambie en el identificador no prueba que el
  número designe a dos personas distintas.
- Los que **sí** comprometen la identidad son **15**: los catorce de edad más el que falla
  en ambas.
- Y aun así, **«comprometen la identidad» es una lectura, no una prueba**. Lo que la regla
  demuestra es que **la trayectoria es imposible**; que el número esté designando a dos
  personas es la explicación más probable, pero el registro no trae nombre ni documento
  que lo confirme.

Y hay un matiz más que conviene saber de memoria: **5 de los 15 están en el borde**. Sus
residuos van de 4,37 a 8,48 años, y con un margen más estrecho o más amplio la lista
cambia (con ±10 años quedarían 13). El margen de 4 años lo fijó el equipo del auditado;
no es un resultado, es una decisión, y se declara como tal.

### El dato que remata el argumento

El auditado **también quiso comprobar la edad, pero lo hizo mal**: comparaba la edad de un
registro con la del anterior **sin mirar cuántos años habían pasado** (marcaba como
sospechoso a quien envejeciera más de 4,1 años, y solo en un sentido). Eso marca
**1 067 pares**, de los cuales **1 058 son falsos positivos** frente a los 18 correctos.
Es decir: habría señalado a un millar de personas perfectamente válidas, y habría dejado
pasar los casos más graves.

Ese es el hallazgo de la pestaña 6 del panel: **el método no estaba mal en la idea, estaba
mal en la referencia**. Nuestro proyecto corrige eso.

**Si te preguntan:** «¿Cuántos identificadores tienen problemas?» — «Quince comprometen de
verdad la identidad de la persona; los otros cuarenta y uno son un cambio de género, que
el propio registro documenta como inestable y no indica que sean dos personas.»

**Si te preguntan:** «¿Y por qué no vale decir 56?» — «Porque 56 es el total de la regla,
pero 41 de esos fallos son de género y no de identidad; la cifra de identidad es 15.»

---

## 8. Las diecisiete reglas

### Qué es una regla, sin nombres raros

Una regla es una **pregunta de sí o no**, escrita una sola vez, que un programa responde
solo cada vez que se va a generar un documento. No es una norma de estilo ni una
recomendación: **si la respuesta es «no», la entrega no sale**.

Existieron por una razón muy concreta: mientras escribíamos, era imposible que alguien
recordara todas las cifras del proyecto de memoria. En lugar de confiar en la memoria,
escribimos las comprobaciones. Cada regla vigila un tipo de coherencia:

- **Que todo se pueda rastrear.** Que cada afirmación tenga un documento, una ficha o una
  fuente externa con enlace.
- **Que no haya contradicciones internas.** Que el mismo dato no aparezca con dos valores,
  que un resumen no sea una copia del documento completo, que el índice de búsqueda esté
  al día.
- **Que el sistema se vigile a sí mismo.** Que las cifras que los documentos dicen del
  propio sistema coincidan con la última corrida real.

### Tabla de referencia

*(Para consulta. En voz alta no se dicen los códigos: se explica el tipo de comprobación,
como en el apartado anterior.)*

| Código | Estado hoy | Qué comprueba, en una frase |
|---|---|---|
| R1 | PASA | Que cada uno de los seis criterios tenga documento completo y versión resumida |
| R2 | PASA | Que todo documento completo termine con sus conclusiones registradas |
| R3 | PASA | Que todo documento resumido termine con su veredicto |
| R4 | PASA | Que cada término del glosario se use de verdad en algún documento |
| R5 | PASA | Que la línea de tiempo de commits que documentamos coincida con la historia real |
| R6 | PASA | Que todo archivo de código del repositorio auditado esté citado donde toca |
| R7 | PASA | Que el commit que citamos sea el que de verdad está congelado en la copia |
| R8 | PASA | Que todo archivo del repositorio auditado esté clasificado por escrito |
| R9 | PASA | Que haya una ficha de análisis por cada archivo del inventario |
| R10 | PASA | Que el mapa de relaciones sea coherente por dentro (nodos, aristas, documentos) |
| R11 | PASA | Que el índice de búsqueda cubra exactamente los documentos declarados |
| R12 | **ADVERTENCIA** | Que los resúmenes no pasen del 40 % ni copien secciones literales |
| R13 | PASA | Que el índice de búsqueda esté al día con los documentos |
| R14 | PASA | Que no haya cifras contradictorias entre documentos |
| R15 | **ADVERTENCIA** | Que las decisiones registradas coincidan con el código |
| R16 | PASA | Que no quede ninguna fuente externa con la dirección en «pendiente» |
| R17 | PASA | Que las cifras del propio sistema citadas en documentos sean las de la última corrida |

Quince pasan, ninguna falla y dos advierten. Eso es el famoso **15 · 0 · 2**.

### Lo que el guion ya cuenta sin nombrarlas

- La sección resumida copiada literal → es la **primera advertencia** (capítulo 10).
- La decisión vieja conservada a propósito → es la **segunda advertencia** (capítulo 10).
- Las «diez cifras viejas» que detuvieron el PDF → es una regla de coherencia de cifras
  que **falló de verdad** y bloqueó la compilación (capítulo 11).

**Si te preguntan:** «¿Qué son las diecisiete reglas?» — «Comprobaciones automáticas que
se ejecutan solas antes de dar cualquier número por bueno; si una falla, la entrega no
sale.»

---

## 9. 15 · 0 · 2: por qué esto no es un error

Las cifras son **quince que pasan, cero que fallan y dos que advierten**. La confusión
típica es creer que las dos advertencias son dos fallos. No lo son. Cada regla termina en
uno de tres estados:

| Estado | Qué significa | Qué hace el sistema |
|---|---|---|
| **PASA** | La comprobación salió bien | Sigue adelante |
| **FALLA** | Encontró una contradicción real | **Detiene la compilación** |
| **ADVERTENCIA** | Encontró una excepción declarada por escrito | Sigue adelante, pero lo deja registrado |

Para que se entienda qué sería una **FALLA** de verdad: que en un documento se afirme que
hay 150 fragmentos y en otro que hay 151; que un documento cite una decisión que el código
ya no implementa; que una cifra cambie entre dos documentos sin que nadie se diera cuenta.
Una falla es **una contradicción**, no una opinión distinta.

**Cero fallas es la cifra que importa**: significa que ninguna contradicción pasó el
filtro. Y **las dos advertencias no son errores** porque no son contradicciones: son cosas
que el sistema **ve, no oculta y deja escritas**. La diferencia no es menor:

- Una deuda declarada se puede leer, fechar, revisar y discutir.
- Una excepción escondida no se puede hacer nada de eso.

Por eso en el guion se dice que, si quitáramos la excepción, la regla no pasaría a verde:
**pasaría a rojo**. Porque dejaría de haber excepción declarada y habría, de verdad, un
desfase entre lo que dice el registro y lo que hace el código.

**Si te preguntan:** «Entonces 15 PASA y 2 ADVERTENCIA, ¿el sistema está fallando?» — «No:
fallas hay cero; las dos advertencias son excepciones que el sistema ve, no oculta y deja
escritas para que se puedan revisar.»

---

## 10. Las dos advertencias: deuda declarada, no error

### La primera: una sección resumida copiada literal

Cada criterio de la auditoría tiene **dos documentos**: el completo y una **versión
resumida** de unas cuatro páginas, pensada para leer en voz baja antes de una reunión.

La regla de los resúmenes es sencilla: **que no pasen del 40 % del documento completo y
que no copien secciones enteras**. Copiar una sección entera no es ilegal, pero suele ser
un síntoma de que el resumen se hizo al afán; la regla está para que nadie resuma
«copiando y pegando» sin darse cuenta.

El resultado fue: ningún resumen pasa del 40 % —bien— y **una sección está copiada
literalmente**: la del criterio 6 que se titula «relación con los demás criterios» aparece
idéntica en el documento completo y en su resumen. Y esa copia es **deliberada**: la
sección existe para enlazar el criterio 6 con los otros cinco, y copiarla tal cual
conserva ese enlace sin reescribirlo peor.

Es una advertencia y no una falla porque la excepción está declarada: se sabe cuál es,
dónde está y por qué. Lo que la regla impide es que la copia pase inadvertida.

### La segunda: la técnica anterior guardada como respaldo

El proyecto tiene un **registro de decisiones**: cada decisión importante está escrita con
su número (D001, D002, y así hasta D010), su motivo y su estado. Una decisión puede quedar
**superada** por otra posterior.

Caso concreto: **D002** decidió que la búsqueda en los documentos se hiciera por
**frecuencia de palabras** —la técnica anterior—, y **D007** la superó con un método que
**entiende el significado** y que **ya está implementado**. Hasta aquí, todo normal: la
decisión vieja debería desaparecer del código.

Pero no desapareció, y eso es a propósito. La técnica anterior **se conserva como método
por defecto y como respaldo** para cuando el método nuevo no está disponible, y además
gana en algunos casos: es más rápida, no depende de nada externo y se puede explicar
palabra por palabra. Retirarla dejaría al sistema sin salida cuando el método nuevo no
esté.

Ahí es donde entra una pieza fina: la regla puede aceptar que una decisión superada siga
viva **si declara su respaldo** —con qué motivo, qué se conserva y quién lo autoriza—. En
ese caso lo registra como **ADVERTENCIA** en lugar de tratarlo como falta. Se hizo en el
commit `b0cafbf`.

Qué la pondría en rojo: que el respaldo declarado se borrara, que la excepción quedara sin
motivo escrito, o que algún documento citara la decisión superada como si siguiera
vigente. Mientras esas tres cosas no pasen, la advertencia es la forma correcta de
registrar una excepción real.

### La idea que hay detrás de las dos

**Deuda declarada** no es lo mismo que **error**. Una deuda tiene monto, fecha, motivo y
un responsable; se puede planear su pago. Un error silencioso solo se descubre cuando
alguien lo sufre. El sistema prefiere tener dos deudas escritas antes que una excepción
escondida.

**Si te preguntan:** «¿Qué son esas dos advertencias?» — «Una sección de la versión
resumida copiada literal, y una decisión vieja que se conservó a propósito como respaldo;
las dos están declaradas por escrito y revisadas.»

---

## 11. Cómo se valida y cómo se bloquea la compilación

### Los dos comandos

| Comando | Qué hace | Qué ves |
|---|---|---|
| `python -m memoria validar` (desde `documentacion_auditoria/src`) | Ejecuta las diecisiete reglas y reporta el estado de cada una | La lista con 15 PASA, 0 FALLA, 2 ADVERTENCIA, y el detalle de las dos advertencias |
| `python documentacion_auditoria/src/compilar.py objetivo_1` (desde la raíz del repositorio) | Genera el PDF de un documento | Antes de escribir el PDF, corre la validación |

El primero se usa cuando quieres saber cómo está el proyecto. El segundo se usa cuando
quieres la entrega. Y el segundo **no es independiente del primero**: lo ejecuta por
dentro. Ojo con una trampa: **`compilar.py` sin el nombre de un documento compila los
doce de golpe**; siempre se le pasa el nombre.

### La puerta

Cuando `compilar.py` corre la validación y encuentra **una sola FALLA**, se detiene:

- **no escribe el PDF**;
- termina con **código de salida 2** (el número que usa el sistema para decir «no
  terminé bien»);
- imprime qué regla falló y con qué archivo y qué línea.

Eso es la puerta. Y tiene una rendija: `--forzar` la salta aunque haya reglas en falla,
y `--sin-validar` ni siquiera corre la validación; las dos **quedan registradas**. La
rendija existe para emergencias, no para el día a día.

**Las advertencias sí dejan compilar.** Por eso 15 · 0 · 2 no bloquea nada: las dos
advertencias pasan por la puerta porque están declaradas. 15 · 1 · 2 no pasaría.

### El caso real que se cuenta en voz alta

Cuando se añadió la sección de muestreo al material, **diez cifras viejas** quedaron
citadas en documentos que ya no las tenían actualizadas. La regla de coherencia de cifras
lo detectó y **la compilación se detuvo sola** hasta que las diez se corrigieron.

Ese episodio es el argumento más fuerte del panel, porque no es un ejemplo inventado: fue
el sistema **bloqueando nuestra propia entrega**. La frase del guion —«esa es la
diferencia entre una validación que se cuenta y una validación que se ejecuta»— sale de
ahí.

### No confundir tres cosas

En el panel aparecen tres tipos de comprobaciones y conviene no mezclarlas:

| Qué | Cuántas | Qué vigila |
|---|---|---|
| Las reglas del proyecto | 17 | Que la documentación sea coherente consigo misma |
| Las comprobaciones de cada análisis | 56 | Que los resultados de cada análisis cuadren por dentro |
| Los verificadores independientes | Varios programas | Que el panel muestre exactamente lo que dicen los archivos |

Las 56 están en verde una por una, en el archivo de resultados de cada análisis. Los
verificadores son programas aparte que se ejecutan y comparan el panel contra los
archivos, para que nadie tenga que creernos de memoria.

**Si te preguntan:** «¿Cómo impiden que se entregue algo malo?» — «El PDF no se genera si
alguna regla falla: la compilación corre las comprobaciones primero y se detiene con un
aviso; ya nos pasó una vez y se detuvo sola.»

---

# PARTE III · El dato y el muestreo

## 12. Qué es el análisis exploratorio y qué encontramos

El **análisis exploratorio** es la parte donde uno se sienta a mirar los datos antes de
analizarlos. Suena a trámite, pero es donde aparecen los problemas: un valor imposible, una
columna vacía, un atributo que cambia donde no debería.

El panel del análisis exploratorio tiene **cuatro pestañas**:

| Pestaña | Qué mira | Qué se aprende |
|---|---|---|
| Univariado | Una variable a la vez: edad, género, área… | Qué forma tienen los datos y qué valores raros aparecen |
| Bivariado | Dos variables a la vez: edad por categoría, retención por área… | Qué se mueve junto con qué |
| Varianza | Cuánta dispersión hay en cada cosa | Qué tan desigual es el registro |
| Diagnósticos | Lo que está mal en el dato | Atípicos, faltantes, atributos que cambian |

Los números de partida: **77 237 registros** de **30 086 personas** en **seis
convocatorias** (2013 a 2021), con **treinta columnas**. La llave persona × convocatoria
es única: **cero duplicados**.

Lo que encontramos, en cinco hallazgos:

| Hallazgo | Cifra | Qué significa |
|---|---|---|
| Atípicos de edad | 106 registros fuera de rango · 11 personas con más de 100 años · máximo 956,25 | Error de captura, no una población |
| Faltantes | 4 columnas con vacíos · la institución falta en el 12,1 % | Vacíos institucionales y geográficos (capítulo 14) |
| Atributos que cambian dentro de la misma persona | 42 género · 1 203 departamento · 1 389 gran área · 3 844 nivel · 8 755 clasificación | Ningún atributo es tan estable como se supone |
| Centenarios | 22 registros · 12 personas · 11 al colapsar | Un problema de unidades, no de datos (capítulo 13) |
| Duplicados | 0 | La base no repite una persona en una misma convocatoria |

Cada hallazgo obligó a una decisión, y todas se tomaron con la misma regla: **no borrar en
silencio**. Lo que se hace es medirlo, declararlo y explicar qué se hizo con ello.

**Si te preguntan:** «¿Qué es el análisis exploratorio?» — «La primera revisión de los
datos, la que se hace antes de analizarlos: mirar cada variable, cruzar dos, ver la
dispersión y detectar defectos.»

---

## 13. Registro contra persona: la lección 22 → 12 → 11

Durante la auditoría aparecían **dos cifras distintas para lo mismo**: 22 y 11 personas
centenarias. La tentación es elegir una y seguir. Lo que hicimos fue preguntar por qué no
coincidían, y la respuesta es que **no estaban contando lo mismo**:

| Unidad | Cuántos | Qué son |
|---|---|---|
| Registros | **22** | Filas con edad mayor a 100 en la base de 77 237 |
| Personas | **12** | Personas distintas que hacen esas declaraciones (5 con 1 registro, 5 con 2, 1 con 3, 1 con 4) |
| Personas, última observación | **11** | Al tomar una sola fila por persona —la de su última convocatoria, que es como se construye la base de análisis— |

La persona que «desaparece» tiene nombre y apellido numérico: `0000671819`. Declara
**115,51 años en 2015** y **16,92 en 2017**, así que su última observación ya no supera los
cien. Al colapsar a una fila por persona, esa persona se queda fuera del recuento.

Las tres cifras son correctas y no se contradicen: cuentan unidades distintas. El 22
coincide con la evidencia que el propio repositorio auditado dejó versionada; el 11 es la
cifra comparable de nuestro análisis; el 12 es el puente entre los dos.

**La lección vale para todo el proyecto.** Es la misma que la del capítulo 7: cuando dos
números parecen pelearse, muchas veces lo que pasa es que están contando cosas distintas.
Por eso el panel lo dice con una frase que conviene tener de memoria: **la unidad de
análisis correcta es la persona, no el registro**.

**Si te preguntan:** «¿Cuántos centenarios hay?» — «Veintidós registros, doce personas y
once al contar una sola fila por persona; las tres cifras son lo mismo contado en unidades
distintas.»

---

## 14. Faltantes: cuatro columnas y por qué no se rellenan

Un **faltante** es una celda vacía: el registro existe, pero ese dato no. El panel del
análisis exploratorio encontró vacíos en **cuatro columnas**, y las tres más afectadas son
institucionales o geográficas:

| Columna | Vacíos | Porcentaje |
|---|---|---|
| Institución de filiación | 9 326 registros | **12,1 %** |
| Código DANE de nacimiento | — | 5,9 % |
| Código DANE de residencia | — | 3,2 % |

La cuarta tiene menos proporción y no es variable del análisis. Y eso es la clave:
**ninguna de las cuatro columnas con vacíos es una variable del análisis principal**.

La decisión fue **no rellenarlas**. La razón tiene tres partes:

1. **Rellenar es inventar.** Un valor imputado es una estimación disfrazada de dato; si se
   usa para calcular, el cálculo hereda el disfraz.
2. **No hace falta.** Si la variable no entra en el análisis, imputarla no mejora nada y
   añade ruido.
3. **Se puede declarar.** Como los vacíos están concentrados en columnas institucionales y
   geográficas, se reportan tal como están y quien lea sabe qué tiene.

Por eso el informe dice que **no fue necesario imputar**, y lo presenta como un argumento a
favor del diseño: se eligieron variables que no dependían de esas columnas.

**Si te preguntan:** «¿Por qué no rellenaron los vacíos?» — «Porque ninguna de las columnas
con vacíos es variable del análisis, y rellenar es inventar: se reportan tal como están.»

---

## 15. El muestreo: 2 224 personas y una prueba contra el censo

Un **muestreo** es elegir una parte para no procesar el todo. Aquí hay una curiosidad que
conviene entender: **tenemos el censo completo** (las 30 086 personas), así que el análisis
principal se hace sobre el censo, no sobre una muestra. Entonces, ¿para qué muestrear?

Para **demostrar que el muestreo funciona**. Es una validación metodológica: si eliges una
muestra y el resultado de la muestra se parece al del censo, sabes que el método de
muestreo es bueno. Eso no se puede hacer casi nunca, porque casi nunca se tiene el todo.
Aquí sí.

El diseño:

| Pieza | Cómo es |
|---|---|
| Tipo | Muestreo aleatorio simple: cada persona tiene la misma probabilidad de ser elegida |
| Unidad | **Personas**, no registros |
| Reemplazo | Sin reemplazo: nadie sale dos veces |
| Semilla | **2026**: la misma semilla da siempre las mismas 2 224 personas, y así cualquiera repite el ejercicio |
| Marco | 30 086 personas |
| Tamaño | **2 224** personas, calculado con la fórmula de Cochran con corrección por población finita |
| Archivo | La lista de identificadores de la muestra queda guardada |

Y la prueba, que es lo bonito: **la retención de 2013 a 2021 es 56,18 % en el censo y
56,63 % en la muestra**. La diferencia es de **0,46 puntos porcentuales**: menos de medio
punto. El muestreo funciona.

**Si te preguntan:** «¿Para qué muestrear si tienen el censo?» — «Para probar que el
muestreo funciona: con el censo completo se puede medir el error de la muestra, y da menos
de medio punto.»

---

## 16. Celdas de 1, 7 y 3: cuando un solo caso pesa demasiado

Este capítulo explica el problema que justifica el paso siguiente del proyecto, así que
conviene entenderlo bien.

Un **estrato** es un subgrupo de la población con una característica común (por ejemplo,
los investigadores en categoría Emérito). Cuando se estima por estratos, cada persona
recibe un peso: cuántas personas del total representa.

El problema: en **tres de los seis pares de convocatorias**, el estrato de **Eméritos**
tenía **1, 7 y 3 observaciones**. Con tan pocas, la fórmula clásica se rompe: el peso de
esas personas se dispara y **una sola persona llega a representar a decenas**. Un resultado
así no se sostiene con datos; se sostiene con la fórmula.

La solución no fue borrar el estrato ni inventar casos. Fueron tres decisiones declaradas:

1. **Declararlo**: se dice que en ese par había 1, 7 y 3 casos, y que el resultado es frágil.
2. **Colapsar estratos**: juntar el estrato diminuto con uno vecino cuando tiene sentido.
3. **Usar un método que presta fuerza**: un estimador que, cuando la celda es pequeña, la
   acerca a la tendencia general en lugar de creerle los tres casos como si fueran la
   verdad absoluta.

Y dos mejoras que se midieron: **reponderar por categoría** reduce la varianza hasta un
**16,6 %**; **un estimador que usa un modelo como apoyo** llega a reducirla hasta un
**20,1 %**.

Guarda la idea, porque es la que justifica el capítulo 18: **cuando el dato es escaso, se
estima con ayuda, no se inventa**.

**Si te preguntan:** «¿Por qué no estimaron los Eméritos?» — «Porque en tres de los seis
pares había 1, 7 y 3 casos, y con tan poco la fórmula clásica se rompe; se declaró y se usó
un método que presta fuerza a la celda pequeña.»

---

# PARTE IV · Trayectorias y cierre

## 17. La herramienta de trayectorias y la movilidad

La **herramienta de trayectorias** cambia el punto de vista: en vez de mostrar promedios,
deja buscar a **una persona concreta** y ver su historia —en qué convocatorias aparece, en
qué categoría estaba en cada una, en qué institución, en qué departamento y cuándo dejó de
aparecer—. Lo que el panel muestra en grande, la herramienta lo muestra persona por persona.

**La movilidad, medida.** Las categorías del sistema son cuatro y van de menor a mayor:
**Junior → Asociado → Sénior → Emérito**. Entre 2019 y 2021 hubo **13 355 personas**
presentes en las dos convocatorias, y su movimiento fue:

| Movimiento | Personas |
|---|---|
| Ascendieron de categoría | **2 336** |
| Se mantuvieron | **9 657** |
| Descendieron | **1 362** |

Es una foto con dos lecturas. La primera: la movilidad es **ascendente y masiva** —más
gente sube que baja, y de lejos—. La segunda: **el descenso también existe** y no es un
detalle; es el doble de lo que uno supondría si solo mirara los titulares.

Y la moraleja de la herramienta: **el promedio esconde historias**. Hay quien asciende y
desaparece al año siguiente, quien se mantiene las seis convocatorias y quien entra una
sola vez y no vuelve. Eso solo se ve mirando a la persona.

**Si te preguntan:** «¿La gente asciende o desciende?» — «Asciende más de lo que desciende:
en 2019 a 2021 ascienden 2 336, bajan 1 362 y se mantienen 9 657.»

---

## 18. XGBoost y lo bayesiano, sin tecnicismos

### Qué es un modelo de árbol

Piensa en un cuestionario de preguntas encadenadas: «¿es Sénior?», «¿trabaja en Antioquia?»,
«¿tiene doctorado?». Cada pregunta parte el grupo en dos. Un **árbol** es exactamente eso:
una secuencia de preguntas de sí o no que termina en una predicción. Un modelo como el que
vamos a usar construye **muchos árboles** y los combina; el nombre del motor es **XGBoost**.

**Tabular** significa que los datos están en una tabla, como los nuestros: una fila por
persona y una columna por variable.

### Por qué se elige

Cuatro razones, todas verificables:

1. **Maneja muchas variables de categoría a la vez** —categoría, área, territorio, género,
   edad, institución— sin que haya que especificar a mano cómo se combinan.
2. **Captura interacciones**: que el efecto de una variable dependa de otra (por ejemplo,
   que la edad pese distinto en Ingeniería que en Humanidades).
3. **Es explicable**: se puede medir cuánto aporta cada variable al resultado.
4. **Es el que propuso el docente** para este corte. No lo elegimos a ciegas.

### El riesgo: escasez

Con seis convocatorias hay **seis puntos en el tiempo**. Cuando se desagrega —por
categoría, por área, por departamento— hay celdas con muy pocos casos. Con tres
observaciones, un modelo convencional se vuelve inestable: los números cambian mucho con un
solo caso de más. Es el mismo problema del capítulo 16, ahora en el modelo.

### Qué es lo bayesiano, aquí

Lo bayesiano es una forma de estimar que **empieza con una idea razonable** (por ejemplo,
que la categoría pesa en la permanencia, porque el negocio lo sugiere) y luego **deja que
los datos la corrijan**:

- con **pocos datos**, el resultado se apoya más en esa idea general y avisa de que hay
  poca información;
- con **muchos datos**, se apoya en la evidencia y la idea general pesa menos.

Dicho simple: **no da una cifra tajante cuando no hay con qué sostenerla**. Es exactamente
lo que pedía el problema de las celdas de 1, 7 y 3 observaciones: una forma honesta de
estimar sin inventar.

**Importante para la exposición:** este modelo es el **norte del próximo corte**. Hoy
tenemos diagnóstico, verificación y descripción; no una predicción terminada.

**Si te preguntan:** «¿Por qué ese modelo?» — «Porque maneja bien muchas variables de
categoría a la vez, mide cuánto aporta cada una y es el que propuso el docente; lo bayesiano
lo acompaña para que no invente cuando hay pocos casos.»

---

## 19. Lo que queda abierto

Una exposición honesta no termina en «todo está resuelto». Termina enumerando lo que queda
abierto y por qué se dice así. Hay cuatro cosas en esa lista:

| Qué queda abierto | Cómo se dice | Por qué |
|---|---|---|
| La convivencia con la técnica anterior | «La técnica anterior quedó guardada como respaldo; el sistema lo registra como advertencia, no como falla» | La decisión nueva ya está implementada (D007); la vieja (D002) se conserva a propósito porque es el método por defecto y el respaldo. Capítulo 10 |
| F2-8 y F2-9 fuera de fase | «Dos análisis quedaron fuera de esta fase: los descriptivos por convocatoria y extender la inferencia» | F2-8 repetía el terreno del análisis exploratorio con otro diseño; F2-9 era extensión, no bloqueo. Capítulo 5 |
| La productividad (F2-1) | «No evaluable por restricción de acceso, no por método» | El archivo de 1,2 GB no está versionado. Capítulo 6 |
| La sección resumida copiada | «Una sección está copiada literal, y está declarada» | Es la otra advertencia del sistema: se ve, no se oculta. Capítulo 10 |

A eso se suma una frase que no se puede olvidar: **el modelo predictivo aún no existe**.
Lo que hay hoy es diagnóstico (qué pasó), verificación (que no nos equivoquemos) y
descripción (cómo se mueve la gente). La predicción es el norte del próximo corte.

Y por qué se dice así, en tres razones: porque la pestaña de límites y los informes lo
tienen escrito; porque una ausencia declarada es más útil que un resultado a medias; y
porque el lector —el docente, el próximo equipo— necesita saber **qué no** encontró en el
paquete antes de confiar en lo que sí.

**Si te preguntan:** «¿Qué les falta?» — «Cuatro cosas declaradas: la convivencia con la
técnica anterior, dos análisis fuera de fase, la productividad que no era evaluable y una
sección copiada; ninguna bloquea lo entregado y todas están escritas.»

---

# PARTE V · Las preguntas difíciles

## 20. Las doce preguntas difíciles

Cada pregunta trae la respuesta de una línea —para decir en voz alta— y el porqué —para
entender qué hay detrás y no improvisar una variante—. Las diez primeras son las del
guion; las dos últimas no están en él, pero son las que más probablemente salgan.

### 1. «¿Usaron inteligencia artificial para hacer esto?»

**Respuesta de una línea:** «Sí, y lo decimos por escrito: usamos un asistente como
herramienta de trabajo, para escribir código y revisar documentos. **No es una fuente de
datos.**»

**Por qué:** cada cifra de un panel sale de un archivo del repositorio, y el sistema de
reglas verifica que los documentos no citen cifras viejas. Si el asistente escribe algo
incorrecto, el sistema lo detecta y la compilación se detiene. La transparencia no es un
adorno: es una de las respuestas del panel.

### 2. «¿Por qué no hay un análisis de productividad?» (F2-1)

**Respuesta de una línea:** «Porque necesita el archivo de 1,2 GB con los productos de cada
autor, que no está guardado en ningún repositorio y no se puede descargar sin conexión; lo
cerramos como no evaluable por falta del dato, no por falta de método.»

**Por qué:** podríamos haber entregado algo a medias, pero una cifra sin dato que la
respalde es peor que una ausencia declarada. El capítulo 6 tiene el detalle completo.

### 3. «15 PASA y 2 ADVERTENCIA… ¿el sistema está fallando?»

**Respuesta de una línea:** «No: fallas hay cero; las dos advertencias son excepciones que
el sistema ve, no oculta y deja escritas.»

**Por qué:** una **falla** sería una contradicción real —un dato con dos valores, una
decisión que el código no implementa—. Las dos advertencias no son contradicciones: una es
una sección resumida copiada literal, y la otra es una decisión vieja conservada a
propósito como respaldo. Las dos están revisadas y aceptadas. Cero fallas significa que
ninguna contradicción pasó el filtro.

### 4. «¿Qué pasa si otro equipo quiere repetir esto?»

**Respuesta de una línea:** «Todo está en el repositorio: los datos, los resultados, los
informes y las reglas; se regenera con un comando y hay un archivo que levanta el panel en
local, sin instalar nada.»

**Por qué:** no depende de internet —la tipografía va incrustada en la página—, y el
sistema de reglas vuelve a comprobar todo cuando alguien regenera. El panel no es una
imagen: es un documento que se construye a partir de los archivos de resultados.

### 5. «¿Cómo sabemos que las cifras del panel son las correctas?»

**Respuesta de una línea:** «Por tres vías: cada análisis deja sus comprobaciones —56, todas
en verde—, hay verificadores independientes que comparan el panel contra los archivos, y las
reglas comparan lo que dicen los documentos contra lo que dicen los datos.»

**Por qué:** son tres controles de naturaleza distinta. Si uno se equivocara, otro lo
detectaría. Cuando algo se desalinea, el sistema lo nombra con archivo y línea: no dice «hay
un problema», dice **dónde**.

### 6. «¿Por qué XGBoost y no un modelo más sencillo?»

**Respuesta de una línea:** «Porque el problema tiene muchas variables de categoría con
interacciones, y ese modelo las maneja sin que haya que especificar cada combinación a mano;
además es el que propuso el docente y se puede medir cuánto aporta cada variable.»

**Por qué:** un modelo más sencillo obligaría a decidir a mano todas las interacciones, y
con seis puntos en el tiempo no hay datos para decidir tanto. El árbol hace ese trabajo y
deja el resultado explicable.

### 7. «¿Qué es lo bayesiano exactamente?»

**Respuesta de una línea:** «Es una forma de estimar que incorpora lo que ya sabemos antes
de mirar los datos, y que **no da una cifra tajante cuando no hay con qué sostenerla**.»

**Por qué:** si un departamento tiene tres observaciones, el modelo no le cree tres datos
como si fueran la verdad absoluta: los acerca a la tendencia general y avisa de que hay poca
información. Es exactamente lo que hace falta con celdas de 1, 7 y 3 casos.

### 8. «¿Y si el próximo grupo no sabe estadística?»

**Respuesta de una línea:** «Por eso el panel tiene una pestaña de «Límites y falencias» y
los informes dicen qué no se pudo hacer y por qué; la idea es que se pueda seguir sin
nuestra ayuda.»

**Por qué:** los números se recalculan solos y las reglas avisan cuando algo queda viejo.
El equipo siguiente no necesita recordar las cifras: necesita poder regenerarlas.

### 9. «¿Cuál es el hallazgo que más les sorprendió?»

**Respuesta de una línea:** «Los 22 registros de centenarios que en realidad son 11
personas, y el momento en que el sistema nos bloqueó nuestra propia entrega por diez cifras
viejas.»

**Por qué:** el primero enseña que dos cifras que parecen contradecirse muchas veces están
contando cosas distintas. El segundo demuestra que el mecanismo de verificación sirve para
lo que fue inventado: nos detuvo a nosotras.

### 10. «¿Cuánto de esto es trabajo del Grupo 8 y cuánto de ustedes?»

**Respuesta de una línea:** «El repositorio auditado es de ellos y no le cambiamos ni un
byte: está guardado como prueba; nuestro aporte es la auditoría, los análisis propios y el
sistema de verificación.»

**Por qué:** cuando corregimos algo, va en una copia aparte y queda registrado el porqué
(34 arreglos sobre 18 archivos). Así se puede distinguir siempre qué es del auditado y qué
es nuestro.

### 11. «¿Qué es eso del sistema de memoria y el grafo?» (pregunta previsible)

**Respuesta de una línea:** «Son piezas que le permiten al proyecto **saber qué contiene y
revisarse solo**: un índice para encontrar los párrafos por tema, un mapa de relaciones y
las reglas de validación.»

**Por qué:** es código que no depende de la red ni de un modelo de lenguaje para funcionar;
es determinista. El índice tiene 151 fragmentos de 25 documentos; el mapa, 255 nodos y 500
aristas. Sirve para que quien escriba después pueda consultar qué se dijo de un tema antes
de contradecirlo.

### 12. «¿Por qué el panel dice 56 y ustedes hablan de 15?» (pregunta previsible)

**Respuesta de una línea:** «56 es el total de la regla, pero 41 de esos fallos son de
género y el género no prueba que sean dos personas; **la cifra de identidad es 15**.»

**Por qué:** el propio análisis exploratorio documenta que el género no es estable en este
registro (42 personas cambian de género entre convocatorias). Un fallo solo de género no
indica que el identificador designe a dos personas; un fallo de edad sí pone la trayectoria
en duda. El capítulo 7 tiene el detalle.

**Si te preguntan:** «¿Y esto para qué me sirve?» — «Para que, si la pregunta sale en otro
tono, tengas la respuesta de una línea y el porqué al lado.»

---

## 21. Las cuatro cosas que no se dicen, y qué se dice en su lugar

Estas cuatro son tan importantes como las cifras: un titular exagerado arruina una
exposición honesta.

| No decir | Qué se dice en su lugar | Por qué |
|---|---|---|
| «Hicimos los diez análisis» | «Ocho cerrados de diez: siete entregados y uno no evaluable, más el de flujos» | F2-1 no era evaluable y F2-8/F2-9 quedaron fuera; la cifra honesta es la del panel |
| «No quedan límites» | «Hay una advertencia declarada, un análisis no evaluable y dos frentes fuera de fase, y todo está en la pestaña de límites» | Ocultar los límites rompe la confianza; declararlos la construye |
| «El modelo va a predecir quién se queda» | «Es el norte del próximo corte: hoy tenemos diagnóstico, verificación y descripción» | La predicción todavía no está hecha; prometerla es vender humo |
| Improvisar una cifra | «No lo tengo a mano, se lo confirmo después» | Una cifra inventada en vivo destruye en diez segundos lo que la auditoría construyó en semanas |

Las cuatro comparten la misma lógica: **es mejor una respuesta pequeña y verificable que
una respuesta grande y dudosa**.

**Si te preguntan:** «¿Qué es lo que no deben decir?» — «Nada que exagere: ni "diez
análisis", ni "no quedan límites", ni "el modelo predecirá", ni una cifra improvisada; lo
que se dice es siempre lo que está en el panel y en la tabla de bolsillo.»

---

# ANEXO A · El archivo de 1,2 GB, con todo el detalle

Este anexo es la respuesta completa a «¿por qué no hay análisis de productividad?», la
pregunta que más sale. El capítulo 6 lo cuenta en corto; aquí está todo: la ficha, qué
contiene, por qué no se pudo evaluar, qué habría permitido hacer y las cuatro preguntas
que suele provocar.

## A.1 La ficha

| Dato | Valor |
|---|---|
| Nombre real | `produccion_grupos.csv` |
| Tamaño | ≈ 1,2 GB |
| Filas | 3 166 629 (3,2 millones) |
| Autores únicos | 77 401 |
| Grano | Una fila por producto-autor |
| Origen | API pública Socrata, conjunto `33dq-ab5a`, descarga paginada |
| Dónde vivía | En el repositorio auditado, en `datos/raw/` (excluido por el control de versiones) |
| ¿Está versionado? | **No**, en ninguna parte |
| ¿Se puede recalcular? | **No** |
| Evidencia que quedó | 8 archivos de producción: se leen, no se recalculan |

## A.2 Qué contiene (la corrección de «revistas»)

El archivo **no es una lista de revistas**. Es el **registro de productos por autor**: una
fila por cada producto publicado —artículo, libro, capítulo— con su autor y sus datos,
entre ellos **la revista donde salió**.

La frase del guion y del panel, «un archivo de 1,2 GB con las revistas», es una
simplificación comprensible: habla del mundo de las publicaciones. Pero si alguien
pregunta, la respuesta precisa es esta: **«el registro de los productos publicados por
cada investigador, con la revista de cada uno»**.

Por qué importa: el análisis F2-1 iba a medir productividad por categoría, autoría no
reconocida y brecha de género en los productos. Todo eso necesita **productos**, no una
lista de revistas. Y con la frase precisa se entiende por qué el archivo pesa 1,2 GB: no
son nombres de revistas, son millones de productos.

## A.3 Por qué no se pudo evaluar (tres razones encadenadas)

| Razón | Detalle | Consecuencia |
|---|---|---|
| **No está versionado** | Pesa demasiado para un repositorio; el auditado lo excluyó a propósito con el control de versiones | No existe en ningún repositorio, ni en el del auditado ni en el nuestro |
| **Requiere red** | Se descarga por la API pública, por páginas, y la disponibilidad es **intermitente** | No es un archivo que se abre: hay que volver a descargarlo, y a veces no responde |
| **No se puede recalcular** | Del auditado solo quedan **8 archivos de evidencia** sobre la producción; se pueden leer, no recalcular | Auditamos el número, no lo reconstruimos |

Las tres se encadenan: sin el archivo no hay recálculo, y sin recálculo no hay auditoría
completa. Por eso el análisis se cerró como **«no evaluable por restricción de acceso, no
por método»** —la diferencia entre «no supe» y «no tengo el dato» es exactamente la
honestidad que se exige—.

El propio auditado descartó un análisis por la misma razón: el índice h se descartó porque
«el cruce de 3,2 millones de filas requiere descargar 1,2 GB y su disponibilidad es
intermitente». No es una excusa nuestra: es una limitación del dato.

## A.4 Qué habría permitido hacer (el alcance de F2-1)

La séptima pregunta del anteproyecto (Q7) pedía cruzar la producción con el padrón de
investigadores para tres cosas:

1. **Productividad por categoría**: cuánto publica, en promedio, un Junior frente a un
   Sénior.
2. **Autoría no reconocida**: qué proporción de los autores que publican no están
   reconocidos en el padrón.
3. **Brecha de género en los productos**: si la producción por persona difiere por género.

Ninguna de las tres es una pregunta difícil de formular; el problema es que **no hay con
qué responderlas**. Y una cifra de productividad sin el archivo de productos sería una
estimación disfrazada de dato.

## A.5 Los tres scripts que fallan por diseño

Tres programas del repositorio auditado dependen de ese archivo:

| Programa | Qué pasaría sin el archivo |
|---|---|
| `sprint5_produccion.py` | Falla al cargar la producción y **termina con código 3** |
| `sprint5_duckdb.py` | Mismo fallo al cargar la base de productos |
| `sprint6_ocde_composicion.py` | Mismo fallo al cruzar la composición |

No es un bug: es diseño. Salen con un aviso accionable en lugar de inventar producción,
y eso se documentó en la errata del repositorio. La decisión del proyecto auditado fue
declarar la ausencia, no fabricar la cifra —y esa decisión es correcta—.

## A.6 Las alternativas que se descartaron, y por qué

| Alternativa | Por qué se descartó |
|---|---|
| Bajar el archivo y quedárselo | Requiere red y la descarga es intermitente; además pesa demasiado para versionarlo |
| Usar el índice h como atajo | Se descartó por lo mismo: el cruce de 3,2 millones de filas requiere descargar 1,2 GB |
| Trabajar solo con las 8 evidencias | Se puede leer la evidencia, pero no recalcularla; una cifra leída no es una cifra auditada |
| Dejar F2-1 «a medias» | Preferimos una ausencia declarada a un resultado a medias que parezca completo |

El anteproyecto ya preveía el plan: si el dato no llegaba, se trabajaría con las
**evidencias versionadas y el catálogo**, y se declararía el límite. Eso es exactamente lo
que se hizo.

## A.7 Cuatro preguntas rápidas

**«¿Y no se les ocurrió descargarlo antes?»** — No consta en lo verificado cuándo se
intentó; lo que consta es que requiere conexión y que la descarga es paginada e
intermitente. El análisis no se cerró por olvido: se cerró porque el insumo no estaba.

**«¿No sirven las ocho evidencias que sí existen?»** — Sirven para **_leer_** qué dijo el
auditado sobre producción; no sirven para **_reconstruir_** su número. Auditar exige
recalcular, y sin el archivo no se puede.

**«¿Esto invalida la Fase 2?»** — No. Ningún análisis de la Fase 2 depende de ese archivo;
la comprobación cruzada lo verificó. F2-1 es el único frente que quedó bloqueado por el
dato, y así está declarado.

**«¿Qué haría falta para cerrarlo?»** — El insumo: el archivo, o una fuente equivalente que
llegue ya versionada. Con eso, la maquinaria de F2-1 se puede montar; hoy no existe.

## A.8 Dónde está documentado

| Archivo | Línea(s) | Qué dice |
|---|---|---|
| `03_informes/analisis_fase2/evaluacion_cumplimiento.md` | 120, 202, 267 | Q7 no evaluable; dataset `33dq-ab5a`, 3,2 M filas; «el hueco más grande del proyecto» |
| `03_informes/analisis_fase2/reporte_validacion_cruzada.md` | 504, 538 | Ningún script de la Fase 2 depende del archivo; F2-1 sin artefacto |
| `04_auditoria/ERRATA.md` | 154 | Los 3 scripts de producción fallan con FileNotFound por falta del archivo |
| `04_auditoria/repo_mejorado/CHANGELOG.md` | 40, 534, 731 | El archivo no está versionado; salen con código 3 por diseño |
| `04_auditoria/repo_original/README.md` | 29 | «Una fila por producto-autor», ~1,2 GB, excluido del control de versiones |
| `04_auditoria/repo_mejorado/datos/raw/README.md` | 8 | El archivo que se espera y no está |
| `documentacion_auditoria/README.md` | 245 | La producción no se pudo ejecutar por falta del archivo |
| `informe_consultoria_observatorio_minciencias.md` | 38, 84 | La ingesta de producción, ~1,2 GB paginada y excluida |
| `documentacion_auditoria/data/validacion/validacion_cierre_D.md` | 92 | El índice h se descartó por el tamaño y la disponibilidad intermitente |
| `documentacion_auditoria/data/validacion/validacion_anteproyecto_S.md` | 79 | Plan si el dato no llega: evidencias versionadas + catálogo |

**En una línea:** «Es el registro de los productos de cada autor —no una lista de
revistas—: un archivo de 1,2 GB que nunca se guardó en el repositorio y que, sin conexión
estable, no se pudo recalcular; por eso el análisis se declara no evaluable por falta del
dato, no por falta de método.»

---

# ANEXO B · Reconciliaciones de cifras (el anexo más útil en vivo)

Cuatro parejas de cifras que **parecen contradecirse y no se contradicen**. Este es el
anexo que conviene tener abierto: si alguien detecta una de las «contradicciones», la
respuesta ya está escrita. Cada sección trae la historia de cómo apareció la contradicción
y la tabla con la respuesta corta.

## B.1 Los centenarios: 22 → 12 → 11

**Cómo aparece.** Durante la auditoría, la evidencia que el auditado dejó versionada decía
**22** centenarios; nuestro análisis decía **11**. La tentación era elegir una cifra y
seguir. Lo que hicimos fue buscar por qué no coincidían, y la respuesta no estaba en el
dato: estaba en la **unidad de conteo**.

**Cómo se resolvió.** 22 **registros** con edad mayor a 100 → esos registros los declaran
**12 personas** distintas → al colapsar a una fila por persona (su última convocatoria)
quedan **11**. La persona que «desaparece» es `0000671819`: declara 115,51 años en 2015 y
16,92 en 2017, y su última observación ya no supera los cien.

| Si alguien dice… | La respuesta es… | Por qué |
|---|---|---|
| «Hay 22 personas centenarias» | «Hay 22 **registros** con edad mayor a 100» | Un registro es una fila (una persona en una convocatoria); una persona puede tener varias |
| «¿Y cuántas personas son?» | «**12 personas** distintas» | 5 con 1 registro, 5 con 2, 1 con 3 y 1 con 4 |
| «¿Por qué el panel dice 11?» | «Porque se cuenta **una sola fila por persona**: su última convocatoria» | Al colapsar, quedan 11 |
| «¿Quién desaparece?» | «`0000671819`: declara 115,51 años en 2015 y 16,92 en 2017; su última observación ya no supera 100» | Es también uno de los 15 del capítulo 7 |
| «La evidencia del auditado dice 22» | «Coincide: son registros. El 11 es la cifra comparable de nuestro análisis» | No se contradicen: cuentan unidades distintas |

## B.2 Ocho cerrados de diez contra nueve informes

**Cómo aparece.** El plan del anteproyecto tenía diez análisis; la carpeta de informes
tiene nueve. Ninguno de los dos números es falso: uno cuenta **lo cerrado del plan** y el
otro cuenta **informes entregados**.

**Cómo se resolvió.** Del plan de diez: siete entregados con informe y uno cerrado como no
evaluable (ocho cerrados); dos quedaron fuera de esta fase (F2-8 y F2-9). Además se añadió
el frente de flujos (F2-11), que no estaba en el plan, y existe el informe longitudinal de
otro objetivo, que sostiene las cifras de retención. Total de informes: nueve.

| Si alguien dice… | La respuesta es… | Por qué |
|---|---|---|
| «Hicieron diez análisis» | «**Ocho cerrados de diez**: siete entregados con informe y uno cerrado como no evaluable» | Dos quedaron fuera de esta fase (F2-8 y F2-9) |
| «¿Y el de flujos?» | «**Se añadió después**: no estaba en el plan de diez» | Es el frente F2-11 |
| «¿Cuántos informes hay en total?» | «**Nueve**: los siete de la fase, más flujos, más el informe longitudinal» | El longitudinal sostiene las cifras de retención (es de otro objetivo) |
| «¿Por qué 8 y 9 no cuadran?» | «El 8 cuenta lo cerrado del plan; el 9 cuenta informes» | El no evaluable no tiene informe, y el longitudinal no es un F2 |

## B.3 56 contra 15

**Cómo aparece.** La regla marca **56** identificadores; el hallazgo de identidad es
**15**. Si se dice «56 comprometen la identidad» se sobrestima el problema; si se dice «15
identificadores violan la regla» se queda corto.

**Cómo se resolvió.** Los 56 son el total de una regla con dos criterios: **41** fallan
solo en el género, **14** solo en la edad y **1** en las dos. Los que comprometen la
identidad —los que tienen una trayectoria de edad imposible— son los 14 de edad más el de
ambas: **15**. Los 41 de género son la inestabilidad que el análisis exploratorio ya
documentó (42 personas cambian de género) y no prueban que el identificador designe a dos
personas.

| Si alguien dice… | La respuesta es… | Por qué |
|---|---|---|
| «56 identificadores violan la regla» | «Sí: es el total. De ellos, **41 solo en el género, 14 solo en la edad y 1 en las dos**» | La regla tiene dos criterios |
| «¿Cuántos comprometen la identidad?» | «**15**: los catorce de edad más el que falla en ambas» | La cifra defendible es 15 |
| «¿Y los 41 de género?» | «Es la inestabilidad que el análisis exploratorio ya documentó: **42 personas cambian de género**» | El género no prueba que el identificador designe a dos personas |
| «¿Por qué no vale decir 56?» | «Porque 41 de los 56 no son un problema de identidad» | Decir 56 como problema de identidad sobrestima el hallazgo |
| «¿El auditado lo detectó?» | «Detectó otra cosa: su filtro marca **1 067 pares**, con **1 058 falsos positivos** y 9 falsos negativos» | No mira el lapso entre convocatorias ni las edades que retroceden |

## B.4 18 contra 15

**Cómo aparece.** El validador reporta **18** pares que incumplen la coherencia de edad; la
tabla del informe lista **15** identificadores. La diferencia no es un error de cuenta: es
un cambio de unidad, como en B.1.

**Cómo se resolvió.** La regla compara **pares consecutivos** de un mismo identificador:
18 pares fallan de los 47 151 comparados. Esos 18 pares pertenecen a **15 identificadores**
porque tres de ellos fallan en dos pares cada uno: `0000034380`, `0000671819` y
`0001378646`. El panel y la tabla de bolsillo usan la cifra de identificadores (15); los
18 son el detalle técnico.

| Si alguien dice… | La respuesta es… | Por qué |
|---|---|---|
| «Hay 18 identificadores con edad imposible» | «**18 pares**, no 18 identificadores: son **15 identificadores**» | Tres de ellos fallan en dos pares cada uno |
| «¿Cuáles fallan dos veces?» | «`0000034380`, `0000671819` y `0001378646`» | El resto falla en un solo par |
| «¿De dónde salen 18?» | «De **47 151 pares consecutivos** comparados: 18 fuera del margen de ±4 años» | La regla compara pares, no personas aisladas |
| «¿Cuántos digo en voz alta?» | «**15** identificadores; 18 es el detalle de pares» | El panel y la tabla de bolsillo usan 15 |

**En una línea:** «Cuando dos cifras se pelean, casi siempre están contando unidades
distintas: 22 registros, 12 personas, 11 filas; 8 de 10 del plan, 9 informes; 56 de la
regla, 15 de identidad; 18 pares, 15 identificadores.»

---

# ANEXO C · Glosario de bolsillo

El **único lugar** de la guía con los nombres técnicos entre paréntesis. En el cuerpo se
dicen en llano; aquí están para que puedas reconocerlos si alguien los usa, y para que no
te tomen por sorpresa. Cada entrada trae qué es, un dato concreto del proyecto y dónde
verificarlo.

## A

**Advertencia (ADVERTENCIA).** Uno de los tres estados de una regla: encontró una excepción
**declarada por escrito** y no detiene la entrega. Hoy hay **2** en el sistema, y las dos
están revisadas y aceptadas: la sección resumida copiada y la técnica anterior conservada
como respaldo. Ver capítulos 9 y 10; `evidencia_validacion.md`.

**Análisis exploratorio (EDA).** La parte del trabajo en que uno se sienta a **mirar los
datos antes de analizarlos**: recorrer cada variable, cruzar pares, medir la dispersión y
detectar defectos. En el proyecto son cuatro pestañas sobre **77 237 registros** de
**30 086 personas** en seis convocatorias. Ver capítulo 12.

**Árbol de decisión (XGBoost).** Modelo que encadena **preguntas de sí o no** y combina
muchos árboles para predecir; es la base del modelo del próximo corte. Se elige porque
maneja muchas categorías y se puede medir cuánto aporta cada variable. Ver capítulo 18.

**Atípico (valor atípico).** Un valor que se aleja mucho del resto; el criterio habitual lo
define el «bigote» de 1,5 veces el rango intercuartílico. En el proyecto marcó **106
registros** de edad fuera de rango. Ver `metodologia_muestreo.md` §3.

**Auditoría.** Reconstruir los números de otro con **sus** datos y anotar con archivo y
línea dónde no cuadran. No es opinar sobre el trabajo: es recomputarlo. Ver capítulo 1.

## B

**Bayesiano (enfoque bayesiano).** Forma de estimar que **empieza con una idea previa
razonable** y deja que los datos la corrijan: con pocos datos se apoya en la tendencia
general y avisa de que hay poca información. No da una cifra tajante sin evidencia. Ver
capítulo 18.

**Búsqueda semántica (TF-IDF, embeddings).** Encontrar los párrafos del repositorio más
parecidos a un tema. En el proyecto cubre **151 fragmentos** de **25 documentos** con
**49 749 términos**. Se usa antes de redactar, para no contradecir lo ya escrito. Ver
capítulo 20, pregunta 11.

## C

**Censura (datos censurados).** La persona sigue en el sistema al cerrar la ventana de
observación: no se le vio salir. En el proyecto afecta al **70,1 % (21 094 personas)**, y
por eso las curvas de permanencia están dominadas por la censura. Ver
`analisis_supervivencia.md` §1.

**Cohorte.** Grupo de personas que entran al sistema en el mismo momento. La cohorte de
2013 tiene **8 016 personas** y es la base del 56,18 % de retención. Ver
`analisis_longitudinal.md` §2.1.

**Compilación (compilar.py).** El programa que genera los PDF. Antes de escribir cada PDF
corre las reglas y, si encuentra una FALLA, se detiene. Ver capítulo 11.

**Cox (modelo de Cox).** Modelo que estima **cuánto cambia el riesgo de salir** según
todas las variables a la vez. Hallazgo del proyecto: la categoría domina y el género
desaparece al ajustar (HR 0,988). Ver `analisis_supervivencia.md`.

## D

**D002.** Decisión registrada de la **técnica anterior**: búsqueda por frecuencia de
palabras. Quedó **superada** por D007, pero se conserva a propósito como respaldo y como
método por defecto. Ver capítulo 10.

**D007.** Decisión registrada de la **técnica nueva**: búsqueda que entiende el
significado. Está **implementada**; sobre ella convive D002 como respaldo declarado. Ver
capítulo 10.

**Deuda declarada.** Excepción con **monto, fecha, motivo y responsable**: se sabe qué es,
por qué existe y quién la asume, así que se puede planear su pago. Es distinta de un error
silencioso. Hoy hay 2. Ver capítulos 9 y 10.

## E

**EDA.** Sigla de análisis exploratorio; ver esa entrada. Ver capítulo 12.

**Embeddings.** Representación **numérica del significado** de un texto: dos frases
parecidas quedan cerca aunque no compartan palabras. Es la técnica nueva de la búsqueda.
Ver capítulo 20, pregunta 11.

**Estimador asistido por modelo (GREG).** Estimador que usa un modelo como **apoyo**: en
lugar de creerle a una celda de tres casos, la acerca a la tendencia general. En el
muestreo redujo la varianza hasta un **20,1 %**. Ver `metodologia_muestreo.md` §5.

**Estrato.** Subgrupo de la población con una característica común, como la categoría
Emérito. El problema del proyecto: en tres pares de convocatorias, ese estrato tenía
**1, 7 y 3 observaciones**. Ver capítulo 16 y `metodologia_muestreo.md` §5.

## F

**FALLA.** Estado de una regla: encontró una **contradicción real** (un dato con dos
valores, una decisión que el código no implementa) y **detiene la compilación**. Hoy hay
**0**. Ver capítulo 9.

## G

**Grafo.** Mapa de **relaciones** del repositorio: documento → criterio → término, commit →
autor, archivo → capa. Tiene **255 nodos** y **500 aristas**. Ver `evidencia_validacion.md`
y capítulo 20, pregunta 11.

## I

**Índice de búsqueda (RAG).** El corpus **indexado** para poder buscar por tema: su tamaño
es el número de fragmentos. En el proyecto: **151 fragmentos** de **25 documentos**,
**123 505 palabras**. Ver `rag_indice.json:12` y capítulo 20, pregunta 11.

## K

**Kaplan-Meier.** Curva de permanencia que **no supone de antemano** la forma de la
salida: en cada momento calcula la probabilidad de seguir. En la cohorte de 2013 da
**S = 0,5618**, idéntico al 56,18 %. Ver `analisis_supervivencia.md` §1.

## L

**LITE.** La **versión resumida** de un documento, de unas cuatro páginas, pensada para leer
en voz baja antes de una reunión. Hay seis pares completo/LITE, uno por criterio. Ver
capítulo 10.

## M

**Muestra aleatoria simple (MAS).** Elegir personas **al azar**, sin reemplazo, todas con
la misma probabilidad. En el proyecto: **2 224 personas** con semilla **2026**. Ver
capítulo 15 y `metodologia_muestreo.md` §1.

**Mediana de supervivencia.** El tiempo en el que la mitad ya salió del sistema; con el
70,1 % de censura casi nunca se alcanza, así que el dato no se usa como titular. Ver
`analisis_supervivencia.md` §1.

**Modelo nulo.** Regla de comparación para juzgar si el patrón observado es **más de lo
que el azar produciría**. Se usa en la pestaña de redes y clustering. Ver panel F2,
pestaña 4.

## P

**PASA.** Estado de una regla: la comprobación salió bien. Hoy hay **15**. Ver capítulo 9.

**Post-estratificación.** **Reponderar** por categoría para que la muestra se parezca a la
población. En el muestreo redujo la varianza hasta un **16,6 %**. Ver
`metodologia_muestreo.md` §5.

## R

**Reglas de validación.** Las **17 comprobaciones automáticas** que se ejecutan antes de
dar un número por bueno: si una falla, la entrega no sale. Hoy: **15 · 0 · 2**. Ver
capítulo 8.

**Repositorio auditado.** El repositorio del **Grupo 8**. No se modificó: quedó como
prueba, intacto. Ver capítulo 1.

## S

**Semilla.** Número que **fija el azar**: la misma semilla da siempre la misma muestra.
En el proyecto, **2026**. Ver capítulo 15.

**Socrata.** Plataforma pública de **datos abiertos** de donde se descarga el archivo de
producción (conjunto `33dq-ab5a`). Ver Anexo A.

**Supervivencia.** Cuánto se queda la gente en el sistema **hasta salir**. En el proyecto:
**8 992 salidas** y 21 094 personas censuradas. Ver `analisis_supervivencia.md` §1.

## T

**TF-IDF.** La **técnica anterior** de la búsqueda: pondera cada palabra por su frecuencia y
compara los textos con esa medida. Es el método por defecto y el respaldo declarado. Ver
capítulo 10.

## V

**Verificador independiente.** Programa **aparte** que compara el panel contra los archivos
de resultados (cuántas gráficas, qué cifras). Hay varios, y se ejecutan a mano. Ver
capítulo 11.

## X · Y

**XGBoost.** El **motor** que combina muchos árboles de decisión; es el modelo del próximo
corte. Ver capítulo 18.

**YAML.** Formato de archivo de configuración legible: ahí viven las **decisiones
registradas** y las reglas. En el proyecto hay **10 decisiones** en ese formato. Ver
`documentacion_auditoria/data/`.

**En una línea:** «Los nombres técnicos están aquí, entre paréntesis, para reconocerlos si
alguien los usa; en el cuerpo se dicen en llano, y si preguntan, la respuesta corta es la
que está al lado.»

---

# ANEXO D · Mapa de archivos: dónde verificar cada cifra

Cada cifra del guion tiene un archivo y una línea. Hay tres rutas para comprobarla:

1. **El archivo:** abrir el informe o el JSON y leer la línea.
2. **La pantalla:** el panel que la muestra (capítulo 4).
3. **El comando:** volver a ejecutar la comprobación (`python -m memoria validar`).

Si una cifra no está en esta tabla ni en pantalla, no se dice.

| Cifra del guion | Fuente (archivo:línea) | Cómo se verifica |
|---|---|---|
| 77 237 registros · 30 086 personas · 6 convocatorias | `analisis_longitudinal.md` §1 (L10-18) | Abrir el informe y leer la primera tabla |
| 30 columnas · 0 duplicados | `analisis_longitudinal.md` L20 | Misma tabla y el párrafo siguiente |
| Retención 56,18 % (8 016 base, 4 503 retenidos) | `analisis_longitudinal.md` L54 | Abrir §2.1 y leer la frase inicial |
| Muestra 56,63 % · 0,46 pp de diferencia | `analisis_longitudinal.md` L260 | Tabla de la muestra frente al censo |
| 2 336 ascienden · 9 657 siguen · 1 362 bajan (13 355) | `analisis_longitudinal.md` L111 | Buscar «13 355» en el informe |
| 106 atípicos · 11 personas > 100 · máx. 956,25 | `metodologia_muestreo.md` §3 (L52) | Abrir el apartado «Edad» |
| Faltantes: 12,1 % institución (9 326) · 5,9 % · 3,2 % | `metodologia_muestreo.md` §4 (L60) | Tabla de faltantes |
| 2 224 personas · semilla 2026 | `metodologia_muestreo.md` §1 (L8, L104) | Primera línea y §4.3 |
| 16,6 % y 20,1 % de ganancia | `metodologia_muestreo.md` §5 | Buscar los porcentajes en las tablas de estimadores |
| 808 mudanzas · 18 430 comparables · 231 rutas · 53 metropolitanas | `flujos_territoriales.json` L24-25, L27, L2484 | Abrir el JSON: claves `movimientos`, `rutas` |
| 11 922 flujo por nacimiento | `flujos_territoriales.json` L2927 | Segunda clave `movimientos` del bloque de nacimiento |
| 56 de 19 215 · 41 / 14 / 1 · 15 identidad | `validacion_unicidad.json` (`ids_no_unicos`) | Abrir el JSON: `por_estado` e `interpretacion_por_rol` |
| 18 pares fuera de ±4 | `validacion_unicidad.json` (`contraste_con_la_implementacion`) | Clave `pares_marcados_documentada` |
| 1 067 pares · 1 058 falsos positivos · 9 falsos negativos | `validacion_unicidad.json` (`contraste_con_la_implementacion`) | Mismas claves |
| 15 PASA · 0 FALLA · 2 ADVERTENCIA | `evidencia_validacion.md` L7 (tabla L24-42) | Abrir el archivo o correr `python -m memoria validar` |
| 255 nodos · 500 aristas | `evidencia_validacion.md` L5 | Primera línea |
| 151 fragmentos · 25 documentos · 123 505 palabras | `rag_indice.json:12` | Abrir el índice o correr `python -m memoria validar` |
| 49 749 términos | `evidencia_validacion.md` L6 | Segunda línea del encabezado |
| 133 commits · 51 archivos | `evidencia_validacion.md` L30, L34 | Tabla de reglas: R5 y R9 |
| 10 decisiones · 4 fuentes externas | `evidencia_validacion.md` L40-41 | Tabla de reglas: R15 y R16 |
| 8 de 10 · F2-1 · F2-8 · F2-9 | Panel F2, tarjeta 1 (generada por `generar_dashboard_fase2.py`) | Clic en la pestaña «1 · Resumen ejecutivo» |
| 56 comprobaciones · 21 figuras | Panel F2, tarjeta 5 | Suma de los bloques `validaciones` y `figuras` de los 7 archivos de resultados |
| 1,2 GB · 3 166 629 filas · 77 401 autores | `evaluacion_cumplimiento.md` L120, L202 | Abrir el anexo A |
| 34 arreglos sobre 18 archivos | `04_auditoria/repo_mejorado/CHANGELOG.md` L15 | Abrir la tabla de arriba del CHANGELOG |
| 42 género · 1 203 depto · 1 389 gran área · 3 844 nivel · 8 755 clasificación | `analisis_longitudinal.md` L182 | Buscar «Atributos que cambian» |
| 21 094 · 8 992 eventos · 70,1 % censura · 36,1 % una sola convocatoria | `analisis_supervivencia.md` §1 (L17-32) | Tabla del diseño de supervivencia |
| 77 237 hechos · 0 huérfanos (modelo de datos) | Panel F2, pestaña 1 (`TABLA_RESUMEN` del generador) | Fila F2-3 de la tabla de análisis |
| Theil intra 0,1015 → 0,1023 (convergencia) | Panel F2, pestaña 2 (`TABLA_RESUMEN`) | Fila F2-2 de la tabla de análisis |
| p = 0,004 (corretaje concentrado) | Panel F2, pestaña 4 | Texto de la figura de redes |
| k = 1 · p = 0,762 (segmentación) | Panel F2, pestaña 4 | Texto del clustering |
| HR 0,988 · p = 0,575 (género en el ajuste) | Panel F2, pestaña 5 | Tabla del modelo de Cox |
| R12: sección `objetivo_6::04_relacion` copiada | `evidencia_validacion.md` L114-119 | Bloque `duplicados` del detalle de R12 |
| R15: D002 conservada como respaldo | `evidencia_validacion.md` L125-133 | Bloque `avisos` del detalle de R15 |

### Cómo se verifica en pantalla

La ruta siempre es la misma: **barra lateral → panel → pestaña → tarjeta o figura**. Por
ejemplo, para el 56: abrir la presentación, clic en «Fase 2», pestaña «1 · Resumen
ejecutivo», tarjeta «IDs que violan la regla». Para las 17 reglas: tarjeta «Reglas de
validación», o pestaña «6 · Calidad y reproducibilidad» para el detalle.

Y una cautela: **el panel se genera desde los archivos de resultados**, no al contrario. Si
un JSON cambia y el panel no se regenera, los verificadores independientes lo detectan
(capítulo 11).

**En una línea:** «Cada cifra del guion tiene un archivo y una línea; si no está en esta
tabla ni en pantalla, no se dice.»

---

# ANEXO E · El sistema de memoria, en una página

Cuatro piezas que le permiten al repositorio **saber qué contiene** y **revisarse solo**.
No dependen de la red ni de un modelo de lenguaje para funcionar: es código determinista.

| Pieza | Qué hace, en llano | Cifra | Cómo se ejecuta |
|---|---|---|---|
| **Sistema de memoria** | El conjunto de las cuatro; se usa como una caja de herramientas | — | `python -m memoria` (desde `documentacion_auditoria/src`) |
| **Búsqueda semántica** | Le das un tema o una pregunta y devuelve los párrafos más parecidos del repositorio | 151 fragmentos · 25 documentos · 123 505 palabras · 49 749 términos | `python -m memoria consultar "texto"` |
| **Grafo** | Un mapa de relaciones: documento → criterio → término, commit → autor, archivo → capa | 255 nodos · 500 aristas | `python -m memoria grafo` |
| **Validación** | Las diecisiete reglas del capítulo 8 | 15 PASA · 0 FALLA · 2 ADVERTENCIA | `python -m memoria validar` |
| **Compuerta** | La puerta de la compilación: si hay FALLA, el PDF no sale | exit 2 | `python documentacion_auditoria/src/compilar.py objetivo_1` |

**Por qué existe:** es la respuesta a «que la próxima persona no tenga que confiar en
nuestra palabra». Antes de redactar, se consulta qué se dijo de un tema; antes de compilar,
se validan las reglas. El sistema no arregla nada por su cuenta: informa y bloquea.

## Un recorrido de ejemplo

Así se usa en la práctica, en orden:

1. **Si cambió un documento**, se reindexa (`python -m memoria indexar`). Si no, se salta.
2. **Antes de escribir**, se consulta: `python -m memoria consultar "lo que va a decirse"`.
   Devuelve los párrafos más parecidos y evita contradecir lo ya escrito.
3. **Se redacta** el documento nuevo con esa información delante.
4. **Antes de compilar**, `python -m memoria validar` dice si algo quedó desalineado.
5. **Se compila** (`compilar.py nombre_del_documento`): la puerta vuelve a validar y, si hay
   FALLA, no escribe el PDF.

## Qué pasa si el índice está viejo

Si se edita un documento y no se reindexa, la búsqueda sigue viendo la versión anterior y
el número de fragmentos deja de cuadrar con los documentos. La regla R13 lo vigila y R17
avisa si algún documento cita una cifra vieja. Pero el sistema **no lo arregla solo**: te
lo dice para que lo arregles.

**Una cautela de fondo:** el sistema comprueba la **coherencia** de la documentación, no la
**verdad** de los datos. Una cifra puede ser perfectamente coherente con lo escrito y
seguir siendo falsa en la realidad. Para eso está la auditoría de la Fase 1, no el sistema.

**En una línea:** «Cuatro piezas para que el proyecto sepa qué contiene y se revise solo:
búsqueda, grafo, reglas y compuerta de compilación; no arreglan nada, informan y bloquean.»

---

# ANEXO F · Índice por concepto

Si en plena exposición olvidas qué era algo, búscalo aquí y sigue. Está ordenado como se
consulta: primero las cifras que se dicen en voz alta y después los conceptos por orden
alfabético. La columna central dice dónde se explica; la derecha es la frase que ya tienes
memorizada.

| Concepto | Dónde se explica | La frase de una línea |
|---|---|---|
| 1,2 GB | Anexo A · cap. 6 | «Registro de productos por autor; no evaluable por falta del dato» |
| 8 de 10 | cap. 5 · Anexo B.2 | «Ocho cerrados de diez, más el de flujos» |
| 15 · 0 · 2 | cap. 9 | «Cero fallas y dos excepciones declaradas» |
| 17 reglas | cap. 8 · Anexo C | «Comprobaciones que se ejecutan antes de entregar» |
| 18 pares | cap. 7 · Anexo B.4 | «15 identificadores; 18 es el detalle de pares» |
| 22 → 12 → 11 | cap. 13 · Anexo B.1 | «Unidades de conteo distintas» |
| 30 columnas | cap. 12 | «77 237 registros en 30 columnas» |
| 34 arreglos | cap. 1 | «34 arreglos sobre 18 archivos, con motivo» |
| 56 vs 15 | cap. 7 · Anexo B.3 | «Quince comprometen la identidad» |
| ADVERTENCIA | cap. 9-10 | «Excepción que el sistema ve, no oculta y deja escrita» |
| Análisis exploratorio (EDA) | cap. 12 | «La primera revisión de los datos» |
| Anteproyecto | cap. 5 | «De ahí viene la numeración F2-n» |
| Árbol de decisión | cap. 18 | «Preguntas de sí o no encadenadas» |
| Ascensos y descensos | cap. 17 | «2 336 suben, 1 362 bajan» |
| Asistente de IA | cap. 20 | «Herramienta declarada, no fuente de datos» |
| Atípicos | cap. 12 · Anexo C | «106 registros, 11 personas centenarias» |
| Auditoría | cap. 1 | «Reconstruir los números del otro» |
| Bayesiano | cap. 18 · Anexo C | «No da cifra tajante sin evidencia» |
| Búsqueda semántica | cap. 20, preg. 11 · Anexo E | «Encuentra los párrafos por tema» |
| Censura | cap. 17 · Anexo C | «70,1 % sigue al cerrar la ventana» |
| Censo | cap. 15 | «El todo: 30 086 personas» |
| Centenarios | cap. 13 | «22 registros, 12 personas, 11» |
| Compilación | cap. 11 | «El PDF no sale si una regla falla» |
| Copia mejorada | cap. 1 | «34 arreglos; el original no se toca» |
| D002 y D007 | cap. 10 | «La técnica anterior como respaldo declarado» |
| Deuda declarada | cap. 9-10 | «Excepción con motivo y responsable» |
| Eméritos (1, 7, 3) | cap. 16 | «Con tres casos la fórmula se rompe» |
| Estratos | cap. 16 | «Subgrupos con pocos casos» |
| Exit 2 | cap. 11 | «La compilación se detiene con aviso» |
| FALLA | cap. 9 | «Contradicción real, detiene la compilación» |
| Faltantes | cap. 14 | «4 columnas, ninguna variable del análisis» |
| Fuera de fase | cap. 5 | «F2-8 y F2-9: mismo terreno, otro diseño» |
| Grafo | cap. 20, preg. 11 · Anexo E | «255 nodos y 500 aristas» |
| Índice de búsqueda | cap. 20, preg. 11 · Anexo E | «151 fragmentos de 25 documentos» |
| Kaplan-Meier | cap. 17 · Anexo C | «Curva de permanencia sin suponer la forma» |
| LITE | cap. 10 | «La versión resumida de cuatro páginas» |
| Muestra 2 224 | cap. 15 | «Aleatoria simple, semilla 2026» |
| Movilidad | cap. 17 | «Ascienden más de lo que bajan» |
| Nueve informes | cap. 5 · Anexo B.2 | «Los siete de la fase más flujos y longitudinal» |
| Panel y pestaña | cap. 4 | «Tres paneles grandes, ocho pestañas» |
| PASA | cap. 9 | «Comprobación que salió bien» |
| Post-estratificación | cap. 16 | «Reponderar por categoría» |
| Productividad | cap. 6 · Anexo A | «F2-1, no evaluable» |
| R12 y R15 | cap. 8 · Anexo C | «Las dos advertencias con nombre» |
| Reglas de validación | cap. 8 | «Se ejecutan solas y pueden tumbar la entrega» |
| Repositorio auditado | cap. 1 | «No le tocamos ni un byte» |
| Residuo · ±4 años | cap. 7 | «Cuánto envejeció menos de lo que pasó el tiempo» |
| Semilla | cap. 15 | «2026: el mismo azar siempre» |
| Servidor local | cap. 2 | «El .bat y el localhost» |
| Sistema de memoria | cap. 20, preg. 11 · Anexo E | «Búsqueda, grafo, reglas y compuerta» |
| Supervivencia | cap. 17 · Anexo C | «Cuánto se queda la gente» |
| Tabular | cap. 18 | «Datos en tabla, como los nuestros» |
| Trayectorias | cap. 17 | «La lupa sobre el promedio» |
| Verificador independiente | cap. 11 | «Programa aparte que compara panel y archivos» |
| XGBoost | cap. 18 | «El motor del próximo corte» |
| YAML | Anexo C | «Formato de configuración de decisiones y reglas» |

**En una línea:** «Si en plena exposición olvidas qué era algo, búscalo aquí y sigue.»
