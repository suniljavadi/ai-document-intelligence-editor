import re
from app.schemas import ActionItem, Contradiction, DocumentAnalysisSchema, EditSuggestion, MissingInformation, QuestionAnswer, Risk


class MockLLMProvider:
    def edit(self, text: str, operation: str) -> EditSuggestion:
        transformations = {
            "professional": text.replace("many problems", "several operational issues").replace("it was delayed", "the schedule was delayed"),
            "improve": text.strip().capitalize(),
            "shorten": text.split(".")[0].strip() + ".",
            "expand": text.strip() + " The team should document the cause and next steps.",
            "bullets": "\n".join(f"- {part.strip()}" for part in text.split(".") if part.strip()),
            "summarize": text[:160].strip() + ("..." if len(text) > 160 else ""),
            "heading": "Document Summary",
            "explain": f"This passage states: {text.strip()}",
        }
        suggestion = transformations.get(operation, text)
        return EditSuggestion(original_text=text, suggested_text=suggestion, operation=operation, explanation=f"Applied the {operation} transformation without overwriting the original text.")

    def answer(self, question: str, chunks: list[tuple[int, str, str | None, int | None]]) -> QuestionAnswer:
        if not chunks:
            return QuestionAnswer(answer="Insufficient evidence in the available documents.", confidence="low")
        question_terms = set(re.findall(r"\w+", question.lower()))
        ranked = sorted(chunks, key=lambda item: len(question_terms & set(re.findall(r"\w+", item[1].lower()))), reverse=True)
        best = ranked[0]
        quote = best[1][:500]
        return QuestionAnswer(answer=f"Based on the document, {quote}", evidence=[quote], citations=[{"chunk_id": best[0], "source": "Uploaded document", "section": best[2], "page_number": best[3], "quote": quote}], confidence="medium")


def analyze_text(text: str) -> DocumentAnalysisSchema:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    lower = text.lower()
    decisions = [s for s in sentences if any(x in s.lower() for x in [" will use ", " selected ", " decided ", " approved "])]
    risks = [Risk(category="operational", description=s, evidence=s, source="Document text") for s in sentences if any(x in s.lower() for x in ["risk", "delay", "failure", "issue", "blocked"])]
    actions = [ActionItem(action=s, evidence=s, source="Document text") for s in sentences if any(x in s.lower() for x in ["must ", "shall ", "owner:", "action:", "prepare ", "complete "])]
    missing = []
    if "rollback" not in lower:
        missing.append(MissingInformation(missing="Rollback procedure", why_it_matters="A recovery path is important if deployment fails.", evidence="No rollback procedure was found in the document."))
    contradictions = []
    dates = re.findall(r"(?:March|April|May|June|July|August|September|October|November|December|January|February)\s+\d{1,2}", text, re.I)
    if len(set(map(str.lower, dates))) > 1 and "migration" in lower:
        contradictions.append(Contradiction(statement_a=dates[0], statement_b=dates[1], assessment="Potential contradiction", explanation="The document mentions multiple dates for a migration-related activity; confirm whether they represent separate stages."))
    return DocumentAnalysisSchema(executive_summary=" ".join(sentences[:3]) or "The document contains no extractable text.", key_points=sentences[:8], decisions=decisions, action_items=actions, risks=risks, missing_information=missing, contradictions=contradictions)
