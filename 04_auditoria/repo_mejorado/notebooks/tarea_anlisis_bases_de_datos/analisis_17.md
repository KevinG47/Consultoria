# Análisis base de datos 2017

La base de datos contiene 13.001 registros y 30 variables, correspondientes a investigadores reconocidos en convocatorias.

## Descripción general:

Convocatorias: Identifica la convocatoria (ID_CONVOCATORIA, NME_CONVOCATORIA, ANO_CONVO).

Investigador: Incluye un identificador único (ID_PERSONA_PR) y variables sociodemográficas (género, edad, país y lugar de nacimiento, lugar de residencia, etnia, condición de víctima del conflicto, discapacidad).

Área de conocimiento: Se especifica el área específica (NME_ESP_AREA_PR), el área general (NME_AREA_PR) y el gran campo disciplinar (NME_GRAN_AREA_PR).

Formación académica: Nivel de formación (NME_NIV_FORM_PR), orden en el que se registra.

Clasificación del investigador: Nivel de reconocimiento (NME_CLASIFICACION_PR).

Ubicación geográfica: País, región, departamento y municipio de residencia.

Afiliación institucional: Nombre de la institución (INST_FILIA).

## Gráficas e interpretaciones

### Variables no útililes para la vizualización

En el proceso de análisis y visualización de la base de datos de investigadores reconocidos por convocatoria, se identificaron algunas variables que no resultan relevantes para la construcción de gráficos ni para la interpretación de tendencias. Estas variables corresponden principalmente a identificadores internos (como códigos únicos de personas, convocatorias), que cumplen una función técnica en la gestión de datos, pero que no aportan información de valor para representar visualmente la población.


Asimismo, existen campos que resultan redundantes o poco informativos: por ejemplo, códigos geográficos (COD_DANE_NAC_PR, COD_DANE_RES_PR) que ya están representados de manera más comprensible mediante nombres de municipios, departamentos o regiones

En consecuencia, para lograr visualizaciones más claras, comprensibles y orientadas al análisis de características sociodemográficas, geográficas y académicas de los investigadores, se decidió excluir las siguientes variables:

#### Identificadores

ID_CONVOCATORIA

ID_PERSONA_PR

ID_AREA_CON_PR

ID_NIV_FORMACION_PR

ID_CLAS_PR

ID_VICTIMA_CONFLICTO

#### Variables redundantes / técnicas

NME_CONVOCATORIA

ANO_CONVO

NRO_ORDEN_FORM_PR

ORDEN_CLAS_PR

COD_DANE_NAC_PR

COD_DANE_RES_PR

### Análisis útililes para la vizualización

Se hara un corto análisis de faltantes

<img width="1438" height="841" alt="Captura de pantalla 2025-09-01 a la(s) 3 57 41 p m" src="https://github.com/user-attachments/assets/581d1afa-6cd6-4fe7-a84c-f86f83c86a2b" />



Se observa que hay tres variables con faltantes, las cuales dos son los coidgos del Dane, con el 2.24% y 6.08%, ahora esto se debe a que el investigador esta en el exterior o no esta disponible la información, no es un problema de faltantes para la base. La tercera variable con el 12.57% es la variable INST_FIlA, si el investigador no tiene filación con ninguna isntitución no se tomara el dato y quedara como dato faltante por lo que no es un problema para la base.


#### NME_ESP_AREA_PR: Especialidad del área de conocimiento OCDE principal del investigador

Gráfica de frecuencia de la especialidad del área de conocimiento OCDE principal del investigador, filtrado solo por n mayor a 250.


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 12 19 17 a m" src="https://github.com/user-attachments/assets/e434d7e4-c934-40c6-b79d-400db19b266b" />


En la gráfica se observa que la especialidad del área de conocimiento OCDE principal con mayor número de investigadores es Educación General (incluye Capacitación y Pedagogía), con 860 investigadores. Le siguen Negocios y Management con 606 investigadores, Ingeniería Eléctrica y Electrónica con 527, y Derecho con 506. Estas cuatro especialidades son las únicas que superan los 500 investigadores, concentrando cerca del 20% del total.

Finalmente, especialidades como Economía, Psicología (incluye terapias de aprendizaje, habla, visual y otras discapacidades físicas y mentales), Salud Pública y Ciencias de la Computación completan el grupo de las áreas más frecuentes entre los investigadores.

Estas ocho especialidades conforman el 29.42% de los investigadores.


