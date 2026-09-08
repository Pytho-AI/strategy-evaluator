"""Denylist grep (v1 P1 gate): scenario content must not name real nations, alliances, commands or
weapon designators. Scans truth entity names/aliases/descriptions, gen/scenario.md and every
rendered document under corpus/ and injects/. Words in the doctrine glossaries that are also
country names (e.g. 'US') are handled by the acronym rule, not here."""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASET = HERE.parent


def load(path: Path = HERE / "denylist.txt") -> list[re.Pattern]:
    pats = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("regex:"):
            pats.append(re.compile(line[6:]))
        else:
            pats.append(re.compile(rf"(?<![\w-]){re.escape(line)}(?![\w-])", re.I))
    return pats


_ACR: set[str] | None = None


def _glossary_acronyms() -> set[str]:
    global _ACR
    if _ACR is None:
        import yaml
        _ACR = set(yaml.safe_load((HERE / "styles" / "acronyms.yml").read_text())["acronyms"])
    return _ACR


def scan_text(text: str, pats: list[re.Pattern]) -> list[str]:
    """Designator-pattern hits that are doctrine glossary acronyms (J-2, C2, ...) are not hits."""
    hits = []
    for p in pats:
        for m in p.finditer(text):
            tok = m.group(0)
            if tok in _glossary_acronyms() or re.match(r"^[IVX]+-\d+$", tok):  # J-2, C2; Fig. IV-9
                continue
            hits.append(m.group(0))
            break
    return hits


def run(dataset_dir: Path = DATASET) -> list[tuple[str, list[str]]]:
    import json

    pats = load()
    out = []
    ents = dataset_dir / "truth" / "entities.jsonl"
    if ents.exists():
        for line in ents.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            text = " ".join([e["canonical_name"], *e.get("aliases", []), e.get("description") or ""])
            h = scan_text(text, pats)
            if h:
                out.append((f"entities:{e['entity_id']}", h))
    for f in [dataset_dir / "gen" / "scenario.md"] + sorted((dataset_dir / "corpus").rglob("*")) + sorted((dataset_dir / "injects").rglob("*")):
        if f.is_file() and f.suffix in (".md", ".txt", ".csv"):
            h = scan_text(f.read_text(encoding="utf-8"), pats)
            if h:
                out.append((str(f.relative_to(dataset_dir)), h))
    return out


if __name__ == "__main__":
    hits = run()
    for k, h in hits:
        print(k, h)
    print("clean" if not hits else f"{len(hits)} files with denylist hits")
    raise SystemExit(1 if hits else 0)
