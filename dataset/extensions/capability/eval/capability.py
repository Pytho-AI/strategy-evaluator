"""Reference capability aggregation."""
def aggregate(values, aggregation):
    if aggregation == "min":
        return min(value for value, _ in values)
    if aggregation == "sum":
        return min(1.0, sum(value * weight for value, weight in values))
    return sum(value * weight for value, weight in values) / sum(weight for _, weight in values)
