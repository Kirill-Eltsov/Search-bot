-- PostgreSQL 15 schema for beltimpex test database

-- Optional: create database manually before running this file
-- CREATE DATABASE beltimpex WITH ENCODING 'UTF8';

-- Enable useful extensions (optional)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    article VARCHAR(100),
    category VARCHAR(100),
    warehouse VARCHAR(50),
    quantity_free INTEGER,
    quantity_mm INTEGER,
    price_per_unit DECIMAL(10,2),
    price_per_mm DECIMAL(10,2),
    width DECIMAL(8,2),
    length DECIMAL(8,2),
    profile VARCHAR(100),
    analogues TEXT[],
    data_source VARCHAR(50), -- 'Склад ремни Струнино' или 'Склад ремни Москва'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Triggers to auto-update updated_at
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_products_updated_at ON products;
CREATE TRIGGER trg_products_updated_at
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_products_article ON products(article);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_warehouse ON products(warehouse);
CREATE INDEX IF NOT EXISTS idx_products_profile ON products(profile);
CREATE INDEX IF NOT EXISTS idx_products_length ON products(length);
CREATE INDEX IF NOT EXISTS idx_products_width ON products(width);

