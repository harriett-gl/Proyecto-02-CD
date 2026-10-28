
# 🚇 Proyecto 01 — Red Metropolitana de Transporte

**Universidad Rafael Landívar**  
**Curso:** Ciencia de Datos  
**Proyecto:** Red Metropolitana de Transporte  
**Fases desarrolladas:** Fase 01 y Fase 02

---

## 📌 Descripción general

El proyecto **Red Metropolitana de Transporte** tiene como finalidad integrar, transformar, validar, analizar y visualizar información de movilidad correspondiente a cuatro operadores de transporte:

- Transmetro
- Transurbano
- MetroRiel
- Aerometro

La solución utiliza una arquitectura de ingeniería de datos basada en capas, con el propósito de garantizar la calidad, trazabilidad y disponibilidad de la información para su posterior análisis.

El proyecto se desarrolla en dos fases:

- **Fase 01:** construcción de la arquitectura de datos, ingesta, transformación y modelo dimensional.
- **Fase 02:** implementación de features analíticas, análisis de demanda, cobertura territorial, validaciones y visualización de resultados.

---

## 🛠️ Tecnologías utilizadas

| Tecnología | Función |
|---|---|
| Python 3.12 | Ingesta, procesamiento y análisis de datos |
| PostgreSQL | Almacenamiento de información |
| Docker | Contenedores y servicios |
| Apache Kafka | Procesamiento de eventos de streaming |
| dbt Core | Transformación y validación de datos |
| Prefect | Orquestación del pipeline |
| PyArrow | Procesamiento de archivos Parquet |
| Pandas | Manipulación y análisis de datos |
| Psycopg | Conexión con PostgreSQL |
| Tableau Desktop | Visualización de información |
| Git y GitHub | Control de versiones |

---

# 🏗️ Arquitectura del proyecto

El procesamiento de datos sigue la siguiente arquitectura:

```text
FUENTES DE DATOS
       |
       v
INGESTA DE DATOS
(Batch / Streaming / CDC)
       |
       v
BRONZE
(Archivos Parquet)
       |
       v
STAGING
(PostgreSQL)
       |
       v
SILVER
(Limpieza y normalización)
       |
       +------> QUARANTINE
       |        (Registros inválidos)
       v
GOLD
(Modelo dimensional)
       |
       +------> FEATURES
       |        (Análisis de movilidad)
       |
       v
REPORTES ANALÍTICOS
(Demanda y cobertura)
       |
       v
TABLEAU
(Dashboards)
```

La solución también incorpora un esquema de auditoría y mecanismos de orquestación mediante Prefect.

---

# 📁 Estructura del proyecto

