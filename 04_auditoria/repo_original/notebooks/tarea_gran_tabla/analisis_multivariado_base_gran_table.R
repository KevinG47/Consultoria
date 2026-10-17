library(readxl)
library(FactoMineR)
library(dplyr)
library(DataExplorer)
library(ggplot2)
library(factoextra)
library(ggrepel)
library(mice)
library(grid)


GT<- read_excel("Downloads/GRAN_TABLA(SIN ID).xlsx")%>%
  mutate(NRO_ORDEN_FORM_PR=ordered(NRO_ORDEN_FORM_PR,levels = c("0","5","7","10","12","13","14","15","16","17","18")),
         ORDEN_CLAS_PR=ordered(ORDEN_CLAS_PR,levels = c("12","13","14","15")),
         NME_NIV_FORM_PR=ordered(NME_NIV_FORM_PR,levels = c("No disponible","Secundario","Técnico - nivel superior",
                                                            "Cursos de corta duración","Perfeccionamiento","Pregrado/Universitario",
                                                            "Especialización","Especialidad Médica","Maestría/Magister",
                                                            "Doctorado","Postdoctorado")),
         NME_CLASIFICACION_PR=ordered(NME_CLASIFICACION_PR,levels = c("Investigador Junior","Investigador Asociado",
                                                                      "Investigador Sénior","Investigador Emérito")));GT

str(GT)

#GT %>%
#  distinct(NME_NIV_FORM_PR, NRO_ORDEN_FORM_PR) %>%
#  arrange(NRO_ORDEN_FORM_PR)


GT%>%
  plot_missing(group = list(`0-5` = 0.05, `5-15` = 0.15,
                            `15-30` = 0.3, `> 30` = 1),
     group_color = list(`0-5` = "#1B9E77", `5-15` = "#E6AB02",
                        `15-30` = "#D95F02", `> 30` = "#E41A1C"))



nrow(GT)
colnames(GT)

### analisis factorial y analisis de componentes principales, se hace solo con variables numericas

### analisis de correspondencia, gran area y genero
#bc<-table(GT$NME_CONVOCATORIA,GT$ANO_CONVO)
bc<-table(GT$NME_GRAN_AREA_PR,GT$NME_GENERO_PR)

b<-CA(bc, graph = F)

b$row$contrib
b$row$cos2
b$col$cos2
b$col$contrib


# Convertir los eigenvalues en data.frame
eig_df <- as.data.frame(b$eig)
eig_df$Comp <- 1:nrow(eig_df)   # Crear columna con número de componente

# Gráfico con ggplot2
ggplot(eig_df, aes(x = factor(Comp), y = `percentage of variance`)) +
  geom_col(fill = "skyblue", color = "black") +
  geom_text(aes(label = round(`percentage of variance`, 1)), 
            vjust = -0.5, size = 3) +
  labs(x = "Dimensión", y = "Porcentaje de varianza explicada",
       title = "Varianza explicada por dimensiones ") +
  theme_minimal()

ggplot(NULL, aes(x=`Dim 1`
                 ,y=`Dim 2`)) +
  geom_vline(xintercept = 0, lty = 2) +
  geom_hline(yintercept = 0, lty = 2)+
  geom_point(data=b$row$coord, col = "red", alpha = 1,aes(shape = "Gran area de conocimiento")) +
  geom_point(data=b$col$coord, col = "blue", alpha = 1,aes(shape = "Genero")) +
  geom_text_repel(data =b$row$coord, , vjust = -.5, size = 4,
  label = rownames(b$row$coord,), col = "red") +
  geom_text_repel(data = b$col$coord, vjust = -.5, size = 4,
  label = rownames(b$col$coord), col = "blue") +
  labs(title="Grafica de dimension 1 y 2", legend.position = "bottom")+
  theme(legend.position = "right")+
  guides(shape = guide_legend(title = "Variable"))

### analisis de correspondencia,  IST_FILA y genero


bd<-table(GT$INST_FILIA,GT$NME_GENERO_PR)

ba<-CA(bd, graph = F)
coseno<-as.data.frame(ba$row$cos2); View(coseno)
contri<-as.data.frame(ba$row$contrib); View(contri)
ba$col$cos2
ba$col$contrib


