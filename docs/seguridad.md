# Seguridad y manejo de datos personales

Los datos son generados, pero el escenario no: un sistema de transporte sabe dónde
estuvo cada persona, a qué hora y todos los días. Estas son las cuatro decisiones
del proyecto (sección 3.3).

## 1. Nada de credenciales en el repositorio

- Las credenciales de PostgreSQL y la sal de seudonimización se leen de variables
  de entorno (`.env`), cargadas por `python-dotenv` en los scripts y por
  `env_var()` en `profiles.yml` de dbt.
- `.env` está en `.gitignore`; el repositorio solo trae `.env.example` con
  valores de ejemplo (`tu_usuario`, `tu_contrasena`, `cambie_este_valor...`).
- **Por qué:** quien clona el repositorio no obtiene acceso a la base de datos, y
  cada integrante puede usar credenciales propias.

## 2. Seudonimizar la llave del usuario antes de Gold

- Las tarjetas originales (`TC-00012345`, `0000012345`, `MR0012345`, hash de
  Aerómetro) **solo existen en Bronze, Staging y Silver**.
- En `silver.dim_usuario_conformado` se calcula
  `usuario_sk = md5(USUARIO_SALT || llave_normalizada)`. Gold, el tablero y la
  tabla de features solo ven `usuario_sk`.
- La sal es secreta y vive en `.env`. Sin ella, un md5 de un número de 10 dígitos
  se podría revertir probando todos los valores posibles; con ella, conocer la
  tarjeta no permite encontrar su fila en Gold.
- El tablero no necesita saber *qué tarjeta* es, solo que dos abordajes son de
  *la misma persona* (para contar usuarios y multimodalidad), y eso se conserva.
- Límite declarado: es seudonimización, no anonimización. Quien tenga la sal y
  acceso a Silver puede volver a enlazar; por eso Silver tiene acceso restringido.

## 3. Quién debe ver qué

| Rol | Esquemas | Qué ve | Por qué |
|---|---|---|---|
| Analista / tablero de la Agencia | `gold` (solo lectura) | Agregados y `usuario_sk` | Responde demanda, cobertura y transbordo sin conocer personas |
| Científico de datos | `features` (solo lectura) | Una fila por `usuario_sk`, sin tarjeta | Entrenar modelos no requiere identidad real |
| Ingeniero de datos | `staging`, `silver`, `quarantine`, `gold` | Detalle con llaves originales | Opera el pipeline y corrige calidad |
| Auditor de fraude / atención al usuario | `silver` (acceso puntual, con registro) | Detalle individual por tarjeta | Investigar un caso concreto lo justifica |
| Operadores (Transmetro, etc.) | Solo `gold`, filtrado a su modo | Sus propios indicadores | Comparten el warehouse sin ver los usuarios de los demás |

Implementación sugerida en PostgreSQL:

```sql
CREATE ROLE analista NOLOGIN;
GRANT USAGE ON SCHEMA gold TO analista;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO analista;
REVOKE ALL ON SCHEMA staging, silver, quarantine FROM analista;
```

## 4. Retención

- **Detalle individual** (Bronze, Silver y cuarentena con llave original):
  **12 meses**. Cubre un ciclo anual completo de demanda (temporada escolar,
  lluvias, fin de año) para planificación y permite resolver reclamos y
  auditorías del año en curso.
- **Después de 12 meses:** se eliminan las llaves originales y se conservan solo
  agregados (Gold) y `usuario_sk`, suficientes para series históricas de demanda.
- **Cuarentena:** mismo plazo que el detalle, porque contiene llaves originales.
