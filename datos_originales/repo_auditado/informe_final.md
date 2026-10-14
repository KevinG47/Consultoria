# Informe final — Observatorio: Investigadores reconocidos (Minciencias) — Grupo 7

## 1. Introducción

Este informe presenta el trabajo final del proyecto realizado por el Grupo 7 en el marco del observatorio de investigadores reconocidos del Ministerio de Ciencia, Tecnología e Innovación (Minciencias) de Colombia. El objetivo general del proyecto fue consolidar y analizar la información de investigadores reconocidos a partir de tres convocatorias (2017, 2019 y 2021) para producir una base de datos única, verificar la consistencia de identificadores y construir un modelo dimensional que permita análisis descriptivos y analíticos para uso en la comunidad académica y en eventos de estadística. El trabajo incluye análisis descriptivos por convocatoria, integración de bases, verificación de unicidad de identificadores, modelado dimensional (esquema estrella) y análisis exploratorio y de segmentación sobre la "gran tabla" consolidadora.


## 2. Justificación y antecedentes

La identificación y el análisis de investigadores reconocidos por Minciencias son relevantes para comprender la distribución regional, disciplinaria y temporal del capital humano científico en Colombia. Consolidar convocatorias históricas facilita:

Analizar la trayectoria de los investigadores a través del tiempo.

Detectar duplicidades o inconsistencias en identificadores que impidan seguimiento longitudinal.

Construir un modelo de datos (estrella) que sirva como base para informes y visualizaciones en un observatorio.

Generar análisis exploratorios y clustering para segmentar perfiles investigativos y apoyar decisiones institucionales.

El repositorio del proyecto contiene las bases originales de cada convocatoria, los análisis descriptivos por base, scripts para unir las bases, procedimientos de verificación de IDs, la construcción de dimensiones y hechos, y análisis sobre una tabla resumen (“gran tabla”) sin identificadores personales.



## 3. Objetivos

### Objetivo general

Consolidar, validar y analizar los datos de investigadores reconocidos de las convocatorias 2017, 2019 y 2021 del Minciencias, y producir un modelo dimensional y un conjunto de análisis descriptivos y multivariados para facilitar su uso en el observatorio institucional.

### Objetivos específicos

Realizar un análisis descriptivo por cada base (2017, 2019 y 2021) para caracterizar variables clave (edad, género, área, afiliación, región, etc.).

Unir las tres bases en una única tabla maestra que contenga todas las convocatorias.

Verificar la unicidad de identificadores de investigador a través de reglas (comparación de edades y atributos).

Diseñar y crear un modelo dimensional (esquema estrella) con nueve dimensiones y una tabla de hechos.

Construir la “gran tabla” (sin IDs) y ejecutar análisis univariado, bivariado, multivariado y clustering para segmentar perfiles.


## 4. Metodología

### Fuentes de datos

Bases de datos de investigadores reconocidos de Minciencias correspondientes a las convocatorias 2017, 2019 y 2021 (archivos en el repositorio).

### Flujo de trabajo y pasos

#### 1) Exploración y análisis descriptivo por base

Carpeta: tarea_anlisis_bases_de_datos

Actividades: limpieza básica (tipos, NA), distribución de variables numéricas (edades), conteos por categorías (sexo, área, región, institución), identificación de valores extremos y missing. 

Resultados: tablas de frecuencias, histogramas y estadísticas resumen por variable.

#### 2) Unión de bases (join)

Carpeta: Tarea Join

Actividades: Uniones por Convocatoria. 

Resultado: base consolidada con registros para las tres convocatorias y campo(s) que indican presencia en cada convocatoria.

#### 3) Verificación de unicidad de ID

Carpeta: tarea_tabla

Procedimiento: para cada par de registros con nombres/patrón similar se compararon edades reportadas en distintas convocatorias; se asumió que si la diferencia de edad entre los registros es coherente con el lapso entre convocatorias y otra variable coincidente (Genero), se trata del mismo investigador y se valida un único ID. 

Resultado: aceptación de unicidad cuando la diferencia de edad y demás atributos eran consistentes; marcado de casos dudosos para revisión manual.


#### 4) Modelado dimensional (esquema estrella)

Carpeta: tarea_dimensiones_y_hechos

Diseño: se construyeron nueve dimensiones (por ejemplo: Dim-Investigador, Dim-Convocatoria, Dim-Universidad, Dim-Área, Dim-nacimiento, Dim-Género, Dim-residencia, Dim-formación, Dim-clasificación) y una tabla de hechos que centraliza métricas (p. ej. edad, victima de conflicto, grupo etnico y población discapacitada, además de los ID de las dimensiones). Normalización y llaves primarias/foráneas definidas.

Se adjunta el link de las dimensiones y la tabla de hechos:

