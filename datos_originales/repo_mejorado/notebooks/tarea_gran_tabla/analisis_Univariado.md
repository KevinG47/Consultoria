# Análisis univariado 

Este análisis univariado utiliza la base **“GRAN_TABLA (sin ID)”**, que recopila información de investigadores reconocidos por **MinCiencias** en tres convocatorias distintas.  
El conjunto de datos proviene de un modelo estrella que consolida variables sociodemográficas, académicas y geográficas de más de **50.000 registros**.

El objetivo de este documento es describir la estructura del conjunto de datos y analizar individualmente cada variable —numérica, categórica y temporal— mediante medidas estadísticas y visualizaciones simples.

## Exploración inicial del dataset

La base de datos contiene información consolidada de investigadores reconocidos en tres convocatorias de MinCiencias (2017, 2019 y 2021).  
En total incluye **50.891 registros** y **23 variables** que describen aspectos personales, formativos, geográficos y clasificatorios de cada investigador.

**Dimensiones del conjunto de datos:**
- Filas: 50.891  
- Columnas: 23  

**Tipos de variables detectadas:**
- **Numéricas (3):** `NRO_ORDEN_FORM_PR`, `ORDEN_CLAS_PR`, `EDAD_ANOS_PR`
- **Temporales (1):** `ANO_CONVO` (posteriormente convertida a formato fecha)
- **Categóricas (19):** resto de variables (género, área, clasificación, país, institución, etc.)

Esta exploración permitió determinar la estructura de la información y definir las técnicas apropiadas de análisis para cada tipo de variable.

## Análisis univariado – Variables numéricas

Se analizaron tres variables numéricas principales:

| Variable | Descripción | Tipo de análisis |
|-----------|-------------|------------------|
| NRO_ORDEN_FORM_PR | Nivel de formación alcanzado (orden jerárquico) | Dispersión y concentración |
| ORDEN_CLAS_PR | Nivel de clasificación dentro del sistema MinCiencias | Distribución y variabilidad |
| EDAD_ANOS_PR | Edad del investigador en años | Medidas de tendencia y dispersión |

**Resumen estadístico:**

| Variable | Media | Desviación Estándar | Mínimo | Mediana | Máximo |
|-----------|-------|----------------------|---------|----------|---------|
| NRO_ORDEN_FORM_PR | 16.49 | 1.01 | 0.00 | 17.00 | 18.00 |
| ORDEN_CLAS_PR | 12.55 | 0.75 | 12.00 | 12.00 | 15.00 |
| EDAD_ANOS_PR | 44.62 | 13.99 | 16.92 | 43.00 | 956.25 |

> *Nota:* el valor máximo atípico de 956 años corresponde a un error de digitación en la base original.

---

**Visualizaciones:**

- Distribución de `EDAD_ANOS_PR`  
 <img width="565" height="394" alt="image" src="https://github.com/user-attachments/assets/66adee20-6c8a-43a7-8d25-b51fe22e02a3" />


- Boxplot de `NRO_ORDEN_FORM_PR`  
 <img width="412" height="316" alt="image" src="https://github.com/user-attachments/assets/a0b953e8-3614-412c-a8e1-bdb28e703f8f" />


- Boxplot de `ORDEN_CLAS_PR`  
<img width="412" height="316" alt="image" src="https://github.com/user-attachments/assets/5127087e-c205-4ced-ac47-c826e080d0e7" />


---

### **Interpretación**

- **Edad:**  
  La media es de aproximadamente **45 años**, con una dispersión moderada (DE ≈ 14). La mayoría de investigadores se concentran entre los 35 y 55 años, reflejando una población adulta con experiencia científica.

- **Orden de formación:**  
  La concentración en valores altos (16–18) indica que la mayoría de los investigadores cuentan con **formación de posgrado avanzada** (maestría o doctorado).

- **Orden de clasificación:**  
  La media de 12.5 muestra predominio de **niveles intermedios** (asociado, junior) y pocos en niveles superiores (senior o emérito).


## Análisis univariado – Variables categóricas

El conjunto de datos incluye **19 variables categóricas**, relacionadas con información sociodemográfica, académica, geográfica y de clasificación.  
A continuación se destacan los principales patrones encontrados.

---

###  Distribución por género
<img width="635" height="456" alt="image" src="https://github.com/user-attachments/assets/92f2f21c-58d2-48b7-abfe-d5b12dbc533d" />

Predomina el **género masculino (≈61%)**, seguido por el **femenino (≈39%)**.  
Las categorías “intersexual” y “no disponible” tienen presencia mínima, lo cual sugiere una brecha de género persistente dentro del sistema de investigadores reconocidos.

---

