import logging
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, text

from app.config import REVISTA_SERVICE_URL
from app.database import get_async_db
from app.models import CanonicalPublication, Author, PublicationAuthor
from app.schemas import CanonicalPublicationDetail as PublicationSchema
from app.schemas import PublicationSummary
from app.schemas import AuthorDetail as AuthorDetailSchema
from app.schemas import AuthorSummary as AuthorSummarySchema
from app.schemas import PublicationAuthor as PublicationAuthorSchema
from app.schemas import SourceRecordSchema, AuthorInPublication, PublicationWithDetails, RevistaDetail, ClasificacionMincienciasSchema


logger = logging.getLogger(__name__)


async def _fetch_revista(issn: str, anio: Optional[int] = None) -> Optional[RevistaDetail]:
    params = {"anio": anio} if anio else {}
    url = f"{REVISTA_SERVICE_URL}/revistas/{issn}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            logger.info("Revista service %s → %s", url, resp.status_code)
            if resp.status_code == 200:
                return RevistaDetail(**resp.json())
            logger.warning("Revista service returned %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.error("Revista service error (%s): %s", url, exc)
    return None
router = APIRouter()

_EXTERNAL_RECORDS_SQL = text("""
    SELECT id, 'openalex' AS source_name, openalex_work_id AS source_id,
           doi, status, match_type,
           ROUND(match_score)::integer AS match_score,
           COALESCE(NULLIF(openalex_work_id, ''), NULLIF(url, '')) AS record_url
    FROM openalex_records
    WHERE canonical_publication_id = :pub_id AND status = 'matched'
    UNION ALL
    SELECT id, 'scopus', scopus_doc_id, doi, status, match_type,
           ROUND(match_score)::integer,
           COALESCE(
               NULLIF(scopus_link, ''),
               'https://www.scopus.com/pages/publications/' || scopus_doc_id || '?origin=resultslist'
           )
    FROM scopus_records
    WHERE canonical_publication_id = :pub_id AND status = 'matched'
    UNION ALL
    SELECT id, 'wos', wos_uid, doi, status, match_type,
           ROUND(match_score)::integer,
           COALESCE(
               NULLIF(url, ''),
               'https://www.webofscience.com/wos/woscc/full-record/' || wos_uid
           )
    FROM wos_records
    WHERE canonical_publication_id = :pub_id AND status = 'matched'
    UNION ALL
    SELECT id, 'cvlac', cvlac_code, doi, status, match_type,
           ROUND(match_score)::integer, NULLIF(url, '')
    FROM cvlac_records
    WHERE canonical_publication_id = :pub_id AND status = 'matched'
    UNION ALL
    SELECT id, 'datos_abiertos', datos_source_id, doi, status, match_type,
           ROUND(match_score)::integer, NULLIF(url, '')
    FROM datos_abiertos_records
    WHERE canonical_publication_id = :pub_id AND status = 'matched'
    UNION ALL
    SELECT id, 'gruplac', gruplac_product_id, doi, status, match_type,
           ROUND(match_score)::integer, NULLIF(url, '')
    FROM gruplac_records
    WHERE canonical_publication_id = :pub_id AND status = 'matched'
    UNION ALL
    SELECT id, 'google_scholar', google_scholar_id, doi, status,
           NULL AS match_type, NULL AS match_score,
           COALESCE(
               NULLIF(url, ''),
               'https://scholar.google.com/scholar?cluster=' || google_scholar_id
           )
    FROM google_scholar_records
    WHERE canonical_publication_id = :pub_id
""")


# ====================== PUBLICACIONES ======================

@router.get(
    "/publications",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Listar publicaciones",
    response_description="Lista paginada de publicaciones (schema resumido)",
)
async def obtener_publicaciones(
    skip: int = Query(0, ge=0, description="Registros a saltar (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados por página"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retorna todas las publicaciones del repositorio con **paginación**.

    Usa `skip` y `limit` para navegar entre páginas:
    - Página 1: `skip=0&limit=10`
    - Página 2: `skip=10&limit=10`

    La respuesta usa el schema **resumido** (sin abstract completo ni metadatos internos).
    Para el detalle completo usa `GET /publications/{id}`.
    """
    result = await db.execute(select(CanonicalPublication).offset(skip).limit(limit))
    return result.scalars().all()


@router.get(
    "/publications/search",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Buscar publicaciones por texto",
    response_description="Publicaciones que coinciden con el término de búsqueda",
)
async def buscar_publicaciones(
    q: str = Query(
        ...,
        min_length=1,
        description="Texto a buscar en título, abstract y palabras clave (case-insensitive), ej: `machine learning`",
    ),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Búsqueda **full-text** en los campos `title`, `abstract` y `keywords`.

    - La búsqueda es **case-insensitive** y busca coincidencias parciales (`LIKE %q%`).
    - Retorna publicaciones donde **al menos uno** de los tres campos coincide.
    - Para búsquedas exactas por identificador usa `GET /publications/by-identifier`.
    """
    pattern = f"%{q}%"
    result = await db.execute(
        select(CanonicalPublication)
        .filter(
            or_(
                CanonicalPublication.title.ilike(pattern),
                CanonicalPublication.abstract.ilike(pattern),
                CanonicalPublication.keywords.ilike(pattern),
            )
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def _build_with_details(pub: CanonicalPublication, db: AsyncSession) -> PublicationWithDetails:
    """Build enriched response: publication metadata + external source records + authors + revista info."""
    authors_result = await db.execute(
        select(PublicationAuthor, Author)
        .join(Author, PublicationAuthor.author_id == Author.id)
        .where(PublicationAuthor.publication_id == pub.id)
        .order_by(PublicationAuthor.author_position)
    )
    authors = [
        AuthorInPublication(
            author_id=pa.author_id,
            name=a.name,
            normalized_name=a.normalized_name,
            orcid=a.orcid,
            cedula=a.cedula,
            is_institutional=pa.is_institutional,
            verification_status=a.verification_status,
            author_position=pa.author_position,
            role=pa.role,
        )
        for pa, a in authors_result.all()
    ]
    ext_result = await db.execute(_EXTERNAL_RECORDS_SQL, {"pub_id": pub.id})
    external_records = [SourceRecordSchema(**dict(row._mapping)) for row in ext_result.all()]

    revista = None
    logger.info("Publication id=%s issn=%r publication_year=%r", pub.id, pub.issn, pub.publication_year)
    if pub.issn:
        revista = await _fetch_revista(pub.issn, anio=pub.publication_year)
    else:
        logger.warning("Publication id=%s has no ISSN — skipping revista lookup", pub.id)

    minciencias_result = await db.execute(
        text("""
            SELECT cod_grupo_gr, nme_grupo_gr, nme_clase_pd, nme_tipo_medicion_pd,
                   nme_tipologia_pd, nme_convocatoria, ano_convo, match_score, match_method
            FROM clasificacion_minciencias
            WHERE canonical_publication_id = :pub_id
            ORDER BY ano_convo DESC
        """),
        {"pub_id": pub.id},
    )
    clasificaciones = [ClasificacionMincienciasSchema(**dict(row._mapping)) for row in minciencias_result.all()]

    pub_data = PublicationSchema.model_validate(pub).model_dump(exclude={"external_links"})
    return PublicationWithDetails(
        **pub_data,
        external_records=external_records,
        authors=authors,
        revista=revista,
        clasificaciones_minciencias=clasificaciones,
    )


@router.get(
    "/publications/by-identifier",
    response_model=PublicationWithDetails,
    tags=["Publicaciones"],
    summary="Buscar por DOI, PMID o PMCID",
    response_description="Publicación con metadatos completos, registros externos y autores",
)
async def obtener_publicacion_por_identificador(
    doi: str = Query(None, description="DOI completo, ej: `10.1016/j.jmb.2023.168025`. No requiere URL-encoding."),
    pmid: str = Query(None, description="PubMed ID numérico, ej: `37852456`"),
    pmcid: str = Query(None, description="PubMed Central ID, ej: `PMC10612345`"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Obtiene el **detalle enriquecido** de una publicación por su identificador externo.
    Incluye registros de fuentes externas (`source_records`) y lista de autores.

    Proporciona **uno** de los tres parámetros:

    | Parámetro | Ejemplo |
    |-----------|---------|
    | `doi` | `10.1016/j.jmb.2023.168025` |
    | `pmid` | `37852456` |
    | `pmcid` | `PMC10612345` |

    > **Tip:** Usa este endpoint en vez de `by-doi/{doi}` cuando el DOI contiene barras `/`,
    > ya que los query params no requieren URL-encoding.

    Retorna `400` si no se proporciona ningún parámetro.
    Retorna `404` si el identificador no existe en el repositorio.
    """
    stmt_base = select(CanonicalPublication)

    if doi:
        result = await db.execute(stmt_base.where(CanonicalPublication.doi == doi))
        pub = result.scalar_one_or_none()
        if not pub:
            raise HTTPException(status_code=404, detail=f"Publicación con DOI '{doi}' no encontrada")
        return await _build_with_details(pub, db)

    if pmid:
        result = await db.execute(stmt_base.where(CanonicalPublication.pmid == pmid))
        pub = result.scalar_one_or_none()
        if not pub:
            raise HTTPException(status_code=404, detail=f"Publicación con PMID '{pmid}' no encontrada")
        return await _build_with_details(pub, db)

    if pmcid:
        result = await db.execute(stmt_base.where(CanonicalPublication.pmcid == pmcid))
        pub = result.scalar_one_or_none()
        if not pub:
            raise HTTPException(status_code=404, detail=f"Publicación con PMCID '{pmcid}' no encontrada")
        return await _build_with_details(pub, db)

    raise HTTPException(
        status_code=400,
        detail="Debes proporcionar al menos un identificador: doi, pmid o pmcid",
    )


@router.get(
    "/publications/top-cited",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Publicaciones más citadas",
    response_description="Lista ordenada por número de citas descendente",
)
async def obtener_publicaciones_mas_citadas(
    limit: int = Query(10, ge=1, le=100, description="Cantidad de publicaciones a retornar"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retorna las publicaciones con **mayor número de citas** en orden descendente.

    El campo `citation_count` agrega citas de todas las fuentes bibliográficas
    (Scopus, Web of Science, PubMed, etc.) registradas para cada publicación.
    """
    result = await db.execute(
        select(CanonicalPublication)
        .order_by(CanonicalPublication.citation_count.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/publications/open-access",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Publicaciones de acceso abierto",
    response_description="Publicaciones con is_open_access = true",
)
async def obtener_publicaciones_acceso_abierto(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Filtra publicaciones donde `is_open_access = true`.

    Para ver el tipo específico de acceso abierto (`gold`, `green`, `hybrid`, `bronze`)
    consulta el campo `oa_status` en el detalle de cada publicación.
    """
    result = await db.execute(
        select(CanonicalPublication)
        .where(CanonicalPublication.is_open_access == True)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/publications/institutional",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Publicaciones institucionales",
    response_description="Publicaciones con al menos un autor institucional",
)
async def obtener_publicaciones_institucionales(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retorna publicaciones donde `is_institutional = true`,
    es decir, con **al menos un autor** afiliado a la institución.

    Para ver exactamente qué autores son institucionales en cada publicación,
    usa `GET /publication-authors/by-publication/{id}`.
    """
    result = await db.execute(
        select(CanonicalPublication)
        .where(CanonicalPublication.is_institutional == True)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/publications/by-doi/{doi:path}",
    response_model=PublicationSchema,
    tags=["Publicaciones"],
    summary="Detalle por DOI (path param)",
    response_description="Publicación con todos sus metadatos",
)
async def obtener_publicacion_por_doi(doi: str, db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene el detalle completo de una publicación por su **DOI** como parámetro de ruta.

    El patrón `{doi:path}` permite DOIs con barras sin URL-encoding,
    ej: `/publications/by-doi/10.1016/j.jmb.2023.168025`

    > **Alternativa recomendada:** usa `GET /publications/by-identifier?doi=...`
    > que es más flexible y no requiere encoding.
    """
    result = await db.execute(select(CanonicalPublication).where(CanonicalPublication.doi == doi))
    pub = result.scalar_one_or_none()
    if not pub:
        raise HTTPException(status_code=404, detail=f"Publicación con DOI '{doi}' no encontrada")
    return pub


@router.get(
    "/publications/by-pmid/{pmid}",
    response_model=PublicationSchema,
    tags=["Publicaciones"],
    summary="Detalle por PMID",
    response_description="Publicación con todos sus metadatos",
)
async def obtener_publicacion_por_pmid(pmid: str, db: AsyncSession = Depends(get_async_db)):
    """Obtiene el detalle completo de una publicación por su **PubMed ID** (`pmid`)."""
    result = await db.execute(select(CanonicalPublication).where(CanonicalPublication.pmid == pmid))
    pub = result.scalar_one_or_none()
    if not pub:
        raise HTTPException(status_code=404, detail=f"Publicación con PMID '{pmid}' no encontrada")
    return pub


@router.get(
    "/publications/by-pmcid/{pmcid}",
    response_model=PublicationSchema,
    tags=["Publicaciones"],
    summary="Detalle por PMCID",
    response_description="Publicación con todos sus metadatos",
)
async def obtener_publicacion_por_pmcid(pmcid: str, db: AsyncSession = Depends(get_async_db)):
    """Obtiene el detalle completo de una publicación por su **PubMed Central ID** (`pmcid`)."""
    result = await db.execute(select(CanonicalPublication).where(CanonicalPublication.pmcid == pmcid))
    pub = result.scalar_one_or_none()
    if not pub:
        raise HTTPException(status_code=404, detail=f"Publicación con PMCID '{pmcid}' no encontrada")
    return pub


@router.get(
    "/publications/by-year/{year}",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Filtrar por año",
    response_description="Publicaciones del año indicado",
)
async def obtener_publicaciones_por_año(
    year: int = Path(..., ge=1900, le=2100, description="Año de publicación, ej: `2023`"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """Retorna todas las publicaciones del **año** especificado."""
    result = await db.execute(
        select(CanonicalPublication)
        .where(CanonicalPublication.publication_year == year)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/publications/by-journal/{journal_id}",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Filtrar por journal",
    response_description="Publicaciones del journal indicado",
)
async def obtener_publicaciones_por_journal(
    journal_id: int = Path(..., description="ID interno del journal en el sistema"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """Retorna publicaciones del **journal** identificado por su `journal_id` interno."""
    result = await db.execute(
        select(CanonicalPublication)
        .where(CanonicalPublication.journal_id == journal_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/publications/by-estado/{estado}",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Filtrar por estado de validación",
    response_description="Publicaciones en el estado solicitado",
)
async def obtener_publicaciones_por_estado(
    estado: str = Path(..., description="Estado de validación: `Avalado` | `Revisión` | `Rechazado`"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Filtra publicaciones por su **estado de validación editorial**.

    | Estado | Significado |
    |--------|-------------|
    | `Avalado` | Publicación revisada y aceptada |
    | `Revisión` | Pendiente de revisión |
    | `Rechazado` | Descartada del repositorio |
    """
    from app.models import PublicacionEstado
    result = await db.execute(
        select(CanonicalPublication)
        .join(PublicacionEstado, CanonicalPublication.estado_publicacion_id == PublicacionEstado.id)
        .where(PublicacionEstado.nombre == estado)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/publications/by-type/{publication_type}",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Filtrar por tipo de publicación",
    response_description="Publicaciones del tipo indicado",
)
async def obtener_publicaciones_por_tipo(
    publication_type: str = Path(..., description="Tipo: `article` | `conference` | `book` | `book_chapter` | `review`"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """Filtra por `publication_type`. Los valores exactos dependen de las fuentes de datos."""
    result = await db.execute(
        select(CanonicalPublication)
        .where(CanonicalPublication.publication_type == publication_type)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/publications/by-language/{language}",
    response_model=List[PublicationSummary],
    tags=["Publicaciones"],
    summary="Filtrar por idioma",
    response_description="Publicaciones en el idioma indicado",
)
async def obtener_publicaciones_por_idioma(
    language: str = Path(..., description="Código de idioma ISO 639-1: `en` | `es` | `pt` | `fr`"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """Filtra publicaciones por idioma usando códigos **ISO 639-1** (`en`, `es`, `pt`, etc.)."""
    result = await db.execute(
        select(CanonicalPublication)
        .where(CanonicalPublication.language == language)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


# RUTA GENÉRICA — debe ir al final para no interceptar rutas específicas
@router.get(
    "/publications/{publication_id}",
    response_model=PublicationSchema,
    tags=["Publicaciones"],
    summary="Detalle completo por ID",
    response_description="Publicación con todos sus metadatos",
)
async def obtener_publicacion(publication_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene **todos los metadatos** de una publicación por su ID interno.

    Para obtener el ID de una publicación primero usa:
    - `GET /publications` (lista general)
    - `GET /publications/search?q=...` (búsqueda por texto)
    - `GET /publications/by-identifier?doi=...` (por identificador externo)
    """
    result = await db.execute(
        select(CanonicalPublication).where(CanonicalPublication.id == publication_id)
    )
    pub = result.scalar_one_or_none()
    if not pub:
        raise HTTPException(status_code=404, detail=f"Publicación con ID {publication_id} no encontrada")
    return pub


# ====================== AUTORES ======================

@router.get(
    "/authors",
    response_model=List[AuthorSummarySchema],
    tags=["Autores"],
    summary="Listar autores",
    response_description="Lista paginada de autores (schema resumido)",
)
async def obtener_autores(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """Retorna todos los autores del repositorio con **paginación**."""
    result = await db.execute(select(Author).offset(skip).limit(limit))
    return result.scalars().all()


@router.get(
    "/authors/search",
    response_model=List[AuthorSummarySchema],
    tags=["Autores"],
    summary="Buscar autores por nombre",
    response_description="Autores que coinciden con el término de búsqueda",
)
async def buscar_autores(
    q: str = Query(
        ...,
        min_length=1,
        description="Texto a buscar en `name` y `normalized_name` (case-insensitive)",
        example="García",
    ),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Búsqueda **case-insensitive** en `name` y `normalized_name`.

    Usa `normalized_name` para búsquedas sin acentos o con variaciones ortográficas,
    ej: buscar `garcia` coincide con `García López, María`.
    """
    pattern = f"%{q}%"
    result = await db.execute(
        select(Author)
        .filter(
            or_(
                Author.name.ilike(pattern),
                Author.normalized_name.ilike(pattern),
            )
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/authors/institutional",
    response_model=List[AuthorSummarySchema],
    tags=["Autores"],
    summary="Autores institucionales",
    response_description="Autores con is_institutional = true",
)
async def obtener_autores_institucionales(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """Retorna autores con `is_institutional = true` (afiliados a la institución)."""
    result = await db.execute(
        select(Author).where(Author.is_institutional == True).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/authors/non-institutional",
    response_model=List[AuthorSummarySchema],
    tags=["Autores"],
    summary="Autores externos (no institucionales)",
    response_description="Autores con is_institutional = false",
)
async def obtener_autores_no_institucionales(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """Retorna autores con `is_institutional = false` (coautores externos a la institución)."""
    result = await db.execute(
        select(Author).where(Author.is_institutional == False).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/authors/verified",
    response_model=List[AuthorSummarySchema],
    tags=["Autores"],
    summary="Autores verificados manualmente",
    response_description="Autores con verification_status distinto de auto_detected",
)
async def obtener_autores_verificados(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retorna autores cuyo `verification_status` **no** es `auto_detected`.

    Estos autores han sido revisados manualmente o verificados contra
    fuentes externas (ORCID, registro institucional, etc.).
    """
    result = await db.execute(
        select(Author)
        .where(Author.verification_status != "auto_detected")
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/authors/with-orcid",
    response_model=List[AuthorSummarySchema],
    tags=["Autores"],
    summary="Autores con ORCID registrado",
    response_description="Autores que tienen ORCID no nulo",
)
async def obtener_autores_con_orcid(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """Retorna autores que tienen un **ORCID** asociado en el repositorio."""
    result = await db.execute(
        select(Author).where(Author.orcid.isnot(None)).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/authors/by-orcid/{orcid}",
    response_model=AuthorDetailSchema,
    tags=["Autores"],
    summary="Detalle por ORCID",
    response_description="Autor con todos sus metadatos",
)
async def obtener_autor_por_orcid(
    orcid: str = Path(..., description="ORCID completo, ej: `0000-0002-1825-0097`"),
    db: AsyncSession = Depends(get_async_db),
):
    """Obtiene el detalle completo de un autor por su **ORCID**."""
    result = await db.execute(select(Author).where(Author.orcid == orcid))
    autor = result.scalar_one_or_none()
    if not autor:
        raise HTTPException(status_code=404, detail=f"Autor con ORCID '{orcid}' no encontrado")
    return autor


@router.get(
    "/authors/by-cedula/{cedula}",
    response_model=AuthorDetailSchema,
    tags=["Autores"],
    summary="Detalle por cédula",
    response_description="Autor con todos sus metadatos",
)
async def obtener_autor_por_cedula(
    cedula: str = Path(..., description="Número de cédula (identificación nacional)"),
    db: AsyncSession = Depends(get_async_db),
):
    """Obtiene el detalle completo de un autor institucional por su **número de cédula**."""
    result = await db.execute(select(Author).where(Author.cedula == cedula))
    autor = result.scalar_one_or_none()
    if not autor:
        raise HTTPException(status_code=404, detail=f"Autor con cédula '{cedula}' no encontrado")
    return autor


# RUTA GENÉRICA — debe ir al final
@router.get(
    "/authors/{author_id}",
    response_model=AuthorDetailSchema,
    tags=["Autores"],
    summary="Detalle completo por ID",
    response_description="Autor con todos sus metadatos",
)
async def obtener_autor(author_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Obtiene **todos los metadatos** de un autor por su ID interno.

    Para obtener el `author_id` usa primero:
    - `GET /authors` o `GET /authors/search?q=...`
    - `GET /publication-authors/by-publication/{id}` para ver autores de una publicación
    """
    result = await db.execute(select(Author).where(Author.id == author_id))
    autor = result.scalar_one_or_none()
    if not autor:
        raise HTTPException(status_code=404, detail=f"Autor con ID {author_id} no encontrado")
    return autor


# ====================== RELACIONES PUBLICACIÓN-AUTOR ======================

@router.get(
    "/publication-authors",
    response_model=List[PublicationAuthorSchema],
    tags=["Relaciones"],
    summary="Listar todas las relaciones",
    response_description="Lista paginada de vínculos publicación-autor",
)
async def obtener_todas_relaciones(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retorna la tabla de relaciones **publicación ↔ autor** con paginación.

    Cada relación incluye `author_position` (orden en la lista de autoría)
    y `role` (`author`, `corresponding`, etc.).

    Para consultar relaciones de una entidad específica usa:
    - `GET /publication-authors/by-publication/{id}`
    - `GET /publication-authors/by-author/{id}`
    """
    result = await db.execute(select(PublicationAuthor).offset(skip).limit(limit))
    return result.scalars().all()


@router.get(
    "/publication-authors/by-publication/{publication_id}",
    response_model=List[PublicationAuthorSchema],
    tags=["Relaciones"],
    summary="Autores de una publicación",
    response_description="Lista de relaciones para la publicación indicada (vacía si no hay autores registrados)",
)
async def obtener_autores_de_publicacion(
    publication_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retorna **todas las relaciones autor** asociadas a una publicación.

    Cada relación incluye `author_id`, `author_position` y `role`.
    Para obtener el detalle del autor usa `GET /authors/{author_id}`.

    Retorna lista vacía `[]` si la publicación no tiene autores registrados en la tabla de relaciones.
    """
    result = await db.execute(
        select(PublicationAuthor).where(PublicationAuthor.publication_id == publication_id)
    )
    return result.scalars().all()


@router.get(
    "/publication-authors/by-author/{author_id}",
    response_model=List[PublicationAuthorSchema],
    tags=["Relaciones"],
    summary="Publicaciones de un autor",
    response_description="Lista de relaciones para el autor indicado (vacía si no hay publicaciones registradas)",
)
async def obtener_publicaciones_de_autor(
    author_id: int,
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Retorna **todas las publicaciones** asociadas a un autor.

    Cada relación incluye `publication_id`, `author_position` y `role`.
    Para obtener el detalle de la publicación usa `GET /publications/{publication_id}`.

    Retorna lista vacía `[]` si el autor no tiene publicaciones en la tabla de relaciones.
    """
    result = await db.execute(
        select(PublicationAuthor)
        .where(PublicationAuthor.author_id == author_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get(
    "/publication-authors/{relation_id}",
    response_model=PublicationAuthorSchema,
    tags=["Relaciones"],
    summary="Detalle de una relación por ID",
    response_description="Relación publicación-autor con todos sus campos",
)
async def obtener_relacion_publicacion_autor(
    relation_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """Obtiene el detalle de un vínculo específico **publicación ↔ autor** por su ID interno."""
    result = await db.execute(
        select(PublicationAuthor).where(PublicationAuthor.id == relation_id)
    )
    relacion = result.scalar_one_or_none()
    if not relacion:
        raise HTTPException(status_code=404, detail=f"Relación con ID {relation_id} no encontrada")
    return relacion


# ====================== DETALLE ENRIQUECIDO ======================

@router.get(
    "/api/publications/{pub_id}",
    response_model=PublicationWithDetails,
    tags=["Publicaciones"],
    summary="Detalle completo con registros externos y autores",
    response_description="Publicación con metadatos completos, registros de fuentes externas y lista de autores",
)
async def obtener_publicacion_con_detalles(pub_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Retorna el **detalle enriquecido** de una publicación combinando tres fuentes:

    | Sección | Contenido |
    |---------|-----------|
    | Metadatos | Todos los campos de `GET /publications/{id}` |
    | `source_records` | Registros originales de Scopus, WoS, PubMed, etc. |
    | `authors` | Lista de autores ordenada por posición, con ORCID, cédula y rol |

    Los `source_records` permiten comparar cómo cada fuente reporta la misma publicación
    (título, DOI, citas) antes de la reconciliación canónica.
    """
    result = await db.execute(
        select(CanonicalPublication)
        .where(CanonicalPublication.id == pub_id)
    )
    pub = result.scalar_one_or_none()
    if not pub:
        raise HTTPException(status_code=404, detail=f"Publicación con ID {pub_id} no encontrada")
    return await _build_with_details(pub, db)
