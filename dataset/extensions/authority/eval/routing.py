"""Reference authority routing."""
ORDER = {"low": 1, "moderate": 2, "significant": 3, "high": 4}
def route(risk_level):
    return f"tier_{ORDER[risk_level]}"
