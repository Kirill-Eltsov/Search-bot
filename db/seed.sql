-- Seed sample data based on provided examples

-- Clean
TRUNCATE TABLE products RESTART IDENTITY CASCADE;
TRUNCATE TABLE users RESTART IDENTITY CASCADE;

-- Moscow (синхронные)
INSERT INTO products (name, article, category, warehouse, quantity_free, quantity_mm, price_per_unit, price_per_mm, width, length, profile, analogues, data_source)
VALUES
  ('800 8M CFNR', '8008M', 'synchronous', 'Москва', 1252, NULL, 15.25, NULL, NULL, 800, '8M', ARRAY['8008M'], 'Склад ремни Москва'),
  ('800 8M Contitech', '8008M', 'synchronous', 'Москва', 1855, NULL, 55.80, NULL, NULL, 800, '8M', ARRAY['8008M'], 'Склад ремни Москва'),
  ('800 8M CXP Contitech', '8008M', 'synchronous', 'Москва', 1345, NULL, 78.90, NULL, NULL, 800, '8M', ARRAY['8008M'], 'Склад ремни Москва'),
  ('800 RPP8 SLV Megadyne', '8008M', 'synchronous', 'Москва', 780, NULL, 69.72, NULL, NULL, 800, '8M', ARRAY['8008M'], 'Склад ремни Москва'),
  ('1778 14M 55 CFNR', '177814M=55', 'synchronous', 'Москва', 5, NULL, 2854, NULL, 55, 1778, '14M', ARRAY['177814M=55'], 'Склад ремни Москва'),
  ('1778 14M 55 Contitech', '177814M=55', 'synchronous', 'Москва', 12, NULL, 6852, NULL, 55, 1778, '14M', ARRAY['177814M=55'], 'Склад ремни Москва'),
  ('1778 14M 55 CXP Contitech', '177814M=55', 'synchronous', 'Москва', 9, NULL, 9854, NULL, 55, 1778, '14M', ARRAY['177814M=55'], 'Склад ремни Москва'),
  ('1778 RPPM 55 Megadyne', '177814M=55', 'synchronous', 'Москва', 19, NULL, 7852, NULL, 55, 1778, '14M', ARRAY['177814M=55'], 'Склад ремни Москва');

-- Strunino (клиновые и исключения 3V/5V/8V/3VX/5VX)
INSERT INTO products (name, article, category, warehouse, quantity_free, quantity_mm, price_per_unit, price_per_mm, width, length, profile, analogues, data_source)
VALUES
  ('SPA 2000 FNR Belt', 'SPA2000', 'vbelt', 'Струнино', 58, NULL, 285, NULL, NULL, 2000, 'SPA', ARRAY['SPA2000'], 'Склад ремни Струнино'),
  ('SPA 2000 PIX Muscle XS3', 'SPA2000', 'vbelt', 'Струнино', 58, NULL, 985, NULL, NULL, 2000, 'SPA', ARRAY['SPA2000'], 'Склад ремни Струнино'),
  ('SPA 2000 PIX Xset', 'SPA2000', 'vbelt', 'Струнино', 25, NULL, 410, NULL, NULL, 2000, 'SPA', ARRAY['SPA2000'], 'Склад ремни Струнино'),
  ('SPA 2000 Megadyne Extra', 'SPA2000', 'vbelt', 'Струнино', 30, NULL, 640, NULL, NULL, 2000, 'SPA', ARRAY['SPA2000'], 'Склад ремни Струнино'),
  ('SPA 1982 FNR Belt', 'SPA1982', 'vbelt', 'Струнино', 32, NULL, 279, NULL, NULL, 1982, 'SPA', ARRAY['SPA2000'], 'Склад ремни Струнино'),
  ('B85 17,0X 2160 Li / 2205 Ld Contitech', 'B85', 'vbelt', 'Струнино', 54, NULL, 1180, NULL, NULL, 2160, 'B', ARRAY['B85'], 'Склад ремни Струнино'),
  ('B 85 2159 Li / 2204 Lw PIX MUSCLE XS3', 'B85', 'vbelt', 'Струнино', 23, NULL, 1210, NULL, NULL, 2159, 'B', ARRAY['B85'], 'Склад ремни Струнино'),
  ('B 85 2159 Li / 2205 Ld FNRbelt (SR)', 'B85', 'vbelt', 'Струнино', 15, NULL, 480, NULL, NULL, 2159, 'B', ARRAY['B85'], 'Склад ремни Струнино'),
  ('3V 1000 PIX', '3V1000', 'vbelt', 'Струнино', 40, NULL, 300, NULL, NULL, 1000, '3V', ARRAY['3V1000'], 'Склад ремни Струнино'),
  ('5V 2000 PIX', '5V2000', 'vbelt', 'Струнино', 20, NULL, 600, NULL, NULL, 2000, '5V', ARRAY['5V2000'], 'Склад ремни Струнино'),
  ('8V 2000 PIX', '8V2000', 'vbelt', 'Струнино', 10, NULL, 1200, NULL, NULL, 2000, '8V', ARRAY['8V2000'], 'Склад ремни Струнино'),
  ('3VX 1000 PIX', '3VX1000', 'vbelt', 'Струнино', 25, NULL, 350, NULL, NULL, 1000, '3VX', ARRAY['3VX1000'], 'Склад ремни Струнино'),
  ('5VX 2000 PIX', '5VX2000', 'vbelt', 'Струнино', 12, NULL, 700, NULL, NULL, 2000, '5VX', ARRAY['5VX2000'], 'Склад ремни Струнино');

-- Example user seed
INSERT INTO users (telegram_id, phone_number, is_verified, verification_date)
VALUES
  (1234567890, '+79991234567', TRUE, CURRENT_TIMESTAMP)
ON CONFLICT (telegram_id) DO NOTHING;

