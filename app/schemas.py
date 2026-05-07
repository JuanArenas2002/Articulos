from pydantic import BaseModel, Field, computed_field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, List, Union


# ====================== AUTHOR SCHEMAS ======================

class AuthorSummary(BaseModel):
    id: int = Field(description="Identificador único del autor")
    name: str = Field(description="Nombre completo tal como aparece en la publicación")
    normalized_name: Optional[str] = Field(None, description="Nombre normalizado para búsquedas y deduplicación")
    orcid: Optional[str] = Field(None, description="ORCID del autor, ej: 0000-0002-1825-0097")
    is_institutional: bool = Field(description="True si el autor pertenece a la institución")
    verification_status: str = Field(
        description="Estado de verificación: `auto_detected` | `verified` | `manual`"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 7,
                "name": "García López, María",
                "normalized_name": "garcia lopez maria",
                "orcid": "0000-0002-1825-0097",
                "is_institutional": True,
                "verification_status": "verified",
            }
        }


class AuthorDetail(BaseModel):
    id: int = Field(description="Identificador único del autor")
    name: str = Field(description="Nombre completo tal como aparece en la publicación")
    normalized_name: Optional[str] = Field(None, description="Nombre normalizado para búsquedas y deduplicación")
    orcid: Optional[str] = Field(None, description="ORCID del autor, ej: 0000-0002-1825-0097")
    is_institutional: bool = Field(description="True si el autor pertenece a la institución")
    cedula: Optional[str] = Field(None, description="Número de cédula (identificación nacional)")
    verification_status: str = Field(
        description="Estado de verificación: `auto_detected` | `verified` | `manual`"
    )
    field_provenance: Optional[Dict[str, Any]] = Field(
        None, description="Origen de cada campo: qué fuente bibliográfica aportó qué dato"
    )
    external_ids: Optional[Dict[str, Any]] = Field(
        None, description="Identificadores externos: Scopus Author ID, ResearcherID, etc."
    )
    possible_duplicate_of: Optional[int] = Field(
        None, description="ID del autor del que podría ser duplicado (null si no aplica)"
    )
    created_at: datetime = Field(description="Fecha de creación del registro")
    updated_at: datetime = Field(description="Fecha de última actualización")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 7,
                "name": "García López, María",
                "normalized_name": "garcia lopez maria",
                "orcid": "0000-0002-1825-0097",
                "is_institutional": True,
                "cedula": "1234567890",
                "verification_status": "verified",
                "field_provenance": {"orcid": "scopus", "name": "wos"},
                "external_ids": {"scopus_id": "55432198700"},
                "possible_duplicate_of": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-03-20T08:00:00Z",
            }
        }


# ====================== PUBLICATION SCHEMAS ======================

class EstadoSchema(BaseModel):
    id: int = Field(description="ID del estado")
    nombre: str = Field(description="Nombre del estado: Avalado | Revisión | Rechazado")

    class Config:
        from_attributes = True


class PublicationSummary(BaseModel):
    id: int = Field(description="Identificador único interno de la publicación")
    title: str = Field(description="Título original de la publicación")
    doi: Optional[str] = Field(None, description="DOI canónico, ej: `10.1016/j.bodyim.2026.102032`")
    publication_year: Optional[int] = Field(None, description="Año de publicación, ej: `2023`")
    publication_type: Optional[str] = Field(
        None, description="Tipo: `article` | `conference` | `book` | `book_chapter` | `review`"
    )
    source_journal: Optional[str] = Field(None, description="Nombre del journal o conferencia fuente")
    citation_count: int = Field(description="Total de citas recibidas (agregado de todas las fuentes)")
    coauthorships_count: Optional[int] = Field(None, description="Número de coautorías")
    is_open_access: Optional[bool] = Field(None, description="True si la publicación es de acceso abierto")
    knowledge_area: Optional[str] = Field(None, description="Área de conocimiento CINE/UNESCO")
    first_author: Optional[str] = Field(None, description="Nombre del primer autor")
    abstract: Optional[str] = Field(None, description="Resumen o abstract de la publicación")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 42,
                "title": "Deep learning approaches for protein structure prediction",
                "doi": "10.1016/j.jmb.2023.168025",
                "publication_year": 2023,
                "publication_type": "article",
                "source_journal": "Journal of Molecular Biology",
                "citation_count": 87,
                "coauthorships_count": 4,
                "is_open_access": True,
                "knowledge_area": "Ciencias Naturales",
                "first_author": "García López, María",
                "abstract": "We present a novel approach...",
            }
        }


