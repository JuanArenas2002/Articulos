import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, async_engine
from app.routes import articulos
from app.routes import grupos

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.warning("Database initialization skipped: %s", e)
    yield
    await async_engine.dispose()
    logger.info("Database connections closed")


CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

_description = """
## Repositorio Bibliográfico Institucional

API de **solo lectura** para consultar el repositorio de publicaciones científicas
del proceso de reconciliación bibliográfica institucional.

---

### ¿Qué puedo consultar?

| Sección | Descripción |
|---------|-------------|
| **Publicaciones** | Búsqueda, filtros por año / journal / tipo / idioma / estado |
| **Autores** | Búsqueda por nombre, ORCID, cédula o estado de verificación |
| **Relaciones** | Vínculos entre publicaciones y autores con posición y rol |
| **Grupos** | Publicaciones de grupos Minciencias cruzadas con metadatos canónicos |

---

### Formatos de respuesta

- Endpoints de **lista** → schema **resumido** (campos clave)
- Endpoints de **detalle** (por ID o identificador único) → schema **completo**

### Paginación

Los endpoints de lista aceptan `skip` (default `0`) y `limit` (default `10`, máx `100`).

### Estados de publicación

| Valor | Significado |
|-------|-------------|
| `Avalado` | Publicación validada y aceptada |
| `Revisión` | Pendiente de revisión editorial |
| `Rechazado` | Descartada del repositorio |

### Identificadores soportados

`DOI` · `PMID` · `PMCID` — usa `/publications/by-identifier?doi=...` para evitar
problemas de URL-encoding con DOIs que contienen barras.
"""

_tags = [
    {
        "name": "Publicaciones",
        "description": (
            "Consulta y filtrado de publicaciones científicas canónicas. "
            "Incluye búsqueda por texto libre, filtros por año / journal / tipo / idioma / estado "
            "y búsqueda exacta por DOI, PMID o PMCID."
        ),
    },
    {
        "name": "Autores",
        "description": (
            "Consulta de autores con soporte para búsqueda por nombre, "
            "filtro por ORCID, cédula, estado de verificación y afiliación institucional."
        ),
    },
    {
        "name": "Relaciones",
        "description": (
            "Vínculos many-to-many entre publicaciones y autores. "
            "Permite obtener todos los autores de una publicación o todas las publicaciones de un autor."
        ),
    },
    {
        "name": "Grupos",
        "description": (
            "Publicaciones clasificadas por Minciencias cruzadas con metadatos canónicos. "
            "Permite consultar todas las publicaciones de un grupo o todos los grupos "
            "que clasifican una publicación específica."
        ),
    },
    {
        "name": "Sistema",
        "description": "Endpoints de infraestructura: raíz y health check.",
    },
]

app = FastAPI(
    title="API de Publicaciones Científicas",
    description=_description,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=_tags,
    contact={"name": "Repositorio Bibliográfico Institucional"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articulos.router)
app.include_router(grupos.router)


@app.get("/", tags=["Sistema"], summary="Raíz de la API")
def root():
    """Punto de entrada. Retorna enlaces a la documentación interactiva."""
    return {
        "mensaje": "Bienvenido a la API de Publicaciones Científicas",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Sistema"], summary="Health check")
def health_check():
    """Verifica que el servidor está activo. Útil para monitoreo y load balancers."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
