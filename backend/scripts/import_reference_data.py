from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.models  # noqa: F401
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import create_all_tables, create_database_if_not_exists, get_session_factory
from app.models import Era, Style, Term, Work, WorkAuthenticity, WorkTermLink, Calligrapher

DATA_DIR = BACKEND_ROOT / "data"

ERA_PRESETS: dict[str, dict[str, Any]] = {
    "东晋": {
        "slug": "eastern-jin",
        "name_en": "Eastern Jin",
        "start_year": 317,
        "end_year": 420,
        "summary": "东晋时期书法艺术高度成熟，王羲之、王献之等推动了行书与今草的发展。",
    },
    "唐": {
        "slug": "tang",
        "name_en": "Tang",
        "start_year": 618,
        "end_year": 907,
        "summary": "唐代是楷书法度与碑刻传统高度发展的关键时期。",
    },
    "隋唐": {
        "slug": "sui-tang",
        "name_en": "Sui-Tang",
        "start_year": 581,
        "end_year": 907,
        "summary": "隋唐时期承前启后，推动了楷书法度的成熟与普及。",
    },
    "宋元": {
        "slug": "song-yuan",
        "name_en": "Song-Yuan",
        "start_year": 960,
        "end_year": 1368,
        "summary": "宋元时期文人书风兴盛，复古与创新并行。",
    },
    "元": {
        "slug": "yuan",
        "name_en": "Yuan",
        "start_year": 1271,
        "end_year": 1368,
        "summary": "元代书法重视复古取法，赵孟頫影响尤大。",
    },
}


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _get_or_create_by_slug(session: Session, model: type, slug: str, **values: Any):
    instance = session.scalar(select(model).where(model.slug == slug))
    if instance:
        for key, value in values.items():
            setattr(instance, key, value)
        return instance

    instance = model(slug=slug, **values)
    session.add(instance)
    session.flush()
    return instance


