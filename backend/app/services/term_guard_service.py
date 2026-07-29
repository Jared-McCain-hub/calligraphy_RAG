from __future__ import annotations

from app.repositories.term_repository import TermRepository
from app.services.rag_runtime import RAGRuntime, TermEntry


class TermGuardService:
    """Normalizes important calligraphy terminology in answers."""

    def __init__(self, runtime: RAGRuntime, term_repository: TermRepository | None = None) -> None:
        self.runtime = runtime
        self.term_repository = term_repository

    def collect_terms(self, *texts: str) -> list[TermEntry]:
        if self.term_repository is not None:
            terms = self.term_repository.collect_terms(*texts)
            if terms:
                return terms
        return self.runtime.build_glossary([text for text in texts if text])

    def normalize_answer(self, answer: str, *, language: str, terms: list[TermEntry]) -> str:
        if not terms:
            return answer

        glossary = self._build_glossary_line(language=language, terms=terms)
        if glossary and glossary not in answer:
            return f"{answer}\n\n{glossary}"
        return answer

    @staticmethod
    def _build_glossary_line(*, language: str, terms: list[TermEntry]) -> str:
        rendered_terms = [f"{term.name_cn} = {term.name_en}" for term in terms[:4]]
        if not rendered_terms:
            return ""

        if language == "en-US":
            return f"Standard terminology: {'; '.join(rendered_terms)}."
        if language == "bilingual":
            return f"术语对照 / Terminology: {'; '.join(rendered_terms)}。"
        return f"术语对照：{'；'.join(rendered_terms)}。"