# Convertir los eigenvalues en data.frame
eig_df <- as.data.frame(ba$eig)
eig_df$Comp <- 1:nrow(eig_df)   # Crear columna con número de componente

# Gráfico con ggplot2
ggplot(eig_df, aes(x = factor(Comp), y = `percentage of variance`)) +
  geom_col(fill = "skyblue", color = "black") +
  geom_text(aes(label = round(`percentage of variance`, 1)), 
            vjust = -0.5, size = 3) +
  labs(x = "Dimensión", y = "Porcentaje de varianza explicada",
       title = "Varianza explicada por dimensiones") +
  theme_minimal()


ggplot(NULL, aes(x=`Dim 1` ,y=`Dim 2`)) +
  geom_vline(xintercept = 0, lty = 2) + 
  geom_hline(yintercept = 0, lty = 2)+ 
  geom_point(data=ba$row$coord, col = "red", alpha = 1,aes(shape = "Universidad")) + 
  geom_point(data=ba$col$coord, col = "blue", alpha = 1,aes(shape = "Genero")) + 
  geom_text_repel(data =ba$row$coord, , vjust = -.5, size = 4, label = rownames(ba$row$coord,), col = "red") + 
  geom_text_repel(data = ba$col$coord, vjust = -.5, size = 4, label = rownames(ba$col$coord), col = "blue") + 
  labs(title="Grafica de dimension 1 y 2", legend.position = "bottom")+ theme(legend.position = "right")+ 
  guides(shape = guide_legend(title = "Variable"))


### analisis de correspondencia, NME_NIV_FORM_PR, y NME_CLASIFICACION_PR

bf<-table(GT$NME_NIV_FORM_PR,GT$NME_CLASIFICACION_PR)

bl<-CA(bf, graph = F)
bl$row$contrib
bl$row$cos2
bl$col$contrib
bl$col$cos2

# Convertir los eigenvalues en data.frame
eig_df <- as.data.frame(bl$eig)
eig_df$Comp <- 1:nrow(eig_df)   # Crear columna con número de componente

# Gráfico con ggplot2
ggplot(eig_df, aes(x = factor(Comp), y = `percentage of variance`)) +
  geom_col(fill = "skyblue", color = "black") +
  geom_text(aes(label = round(`percentage of variance`, 1)), 
            vjust = -0.5, size = 3) +
  labs(x = "Dimensión", y = "Porcentaje de varianza explicada",
       title = "Varianza explicada por dimensiones") +
  theme_minimal()


ggplot(NULL, aes(x=`Dim 1` ,y=`Dim 2`)) +
  geom_vline(xintercept = 0, lty = 2) + 
  geom_hline(yintercept = 0, lty = 2)+ 
  geom_point(data=bl$row$coord, col = "red", alpha = 1,aes(shape = "Gran area de conocimiento")) + 
  geom_point(data=bl$col$coord, col = "blue", alpha = 1,aes(shape = "Genero")) + 
  geom_text_repel(data =bl$row$coord, , vjust = -.5, size = 4, label = rownames(bl$row$coord,), col = "red") + 
  geom_text_repel(data = bl$col$coord, vjust = -.5, size = 4, label = rownames(bl$col$coord), col = "blue") + 
  labs(title="Grafica de dimension 1 y 2", legend.position = "bottom")+ theme(legend.position = "right")+ 
  guides(shape = guide_legend(title = "Variable"))




### analisis de correspondencia multiple(ANO_CONVO,NME_GRAN_AREA_PR,NME_GENERO_PR,
## NME_PAIS_NAC_PR, NME_PAIS_RES_PR) 
###se queda como borrador a no ser que se reuqiera este analisis
### se requiere un ajuste al elegir variebles, se queda con muchas dimensiones
colnames(GT)

a<-MCA(GT[,c(2,5,6,7,16)],graph = F)


eig_df <- as.data.frame(a$eig)
eig_df$Comp <- 1:nrow(eig_df)

eig_df %>%
  filter(`cumulative percentage of variance` > 70)