https://usantotomaseduco-my.sharepoint.com/:f:/g/personal/paulaguevarag_usantotomas_edu_co/Ep57IXtzL95LspDjMxohEgkBXapmReFSNoizh_dpRlDpzQ?e=oVtJVU


#### 5) Construcción de la gran tabla y análisis exploratorio

Carpeta: tarea_gran_tabla

La gran tabla contiene solo variables informativas (sin IDs) derivadas de las dimensiones y campos de interés para análisis estadístico.

Análisis realizados:

Univariado: distribuciones y estadísticas resumen.

Bivariado: asociaciones entre variables categóricas (tablas de contingencia, chi-cuadrado) y correlaciones/ANOVA donde corresponda.

Multivariado: Analisis de correspondencia simple o multiple y analisis factorial de datos mixtos.

Clustering: segmentación para encontrar grupos homogéneos de investigadores según variables seleccionadas (residencia, edad, área).


### Herramientas y lenguajes

Lenguajes: Python , o R — según scripts en el repositorio.

Visualización: matplotlib/ggplot para gráficos descriptivos.

Documentación y reproducibilidad: notebooks y scripts guardados en las carpetas correspondientes.


## 5. Resultados y análisis de resultados


### 5.1 Análisis descriptivo por base (2017, 2019, 2021)

Se realizaron estadísticas descriptivas para cada convocatoria: conteos por área temática, género, región y tipo de institución.

Se identificaron patrones consistentes entre convocatorias (por ejemplo, sobre/representación en ciertas áreas o regiones) y variables que muestran mayor variabilidad entre años


Interpretación: los análisis descriptivos permiten detectar sesgos de cobertura (regiones/instituciones subrepresentadas) y orientar limpieza para el join y verificaciones de ID.


### 5.2 Verificación de unicidad de ID

Mediante comparación de edades entre convocatorias y otras variables coincidentes se verificó que, en la mayoría de casos, registros que correspondían a la misma persona conservaban un mismo ID o podían mapearse razonablemente.

Se estableció la regla práctica: si la diferencia de edad entre dos registros coincide con el lapso temporal entre convocatorias (±4 año tolerancia para errores de digitación) y al menos una otra variable coincide (genero), se acepta unicidad del ID. Los casos con conflicto quedaron marcados para revisión manual.


### 5.3 Modelo dimensional (esquema estrella)

Se definieron nueve dimensiones que describen atributos de los investigadores (persona, residencia, convocatoria, institucionales, formación, regionales, género, clasificación etc.) y una tabla de hechos

Interpretación: el esquema estrella es apropiado para el observatorio, ya que reduce la complejidad de consultas y es óptimo para reporting y dashboards.


### 5.4 Análisis sobre la gran tabla

Univariado: se describieron variables clave (medias, medianas, dispersiones) y distribuciones; variables con sesgo marcado o outliers fueron transformadas o anotadas.

Bivariado: se exploraron asociaciones (por ejemplo: área vs. tipo de institución, género vs. reconocimiento) mediante tablas cruzadas y pruebas de independencia; se identificaron asociaciones significativas en varios pares (detalles numéricos en los scripts).

Multivariado: se aplicaron técnicas de reducción de dimensión (MCA) para visualizar estructura y detectar variables más informativas.

Clustering: se realizó una segmentación que arrojó grupos diferenciados de investigadores. Cada cluster fue perfilado con estadísticas resumen y variables más discriminantes.

Interpretación general: la gran tabla permite análisis multi-ángulo: identificar perfiles, detectar desigualdades territoriales y priorizar líneas de acción institucional. El clustering ofrece insumos para políticas de apoyo focalizado según grupos.


## 6. Conclusiones y recomendaciones

La consolidación de convocatorias (2017, 2019, 2021) y la verificación de unicidad de IDs permiten construir trayectorias longitudinales de investigadores reconocidos y aportar insumos para toma de decisiones.

La heurística de verificación por edad (coherencia con lapsos entre convocatorias) es práctica, pero debe complementarse con revisiones manuales en casos dudosos. Si es posible, incorporar campos adicionales de verificación (correo institucional, documento nacional) mejorará la exactitud.

El modelo dimensional (nueve dimensiones + tabla de hechos) es adecuado para alimentar dashboards y reportes. Recomiendo implementar una instancia ligera de un data mart o una base relacional para consultas recurrentes.

Documentar las transformaciones (ETL) y guardar versiones de la gran tabla facilita reproducibilidad y auditoría.


## 7. Bibliografía


Ministerio de Ciencia, Tecnología e Innovación — Bases de datos de investigadores reconocidos (convocatorias 2017, 2019, 2021) https://minciencias.gov.co/ciudadano/datosabiertos



