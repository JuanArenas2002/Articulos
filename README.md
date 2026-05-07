# FastAPI - API de Publicaciones Científicas (READ-ONLY)

Proyecto FastAPI para **consultar** publicaciones científicas, autores y sus relaciones.

**⚠️ API de solo lectura** - No se pueden modificar, crear ni eliminar datos

Incluye 3 modelos: `canonical_publications`, `authors`, `publication_authors`

## Estructura del Proyecto

```
fastapi_db_project/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuración de la aplicación
│   ├── database.py         # Conexión a la base de datos
│   ├── models.py           # Modelos SQLAlchemy (3 tablas)
│   ├── schemas.py          # Esquemas Pydantic (solo lectura)
│   └── routes/
│       ├── __init__.py
│       └── articulos.py    # Rutas para publicaciones, autores (GET only)
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias
├── .env                    # Variables de entorno
└── README.md
```

## Instalación

### 1. Crear entorno virtual
```bash
cd fastapi_db_project
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar base de datos

El archivo `.env` ya contiene:
```
DATABASE_URL=postgresql://postgres:123456@localhost:5432/reconciliacion_bibliografica
```

Ajusta según tu configuración si es necesario.

## Ejecución

```bash
python main.py
```

O con uvicorn:
```bash
uvicorn main:app --reload
```

La API estará disponible en: **http://localhost:8000**

## Test de Conexión a Base de Datos

Antes de usar la API, verifica que la conexión a la BD funciona correctamente:

```bash
python test_database_connection.py
```

Este test verifica:
- ✓ Conexión a la base de datos
- ✓ Existencia de las 3 tablas (canonical_publications, authors, publication_authors)
- ✓ Cantidad de registros en cada tabla
- ✓ Información de columnas
- ✓ Claves primarias

## Documentación API

- Swagger UI: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

## Endpoints Disponibles (Solo Lectura)

### 📖 PUBLICACIONES

#### GET /publications
Obtiene lista de publicaciones (paginado)
```bash
GET http://localhost:8000/publications?skip=0&limit=10
```

#### GET /publications/search
Busca publicaciones por título, abstract o palabras clave
```bash
GET http://localhost:8000/publications/search?q=COVID&skip=0&limit=10
```

#### GET /publications/{publication_id}
Obtiene una publicación específica por ID
```bash
GET http://localhost:8000/publications/1
```

#### GET /publications/by-identifier
Obtiene una publicación por identificador (DOI, PMID o PMCID).
**Mejor para DOIs con barras** - no necesita URL-encoding

```bash
# Por DOI (funciona con barras)
GET http://localhost:8000/publications/by-identifier?doi=10.1016/j.bodyim.2026.102032

# Por PMID
GET http://localhost:8000/publications/by-identifier?pmid=12345678

# Por PMCID
GET http://localhost:8000/publications/by-identifier?pmcid=PMC9876543
```

#### GET /publications/by-doi/{doi}
Obtiene una publicación por DOI (path parameter - requiere URL-encoding para barras)
```bash
GET http://localhost:8000/publications/by-doi/10.1234%2Fexample
```

#### GET /publications/by-pmid/{pmid}
Obtiene una publicación por PMID
```bash
GET http://localhost:8000/publications/by-pmid/12345678
```

#### GET /publications/by-pmcid/{pmcid}
Obtiene una publicación por PMCID
```bash
GET http://localhost:8000/publications/by-pmcid/PMC9876543
```

#### GET /publications/by-year/{year}
Obtiene publicaciones por año
```bash
GET http://localhost:8000/publications/by-year/2023?skip=0&limit=10
```

#### GET /publications/by-journal/{journal_id}
Obtiene publicaciones por journal ID
```bash
GET http://localhost:8000/publications/by-journal/5?skip=0&limit=10
```

#### GET /publications/by-estado/{estado}
Obtiene publicaciones por estado (Avalado, Revisión, Rechazado)
```bash
GET http://localhost:8000/publications/by-estado/Avalado?skip=0&limit=10
```

#### GET /publications/by-type/{publication_type}
Obtiene publicaciones por tipo (article, conference, book, etc.)
```bash
GET http://localhost:8000/publications/by-type/article?skip=0&limit=10
```

#### GET /publications/by-language/{language}
Obtiene publicaciones por idioma
```bash
GET http://localhost:8000/publications/by-language/en?skip=0&limit=10
```

#### GET /publications/open-access
Obtiene publicaciones de acceso abierto
```bash
GET http://localhost:8000/publications/open-access?skip=0&limit=10
```

#### GET /publications/institutional
Obtiene publicaciones institucionales
```bash
GET http://localhost:8000/publications/institutional?skip=0&limit=10
```

#### GET /publications/top-cited
Obtiene las publicaciones más citadas
```bash
GET http://localhost:8000/publications/top-cited?limit=10
```

---

### 👤 AUTORES

#### GET /authors
Obtiene lista de autores (paginado)
```bash
GET http://localhost:8000/authors?skip=0&limit=10
```

#### GET /authors/search
Busca autores por nombre o nombre normalizado
```bash
GET http://localhost:8000/authors/search?q=Juan&skip=0&limit=10
```

#### GET /authors/{author_id}
Obtiene un autor específico por ID
```bash
GET http://localhost:8000/authors/1
```

#### GET /authors/by-orcid/{orcid}
Obtiene un autor por ORCID
```bash
GET http://localhost:8000/authors/by-orcid/0000-0001-2345-6789
```

#### GET /authors/by-cedula/{cedula}
Obtiene un autor por cédula
```bash
GET http://localhost:8000/authors/by-cedula/12345678
```

#### GET /authors/institutional
Obtiene autores institucionales
```bash
GET http://localhost:8000/authors/institutional?skip=0&limit=10
```

#### GET /authors/non-institutional
Obtiene autores no institucionales
```bash
GET http://localhost:8000/authors/non-institutional?skip=0&limit=10
```

#### GET /authors/verified
Obtiene autores verificados (verification_status != auto_detected)
```bash
GET http://localhost:8000/authors/verified?skip=0&limit=10
```

#### GET /authors/with-orcid
Obtiene autores que tienen ORCID registrado
```bash
GET http://localhost:8000/authors/with-orcid?skip=0&limit=10
```

---

### 🔗 RELACIONES (Publication-Author)

#### GET /publication-authors
Obtiene todas las relaciones publicación-autor (paginado)
```bash
GET http://localhost:8000/publication-authors?skip=0&limit=10
```

#### GET /publication-authors/{relation_id}
Obtiene una relación específica por ID
```bash
GET http://localhost:8000/publication-authors/1
```

#### GET /publication-authors/by-publication/{publication_id}
Obtiene todos los autores de una publicación
```bash
GET http://localhost:8000/publication-authors/by-publication/1
```

#### GET /publication-authors/by-author/{author_id}
Obtiene todas las publicaciones de un autor
```bash
GET http://localhost:8000/publication-authors/by-author/1?skip=0&limit=10
```

---

## Modelos de Datos

### CanonicalPublication
- id, doi, pmid, pmcid
- title, normalized_title
- publication_year, publication_date
- publication_type, language
- journal_id, source_journal, issn
- is_open_access, oa_status
- citation_count, institutional_authors_count
- abstract, keywords
- Y más campos...

### Author
- id, name, normalized_name
- orcid, cedula
- is_institutional
- verification_status
- external_ids, field_provenance

### PublicationAuthor
- id, publication_id, author_id
- is_institutional, author_position, role