class CanonicalPublicationDetail(BaseModel):
    id: int = Field(description="Identificador único interno")
    title: str = Field(description="Título original de la publicación")
    doi: Optional[str] = Field(None, description="DOI canónico, ej: `10.1016/j.bodyim.2026.102032`")
    pmid: Optional[str] = Field(None, description="PubMed ID (artículos biomédicos)")
    pmcid: Optional[str] = Field(None, description="PubMed Central ID")
    normalized_title: Optional[str] = Field(None, description="Título normalizado para búsquedas (sin acentos, minúsculas)")
    publication_year: Optional[int] = Field(None, description="Año de publicación")
    publication_date: Optional[str] = Field(None, description="Fecha exacta de publicación (YYYY-MM-DD cuando disponible)")
    publication_type: Optional[str] = Field(
        None, description="Tipo: `article` | `conference` | `book` | `book_chapter` | `review`"
    )
    language: Optional[str] = Field(None, description="Idioma del documento, ej: `en` | `es`")
    journal_id: Optional[int] = Field(None, description="ID interno del journal en el sistema")
    source_journal: Optional[str] = Field(None, description="Nombre completo del journal o venue")
    issn: Optional[str] = Field(None, description="ISSN del journal")
    is_open_access: Optional[bool] = Field(None, description="True si tiene acceso abierto")
    oa_status: Optional[str] = Field(
        None, description="Tipo de acceso abierto: `gold` | `green` | `hybrid` | `bronze` | `closed`"
    )
    citation_count: int = Field(description="Total de citas recibidas (agregado multi-fuente)")
    institutional_authors_count: int = Field(description="Número de autores que pertenecen a la institución")
    sources_count: int = Field(description="Número de fuentes bibliográficas que registran esta publicación")
    estado: Optional[EstadoSchema] = Field(None, description="Estado resuelto: id y nombre desde publicacion_estados")
    abstract: Optional[str] = Field(None, description="Resumen completo")
    keywords: Optional[str] = Field(None, description="Palabras clave separadas por punto y coma")
    source_url: Optional[str] = Field(None, description="URL a la publicación original")
    page_range: Optional[str] = Field(None, description="Rango de páginas, ej: `120-135`")
    publisher: Optional[str] = Field(None, description="Editorial o publisher")
    citations_by_source: Optional[Dict[str, Any]] = Field(
        None,
        description="Citas desglosadas por fuente bibliográfica, ej: `{\"scopus\": 45, \"wos\": 38, \"pubmed\": 4}`",
    )
    corresponding_author: Optional[str] = Field(None, description="Nombre del autor de correspondencia")
    is_institutional: bool = Field(description="True si al menos un autor es institucional")
    created_at: datetime = Field(description="Fecha de ingreso al sistema")
    updated_at: datetime = Field(description="Fecha de última actualización del registro")

    @computed_field(description="URLs directas a los registros en fuentes externas, derivadas de los identificadores disponibles")
    @property
    def external_links(self) -> Dict[str, str]:
        links = {}
        if self.doi:
            links["doi"] = f"https://doi.org/{self.doi}"
        if self.pmid:
            links["pubmed"] = f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}"
        if self.pmcid:
            links["pmc"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{self.pmcid}"
        if self.source_url:
            links["source"] = self.source_url
        return links

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 42,
                "title": "Deep learning approaches for protein structure prediction",
                "doi": "10.1016/j.jmb.2023.168025",
                "pmid": "37852456",
                "pmcid": "PMC10612345",
                "normalized_title": "deep learning approaches for protein structure prediction",
                "publication_year": 2023,
                "publication_date": "2023-09-01",
                "publication_type": "article",
                "language": "en",
                "journal_id": 501,
                "source_journal": "Journal of Molecular Biology",
                "issn": "0022-2836",
                "is_open_access": True,
                "oa_status": "gold",
                "citation_count": 87,
                "institutional_authors_count": 2,
                "sources_count": 3,
                "abstract": "We present a novel approach...",
                "keywords": "deep learning; protein folding; neural networks",
                "source_url": "https://doi.org/10.1016/j.jmb.2023.168025",
                "page_range": "168025",
                "publisher": "Elsevier",
                "citations_by_source": {"scopus": 45, "wos": 38, "pubmed": 4},
                "corresponding_author": "García López, María",
                "is_institutional": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-03-20T08:00:00Z",
                "external_links": {
                    "doi": "https://doi.org/10.1016/j.jmb.2023.168025",
                    "pubmed": "https://pubmed.ncbi.nlm.nih.gov/37852456",
                    "pmc": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10612345",
                    "source": "https://doi.org/10.1016/j.jmb.2023.168025",
                },
            }
        }