Gráfica de frecuencia de la especialidad del área de conocimiento OCDE principal del investigador, filtrado solo por n menor a 2.


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 12 30 18 a m" src="https://github.com/user-attachments/assets/9e744887-687e-45cc-9d60-6cca031aa62e" />

Se observa que hay especialidades que solo tienen un investigador como textiles, senores remotos, minerología, entre otros.

#### NME_AREA_PR: Área de conocimiento OCDE principal del investigador

Gráfica de área de conocimiento OCDE principal del investigador, filtrado solo por n mayor a 500.


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 12 43 01 a m" src="https://github.com/user-attachments/assets/c147fcae-d5d7-48b8-aaa6-19742106ba8d" />


Ciencias Biológicas es el área con más investigadores siendo 1289, seguido por Economía y Negocios con 1016,  Ciencias de la Salud con 936, estas tres son por poco un cuarto de la base. Si se agrega las otras áreas representadas en la grafica, es el 51.97% de los investigadores, por lo que se concluye que más de la mitad de los investigadores reconocidos por Colombia estan en las  8 áreas del conocimiento más frecuentadas.

 
Gráfica de área de conocimiento OCDE principal del investigador, filtrado solo por n menor a 40.


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 12 56 06 a m" src="https://github.com/user-attachments/assets/0b10c2e2-4d0c-4ced-b145-be25a7a68e55" />


El área de conocimiento con menor número de investigadores es “Otras Historias”, con 6 investigadores, seguida por Biología Ambiental y “Otras Ciencias Naturales”, cada una con 18 investigadores.


#### NME_GRAN_AREA_PR: Gran área de conocimiento OCDE principal del investigador

<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 03 38 a m" src="https://github.com/user-attachments/assets/0a285847-068b-4719-a7f9-a0e206e0700a" />


Ciencias sociales es la gran área de conocimiento de los investigadores con 3813, esto es un 29% de los investigadores, ciencias naturales con 3029, estas dos abarcan más del 50% de los investigadores, la Gran área de conocimiento con menos investigadores es ciencias agrícolas con 624.


#### NME_GENERO_PR: Género del investigador


<img width="475" height="375" alt="Captura de pantalla 2025-09-02 a la(s) 1 25 57 a m" src="https://github.com/user-attachments/assets/88026745-8900-4c03-a9e7-9d22124ca9df" />

Se observan más personas del genero masculino que femenino, 62.6% y 37.4% respectivamente, por lo que se concluye que los invvestigadores reconocidos de Colombia en el 2017 es su mayoria son del genero masculino.


#### NME_PAIS_NAC_PR: País de nacimiento del investigador


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 32 36 a m" src="https://github.com/user-attachments/assets/f1d39ede-3d18-447f-8ae3-4a23b476cdd8" />


El 93.9% de los investigadores reconocidos por Colombia en el año 2017 son Colombianos y el 5.8% es del extranjero.


#### NME_REGION_NAC_PR: Región de nacimiento del investigador


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 38 44 a m" src="https://github.com/user-attachments/assets/df9f22a8-b714-457a-a689-a3b96357a21e" />


Distrito Capital es la región donde nacieron más investigadores con 3349, seguida por el Eje cafetero con 2813, estas dos son las que más investigadores tienen, ahora centro oriente, pacífico y caribe son similares en nacimientos de investigadores.
Centro sut y llano son los que menos investigadores tienen.


#### NME_DEPARTAMENTO_NAC_PR: Departamento de nacimiento del investigador

Gráfica del departamento de nacimiento del investigador, filtrado solo por n mayor a 1000.


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 55 42 a m" src="https://github.com/user-attachments/assets/b9c1dfec-f4b9-497c-b574-79871eb7c380" />

Los departamentos con más investigadores son Bogotá D.C, Antioquia y Valle de Cauca, en estos departamentos se encuentra el 50% de los naciminetos de los investigadores.


Gráfica del departamento de nacimiento del investigador, filtrado solo por n menor a 20.


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 2 17 01 a m" src="https://github.com/user-attachments/assets/b4e5d717-3d94-4cea-b8c2-6c6d73ac3049" />


Los cuatros departamentos con menos nacimientos de investigadores son Amazonas, San Andres y islas, Vaupés y Vichada todos con dos investigadores nacidas en cada departamento


#### NME_MUNICIPIO_NAC_PR: Municipio de nacimiento del investigador


