## Depuración de IDs duplicados por convocatoria

Durante el proceso de limpieza de la base de datos se detectó la presencia de registros repetidos por persona en distintas convocatorias.
Para asegurar la consistencia del dataset y mantener únicamente la información más reciente de cada persona, se definió la siguiente regla de depuración:

Si un mismo ID aparecía en más de una convocatoria (por ejemplo, 19, 20 y 21), se conservó únicamente el registro correspondiente a la convocatoria más alta (más reciente).

Los registros asociados a convocatorias anteriores fueron eliminados.

Después de aplicar este procedimiento, el dataset final quedó conformado por 26.662 registros, garantizando que para cada persona solo se conserve la versión más actualizada de su información.


## Validación de unicidad de IDs

Con el fin de confirmar la calidad de la base depurada, se implementó un procedimiento en R que verifica la unicidad de los IDs.

La función utilizada realiza los siguientes pasos:

Agrupa los registros por ID_PERSONA_PR para revisar que cada persona tenga un único historial en la base final.

A partir de esta agrupación, se genera una nueva base de control con las siguientes variables:

ID_PERSONA_PR

ID_CONVOCATORIA

NME_GENERO_PR

EDAD_ANOS_PR

dif_edad (diferencia entre la edad nueva y la anterior).

La variable dif_edad fue diseñada como un mecanismo de control: su valor no debe superar 4 años entre registros consecutivos de la misma persona, lo que asegura coherencia temporal en la información.

Como resultado de la validación se identificaron 8 personas con valores de dif_edad superiores a lo esperado. Sin embargo, dado que en las demás variables de la base original no se encontraron incoherencias, se considera que estos casos corresponden a errores de digitación en la base original y no afectan de manera sustancial la integridad general del dataset. Por lo que se confirma que cada ID es unico.

El código empleado para esta verificación está documentado en el tarea_tabla/arreglar_base_consultoria_7.R 