```text
Proyecto01-Fase01/
│
├── datos_red/
│   └── Fuentes originales del proyecto
│
├── lake/
│   └── bronze/
│       ├── batch/
│       ├── cdc/
│       └── streaming/
│
├── scripts/
│   ├── cargar_staging.py
│   ├── ingesta_batch.py
│   ├── ingesta_cdc.py
│   ├── stream_consumer.py
│   ├── stream_producer.py
│   ├── generar_diccionario.py
│   └── medir_consultas_tablero.py
│
├── orchestration/
│   └── flow_red_metropolitana.py
│
├── dbt_red_metropolitana/
│   ├── macros/
│   │   └── definiciones_oficiales.sql
│   │
│   ├── models/
│   │   ├── staging/
│   │   ├── silver/
│   │   ├── quarantine/
│   │   ├── gold/
│   │   │   ├── rpt_demanda_red.sql
│   │   │   ├── rpt_cobertura_zona.sql
│   │   │   └── reportes.yml
│   │   │
│   │   ├── features/
│   │   │   ├── features_usuario_movilidad.sql
│   │   │   └── features.yml
│   │   │
│   │   └── exposures.yml
│   │
│   ├── tests/
│   ├── dbt_project.yml
│   └── profiles.yml
│
├── docs/
│   ├── evidencias/
│   │   ├── Proyecto 01 - Fase 01.pdf
│   │   ├── Proyecto 01 - Fase 02.pdf
│   │   └── Proyecto 01 - Fase 02.twb
│   │
│   ├── diccionario_datos.md
│   ├── features.md
│   ├── gobernanza.md
│   ├── metricas_fase1.md
│   ├── metricas_fase2.md
│   ├── recomendacion.md
│   ├── seguridad.md
│   ├── tablero.md
│   └── últimas pruebas.sql
│
├── docker-compose.yml
├── generar_red_metropolitana.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

**Nota:** algunos directorios contienen archivos generados durante la ejecución y pueden estar excluidos del repositorio mediante `.gitignore`.

---

# 🟣 FASE 01 — Ingeniería y arquitectura de datos

## 🎯 Objetivo

Construir una plataforma de ingeniería de datos capaz de integrar información de distintos operadores de transporte mediante procesos de ingesta, almacenamiento, transformación y validación.

## 1. Ingesta de datos

Se implementaron tres mecanismos de ingesta.

### Ingesta Batch

Procesamiento de archivos históricos y catálogos de transporte.

### Ingesta Streaming

Procesamiento de eventos mediante Apache Kafka, principalmente para Transmetro y Aerometro.

### Ingesta CDC

Procesamiento de modificaciones del padrón de usuarios.

Los datos originales se almacenan en formato Parquet dentro de la capa Bronze.

## 2. Capa Bronze

Conserva los datos originales antes de su transformación.

Permite:

- Mantener los registros originales.
- Conservar información de procedencia.
- Facilitar el reprocesamiento.
- Organizar archivos por fuente y tipo de ingesta.

## 3. Capa Staging

Carga los datos provenientes de Bronze hacia PostgreSQL para facilitar las transformaciones posteriores.

## 4. Capa Silver

Implementa procesos de:

- Limpieza de información.
- Normalización de campos.
- Validación de fechas.
- Estandarización de zonas.
- Procesamiento de usuarios.
- Aplicación de reglas de calidad.

## 5. Capa Quarantine

Almacena registros que no cumplen las reglas de calidad establecidas.

Esto permite separar información inválida sin eliminarla definitivamente.

## 6. Capa Gold

Se implementó un modelo dimensional para facilitar las consultas analíticas.

### Dimensiones

| Dimensión | Descripción |
|---|---|
| `dim_fecha` | Información temporal |
| `dim_hora` | Distribución por hora |
| `dim_modo` | Modos de transporte |
| `dim_usuario` | Usuarios de la red |
| `dim_zona` | Zonas geográficas |

### Tablas de hechos

| Tabla | Descripción |
|---|---|
| `fct_abordajes` | Eventos de abordaje |
| `fct_viajes_metroriel` | Viajes registrados en MetroRiel |

## 7. Orquestación

Se utiliza Prefect para coordinar las etapas del pipeline y facilitar su ejecución.

## 8. Resultados de Fase 01

| Indicador | Resultado |
|---|---:|
| Registros en Staging | 1,730,184 |
| Registros en Silver | 1,919,887 |
| Registros en Gold | 1,718,037 |
| Registros en cuarentena | 18,431 |
| Viajes válidos de MetroRiel | 295,511 |

### Idempotencia

Se verificó que dos ejecuciones consecutivas del pipeline produjeran los mismos totales por capa, sin duplicar registros.

---

# 🔵 FASE 02 — Análisis y visualización de datos

## 🎯 Objetivo

Ampliar la arquitectura de la Fase 01 mediante modelos analíticos que permitan estudiar la movilidad de los usuarios, identificar patrones multimodales y evaluar la demanda y cobertura territorial.

## 1. Features de movilidad

Se implementó el modelo:

`features.features_usuario_movilidad`

Este modelo permite obtener características analíticas relacionadas con el comportamiento de los usuarios.

Entre las variables consideradas se encuentran:

- Cantidad de modos de transporte identificados.
- Identificación de usuarios multimodales.
- Actividad registrada.
- Zonas de movilidad.
- Patrones asociados con el uso del transporte.

### Resultados

Se procesaron **70,380 usuarios** en el modelo de features.

| Modos identificados | Usuarios |
|---|---:|
| 1 modo | 33,551 |
| 2 modos | 26,833 |
| 3 modos | 9,996 |
| **Total** | **70,380** |

Se considera usuario multimodal a quien utiliza o está identificado en dos o más modos de transporte.

**Usuarios multimodales identificados: 36,829.**

---

## 2. Modelo de demanda

Se implementó:

`gold.rpt_demanda_red`

Este modelo permite analizar los abordajes registrados por modo de transporte.

### Resultados de demanda

| Modo de transporte | Abordajes |
|---|---:|
| Transurbano | 786,398 |
| Transmetro | 362,106 |
| MetroRiel | 295,511 |
| Aerometro | 203,554 |

Estos resultados facilitan la comparación de la demanda entre operadores.

---

## 3. Modelo de cobertura territorial

Se implementó:

`gold.rpt_cobertura_zona`

Este modelo permite analizar la demanda por zona y su relación con la cobertura de transporte.

El análisis permite:

- Identificar zonas con mayor demanda.
- Comparar zonas con y sin cobertura de MetroRiel.
- Detectar oportunidades de mejora.
- Apoyar decisiones de planificación territorial.

### Caso MetroRiel

Se analizaron zonas objetivo relacionadas con el servicio de MetroRiel.

| Zona | Demanda total |
|---|---:|
| Zona 17 | 94,799 |
| Zona 12 | 93,933 |
| Zona 1 | 83,367 |
| Zona 8 | 80,157 |
| Zona 6 | 71,840 |

---

## 4. Validaciones de calidad

Se incorporaron pruebas adicionales de dbt para verificar:

- Consistencia de las features.
- Ausencia de dependencias incorrectas entre capas.
- Prevención de fuga de información.
- Conciliación entre Silver y Gold.
- Consistencia de los registros en cuarentena.
- Detección de zonas sin servicio.

### Pruebas incorporadas

```text
tests/
├── cobertura_sin_servicio_detectada.sql
├── conciliacion_silver_gold.sql
├── cuarentena_cuadra_con_staging.sql
├── features_consistencia.sql
├── features_no_lee_gold.sql
├── features_sin_fuga_de_informacion.sql
└── gold_no_lee_bronze_ni_staging.sql
```

### Validaciones ejecutadas

Los cuatro modelos actualizados se construyeron correctamente:

```text
dim_usuario_conformado
features_usuario_movilidad
rpt_cobertura_zona
rpt_demanda_red
```

También se ejecutaron pruebas seleccionadas de Fase 02.

```text
PASS=32
WARN=0
ERROR=0
```

Las 32 pruebas seleccionadas finalizaron correctamente.

---

## 5. Visualización en Tableau

Se desarrolló un libro de Tableau para presentar los resultados de la Red Metropolitana.

### Dashboard: Red Metropolitana

Incluye visualizaciones de:

- Abordajes por modo.
- Demanda por zona.
- Demanda por hora.
- Usuarios multimodales.
- Viajes por estación de MetroRiel.
- Cobertura por zona.

### Dashboard: Cobertura y Caso MetroRiel

Permite analizar:

- Cobertura territorial.
- Demanda por zona.
- Relación entre demanda y disponibilidad de transporte.
- Zonas de interés para la planificación de MetroRiel.

### Archivo principal

`docs/evidencias/Proyecto 01 - Fase 02.twb`

---

## 6. Documentación técnica

Se incorporaron documentos específicos para respaldar los resultados de Fase 02.

| Documento | Contenido |
|---|---|
| `diccionario_datos.md` | Definición de campos y estructuras |
| `features.md` | Características analíticas |
| `gobernanza.md` | Reglas y responsabilidades de datos |
| `metricas_fase2.md` | Indicadores de Fase 02 |
| `recomendacion.md` | Recomendaciones basadas en resultados |
| `seguridad.md` | Controles de seguridad |
| `tablero.md` | Documentación de Tableau |

---

# ⚙️ Configuración y ejecución

## 1. Crear el entorno virtual

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

## 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con las credenciales correspondientes.

**Importante:** no subir `.env` a GitHub.

### Variables de entorno

| Variable | Descripción |
|---|---|
| `POSTGRES_HOST` | Dirección del servidor PostgreSQL. |
| `POSTGRES_PORT` | Puerto de PostgreSQL, normalmente `5432`. |
| `POSTGRES_DB` | Nombre de la base de datos. |
| `POSTGRES_USER` | Usuario de conexión a PostgreSQL. |
| `POSTGRES_PASSWORD` | Contraseña de conexión a PostgreSQL. |
| `USUARIO_SALT` | Clave secreta obligatoria utilizada para generar identificadores mediante HMAC-SHA256. |

Para generar una clave privada:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Agregar la clave generada al archivo `.env` y mantenerla fuera del repositorio.

El modelo `silver.dim_usuario_conformado` rechaza la ejecución si `USUARIO_SALT` está ausente o vacía.

Cambiar esta clave modifica los identificadores seudonimizados y requiere reconstruir los modelos dependientes.

## Generación de datos de prueba

El proyecto incluye el script `generar_red_metropolitana.py`, que permite generar los datos utilizados en la simulación de la Red Metropolitana de Transporte.

Desde la carpeta raíz del proyecto, ejecutar:

```bash
python generar_red_metropolitana.py
```

Los datos generados sirven como entrada para los procesos de ingesta Batch, Streaming y CDC, según la estructura implementada en el proyecto.

**Importante:** este procedimiento debe ejecutarse antes de realizar la ingesta inicial cuando todavía no se dispone de los datos de origen.

La generación de datos no sustituye los procesos de ingesta, transformación y validación del pipeline.

## 4. Levantar los servicios

```bash
docker compose up -d
docker compose ps
```

## 5. Verificar la conexión de dbt

```bash
dbt debug \
  --project-dir dbt_red_metropolitana \
  --profiles-dir dbt_red_metropolitana