ggplot(eig_df, aes(x = factor(Comp), y = `percentage of variance`)) +
  geom_col(fill = "skyblue", color = "black") +
  geom_text(aes(label = round(`percentage of variance`, 1)),
            vjust = -0.5, size = 3) +
  labs(x = "Dimensión", y = "Porcentaje de varianza explicada",
       title = "Varianza explicada por dimensiones (MCA)") +
  theme_minimal()

ggplot(eig_df, aes(x = Comp, y = `cumulative percentage of variance`)) +
  geom_line(color = "blue") +
  geom_point(size = 2, color = "red") +
  geom_hline(yintercept = 70, linetype = "dashed", color = "gray") +
  labs(x = "Dimensión", y = "Porcentaje acumulado",
       title = "Varianza acumulada (MCA)") +
  theme_minimal()

# Gráfico de categorías (modalidades de las variables)

coord <- as.data.frame(a$var$coord)
coord$Categoria <- rownames(coord)



ggplot(coord, aes(x = `Dim 1`, y = `Dim 2`)) +
  geom_point(color = "red", size = 3) +
  geom_text_repel(aes(label = Categoria), size = 3.5, max.overlaps = 100) +
  geom_vline(xintercept = 0, linetype = 2, color = "gray70") +
  geom_hline(yintercept = 0, linetype = 2, color = "gray70") +
  theme_minimal() +
  ggtitle("Representación de categorías (MCA)") +
  theme(
    plot.title = element_text(hjust = 0.5, face = "bold"),
    legend.position = "none"
  )


### analisis de correspondencia multiple
##(ID_VICTIMA_CONFLICTO,TXT_GRUPO_ETNICO,TXT_POBLACION_DISCA)

aa<-MCA(GT[,c(20:22)],graph = F,ncp = 16)
aa$eig
cose<-as.data.frame(aa$var$cos2);View(cose)
con<-as.data.frame(aa$var$contrib);View(con)



eig_df <- as.data.frame(aa$eig)
eig_df$Comp <- 1:nrow(eig_df)

eig_df %>%
  filter(`cumulative percentage of variance` > 70)

nrow(eig_df)

ggplot(eig_df, aes(x = factor(Comp), y = `percentage of variance`)) +
  geom_col(fill = "skyblue", color = "black") +
  geom_text(aes(label = round(`percentage of variance`, 1)),
            vjust = -0.5, size = 3) +
  labs(x = "Dimensión", y = "Porcentaje de varianza explicada",
       title = "Varianza explicada por dimensiones") +
  theme_minimal()

coord <- as.data.frame(aa$var$coord)
coord$Categoria <- rownames(coord)



ggplot(coord, aes(x = `Dim 1`, y = `Dim 2`)) +
  geom_point(color = "red", size = 3) +
  geom_text_repel(aes(label = Categoria), size = 3.5, max.overlaps = 100) +
  geom_vline(xintercept = 0, linetype = 2, color = "gray70") +
  geom_hline(yintercept = 0, linetype = 2, color = "gray70") +
  theme_minimal() +
  ggtitle("Representación de categorías (MCA)") +
  theme(
    plot.title = element_text(hjust = 0.5, face = "bold"),
    legend.position = "none"
  )




### Factor Analysis for Mixed Data

#preparamos para el analisis mixto

# Solo variables numéricas
num_vars <- sapply(GT, is.numeric)
GT_num <- GT[, num_vars]

# Revisar NA e infinitos SOLO en numéricas
sum(!is.finite(as.matrix(GT_num)))


which(!is.finite(as.matrix(GT_num)), arr.ind = TRUE)
GT_num[50891, 1]

md.pattern(GT, rotate.names = TRUE, plot = TRUE)

### Se observa que una observacion esta vacia en la mayoria de variables por lo cual se retira de la base, que dadon con 50890 filas
### 50890/50891=99.99804% se trabaja con este porcentaje de la base 



colnames(GT)
#sum(!is.finite(as.matrix(GT[-50891,])))
#sum(is.finite(as.matrix(GT))) 

## ANO_CONVO,NME_GRAN_AREA_PR,NME_GENERO_PR,ME_PAIS_NAC_PR,EDAD_ANOS_PR

