import sys
import os
from sqlalchemy import text

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.database import SessionLocal, Base
from app import models  # 👈 IMPORTANTE: importa tus modelos

def reset_tables():
    """
    Cleans all tables in the database.
    Works with PostgreSQL (TRUNCATE + RESTART IDENTITY).
    """
    db = SessionLocal()
    dialect = db.bind.dialect.name
    print(f"ℹ️ Detected database dialect: {dialect}")

    try:
        if dialect == "postgresql":
            print("🔥 Using TRUNCATE method for PostgreSQL...")

            # Temporarily disable foreign key checks
            db.execute(text("SET session_replication_role = 'replica';"))

            tables = list(Base.metadata.sorted_tables)
            if not tables:
                print("⚠️ No tables found in Base.metadata. Did you import your models?")
                return

            for table in tables:
                print(f"🧹 Cleaning table: {table.name}")
                db.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'))

            db.execute(text("SET session_replication_role = 'origin';"))
            db.commit()
            print("✅ Database cleaned successfully.")

        else:
            print("⚠️ Unsupported dialect for reset. Add logic for SQLite/MySQL if needed.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during database reset: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_tables()

