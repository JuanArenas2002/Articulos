"""
Script de diagnóstico para source_records.
Corre: python debug_source_records.py
"""
from sqlalchemy import text
from app.database import SessionLocal

def debug():
    db = SessionLocal()
    try:
        # 1. Cuántos registros hay
        total = db.execute(text("SELECT COUNT(*) FROM source_records")).scalar()
        print(f"\nTotal filas en source_records: {total}")

        if total == 0:
            print("La tabla está vacía — no hay external records para ninguna publicación.")
            return

        # 2. Columnas reales de la tabla
        cols = db.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'source_records'
            ORDER BY ordinal_position
        """)).fetchall()
        print(f"\nColumnas reales de source_records:")
        for col in cols:
            print(f"  {col[0]:35} {col[1]}")

        # 3. Muestra 5 filas de ejemplo
        rows = db.execute(text("SELECT * FROM source_records LIMIT 5")).fetchall()
        print(f"\nEjemplos (primeras 5 filas):")
        for row in rows:
            print(f"  {dict(row._mapping)}")

        # 4. Qué publication IDs tienen registros
        linked = db.execute(text("""
            SELECT canonical_publication_id, COUNT(*) as n
            FROM source_records
            GROUP BY canonical_publication_id
            ORDER BY n DESC
            LIMIT 10
        """)).fetchall()
        print(f"\nTop 10 canonical_publication_id con más source records:")
        for row in linked:
            print(f"  pub_id={row[0]}  registros={row[1]}")

    finally:
        db.close()

if __name__ == "__main__":
    debug()
