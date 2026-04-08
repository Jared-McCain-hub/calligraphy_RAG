from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Calligrapher, Era, Style, Term, Work
from app.schemas.catalog import CalligrapherDetailResponse, WorkDetailResponse
from app.schemas.common import EntityReference


class CatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_work(self, identifier: str) -> WorkDetailResponse | None:
        stmt = (
            select(Work)
            .options(
                selectinload(Work.calligrapher),
                selectinload(Work.era),
                selectinload(Work.style),
                selectinload(Work.terms),
            )
            .where(or_(Work.id == identifier, Work.slug == identifier))
        )
        work = self.session.scalar(stmt)
        if work is None:
            return None
        return self._to_work_detail(work)

    def get_calligrapher(self, identifier: str) -> CalligrapherDetailResponse | None:
        stmt = (
            select(Calligrapher)
            .options(
                selectinload(Calligrapher.era),
                selectinload(Calligrapher.primary_style),
                selectinload(Calligrapher.works),
            )
            .where(or_(Calligrapher.id == identifier, Calligrapher.slug == identifier))
        )
        calligrapher = self.session.scalar(stmt)
        if calligrapher is None:
            return None
        return self._to_calligrapher_detail(calligrapher)

    def search_entities(self) -> list[EntityReference]:
        entities: list[EntityReference] = []

        calligraphers = self.session.scalars(select(Calligrapher)).all()
        works = self.session.scalars(select(Work)).all()
        terms = self.session.scalars(select(Term)).all()
        eras = self.session.scalars(select(Era)).all()
        styles = self.session.scalars(select(Style)).all()

        entities.extend(
            EntityReference(
                id=calligrapher.id,
                entity_type="calligrapher",
                name=self._bilingual_name(calligrapher.name_cn, calligrapher.name_en),
                summary=calligrapher.biography,
            )
            for calligrapher in calligraphers
        )
        entities.extend(
            EntityReference(
                id=work.id,
                entity_type="work",
                name=self._bilingual_name(work.title_cn, work.title_en),
                summary=work.description,
            )
            for work in works
        )
        entities.extend(
            EntityReference(
                id=term.id,
                entity_type="term",
                name=self._bilingual_name(term.name_cn, term.name_en),
                summary=term.definition or term.usage_notes,
            )
            for term in terms
        )
        entities.extend(
            EntityReference(
                id=era.id,
                entity_type="era",
                name=self._bilingual_name(era.name_cn, era.name_en),
                summary=era.summary,
            )
            for era in eras
        )
        entities.extend(
            EntityReference(
                id=style.id,
                entity_type="style",
                name=self._bilingual_name(style.name_cn, style.name_en),
                summary=style.description,
            )
            for style in styles
        )
        return entities

    def _to_work_detail(self, work: Work) -> WorkDetailResponse:
        return WorkDetailResponse(
            id=work.id,
            slug=work.slug,
            title_cn=work.title_cn,
            title_en=work.title_en,
            description=work.description,
            excerpt_text=work.excerpt_text,
            image_url=work.image_url,
            authenticity=work.authenticity.value,
            creation_period=work.creation_period,
            material=work.material,
            dimensions=work.dimensions,
            current_collection=work.current_collection,
            era=self._entity_ref("era", work.era.name_cn, work.era.name_en, work.era.summary, work.era.id)
            if work.era
            else None,
            style=self._entity_ref(
                "style",
                work.style.name_cn,
                work.style.name_en,
                work.style.description,
                work.style.id,
            )
            if work.style
            else None,
            calligrapher=self._entity_ref(
                "calligrapher",
                work.calligrapher.name_cn,
                work.calligrapher.name_en,
                work.calligrapher.biography,
                work.calligrapher.id,
            )
            if work.calligrapher
            else None,
            related_terms=[
                self._entity_ref("term", term.name_cn, term.name_en, term.definition or term.usage_notes, term.id)
                for term in work.terms
            ],
        )

    def _to_calligrapher_detail(self, calligrapher: Calligrapher) -> CalligrapherDetailResponse:
        representative_works = sorted(
            calligrapher.works,
            key=lambda item: item.created_at or item.updated_at,
            reverse=True,
        )[:5]
        return CalligrapherDetailResponse(
            id=calligrapher.id,
            slug=calligrapher.slug,
            name_cn=calligrapher.name_cn,
            name_en=calligrapher.name_en,
            biography=calligrapher.biography,
            hometown=calligrapher.hometown,
            birth_year=calligrapher.birth_year,
            death_year=calligrapher.death_year,
            era=self._entity_ref(
                "era",
                calligrapher.era.name_cn,
                calligrapher.era.name_en,
                calligrapher.era.summary,
                calligrapher.era.id,
            )
            if calligrapher.era
            else None,
            primary_style=self._entity_ref(
                "style",
                calligrapher.primary_style.name_cn,
                calligrapher.primary_style.name_en,
                calligrapher.primary_style.description,
                calligrapher.primary_style.id,
            )
            if calligrapher.primary_style
            else None,
            representative_works=[
                self._entity_ref(
                    "work",
                    work.title_cn,
                    work.title_en,
                    work.description,
                    work.id,
                )
                for work in representative_works
            ],
        )

    @staticmethod
    def _entity_ref(
        entity_type: str,
        name_cn: str,
        name_en: str | None,
        summary: str | None,
        identifier: str,
    ) -> EntityReference:
        return EntityReference(
            id=identifier,
            entity_type=entity_type,
            name=CatalogRepository._bilingual_name(name_cn, name_en),
            summary=summary,
        )

    @staticmethod
    def _bilingual_name(name_cn: str, name_en: str | None) -> str:
        return f"{name_cn} / {name_en}" if name_en else name_cn
