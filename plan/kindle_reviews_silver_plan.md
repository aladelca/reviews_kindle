# Plan detallado: Pasar kindle_reviews.json de raw a silver (Medallion)

## Contexto
- Fuente: `data/kindle_reviews.json` (NDJSON: 1 JSON por línea, ~0.8 GB).
- Capa raw: conservar el archivo original sin cambios.
- Capa silver: limpieza, normalización y particionado mensual en Parquet.
- Salida requerida: Parquet particionado por mes.

## Objetivos (silver)
- Tipos consistentes y parseables.
- Campos derivados para análisis.
- Reglas mínimas de calidad y trazabilidad (métricas DQ).
- Persistencia en `data/silver/` particionada por mes.

## Estado de avance
- [x] Crear carpetas `data/silver` y `data/gold`.
- [x] Crear script base en `pipelines/kindle_reviews_raw_to_silver.py`.
- [x] Ejecutar el script y validar salida Parquet particionada.
- [x] Revisar y validar reporte DQ en `docs/dq_kindle_reviews_silver.md`.

## Entregables
1. Script Python en `pipelines/kindle_reviews_raw_to_silver.py`.
2. Dataset silver en `data/silver/kindle_reviews/` (particionado por `review_year` y `review_month`).
3. Reporte DQ en `docs/dq_kindle_reviews_silver.md` (vacíos, outliers, nulos, conteos).

## Esquema Silver propuesto
Campos base (del raw):
- `reviewerID` (string) — requerido
- `asin` (string) — requerido
- `reviewerName` (string, opcional)
- `reviewText` (string, opcional)
- `summary` (string, opcional)
- `overall` (float) — requerido, rango [1,5]
- `reviewTime` (string original)
- `unixReviewTime` (int)
- `helpful` (array [yes, total])

Campos derivados (silver):
- `helpful_yes` (int)
- `helpful_total` (int)
- `review_ts` (timestamp, desde `unixReviewTime`)
- `review_date` (date, desde `reviewTime`)
- `review_year` (int, desde `review_ts`)
- `review_month` (int, desde `review_ts`)

## Reglas de limpieza y normalización
1. **Texto**
   - `reviewText`, `summary`, `reviewerName`: trim, reducir espacios múltiples, remover `\r` y `\t`.
   - `reviewText` vacío permitido si tiene score (no se filtra).
   - Si queda vacío, convertir a `null`.

2. **Tipos y parseo**
   - `overall` -> float con `errors='coerce'`.
   - `unixReviewTime` -> int con `errors='coerce'`.
   - `review_ts` -> datetime desde unix (seconds).
   - `review_date` -> datetime desde `reviewTime` (parse flexible).

3. **Helpful**
   - Si `helpful` es lista de largo 2: mapear a `helpful_yes`, `helpful_total`.
   - Si `helpful` inválido o faltante -> ambos `null`.

4. **Filtros mínimos (silver)**
   - Rechazar filas sin `reviewerID`, `asin` u `overall`.
   - Rechazar filas con `overall` fuera de [1,5].

5. **Particionado**
   - Particionar por `review_year` y `review_month` (derivados de `review_ts`).
   - Si `review_ts` es nulo, enviar a partición especial `review_year=-1`, `review_month=-1`.

## Ejemplos de inconsistencias y tratamiento
- `helpful`: si viene como `"[0,0]"` (string) en vez de lista → intentar parsear JSON; si falla → `helpful_yes=null`, `helpful_total=null`.
- `reviewTime`: formato irregular o inválido → `review_date=null`, pero se conserva `reviewTime` original.
- `unixReviewTime`: ausente o no numérico → `review_ts=null`, `review_year=-1`, `review_month=-1`.
- `overall`: `"five"` o `7` → `overall=null` → fila descartada.
- `reviewText`: cadena vacía → `reviewText=null`, fila se conserva si tiene `overall` válido.

## Métricas DQ mínimas (generadas al correr el script)
- Total leídas, total válidas, descartadas.
- Nulos/vacíos por columna (conteo y %).
- Outliers:
  - `overall` fuera de [1,5].
  - `helpful_yes > helpful_total`.
  - `helpful_total < 0` o `helpful_yes < 0`.
  - `review_ts` nulo o fuera de rango razonable (opcional: < 1997-01-01 o > fecha actual).
- Distribución de `overall`.
- % con `review_ts` válido.

## Pipeline propuesto (paso a paso)
1. **Lectura incremental**
   - Leer NDJSON con `pd.read_json(lines=True, chunksize=200_000)`.
2. **Limpieza por chunk**
   - Aplicar reglas de texto, tipos, helpful, derivadas.
3. **Filtrado de calidad**
   - Reglas mínimas de `reviewerID`, `asin`, `overall` y rango.
4. **Derivados de tiempo**
   - `review_ts`, `review_year`, `review_month` (o -1 si nulo).
5. **Escritura**
   - `data/silver/kindle_reviews/` en Parquet particionado (`review_year`, `review_month`).
6. **Reporte DQ**
   - Generar y guardar métricas DQ en `docs/dq_kindle_reviews_silver.md`.

## Pasos detallados y accionables para crear el script
1. **Crear archivo de pipeline**
   - Crear `pipelines/kindle_reviews_raw_to_silver.py`.
   - Definir constantes de rutas: `RAW_PATH`, `SILVER_DIR`, `OUT_DIR`, `DQ_REPORT_PATH`.

2. **Definir funciones auxiliares**
   - `parse_helpful(value)`:
     - Si `value` es lista/tupla de largo 2 → retornar (yes, total).
     - Si `value` es string tipo "[0,0]" → `json.loads`.
     - Si falla → retornar (None, None).
   - `clean_text(series)`:
     - `str.replace` para `\r`/`\t`, colapsar espacios, `str.strip`.
     - Convertir vacíos a `pd.NA`.

3. **Implementar limpieza por chunk**
   - Convertir columnas de texto con `clean_text`.
   - Aplicar `parse_helpful` y generar `helpful_yes`, `helpful_total`.
   - Tipar `overall` y `unixReviewTime` con `to_numeric(errors='coerce')`.
   - Crear `review_ts`, `review_date`.
   - Crear `review_year`, `review_month` (usar -1 si `review_ts` nulo).

4. **Calidad y filtros**
   - Filtrar por `reviewerID`, `asin`, `overall` no nulos.
   - Filtrar `overall` en [1,5].
   - Contabilizar outliers (antes de filtrar) para reporte DQ:
     - `overall` fuera de rango.
     - `helpful_yes > helpful_total`.
     - `helpful_total < 0` o `helpful_yes < 0`.
     - `review_ts` nulo.

5. **Escritura Parquet particionada**
   - Escribir a `data/silver/kindle_reviews/` con particiones `review_year` y `review_month`.
   - Usar `engine="pyarrow"` y `append=True` por chunk.

6. **Reporte DQ final**
   - Acumular métricas globales (contadores) en un dict.
   - Al final, generar `docs/dq_kindle_reviews_silver.md` con:
     - Totales leídos/filtrados.
     - Nulos por columna.
     - Outliers por regla.
     - Distribución simple de `overall`.