Gráfica del municipio de nacimiento del investigador, filtrado solo por n mayor a 200.


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 2 27 24 a m" src="https://github.com/user-attachments/assets/2690039e-7a19-4ed0-90b2-1e4edbf6532e" />



Bogotá D.C es el municipio con más nacimientos de investigadores con 3346, doblando al segundo el cual es Medellin con 1520.


#### NME_NIV_FORM_PR:Nombre del nivel de formación máximo alcanzado


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 31 32 p m" src="https://github.com/user-attachments/assets/45b0dae2-b96e-4ea8-8523-40c92acfc74a" />


Se observa que lel 49.68% de los investigadores son doctores, siendo 6459 investigadores con doctorado. Hay 4939 ivestigadores que su maximo nivel alcanzado es maestria, en estos dos niveles se encuentra el 87.67% de los investigadores


#### ##NME_CLASIFICACION_PR:Nombre de la categoría alcanzada por el investigador


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 33 39 p m" src="https://github.com/user-attachments/assets/14001a41-02ef-4aad-b0ae-5757f60f9eb8" />


Se observa que la mayoria de investigadores tienen la categoría Junior con un 58,3%, seguido por el asociado con el 27.7%, el investigador senior tienen un 13,1% y por ultimo el emérito con 1%


#### EDAD_ANOS_PR	Edad en años desde la fecha de nacimiento hasta el último mes de la convocatoria (2017-07)

En esta variable se encuentran dos datos que carecen de sentido, los cuales son que un hombre tenga 226 años y otro 952 años, por lo cual para el analisis de esta variable se remueven.


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 47 00 p m" src="https://github.com/user-attachments/assets/ae88a548-2510-4a25-b022-e1a2bb9184f6" />



<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 49 39 p m" src="https://github.com/user-attachments/assets/b36369b3-a6e8-455f-a8bc-15c2eb016697" />

Se observa que hay datos atipicos por encima del rango intercuartilico, el valor maximo es 89.7 y el valor minimo es 16.92, la media de las edades es 44.54.


#### NME_PAIS_RES_PR: País de ubicación del investigador


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 54 51 p m" src="https://github.com/user-attachments/assets/d01fe0f0-69e2-4cc8-b5f8-900572696455" />

El 97.8% de los investigadores investigan en Colombia y el 2% en el exterior.


#### NME_REGION_RES_PR:	Región de ubicación del investigador


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 1 57 50 p m" src="https://github.com/user-attachments/assets/0b142969-16a3-458b-81e6-825e4ed48558" />

Distrito capital es donde más investigan con 4362 investigadores, seguido por el Eje cafetero con 3149, esta grafica se comporta similar a la de nacimientos por región.


####  NME_DEPARTAMENTO_RES_PR: Departamento de ubicación del investigador

Gráfica del departamento de ubicación del investigador, filtrado solo por n mayor a 1000.


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 2 08 03 p m" src="https://github.com/user-attachments/assets/20300461-5901-407a-b0da-3735b755ac9d" />

Los investigadores residen más en Bogota D.C, Antioquia y Valle del Cauca.


Gráfica del departamento de ubicación del investigador, filtrado solo por n menor a 10.

<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 2 12 08 p m" src="https://github.com/user-attachments/assets/a3b8c358-3941-4365-a7a3-bdb9903e41fe" />

Aurauca y Vaupes es donde menos residen investigadores, cada uno con un solo investigador


#### NME_MUNICIPIO_RES_PR:	Municipio de ubicación del investigador

Gráfica del municipio de ubicación del investigador, filtrado solo por n mayor a 1000.

<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 2 18 14 p m" src="https://github.com/user-attachments/assets/01e8f7dd-275d-4d9f-8188-4ee534fe1cf7" />


Bogotá con 4357, Medellin con 2216 y Cali con 1008 son los municipios donde más residen investigadores, en terminos porcetuales es el 58.31%


#### INST_FILIA:	Lista de instituciones que el investigador indica tener filiación separados por PIPE (inst_filia)

Gráfica de instituciones que el investigador indica tener filiación separados por PIPE, filtrado solo por n mayor a 300. Se omiten los NA 


<img width="1440" height="900" alt="Captura de pantalla 2025-09-02 a la(s) 2 24 17 p m" src="https://github.com/user-attachments/assets/642d8255-b024-467b-b09b-abe649425577" />

La universidad Nacional sede Bogota y la universidad de Antioquia tienen más de 600 investigadores con una filiación, la Javeriana con más de 400, por ultimo los Andes y Valle con más de 300

