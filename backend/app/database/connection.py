
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


# Safely construct the PostgreSQL connection URL.
# URL.create handles special characters in passwords.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)


# Create the database engine.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# Create a reusable database session factory.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for all SQLAlchemy database models.
class Base(DeclarativeBase):
    pass


# Database session dependency for FastAPI routes.
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
