-- DDL LÓGICO DE LA CAPA GOLD
-- PROYECTO RED METROPOLITANA - FASE 01

-- 1. CREACIÓN DEL ESQUEMA GOLD
CREATE SCHEMA IF NOT EXISTS gold;

-- 2. DIMENSIÓN FECHA
CREATE TABLE IF NOT EXISTS gold.dim_fecha (
    fecha_sk INTEGER PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    dia INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL,
    es_dia_habil BOOLEAN NOT NULL,
    es_fin_semana BOOLEAN NOT NULL
);

-- 3. DIMENSIÓN HORA
CREATE TABLE IF NOT EXISTS gold.dim_hora (
    hora_sk INTEGER PRIMARY KEY,
    hora INTEGER NOT NULL UNIQUE,
    franja_horaria TEXT NOT NULL,
    es_hora_pico BOOLEAN NOT NULL
);

-- 4. DIMENSIÓN MODO DE TRANSPORTE
CREATE TABLE IF NOT EXISTS gold.dim_modo (
    modo_sk INTEGER PRIMARY KEY,
    modo_nombre TEXT NOT NULL UNIQUE
);

-- 5. DIMENSIÓN USUARIO CONFORMADO
CREATE TABLE IF NOT EXISTS gold.dim_usuario (
    usuario_sk VARCHAR(32) PRIMARY KEY,
    perfil TEXT,
    zona_residencia TEXT,
    activo_en_transmetro BOOLEAN NOT NULL,
    modos_identificados TEXT NOT NULL,
    cantidad_modos_identificados BIGINT NOT NULL
);

-- 6. DIMENSIÓN ZONA CONFORMADA
CREATE TABLE IF NOT EXISTS gold.dim_zona (
    zona_sk VARCHAR(32) PRIMARY KEY,
    zona_nombre TEXT NOT NULL UNIQUE
);

-- 7. TABLA DE HECHOS DE ABORDAJES
-- Grano: una fila por evento de abordaje válido.
CREATE TABLE IF NOT EXISTS gold.fct_abordajes (
    -- Aquí permanece todo el contenido que ya tienes.
);

-- 8. TABLA DE HECHOS DE VIAJES DE METRORIEL
-- Grano: una fila por viaje completo válido de MetroRiel.
CREATE TABLE IF NOT EXISTS gold.fct_viajes_metroriel (
    -- Aquí permanece todo el contenido que ya tienes.
);