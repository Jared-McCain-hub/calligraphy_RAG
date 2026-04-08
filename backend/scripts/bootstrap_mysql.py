from __future__ import annotations

import argparse
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.models  # noqa: F401
from app.core.config import settings
from app.core.database import create_all_tables, create_database_if_not_exists
from scripts.import_reference_data import seed_reference_data
from scripts.seed_rag_knowledge import seed_reference_rag_knowledge
from scripts.seed_demo_data import seed_demo_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap MySQL database for the backend.")
    parser.add_argument(
        "--with-seed",
        action="store_true",
        help="Insert or update demo seed data after tables are created.",
    )
    parser.add_argument(
        "--with-reference-data",
        action="store_true",
        help="Import structured reference data from backend/data/*.json after tables are created.",
    )
    parser.add_argument(
        "--with-rag-knowledge",
        action="store_true",
        help="Generate initial knowledge_documents and knowledge_chunks from imported reference entities.",
    )
    args = parser.parse_args()

    create_database_if_not_exists()
    create_all_tables()
    print(f"MySQL database ready: {settings.db_name}")

    if args.with_seed:
        from app.core.database import get_session_factory

        session = get_session_factory()()
        try:
            seed_demo_data(session)
        finally:
            session.close()
        print("Demo seed data inserted.")

    if args.with_reference_data:
        from app.core.database import get_session_factory

        session = get_session_factory()()
        try:
            counts = seed_reference_data(session)
        finally:
            session.close()
        print(f"Reference data imported: {counts}")

    if args.with_rag_knowledge:
        from app.core.database import get_session_factory

        session = get_session_factory()()
        try:
            counts = seed_reference_rag_knowledge(session)
        finally:
            session.close()
        print(f"Reference RAG knowledge seeded: {counts}")


if __name__ == "__main__":
    main()
