import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def get_database_url():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://postgres:123@localhost/shop"

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    return database_url


_engine = None
_session_local = None


def get_engine():
    global _engine
    if _engine is None:
        database_url = get_database_url()
        _engine = create_engine(database_url)
    return _engine


def get_session_local():
    global _session_local
    if _session_local is None:
        engine = get_engine()
        _session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _session_local


Base = declarative_base()


def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()

engine = None
SessionLocal = None