# ====================== SOURCE RECORD SCHEMAS ======================

class SourceRecordSchema(BaseModel):
    id: int = Field(description="ID del registro en la tabla fuente")
    source_name: str = Field(description="Fuente: `openalex` | `scopus` | `wos` | `cvlac` | `datos_abiertos` | `gruplac` | `google_scholar`")
    source_id: Optional[str] = Field(None, description="Identificador nativo de la fuente (es URL en OpenAlex)")
    doi: Optional[str] = Field(None, description="DOI reportado por esta fuente")
    status: Optional[str] = Field(None, description="Estado del registro: `matched` | `unmatched` | `rejected`")
    match_type: Optional[str] = Field(None, description="Tipo de coincidencia: `doi_exact` | `title_fuzzy` | ...")
    match_score: Optional[int] = Field(None, description="Puntuación de coincidencia 0-100")
    record_url: Optional[str] = Field(None, description="URL directa al registro en la fuente externa")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 4379,
                "source_name": "openalex",
                "source_id": "https://openalex.org/W7128480087",
                "doi": "10.3390/en19040915",
                "status": "matched",
                "match_type": "doi_exact",
                "match_score": 100,
                "record_url": "https://openalex.org/W7128480087",
            }
        }


# ====================== PUBLICATION_AUTHOR SCHEMAS ======================

class PublicationAuthor(BaseModel):
    id: int = Field(description="Identificador único de la relación")
    publication_id: int = Field(description="ID de la publicación")
    author_id: int = Field(description="ID del autor")
    is_institutional: bool = Field(description="True si el autor es institucional en esta publicación")
    author_position: Optional[int] = Field(
        None, description="Posición del autor en la lista de autoría (1 = primer autor)"
    )
    role: Optional[str] = Field(None, description="Rol del autor: `author` | `corresponding` | `editor`")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 155,
                "publication_id": 42,
                "author_id": 7,
                "is_institutional": True,
                "author_position": 1,
                "role": "corresponding",
            }
        }


# ====================== REVISTA SCHEMAS ======================

class CategoriaItem(BaseModel):
    cuartil: Optional[str] = Field(None, description="Cuartil en esta categoría: Q1 | Q2 | Q3 | Q4")
    categoria: Optional[str] = Field(None, description="Nombre de la categoría SCImago")

    class Config:
        from_attributes = True