###  Región de residencia
<img width="635" height="463" alt="image" src="https://github.com/user-attachments/assets/881d25f0-397f-4eef-a59a-dd51dd20401c" />


La mayoría de investigadores residen en el **Distrito Capital** y el **Eje Cafetero**, seguidos de las regiones **Caribe, Centro Oriente y Pacífico**.  
Esto evidencia una **concentración geográfica** del talento científico en los principales centros urbanos y académicos del país.

---

###  Gran área del conocimiento
<img width="635" height="541" alt="image" src="https://github.com/user-attachments/assets/7afad09d-975c-4622-9ba7-b62ef992de7d" />


Las áreas con mayor número de investigadores son:
- **Ciencias Sociales (≈30%)**
- **Ciencias Naturales**
- **Ingeniería y Tecnología**
- **Ciencias Médicas y de la Salud**

Esto demuestra una **diversificación disciplinar**, con predominio de las ciencias sociales, naturales e ingenierías.

---

###  Nivel de formación
<img width="635" height="513" alt="image" src="https://github.com/user-attachments/assets/aba638d9-f294-4f79-8d32-b38feb0451ea" />


Los niveles formativos más frecuentes son **Doctorado** y **Maestría/Magíster**, seguidos por **Postdoctorado** y **Especialidad médica**.  
Más del **85%** de los investigadores cuentan con formación de posgrado, lo que refleja un **alto nivel académico** en el sistema.

---

###  Clasificación
<img width="635" height="498" alt="image" src="https://github.com/user-attachments/assets/e1fb543b-05d5-4bd4-a51a-2ba345acf652" />


La mayor proporción corresponde a la categoría **Investigador Junior**, seguida de **Asociado** y **Senior**, con pocos **Eméritos**.  
Esto muestra una estructura **piramidal**, con amplia base de investigadores en formación o consolidación y un grupo reducido de investigadores altamente experimentados.

---

###  Otras observaciones generales

A continuación se resumen algunas variables relevantes no representadas gráficamente, que complementan el perfil general de los investigadores reconocidos:

---

####  País y región de nacimiento

| País de nacimiento | Frecuencia | Porcentaje aproximado |
|--------------------|-------------|------------------------|
| Colombia | 48.150 | 94,6% |
| Exterior | 2.634 | 5,2% |
| No disponible | 107 | 0,2% |

| Región de nacimiento (Top 5) | Frecuencia |
|-------------------------------|-------------|
| Distrito Capital | 12.894 |
| Eje Cafetero | 10.664 |
| Centro Oriente | 7.664 |
| Caribe | 7.399 |
| Pacífico | 6.704 |

---

####  Institución de filiación (Top 10)

| Institución | Frecuencia |
|--------------|-------------|
| Universidad de Antioquia | 2.178 |
| Universidad Nacional de Colombia (Bogotá) | 1.868 |
| Pontificia Universidad Javeriana | 1.431 |
| Universidad del Valle | 1.152 |
| Universidad de los Andes | 1.146 |
| Universidad Industrial de Santander | 898 |
| Universidad Pontificia Bolivariana | 737 |
| Fundación Universidad del Norte | 722 |
| Colegio Mayor Nuestra Señora del Rosario | 622 |
| Universidad de Caldas | 601 |

---

####  Grupo étnico y discapacidad declarada

| Grupo étnico (Top 5) | Frecuencia |
|-----------------------|-------------|
| No disponible | 30.468 |
| Ningún grupo étnico | 19.674 |
| Afrocolombiano / Afrodescendiente | 453 |
| Blanco o mestizo | 120 |
| Indígena | 114 |

| Tipo de discapacidad | Frecuencia |
|----------------------|-------------|
| No disponible | 30.470 |
| Ninguna | 20.240 |
| Visual | 68 |
| Física | 55 |
| Auditiva | 42 |

---

####  Víctimas del conflicto armado

| Condición | Frecuencia |
|------------|-------------|
| No registra | 30.468 |
| No | 20.002 |
| Sí | 421 |

---

## Análisis univariado – Variable temporal

La variable temporal corresponde al **año de convocatoria (`ANO_CONVO`)**, que identifica en qué proceso oficial de MinCiencias fue reconocido cada investigador.

---

###  Distribución por año de convocatoria
<img width="590" height="390" alt="image" src="https://github.com/user-attachments/assets/02188f8c-f425-4d7d-b3c4-58333b6fa588" />


| Año | Número de investigadores |
|------|---------------------------|
| 2017 | 13.001 |
| 2019 | 16.796 |
| 2021 | 21.094 |


Se evidencia un crecimiento sostenido en el número de investigadores reconocidos en Colombia a lo largo de las tres convocatorias.  

- De 2017 a 2019 hubo un incremento del **29%**,  
- y de 2019 a 2021 otro aumento del **26%**.  





