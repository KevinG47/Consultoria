# Análisis Multivariado

## 1. Análisis de Componentes Principales (ACP)

*Técnicas con variables numéricas*

En la base de datos analizada se cuenta con las siguientes variables:

Edad → variable numérica continua.

Nivel de estudio conseguido por el investigador → variable cualitativa ordinal (codificada con números, pero que representa categorías ordenadas).

Nivel del investigador → variable cualitativa ordinal (también codificada en números, pero que corresponde a jerarquías de categorías).


El Análisis de Componentes Principales (ACP) es una técnica multivariada cuyo propósito es reducir la dimensionalidad de un conjunto de variables cuantitativas, transformándolas en nuevas variables no correlacionadas llamadas componentes principales, que explican la mayor parte de la varianza total.


Requisitos fundamentales:

Contar con varias variables numéricas continuas.

Que exista una matriz de correlaciones significativa entre ellas.

En el presente caso:

Solo se dispone de una variable continua (Edad).

Las otras dos variables, aunque están codificadas como números, son en realidad cualitativas ordinales, por lo que no cumplen el supuesto de ser cuantitativas.



Conclusión: No es posible aplicar un ACP en esta base de datos, ya que no existen suficientes variables numéricas continuas para extraer componentes principales.

--------------------------------

## 2. Análisis Factorial (FA)

*Técnicas con variables numéricas*


El Análisis Factorial es una técnica multivariada que busca identificar factores comunes latentes que expliquen las correlaciones entre un conjunto de variables observadas.

Requisitos principales:

Contar con múltiples variables numéricas continuas.

Que dichas variables estén suficientemente correlacionadas para justificar la existencia de factores comunes.

En este caso:

Solo se dispone de una variable continua (Edad).

Las otras dos, aunque numéricas en apariencia, son en realidad ordinales categóricas y no cumplen con los supuestos del análisis factorial.

Conclusión: No es posible realizar un análisis factorial en esta base de datos, pues no se cumplen los requisitos básicos de contar con varias variables numéricas continuas correlacionadas.

--------------------------


## 3. Análisis de Correspondencia Simple (CA)

Con el propósito de explorar las asociaciones existentes entre variables categóricas relevantes dentro del conjunto de datos, se realizaron tres análisis de correspondencia simple (ACS).Cada análisis permitió identificar patrones y relaciones entre categorías, así como posibles agrupamientos o afinidades entre las modalidades de las variables estudiadas.

Los tres análisis efectuados fueron los siguientes:

**a) Relación entre el género del investigador y el gran área del conocimiento.**

Este análisis busca determinar si existen diferencias o concentraciones particulares de género en las distintas áreas del conocimiento, permitiendo observar posibles sesgos o desigualdades en la participación investigativa según el campo disciplinar.

**b) Relación entre el género del investigador y la universidad a la que pertenece.**

En este caso, el análisis permite observar si hay una asociación entre el género y la institución de afiliación, con el fin de detectar posibles patrones institucionales o diferencias en la composición de género entre universidades.

**c) Relación entre el nivel de formación del investigador y su clasificación como investigador.**

El objetivo de este análisis es examinar cómo se relacionan los niveles académicos alcanzados con la categoría de clasificación otorgada a los investigadores, identificando posibles tendencias o correspondencias entre formación y estatus investigativo.



### a) Género y Gran Área del Conocimiento


<img width="1440" height="900" alt="Captura de pantalla 2025-10-07 a la(s) 1 00 56 a m" src="https://github.com/user-attachments/assets/1600c806-7cff-4f0b-bf1f-b582b2eebee5" />


Se observa que en las dos primeras componentes se explica el 99.6% de la varianza, esto nos indica que se deberían escoger dos componentes. Ahora, en las contribuciones y cosenos cuadrados, nos indica algo similar, por lo que se escogen dos componentes.

<img width="1440" height="900" alt="Captura de pantalla 2025-10-07 a la(s) 1 07 35 a m" src="https://github.com/user-attachments/assets/25289893-a9d5-4c47-b6e9-f332517df861" />

La gráfica muestra que las personas que tienen género masculino están asociadas con la gran área de conocimiento, ciencias agrícolas, ciencias naturales y humanidades. 
Por otro lado, las personas del género femenino están asociadas con las ciencias médicas y de la salud. 
Las personas con género intersexual no están asociadas con nadie, al igual que no disponible.
Ingeniería y tecnología, ciencias sociales y no registra, no están asociadas con ningún tipo de género de los investigadores.


### b) Género y Universidad del Investigador


<img width="1440" height="900" alt="Captura de pantalla 2025-10-07 a la(s) 12 57 23 a m" src="https://github.com/user-attachments/assets/f7cc6560-7d0e-4b59-a518-72f437f0d071" />


Se observa que la varianza explicada por las dos primeras componentes es de 84.9% por lo que con dos dimensiones se puede explicar estas dos variables. Aunque sse observa en los cosenos y contribuciones que la dimension tres aporta, de igual manera solo se trabajara con las dos primeras dimensiones.


