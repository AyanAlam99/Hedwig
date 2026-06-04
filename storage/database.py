import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker


DB_PATH = Path(os.getenv("HEDWIG_DB_PATH", "data/hedwig.db"))
DATABASE_URL = os.getenv("HEDWIG_DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    future=True,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)

Base = declarative_base()


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    from storage import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
