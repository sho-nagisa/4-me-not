import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# prefer DATABASE_URL for compatibility with .env
DATABASE_URL = os.environ.get("DB_URL") or os.environ.get("DATABASE_URL")
print("DATABASE_URL =", DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    echo=True,          # SQL をログに出す（最初はON）
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
