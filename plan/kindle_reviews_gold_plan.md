# Plan detallado: De Silver a Gold para Dashboard de Ratings

## Contexto y objetivo
- Fuente: `data/silver/kindle_reviews/` (Parquet particionado por `review_year` y `review_month`).
- Capa gold: dataset **muy limpio y listo para dashboard**, en **un solo archivo Parquet** (no particionado).
- El dashboard debe mostrar:
  - Detalle de ratings (distribución, promedios, tendencias).
  - Desempeño de productos (mejores/peores, volumen de reviews, utilidad).

## Supuestos validados en silver
- Campos clave disponibles: `asin`, `overall`, `review_ts`, `review_date`, `helpful_yes`, `helpful_total`, `reviewerID`.
- `review_ts` está en UTC y `overall` es numérico.

## Diseño del dataset Gold (una sola tabla)
**Grano recomendado**: `asin` + `review_year` + `review_month`.
- Permite series temporales y comparaciones por producto.
- Un solo archivo Parquet con todas las filas (no particionado).

**Columnas sugeridas**
- Identificación:
  - `asin`
  - `review_year`
  - `review_month`
  - `period_start` (primer día del mes)
- Métricas de rating:
  - `review_count`
  - `avg_rating`
  - `median_rating`
  - `std_rating`
  - `pct_5`, `pct_4`, `pct_3`, `pct_2`, `pct_1` (distribución)
- Métricas de utilidad:
  - `helpful_yes_sum`
  - `helpful_total_sum`
  - `helpful_ratio` (= yes/total, con manejo de 0)
- Calidad/limpieza:
  - `distinct_reviewers`
  - `pct_missing_text` (reviewText nulo en el mes)

**Métricas lifetime (incluidas)**
- `lifetime_review_count`
- `lifetime_avg_rating`
- `lifetime_median_rating`
- `lifetime_helpful_ratio`
- `lifetime_distinct_reviewers`
  - Calculadas por `asin` y repetidas en cada fila mensual del producto.

## Reglas de limpieza adicionales (Gold)
1. **Eliminar duplicados**
   - Duplicados exactos por (`reviewerID`, `asin`, `review_ts`).
2. **Validar outliers**
   - `overall` fuera de [1,5] → excluir.
   - `helpful_yes > helpful_total` o negativos → set `helpful_*` a null y excluir de ratio.
3. **Datos temporales**
   - `review_ts` nulo → excluir (no se puede ubicar en el tiempo).

## Pipeline (paso a paso)
1. **Lectura**
   - Leer `data/silver/kindle_reviews/` con `pyarrow.dataset` (sin partición hive).
   - Seleccionar solo columnas necesarias para métricas y calidad.
2. **Normalización y validación**
   - Asegurar tipos numéricos (`overall`, `helpful_*`).
   - Eliminar duplicados por `reviewerID`, `asin`, `review_ts`.
   - Invalidar `helpful_*` si negativos o `helpful_yes > helpful_total`.
3. **Derivar período**
   - Crear `review_year` y `review_month` desde `review_ts`.
   - `period_start` = primer día del mes.
4. **Agregación mensual por producto**
   - Agrupar por `asin`, `review_year`, `review_month`.
   - Calcular métricas definidas.
5. **Métricas lifetime (obligatorias)**
   - Agregar por `asin` y unir a la tabla mensual.
6. **Salida Gold**
   - Guardar a `data/gold/kindle_reviews_dashboard.parquet`.
   - Archivo único (sin particiones).
7. **Reporte de calidad Gold (opcional recomendado)**
   - Conteo de productos, meses disponibles, % filas con ratio inválido.

## Ejemplos de inconsistencias y tratamiento
- Mismo `reviewerID` + `asin` + `review_ts` repetido → quedarse con 1.
- `helpful_total = 0` → `helpful_ratio = null`.
- `overall = 6` o `overall = "five"` → excluir del gold.
- `review_ts` nulo → excluir del gold.

## Entregables
1. Script: `pipelines/kindle_reviews_silver_to_gold.py`.
2. Output gold: `data/gold/kindle_reviews_dashboard.parquet` (archivo único).
3. (Opcional) Reporte DQ gold: `docs/dq_kindle_reviews_gold.md`.

## Preguntas abiertas
- ¿Quieres incluir un top-N de productos (por volumen) o mantener todo el universo?

## Estado de avance
- [x] Crear script `pipelines/kindle_reviews_silver_to_gold.py`.
- [x] Ejecutar script y generar `data/gold/kindle_reviews_dashboard.parquet`.