<img width="1440" height="900" alt="Captura de pantalla 2025-10-07 a la(s) 1 25 50 a m" src="https://github.com/user-attachments/assets/ac785bc8-82d4-41d4-a6e3-19bfc309a301" />


En la gráfica se observa que la universidad estadual do norte fluminense Darcy y Ribero y investigador independiente no se asocian con ningún género, las demás afiliaciones de universidades de los investigadores se asocian a masculino y femenino.
Además no disponible e intersexual, no se asocia a ninguna universidad.



### c) Nivel de Formación y Clasificación del Investigador

<img width="717" height="627" alt="Captura de pantalla 2025-10-07 a la(s) 1 37 08 a m" src="https://github.com/user-attachments/assets/81ce5ea4-620a-4aed-ad07-cf7855a0e60d" />

Se observa que la varianza explicada por las dos primeras componentes es de 98.8% por lo que con dos dimensiones se puede explicar estas dos variables. Los cosenos y contribuciones respaldan esta dicision.


<img width="1394" height="632" alt="Captura de pantalla 2025-10-07 a la(s) 1 48 31 a m" src="https://github.com/user-attachments/assets/5daa9f84-c1b1-4ff4-bf52-6b8dc39e5b6a" />


Los investigadores que tienen posdoctorado se asocian con los investigadores senior y emérito, esto teniendo sentido que entre más estudio poseas el investigador mayor su cargo como investigador.
El investigador junior está asociado con pregrado, magíster, especialidad médica y especialización.
Las demás no tienen asociación

-----------

## 4) Análisis de Correspondencia Múltiple (MCA)


Con el fin de examinar de manera conjunta la relación entre varias variables categóricas, se realizó un Análisis de Correspondencia Múltiple (ACM). Esta técnica permite identificar estructuras latentes o asociaciones entre categorías de distintas variables cualitativas, representando la información en un espacio reducido de dimensiones que facilita su interpretación visual y conceptual.

En este caso, el análisis se efectuó considerando las siguientes variables:

ID_VICTIMA_CONFLICTO: identifica si el investigador o sujeto pertenece a población víctima del conflicto.

TXT_GRUPO_ETNICO: describe el grupo étnico de pertenencia.

TXT_POBLACION_DISCA: indica si la persona se reconoce o no como parte de una población con discapacidad.

Estas tres variables fueron incluidas por su naturaleza cualitativa y su relevancia en el análisis de diversidad y condiciones diferenciales dentro de la población de investigadores. El objetivo principal fue explorar la posible asociación entre estas categorías y determinar si existen patrones o relaciones entre pertenecer a ciertos grupos étnicos, tener condición de discapacidad y haber sido víctima del conflicto.

.
<img width="614" height="621" alt="Captura de pantalla 2025-10-07 a la(s) 2 17 49 a m" src="https://github.com/user-attachments/assets/3a6ffdee-64e3-4396-9ca1-a39a25ca7e80" />
.

Se observa que oara cumplir con el 70% de varianza explicada se deben selecionar 9 dimensiones, ahora bien en la grafica despues de la priemra dimension hay una caida importante, esto nos indica que la primera dimension explica más varianza que las demas y despues de ella no se explica ni la mitad de la varianza en cualquier dimension.

Por cosenos cuadrados en las primeras dos dimensiones no se explica bien, en la variable de grupo etnico, Blanco o mestizo, Indígena, Palenquero, Afrocolombiano/Afrodescendiente, Raizal y en poblacion discapacitada, Auditiva, Física, Múltiple, Psicosocial, Visual. Esto se tendra en cuenta en la interpretación de la grafica.

En las contribuciones es similar que en los cosenos esto pasa por tener el 70% de la varianza en demasiadas dimensiones, por lo cual las observaciones se ven mejor contribuidas o con mejor coseno cuadrado en dimensiones altas como la 5 o 8. 

Por ahora se explicaran las dos primeras dimensiones, en tal caso que se requiera otra información se interpretara con otras dimensiones.

.
<img width="1398" height="632" alt="Captura de pantalla 2025-10-07 a la(s) 2 32 07 a m" src="https://github.com/user-attachments/assets/5a5f0329-79e3-47f3-a4ea-bb1f7dd272a6" />
.

Los investigadores que no son victimas del conflicto se asocian con las que no pertenecen a un grupo etnico.

Los investigadores que si son victimas del conflicto se asocian con que pertenecen a grupos etnicos como indigenas entre otros y tambien tienen discapacidad auditiva entre otros, pero como no se representan bien esas observaciones en esta dimensiones no se debe interprtar.

Se observa que las persoans que no tienen disponible la observación en grupo etnico y discapacidad se asocian igualmente se asocian con las perosnas que no registran haber sido victima de conflicto.

Las personas que pertenecen a un grupo etnico gitano y tienen discapacidad intelectual se asocian entre si

-----------------------

## 5) Análisis Factorial de Datos Mixtos (FAMD)

Introducción

