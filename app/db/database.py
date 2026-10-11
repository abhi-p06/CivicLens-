import os
from pathlib import Path
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from app.config import settings

class Base(DeclarativeBase):
    pass

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Enforce WAL mode and foreign key constraints for SQLite connections.
    WAL mode prevents write-locks from blocking concurrent readers.
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
    finally:
        cursor.close()

def build_engine(db_path: Optional[Path] = None) -> Engine:
    target_path = db_path or settings.resolved_db_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{target_path}",
        connect_args={"check_same_thread": False, "timeout": 30.0},
        echo=False
    )
    return engine

# Global primary engine and sessionmaker
engine = build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session_factory(custom_engine: Optional[Engine] = None):
    if custom_engine:
        return sessionmaker(autocommit=False, autoflush=False, bind=custom_engine)
    return SessionLocal

@contextmanager
def get_db_session(session_factory=None) -> Generator[Session, None, None]:
    """
    Centralized transactional context manager.
    Commits on clean exit, rolls back on exception, always closes.
    """
    factory = session_factory or SessionLocal
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db(target_engine: Optional[Engine] = None) -> None:
    """
    Creates all database tables if they do not already exist.
    Safe to execute multiple times (idempotent).
    """
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)

def rebind_database(target_path: Path) -> Engine:
    """
    Rebinds global engine and SessionLocal to a new database path.
    Essential for running tests in an isolated temporary database.
    """
    global engine, SessionLocal
    engine = build_engine(target_path)
    SessionLocal.configure(bind=engine)
    return engine

