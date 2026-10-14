library(readxl)
library(ggplot2)
library(dplyr)
library(forcats)


Investigadores_Reconocidos_17 <- read_excel("Downloads/Investigadores_Reconocidos_por_convocatoria_20250831.xlsx")

str(Investigadores_Reconocidos_17)

## analisis datos variables con datos faltantes

Investigadores_Reconocidos_17%>%
  plot_missing(
    group = list(`0-5` = 0.05, `5-15` = 0.15,
                 `15-30` = 0.3, `> 30` = 1),
    group_color = list(`0-5` = "#1B9E77", `5-15` = "#E6AB02",
                       `15-30` = "#D95F02", `> 30` = "#E41A1C"))


sum(is.na(Investigadores_Consolidado$COD_DANE_NAC_PR))
sum(Investigadores_Reconocidos_17$NME_PAIS_NAC_PR == "Exterior" | Investigadores_Reconocidos_17$NME_PAIS_NAC_PR == "No disponible")

###Las primeras cuatro variables son de identificación, por lo que no se hace graficas de ellas

table(Investigadores_Reconocidos_17$ID_CONVOCATORIA)
table(Investigadores_Reconocidos_17$NME_CONVOCATORIA)
table(Investigadores_Reconocidos_17$ANO_CONVO)
length(unique(Investigadores_Reconocidos_17$ID_PERSONA_PR)) == length(Investigadores_Reconocidos_17$ID_PERSONA_PR)

#ID_AREA_CON_PR, esta variable es el Id de la variable NME_ESP_AREA_PR,
##por lo que se analizara la otra

##NME_ESP_AREA_PR, de aqui empieza las variables que se pueden explicar

ggplot(Investigadores_Reconocidos_17, aes(x = as.factor(NME_ESP_AREA_PR))) +
  geom_bar(fill = "black") +
  labs(title = "Frecuencia por Área",
       x = "NME_ESP_AREA_PR",
       y = "Frecuencia") +
  theme_minimal()


NME_ESP_AREA_PR<-Investigadores_Reconocidos_17 %>%
  count(NME_ESP_AREA_PR)

###se dividira por partes, este primer paso sera con las frecuencias más altas >250
NME_ESP_AREA_PR1<-NME_ESP_AREA_PR%>%
  filter(n>250)


ggplot(NME_ESP_AREA_PR1, aes(x = reorder(NME_ESP_AREA_PR, n), y = n)) +
  geom_col(fill = "steelblue") +
  geom_text(aes(label = n), vjust = -0.5, size = 4) + 
  coord_flip() +
  labs(title = "Frecuencia por Área",
       x = "NME_ESP_AREA_PR",
       y = "Frecuencia") +
  theme_minimal()

sum(NME_ESP_AREA_PR1$n)/nrow(Investigadores_Reconocidos_17)

table(NME_ESP_AREA_PR1$NME_ESP_AREA_PR)
## 8 con más de 250 theme(axis.text.x = element_text(angle = 90, vjust = 0.5))

## frecuencias más bajas, menor a 2

NME_ESP_AREA_PR2<-NME_ESP_AREA_PR%>%
  filter(n<2)


ggplot(NME_ESP_AREA_PR2, aes(x = as.factor(NME_ESP_AREA_PR), y = n)) +
  geom_col(fill = "red") +
  labs(title = "Frecuencia por Área",
       x = "NME_ESP_AREA_PR",
       y = "Frecuencia") +
  theme_minimal()

table(NME_ESP_AREA_PR2$NME_ESP_AREA_PR)
##17 con menos de 3

#NME_AREA_PR, este grafico es para daros cuenta por cual numero filtraremos

ggplot(Investigadores_Reconocidos_17, aes(x = as.factor(NME_AREA_PR))) +
  geom_bar(fill = "steelblue") +
  labs(title = "Frecuencia por Área",
       x = "NME_AREA_PR",
       y = "Frecuencia") +
  theme_minimal()


NME_AREA_PR<-Investigadores_Reconocidos_17 %>%
  count(NME_AREA_PR)