class RevistaMetricaAnual(BaseModel):
    anio: int = Field(description="Año de la métrica")
    cuartil: Optional[str] = Field(None, description="Cuartil SCImago: Q1 | Q2 | Q3 | Q4")
    sjr: Optional[float] = Field(None, description="SCImago Journal Rank")
    h_index: Optional[int] = Field(None, description="Índice H acumulado")
    total_docs: Optional[int] = Field(None, description="Total documentos publicados ese año")
    total_docs_3years: Optional[int] = Field(None, description="Total documentos en ventana de 3 años")
    total_citas_3years: Optional[int] = Field(None, description="Total citas en ventana de 3 años")
    citas_por_doc: Optional[float] = Field(None, description="Promedio de citas por documento")
    categorias: Optional[List[CategoriaItem]] = Field(None, description="Categorías temáticas SCImago con cuartil")

    class Config:
        from_attributes = True


class RevistaCoberturaItem(BaseModel):
    anio_inicio: Optional[int] = Field(None, description="Año de inicio de cobertura")
    anio_fin: Optional[int] = Field(None, description="Año de fin de cobertura (null = presente)")

    class Config:
        from_attributes = True


class RevistaDetail(BaseModel):
    source_id: Optional[str] = Field(None, description="ID en la fuente origen (SCImago)")
    titulo: str = Field(description="Nombre oficial de la revista")
    tipo: Optional[str] = Field(None, description="Tipo: journal | conference | book series")
    issn_print: Optional[str] = Field(None, description="ISSN edición impresa")
    eissn: Optional[str] = Field(None, description="ISSN edición electrónica")
    editorial: Optional[str] = Field(None, description="Editorial o publisher")
    pais: Optional[str] = Field(None, description="País de publicación")
    region: Optional[str] = Field(None, description="Región geográfica")
    open_access: Optional[bool] = Field(None, description="True si es revista de acceso abierto")
    coverage: Optional[str] = Field(None, description="Cobertura temporal textual, ej: 1997-present")
    areas_tematicas: Optional[List[str]] = Field(None, description="Áreas temáticas amplias")
    metricas_anuales: List[RevistaMetricaAnual] = Field(
        default_factory=list, description="Historial de métricas anuales (SCImago)"
    )
    organismo_responsable: Optional[str] = Field(None, description="Organismo responsable (Latindex)")
    naturaleza_publicacion: Optional[str] = Field(None, description="Naturaleza editorial (Latindex)")
    indizaciones: Optional[List[str]] = Field(None, description="Bases de datos en que está indizada (Latindex)")
    derechos_uso: Optional[str] = Field(None, description="Política de derechos de uso (Latindex)")
    arbitrada: Optional[bool] = Field(None, description="True si es revista arbitrada (Latindex)")
    notas: Optional[str] = Field(None, description="Notas adicionales")
    cobertura: List[RevistaCoberturaItem] = Field(
        default_factory=list, description="Rangos de cobertura temporal (Scopus)"
    )
    metrica_del_anio: Optional[RevistaMetricaAnual] = Field(
        None, description="Métrica del año consultado (o del último año disponible)"
    )
    anio_consultado: Optional[int] = Field(None, description="Año solicitado en la consulta")
    anio_encontrado: Optional[int] = Field(None, description="Año para el que se encontró métrica")
    fuentes: Optional[Dict[str, Any]] = Field(
        None, description="Mapa campo → fuente que aportó el dato"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "source_id": "1234567",
                "titulo": "Nature Reviews Medicine",
                "tipo": "journal",
                "issn_print": "2684-6543",
                "eissn": "2684-6551",
                "editorial": "Springer Nature",
                "pais": "United Kingdom",
                "region": "Europe",
                "open_access": False,
                "coverage": "1997-present",
                "areas_tematicas": ["Medicine & Pharmacology", "Biomedical Sciences"],
                "metricas_anuales": [
                    {
                        "anio": 2024,
                        "cuartil": "Q1",
                        "sjr": 3.512,
                        "h_index": 162,
                        "total_docs": 156,
                        "total_docs_3years": 463,
                        "total_citas_3years": 9876,
                        "citas_por_doc": 21.34,
                        "categorias": ["Medicine, General"],
                    }
                ],
                "organismo_responsable": "Springer Nature",
                "naturaleza_publicacion": "Peer-reviewed journal",
                "indizaciones": ["Scopus", "PubMed", "Web of Science"],
                "derechos_uso": "Restricted Access",
                "arbitrada": True,
                "notas": "High impact journal in medical research",
                "cobertura": [{"anio_inicio": 2010, "anio_fin": 2024}],
                "metrica_del_anio": {
                    "anio": 2024,
                    "cuartil": "Q1",
                    "sjr": 3.512,
                    "h_index": 162,
                    "total_docs": 156,
                    "total_docs_3years": 463,
                    "total_citas_3years": 9876,
                    "citas_por_doc": 21.34,
                    "categorias": ["Medicine, General"],
                },
                "anio_consultado": 2024,
                "anio_encontrado": 2024,
                "fuentes": {
                    "source_id": "SCImago",
                    "titulo": "SCImago",
                    "cuartil": "SCImago",
                    "organismo_responsable": "Latindex",
                    "indizaciones": "Latindex",
                    "cobertura": "Scopus",
                },
            }
        }


