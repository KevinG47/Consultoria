# Fase 3 — Modelo de ML: contexto compacto

Documento de traspaso de la Fase 3 (modelo de clasificación de transición de
categoría). Estado: **cerrado el 26-oct-2026**. La ficha formal está en
[`model_card.md`](modelado/model_card.md); la bitácora completa de validación en
[`validacion_honesta.md`](modelado/validacion_honesta.md). El contexto general
del proyecto está en [`../contexto_deepseek.md`](../contexto_deepseek.md) (§17).

## 1. Qué se hizo

Predecir, para cada investigador reconocido y cada convocatoria `t`, si en la
convocatoria siguiente su categoría **sube**, **se mantiene** o **baja**.

- **XGBoost con máscaras estructurales** por categoría de origen: Junior
  binario (sube / se mantiene, porque IJ no puede bajar), Asociado y Senior
  tricótomos, Emérito excluido (sin transiciones).
- **172 features** de producción (volumen, clase de producto, tipología,
  categoría/calidad), sin `ano`. **111 tienen gain > 0 en el modelo final**
  (43 en el fold más pequeño, entrenado solo con la cohorte 17).
- Configuración: 100 árboles, `gamma=0.1`, `subsample=0.8`, `max_depth=7`,
  `learning_rate=0.05`, `min_child_weight=1`, pesos balanceados, semilla 42.
- Umbral de «baja»: **0,15** (mediana de los folds temporales).

## 2. Datos

| Fuente | Tamaño |
|---|---|
| Censo de investigadores reconocidos | 77 237 registros (persona × convocatoria) |
| Producción (`produccion_grupos.csv`) | 3 166 629 filas |
| Convocatorias | 6 (2013, 2014, 2015, 2017, 2019, 2021) |
| Transiciones contiguas modelables | **43 187** (18 116 personas) |

- **Train**: 2014, 2015, 2017 → 19 838 filas.
- **Val**: 2019 → 9 994.
- **Test**: 2021 → 13 355, evaluado **una sola vez**.

## 3. Métricas en test (13 355 filas, una sola vez)

| Métrica | Valor |
|---|---|
| F1 «baja» (umbral 0,15) | **0,4234** |
| Recall «baja» | **0,7878** |
| Precisión «baja» | 0,2895 |
| F1 macro | 0,5109 |
| Brier multiclase | **0,4692** |
| AUC «baja» | 0,8631 |
| Alertas emitidas | 25,7 % de las filas |

Referencias: constante con prevalencias de train → Brier 0,4419 y F1 «baja»
0,1851. Validación temporal (3 folds): F1 «baja» OOS medio 0,3054 (desv. 0,0295).

**Modelo bayesiano jerárquico** (capa de incertidumbre, no operativo): ordinal
acumulativo mínimo de 12 predictores, 2 cadenas × 1000+1000; **AUC «baja» 0,82**
y **Brier 0,437**. Mejores probabilidades, peor `argmax`.

## 4. Limitaciones

1. **Brier peor que la constante**: la prevalencia de «baja» pasa de 5,2 %
   (train) a 10,2 % (test). La corrección por *prior shift* se probó y **empeora**
   el Brier (0,4917–0,6054; 0,4851 incluso con la prevalencia observada como
   oráculo). No se aplica.
2. **Umbral sensible a la cohorte**: el óptimo por fold va de 0,08 a 0,29.
3. **Sobreajuste train-val**: F1 macro 0,83 en train vs 0,50 en val.
4. **61 de 172 features con gain 0 en el modelo final** (111 activas; en el fold
   más pequeño se activan 43).
5. **No hay coautorías en el dato**: 1,02 autores por producto; solo 72 226
   pares de coautoría en todo el censo. La red de grupos tampoco aporta.
6. **Solo 5 cohortes históricas**: no alcanza para validar estabilidad.

## 5. Cuatro rondas de mejora (todas sin cambio)

| Palanca | Mejor Δ en F1 «baja» OOS |
|---|---|
| Tuning (54 configuraciones) | +0,50 pp |
| Features top 50/80/120 | +0,00 pp |
| Demografía (género, edad, depto, institución) | −0,02 pp |
| Trayectoria (5 features) | +0,78 pp |
| Red de grupos (6 features) | +0,00 pp |
| Prior shift (Brier) | empeora (0,4917 vs 0,4692) |

Umbral de decisión para volver a test: +2 pp (0,3185). **Nunca se alcanzó.**
Conclusión: **techo del dato, no del método**.

## 6. Uso recomendado

- **Priorizar revisión humana, no automatizar.** Detecta ~79 % de los descensos
  pero 1 de cada 3,4 alertas es correcta.
- Las probabilidades no son confiables: usar el **ranking** y el umbral.
- Punto de operación: umbral 0,06–0,08 → recall 0,84–0,80; umbral 0,20 →
  recall 0,54. Recalcular el umbral con cada cohorte nueva.

## 7. Comandos de reproducción

```powershell
# evaluación final (entrena con 2014-2019 y evalúa 2021 una sola vez)
07_modelo\.venv-bayes\Scripts\python.exe 07_modelo/modelado/expE_test.py

# validación temporal (3 folds) y umbral mediana
07_modelo\.venv-bayes\Scripts\python.exe 07_modelo/modelado/pasoA_cv_temporal.py
07_modelo\.venv-bayes\Scripts\python.exe 07_modelo/modelado/expD_umbral_mediana.py
```

Entorno: Python 3.11.9 · xgboost 3.2.0 · scikit-learn 1.9.1 · venv
`07_modelo/.venv-bayes`. Semilla 42.

## 8. Artefactos

| Pieza | Ruta |
|---|---|
| Ficha del modelo | `07_modelo/modelado/model_card.md` |
| Bitácora y techo del dato | `07_modelo/modelado/validacion_honesta.md` |
| Utilidades de features y folds | `07_modelo/modelado/opt_comun.py` |
| Entrenamiento/evaluación final | `07_modelo/modelado/expE_test.py` |
| Resultados (JSON) | `07_modelo/modelado/resultados/` |
| Dataset modelable | `07_modelo/datos/derivados/modelo_dataset_ventana_contiguo.parquet` |