###se dividira por partes, este primer paso sera con las frecuencias más altas >250
NME_AREA_PR1<-NME_AREA_PR%>%
  filter(n>500)


ggplot(NME_AREA_PR1, aes(x = reorder(NME_AREA_PR, n), y = n)) +
  geom_col(fill = "steelblue") +
  geom_text(aes(label = n), hjust = -0.01, size = 5) +
  coord_flip()+
  labs(title = "Frecuencia por Área",
       x = "NME_AREA_PR",
       y = "Frecuencia") +
  theme_minimal()

sum(NME_AREA_PR1$n)/sum(NME_AREA_PR$n)

table(NME_AREA_PR1$NME_AREA_PR)
## 8 con más de 500

## frecuencias más bajas, menor a 140

NME_AREA_PR2<-NME_AREA_PR%>%
  filter(n<40)


ggplot(NME_AREA_PR2, aes(x = reorder(NME_AREA_PR, n), y = n)) +
  geom_col(fill = "red") +
  geom_text(aes(label = n), vjust = -1.1, size = 5)+
  labs(title = "Frecuencia por Área",
       x = "NME_AREA_PR",
       y = "Frecuencia") +
  theme_minimal()

## 5 con menos de 40

### NME_GRAN_AREA_PR	Gran área de conocimiento OCDE principal del investigador




ggplot(Investigadores_Reconocidos_17, 
       aes(x = fct_infreq(as.factor(NME_GRAN_AREA_PR)))) +
  geom_bar(fill = "steelblue") +
  geom_text(stat = "count", aes(label = ..count..), 
            vjust = -0.5, size = 4) +
  labs(title = "Gran área de conocimiento OCDE principal del investigador",
       x = "Área",
       y = "Frecuencia") +
  theme_minimal()


table(Investigadores_Reconocidos_17$NME_GRAN_AREA_PR)

## NME_GENERO_PR	Género del investigador

table(Investigadores_Reconocidos_17$NME_GENERO_PR)

# Calcular frecuencias y porcentajes por género
genero <- Investigadores_Reconocidos_17 %>%
  count(NME_GENERO_PR) %>%
  mutate(pct = n / sum(n) * 100,
         label = paste0(round(pct, 1), "%"))

# Pie chart con porcentajes
ggplot(genero, aes(x = "", y = n, fill = NME_GENERO_PR)) +
  geom_col(width = 1, color = "white") +
  coord_polar("y") +
  geom_text(aes(label = label),
            position = position_stack(vjust = 0.5), size = 4) +
  labs(title = "Distribución por Género", fill="Genero") +
  theme_void()


## NME_PAIS_NAC_PR	País de nacimiento del investigador

table(Investigadores_Reconocidos_17$NME_PAIS_NAC_PR)

pais<- Investigadores_Reconocidos_17 %>%
  count(NME_PAIS_NAC_PR) %>%
  mutate(pct = n / sum(n) * 100,
         label = paste0(round(pct, 1), "%"))

# Pie chart con porcentajes
ggplot(pais, aes(x = "", y = n, fill = NME_PAIS_NAC_PR)) +
  geom_col(width = 1, color = "black") +
  coord_polar("y") +
  geom_text(aes(label = label),
            position = position_stack(vjust = 0.5), size = 3) +
  labs(title = "País de nacimiento del investigador", fill="País de nacimiento") +
  theme_void()


## NME_REGION_NAC_PR	Región de nacimiento del investigador

table(Investigadores_Reconocidos_17$NME_REGION_NAC_PR)

Region<- Investigadores_Reconocidos_17 %>%
  count(NME_REGION_NAC_PR) %>%
  mutate(pct = n / sum(n) * 100,
         label = paste0(round(pct, 1), "%"))

# Pie chart con porcentajes
ggplot(Region, aes(x = "", y = n, fill = NME_REGION_NAC_PR)) +
  geom_col(width = 1, color = "white") +
  coord_polar("y") +
  geom_text(aes(label = label),
            position = position_stack(vjust = 0.5), size = 4) +
  labs(title = "Distribución") +
  theme_void()

##frecuencia

