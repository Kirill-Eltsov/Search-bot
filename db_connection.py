import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    dsn = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN")
    if not dsn:
        # Фолбэк на локальные переменные окружения
        host = os.getenv("PGHOST", "localhost")
        port = os.getenv("PGPORT", "5432")
        dbname = os.getenv("PGDATABASE", "beltimpex")
        user = os.getenv("PGUSER", "postgres")
        password = os.getenv("PGPASSWORD", "postgres")
        dsn = f"dbname={dbname} user={user} password={password} host={host} port={port}"
    return psycopg2.connect(dsn, cursor_factory=RealDictCursor)


