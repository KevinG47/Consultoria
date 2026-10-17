# Análisis de Agrupamiento de Investigadores – Informe Técnico

## 1. Descripción del Método

Para identificar perfiles homogéneos dentro de la población de investigadores, se aplicó un método de análisis multivariado no supervisado denominado K-Prototypes.

Este método fue seleccionado debido a que la base de datos contiene variables mixtas, es decir:

Cuantitativas.

Cualitativas.

A diferencia del método K-means, que solo admite variables numéricas, el método K-Prototypes permite:

Tipo de Variable	Medida que utiliza
Numérica	Distancia euclidiana (promedios en los centroides)
Categórica	Distancia por coincidencia de categorías (moda en los centroides)

Esto garantiza que los grupos resultantes reflejan similitud tanto en características académicas numéricas como en atributos institucionales y sociodemográficos.

## 2. Número de Clústeres Seleccionado

Se definió un modelo con 3 clústeres, seleccionado considerando:

Interpretabilidad de los grupos.

Estabilidad de resultados.

Diferencias sustantivas en los perfiles.

## 3. Resultados del Agrupamiento

Los perfiles obtenidos se resumen a continuación:

Clúster 1: Ciencias Sociales (Bogotá)

Edad promedio: ~45 años

Composición por área: 33% en Ciencias Sociales

Localización predominante: 38% en Bogotá D.C.
Este grupo representa investigadores en Ciencias Sociales, con una presencia significativa en universidades de la capital y edad laboral media-alta.

Clúster 2: Ciencias Sociales (Bogotá)

Edad promedio: ~47 años

Composición por área: 43% Ciencias Sociales

Localización predominante: 54% Bogotá D.C.
Este clúster es similar al primero en área y ubicación, pero se diferencia principalmente por:

Mayor edad promedio

Mayor concentración en instituciones de la capital
Sugiere académicos con trayectorias más consolidadas.

Clúster 3: Ingeniería (Eje Cafetero)

Edad promedio: ~42 años

Composición por área: 36% Ingeniería

Localización predominante: 64% Eje Cafetero
Este grupo concentra investigadores más jóvenes, con perfiles técnicos o ingenieriles, mayor descentralización geográfica y menor presencia en Bogotá.

## 4. Hallazgos Transversales

Un patrón común notable es que:

Más del 80% de los investigadores, en todos los clústeres, poseen títulos de Maestría o Doctorado.

Esto confirma la alta cualificación académica en el sistema analizado, independientemente del perfil disciplinar o regional.


## 5. Conclusión

El uso del método K-Prototypes permitió identificar tres perfiles representativos de investigadores en Colombia, integrando adecuadamente información cuantitativa y cualitativa.
Los resultados ofrecen evidencia útil para segmentar políticas de fomento, asignación de recursos, apoyos regionales y estrategias de fortalecimiento de comunidades académicas.
