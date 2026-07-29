from __future__ import annotations

from app.repositories.catalog_repository import CatalogRepository
from app.schemas.catalog import CalligrapherDetailResponse, WorkDetailResponse
from app.schemas.common import EntityReference


ERA_JIN = EntityReference(
    id="era-eastern-jin",
    entity_type="era",
    name="东晋 / Eastern Jin",
    summary="中国书法史上的关键时期。",
)

STYLE_RUNNING = EntityReference(
    id="style-running-script",
    entity_type="style",
    name="行书 / Running Script",
    summary="兼具书写速度与审美表现力的书体。",
)

CALLIGRAPHER_WANG = CalligrapherDetailResponse(
    id="calligrapher-wang-xizhi",
    slug="wang-xizhi",
    name_cn="王羲之",
    name_en="Wang Xizhi",
    biography="东晋书法家，被后世尊为“书圣”。",
    hometown="琅琊临沂",
    birth_year=303,
    death_year=361,
    era=ERA_JIN,
    primary_style=STYLE_RUNNING,
    representative_works=[
        EntityReference(
            id="work-lantingji-xu",
            entity_type="work",
            name="兰亭集序 / Preface to the Orchid Pavilion",
            summary="最具代表性的行书名作之一。",
        )
    ],
)

WORK_LANTINGJI = WorkDetailResponse(
    id="work-lantingji-xu",
    slug="lantingji-xu",
    title_cn="兰亭集序",
    title_en="Preface to the Orchid Pavilion",
    description="东晋永和九年兰亭雅集后所作，被视为行书典范。",
    excerpt_text="永和九年，岁在癸丑，暮春之初，会于会稽山阴之兰亭……",
    image_url=None,
    authenticity="authentic",
    creation_period="东晋永和九年",
    material="纸本（摹本流传）",
    dimensions=None,
    current_collection="故宫博物院藏唐摹本系统",
    era=ERA_JIN,
    style=STYLE_RUNNING,
    calligrapher=EntityReference(
        id=CALLIGRAPHER_WANG.id,
        entity_type="calligrapher",
        name="王羲之 / Wang Xizhi",
        summary="东晋书法家，擅行书与草书。",
    ),
    related_terms=[
        EntityReference(
            id="term-running-script",
            entity_type="term",
            name="行书 / Running Script",
            summary="介于楷书和草书之间的书写体。",
        )
    ],
)


class CatalogService:
    """Catalog service backed by MySQL with demo fallback."""

    def __init__(self, repository: CatalogRepository | None = None) -> None:
        self.repository = repository

    def get_work(self, work_id: str) -> WorkDetailResponse:
        if self.repository is not None:
            work = self.repository.get_work(work_id)
            if work is not None:
                return work
        if work_id in {WORK_LANTINGJI.id, WORK_LANTINGJI.slug}:
            return WORK_LANTINGJI
        raise KeyError(work_id)

    def get_calligrapher(self, calligrapher_id: str) -> CalligrapherDetailResponse:
        if self.repository is not None:
            calligrapher = self.repository.get_calligrapher(calligrapher_id)
            if calligrapher is not None:
                return calligrapher
        if calligrapher_id in {CALLIGRAPHER_WANG.id, CALLIGRAPHER_WANG.slug}:
            return CALLIGRAPHER_WANG
        raise KeyError(calligrapher_id)

    def search_entities(self) -> list[EntityReference]:
        if self.repository is not None:
            entities = self.repository.search_entities()
            if entities:
                return entities
        return [
            EntityReference(
                id=CALLIGRAPHER_WANG.id,
                entity_type="calligrapher",
                name="王羲之 / Wang Xizhi",
                summary=CALLIGRAPHER_WANG.biography,
            ),
            EntityReference(
                id=WORK_LANTINGJI.id,
                entity_type="work",
                name="兰亭集序 / Preface to the Orchid Pavilion",
                summary=WORK_LANTINGJI.description,
            ),
            EntityReference(
                id="term-running-script",
                entity_type="term",
                name="行书 / Running Script",
                summary="常见于王羲之等书家的经典作品。",
            ),
            ERA_JIN,
            STYLE_RUNNING,
        ]
