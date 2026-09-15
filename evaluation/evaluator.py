import json
from pathlib import Path
from app.ai import MockLLMProvider
from app.document_processing.parsers import DocumentParser
from evaluation.metrics import term_recall


def run() -> dict:
    parser = DocumentParser()
    provider = MockLLMProvider()
    scores = []
    root = Path(__file__).parent
    for item in json.loads((root / "datasets" / "questions.json").read_text()):
        path = Path("data/sample_documents") / item["document"]
        text = parser.parse(item["document"], path.read_bytes())
        answer = provider.answer(item["question"], [(1, text, None, None)])
        scores.append(term_recall(answer.answer, item["expected_terms"]))
    return {"cases": len(scores), "term_recall": sum(scores) / len(scores) if scores else 0.0, "note": "Synthetic smoke evaluation, not a quality guarantee."}