ggplot(Investigadores_Reconocidos_17, 
       aes(x = fct_infreq(as.factor(NME_REGION_NAC_PR)))) +
  geom_bar(fill = "plum") +
  geom_text(stat = "count", aes(label = ..count..), 
            vjust = -0.5, size = 4) +
  labs(title = "Región de nacimiento del investigador",
       x = "Área",
       y = "Frecuencia") +
  theme_minimal()




## NME_DEPARTAMENTO_NAC_PR	Departamento de nacimiento del investigador

table(Investigadores_Reconocidos_17$NME_DEPARTAMENTO_NAC_PR)

ggplot(Investigadores_Reconocidos_17, 
       aes(x = fct_infreq(as.factor(NME_DEPARTAMENTO_NAC_PR)))) +
  geom_bar(fill = "steelblue") +
  labs(title = "Frecuencia por Área",
       x = "Área",
       y = "Frecuencia") +
  theme_minimal()

###se dividira por partes, este primer paso sera con las frecuencias más altas >1000
NME_DEPARTAMENTO_NAC_PR<-Investigadores_Reconocidos_17 %>%
  count(NME_DEPARTAMENTO_NAC_PR)

NME_DEPARTAMENTO_NAC_PR1<-NME_DEPARTAMENTO_NAC_PR%>%
  filter(n>1000)


ggplot(NME_DEPARTAMENTO_NAC_PR1, aes(x = as.factor(NME_DEPARTAMENTO_NAC_PR), y = n)) +
  geom_col(fill = "plum") +
  labs(title = "Departamento de nacimiento del investigador",
       x = "NME_DEPARTAMENTO_NAC_PR",
       y = "Frecuencia") +
  theme_minimal()

sum(NME_DEPARTAMENTO_NAC_PR1$n)

table(NME_DEPARTAMENTO_NAC_PR1$NME_DEPARTAMENTO_NAC_PR)
## 3 con más de 1000

## frecuencias más bajas, menor a 20

NME_DEPARTAMENTO_NAC_PR2<-NME_DEPARTAMENTO_NAC_PR%>%
  filter(n<20)

ggplot(NME_DEPARTAMENTO_NAC_PR2, 
       aes(x = fct_reorder(as.factor(NME_DEPARTAMENTO_NAC_PR), desc(n)), y = n)) +
  geom_col(fill = "#00A86B") +
  geom_text(aes(label = n), vjust = -0.5, size = 3) +
  labs(title = "Frecuencias más bajas",
       x = "NME_DEPARTAMENTO_NAC_PR",
       y = "Frecuencia") +
  theme_minimal()

## 7 con menos de 20


## NME_MUNICIPIO_NAC_PR	Municipio de nacimiento del investigador

ggplot(Investigadores_Reconocidos_17, 
       aes(x = fct_infreq(as.factor(NME_MUNICIPIO_NAC_PR)))) +
  geom_bar(fill = "steelblue") +
  labs(title = "Frecuencia por Área",
       x = "Área",
       y = "Frecuencia") +
  theme_minimal()

###se dividira por partes, este primer paso sera con las frecuencias más altas >500
NME_MUNICIPIO_NAC_PR<-Investigadores_Reconocidos_17 %>%
  count(NME_MUNICIPIO_NAC_PR)

NME_MUNICIPIO_NAC_PR1<-NME_MUNICIPIO_NAC_PR%>%
  filter(n>200)

ggplot(NME_MUNICIPIO_NAC_PR1, 
       aes(x = fct_reorder(as.factor(NME_MUNICIPIO_NAC_PR), desc(n)), y = n)) +
  geom_col(fill = "plum") +
  geom_text(aes(label = n), vjust = -0.5, size = 3) +
  labs(title = "Frecuencia por Municipio de Nacimiento",
       x = "NME_MUNICIPIO_NAC_PR",
       y = "Frecuencia (n)") +
  theme_minimal()


## 9 con más de 200

## frecuencias más bajas, menor a 2

NME_MUNICIPIO_NAC_PR2<-NME_MUNICIPIO_NAC_PR%>%
  filter(n<2)


