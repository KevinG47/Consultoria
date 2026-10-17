"""
Sprint 6 — Borrador de la tabla maestra de IES.

Construye un primer borrador del catálogo canónico de instituciones a partir
de los strings que aparecen en INST_FILIA. La lista cubre las top entidades
por frecuencia, agrupando sedes y razones sociales bajo un nombre canónico
único, y asigna departamento por sede.

Salidas:
    evidencias/tabla_maestra_ies.csv          — una fila por IES canónica
    evidencias/mapping_inst_filia_to_ies.csv  — string original → IES canónica
    evidencias/ies_pendientes_revision.csv    — entradas sin mapeo asignado

Uso:
    python scripts/sprint6_tabla_maestra_ies.py
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

EVIDENCIAS = ROOT / "evidencias"
EVIDENCIAS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Tabla maestra: un registro por sede / razón social.
# Se agrupan bajo el mismo (nombre_canonico, sigla) las que pertenecen a la
# misma institución, pero el departamento_sede refleja la ubicación física
# real de cada sede (clave para el análisis geográfico institucional).
# ---------------------------------------------------------------------------

# Estructura: string_original_upper -> (nombre_canonico, sigla, departamento_sede, naturaleza)
MAPEO = {
    # --- Top 20 por frecuencia -------------------------------------------
    "UNIVERSIDAD DE ANTIOQUIA":
        ("Universidad de Antioquia", "UdeA", "Antioquia", "publica"),
    "UNIVERSIDAD NACIONAL DE COLOMBIA SEDE BOGOTA (UNIVERSIDAD NACIONAL DE COLOMBIA)":
        ("Universidad Nacional de Colombia", "UNAL", "Bogotá D.C.", "publica"),
    "UNIVERSIDAD NACIONAL DE COLOMBIA SEDE MEDELLIN (UNIVERSIDAD NACIONAL DE COLOMBIA)":
        ("Universidad Nacional de Colombia", "UNAL", "Antioquia", "publica"),
    "UNIVERSIDAD NACIONAL DE COLOMBIA SEDE MANIZALES (UNIVERSIDAD NACIONAL DE COLOMBIA)":
        ("Universidad Nacional de Colombia", "UNAL", "Caldas", "publica"),
    "UNIVERSIDAD NACIONAL DE COLOMBIA SEDE PALMIRA (UNIVERSIDAD NACIONAL DE COLOMBIA)":
        ("Universidad Nacional de Colombia", "UNAL", "Valle del Cauca", "publica"),
    "UNIVERSIDAD NACIONAL DE COLOMBIA":
        ("Universidad Nacional de Colombia", "UNAL", "Bogotá D.C.", "publica"),
    "PONTIFICIA UNIVERSIDAD JAVERIANA":
        ("Pontificia Universidad Javeriana", "PUJ", "Bogotá D.C.", "privada"),
    "PONTIFICIA UNIVERSIDAD JAVERIANA PUJ SEDE CALI (PONTIFICIA UNIVERSIDAD JAVERIANA)":
        ("Pontificia Universidad Javeriana", "PUJ", "Valle del Cauca", "privada"),
    "UNIVERSIDAD DE LOS ANDES":
        ("Universidad de los Andes", "Uniandes", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DEL VALLE":
        ("Universidad del Valle", "Univalle", "Valle del Cauca", "publica"),
    "UNIVERSIDAD INDUSTRIAL DE SANTANDER":
        ("Universidad Industrial de Santander", "UIS", "Santander", "publica"),
    "UNIVERSIDAD PONTIFICIA BOLIVARIANA":
        ("Universidad Pontificia Bolivariana", "UPB", "Antioquia", "privada"),
    "UNIVERSIDAD PONTIFICIA BOLIVARIANA SECCIONAL BUCARAMANGA (UNIVERSIDAD PONTIFICIA BOLIVARIANA)":
        ("Universidad Pontificia Bolivariana", "UPB", "Santander", "privada"),
    "COLEGIO MAYOR NUESTRA SENORA DEL ROSARIO":
        ("Universidad del Rosario", "URosario", "Bogotá D.C.", "privada"),
    "FUNDACION UNIVERSIDAD DEL NORTE":
        ("Universidad del Norte", "Uninorte", "Atlántico", "privada"),
    "UNIVERSIDAD DISTRITAL FRANCISCO JOSE DE CALDAS":
        ("Universidad Distrital Francisco José de Caldas", "UDFJC", "Bogotá D.C.", "publica"),
    "UNIVERSIDAD EAFIT":
        ("Universidad EAFIT", "EAFIT", "Antioquia", "privada"),
    "UNIVERSIDAD PEDAGOGICA Y TECNOLOGICA DE COLOMBIA UPTC SEDE TUNJA (UNIVERSIDAD PEDAGOGICA Y TECNOLOGICA DE COLOMBIA)":
        ("Universidad Pedagógica y Tecnológica de Colombia", "UPTC", "Boyacá", "publica"),
    "UNIVERSIDAD PEDAGOGICA Y TECNOLOGICA DE COLOMBIA":
        ("Universidad Pedagógica y Tecnológica de Colombia", "UPTC", "Boyacá", "publica"),
    "UNIVERSIDAD DE CARTAGENA":
        ("Universidad de Cartagena", "Unicartagena", "Bolívar", "publica"),
    "UNIVERSIDAD TECNOLOGICA DE PEREIRA":
        ("Universidad Tecnológica de Pereira", "UTP", "Risaralda", "publica"),
    "UNIVERSIDAD DE LA SABANA":
        ("Universidad de La Sabana", "Unisabana", "Cundinamarca", "privada"),
    "UNIVERSIDAD DE CALDAS":
        ("Universidad de Caldas", "Ucaldas", "Caldas", "publica"),
    "UNIVERSIDAD EXTERNADO DE COLOMBIA":
        ("Universidad Externado de Colombia", "Externado", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD MILITAR NUEVA GRANADA":
        ("Universidad Militar Nueva Granada", "UMNG", "Bogotá D.C.", "publica"),
    "UNIVERSIDAD DEL ATLANTICO":
        ("Universidad del Atlántico", "Uniatlántico", "Atlántico", "publica"),
    "UNIVERSIDAD DE LA SALLE":
        ("Universidad de La Salle", "ULaSalle", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DEL CAUCA":
        ("Universidad del Cauca", "Unicauca", "Cauca", "publica"),
    "UNIVERSIDAD EL BOSQUE":
        ("Universidad El Bosque", "UElBosque", "Bogotá D.C.", "privada"),
    "CORPORACION COLOMBIANA DE INVESTIGACION AGROPECUARIA AGROSAVIA":
        ("Corporación Colombiana de Investigación Agropecuaria", "Agrosavia", "Cundinamarca", "mixta"),
    "UNIVERSIDAD SANTO TOMAS":
        ("Universidad Santo Tomás", "USTA", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD SANTO TOMAS SECCIONAL BUCARAMANGA (UNIVERSIDAD SANTO TOMAS)":
        ("Universidad Santo Tomás", "USTA", "Santander", "privada"),
    "UNIVERSIDAD SANTO TOMAS SECCIONAL TUNJA (UNIVERSIDAD SANTO TOMAS)":
        ("Universidad Santo Tomás", "USTA", "Boyacá", "privada"),
    "CORPORACION UNIVERSIDAD DE LA COSTA":
        ("Universidad de la Costa", "CUC", "Atlántico", "privada"),
    "UNIVERSIDAD DEL TOLIMA":
        ("Universidad del Tolima", "UTolima", "Tolima", "publica"),
    "UNIVERSIDAD DE CORDOBA":
        ("Universidad de Córdoba", "Unicórdoba", "Córdoba", "publica"),
    "UNIVERSIDAD DE MEDELLIN":
        ("Universidad de Medellín", "UdeM", "Antioquia", "privada"),
    "UNIVERSIDAD COOPERATIVA DE COLOMBIA":
        ("Universidad Cooperativa de Colombia", "UCC", "Antioquia", "privada"),
    "UNIVERSIDAD DEL QUINDIO":
        ("Universidad del Quindío", "Uniquindío", "Quindío", "publica"),
    "UNIVERSIDAD DEL MAGDALENA":
        ("Universidad del Magdalena", "Unimagdalena", "Magdalena", "publica"),
    "UNIVERSIDAD LIBRE DE COLOMBIA":
        ("Universidad Libre", "Unilibre", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD PEDAGOGICA NACIONAL":
        ("Universidad Pedagógica Nacional", "UPN", "Bogotá D.C.", "publica"),
    "UNIVERSIDAD DE PAMPLONA":
        ("Universidad de Pamplona", "Unipamplona", "Norte de Santander", "publica"),
    "UNIVERSIDAD ICESI":
        ("Universidad ICESI", "ICESI", "Valle del Cauca", "privada"),
    "UNIVERSIDAD DE NARINO":
        ("Universidad de Nariño", "Udenar", "Nariño", "publica"),
    "UNIVERSIDAD JORGE TADEO LOZANO":
        ("Universidad de Bogotá Jorge Tadeo Lozano", "UTadeo", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD CES":
        ("Universidad CES", "CES", "Antioquia", "privada"),
    "UNIVERSIDAD SIMON BOLIVAR":
        ("Universidad Simón Bolívar", "Unisimón", "Atlántico", "privada"),
    "UNIVERSIDAD SIMON BOLIVAR SEDE BARRANQUILLA Y SEDE CUCUTA (UNIVERSIDAD SIMON BOLIVAR)":
        ("Universidad Simón Bolívar", "Unisimón", "Atlántico", "privada"),
    "INSTITUTO TECNOLOGICO METROPOLITANO DE MEDELLIN":
        ("Instituto Tecnológico Metropolitano", "ITM", "Antioquia", "publica"),
    "UNIVERSIDAD SANTIAGO DE CALI":
        ("Universidad Santiago de Cali", "USC", "Valle del Cauca", "privada"),
    "UNIVERSIDAD DE LA GUAJIRA":
        ("Universidad de La Guajira", "Uniguajira", "La Guajira", "publica"),
    "UNIVERSIDAD AUTONOMA DE BUCARAMANGA":
        ("Universidad Autónoma de Bucaramanga", "UNAB", "Santander", "privada"),
    "UNIVERSIDAD FRANCISCO DE PAULA SANTANDER":
        ("Universidad Francisco de Paula Santander", "UFPS", "Norte de Santander", "publica"),
    "UNIVERSIDAD NACIONAL ABIERTA Y A DISTANCIA":
        ("Universidad Nacional Abierta y a Distancia", "UNAD", "Bogotá D.C.", "publica"),
    "CORPORACION UNIVERSITARIA MINUTO DE DIOS UNIMINUTO":
        ("Corporación Universitaria Minuto de Dios", "UNIMINUTO", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD AUTONOMA DE OCCIDENTE":
        ("Universidad Autónoma de Occidente", "UAO", "Valle del Cauca", "privada"),
    "UNIVERSIDAD SERGIO ARBOLEDA":
        ("Universidad Sergio Arboleda", "USA", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD CATOLICA DE COLOMBIA":
        ("Universidad Católica de Colombia", "UCatólica", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD SURCOLOMBIANA":
        ("Universidad Surcolombiana", "USCO", "Huila", "publica"),
    "UNIVERSIDAD AUTONOMA DEL CARIBE":
        ("Universidad Autónoma del Caribe", "Uniautónoma", "Atlántico", "privada"),
    "UNIVERSIDAD CATOLICA LUIS AMIGO":
        ("Universidad Católica Luis Amigó", "UCatólicaLA", "Antioquia", "privada"),
    "INSTITUTO NACIONAL DE SALUD":
        ("Instituto Nacional de Salud", "INS", "Bogotá D.C.", "publica"),
    "UNIVERSIDAD DE SUCRE":
        ("Universidad de Sucre", "Unisucre", "Sucre", "publica"),
    "UNIVERSIDAD DE SAN BUENAVENTURA CALI (UNIVERSIDAD DE SAN BUENAVENTURA)":
        ("Universidad de San Buenaventura", "USB", "Valle del Cauca", "privada"),
    "UNIVERSIDAD DE SAN BUENAVENTURA SEDE MEDELLIN (UNIVERSIDAD DE SAN BUENAVENTURA)":
        ("Universidad de San Buenaventura", "USB", "Antioquia", "privada"),
    "UNIVERSIDAD DE SAN BUENAVENTURA SEDE BOGOTA (UNIVERSIDAD DE SAN BUENAVENTURA)":
        ("Universidad de San Buenaventura", "USB", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD SAN BUENAVENTURA CARTAGENA (UNIVERSIDAD DE SAN BUENAVENTURA)":
        ("Universidad de San Buenaventura", "USB", "Bolívar", "privada"),
    "UNIVERSIDAD AUTONOMA DE MANIZALES":
        ("Universidad Autónoma de Manizales", "Autónoma", "Caldas", "privada"),
    "CORPORACION UNIVERSITARIA AMERICANA":
        ("Corporación Universitaria Americana", "Americana", "Atlántico", "privada"),
    "UNIVERSIDAD ANTONIO NARINO SEDE BOGOTA U A N (UNIVERSIDAD ANTONIO NARINO)":
        ("Universidad Antonio Nariño", "UAN", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD ANTONIO NARINO":
        ("Universidad Antonio Nariño", "UAN", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DE MANIZALES UMANIZALES":
        ("Universidad de Manizales", "Umanizales", "Caldas", "privada"),
    "SERVICIO NACIONAL DE APRENDIZAJE SENA":
        ("Servicio Nacional de Aprendizaje", "SENA", "Bogotá D.C.", "publica"),
    "UNIVERSIDAD MANUELA BELTRAN":
        ("Universidad Manuela Beltrán", "UMB", "Bogotá D.C.", "privada"),
    "FUNDACION UNIVERSITARIA DE CIENCIAS DE LA SALUD FUCS":
        ("Fundación Universitaria de Ciencias de la Salud", "FUCS", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DE LOS LLANOS":
        ("Universidad de los Llanos", "Unillanos", "Meta", "publica"),
    "UNIVERSIDAD EAN":
        ("Universidad EAN", "EAN", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DE LA AMAZONIA":
        ("Universidad de la Amazonia", "Uniamazonia", "Caquetá", "publica"),
    "UNIVERSIDAD DE SANTANDER":
        ("Universidad de Santander", "UDES", "Santander", "privada"),
    "UNIVERSIDAD POPULAR DEL CESAR":
        ("Universidad Popular del Cesar", "UPC", "Cesar", "publica"),
    "UNIVERSIDAD DE BOYACA":
        ("Universidad de Boyacá", "Uniboyacá", "Boyacá", "privada"),
    "UNIVERSIDAD TECNOLOGICA DE BOLIVAR":
        ("Universidad Tecnológica de Bolívar", "UTB", "Bolívar", "privada"),
    "POLITECNICO COLOMBIANO JAIME ISAZA CADAVID":
        ("Politécnico Colombiano Jaime Isaza Cadavid", "PCJIC", "Antioquia", "publica"),
    "UNIDADES TECNOLOGICAS DE SANTANDER":
        ("Unidades Tecnológicas de Santander", "UTS", "Santander", "publica"),
    "CORPORACION UNIVERSITARIA DEL CARIBE CECAR":
        ("Corporación Universitaria del Caribe", "CECAR", "Sucre", "privada"),
    "UNIVERSIDAD DE CIENCIAS APLICADAS Y AMBIENTALES U D C A":
        ("Universidad de Ciencias Aplicadas y Ambientales", "UDCA", "Bogotá D.C.", "privada"),
    "FUNDACION UNIVERSITARIA DEL AREA ANDINA":
        ("Fundación Universitaria del Área Andina", "Areandina", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD CENTRAL":
        ("Universidad Central", "UCentral", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD MARIANA UNIMAR":
        ("Universidad Mariana", "Unimar", "Nariño", "privada"),
    "FUNDACION SANTA FE DE BOGOTA":
        ("Fundación Santa Fe de Bogotá", "FSFB", "Bogotá D.C.", "privada"),
    "TECNOLOGICO DE ANTIOQUIA INSTITUCION UNIVERSITARIA":
        ("Tecnológico de Antioquia", "TdeA", "Antioquia", "publica"),
    "CORPORACION UNIVERSITARIA LASALLISTA":
        ("Corporación Universitaria Lasallista", "Lasallista", "Antioquia", "privada"),
    "UNIVERSIDAD DEL SINU ELIAS BECHARA ZAINUM":
        ("Universidad del Sinú", "Unisinú", "Córdoba", "privada"),
    "UNIVERSIDAD EIA":
        ("Universidad EIA", "EIA", "Antioquia", "privada"),
    "INSTITUTO DE INVESTIGACION DE RECURSOS BIOLOGICOS ALEXANDER VON HUMBOLDT":
        ("Instituto Humboldt", "Humboldt", "Bogotá D.C.", "publica"),
    "FUNDACION UNIVERSITARIA LOS LIBERTADORES":
        ("Fundación Universitaria Los Libertadores", "Libertadores", "Bogotá D.C.", "privada"),
    "CORPORACION UNIVERSIDAD PILOTO DE COLOMBIA":
        ("Universidad Piloto de Colombia", "Unipiloto", "Bogotá D.C.", "privada"),
    "FUNDACION UNIVERSITARIA KONRAD LORENZ":
        ("Fundación Universitaria Konrad Lorenz", "Konrad", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DE IBAGUE":
        ("Universidad de Ibagué", "Unibagué", "Tolima", "privada"),
    "UNIVERSIDAD CATOLICA DE ORIENTE":
        ("Universidad Católica de Oriente", "UCO", "Antioquia", "privada"),
    "INSTITUTO NACIONAL DE CANCEROLOGIA ESE":
        ("Instituto Nacional de Cancerología", "INC", "Bogotá D.C.", "publica"),
    "UNIVERSIDAD CATOLICA DE PEREIRA":
        ("Universidad Católica de Pereira", "UCP", "Risaralda", "privada"),
    "UNIVERSIDAD CATOLICA DE MANIZALES":
        ("Universidad Católica de Manizales", "UCM", "Caldas", "privada"),
    "INSTITUTO DE INVESTIGACIONES MARINAS Y COSTERAS JOSE BENITO VIVES DE ANDREIS INVEMAR":
        ("Instituto INVEMAR", "INVEMAR", "Magdalena", "publica"),
    "UNIVERSIDAD COLEGIO MAYOR DE CUNDINAMARCA":
        ("Universidad Colegio Mayor de Cundinamarca", "UCMC", "Bogotá D.C.", "publica"),
    "ESCUELA COLOMBIANA DE INGENIERIA JULIO GARAVITO":
        ("Escuela Colombiana de Ingeniería Julio Garavito", "ECI", "Bogotá D.C.", "privada"),
    "FUNDACION CARDIOINFANTIL INSTITUTO DE CARDIOLOGIA":
        ("Fundación Cardioinfantil", "FCI", "Bogotá D.C.", "privada"),
    "INSTITUCION UNIVERSITARIA PASCUAL BRAVO":
        ("Institución Universitaria Pascual Bravo", "IUPB", "Antioquia", "publica"),
    "FUNDACION UNIVERSITARIA TECNOLOGICO COMFENALCO CARTAGENA":
        ("Fundación Universitaria Tecnológico Comfenalco", "Comfenalco", "Bolívar", "privada"),
    "UNIVERSIDAD AUTONOMA DE COLOMBIA":
        ("Universidad Autónoma de Colombia", "FUAC", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DE CUNDINAMARCA":
        ("Universidad de Cundinamarca", "Ucundinamarca", "Cundinamarca", "publica"),
    "INSTITUCION UNIVERSITARIA POLITECNICO GRANCOLOMBIANO":
        ("Politécnico Grancolombiano", "Poli", "Bogotá D.C.", "privada"),
    "CORPORACION UNIVERSITARIA REMINGTON":
        ("Corporación Universitaria Remington", "Remington", "Antioquia", "privada"),
    "HOSPITAL UNIVERSITARIO SAN IGNACIO":
        ("Hospital Universitario San Ignacio", "HUSI", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD ECCI":
        ("Universidad ECCI", "ECCI", "Bogotá D.C.", "privada"),
    "INSTITUCION UNIVERSITARIA ITSA":
        ("Institución Universitaria ITSA", "ITSA", "Atlántico", "publica"),
    "CORPORACION UNIVERSITARIA RAFAEL NUNEZ":
        ("Corporación Universitaria Rafael Núñez", "Curn", "Bolívar", "privada"),
    "FUNDACION VALLE DEL LILI":
        ("Fundación Valle del Lili", "FVL", "Valle del Cauca", "privada"),

    # --- Extensión segunda pasada (objetivo: superar 90% de cobertura) ---
    "UNIVERSIDAD METROPOLITANA":
        ("Universidad Metropolitana", "Unimetro", "Atlántico", "privada"),
    "UNIVERSIDAD FRANCISCO DE PAULA SANTANDER OCANA":
        ("Universidad Francisco de Paula Santander", "UFPS", "Norte de Santander", "publica"),
    "UNIVERSIDAD AUTONOMA LATINOAMERICANA UNAULA":
        ("Universidad Autónoma Latinoamericana", "UNAULA", "Antioquia", "privada"),
    "UNIVERSIDAD EL BOSQUE ESCUELA COLOMBIANA DE MEDICINA (UNIVERSIDAD EL BOSQUE)":
        ("Universidad El Bosque", "UElBosque", "Bogotá D.C.", "privada"),
    "INSTITUTO AMAZONICO DE INVESTIGACIONES CIENTIFICAS SINCHI":
        ("Instituto Amazónico de Investigaciones Científicas SINCHI", "SINCHI", "Amazonas", "publica"),
    "UNIVERSIDAD SIMON BOLIVAR SEDE CUCUTA (UNIVERSIDAD SIMON BOLIVAR)":
        ("Universidad Simón Bolívar", "Unisimón", "Norte de Santander", "privada"),
    "FUNDACION CARDIOVASCULAR DE COLOMBIA FLORIDABLANCA":
        ("Fundación Cardiovascular de Colombia", "FCV", "Santander", "privada"),
    "FUNDACION UNIVERSITARIA JUAN DE CASTELLANOS":
        ("Fundación Universitaria Juan de Castellanos", "JDC", "Boyacá", "privada"),
    "UNIVERSIDAD TECNOLOGICA DEL CHOCO DIEGO LUIS CORDOBA":
        ("Universidad Tecnológica del Chocó", "UTCH", "Chocó", "publica"),
    "UNIVERSIDAD CESMAG":
        ("Universidad CESMAG", "CESMAG", "Nariño", "privada"),
    "CORPORACION UNIVERSIDAD DE INVESTIGACION Y DESARROLLO":
        ("Universidad de Investigación y Desarrollo", "UDI", "Santander", "privada"),
    "FEDERACION NACIONAL DE CAFETEROS DE COLOMBIA CENTRO NACIONAL DE INVESTIGACIONES DE CAFE CENICAFE":
        ("Centro Nacional de Investigaciones de Café", "Cenicafé", "Caldas", "mixta"),
    "HOSPITAL PABLO TOBON URIBE":
        ("Hospital Pablo Tobón Uribe", "HPTU", "Antioquia", "privada"),
    "SERVICIO GEOLOGICO COLOMBIANO":
        ("Servicio Geológico Colombiano", "SGC", "Bogotá D.C.", "publica"),
    "FUNDACION UNIVERSITARIA AGRARIA DE COLOMBIA":
        ("Fundación Universitaria Agraria de Colombia", "UNIAGRARIA", "Bogotá D.C.", "privada"),
    "CORPORACION PARA INVESTIGACIONES BIOLOGICAS":
        ("Corporación para Investigaciones Biológicas", "CIB", "Antioquia", "privada"),
    "MINISTERIO DE EDUCACION NACIONAL MINEDUCACION":
        ("Ministerio de Educación Nacional", "MEN", "Bogotá D.C.", "publica"),
    "HOSPITAL MILITAR CENTRAL":
        ("Hospital Militar Central", "HMC", "Bogotá D.C.", "publica"),
    "FUNDACION UNIVERSIDAD DE AMERICA":
        ("Fundación Universidad de América", "UAmérica", "Bogotá D.C.", "privada"),
    "CORPORACION UNIVERSITARIA REPUBLICANA":
        ("Corporación Universitaria Republicana", "URepublicana", "Bogotá D.C.", "privada"),
    "FUNDACION UNIVERSITARIA MARIA CANO":
        ("Fundación Universitaria María Cano", "FUMC", "Antioquia", "privada"),
    "INSTITUCION UNIVERSITARIA DE ENVIGADO":
        ("Institución Universitaria de Envigado", "IUE", "Antioquia", "publica"),
    "UNIVERSIDAD SANTO TOMAS DE AQUINO SEDE BOGOTA USTA (UNIVERSIDAD SANTO TOMAS)":
        ("Universidad Santo Tomás", "USTA", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD PONTIFICIA BOLIVARIANA SECCIONAL MONTERIA (UNIVERSIDAD PONTIFICIA BOLIVARIANA)":
        ("Universidad Pontificia Bolivariana", "UPB", "Córdoba", "privada"),
    "CENTRO INTERNACIONAL DE AGRICULTURA TROPICAL":
        ("Centro Internacional de Agricultura Tropical", "CIAT", "Valle del Cauca", "mixta"),
    "UNIVERSIDAD LA GRAN COLOMBIA":
        ("Universidad La Gran Colombia", "UGC", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD LA GRAN COLOMBIA SECCIONAL ARMENIA (UNIVERSIDAD LA GRAN COLOMBIA)":
        ("Universidad La Gran Colombia", "UGC", "Quindío", "privada"),
    "UNIVERSIDAD DEL ROSARIO (COLEGIO MAYOR NUESTRA SENORA DEL ROSARIO)":
        ("Universidad del Rosario", "URosario", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DEL SINU SECCIONAL CARTAGENA (UNIVERSIDAD DEL SINU ELIAS BECHARA ZAINUM)":
        ("Universidad del Sinú", "Unisinú", "Bolívar", "privada"),
    "ESCUELA NACIONAL DEL DEPORTE":
        ("Escuela Nacional del Deporte", "END", "Valle del Cauca", "publica"),
    "CORPORACION CENTRO DE INVESTIGACION EN PALMA DE ACEITE":
        ("Centro de Investigación en Palma de Aceite", "Cenipalma", "Bogotá D.C.", "mixta"),
    "UNIVERSITARIA AGUSTINIANA":
        ("Universitaria Agustiniana", "Uniagustiniana", "Bogotá D.C.", "privada"),
    "INSTITUTO UNIVERSITARIO DE LA PAZ INUPAZ":
        ("Instituto Universitario de La Paz", "UNIPAZ", "Santander", "publica"),
    "MINISTERIO DE CIENCIA TECNOLOGIA E INNOVACION":
        ("Ministerio de Ciencia, Tecnología e Innovación", "MinCiencias", "Bogotá D.C.", "publica"),
    "DIRECCION NACIONAL DE ESCUELAS POLICIA NACIONAL DE COLOMBIA":
        ("Dirección Nacional de Escuelas - Policía Nacional", "DINAE", "Bogotá D.C.", "publica"),
    "INSTITUCION UNIVERSITARIA COLEGIO MAYOR DE ANTIOQUIA":
        ("Colegio Mayor de Antioquia", "Colmayor", "Antioquia", "publica"),
    "INSTITUTO COLOMBIANO DEL PETROLEO (ECOPETROL S A)":
        ("Instituto Colombiano del Petróleo - Ecopetrol", "ICP", "Santander", "mixta"),
    "UNIVERSIDAD DE SAN BUENAVENTURA":
        ("Universidad de San Buenaventura", "USB", "Bogotá D.C.", "privada"),
    "CORPORACION UNIFICADA DE EDUCACION SUPERIOR CUN":
        ("Corporación Unificada de Educación Superior", "CUN", "Bogotá D.C.", "privada"),
    "CORPORACION CENTRO INTERNACIONAL DE ENTRENAMIENTO E INVESTIGACIONES MEDICAS CIDEIM":
        ("Centro Internacional de Entrenamiento e Investigaciones Médicas", "CIDEIM", "Valle del Cauca", "privada"),
    "FUNDACION UNIVERSITARIA SAN MARTIN":
        ("Fundación Universitaria San Martín", "FUSM", "Bogotá D.C.", "privada"),
    "FUNDACION CENTRO INTERNACIONAL DE EDUCACION Y DESARROLLO HUMANO CINDE":
        ("Centro Internacional de Educación y Desarrollo Humano", "CINDE", "Caldas", "privada"),
    "ESCUELA NAVAL DE CADETES ALMIRANTE PADILLA":
        ("Escuela Naval de Cadetes Almirante Padilla", "ENAP", "Bolívar", "publica"),
    "UNIVERSIDAD PEDAGOGICA Y TECNOLOGICA DE COLOMBIA - UPTC - SEDE TUNJA (UNIVERSIDAD PEDAGOGICA Y TECNOLOGICA DE COLOMBIA)":
        ("Universidad Pedagógica y Tecnológica de Colombia", "UPTC", "Boyacá", "publica"),
    "FUNDACION UNIVERSITARIA SANITAS":
        ("Fundación Universitaria Sanitas", "Sanitas", "Bogotá D.C.", "privada"),
    "FUNDACION INSTITUTO DE INMUNOLOGIA DE COLOMBIA":
        ("Fundación Instituto de Inmunología de Colombia", "FIDIC", "Bogotá D.C.", "privada"),
    "CORPORACION UNIVERSITARIA ADVENTISTA":
        ("Corporación Universitaria Adventista", "UNAC", "Antioquia", "privada"),
    "FUNDACION UNIVERSITARIA AUTONOMA DE LAS AMERICAS":
        ("Fundación Universitaria Autónoma de las Américas", "Americas", "Antioquia", "privada"),
    "UNIDAD CENTRAL DEL VALLE DEL CAUCA":
        ("Unidad Central del Valle del Cauca", "UCEVA", "Valle del Cauca", "publica"),
    "CENTRO DE INVESTIGACION DE LA CANA DE AZUCAR DE COLOMBIA":
        ("Centro de Investigación de la Caña de Azúcar", "Cenicaña", "Valle del Cauca", "mixta"),
    "UNIVERSIDAD DE SANTANDER CAMPUS BUCARAMANGA (UNIVERSIDAD DE SANTANDER)":
        ("Universidad de Santander", "UDES", "Santander", "privada"),
    "COLEGIO DE ESTUDIOS SUPERIORES DE ADMINISTRACION CESA":
        ("Colegio de Estudios Superiores de Administración", "CESA", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD NACIONAL DE COLOMBIA SEDE AMAZONIA (UNIVERSIDAD NACIONAL DE COLOMBIA)":
        ("Universidad Nacional de Colombia", "UNAL", "Amazonas", "publica"),
    "FUNDACION HOSPITALARIA SAN VICENTE DE PAUL":
        ("Hospital San Vicente Fundación", "HSVF", "Antioquia", "privada"),
    "ESCUELA SUPERIOR DE ADMINISTRACION PUBLICA":
        ("Escuela Superior de Administración Pública", "ESAP", "Bogotá D.C.", "publica"),
    "INSTITUTO CARO Y CUERVO":
        ("Instituto Caro y Cuervo", "ICC", "Bogotá D.C.", "publica"),
    "INSTITUCION UNIVERSITARIA ANTONIO JOSE CAMACHO":
        ("Institución Universitaria Antonio José Camacho", "UNIAJC", "Valle del Cauca", "publica"),
    "INSTITUCION UNIVERSITARIA ESUMER":
        ("Institución Universitaria Esumer", "Esumer", "Antioquia", "privada"),
    "FUNDACION UNIVERSITARIA DE SAN GIL UNISANGIL":
        ("Fundación Universitaria de San Gil", "Unisangil", "Santander", "privada"),

    # --- Tercera pasada: sedes adicionales + IES regionales (objetivo > 90%) -
    "CONSEJO SUPERIOR DE INVESTIGACIONES CIENTIFICAS CSIC":
        ("Consejo Superior de Investigaciones Científicas (España)", "CSIC", "EXTRANJERO", "publica"),
    "FUNDACION UNIVERSITARIA DE POPAYAN":
        ("Fundación Universitaria de Popayán", "FUP", "Cauca", "privada"),
    "UNIVERSIDAD DE SAO PABLO":
        ("Universidad de São Paulo (Brasil)", "USP", "EXTRANJERO", "publica"),
    "FUNDACION UNIVERSITARIA JUAN N CORPAS":
        ("Fundación Universitaria Juan N. Corpas", "Corpas", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD SERGIO ARBOLEDA SEDE SANTA MARTA (UNIVERSIDAD SERGIO ARBOLEDA)":
        ("Universidad Sergio Arboleda", "USA", "Magdalena", "privada"),
    "UNIVERSIDAD PEDAGOGICA Y TECNOLOGICA DE COLOMBIA UPTC":
        ("Universidad Pedagógica y Tecnológica de Colombia", "UPTC", "Boyacá", "publica"),
    "INSTITUCION UNIVERSITARIA COLEGIOS DE COLOMBIA UNICOC ANTES COLEGIO ODONTOLOGICO COLOMBIANO":
        ("Institución Universitaria Colegios de Colombia", "UNICOC", "Bogotá D.C.", "privada"),
    "CORPORACION UNIVERSITARIA AUTONOMA DEL CAUCA":
        ("Corporación Universitaria Autónoma del Cauca", "Uniautónoma-Cauca", "Cauca", "privada"),
    "CORPORACION UNIVERSITARIA LATINOAMERICANA":
        ("Corporación Universitaria Latinoamericana", "CUL", "Atlántico", "privada"),
    "UNIVERSIDAD SANTO TOMAS VILLAVICENCIO (UNIVERSIDAD SANTO TOMAS)":
        ("Universidad Santo Tomás", "USTA", "Meta", "privada"),
    "UNIVERSIDAD LA GRAN COLOMBIA SEDE BOGOTA (UNIVERSIDAD LA GRAN COLOMBIA)":
        ("Universidad La Gran Colombia", "UGC", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DEL VALLE SEDE CALI (UNIVERSIDAD DEL VALLE)":
        ("Universidad del Valle", "Univalle", "Valle del Cauca", "publica"),
    "SECRETARIA DISTRITAL DE SALUD DE BOGOTA (ALCALDIA MAYOR DE BOGOTA)":
        ("Secretaría Distrital de Salud de Bogotá", "SDS", "Bogotá D.C.", "publica"),
    "FEDERACION NACIONAL DE CAFETEROS DE COLOMBIA FEDECAFE (FEDERACION NACIONAL DE CAFETEROS DE COLOMBIA CENTRO NACIONAL DE INVESTIGACIONES DE CAFE CENICAFE)":
        ("Centro Nacional de Investigaciones de Café", "Cenicafé", "Caldas", "mixta"),
    "SUMICOL SAS":
        ("Sumicol S.A.S.", "Sumicol", "Antioquia", "privada"),
    "FUNDACION NEUMOLOGICA COLOMBIANA":
        ("Fundación Neumológica Colombiana", "FNC", "Bogotá D.C.", "privada"),
    "FUNDACION UNIVERSITARIA SAN MATEO EDUCACION SUPERIOR":
        ("Fundación Universitaria San Mateo", "San Mateo", "Bogotá D.C.", "privada"),
    "FUNDACION UNIVERSITARIA COLOMBO INTERNACIONAL":
        ("Fundación Universitaria Colombo Internacional", "Unicolombo", "Bolívar", "privada"),
    "CORPORACION UNIVERSITARIA DEL META":
        ("Corporación Universitaria del Meta", "UNIMETA", "Meta", "privada"),
    "FUNDACION UNIVERSITARIA CEIPA":
        ("Fundación Universitaria CEIPA", "CEIPA", "Antioquia", "privada"),
    "CORPORACION PARA LA INVESTIGACION DE LA CORROSION":
        ("Corporación para la Investigación de la Corrosión", "CIC", "Santander", "mixta"),
    "INSTITUTO DE CAPACITACION E INVESTIGACION DEL PLASTICO Y DEL CAUCHO ICIPC":
        ("Instituto de Capacitación e Investigación del Plástico y del Caucho", "ICIPC", "Antioquia", "privada"),
    "CLINICA UNIVERSITARIA BOLIVARIANA UNIVERSIDAD PONTIFICIA BOLIVARIANA (UNIVERSIDAD PONTIFICIA BOLIVARIANA)":
        ("Universidad Pontificia Bolivariana", "UPB", "Antioquia", "privada"),
    "FUNDACION OFTALMOLOGICA DE SANTANDER":
        ("Fundación Oftalmológica de Santander", "FOSCAL", "Santander", "privada"),
    "INSTITUTO COLOMBIANO DE ANTROPOLOGIA E HISTORIA ICANH":
        ("Instituto Colombiano de Antropología e Historia", "ICANH", "Bogotá D.C.", "publica"),
    "ESCUELA SUPERIOR DE GUERRA":
        ("Escuela Superior de Guerra", "ESDEG", "Bogotá D.C.", "publica"),
    "CORPORACION POLITECNICO DE LA COSTA ATLANTICA":
        ("Politécnico de la Costa Atlántica", "PCA", "Atlántico", "privada"),
    "ESCUELA SUPERIOR DE ADMINISTRACION PUBLICA ESAP SEDE BOGOTA (ESCUELA SUPERIOR DE ADMINISTRACION PUBLICA)":
        ("Escuela Superior de Administración Pública", "ESAP", "Bogotá D.C.", "publica"),
    "FUNDACION UNIVERSIDAD INCCA DE COLOMBIA":
        ("Fundación Universidad INCCA de Colombia", "INCCA", "Bogotá D.C.", "privada"),
    "CORPORACION UNIVERSITARIA DEL HUILA":
        ("Corporación Universitaria del Huila", "Corhuila", "Huila", "privada"),
    "CORPORACION UNIVERSITARIA SANTA ROSA DE CABAL UNISARC":
        ("Corporación Universitaria Santa Rosa de Cabal", "UNISARC", "Risaralda", "privada"),
    "CENTRO PARA LA INVESTIGACION EN SISTEMAS SOSTENIBLES DE PRODUCCION AGROPECUARIA CIPAV":
        ("Centro para la Investigación en Sistemas Sostenibles de Producción Agropecuaria", "CIPAV", "Valle del Cauca", "mixta"),
    "FUNDACION INSTITUTO NEUROLOGICO DE COLOMBIA":
        ("Instituto Neurológico de Colombia", "INDEC", "Antioquia", "privada"),
    "INSTITUTO NACIONAL DE METROLOGIA INM":
        ("Instituto Nacional de Metrología", "INM", "Bogotá D.C.", "publica"),
    "FUNDACION UNIVERSIDAD JORGE TADEO LOZANO SANTA MARTA (UNIVERSIDAD JORGE TADEO LOZANO)":
        ("Universidad de Bogotá Jorge Tadeo Lozano", "UTadeo", "Magdalena", "privada"),
    "CORPORACION UNIVERSITARIA COMFACAUCA UNICOMFACAUCA":
        ("Corporación Universitaria Comfacauca", "Unicomfacauca", "Cauca", "privada"),
    "EMPRESA SOCIAL DEL ESTADO CENTRO DERMATOLOGICO FEDERICO LLERAS ACOSTA":
        ("Centro Dermatológico Federico Lleras Acosta", "CDFLLA", "Bogotá D.C.", "publica"),
    "UNIVERSIDAD PEDAGOGICA Y TECNOLOGICA DE COLOMBIA UPTC SEDE DUITAMA (UNIVERSIDAD PEDAGOGICA Y TECNOLOGICA DE COLOMBIA)":
        ("Universidad Pedagógica y Tecnológica de Colombia", "UPTC", "Boyacá", "publica"),
    "SERVICIO NACIONAL DE APRENDIZAJE SENA SEDE CALI (SERVICIO NACIONAL DE APRENDIZAJE SENA)":
        ("Servicio Nacional de Aprendizaje", "SENA", "Valle del Cauca", "publica"),
    "CENTRO MEDICO IMBANACO DE CALI SA":
        ("Centro Médico Imbanaco", "Imbanaco", "Valle del Cauca", "privada"),

    # --- Cuarta pasada: alias, sedes adicionales, IES regionales ---------
    "FUNDACION UNIVERSITARIA NAVARRA UNINAVARRA":
        ("Fundación Universitaria Navarra", "UNINAVARRA", "Huila", "privada"),
    "INSTITUTO TECNOLOGICO METROPOLITANO ITM":
        ("Instituto Tecnológico Metropolitano", "ITM", "Antioquia", "publica"),
    "INSTITUTO COLOMBIANO DE MEDICINA TROPICAL UNIVERSIDAD CES":
        ("Universidad CES", "CES", "Antioquia", "privada"),
    "FUNDACION ERIGAIE":
        ("Fundación Erigaie", "Erigaie", "Bogotá D.C.", "privada"),
    "CORPORACION UNIVERSITARIA DE SABANETA":
        ("Corporación Universitaria de Sabaneta", "UNISABANETA", "Antioquia", "privada"),
    "COMPANIA NACIONAL DE LEVADURAS LEVAPAN SA":
        ("Compañía Nacional de Levaduras Levapan", "Levapan", "Valle del Cauca", "privada"),
    "UNIVERSIDAD MANUELA BELTRAN SECCIONAL BUCARAMANGA (UNIVERSIDAD MANUELA BELTRAN)":
        ("Universidad Manuela Beltrán", "UMB", "Santander", "privada"),
    "CORPORACION VIDARIUM CENTRO DE INVESTIGACION EN NUTRICION SALUD Y BIENESTAR":
        ("Corporación Vidarium", "Vidarium", "Antioquia", "privada"),
    "FUNDACION TECNOLOGICA ANTONIO DE AREVALO TECNAR":
        ("Fundación Tecnológica Antonio de Arévalo", "Tecnar", "Bolívar", "privada"),
    "FUNDACION CATOLICA LUMEN GENTIUM":
        ("Fundación Católica Lumen Gentium", "FUCLG", "Valle del Cauca", "privada"),
    "SOCIEDAD DE CIRUGIA DE BOGOTA HOSPITAL DE SAN JOSE":
        ("Hospital de San José - Sociedad de Cirugía de Bogotá", "HSJ", "Bogotá D.C.", "privada"),
    "HOSPITAL UNIVERSITARIO DE LA SAMARITANA H U S":
        ("Hospital Universitario de la Samaritana", "HUS", "Bogotá D.C.", "publica"),
    "FUNDACION ABOOD SHAIO EN RESTRUCTURACION":
        ("Fundación Clínica Shaio", "Shaio", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD MARIANA (UNIVERSIDAD MARIANA UNIMAR)":
        ("Universidad Mariana", "Unimar", "Nariño", "privada"),
    "INDUSTRIA DE ALIMENTOS ZENU SAS":
        ("Industria de Alimentos Zenú", "Zenú", "Antioquia", "privada"),
    "CORPORACION UNIVERSITARIA EMPRESARIAL ALEXANDER VON HUMBOLDT":
        ("Corporación Universitaria Empresarial Alexander von Humboldt", "CUE", "Quindío", "privada"),
    "CORPORACION UNIVERSITARIA CENTRO SUPERIOR":
        ("Corporación Universitaria Centro Superior", "UNICUCES", "Valle del Cauca", "privada"),
    "JARDIN BOTANICO DE BOGOTA JOSE CELESTINO MUTIS":
        ("Jardín Botánico de Bogotá José Celestino Mutis", "JBB", "Bogotá D.C.", "publica"),
    "CORPORACION CORPOGEN":
        ("Corporación CorpoGen", "Corpogen", "Bogotá D.C.", "privada"),
    "UNIVERSIDADE ESTADUAL PAULISTA JULIO DE MESQUITA FILHO":
        ("Universidad Estadual Paulista (Brasil)", "UNESP", "EXTRANJERO", "publica"),
    "UNIVERSIDAD DEL PACIFICO":
        ("Universidad del Pacífico", "Unipacífico", "Valle del Cauca", "publica"),
    "UNIVERSIDAD ANTONIO NARINO TUNJA (UNIVERSIDAD ANTONIO NARINO)":
        ("Universidad Antonio Nariño", "UAN", "Boyacá", "privada"),
    "CORPORACION UNIVERSITARIA IBEROAMERICANA":
        ("Corporación Universitaria Iberoamericana", "Iberoamericana", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD PONTIFICIA BOLIVARIANA SEDE PALMIRA (UNIVERSIDAD PONTIFICIA BOLIVARIANA)":
        ("Universidad Pontificia Bolivariana", "UPB", "Valle del Cauca", "privada"),
    "CORPORACION UNIVERSITARIA DE CIENCIAS EMPRESARIALES EDUCACION Y SALUD":
        ("Corporación Universitaria de Ciencias Empresariales, Educación y Salud", "CORSALUD", "Atlántico", "privada"),
    "SERVICIO NACIONAL DE APRENDIZAJE SENA REGIONAL ATLANTICO (SERVICIO NACIONAL DE APRENDIZAJE SENA)":
        ("Servicio Nacional de Aprendizaje", "SENA", "Atlántico", "publica"),
    "INSTITUTO GEOGRAFICO AGUSTIN CODAZZI":
        ("Instituto Geográfico Agustín Codazzi", "IGAC", "Bogotá D.C.", "publica"),
    "INSTITUCION UNIVERSITARIA SALAZAR Y HERRERA":
        ("Institución Universitaria Salazar y Herrera", "IUSH", "Antioquia", "privada"),
    "FUNDACION HOSPITAL DE LA MISERICORDIA":
        ("Fundación Hospital de la Misericordia", "HOMI", "Bogotá D.C.", "privada"),
    "FUNDACION INSTITUTO DE ALTA TECNOLOGIA MEDICA DE ANTIOQUIA IATM":
        ("Instituto de Alta Tecnología Médica de Antioquia", "IATM", "Antioquia", "privada"),
    "CORPORACION UNIVERSITARIA DE CIENCIA Y DESARROLLO UNICIENCIA":
        ("Corporación Universitaria de Ciencia y Desarrollo", "UNICIENCIA", "Santander", "privada"),
    "FUNDACION UNIVERSITARIA COMPENSAR":
        ("Fundación Universitaria Compensar", "UCompensar", "Bogotá D.C.", "privada"),
    "PONTIFICIA UNIVERSIDAD JAVERIANA SEDE BOGOTA (PONTIFICIA UNIVERSIDAD JAVERIANA)":
        ("Pontificia Universidad Javeriana", "PUJ", "Bogotá D.C.", "privada"),
    "UNIVERSIDAD DEL NORTE":
        ("Universidad del Norte", "Uninorte", "Atlántico", "privada"),
    "CORPORACION UNIVERSITARIA REFORMADA":
        ("Corporación Universitaria Reformada", "UNIREFORMADA", "Atlántico", "privada"),
    "CORPORACION DE LUCHA CONTRA EL SIDA":
        ("Corporación de Lucha contra el Sida", "CLS", "Valle del Cauca", "privada"),
    "INSTITUTO NACIONAL DE MEDICINA LEGAL Y CIENCIAS FORENSES":
        ("Instituto Nacional de Medicina Legal y Ciencias Forenses", "INMLCF", "Bogotá D.C.", "publica"),
    "CORPORACION EDUCATIVA MAYOR DEL DESARROLLO SIMON BOLIVAR (UNIVERSIDAD SIMON BOLIVAR)":
        ("Universidad Simón Bolívar", "Unisimón", "Atlántico", "privada"),
    "ALPINA PRODUCTOS ALIMENTICIOS SA":
        ("Alpina Productos Alimenticios", "Alpina", "Cundinamarca", "privada"),
    "ANHIDRIDOS Y DERIVADOS DE COLOMBIA":
        ("Anhídridos y Derivados de Colombia", "Andercol", "Antioquia", "privada"),
}


def aplicar_mapeo(row: pd.Series) -> pd.Series:
    """Devuelve nombre canónico, sigla, departamento, naturaleza para una fila."""
    s = row["inst_filia_str"]
    if s in MAPEO:
        n, sg, dp, nat = MAPEO[s]
        return pd.Series({
            "nombre_canonico": n,
            "sigla": sg,
            "departamento_sede": dp,
            "naturaleza": nat,
            "estado": "asignado",
        })
    return pd.Series({
        "nombre_canonico": pd.NA,
        "sigla": pd.NA,
        "departamento_sede": pd.NA,
        "naturaleza": pd.NA,
        "estado": "pendiente_revision",
    })


def main() -> None:
    print("[1/4] Cargando dump de instituciones únicas...")
    raw = pd.read_csv(EVIDENCIAS / "instituciones_unicas_raw.csv")
    print(f"      Total entradas: {len(raw):,}")

    print("\n[2/4] Aplicando mapeo del borrador...")
    asignaciones = raw.apply(aplicar_mapeo, axis=1)
    mapping = pd.concat([raw, asignaciones], axis=1)

    n_asignado = (mapping["estado"] == "asignado").sum()
    cob_asignado = mapping.loc[mapping["estado"] == "asignado", "n_apariciones"].sum()
    total_apariciones = mapping["n_apariciones"].sum()
    print(f"      Entradas con mapeo asignado: {n_asignado} / {len(mapping)}")
    print(f"      Cobertura sobre el padrón: {cob_asignado/total_apariciones*100:.1f}% "
          f"({cob_asignado:,} de {total_apariciones:,} apariciones)")

    print("\n[3/4] Construyendo tabla maestra (consolidada por IES)...")
    asignadas = mapping[mapping["estado"] == "asignado"]
    maestra = (asignadas
        .groupby(["nombre_canonico", "sigla", "naturaleza"], dropna=False)
        .agg(
            sedes_registradas=("departamento_sede", "nunique"),
            departamentos=("departamento_sede", lambda s: " | ".join(sorted(set(s)))),
            apariciones_totales=("n_apariciones", "sum"),
            variantes_inst_filia=("inst_filia_str", "count"),
        )
        .reset_index()
        .sort_values("apariciones_totales", ascending=False))
    print(f"      IES canónicas: {len(maestra)}")

    print("\n[4/4] Exportando archivos...")
    maestra.to_csv(EVIDENCIAS / "tabla_maestra_ies.csv", index=False, encoding="utf-8")
    mapping.to_csv(EVIDENCIAS / "mapping_inst_filia_to_ies.csv", index=False, encoding="utf-8")

    pendientes = mapping[mapping["estado"] == "pendiente_revision"].copy()
    pendientes.to_csv(EVIDENCIAS / "ies_pendientes_revision.csv",
                       index=False, encoding="utf-8")
    cobertura_pendientes = pendientes["n_apariciones"].sum() / total_apariciones * 100

    print(f"      evidencias/tabla_maestra_ies.csv          ({len(maestra)} IES)")
    print(f"      evidencias/mapping_inst_filia_to_ies.csv  ({len(mapping)} filas)")
    print(f"      evidencias/ies_pendientes_revision.csv    "
          f"({len(pendientes)} entradas, {cobertura_pendientes:.1f}% del padrón)")

    print("\n--- Tabla maestra (top 20 por apariciones) ---")
    print(maestra.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
