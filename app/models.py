from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc)
from app.database import Base


class PublicacionEstado(Base):
    __tablename__ = "publicacion_estados"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=True)


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    normalized_name = Column(String(300), nullable=True)
    orcid = Column(String(50), nullable=True)
    is_institutional = Column(Boolean, nullable=False)
    field_provenance = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=_now)
    updated_at = Column(TIMESTAMP(timezone=True), default=_now, onupdate=_now)
    external_ids = Column(JSON, default={})
    verification_status = Column(String(30), default="auto_detected")
    possible_duplicate_of = Column(Integer, nullable=True)
    cedula = Column(String(30), nullable=True)

    publications = relationship("PublicationAuthor", back_populates="author")

    class Config:
        from_attributes = True


class CanonicalPublication(Base):
    __tablename__ = "canonical_publications"

    id = Column(Integer, primary_key=True, index=True)
    doi = Column(String(255), nullable=True)
    pmid = Column(String(50), nullable=True)
    pmcid = Column(String(50), nullable=True)
    title = Column(Text, nullable=False)
    normalized_title = Column(Text, nullable=True)
    publication_year = Column(Integer, nullable=True)
    publication_date = Column(String(20), nullable=True)
    publication_type = Column(String(100), nullable=True)
    language = Column(String(10), nullable=True)
    journal_id = Column(Integer, nullable=True)
    source_journal = Column(String(500), nullable=True)
    issn = Column(String(20), nullable=True)
    is_open_access = Column(Boolean, nullable=True)
    oa_status = Column(String(50), nullable=True)
    citation_count = Column(Integer, default=0)
    institutional_authors_count = Column(Integer, default=0)
    field_provenance = Column(JSON, nullable=True)
    sources_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), default=_now)
    updated_at = Column(TIMESTAMP(timezone=True), default=_now, onupdate=_now)
    estado_publicacion_id = Column(Integer, default=1)
    field_conflicts = Column(JSON, default={})
    citations_by_source = Column(JSON, default={})
    abstract = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    source_url = Column(String(1000), nullable=True)
    page_range = Column(String(100), nullable=True)
    publisher = Column(String(300), nullable=True)
    journal_coverage = Column(String(100), nullable=True)
    knowledge_area = Column(String(300), nullable=True)
    cine_code = Column(String(50), nullable=True)
    first_author = Column(String(300), nullable=True)
    corresponding_author = Column(String(300), nullable=True)
    coauthorships_count = Column(Integer, nullable=True)
    isbn = Column(Text, nullable=True)
    eid = Column(String(100), nullable=True)
    source_abbrev = Column(String(200), nullable=True)
    index_keywords = Column(Text, nullable=True)
    page_start = Column(String(20), nullable=True)
    page_end = Column(String(20), nullable=True)
    article_number = Column(String(50), nullable=True)
    publication_stage = Column(String(50), nullable=True)
    funding_agency = Column(String(300), nullable=True)
    funding_number = Column(String(200), nullable=True)
    conference_name = Column(String(500), nullable=True)
    is_institutional = Column(Boolean, default=False)

    authors = relationship("PublicationAuthor", back_populates="publication")
    estado = relationship(
        "PublicacionEstado",
        foreign_keys=[estado_publicacion_id],
        primaryjoin="CanonicalPublication.estado_publicacion_id == PublicacionEstado.id",
        lazy="selectin",
    )

    class Config:
        from_attributes = True


class PublicationAuthor(Base):
    __tablename__ = "publication_authors"

    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey("canonical_publications.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    is_institutional = Column(Boolean, nullable=False)
    author_position = Column(Integer, nullable=True)
    role = Column(String(50), nullable=True)

    publication = relationship("CanonicalPublication", back_populates="authors")
    author = relationship("Author", back_populates="publications")

    class Config:
        from_attributes = True