ggplot(NME_MUNICIPIO_NAC_PR2, aes(x = as.factor(NME_MUNICIPIO_NAC_PR), y = n)) +
  geom_col(fill = "#00A86B") +
  labs(title = "Frecuencia por Área",
       x = "NME_MUNICIPIO_NAC_PR",
       y = "Frecuencia") +
  theme_minimal()
### Grafica sin sentido, muchas categorias menores a n=2

# COD_DANE_NAC_PR	Código de homologación DANE para el municipio de nacimiento
### a esa variable no se le hara nada, es como ID, se tiene la misma informacion
# y más clara en ptras variables

##ID_NIV_FORMACION_PR	Nivel de formación máximo alcanzado, se hace tabla, pero se analizara
# la siguiente variable que es la misma información cambiado el ID por nombres

table(Investigadores_Reconocidos_17$ID_NIV_FORMACION_PR)

##NME_NIV_FORM_PR	Nombre del nivel de formación máximo alcanzado

table(Investigadores_Reconocidos_17$NME_NIV_FORM_PR)

nivel<- Investigadores_Reconocidos_17 %>%
  count(NME_NIV_FORM_PR) %>%
  mutate(pct = n / sum(n) * 100,
         label = paste0(round(pct, 1), "%"))

# Pie chart con porcentajes
ggplot(nivel, aes(x = "", y = n, fill = NME_NIV_FORM_PR)) +
  geom_col(width = 1, color = "white") +
  coord_polar("y") +
  geom_text(aes(label = label),
            position = position_stack(vjust = 0.5), size = 4) +
  labs(title = "Distribución por Género") +
  theme_void()


ggplot(Investigadores_Reconocidos_17, 
       aes(x = fct_infreq(as.factor(NME_NIV_FORM_PR)))) +
  geom_bar(fill = "orange") +
  geom_text(stat = "count", aes(label = ..count..), 
            vjust = -0.5, size = 3) +
  labs(title = "Nombre del nivel de formación máximo alcanzado",
       x = "Nivel de Formación",
       y = "Frecuencia") +
  theme_minimal()



# NRO_ORDEN_FORM_PR	Importancia del nivel de formación, siendo 0 la de menor valor

table(Investigadores_Reconocidos_17$NRO_ORDEN_FORM_PR)

## ID_CLAS_PR	Categoría alcanzada por el investigador

table(Investigadores_Reconocidos_17$ID_CLAS_PR)

##NME_CLASIFICACION_PR	Nombre de la categoría alcanzada por el investigador

table(Investigadores_Reconocidos_17$NME_CLASIFICACION_PR)


clasi<- Investigadores_Reconocidos_17 %>%
  count(NME_CLASIFICACION_PR) %>%
  mutate(pct = n / sum(n) * 100,
         label = paste0(round(pct, 1), "%"))

# Pie chart con porcentajes
ggplot(clasi, aes(x = "", y = n, fill = NME_CLASIFICACION_PR)) +
  geom_col(width = 1, color = "white") +
  coord_polar("y") +
  geom_text(aes(label = label),
            position = position_stack(vjust = 0.5), size = 4) +
  labs(title = "Distribución por categoría alcanzada por el investigador",fill="categoría") +
  theme_void()

## ORDEN_CLAS_PR	Orden de importancia de la categoría alcanzada por el investigador

table(Investigadores_Reconocidos_17$ORDEN_CLAS_PR)


### EDAD_ANOS_PR	Edad en años desde la fecha de nacimiento hasta el 
## último mes de la convocatoria (2017-07)

ggplot(Investigadores_Reconocidos_17, aes(x = EDAD_ANOS_PR)) +
  geom_histogram(aes(y = ..density..), 
                 binwidth = 5, fill = "steelblue", color = "white", alpha = 0.7) +
  geom_density(color = "red", size = 1) +
  geom_vline(aes(xintercept = mean(EDAD_ANOS_PR, na.rm = TRUE)), 
             color = "black", linetype = "dashed", size = 1) +
  labs(title = "Distribución de la Edad con Media",
       x = "Edad (años)",
       y = "Densidad") +
  xlim(0,100) +
  theme_minimal()

