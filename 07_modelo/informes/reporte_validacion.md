# Reporte de validación de la suite documental

**Fecha:** 2026-10-27 17:12 Hora est. Pacífico, Sudamérica  
**Validador:** `07_modelo/informes/validar_informes.py`  
**Alcance:** 6 informes de `07_modelo/informes/` (maestro + 5 modulares)  
**Fuentes de verdad:** `expE_test_20261026_024016.json`, `model_card.md` y el manifiesto del dataset

---

**Auditoría completada. 6 archivos revisados. 197 consistencias encontradas. 0 discrepancias corregidas.**

---

## 1. Archivos revisados

| Archivo | Líneas | Palabras |
|---|---:|---:|
| `00_informe_maestro.md` | 859 | 7763 |
| `01_ingesta_y_datos.md` | 326 | 2402 |
| `02_eda_y_auditoria.md` | 388 | 3059 |
| `03_modelado_xgboost.md` | 300 | 2245 |
| `04_modelo_bayesiano.md` | 302 | 2237 |
| `05_pruebas_alternativas.md` | 263 | 1995 |

## 2. Comprobaciones

| Comprobación | Resultado |
|---|---|
| Cifras de cierre (F1, recall, Brier) en contexto de test | OK |
| Transiciones = 43 187 | OK |
| Referencias cruzadas existentes | 42/42 OK |
| Ortografía de autores | OK |
| Anclaje a artefactos | expE_test:F1:OK; expE_test:Recall:OK; expE_test:Brier:OK; dataset:transiciones:OK |

El detalle de las comprobaciones es:

- **Cifras de cierre:** se considera contexto de cierre toda línea que menciona `test`, `cierre` o la cohorte 2021. En ese contexto, la cifra publicada debe ser la canónica. Las menciones a resultados experimentales (OOS, folds, matriz, benchmark, alternativas) se verifican contra su propio experimento y se listan abajo; no son discrepancias.
- **Transiciones:** se exige 43 187; se admite 47 151 solo cuando el texto lo etiqueta como variante «completo».
- **Referencias cruzadas:** todo enlace a un `.md` y toda mención «Informe NN» deben resolver a un archivo existente.
- **Autores:** se comparan las formas encontradas contra la lista canónica; se marcan variantes, errores de letra y tildes omitidas.
- **Anclaje:** las cifras canónicas se contrastan contra el JSON de test y el manifiesto del dataset.

## 3. Menciones contextuales verificadas

Valores que **no** son la cifra de cierre y que el validador deja intactos porque están etiquetados como resultados de otro experimento. No se corrigen: hacerlo falsificaría el informe.

| Archivo | Línea | Valor | Justificación |
|---|---:|---:|---|
| `00_informe_maestro.md` | 91 | 0,003 | modelo bayesiano (validación) |
| `00_informe_maestro.md` | 91 | 0,4370 | modelo bayesiano (validación) |
| `00_informe_maestro.md` | 322 | 0,003 | modelo bayesiano (validación) |
| `00_informe_maestro.md` | 322 | 0,4370 | modelo bayesiano (validación) |
| `00_informe_maestro.md` | 337 | 0,4370 | modelo bayesiano (validación) |
| `00_informe_maestro.md` | 340 | 0,003 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 359 | 0,132 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 360 | 0,345 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 372 | 0,54 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 397 | 0,2985 | folds / OOS |
| `00_informe_maestro.md` | 446 | 0,7437 | matriz (umbral 0,117) |
| `00_informe_maestro.md` | 447 | 0,4223 | matriz (umbral 0,117) |
| `00_informe_maestro.md` | 451 | 0,4592 | matriz (umbral 0,117) |
| `00_informe_maestro.md` | 462 | 0,79 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 493 | 0,6153 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 518 | 0,3054 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 520 | 0,4196 | folds / OOS |
| `00_informe_maestro.md` | 522 | 0,54 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 526 | 0,4196 | folds / OOS |
| `00_informe_maestro.md` | 555 | 0,4917 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 587 | 0,79 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 667 | 0,132 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 670 | 0,4370 | resultado experimental etiquetado |
| `00_informe_maestro.md` | 680 | 0,54 | folds / OOS |
| `02_eda_y_auditoria.md` | 316 | 0,6153 | resultado experimental etiquetado |
| `02_eda_y_auditoria.md` | 337 | 0,27 | folds / OOS |
| `03_modelado_xgboost.md` | 88 | 0,3185 | folds / OOS |
| `03_modelado_xgboost.md` | 148 | 0,132 | resultado experimental etiquetado |
| `03_modelado_xgboost.md` | 149 | 0,345 | resultado experimental etiquetado |
| `03_modelado_xgboost.md` | 188 | 0,15 | folds / OOS |
| `03_modelado_xgboost.md` | 227 | 0,238 | constante de referencia |
| `04_modelo_bayesiano.md` | 161 | 0,003 | resultado experimental etiquetado |
| `04_modelo_bayesiano.md` | 173 | 0,4370 | constante de referencia |
| `04_modelo_bayesiano.md` | 206 | 0,003 | resultado experimental etiquetado |
| `04_modelo_bayesiano.md` | 212 | 0,4370 | resultado experimental etiquetado |
| `04_modelo_bayesiano.md` | 216 | 0,4510 | modelo bayesiano (validación) |
| `04_modelo_bayesiano.md` | 250 | 0,1109 | resultado experimental etiquetado |
| `04_modelo_bayesiano.md` | 251 | 0,003 | resultado experimental etiquetado |
| `04_modelo_bayesiano.md` | 252 | 0,4370 | resultado experimental etiquetado |
| `04_modelo_bayesiano.md` | 265 | 0,4370 | resultado experimental etiquetado |
| `05_pruebas_alternativas.md` | 129 | 0,1269 | resultado experimental etiquetado |
| `05_pruebas_alternativas.md` | 211 | 0,2985 | folds / OOS |

