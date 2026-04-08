from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel, EntityReference


class WorkDetailResponse(APIModel):
    id: str
    slug: str
    title_cn: str
    title_en: str | None = None
    description: str | None = None
    excerpt_text: str | None = None
    image_url: str | None = None
    authenticity: str
    creation_period: str | None = None
    material: str | None = None
    dimensions: str | None = None
    current_collection: str | None = None
    era: EntityReference | None = None
    style: EntityReference | None = None
    calligrapher: EntityReference | None = None
    related_terms: list[EntityReference] = Field(default_factory=list)


class CalligrapherDetailResponse(APIModel):
    id: str
    slug: str
    name_cn: str
    name_en: str | None = None
    biography: str | None = None
    hometown: str | None = None
    birth_year: int | None = None
    death_year: int | None = None
    era: EntityReference | None = None
    primary_style: EntityReference | None = None
    representative_works: list[EntityReference] = Field(default_factory=list)
