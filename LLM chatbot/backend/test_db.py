import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))

        print("Connected to PostgreSQL successfully!")
        print(result.scalar())

except Exception as error:
    print("Database connection failed:")
    print(type(error).__name__, error)

finally:
    engine.dispose()