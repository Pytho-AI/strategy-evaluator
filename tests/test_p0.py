"""P0 gate: all schemas load; RPS instantiation validates end-to-end incl. validity tests."""
import json
import subprocess
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DS = ROOT / "dataset"
sys.path.insert(0, str(DS))
sys.path.insert(0, str(ROOT))


def test_schemas_export_and_load():
    from gen.export_schema import export
    paths = export()
    assert len(paths) >= 29
    for p in paths:
        s = json.loads(p.read_text())
        jsonschema.Draft202012Validator.check_schema(s)


def test_rps_end_to_end(tmp_path):
    from gen.__main__ import generate
    from gen import validate
    from gen.context import T0
    from eval.tables import load_dir

    tmp = tmp_path / "dataset"
    tmp.mkdir()
    (tmp / "gen").symlink_to(DS / "gen")
    ctx = generate(20260908, tmp, only=["rps"])
    tables = load_dir(tmp / "truth")
    assert validate.schema_load(tables).passed
    # every row also validates against the exported JSON Schema
    from gen.models import TABLES
    for t in TABLES:
        schema = t.model.model_json_schema()
        for r in tables[t.name]:
            jsonschema.validate(r, schema)
    res = validate.run_all(tables, tmp, T0, 0)
    failed = [r for r in res if not r.passed]
    assert not failed, "\n".join(f"{r.id}: {r.detail}" for r in failed)
    s = {x["strategy_id"]: x for x in tables["strategies"]}
    uni = s["str_rps_p1_uniform"]
    assert abs(uni["value"]) < 1e-12
    assert uni["status"] == "valid"
    assert all(v["pass"] for v in uni["validity"].values())
    a = {x["assumption_id"]: x for x in tables["assumptions"]}
    assert a["asm_rps_p1_uniform_k0"]["status"] == "holds"
    assert a["asm_rps_p1_uniform_k0"]["p_holds"] == 0.97
    assert a["asm_rps_p1_paper_k0"]["evpi"] > 0  # learning P2's bias would change the best decision
    assert a["asm_rps_p1_paper_k0"]["sensitivity"] < 0


def test_every_enum_cites_a_source_and_appears_in_schema_md():
    from enum import Enum
    from gen import vocab as V
    enums = [n for n, o in vars(V).items() if isinstance(o, type) and issubclass(o, Enum) and o not in (V.StrEnum, Enum) and n != "StrEnum"]
    missing = [n for n in enums if n not in V.SOURCE]
    assert not missing, f"enums without doctrinal source: {missing}"
    md = (DS / "schema" / "SCHEMA.md").read_text()
    assert all(f"`{n}`" in md for n in enums)


def test_extracts_verbatim():
    from gen.check_extracts import main
    assert main() == 0
