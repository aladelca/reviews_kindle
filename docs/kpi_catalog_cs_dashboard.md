# KPI Catalog - Customer Service Dashboard (Kindle Reviews)

## Propósito
Definir KPIs críticos para el área de Servicio al Cliente, con fórmulas claras, utilidad, owners y trazabilidad.

## Fuentes y lineage
- Gold: `data/gold/kindle_reviews_dashboard.parquet`
- Silver: `data/silver/kindle_reviews/`
- Raw: `data/kindle_reviews.json`

## KPI Definitions

### 1) CSAT Rating Promedio (mensual)
- **Fórmula**: `avg_rating`
- **Descripción**: promedio mensual de calificaciones por producto.
- **Utilidad**: mide satisfacción reciente; monitorea cambios en la percepción.
- **Owner**: Customer Service Manager
- **Frecuencia**: mensual

### 2) Tasa de Reviews Negativas (1-2 estrellas)
- **Fórmula**: `pct_1 + pct_2`
- **Descripción**: proporción de reviews negativos en el mes.
- **Utilidad**: alerta temprana de problemas críticos.
- **Owner**: Customer Experience Lead
- **Frecuencia**: mensual

### 3) Volumen de Reviews (mensual)
- **Fórmula**: `review_count`
- **Descripción**: cantidad de reviews por producto y mes.
- **Utilidad**: prioriza productos con mayor exposición.
- **Owner**: Customer Service Ops
- **Frecuencia**: mensual

### 4) Volatilidad de Rating
- **Fórmula**: `std_rating`
- **Descripción**: desviación estándar de ratings mensuales.
- **Utilidad**: identifica inestabilidad o inconsistencias de percepción.
- **Owner**: Quality Assurance Lead
- **Frecuencia**: mensual

### 5) Helpfulness Ratio (mensual)
- **Fórmula**: `helpful_ratio = helpful_yes_sum / helpful_total_sum`
- **Descripción**: ratio de votos útiles en reviews.
- **Utilidad**: proxy de valor percibido de los reviews para clientes.
- **Owner**: Customer Insights
- **Frecuencia**: mensual

### 6) Rating Lifetime Promedio
- **Fórmula**: `lifetime_avg_rating`
- **Descripción**: promedio histórico de rating por producto.
- **Utilidad**: baseline para comparar tendencias recientes.
- **Owner**: Product Support
- **Frecuencia**: histórico

### 7) Brecha de Satisfacción (mensual vs lifetime)
- **Fórmula**: `avg_rating - lifetime_avg_rating`
- **Descripción**: diferencia entre el rating mensual y el promedio histórico.
- **Utilidad**: detecta deterioro/mejora reciente.
- **Owner**: Customer Experience Lead
- **Frecuencia**: mensual

### 8) Cobertura de Reviews (participación usuarios)
- **Fórmula**: `distinct_reviewers / review_count`
- **Descripción**: proporción de usuarios únicos por review.
- **Utilidad**: detecta concentración de opiniones en pocos usuarios.
- **Owner**: Customer Service Ops
- **Frecuencia**: mensual

### 9) Riesgo de Producto (flag operativo)
- **Fórmula**: `avg_rating < 3.0 OR (pct_1 + pct_2) > 0.25`
- **Descripción**: indicador binario para priorización de casos.
- **Utilidad**: ayuda a triage de productos críticos.
- **Owner**: Customer Service Manager
- **Frecuencia**: mensual

## Notas de calidad
- Si `review_count < 10`, KPI se considera de baja confiabilidad.
- Si `helpful_total_sum = 0`, `helpful_ratio` se reporta como nulo.
