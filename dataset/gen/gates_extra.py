"""P8 extension gates appended to ``python -m gen check``."""
from __future__ import annotations

import json

from jsonschema import Draft202012Validator

from gen.io import read_jsonl
from gen.validate import Result


EXTENSIONS = ["rag_qa", "target_systems", "capability", "authority", "collection_assets", "events"]


def run(dataset_dir, _tables):
    results = []
    for name in EXTENSIONS:
        root = dataset_dir / "extensions" / name
        errors = []
        if not root.is_dir():
            results.append(Result(f"ext:{name}", False, "extension directory missing"))
            continue
        for path in sorted((root / "schema").glob("*.json")):
            schema = json.loads(path.read_text())
            try:
                Draft202012Validator.check_schema(schema)
                validator = Draft202012Validator(schema)
                for row in read_jsonl(root / "truth" / f"{path.stem}.jsonl"):
                    validator.validate(row)
            except Exception as exc:
                errors.append(f"{path.stem}: {exc.message if hasattr(exc, 'message') else exc}")
        result_path = root / "eval" / "result.json"
        if result_path.exists() and json.loads(result_path.read_text()).get("truth_vs_truth") != 1.0:
            errors.append("eval truth_vs_truth is not 1.0")
        readme = (root / "README.md").read_text() if (root / "README.md").exists() else ""
        if "from dataset import load" not in readme or "CC BY 4.0" not in readme:
            errors.append("README lacks starter query or license")
        results.append(Result(f"ext:{name}", not errors,
                              "schemas, starter query, license, and eval pass" if not errors else "; ".join(errors[:3])))
    return results