# ====================== PUBLICATION WITH DETAILS SCHEMAS ======================

class AuthorInPublication(BaseModel):
    author_id: int = Field(description="ID interno del autor")
    name: str = Field(description="Nombre completo del autor")
    normalized_name: Optional[str] = Field(None, description="Nombre normalizado para búsquedas")
    orcid: Optional[str] = Field(None, description="ORCID del autor")
    cedula: Optional[str] = Field(None, description="Cédula del autor (institucionales)")
    is_institutional: bool = Field(description="True si el autor es institucional")
    verification_status: str = Field(description="Estado de verificación: `auto_detected` | `verified` | `manual`")
    author_position: Optional[int] = Field(None, description="Posición en la lista de autoría (1 = primer autor)")
    role: Optional[str] = Field(None, description="Rol: `author` | `corresponding` | `editor`")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "author_id": 7,
                "name": "García López, María",
                "normalized_name": "garcia lopez maria",
                "orcid": "0000-0002-1825-0097",
                "cedula": "1234567890",
                "is_institutional": True,
                "verification_status": "verified",
                "author_position": 1,
                "role": "corresponding",
            }
        }


# ====================== GRUPOS / MINCIENCIAS SCHEMAS ======================

class ClasificacionMincienciasSchema(BaseModel):
    cod_grupo_gr: str = Field(description="Código del grupo de investigación")
    nme_grupo_gr: Optional[str] = Field(None, description="Nombre del grupo")
    nme_clase_pd: Optional[str] = Field(None, description="Clasificación obtenida: A1 | A | B | C | D")
    nme_tipo_medicion_pd: Optional[str] = Field(None, description="Tipo de medición Minciencias")
    nme_tipologia_pd: Optional[str] = Field(None, description="Tipología de la publicación")
    nme_convocatoria: Optional[str] = Field(None, description="Nombre de la convocatoria")
    ano_convo: Optional[int] = Field(None, description="Año de la convocatoria")
    match_score: Optional[float] = Field(None, description="Score del cruce")
    match_method: Optional[str] = Field(None, description="Método: doi_exact | title_fuzzy | ...")

    @field_validator("ano_convo", mode="before")
    @classmethod
    def parse_ano_convo(cls, v):
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                pass
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(v, fmt).year
                except ValueError:
                    pass
        return None


class PublicationWithDetails(CanonicalPublicationDetail):
    external_records: List[SourceRecordSchema] = Field(
        default_factory=list,
        description="Registros originales de cada fuente bibliográfica que reporta esta publicación",
    )
    authors: List[AuthorInPublication] = Field(
        default_factory=list,
        description="Lista de autores ordenada por posición, con datos de identificación y rol",
    )
    revista: Optional[RevistaDetail] = Field(
        None,
        description="Información de la revista (SCImago + Latindex + Scopus) obtenida por ISSN del artículo",
    )
    clasificaciones_minciencias: List[ClasificacionMincienciasSchema] = Field(
        default_factory=list,
        description="Grupos de investigación que clasificaron esta publicación en Minciencias, con convocatoria y categoría obtenida",
    )

    class Config:
        from_attributes = True

