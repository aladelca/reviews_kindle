# Plan detallado: Dashboard de Servicio al Cliente (Streamlit) sobre Gold

## 1) Contexto y objetivo
- Dataset gold: `data/gold/kindle_reviews_dashboard.parquet` (23 columnas, 48,735 filas).
- Grano: `asin` + `review_year` + `review_month` (métricas mensuales por producto) con métricas lifetime.
- Objetivo del dashboard (Customer Service):
  - Monitorear satisfacción y señales tempranas de problemas.
  - Priorizar productos con bajas calificaciones y alto volumen.
  - Medir impacto de cambios en rating en el tiempo.

## 2) Diagnóstico rápido del dataset gold (validado)
- Columnas disponibles:
  - Identificación/tiempo: `asin`, `review_year`, `review_month`, `period_start`
  - Ratings: `review_count`, `avg_rating`, `median_rating`, `std_rating`, `pct_1..pct_5`
  - Utilidad: `helpful_yes_sum`, `helpful_total_sum`, `helpful_ratio`
  - Calidad: `distinct_reviewers`, `pct_missing_text`
  - Lifetime: `lifetime_review_count`, `lifetime_avg_rating`, `lifetime_median_rating`, `lifetime_distinct_reviewers`, `lifetime_helpful_ratio`

## 3) KPIs prioritarios (Customer Service) y documentación (DAMA-DMBOK)
> Esta sección debe convertirse en documentación oficial (Data Glossary + Data Dictionary).

### Tabla de KPIs (definición, fórmula, utilidad, owner)
1. **CSAT Rating Promedio (mensual)**
   - Fórmula: `avg_rating`
   - Utilidad: mide satisfacción reciente por producto.
   - Owner: Customer Service Manager.

2. **Tasa de Reviews Negativas (1-2 estrellas)**
   - Fórmula: `pct_1 + pct_2`
   - Utilidad: alerta temprana de problemas severos.
   - Owner: Customer Experience Lead.

3. **Volumen de Reviews (mensual)**
   - Fórmula: `review_count`
   - Utilidad: prioriza productos con mayor exposición.
   - Owner: Customer Service Ops.

4. **Volatilidad de Rating**
   - Fórmula: `std_rating`
   - Utilidad: identifica inestabilidad en percepción del producto.
   - Owner: Quality Assurance Lead.

5. **Helpfulness Ratio (mensual)**
   - Fórmula: `helpful_ratio = helpful_yes_sum / helpful_total_sum`
   - Utilidad: proxy de valor percibido de los reviews.
   - Owner: Customer Insights.

6. **Rating Lifetime Promedio**
   - Fórmula: `lifetime_avg_rating`
   - Utilidad: baseline histórico para comparar tendencias recientes.
   - Owner: Product Support.

7. **Brecha de Satisfacción (mensual vs lifetime)**
   - Fórmula: `avg_rating - lifetime_avg_rating`
   - Utilidad: detecta deterioro/mejora reciente.
   - Owner: Customer Experience Lead.

8. **Cobertura de Reviews (participación usuarios)**
   - Fórmula: `distinct_reviewers / review_count`
   - Utilidad: detecta concentración de opiniones en pocos usuarios.
   - Owner: Customer Service Ops.

### Entregable de documentación
- Crear `docs/kpi_catalog_cs_dashboard.md` con:
  - Definición, fórmula, owner, frecuencia, dimensión temporal, fuente.
  - Lineage: gold (fuente), silver, raw.

## 4) Diseño de dashboard en Streamlit (accionable)
### 4.1 Estructura de la app
- Archivo: `apps/cs_dashboard.py` (crear carpeta `apps/`).
- Secciones:
  1) **KPIs globales** (cards con filtros de fecha/producto).
  2) **Tendencias** (línea por mes: `avg_rating`, `review_count`, `pct_1+pct_2`).
  3) **Ranking de productos** (top/bottom por rating, volumen, brecha vs lifetime).
  4) **Detalle por producto** (panel con evolución mensual y distribución de rating).

### 4.2 Filtros
- Rango de fechas (slider por `period_start`).
- Selector de producto (`asin`) con búsqueda.
- Filtro de volumen mínimo (`review_count >= N`).

### 4.3 Visualizaciones clave
- **KPI cards**: `avg_rating`, `pct_1+pct_2`, `review_count`, `helpful_ratio`.
- **Line charts**: evolución temporal por KPI.
- **Bar chart**: top 10 productos con `pct_1+pct_2` más alto.
- **Scatter**: `avg_rating` vs `review_count` para priorización.
- **Heatmap**: meses vs avg_rating (opcional).

### 4.4 UX y acciones
- Resaltar productos con `avg_rating < 3.0` o `pct_1+pct_2 > 0.25`.
- Badge "en riesgo" y export a CSV de lista priorizada.

## 5) Controles de calidad (DAMA-DMBOK)
- **Data Quality Rules** en dashboard:
  - Avisar si `review_count` muy bajo (<10) para evitar interpretaciones erróneas.
  - Avisar si `helpful_ratio` es nulo por falta de datos.
- **Metadata y Lineage**:
  - Mostrar fuente y fecha de generación del gold en sidebar.
- **Data Stewardship**:
  - Definir responsable de aprobación de KPIs (Data Owner + Data Steward).

## 6) Plan de implementación (accionable)
1. **Documentación de KPIs**
   - Crear `docs/kpi_catalog_cs_dashboard.md` con definiciones y owners.
2. **App Streamlit base**
   - Crear `apps/cs_dashboard.py`.
   - Cargar dataset con `st.cache_data`.
3. **Capa de filtros**
   - Implementar selector de fechas, asin, volumen mínimo.
4. **KPIs principales**
   - Calcular KPIs globales con datos filtrados.
   - Mostrar tarjetas con variación mensual (delta).
5. **Visualizaciones**
   - Implementar gráficos en secciones (líneas, ranking, scatter).
6. **Alertas y segmentación**
   - Marcar productos en riesgo y exportar lista.
7. **Validación de datos**
   - Checks básicos y mensajes de warning.
8. **QA funcional**
   - Probar con distintos filtros y tamaños.

## 7) Checklist DAMA-DMBOK (resumido)
- **Data Governance**: owners definidos por KPI.
- **Data Quality**: reglas visibles y registradas.
- **Metadata**: glosario + diccionario en docs.
- **Security/Privacy**: dataset sin PII (solo `reviewerID` agregado).
- **Data Lifecycle**: gold actualizado con script silver→gold.

## Estado de avance
- [x] Crear documentación de KPIs.
- [x] Implementar dashboard en Streamlit.
- [ ] Validar métricas y UX.
