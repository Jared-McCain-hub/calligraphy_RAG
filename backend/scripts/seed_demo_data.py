from __future__ import annotations

from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Calligrapher,
    Era,
    Style,
    Term,
    Work,
    WorkAuthenticity,
    WorkTermLink,
)


def _get_or_create_by_slug(session: Session, model: type, slug: str, **values):
    instance = session.scalar(select(model).where(model.slug == slug))
    if instance:
        for key, value in values.items():
            setattr(instance, key, value)
        return instance

    instance = model(slug=slug, **values)
    session.add(instance)
    session.flush()
    return instance


def seed_demo_data(session: Session) -> None:
    era = _get_or_create_by_slug(
        session,
        Era,
        slug="eastern-jin",
        name_cn="东晋",
        name_en="Eastern Jin",
        start_year=317,
        end_year=420,
        summary="中国书法史上的关键时代之一。",
        aliases_json=[],
        metadata_json={"seed": True},
    )

    style = _get_or_create_by_slug(
        session,
        Style,
        slug="running-script",
        name_cn="行书",
        name_en="Running Script",
        category="script",
        description="介于楷书与草书之间的经典书体。",
        aliases_json=[],
        metadata_json={"seed": True},
    )

    calligrapher = _get_or_create_by_slug(
        session,
        Calligrapher,
        slug="wang-xizhi",
        name_cn="王羲之",
        name_en="Wang Xizhi",
        courtesy_name="逸少",
        art_name=None,
        aliases_json=[],
        era_id=era.id,
        primary_style_id=style.id,
        birth_year=303,
        death_year=361,
        hometown="琅琊临沂",
        biography="东晋书法家，被尊为书圣。",
        achievements="对行书体系的成熟具有深远影响。",
        source="seed",
        metadata_json={"seed": True},
    )

    work = _get_or_create_by_slug(
        session,
        Work,
        slug="lantingji-xu",
        title_cn="兰亭集序",
        title_en="Preface to the Orchid Pavilion",
        calligrapher_id=calligrapher.id,
        era_id=era.id,
        style_id=style.id,
        authenticity=WorkAuthenticity.AUTHENTIC,
        creation_period="东晋永和九年",
        material="纸本（摹本流传）",
        dimensions=None,
        current_collection="故宫博物院藏唐摹本系统",
        excerpt_text="永和九年，岁在癸丑，暮春之初，会于会稽山阴之兰亭……",
        description="被普遍视为行书传统中的代表性作品。",
        image_url=None,
        source="seed",
        metadata_json={"seed": True},
    )

    term = _get_or_create_by_slug(
        session,
        Term,
        slug="running-script-term",
        name_cn="行书",
        name_en="Running Script",
        category="style",
        aliases_json=[],
        definition="介于楷书与草书之间，兼顾辨识度与书写流动性的书体。",
        usage_notes="常用于介绍王羲之及后续帖学系统作品。",
        source="seed",
        metadata_json={"seed": True},
    )

    link = session.scalar(
        select(WorkTermLink).where(
            WorkTermLink.work_id == work.id,
            WorkTermLink.term_id == term.id,
        )
    )
    if not link:
        session.add(
            WorkTermLink(
                work_id=work.id,
                term_id=term.id,
                relation_note="seed relation",
            )
        )

    session.commit()


if __name__ == "__main__":
    from app.core.database import get_session_factory

    session = get_session_factory()()
    try:
        seed_demo_data(session)
        print("Demo seed data inserted or updated.")
    finally:
        session.close()
