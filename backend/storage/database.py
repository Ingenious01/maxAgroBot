from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from backend.config import (
    DB_SERVER,
    DB_PORT,
    DB_NAME,
    DB_DRIVER,
    DB_TRUSTED_CONNECTION,
    DB_USER,
    DB_PASSWORD,
)


def build_database_url() -> URL:
    query = {
        "driver": DB_DRIVER,
        "TrustServerCertificate": "yes",
    }

    if DB_TRUSTED_CONNECTION:
        query["trusted_connection"] = "yes"

        return URL.create(
            "mssql+pyodbc",
            host=DB_SERVER,
            port=DB_PORT,
            database=DB_NAME,
            query=query,
        )

    return URL.create(
        "mssql+pyodbc",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_SERVER,
        port=DB_PORT,
        database=DB_NAME,
        query=query,
    )


DATABASE_URL = build_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def test_connection() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(f"SQL Server подключен: {result.scalar()}")