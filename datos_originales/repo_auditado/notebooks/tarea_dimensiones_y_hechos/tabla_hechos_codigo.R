library(readxl)
library(openxlsx)
library(dplyr)

Dimensiones_Universidad<- read_excel("Downloads/dimensiones_investigadores.xlsx",sheet = 1)
Dimensiones_genero<-read.csv("Downloads/Dim_genero (1).csv")



Investigadores_Consolidado_R<-Investigadores_Consolidado%>%
  left_join(Dimensiones_Universidad, by = "INST_FILIA")%>%
  left_join(Dimensiones_genero, by = "NME_GENERO_PR")


Tabla_hechos<-Investigadores_Consolidado_R[,c(1,4,5,14,15,18,21,26,27:29,31,32)]
colnames(Tabla_hechos)
dim(Tabla_hechos)


write.xlsx(Tabla_hechos, "Tabla_hechos.xlsx")
