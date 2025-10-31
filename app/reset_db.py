import sys
import os
from sqlalchemy import text

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to the Python path (as in your original code)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Asumo que estos son correctos, ajusta según tu proyecto
from app.core.database import SessionLocal, Base
from app import models  # 👈 Crucial para cargar la metadata


def drop_all_tables():
    """
    Elimina TODAS las tablas definidas en Base.metadata de la base de datos.
    Esta es la forma canónica de SQLAlchemy para eliminar la estructura.
    """
    engine = SessionLocal().bind  # Obtener el objeto Engine desde la SessionLocal

    # ⚠️ OPCIÓN 1: Usar la función DROP_ALL de SQLAlchemy (Recomendado y más simple)
    # SQLAlchemy ya sabe cómo generar los comandos DROP TABLE con la dependencia correcta.

    print("🔥 Eliminando TODAS las tablas definidas en el metadata de SQLAlchemy...")

    try:
        # Usa el método drop_all() de la metadata de Base
        Base.metadata.drop_all(bind=engine)
        print("✅ Todas las tablas han sido eliminadas correctamente.")

    except Exception as e:
        print(f"❌ Error al eliminar las tablas: {e}")
        # La función drop_all suele manejar las transacciones, pero es bueno reportar errores.

    # OPCIÓN 2 (Alternativa si la opción 1 no funcionara, usando comandos SQL crudos):
    # if dialect == "postgresql":
    #     for table in reversed(Base.metadata.sorted_tables):
    #         print(f"💣 Eliminando tabla: {table.name}")
    #         db.execute(text(f'DROP TABLE IF EXISTS "{table.name}" CASCADE;'))
    #     db.commit()


# --- Tu función principal ---
if __name__ == "__main__":
    drop_all_tables()

    # Una vez que ejecutes esto, tu base de datos estará vacía.
    print("\n¡Base de datos vacía!")
    print("Sigue con el proceso de migración de Alembic:")
    print("1. alembic stamp head (Sella el historial)")
    print("2. alembic upgrade head (Crea todas las tablas)")
