# Marco Teórico — Observatorio de Ciencia, Tecnología e Innovación
## Investigadores Reconocidos por Convocatoria — Minciencias — Grupo 7

---

## 1. Contexto

El Ministerio de Ciencia, Tecnología e Innovación de Colombia (Minciencias) es la entidad rectora del Sistema Nacional de Ciencia, Tecnología e Innovación (SNCTI). Mediante convocatorias periódicas, Minciencias reconoce y clasifica a los investigadores activos del país, generando una base de datos oficial que constituye el principal insumo para la medición y el seguimiento del capital humano científico nacional.

El presente proyecto se enmarca en la construcción de un **Observatorio de Ciencia, Tecnología e Innovación** que consolide, analice y visualice la información de las convocatorias 2017, 2019 y 2021, facilitando la toma de decisiones basada en evidencia en materia de política científica.

---

## 2. Sistema Nacional de Ciencia, Tecnología e Innovación (SNCTI)

El SNCTI, creado mediante la Ley 1286 de 2009 y fortalecido por el Acto Legislativo 05 de 2011 y la Ley 1955 de 2019 (Plan Nacional de Desarrollo), está integrado por entidades públicas, empresas privadas, universidades, centros de investigación y la sociedad civil. Su propósito es articular esfuerzos para generar conocimiento, innovación y apropiación social de la ciencia como motores del desarrollo sostenible del país.

---

## 3. Reconocimiento de Investigadores

### 3.1 Proceso de clasificación

Minciencias clasifica a los investigadores a través de convocatorias nacionales que evalúan criterios como:

- **Producción científica**: artículos indexados, libros, capítulos de libro, patentes.
- **Formación de recursos humanos**: dirección de tesis de maestría y doctorado.
- **Transferencia de conocimiento**: participación en proyectos de extensión e innovación.
- **Colaboración en redes**: participación en redes nacionales e internacionales.

### 3.2 Categorías de clasificación

Los investigadores son ubicados en las siguientes categorías, de mayor a menor reconocimiento:

| Categoría         | Descripción                                                  |
|-------------------|--------------------------------------------------------------|
| Senior (Emérito)  | Trayectoria consolidada y producción de alto impacto         |
| Asociado          | Producción científica sostenida y vinculación a grupos       |
| Junior            | Inicio de trayectoria con producción demostrable             |
| Reconocido        | Cumple criterios mínimos de reconocimiento institucional     |

---

## 4. Datos Abiertos y Gobierno Abierto

Colombia ha adoptado políticas de datos abiertos bajo el marco del Gobierno Digital (anteriormente Gobierno en Línea), establecido en el Decreto 1078 de 2015 y la Política de Datos Abiertos del CONPES 3920 de 2018. Los datasets de investigadores reconocidos por Minciencias están disponibles en el portal [Datos Abiertos de Colombia](https://www.datos.gov.co) en formato CSV y XLSX de acceso libre.

---

## 5. Modelo Dimensional para Observatorios

El enfoque de **Data Warehousing** y el **esquema estrella** (Kimball, 1996) constituyen la base metodológica para la organización del repositorio analítico del observatorio. Este modelo permite:

- Separar hechos (métricas cuantitativas) de dimensiones (contexto descriptivo).
- Facilitar consultas analíticas eficientes sobre grandes volúmenes de datos.
- Construir tableros de control e informes con herramientas de visualización modernas (Streamlit, Power BI, Tableau).

### 5.1 Dimensiones identificadas

1. **Dim_Investigador**: información personal del investigador.
2. **Dim_Convocatoria**: año y nombre de la convocatoria.
3. **Dim_AreaConocimiento**: gran área, área y especialidad OCDE.
4. **Dim_Formacion**: nivel de formación.
5. **Dim_Clasificacion**: categoría obtenida.
6. **Dim_Genero**: género reportado.
7. **Dim_Nacimiento**: ubicación geográfica de nacimiento.
8. **Dim_Residencia**: ubicación geográfica de residencia.
9. **Dim_Institucion**: filiaciones institucionales.

### 5.2 Tabla de hechos

La **Fact_Investigador** centraliza los identificadores de cada dimensión junto con las métricas: edad, orden de formación, orden de clasificación y variables de equidad (víctima de conflicto, grupo étnico, discapacidad).

---

## 6. Análisis Estadístico Aplicado

### 6.1 Análisis Exploratorio de Datos (EDA)

El EDA permite caracterizar las distribuciones univariadas y multivariadas del dataset, identificar valores atípicos, datos faltantes y patrones iniciales que orientan las etapas posteriores del análisis.

### 6.2 Análisis Longitudinal

La disponibilidad de tres convocatorias (2017, 2019, 2021) permite realizar un **análisis longitudinal** para:

- Comparar la evolución del número y perfil de investigadores reconocidos.
- Detectar tendencias en la distribución por género, área y región.
- Identificar investigadores que mantienen o mejoran su categoría a lo largo del tiempo.

### 6.3 Análisis Multivariado y Clustering

Se aplicarán técnicas de reducción de dimensión (Análisis de Correspondencias Múltiples — MCA) y algoritmos de agrupamiento (K-Means, clustering jerárquico) para segmentar perfiles investigativos y apoyar decisiones de política científica focalizadas.

---

## 7. Herramientas y Tecnologías

| Herramienta   | Uso                                                      |
|---------------|----------------------------------------------------------|
| Python 3.10+  | Lenguaje principal de análisis                           |
| pandas        | Manipulación y transformación de datos                   |
| NumPy         | Cómputo numérico                                         |
| matplotlib / seaborn / plotly | Visualización                           |
| scikit-learn  | Machine Learning y clustering                            |
| Streamlit     | Tablero de control interactivo                           |
| Poetry        | Gestión de dependencias y entornos virtuales             |
| JupyterLab    | Entorno de notebooks para análisis interactivo           |
| Git / GitHub  | Control de versiones y colaboración                      |

---

## 8. Referencias

- Kimball, R., & Ross, M. (1996). *The Data Warehouse Toolkit*. John Wiley & Sons.
- Ministerio de Ciencia, Tecnología e Innovación. (2021). *Datos Abiertos — Investigadores reconocidos por convocatoria*. https://minciencias.gov.co/ciudadano/datosabiertos
- Departamento Nacional de Planeación. (2018). *CONPES 3920: Política Nacional de Explotación de Datos (Big Data)*. Bogotá: DNP.
- Ley 1286 de 2009. *Por la cual se modifica la Ley 29 de 1990 y se transforma a Colciencias en Departamento Administrativo*. Congreso de la República de Colombia.
- Acto Legislativo 05 de 2011. *Por el cual se constituye el Sistema General de Regalías*. Congreso de la República de Colombia.
