"""Load seed JSON into the database (idempotent)."""

from app.db import SessionLocal, init_db
from app.services.catalog import seed_catalog


def main() -> None:
    init_db()
    with SessionLocal() as session:
        seed_catalog(session)
    print("Seed OK")


if __name__ == "__main__":
    main()
