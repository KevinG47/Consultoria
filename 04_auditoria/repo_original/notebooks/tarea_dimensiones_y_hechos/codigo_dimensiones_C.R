library(readxl)
library(openxlsx)
library(dplyr)

Investigadores_Consolidado <- read_excel("Downloads/Investigadores_Consolidado.xlsx")

colnames(Investigadores_Consolidado)

# Dimensiones

##  ID del investigador

IDinvestiagores<-unique(Investigadores_Consolidado[,c(4)])
colnames(IDinvestiagores)

write.xlsx(IDinvestiagores, "Dimension_invetigadores.xlsx")

##  Cod_Dane del municipio de nacimiento del investigador


IDMUNICIPIO_NAC_PR <- Investigadores_Consolidado[,c(14,10:13)] %>%
  distinct(COD_DANE_NAC_PR, .keep_all = TRUE)


colnames(IDMUNICIPIO_NAC_PR)

write.xlsx(IDMUNICIPIO_NAC_PR, "Dimension_municipos_de_naciminetos.xlsx")


## ID de la convocatoria 


IDCONVOCATORIA<-Investigadores_Consolidado[,c(1:3)] %>%
  distinct(ID_CONVOCATORIA, .keep_all = TRUE)

colnames(IDCONVOCATORIA)

write.xlsx(IDCONVOCATORIA, "Dimension_convocatoria.xlsx")