def seed_reference_data(session: Session, *, data_dir: Path = DATA_DIR) -> dict[str, int]:
    terms_data = load_json(data_dir / "terms.json")
    calligraphers_data = load_json(data_dir / "calligraphers.json")
    works_data = load_json(data_dir / "works.json")

    created_counts = {
        "eras": 0,
        "styles": 0,
        "terms": 0,
        "calligraphers": 0,
        "works": 0,
        "work_term_links": 0,
    }

    era_by_name: dict[str, Era] = {}
    style_by_name: dict[str, Style] = {}
    term_by_name: dict[str, Term] = {}
    calligrapher_by_name: dict[str, Calligrapher] = {}
    work_by_title: dict[str, Work] = {}

    all_era_names = {
        *(item.get("era", "") for item in calligraphers_data),
        *(item.get("era", "") for item in works_data),
    }
    for era_name in sorted(name for name in all_era_names if name):
        preset = ERA_PRESETS.get(
            era_name,
            {
                "slug": era_name,
                "name_en": None,
                "start_year": None,
                "end_year": None,
                "summary": None,
            },
        )
        era = _get_or_create_by_slug(
            session,
            Era,
            slug=preset["slug"],
            name_cn=era_name,
            name_en=preset["name_en"],
            start_year=preset["start_year"],
            end_year=preset["end_year"],
            summary=preset["summary"],
            aliases_json=[],
            metadata_json={"seed": True},
        )
        era_by_name[era_name] = era
        created_counts["eras"] += 1

    for item in terms_data:
        term = _get_or_create_by_slug(
            session,
            Term,
            slug=item["slug"],
            name_cn=item["name_cn"],
            name_en=item.get("name_en"),
            category=item.get("category"),
            aliases_json=item.get("aliases", []),
            definition=item.get("definition"),
            usage_notes=item.get("usage_notes"),
            source=item.get("source"),
            metadata_json={
                "seed": True,
                "source_url": item.get("source_url"),
            },
        )
        term_by_name[item["name_cn"]] = term
        created_counts["terms"] += 1

        if item.get("category") in {"style", "script"}:
            style = _get_or_create_by_slug(
                session,
                Style,
                slug=item["slug"],
                name_cn=item["name_cn"],
                name_en=item.get("name_en"),
                category=item.get("category"),
                description=item.get("definition"),
                aliases_json=item.get("aliases", []),
                metadata_json={
                    "seed": True,
                    "source_url": item.get("source_url"),
                },
            )
            style_by_name[item["name_cn"]] = style
            created_counts["styles"] += 1

    for item in calligraphers_data:
        calligrapher = _get_or_create_by_slug(
            session,
            Calligrapher,
            slug=item["slug"],
            name_cn=item["name_cn"],
            name_en=item.get("name_en"),
            courtesy_name=item.get("courtesy_name") or None,
            art_name=item.get("art_name") or None,
            aliases_json=item.get("aliases", []),
            era_id=era_by_name[item["era"]].id if item.get("era") in era_by_name else None,
            primary_style_id=(
                style_by_name[item["primary_style"]].id
                if item.get("primary_style") in style_by_name
                else None
            ),
            birth_year=item.get("birth_year"),
            death_year=item.get("death_year"),
            hometown=item.get("hometown"),
            biography=item.get("biography"),
            achievements=item.get("achievements"),
            source=item.get("source"),
            metadata_json={
                "seed": True,
                "source_url": item.get("source_url"),
                "representative_works": item.get("representative_works", []),
            },
        )
        calligrapher_by_name[item["name_cn"]] = calligrapher
        created_counts["calligraphers"] += 1

    for item in works_data:
        authenticity = WorkAuthenticity(item.get("authenticity", WorkAuthenticity.UNKNOWN.value))
        work = _get_or_create_by_slug(
            session,
            Work,
            slug=item["slug"],
            title_cn=item["title_cn"],
            title_en=item.get("title_en"),
            calligrapher_id=(
                calligrapher_by_name[item["calligrapher"]].id
                if item.get("calligrapher") in calligrapher_by_name
                else None
            ),
            era_id=era_by_name[item["era"]].id if item.get("era") in era_by_name else None,
            style_id=style_by_name[item["style"]].id if item.get("style") in style_by_name else None,
            authenticity=authenticity,
            creation_period=item.get("creation_period"),
            material=item.get("material"),
            dimensions=item.get("dimensions") or None,
            current_collection=item.get("current_collection"),
            excerpt_text=item.get("excerpt_text") or None,
            description=item.get("description"),
            image_url=item.get("image_url") or None,
            source=item.get("source"),
            metadata_json={
                "seed": True,
                "aliases": item.get("aliases", []),
                "significance": item.get("significance"),
                "source_url": item.get("source_url"),
            },
        )
        work_by_title[item["title_cn"]] = work
        created_counts["works"] += 1

    session.flush()

    for item in works_data:
        work = work_by_title[item["title_cn"]]
        candidate_term_names = {item.get("style")}
        candidate_term_names.update(item.get("aliases", []))
        for term_name in sorted(name for name in candidate_term_names if name in term_by_name):
            existing_link = session.scalar(
                select(WorkTermLink).where(
                    WorkTermLink.work_id == work.id,
                    WorkTermLink.term_id == term_by_name[term_name].id,
                )
            )
            if existing_link is None:
                session.add(
                    WorkTermLink(
                        work_id=work.id,
                        term_id=term_by_name[term_name].id,
                        relation_note="reference-seed relation",
                    )
                )
                created_counts["work_term_links"] += 1

    session.commit()
    return created_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Import structured calligraphy reference data.")
    parser.add_argument(
        "--ensure-db",
        action="store_true",
        help="Create the MySQL database and tables before importing reference data.",
    )
    args = parser.parse_args()

    if args.ensure_db:
        create_database_if_not_exists()
        create_all_tables()

    session = get_session_factory()()
    try:
        counts = seed_reference_data(session)
    finally:
        session.close()

    print("Reference data imported.")
    for key, value in counts.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
