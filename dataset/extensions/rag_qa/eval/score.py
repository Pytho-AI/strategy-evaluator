"""Exact-answer and citation-id scorer for the RAG QA extension."""
def score(predictions, truth):
    expected = {row["question_id"]: row for row in truth}
    answer = citation = 0
    for row in predictions:
        gold = expected.get(row["question_id"])
        if gold and row.get("answer_value") == gold["answer_value"]:
            answer += 1
        if gold and set(row.get("answer_claim_ids", [])) == set(gold["answer_claim_ids"]):
            citation += 1
    n = max(1, len(expected))
    return {"answer_match": answer / n, "citation_match": citation / n}
