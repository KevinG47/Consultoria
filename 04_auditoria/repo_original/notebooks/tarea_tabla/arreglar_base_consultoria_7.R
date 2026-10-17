library(readxl)
library(dplyr)

Investigadores_Consolidado <- read_excel("Downloads/Investigadores_Consolidado.xlsx")

colnames(Investigadores_Consolidado)

summary(Investigadores_Consolidado)

summary(Investigadores_Consolidado$ID_PERSONA_PR)


Investigadores_Consolidado$ID_PERSONA_PR

length(unique(Investigadores_Consolidado$ID_PERSONA_PR)) == length(Investigadores_Consolidado$ID_PERSONA_PR)

sum(duplicated(Investigadores_Consolidado$ID_PERSONA_PR))

Investigadores_Consolidado$ID_PERSONA_PR[duplicated(Investigadores_Consolidado$ID_PERSONA_PR)]

sum(table(Investigadores_Consolidado$ID_PERSONA_PR) > 1)

View(Investigadores_Consolidado%>%
     filter(ID_PERSONA_PR=="65829" ))

table(Investigadores_Consolidado$ID_CONVOCATORIA)


###Prueba de mejorar DataSets

nuevo_dataset <- Investigadores_Consolidado %>%
  group_by(ID_PERSONA_PR) %>%
  mutate(prioridad = case_when(
    ID_CONVOCATORIA == 21 ~ 3,
    ID_CONVOCATORIA == 20 ~ 2,
    ID_CONVOCATORIA == 19 ~ 1,
    TRUE ~ 0
  )) %>%
  arrange(desc(prioridad)) %>%
  slice(1) %>%
  ungroup() %>%
  select(-prioridad)   # quitar la variable auxiliar


table(nuevo_dataset$ID_CONVOCATORIA)

length(unique(nuevo_dataset$ID_PERSONA_PR)) == length(nuevo_dataset$ID_PERSONA_PR)

sum(duplicated(nuevo_dataset$ID_PERSONA_PR))

nuevo_dataset$ID_PERSONA_PR[duplicated(nuevo_dataset$ID_PERSONA_PR)]

View(nuevo_dataset%>%
       filter(ID_PERSONA_PR=="65829" ))


nrow(nuevo_dataset)/nrow(Investigadores_Consolidado)

nrow(Investigadores_Consolidado)-sum(duplicated(Investigadores_Consolidado$ID_PERSONA_PR))


write.xlsx(nuevo_dataset, "Base_sin_duplicados")


#### verificación de que cada ID es unico 

View(Investigadores_Consolidado%>%
  filter(ID_PERSONA_PR=="20"))


# Filtrar solo los IDs repetidos
duplicados <- Investigadores_Consolidado %>%
  group_by(ID_PERSONA_PR) %>%
  filter(n() > 1) %>%   # IDs con más de una fila
  arrange(ID_PERSONA_PR, ID_CONVOCATORIA) %>%
  select(ID_PERSONA_PR, ID_CONVOCATORIA, NME_GENERO_PR, EDAD_ANOS_PR)


duplicados_dif <- Investigadores_Consolidado %>%
  group_by(ID_PERSONA_PR) %>%
  filter(n() > 1) %>%
  arrange(ID_PERSONA_PR, ID_CONVOCATORIA) %>%
  select(ID_PERSONA_PR, ID_CONVOCATORIA, NME_GENERO_PR, EDAD_ANOS_PR)

duplicados_dif<-duplicados_dif%>%
  mutate(dif_edad = EDAD_ANOS_PR - lag(EDAD_ANOS_PR))

dim(duplicados_dif)

find("lag")

duplicados_dif <- Investigadores_Consolidado %>%
  group_by(ID_PERSONA_PR) %>%
  filter(n() > 1) %>%
  arrange(ID_PERSONA_PR, ID_CONVOCATORIA) %>%
  mutate(dif_edad = EDAD_ANOS_PR - dplyr::lag(EDAD_ANOS_PR)) %>%
  select(ID_PERSONA_PR, ID_CONVOCATORIA, NME_GENERO_PR, EDAD_ANOS_PR, dif_edad)


duplicados_dif%>%
  filter(dif_edad>4.1)

View(Investigadores_Consolidado%>%
       filter(ID_PERSONA_PR=="1626437"))## 12, 21

View(Investigadores_Consolidado%>%
       filter(ID_PERSONA_PR=="154598"))###4.98, 21

View(Investigadores_Consolidado%>%
       filter(ID_PERSONA_PR=="1125974"))###5.03, 20

View(Investigadores_Consolidado%>%
       filter(ID_PERSONA_PR=="671819"))##40.3, 20

View(Investigadores_Consolidado%>%
       filter(ID_PERSONA_PR=="671827"))##28.4, 20

View(Investigadores_Consolidado%>%
       filter(ID_PERSONA_PR=="1430632"))##24.5, 20

View(Investigadores_Consolidado%>%
       filter(ID_PERSONA_PR=="1434533"))##15.1, 20

View(Investigadores_Consolidado%>%
       filter(ID_PERSONA_PR=="1499639"))##9.28, 20
