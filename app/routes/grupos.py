from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.schemas import PublicacionGrupoSchema

router = APIRouter(tags=["Grupos"])

# Campos comunes para ambos endpoints
_SELECT = """
    SELECT
        cp.id                           AS canonical_publication_id,
        cp.title,
        cp.doi,
        cp.publication_year,
        cp.source_journal,
        cp.publication_type,
        cp.is_institutional,
        cp.institutional_authors_count,
        cp.citation_count,
        cp.is_open_access,
        cp.source_url,
        cm.cod_grupo_gr,
        cm.nme_grupo_gr,
        cm.nme_clase_pd,
        cm.nme_tipo_medicion_pd,
        cm.nme_tipologia_pd,
        cm.nme_convocatoria,
        cm.ano_convo,
        cm.match_score,
        cm.match_method,
        (
            SELECT COALESCE(
                NULLIF(scopus_link, ''),
                'https://www.scopus.com/pages/publications/' || scopus_doc_id || '?origin=resultslist'
            )
            FROM scopus_records
            WHERE canonical_publication_id = cp.id AND status = 'matched'
            LIMIT 1
        ) AS scopus_url,
        (
            SELECT COALESCE(NULLIF(openalex_work_id, ''), NULLIF(url, ''))
            FROM openalex_records
            WHERE canonical_publication_id = cp.id AND status = 'matched'
            LIMIT 1
        ) AS openalex_url,
        (
            SELECT COALESCE(
                NULLIF(url, ''),
                'https://www.webofscience.com/wos/woscc/full-record/' || wos_uid
            )
            FROM wos_records
            WHERE canonical_publication_id = cp.id AND status = 'matched'
            LIMIT 1
        ) AS wos_url
    FROM clasificacion_minciencias cm
    JOIN canonical_publications cp ON cp.id = cm.canonical_publication_id
"""


@router.get(
    "/grupos/{cod_grupo}/publicaciones",
    response_model=List[PublicacionGrupoSchema],
    summary="Publicaciones de un grupo de investigación",
    description=(
        "Retorna todas las publicaciones clasificadas en Minciencias para un grupo, "
        "cruzadas con sus metadatos canónicos y URLs de fuentes externas (Scopus, OpenAlex, WoS). "
        "Filtros opcionales: `anio` y `clasificacion`."
    ),
)
async def publicaciones_por_grupo(
    cod_grupo: str,
    anio: Optional[int] = Query(None, description="Filtrar por año de publicación", ge=1900, le=2100),
    clasificacion: Optional[str] = Query(None, description="Filtrar por clasificación: A1 | A | B | C | D"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(20, ge=1, le=200, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_async_db),
):
    where = "WHERE cm.cod_grupo_gr = :cod_grupo"
    params: dict = {"cod_grupo": cod_grupo, "skip": skip, "limit": limit}

    if anio:
        where += " AND cp.publication_year = :anio"
        params["anio"] = anio
    if clasificacion:
        where += " AND cm.nme_clase_pd = :clasificacion"
        params["clasificacion"] = clasificacion.upper()

    sql = text(f"{_SELECT} {where} ORDER BY cp.publication_year DESC OFFSET :skip LIMIT :limit")
    result = await db.execute(sql, params)
    rows = result.mappings().all()

    if not rows and not anio and not clasificacion:
        # Verificar si el grupo existe
        check = await db.execute(
            text("SELECT 1 FROM clasificacion_minciencias WHERE cod_grupo_gr = :g LIMIT 1"),
            {"g": cod_grupo},
        )
        if not check.fetchone():
            raise HTTPException(status_code=404, detail=f"Grupo '{cod_grupo}' no encontrado")

    return [PublicacionGrupoSchema(**dict(row)) for row in rows]


@router.get(
    "/publicaciones/{canonical_publication_id}/grupos",
    response_model=List[PublicacionGrupoSchema],
    summary="Grupos que clasifican una publicación",
    description=(
        "Retorna todos los grupos de investigación de Minciencias que tienen clasificada "
        "esta publicación, con sus metadatos de cruce (score, método, convocatoria)."
    ),
)
async def grupos_por_publicacion(
    canonical_publication_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    sql = text(f"{_SELECT} WHERE cm.canonical_publication_id = :pub_id ORDER BY cm.ano_convo DESC")
    result = await db.execute(sql, {"pub_id": canonical_publication_id})
    rows = result.mappings().all()

    if not rows:
        check = await db.execute(
            text("SELECT 1 FROM canonical_publications WHERE id = :id LIMIT 1"),
            {"id": canonical_publication_id},
        )
        if not check.fetchone():
            raise HTTPException(status_code=404, detail=f"Publicación {canonical_publication_id} no encontrada")

    return [PublicacionGrupoSchema(**dict(row)) for row in rows]