Con el propósito de analizar de manera conjunta variables categóricas y numéricas relacionadas con las características de los investigadores, se aplicó un Análisis Factorial de Datos Mixtos (FAMD).
Esta técnica combina los principios del Análisis de Componentes Principales (ACP) —para variables cuantitativas— y del Análisis de Correspondencias Múltiple (ACM) —para variables cualitativas—, lo que permite representar ambas en un mismo espacio factorial de forma equilibrada.

El FAMD facilita la identificación de patrones conjuntos, agrupamientos naturales y relaciones multidimensionales entre los individuos y las variables, proporcionando una visión global de la estructura de los datos.

En este caso, el análisis se realizó considerando las siguientes variables:

ANO_CONVO: año de la convocatoria del investigador.

NME_GRAN_AREA_PR: gran área del conocimiento a la que pertenece el investigador principal.

NME_GENERO_PR: género del investigador principal.

ME_PAIS_NAC_PR: país de nacimiento del investigador.

EDAD_ANOS_PR: edad en años del investigador.

Estas variables combinan tanto información demográfica como académica, permitiendo explorar las relaciones entre la edad, el contexto geográfico y las características de participación científica.

Depuración de los datos

Previo al análisis, se revisó la base de datos con el fin de garantizar la consistencia y completitud de la información.
Durante este proceso se identificó una fila con un valor faltante (NA) en la variable EDAD_ANOS_PR, la cual es fundamental para el cálculo del FAMD al representar una variable numérica.
Dado que este valor ausente impedía la ejecución del procedimiento factorial —afectando el cálculo de las componentes principales—, se decidió eliminar dicha observación.

Esta eliminación no comprometió la integridad del conjunto de datos, ya que la observación no aportaba información sustancial al análisis, y su exclusión permitió ejecutar correctamente el modelo y obtener resultados interpretables.

.
<img width="1440" height="900" alt="Captura de pantalla 2025-10-07 a la(s) 1 02 42 p m" src="https://github.com/user-attachments/assets/c3ca8822-4102-4a4c-adfc-86e1491ffb1f" />
.

Se observa que dos componentes no es suficientes para el analisis completar el 70% de varianza explicada, este 70% se explica con las 10 dimensiones.

Los cosenos cuadrados y las contribuciones nos dicen que se debe elegir más de dos dimensiones, ya que las que sí están representadas en el análisis son 7 de 19 observaciones por las primeras dos componentes. De igual forma, la siguiente gráfica será de las dos primeras dimensiones, en tal caso que se requiera, se hará un análisis más exhaustivo con las observaciones que se requieran.


.
<img width="1440" height="900" alt="Captura de pantalla 2025-10-07 a la(s) 1 44 51 p m" src="https://github.com/user-attachments/assets/ba46a827-a02f-4d61-8a28-e5b992a40009" />
.


Los investigadores que nacieron en el exterior no se asocian con nada, pero los que nacieron en Colombia se asocian con los años tomados de la concocatoria, tambien con ciencias agricolas, ciencias natutares.


Los investigadores con genero masculino se asocian con con ciencias agricolas, ciencias batutares y el año de la concocatoria 2017


Los investigadores con genero femenino se asocian con las ciencias medicas y de la salud.

En el primer cuadrante se ecuentra la variable edad por lo que los investigadores con más años de vida se encuentran el la gran area de ciencias sociales.

## 6) Conclusión

En el presente análisis multivariado no se emplearon métodos estrictamente cuantitativos, ya que la base de datos no cuenta con suficientes variables numéricas continuas que permitan la aplicación adecuada de técnicas como el Análisis de Componentes Principales (ACP) o el Análisis Factorial.

En su lugar, se realizaron diferentes tipos de análisis de correspondencia:

Análisis de Correspondencia Simple (ACS): Se desarrollaron tres ejercicios con pares de variables categóricas, los cuales permiten identificar asociaciones claras y visualmente interpretables en dos dimensiones. Estos análisis fueron apropiados, ya que las relaciones entre las categorías se explican adecuadamente en los dos primeros ejes.

Análisis de Correspondencia Múltiple (ACM): Se aplicó con un conjunto mayor de variables cualitativas. Sin embargo, los resultados mostraron que no todas las variables quedan bien representadas en las dos primeras dimensiones, por lo que, si se desea realizar un estudio más profundo, sería necesario considerar un número mayor de dimensiones o aplicar un análisis más exhaustivo que permita capturar con mayor detalle la variabilidad de los datos.

Análisis Factorial Mixto (FAMD): Este método, que combina variables cualitativas y cuantitativas, tampoco logra explicar adecuadamente la estructura de los datos en las dos primeras dimensiones. Aunque permite visualizar relaciones generales entre las categorías y las variables numéricas, se concluye que, para obtener resultados más precisos, es necesario realizar un análisis complementario más detallado, considerando una mayor cantidad de componentes o técnicas adicionales.

En síntesis, el conjunto de análisis realizados permitió una exploración general de las asociaciones entre variables categóricas y mixtas, pero la limitada cantidad de variables numéricas y la complejidad de las relaciones hacen recomendable profundizar en estudios posteriores con técnicas más específicas o un mayor número de dimensiones.
