"""P8: shareable extension layers."""
import json
from pathlib import Path
import sys
import zipfile

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dataset"))

REQUIRED = {
    "rag_qa": "RAG Intelligence Service",
    "target_systems": "Target System Object Development",
    "capability": "Capability Assessment Visualization",
    "authority": "Mission Authority Broker",
    "collection_assets": "Dynamic Collection Resource Optimization",
}


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def generated(tmp_path):
    from gen.__main__ import generate
    out = tmp_path / "dataset"
    out.mkdir()
    generate(20260908, out)
    return out


def test_extension_contracts_and_loader(tmp_path):
    from dataset.loader import _load_from

    out = generated(tmp_path)
    shipped = list(REQUIRED) + ["events"]
    for name in shipped:
        root = out / "extensions" / name
        readme = (root / "README.md").read_text()
        assert "CC BY 4.0" in readme
        assert "from dataset import load" in readme
        if name in REQUIRED:
            assert REQUIRED[name] in readme
        for schema_path in sorted((root / "schema").glob("*.json")):
            schema = json.loads(schema_path.read_text())
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema)
            for row in rows(root / "truth" / f"{schema_path.stem}.jsonl"):
                validator.validate(row)

    for name in shipped:
        assert _load_from(out, base=True, extensions=[name], through_batch=0)
    data = _load_from(out, base=True, extensions=shipped, through_batch=0)
    assert {"questions", "systems", "capability_scores", "authority_tiers", "assets", "events"} <= set(data)
    assert set(data["capability_scores"]["world_version"]) == {0}
    with zipfile.ZipFile(out / "strategy-evaluation-dataset-pytho.zip") as archive:
        names = set(archive.namelist())
        assert {"LICENSE", "DATA_CARD.md", "extensions/rag_qa/truth/questions.jsonl", "extensions/events/truth/events.jsonl"} <= names


def test_extension_contents(tmp_path):
    out = generated(tmp_path)
    ext = out / "extensions"

    questions = rows(ext / "rag_qa" / "truth" / "questions.jsonl")
    assert 150 <= len(questions) <= 250
    assert .08 <= sum(q["difficulty"] == "unanswerable" for q in questions) / len(questions) <= .12
    assert sum(q["question_type"] == "doctrinal" for q in questions) >= 10
    assert all(q["answer_claim_ids"] for q in questions if q["difficulty"] not in {"unanswerable", "doctrinal"})
    assert json.loads((ext / "rag_qa" / "eval" / "result.json").read_text())["truth_vs_truth"] == 1.0

    systems = rows(ext / "target_systems" / "truth" / "systems.jsonl")
    characteristics = rows(ext / "target_systems" / "truth" / "target_characteristics.jsonl")
    assert 3 <= len(systems) <= 4
    assert {r["characteristic_type"] for r in characteristics} == {
        "physical", "functional", "cognitive_control_informational", "environmental", "temporal"
    }
    assert all(0 <= r["criticality"] <= 1 for r in rows(ext / "target_systems" / "truth" / "system_links.jsonl"))

    areas = rows(ext / "capability" / "truth" / "capability_areas.jsonl")
    per_actor = {actor: sum(a["actor_id"] == actor for a in areas) for actor in {a["actor_id"] for a in areas}}
    assert all(5 <= count <= 7 for count in per_actor.values())
    scores = rows(ext / "capability" / "truth" / "capability_scores.jsonl")
    assert all(0 <= row["score"] <= 1 for row in scores)
    assert any(len({r["score"] for r in scores if r["area_id"] == area["area_id"]}) > 1 for area in areas)
    assert json.loads((ext / "capability" / "eval" / "result.json").read_text())["truth_vs_truth"] == 1.0

    tiers = rows(ext / "authority" / "truth" / "authority_tiers.jsonl")
    assert [row["name"] for row in tiers] == ["automatic", "J-staff analyst", "J-2/J-5 director", "commander"]
    examples = rows(ext / "authority" / "truth" / "example_decisions.jsonl")
    assert 20 <= len(examples) <= 30
    order = {row["tier_id"]: i for i, row in enumerate(tiers, start=1)}
    assert all(order[row["tier_id"]] >= 3 for row in examples if row["risk_level"] in {"significant", "high"})

    assets = rows(ext / "collection_assets" / "truth" / "assets.jsonl")
    coverage = rows(ext / "collection_assets" / "truth" / "asset_coverage.jsonl")
    assert 6 <= len(assets) <= 10
    assert {row["discipline"] for row in coverage} == {"GEOINT", "SIGINT", "HUMINT", "OSINT", "MASINT"}
    result = json.loads((ext / "collection_assets" / "eval" / "result.json").read_text())
    assert result["truth_vs_truth"] == 1.0 and result["objective_value"] > 0

    events = rows(ext / "events" / "truth" / "events.jsonl")
    assert 500 <= len(events) <= 1000
    assert sum(row["entity_id"] is None for row in events) / len(events) == .4