## 4. Referencias cruzadas

| Archivo | Destino | Existe |
|---|---|---|
| `00_informe_maestro.md` | `01_ingesta_y_datos.md` | sí |
| `00_informe_maestro.md` | `02_eda_y_auditoria.md` | sí |
| `00_informe_maestro.md` | `03_modelado_xgboost.md` | sí |
| `00_informe_maestro.md` | `04_modelo_bayesiano.md` | sí |
| `00_informe_maestro.md` | `05_pruebas_alternativas.md` | sí |
| `00_informe_maestro.md` | `01_ingesta_y_datos.md` | sí |
| `00_informe_maestro.md` | `01_ingesta_y_datos.md` | sí |
| `00_informe_maestro.md` | `04_modelo_bayesiano.md` | sí |
| `00_informe_maestro.md` | `05_pruebas_alternativas.md` | sí |
| `00_informe_maestro.md` | `03_modelado_xgboost.md` | sí |
| `00_informe_maestro.md` | `03_modelado_xgboost.md` | sí |
| `00_informe_maestro.md` | `05_pruebas_alternativas.md` | sí |
| `00_informe_maestro.md` | `02_eda_y_auditoria.md` | sí |
| `00_informe_maestro.md` | `05_pruebas_alternativas.md` | sí |
| `00_informe_maestro.md` | `02_eda_y_auditoria.md` | sí |
| `00_informe_maestro.md` | `03_modelado_xgboost.md` | sí |
| `00_informe_maestro.md` | `Informe 1` | sí |
| `00_informe_maestro.md` | `Informe 2` | sí |
| `00_informe_maestro.md` | `Informe 3` | sí |
| `00_informe_maestro.md` | `Informe 4` | sí |
| `00_informe_maestro.md` | `Informe 5` | sí |
| `00_informe_maestro.md` | `Informe 1` | sí |
| `00_informe_maestro.md` | `Informe 1` | sí |
| `00_informe_maestro.md` | `Informe 4` | sí |
| `00_informe_maestro.md` | `Informe 5` | sí |
| `00_informe_maestro.md` | `Informe 3` | sí |
| `00_informe_maestro.md` | `Informe 3` | sí |
| `00_informe_maestro.md` | `Informe 5` | sí |
| `00_informe_maestro.md` | `Informe 2` | sí |
| `00_informe_maestro.md` | `Informe 5` | sí |
| `00_informe_maestro.md` | `Informe 2` | sí |
| `00_informe_maestro.md` | `Informe 3` | sí |
| `01_ingesta_y_datos.md` | `Informe 1` | sí |
| `01_ingesta_y_datos.md` | `Informe 2` | sí |
| `02_eda_y_auditoria.md` | `Informe 2` | sí |
| `02_eda_y_auditoria.md` | `Informe 1` | sí |
| `03_modelado_xgboost.md` | `Informe 3` | sí |
| `03_modelado_xgboost.md` | `Informe 1` | sí |
| `03_modelado_xgboost.md` | `Informe 5` | sí |
| `04_modelo_bayesiano.md` | `Informe 4` | sí |
| `05_pruebas_alternativas.md` | `Informe 5` | sí |
| `05_pruebas_alternativas.md` | `Informe 3` | sí |

## 5. Ortografía de autores

Sin variantes: todas las formas encontradas coinciden con la lista canónica.

## 6. Discrepancias corregidas

No hubo cifras que corregir: todas las menciones de cierre ya contenían el valor canónico.

## 7. Hallazgos pendientes

Ninguno.

---

## 8. Alcance y límites del validador

El validador comprueba **consistencia textual y anclaje a artefactos**, no la verdad sustantiva de cada afirmación. Es decir: garantiza que los seis documentos digan lo mismo y que esas cifras coincidan con el JSON de test y el manifiesto del dataset; no sustituye la revisión de un lector humano sobre la interpretación de los resultados.

Las menciones contextuales se listan para que el lector pueda auditar la decisión: son valores de otros experimentos (OOS, matriz, benchmark, alternativas) y convertirlos a 0,4234 habría introducido un error. El validador solo corrige redondeos inequívocos de la cifra de cierre.

**Reproducción:**

```powershell
07_modelo\.venv-bayes\Scripts\python.exe 07_modelo/informes/validar_informes.py
```
