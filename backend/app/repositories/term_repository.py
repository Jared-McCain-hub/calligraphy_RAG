from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Term
from app.services.rag_runtime import TermEntry


class TermRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_terms(self) -> list[Term]:
        return self.session.scalars(select(Term)).all()

    def build_term_entries(self) -> list[TermEntry]:
        return [
            TermEntry(
                id=term.id,
                name_cn=term.name_cn,
                name_en=term.name_en or term.name_cn,
                summary=term.definition or term.usage_notes or "",
                aliases=tuple(term.aliases_json or []),
            )
            for term in self.list_terms()
        ]

    def collect_terms(self, *texts: str) -> list[TermEntry]:
        entries = self.build_term_entries()
        haystack = " ".join(text.lower() for text in texts if text)
        matched: list[TermEntry] = []
        seen: set[str] = set()
        for entry in entries:
            candidates = [entry.name_cn.lower(), entry.name_en.lower(), *(alias.lower() for alias in entry.aliases)]
            if any(candidate and candidate in haystack for candidate in candidates):
                if entry.id not in seen:
                    matched.append(entry)
                    seen.add(entry.id)
        return matched
