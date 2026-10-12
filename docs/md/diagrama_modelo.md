# Diagrama dimensional - Red Metropolitana

El modelo Gold utiliza dos tablas de hechos y cinco dimensiones conformadas. Todas las tablas Gold se construyen a partir de modelos Silver.

```mermaid
erDiagram
    DIM_FECHA ||--o{ FCT_ABORDAJES : fecha
    DIM_HORA ||--o{ FCT_ABORDAJES : hora
    DIM_USUARIO ||--o{ FCT_ABORDAJES : usuario
    DIM_MODO ||--o{ FCT_ABORDAJES : modo
    DIM_ZONA ||--o{ FCT_ABORDAJES : zona

    DIM_FECHA ||--o{ FCT_VIAJES_METRORIEL : fecha
    DIM_HORA ||--o{ FCT_VIAJES_METRORIEL : horas
    DIM_USUARIO ||--o{ FCT_VIAJES_METRORIEL : usuario
    DIM_MODO ||--o{ FCT_VIAJES_METRORIEL : modo
    DIM_ZONA ||--o{ FCT_VIAJES_METRORIEL : zonas

    DIM_FECHA {
        int fecha_sk PK
        date fecha
        int dia
        int mes
        int anio
        int trimestre
        int dia_semana
        boolean es_dia_habil
        boolean es_fin_semana
    }

    DIM_HORA {
        int hora_sk PK
        int hora
        string franja_horaria
        boolean es_hora_pico
    }

    DIM_USUARIO {
        string usuario_sk PK
        string perfil
        string zona_residencia
        boolean activo_en_transmetro
        string modos_identificados
        int cantidad_modos_identificados
    }

    DIM_MODO {
        int modo_sk PK
        string modo_nombre
    }

    DIM_ZONA {
        string zona_sk PK
        string zona_nombre
    }

    FCT_ABORDAJES {
        string abordaje_sk PK
        string evento_origen_id
        int modo_sk FK
        string usuario_sk FK
        string zona_sk FK
        int fecha_sk FK
        int hora_sk FK
        string ubicacion_codigo
        string servicio
        timestamp fecha_hora_local
        decimal monto_gtq
        boolean operacion_exitosa
        int cantidad_abordajes
    }

    FCT_VIAJES_METRORIEL {
        string viaje_sk PK
        bigint viaje_id
        int modo_sk FK
        string usuario_sk FK
        string zona_entrada_sk FK
        string zona_salida_sk FK
        int fecha_sk FK
        int hora_entrada_sk FK
        int hora_salida_sk FK
        timestamp fecha_hora_entrada
        timestamp fecha_hora_salida
        int duracion_segundos
        decimal monto_gtq
        int cantidad_viajes
    }