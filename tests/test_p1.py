"""P1 gate: denylist grep clean; every scenario entity has >= 2 facts; change events land in three clusters."""
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DS = ROOT / "dataset"
sys.path.insert(0, str(DS))
sys.path.insert(0, str(ROOT))


def _rows(name):
    return [json.loads(l) for l in (DS / "truth" / f"{name}.jsonl").read_text().splitlines() if l.strip()]


def test_denylist_clean():
    from gen.denylist import run
    assert run(DS) == []


def test_every_entity_has_two_facts():
    ents = _rows("entities")
    facts = _rows("facts")
    cnt = Counter()
    for f in facts:
        cnt[f["subject_id"]] += 1
        if f.get("object_id"):
            cnt[f["object_id"]] += 1
    weak = [e["entity_id"] for e in ents if e["entity_type"] != "organization_role" and not e["entity_id"].startswith("ent_rps") and cnt[e["entity_id"]] < 2]
    assert not weak, weak
    assert 100 <= len(ents) <= 140, len(ents)


def test_change_events_in_three_clusters():
    from gen.scenario_data import T0, BATCH_DAYS
    facts = _rows("facts")
    by_id = {f["fact_id"]: f for f in facts}
    days = []
    for f in facts:
        if f.get("supersedes_fact_id") and f["first_asserted_batch"] > 0:
            days.append((date.fromisoformat(f["valid_from"]) - T0).days)
    assert len(days) >= 12
    clusters = {b: [d for d in days if abs(d - bd) <= 8] for b, bd in BATCH_DAYS.items()}
    assert all(len(v) >= 4 for v in clusters.values()), clusters
    assert sum(len(v) for v in clusters.values()) == len(days)
    # each change event pairs adjoining valid-time intervals
    for f in facts:
        if f.get("supersedes_fact_id"):
            old = by_id[f["supersedes_fact_id"]]
            assert old["valid_to"] is not None
            assert (date.fromisoformat(f["valid_from"]) - date.fromisoformat(old["valid_to"])).days == 1, (old["fact_id"], f["fact_id"])


def test_scenario_md_anchors():
    from gen import scenario_data as S
    md = (DS / "gen" / "scenario.md").read_text()
    for _, _, name, *_ in S.ACTORS + S.POLITIES:
        assert name in md
    for gid, ptype, *_ in S.GUIDANCE:
        assert gid in md
    for b, d in S.BATCH_DAYS.items():
        assert f"+{d}" in md