c<-FAMD(GT[-50891,c(2,5,6,7,15)],ncp=20, graph = T)


c$eig
c$quanti.var$cos2
c$quali.var$cos2
c$var$cos2
c$quanti.var$contrib
c$quali.var$contrib
c$var$cos2


##

# Extraer la información de varianza del FAMD
var_exp <- as.data.frame(c$eig)
colnames(var_exp) <- c("Eigenvalue", "Variance", "CumulativeVariance")


# Crear gráfico de barras
ggplot(var_exp, aes(x = factor(1:nrow(var_exp)), y = Variance)) +
  geom_bar(stat = "identity", fill = "steelblue", alpha = 0.8) +
  geom_text(aes(label = paste0(round(Variance, 1), "%")),
            vjust = -0.5, size = 3.5, color = "black") +
  labs(
    title = "Varianza explicada por cada dimensión",
    x = "Dimensión",
    y = "Varianza explicada (%)"
  ) +
  theme_minimal(base_size = 13)


# Extraer la matriz de eigenvalores del FAMD
var_exp <- as.data.frame(c$eig)

# Asignar nombres claros
colnames(var_exp) <- c("Eigenvalue", "Variance", "CumulativeVariance")



# Graficar la varianza acumulada
ggplot(var_exp, aes(x = 1:nrow(var_exp), y = CumulativeVariance)) +
  geom_line(color = "steelblue", size = 1.2) +
  geom_point(color = "darkred", size = 2) +
  geom_text(aes(label = round(CumulativeVariance, 1)), vjust = -0.6, size = 3.5) +
  labs(
    title = "Varianza acumulada explicada por las dimensiones (FAMD)",
    x = "Dimensión",
    y = "Varianza acumulada (%)"
  ) +
  theme_minimal(base_size = 13)




############
  
  # ---  Extraer coordenadas ---
  coord_cat <- as.data.frame(c$quali.var$coord)
  coord_cat$Categoria <- rownames(c$quali.var$coord)
  
  # Crear una columna "Variable" con el nombre de la variable original
  # (todo lo que está antes del primer punto)
  coord_cat$Variable <- sub("\\..*", "", coord_cat$Categoria)
  
  # Coordenadas de las cuantitativas
  coord_num <- as.data.frame(c$quanti.var$coord)
  coord_num$Variable <- rownames(c$quanti.var$coord)
  
  # ---  Gráfico ---
  ggplot() +
    # Puntos de categorías agrupadas por variable (color)
    geom_point(
      data = coord_cat,
      aes(x = Dim.1, y = Dim.2, color = Variable),
      size = 3,
      alpha = 0.9
    ) +
    
    # Etiquetas de categorías (mismo color del grupo)
    geom_text_repel(
      data = coord_cat,
      aes(x = Dim.1, y = Dim.2, label = Categoria, color = Variable),
      size = 3,
      max.overlaps = 100,
      box.padding = 0.5,
      force = 1.3,
      show.legend = FALSE
    ) +
    
    # Vectores de las variables cuantitativas (azules)
    geom_segment(
      data = coord_num,
      aes(x = 0, y = 0, xend = Dim.1, yend = Dim.2),
      arrow = arrow(length = unit(0.25, "cm")),
      color = "blue",
      size = 1,
      alpha = 0.7
    ) +
    
    # Etiquetas de variables cuantitativas
    geom_text_repel(
      data = coord_num,
      aes(x = Dim.1, y = Dim.2, label = Variable),
      color = "blue",
      size = 3.2,
      max.overlaps = 100,
      box.padding = 0.8,
      force = 3,
      show.legend = FALSE
    ) +
    
    # Ejes y diseño
    geom_vline(xintercept = 0, linetype = 2, color = "gray70") +
    geom_hline(yintercept = 0, linetype = 2, color = "gray70") +
    theme_minimal() +
    ggtitle("FAMD, variables cuantitativas y cualitativas") +
    theme(
      plot.title = element_text(hjust = 0.5, face = "bold"),
      panel.grid.minor = element_blank(),
      legend.position = "bottom"
    ) +
    guides(color = guide_legend(title = "Variable Categórica"))
  