"""Entity-resolution accuracy for events with withheld observed IDs."""
def score(predictions, truth):
    expected = {row["event_id"]: row["truth_entity_id"] for row in truth}
    return sum(expected.get(row["event_id"]) == row.get("entity_id") for row in predictions) / max(1, len(expected))