```

## 6. Ejecutar las transformaciones

```bash
dbt build \
  --project-dir dbt_red_metropolitana \
  --profiles-dir dbt_red_metropolitana
```

**Nota:** este comando ejecuta transformaciones y pruebas sobre la base de datos configurada. Debe utilizarse únicamente cuando el entorno esté preparado.

## 7. Ejecutar las pruebas de Fase 02

```bash
dbt test \
  --project-dir dbt_red_metropolitana \
  --profiles-dir dbt_red_metropolitana \
  --select features_usuario_movilidad rpt_cobertura_zona rpt_demanda_red
```

## 8. Ejecutar la orquestación

```bash
python orchestration/flow_red_metropolitana.py
```

La ejecución completa del flujo puede realizar ingestas y modificar datos en PostgreSQL.

---

# 🔐 Seguridad

El proyecto incorpora las siguientes prácticas:

- Administración de credenciales mediante variables de entorno.
- Exclusión de `.env` del repositorio.
- Uso de llaves sustitutas en dimensiones.
- Separación de capas y responsabilidades.
- Validaciones automatizadas de calidad.
- Documentación de controles y reglas de gobernanza.

---

# 📊 Resultados generales

| Componente | Fase 01 | Fase 02 |
|---|---|---|
| Ingesta Batch | Implementado | Reutilizado |
| Streaming con Kafka | Implementado | Reutilizado |
| CDC | Implementado | Reutilizado |
| Bronze | Implementado | Reutilizado |
| Staging | Implementado | Reutilizado |
| Silver | Implementado | Ampliado |
| Gold | Modelo dimensional | Reportes analíticos |
| Features | — | Implementado |
| Pruebas dbt | Implementadas | Ampliadas |
| Prefect | Implementado | Flujo actualizado |
| Tableau | — | Dashboards desarrollados |
| Documentación | Fase 01 | Fase 02 |

---

# 📚 Evidencias

Los principales entregables se encuentran en:

```text
docs/evidencias/
├── Proyecto 01 - Fase 01.pdf
├── Proyecto 01 - Fase 02.pdf
└── Proyecto 01 - Fase 02.twb
```

La documentación técnica adicional se encuentra en la carpeta `docs/`.

---

# 👩‍💻 Integrantes

Proyecto académico desarrollado por:

- 💜 Rochelle Esquivel
- 🩷 Susana García
- 💙 Harriett Guzmán

**Universidad Rafael Landívar — Ciencia de Datos**