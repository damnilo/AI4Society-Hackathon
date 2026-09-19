from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models import Base


connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _sqlite_fk(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db() -> None:
    Base.metadata.create_all(engine)
    _ensure_procedure_place_scope()


def _ensure_procedure_place_scope() -> None:
    """Add place_scope to existing SQLite DBs created before the column existed."""
    inspector = inspect(engine)
    if "procedures" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("procedures")}
    if "place_scope" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE procedures ADD COLUMN place_scope JSON"))
        conn.execute(text("UPDATE procedures SET place_scope = '[]' WHERE place_scope IS NULL"))


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
