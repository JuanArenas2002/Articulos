"""
Test de conexión a la base de datos
Verifica que la conexión funciona correctamente y que las tablas existen
"""

import sys
from sqlalchemy import inspect, text
from app.database import engine, SessionLocal
from app.models import CanonicalPublication, Author, PublicationAuthor

def test_connection():
    """Prueba la conexión básica a la base de datos"""
    print("\n" + "="*60)
    print("TEST DE CONEXIÓN A BASE DE DATOS")
    print("="*60 + "\n")
    
    try:
        # Prueba 1: Conexión básica
        print("✓ PRUEBA 1: Conectando a la base de datos...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"  ✓ Conexión exitosa: {result.scalar()}\n")
    except Exception as e:
        print(f"  ✗ Error de conexión: {e}\n")
        return False

    try:
        # Prueba 2: Verificar que las tablas existen
        print("✓ PRUEBA 2: Verificando tablas...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ["canonical_publications", "authors", "publication_authors"]
        
        for table in required_tables:
            if table in tables:
                print(f"  ✓ Tabla '{table}' encontrada")
            else:
                print(f"  ✗ Tabla '{table}' NO ENCONTRADA")
                return False
        print()
    except Exception as e:
        print(f"  ✗ Error al verificar tablas: {e}\n")
        return False

    try:
        # Prueba 3: Contar registros en cada tabla
        print("✓ PRUEBA 3: Contando registros en cada tabla...")
        db = SessionLocal()
        
        try:
            count_publications = db.query(CanonicalPublication).count()
            print(f"  • canonical_publications: {count_publications} registros")
            
            count_authors = db.query(Author).count()
            print(f"  • authors: {count_authors} registros")
            
            count_relations = db.query(PublicationAuthor).count()
            print(f"  • publication_authors: {count_relations} registros")
            print()
        finally:
            db.close()
    except Exception as e:
        print(f"  ✗ Error al contar registros: {e}\n")
        return False

    try:
        # Prueba 4: Obtener info de columnas
        print("✓ PRUEBA 4: Información de columnas...")
        inspector = inspect(engine)
        
        # Columnas de canonical_publications
        print("  canonical_publications:")
        columns = inspector.get_columns("canonical_publications")
        for col in columns[:5]:  # Mostrar primeras 5
            print(f"    - {col['name']}: {col['type']}")
        print(f"    ... ({len(columns)} columnas totales)\n")
        
        # Columnas de authors
        print("  authors:")
        columns = inspector.get_columns("authors")
        for col in columns[:5]:  # Mostrar primeras 5
            print(f"    - {col['name']}: {col['type']}")
        print(f"    ... ({len(columns)} columnas totales)\n")
        
        # Columnas de publication_authors
        print("  publication_authors:")
        columns = inspector.get_columns("publication_authors")
        for col in columns:
            print(f"    - {col['name']}: {col['type']}")
        print()
    except Exception as e:
        print(f"  ✗ Error al obtener info de columnas: {e}\n")
        return False

    try:
        # Prueba 5: Verificar claves primarias
        print("✓ PRUEBA 5: Verificando claves primarias...")
        inspector = inspect(engine)
        
        for table_name in ["canonical_publications", "authors", "publication_authors"]:
            pk = inspector.get_pk_constraint(table_name)
            print(f"  • {table_name}: {pk['constrained_columns']}")
        print()
    except Exception as e:
        print(f"  ✗ Error al verificar claves primarias: {e}\n")
        return False

    # Resumen final
    print("="*60)
    print("✓ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    print("="*60 + "\n")
    return True


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
