# Тестовая БД (PostgreSQL 15)

## Быстрый старт

1) Создайте БД (при необходимости):
```bash
psql -U postgres -h localhost -c "CREATE DATABASE beltimpex WITH ENCODING 'UTF8';"
```

2) Примените схему:
```bash
psql -U postgres -h localhost -d beltimpex -f db/schema.sql
```

3) Загрузите тестовые данные:
```bash
psql -U postgres -h localhost -d beltimpex -f db/seed.sql
```

## Замечания
- Поля `updated_at` обновляются триггерами при UPDATE.
- Поля `analogues` в `products` — массив строк (TEXT[]).
- Поле `data_source`: 'Склад ремни Струнино' или 'Склад ремни Москва'.