summary(Investigadores_Reconocidos_17$EDAD_ANOS_PR)

boxplot(Investigadores_Reconocidos_17$EDAD_ANOS_PR)

edad_sin_error<-Investigadores_Reconocidos_17%>%
       filter(EDAD_ANOS_PR <100)

summary(edad_sin_error$EDAD_ANOS_PR)

boxplot(edad_sin_error$EDAD_ANOS_PR)

ggplot(edad_sin_error, aes(x = EDAD_ANOS_PR)) +
  geom_histogram(aes(y = ..density..), 
                 binwidth = 5, fill = "steelblue", color = "white", alpha = 0.7) +
  geom_density(color = "red", size = 1) +
  geom_vline(aes(xintercept = mean(EDAD_ANOS_PR, na.rm = TRUE)), 
             color = "black", linetype = "dashed", size = 1) +
  labs(title = "Distribución de la Edad con Media",
       x = "Edad (años)",
       y = "Densidad") +
  xlim(0,100) +
  theme_minimal()



##dato imposible, 952 en edad

## NME_PAIS_RES_PR	País de ubicación del investigador

table(Investigadores_Reconocidos_17$NME_PAIS_RES_PR)

pai<- Investigadores_Reconocidos_17 %>%
  count(NME_PAIS_RES_PR) %>%
  mutate(pct = n / sum(n) * 100,
         label = paste0(round(pct, 1), "%"))

# Pie chart con porcentajes
ggplot(pai, aes(x = "", y = n, fill = NME_PAIS_RES_PR)) +
  geom_col(width = 1, color = "white") +
  coord_polar("y") +
  geom_text(aes(label = label),
            position = position_stack(vjust = 0.5), size = 4) +
  labs(title = "País de ubicación del investigador", fill="País de ubicación") +
  theme_void()


## NME_REGION_RES_PR	Región de ubicación del investigador

table(Investigadores_Reconocidos_17$NME_REGION_RES_PR)


ggplot(Investigadores_Reconocidos_17, 
       aes(x = fct_infreq(as.factor(NME_REGION_RES_PR)))) +
  geom_bar(fill = "black") +
  geom_text(stat = "count", aes(label = ..count..), 
            vjust = -0.5, color = "black", size = 3) +
  labs(title = "Región de ubicación del investigador",
       x = "Región",
       y = "Frecuencia") +
  theme_minimal()


##  NME_DEPARTAMENTO_RES_PR	Departamento de ubicación del investigador

ggplot(Investigadores_Reconocidos_17, 
       aes(x = fct_infreq(as.factor(NME_DEPARTAMENTO_RES_PR)))) +
  geom_bar(fill = "steelblue") +
  labs(title = "Frecuencia por Área",
       x = "Área",
       y = "Frecuencia") +
  theme_minimal()


NME_DEPARTAMENTO_RES_PR<-Investigadores_Reconocidos_17 %>%
  count(NME_DEPARTAMENTO_RES_PR)
###mayor a 1000
NME_DEPARTAMENTO_RES_PR1<-NME_DEPARTAMENTO_RES_PR%>%
  filter(n>1000)


ggplot(NME_DEPARTAMENTO_RES_PR1, aes(x = as.factor(NME_DEPARTAMENTO_RES_PR), y = n)) +
  geom_col(fill = "black") +
  labs(title = "Frecuencia más altas",
       x = "NME_MUNICIPIO_NAC_PR",
       y = "Frecuencia") +
  theme_minimal()

## 3 con más de 1000

## frecuencias más bajas, menor a 10

NME_DEPARTAMENTO_RES_PR2<-NME_DEPARTAMENTO_RES_PR%>%
  filter(n<10)


ggplot(NME_DEPARTAMENTO_RES_PR2, 
       aes(x = fct_reorder(as.factor(NME_DEPARTAMENTO_RES_PR), desc(n)), y = n)) +
  geom_col(fill = "gold") +
  geom_text(aes(label = n), vjust = -0.5, size = 3) +
  labs(title = "Frecuencia por Departamento de Residencia",
       x = "Departamento",
       y = "Frecuencia") +
  theme_minimal()
