"""Shared rendering helpers: markings, acronym glossary footer, span location, date formats."""
from __future__ import annotations

from datetime import date

CAVEAT = "SYNTHETIC DATA — FOR EXERCISE AND DEVELOPMENT USE ONLY. NOT A REAL ASSESSMENT."
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MON3 = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def product_header() -> str:
    return f"UNCLASSIFIED\n{CAVEAT}\n"


def product_footer(acronyms_used: list[str]) -> str:
    gl = ", ".join(acronyms_used) if acronyms_used else "none"
    return f"Acronyms used: {gl}\nUNCLASSIFIED\n"


def fmt_date(d: date) -> str:
    """DD Month YYYY (v2 §1A.3)."""
    return f"{d.day:02d} {MONTHS[d.month - 1]} {d.year}"


def fmt_dtg(d: date, hhmm: str = "1200") -> str:
    """DDHHMMZ MON YY (v2 §1A.3)."""
    return f"{d.day:02d}{hhmm}Z {MON3[d.month - 1]} {d.year % 100:02d}"


def locate_span(text: str, needle: str) -> tuple[int, int]:
    i = text.find(needle)
    if i < 0:
        raise ValueError(f"evidence sentence not found in text: {needle!r}")
    return i, i + len(needle)
