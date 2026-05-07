"""
Script para debuggear DOIs disponibles en la base de datos
"""

from app.database import SessionLocal
from app.models import CanonicalPublication

def debug_dois():
    """Muestra todos los DOIs disponibles en la BD"""
    db = SessionLocal()
    
    print("\n" + "="*80)
    print("DOIs DISPONIBLES EN LA BASE DE DATOS")
    print("="*80 + "\n")
    
    try:
        publicaciones = db.query(CanonicalPublication).filter(
            CanonicalPublication.doi.isnot(None)
        ).all()
        
        print(f"Total de publicaciones con DOI: {len(publicaciones)}\n")
        
        for pub in publicaciones[:20]:  # Mostrar primeras 20
            print(f"ID: {pub.id}")
            print(f"  DOI: {pub.doi}")
            print(f"  Título: {pub.title[:60]}...")
            print(f"  Año: {pub.publication_year}")
            print()
        
        if len(publicaciones) > 20:
            print(f"... y {len(publicaciones) - 20} más\n")
        
    finally:
        db.close()

    print("="*80)
    print("\nAhora prueba estos endpoints en /docs:\n")
    
    if publicaciones:
        doi_example = publicaciones[0].doi
        print(f"GET /publications/by-doi/{doi_example}")
        print(f"GET /publications/{publicaciones[0].id}")
        print(f"GET /publications/search?q={publicaciones[0].title.split()[0]}")


if __name__ == "__main__":
    debug_dois()