## 5 con menos de 10


## NME_MUNICIPIO_RES_PR	Municipio de ubicación del investigador

ggplot(Investigadores_Reconocidos_17, 
       aes(x = fct_infreq(as.factor(NME_MUNICIPIO_RES_PR)))) +
  geom_bar(fill = "steelblue") +
  labs(title = "Frecuencia por Área",
       x = "Área",
       y = "Frecuencia") +
  theme_minimal()


NME_MUNICIPIO_RES_PR<-Investigadores_Reconocidos_17 %>%
  count(NME_MUNICIPIO_RES_PR)
###mayor a 1000
NME_MUNICIPIO_RES_PR1<-NME_MUNICIPIO_RES_PR%>%
  filter(n>1000)



ggplot(NME_MUNICIPIO_RES_PR1, 
       aes(x = fct_reorder(as.factor(NME_MUNICIPIO_RES_PR), desc(n)), y = n)) +
  geom_col(fill = "black") +
  geom_text(aes(label = n), vjust = -0.5, size = 3, color = "black") +
  labs(title = "Frecuencia por Municipio de Residencia",
       x = "Municipio",
       y = "Frecuencia") +
  theme_minimal()

sum(NME_MUNICIPIO_RES_PR1$n)/13001

## 3 con más de 1000

## frecuencias más bajas, menor a 50

NME_MUNICIPIO_RES_PR2<-NME_MUNICIPIO_RES_PR%>%
  filter(n<2)


ggplot(NME_MUNICIPIO_RES_PR2, aes(x = as.factor(NME_MUNICIPIO_RES_PR), y = n)) +
  geom_col(fill = "red") +
  labs(title = "Frecuencia por Área",
       x = "NME_MUNICIPIO_NAC_PR",
       y = "Frecuencia") +
  theme_minimal()
## grafico no sirve para nada

#COD_DANE_RES_PR	Código DANE para el municipio de ubicación del investigador
# no se analiza codigo ni ID


###ID_VICTIMA_CONFLICTO	Población víctima del conflicto armado

table(Investigadores_Reconocidos_17$ID_VICTIMA_CONFLICTO)

###TXT_GRUPO_ETNICO	Grupo étnico del investigador

table(Investigadores_Reconocidos_17$TXT_GRUPO_ETNICO)


##3 TXT_POBLACION_DISCA	Población en situación de discapacidad

table(Investigadores_Reconocidos_17$TXT_POBLACION_DISCA)


### INST_FILIA	Lista de instituciones que el investigador indica 
### tener filiación separados por PIPE (inst_filia)

ggplot(Investigadores_Reconocidos_17, 
       aes(x = fct_infreq(as.factor(INST_FILIA)))) +
  geom_bar(fill = "steelblue") +
  labs(title = "Frecuencia por Área",
       x = "Área",
       y = "Frecuencia") +
  theme_minimal()


INST_FILIA<-Investigadores_Reconocidos_17 %>%
  count(INST_FILIA)
###mayor a 300
INST_FILIA1<-INST_FILIA%>%
  filter(n>300)


ggplot(na.omit(INST_FILIA1), 
       aes(x = fct_reorder(as.factor(INST_FILIA), n), y = n)) +
  geom_col(fill = "steelblue") +
  geom_text(aes(label = n), hjust = -0.5, size = 3, color = "black") +
  labs(title = "Frecuencia por Institución",
       x = "INST_FILIA",
       y = "Frecuencia") +
  theme_minimal()+
  coord_flip()

## 6 con más de 300, una es NA por lo que se quita

## frecuencias más bajas, menor a 50

INST_FILIA2<-INST_FILIA%>%
  filter(n<2)


ggplot(INST_FILIA2, aes(x = as.factor(INST_FILIA), y = n)) +
  geom_col(fill = "red") +
  labs(title = "Frecuencia por Área",
       x = "NME_MUNICIPIO_NAC_PR",
       y = "Frecuencia") +
  theme_minimal()

###no sirve la grafica