class PublicacionGrupoSchema(BaseModel):
    # ── Publicación canónica ──────────────────────────────────────────────
    canonical_publication_id: int = Field(description="ID interno de la publicación canónica")
    title: str = Field(description="Título de la publicación")
    doi: Optional[str] = Field(None, description="DOI canónico")
    publication_year: Optional[int] = Field(None, description="Año de publicación")
    source_journal: Optional[str] = Field(None, description="Revista o venue")
    publication_type: Optional[str] = Field(None, description="Tipo: article | review | conference | ...")
    is_institutional: bool = Field(description="True si tiene al menos un autor institucional")
    institutional_authors_count: int = Field(description="Número de autores con afiliación institucional")
    citation_count: int = Field(description="Total de citas recibidas")
    is_open_access: Optional[bool] = Field(None, description="True si es acceso abierto")
    source_url: Optional[str] = Field(None, description="URL al documento fuente")
    # ── URLs externas (primera coincidencia matched por fuente) ───────────
    scopus_url: Optional[str] = Field(None, description="URL del registro en Scopus")
    openalex_url: Optional[str] = Field(None, description="URL del registro en OpenAlex")
    wos_url: Optional[str] = Field(None, description="URL del registro en Web of Science")
    # ── Clasificación Minciencias ─────────────────────────────────────────
    cod_grupo_gr: str = Field(description="Código del grupo de investigación")
    nme_grupo_gr: Optional[str] = Field(None, description="Nombre del grupo de investigación")
    nme_clase_pd: Optional[str] = Field(None, description="Clasificación: A1 | A | B | C | D")
    nme_tipo_medicion_pd: Optional[str] = Field(None, description="Tipo de medición Minciencias")
    nme_tipologia_pd: Optional[str] = Field(None, description="Tipología de la publicación")
    nme_convocatoria: Optional[str] = Field(None, description="Nombre de la convocatoria")
    ano_convo: Optional[int] = Field(None, description="Año de la convocatoria")
    match_score: Optional[float] = Field(None, description="Score del cruce publicación-grupo")
    match_method: Optional[str] = Field(None, description="Método de cruce: doi_exact | title_fuzzy | ...")

    @field_validator("ano_convo", mode="before")
    @classmethod
    def parse_ano_convo(cls, v):
        if v is None:
            return None
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                pass
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(v, fmt).year
                except ValueError:
                    pass
        return None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "canonical_publication_id": 3189,
                "title": "Cytokine storm and COVID-19",
                "doi": "10.1136/annrheumdis-2021-220920",
                "publication_year": 2022,
                "source_journal": "Annals of the Rheumatic Diseases",
                "publication_type": "article",
                "is_institutional": True,
                "institutional_authors_count": 2,
                "citation_count": 45,
                "is_open_access": False,
                "source_url": "https://doi.org/10.1136/annrheumdis-2021-220920",
                "scopus_url": "https://www.scopus.com/pages/publications/123456",
                "openalex_url": "https://openalex.org/W2741809807",
                "wos_url": "https://www.webofscience.com/wos/woscc/full-record/WOS:000123",
                "cod_grupo_gr": "COL0012345",
                "nme_grupo_gr": "Grupo de Inmunología Clínica",
                "nme_clase_pd": "A1",
                "nme_tipo_medicion_pd": "Artículo de investigación",
                "nme_tipologia_pd": "Artículo en revista",
                "nme_convocatoria": "Convocatoria 894 de 2021",
                "ano_convo": 2021,
                "match_score": 100.0,
                "match_method": "doi_exact",
            }
        }
