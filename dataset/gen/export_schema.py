"""Export one JSON Schema per table into schema/ from the pydantic models (the contract)."""
from __future__ import annotations

import json
from pathlib import Path

from gen.models import MANIFEST_MODEL, TABLES

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schema"


def export(schema_dir: Path = SCHEMA_DIR) -> list[Path]:
    schema_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for t in TABLES:
        s = t.model.model_json_schema()
        s["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        s["$id"] = f"https://claimgraph-dataset/schema/{t.name}.json"
        s["title"] = t.name
        s["description"] = t.purpose
        s["x-primary-key"] = t.pk
        s["x-foreign-keys"] = t.fks
        s["x-polymorphic-foreign-keys"] = t.polymorphic_fks
        s["x-computed"] = t.computed
        s["x-truth-only"] = t.truth_only
        p = schema_dir / f"{t.name}.json"
        p.write_text(json.dumps(s, indent=2, sort_keys=False) + "\n")
        written.append(p)
    m = MANIFEST_MODEL.model_json_schema()
    m["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    m["title"] = "inject_manifest"
    m["description"] = "injects/batch_n/manifest.json: documents, change events and COMPUTED expected effects of one inject batch."
    p = schema_dir / "inject_manifest.json"
    p.write_text(json.dumps(m, indent=2) + "\n")
    written.append(p)
    return written


if __name__ == "__main__":
    for p in export():
        print(p)
