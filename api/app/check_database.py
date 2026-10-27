"""Sanitized, read-only database connectivity check."""

from __future__ import annotations

import sys
from typing import TextIO

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError


def check_database_connection(engine: Engine, output: TextIO = sys.stdout) -> bool:
    """Run SELECT 1 and report success or a sanitized diagnostic."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        original = getattr(error, "orig", error)
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        code_detail = f", SQLSTATE {sqlstate}" if sqlstate else ""
        print(
            f"Database connection failed ({type(error).__name__}{code_detail}). "
            "Check DATABASE_URL, network access, and database availability.",
            file=output,
        )
        return False

    print("Database connection successful (SELECT 1).", file=output)
    return True


def main() -> int:
    # Import lazily so URL/driver construction failures can also be reported safely.
    try:
        from app.database import engine

        return 0 if check_database_connection(engine) else 1
    except SQLAlchemyError as error:
        original = getattr(error, "orig", error)
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        code_detail = f", SQLSTATE {sqlstate}" if sqlstate else ""
        print(
            f"Database connection check could not start ({type(error).__name__}{code_detail}). "
            "Check DATABASE_URL and the configured database driver."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
