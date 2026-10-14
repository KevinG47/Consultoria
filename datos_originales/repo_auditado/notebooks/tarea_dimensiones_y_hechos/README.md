# Dimensiones 

---

### ID investigadores

Se seleciona la columna de ID_PERSONA_PR en la base de investigadores consolidados hecha anteriormente por grupo.
Ya se tiene ID por investigador en la base, por lo cual no se crea uno.

Esta base contiene la variable:

 - `ID_PERSONA_PR ` (ID del investigador).

   Filas: 26662 , Columnas: 1

---

### ID de la convocatoria 

Se selciona la columna de ID_CONVOCATORIA en la base de investigadores consolidados hecha anteriormente por grupo.
Ya se tiene ID por convocatoria en la base, por lo cual no se crea uno.

Esta base contiene la variables:

 - `ID_CONVOCATORIA` (ID de la convocatoria)  

 - `NME_CONVOCATORIA` (Nombre de la convocatoria)

 - `ANO_CONVO`  (Año de realización de la convocatoria)


  Filas: 3 , Columnas: 3

---

### Codigo del Dane por municipio de Nacimineto

Se selciona la columna de COD_DANE_NAC_PR en la base de investigadores consolidados hecha anteriormente por grupo.
Ya se tiene el codigo del Dane por municipio en la base, por lo cual no se crea uno.

Esta base contiene la variables:

 - `NME_PAIS_NAC_PR` (País de nacimiento del investigador)  

 - `NME_REGION_NAC_PR` (Región de nacimiento del investigador)

 - `NME_DEPARTAMENTO_NAC_PR`  (Departamento de nacimiento del investigador)

 - `NME_MUNICIPIO_NAC_PR` (Municipio de nacimiento del investigador)  

 - `COD_DANE_NAC_PR` (Código de homologación DANE para el municipio de nacimiento)


  Filas: 875 , Columnas: 5


---

### Dimensión **Universidad**
- Se crea a partir de la columna `INST_FILIA`.  
- Se creó un identificador único para cada universidad, se eliminaron de nulos y duplicados.

**Resultado:** 2.983 universidades 

---

### Dimensión **Nivel de Formación**
- Columnas utilizadas:
  - `ID_NIV_FORMACION_PR` (id del nivel).  
  - `NME_NIV_FORM_PR` (nombre del nivel).  
  - `NRO_ORDEN_FORM_PR` (jerarquía).  
- Se eliminaron duplicados y valores faltantes.  

**Resultado:** 11 niveles de formación  

---

### Dimensión **Residencia**
- Columnas utilizadas:
  - `COD_DANE_RES_PR` (código DANE).  
  - `NME_PAIS_RES_PR` (país).  
  - `NME_REGION_RES_PR` (región).  
  - `NME_DEPARTAMENTO_RES_PR` (departamento).  
  - `NME_MUNICIPIO_RES_PR` (municipio).  

**Resultado:** 224 combinaciones únicas 

Se exportan las tablas a un archivo **Excel** `dimensiones_investigadores.xlsx`.
