def term_recall(answer: str, expected_terms: list[str]) -> float:
    if not expected_terms:
        return 1.0
    answer_lower = answer.lower()
    return sum(term.lower() in answer_lower for term in expected_terms) / len(expected_terms)
