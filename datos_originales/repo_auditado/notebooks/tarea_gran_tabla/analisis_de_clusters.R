library(readxl)
library(klaR)
library(dplyr)
library(factoextra)
library(clustMixType)


GT<- read_excel("Downloads/GRAN_TABLA(SIN ID).xlsx")%>%
  mutate(across(c(1:10,16:23), factor),
         NRO_ORDEN_FORM_PR=ordered(NRO_ORDEN_FORM_PR,levels = c("0","5","7","10","12","13","14","15","16","17","18")),
         ORDEN_CLAS_PR=ordered(ORDEN_CLAS_PR,levels = c("12","13","14","15")),
         NME_NIV_FORM_PR=ordered(NME_NIV_FORM_PR,levels = c("No disponible","Secundario","Técnico - nivel superior",
                                                            "Cursos de corta duración","Perfeccionamiento","Pregrado/Universitario",
                                                            "Especialización","Especialidad Médica","Maestría/Magister",
                                                            "Doctorado","Postdoctorado")),
         NME_CLASIFICACION_PR=ordered(NME_CLASIFICACION_PR,levels = c("Investigador Junior","Investigador Asociado",
                                                                      "Investigador Sénior","Investigador Emérito")))

## Se trabaja sin NA para hacer el k prototipos

GT_NA<-cc(GT)

nrow(GT_NA)/nrow(GT)
## se trabaja con el 91.60% de la base



set.seed(123)
res.kproto<- kproto(GT_NA, k = 3) 


## Asignar los clusters al dataset

GT_NA$cluster <- as.factor(res.kproto$cluster)

# Centros de los clusters (prototipos)
## res.kproto$centers

### Analisis de grupos

###filtrar por grupos para hacer comparaciones

c1<-GT_NA%>%
  filter(cluster=="1")
c2<-GT_NA%>%
  filter(cluster=="2")
c3<-GT_NA%>%
  filter(cluster=="3")

### Resultados

## gran area
table(c1$NME_GRAN_AREA_PR)/nrow(c1)
table(c2$NME_GRAN_AREA_PR)/nrow(c2)
table(c3$NME_GRAN_AREA_PR)/nrow(c3)


##genero
table(c1$NME_GENERO_PR)/nrow(c1)
table(c2$NME_GENERO_PR)/nrow(c2)
table(c3$NME_GENERO_PR)/nrow(c3)

##Nacimiento
table(c1$NME_REGION_NAC_PR)/nrow(c1)
table(c2$NME_REGION_NAC_PR)/nrow(c2)
table(c3$NME_REGION_NAC_PR)/nrow(c3)

## formacion
table(c1$NME_NIV_FORM_PR)/nrow(c1)
table(c2$NME_NIV_FORM_PR)/nrow(c2)
table(c3$NME_NIV_FORM_PR)/nrow(c3)


## Clasificacion
table(c1$NME_CLASIFICACION_PR)/nrow(c1)
table(c2$NME_CLASIFICACION_PR)/nrow(c2)
table(c3$NME_CLASIFICACION_PR)/nrow(c3)


## Residencia 
table(c1$NME_REGION_RES_PR)/nrow(c1)
table(c2$NME_REGION_RES_PR)/nrow(c2)
table(c3$NME_REGION_RES_PR)/nrow(c3)

###Edad
mean(c1$EDAD_ANOS_PR)
mean(c2$EDAD_ANOS_PR)
mean(c3$EDAD_ANOS_PR)

## Población discapacitada
table(c1$TXT_POBLACION_DISCA)/nrow(c1)
table(c2$TXT_POBLACION_DISCA)/nrow(c2)
table(c3$TXT_POBLACION_DISCA)/nrow(c3)

