# Reviews Kindle - Ejercicio de Gobierno y Gestión de Datos (UPC)

Este repositorio corresponde a un **ejercicio académico para la UPC** en el curso de **Gobierno y Gestión de Datos**.

## Objetivo
Realizar un proceso completo de **limpieza de datos** y recorrer todas las etapas del **esquema Medallion** utilizando el dataset de reseñas de Kindle de Kaggle:
- https://www.kaggle.com/datasets/bharadwaj6/kindle-reviews

El propósito es aplicar principios de **gobierno de datos** (calidad, trazabilidad, documentación y reproducibilidad) sobre un flujo de datos real.

## Alcance del trabajo
En este repositorio se desarrollará:
1. **Ingesta del dataset** (Bronze)
2. **Limpieza, estandarización y validaciones básicas** (Silver)
3. **Datos listos para análisis y consumo** (Gold)

El foco está en aplicar buenas prácticas de gobierno de datos y documentar el flujo de transformación de punta a punta.

## Esquema Medallion (visión general)
- **Bronze**: datos crudos tal como vienen del origen, sin modificar.
- **Silver**: datos limpios, con tipos normalizados, duplicados tratados, nulos gestionados y reglas de calidad básicas.
- **Gold**: datos curados y agregados para análisis, métricas y consumo final.

## Pipeline (por crear)
Se implementará un **pipeline reproducible** que automatice el flujo Bronze → Silver → Gold. Aún no existe, pero se prevé incluir:
- extracción del dataset desde Kaggle y registro de metadatos de origen
- reglas de calidad y validaciones (campos obligatorios, rangos, formatos)
- generación de tablas/archivos por capa con trazabilidad
- documentación de decisiones de limpieza y transformaciones aplicadas

## Estructura del repositorio (planificada)
La estructura se ajustará a medida que se implemente el pipeline. Se propone la siguiente organización:

```
.
├── data/
│   ├── bronze/        # datos crudos
│   ├── silver/        # datos limpios y normalizados
│   └── gold/          # datos curados para análisis
├── pipelines/         # scripts o notebooks del pipeline (por crear)
├── docs/              # documentación del proceso, diccionario de datos, decisiones
└── README.md
```

## Cómo ejecutar (placeholder)
El pipeline aún no está implementado. Cuando esté listo, esta sección incluirá:
- dependencias e instalación del entorno
- comandos para ejecutar la ingesta y las transformaciones
- ejemplos de ejecución por cada capa (Bronze, Silver, Gold)

## Autor
Carlos Adrian Alarcon (GitHub: [aladelca](https://github.com/aladelca))

## Nota
Este proyecto es exclusivamente educativo y se utiliza con fines de aprendizaje dentro de la UPC.
