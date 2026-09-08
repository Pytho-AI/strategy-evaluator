"""Invariants 1-20 (v1 §3, v2 §3) over the truth tables and the rendered corpus. Each returns
(id, passed, detail). `run_all` is what `python -m gen check` prints."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

from eval import style_check
from eval.jram import parse_risk_statement, topological_order
from eval.engine import recompute
from gen.models import TABLES, TABLE_BY_NAME

PRODUCT_ONLY = {"risk_context", "collection_plan", "coa_statement", "guidance"}  # exempt from 'yields >= 1 claim'


@dataclass
class Result:
    id: str
    passed: bool
    detail: str


def _ids(tables, table, col):
    return {r[col] for r in tables[table]}


def inv01_referential_integrity(tables, **_) -> Result:
    bad = []
    for t in TABLES:
        for col, ref in t.fks.items():
            rt, rc = ref.split(".")
            valid = _ids(tables, rt, rc)
            for r in tables[t.name]:
                v = r.get(col)
                if v is not None and v not in valid:
                    bad.append(f"{t.name}.{col}={v}")
    poly = {"claim": ("claims", "claim_id"), "assumption": ("assumptions", "assumption_id"), "strategy": ("strategies", "strategy_id"),
            "action": ("actions", "action_id"), "objective": ("objectives", "objective_id"), "problem_set": ("problem_sets", "problem_set_id"),
            "harmful_event": ("harmful_events", "he_id")}
    for d in tables["dependencies"]:
        for typ, nid in ((d["from_type"], d["from_id"]), (d["to_type"], d["to_id"])):
            rt, rc = poly[typ]
            if nid not in _ids(tables, rt, rc):
                bad.append(f"dependencies.{typ}={nid}")
    list_fks = [
        ("guidance", "objective_ids", "objectives", "objective_id"), ("problem_sets", "thing_of_value_ids", "objectives", "objective_id"),
        ("strategies", "theory_of_victory", "dependencies", "edge_id"), ("strategies", "task_org", "entities", "entity_id"),
        ("strategies", "mitigates_he_ids", "harmful_events", "he_id"), ("policy_rules", "rationale_claim_ids", "claims", "claim_id"),
        ("dependencies", "evidence_claim_ids", "claims", "claim_id"), ("escalation_edges", "evidence_claim_ids", "claims", "claim_id"),
        ("decision_points", "branch_rule_ids", "policy_rules", "rule_id"), ("pirs", "decision_point_ids", "decision_points", "dp_id"),
        ("games", "actor_ids", "entities", "entity_id"), ("harmful_events", "posture_subject_ids", "entities", "entity_id"),
        ("risk_assessments", "active_driver_ids", "risk_drivers", "driver_id"), ("problem_set_assessments", "he_ids", "harmful_events", "he_id"),
    ]
    for tn, col, rt, rc in list_fks:
        valid = _ids(tables, rt, rc)
        for r in tables[tn]:
            for v in r.get(col) or []:
                if v not in valid:
                    bad.append(f"{tn}.{col}∋{v}")
    sids = _ids(tables, "strategies", "strategy_id")
    for om in tables["opponent_models"]:
        for m in om["distribution"]:
            if m["strategy_id"] not in sids:
                bad.append(f"opponent_models.distribution∋{m['strategy_id']}")
    rids = _ids(tables, "resources", "resource_id")
    for a in tables["actions"]:
        for res in a.get("cost", {}):
            if res not in rids:
                bad.append(f"actions.cost∋{res}")
    # PK uniqueness
    for t in TABLES:
        seen = set()
        for r in tables[t.name]:
            key = tuple(r[c] for c in t.pk)
            if key in seen:
                bad.append(f"duplicate PK {t.name}{key}")
            seen.add(key)
    return Result("01", not bad, "referential integrity and PK uniqueness" if not bad else f"{len(bad)} violations: {bad[:8]}")


def inv02_spans(tables, dataset_dir: Path, **_) -> Result:
    src = {s["source_id"]: s for s in tables["sources"]}
    ent = {e["entity_id"]: e for e in tables["entities"]}
    texts = {}
    bad = []
    for c in tables["claims"]:
        s = src[c["source_id"]]
        if s["path"] not in texts:
            texts[s["path"]] = (Path(dataset_dir) / s["path"]).read_text(encoding="utf-8")
        text = texts[s["path"]]
        if not (0 <= c["span_start"] < c["span_end"] <= len(text)):
            bad.append(f"{c['claim_id']}: span outside text")
            continue
        span = text[c["span_start"]:c["span_end"]].lower()
        e = ent[c["subject_id"]]
        names = [e["canonical_name"]] + e.get("aliases", [])
        mentions = any(n.lower() in span for n in names)
        if c.get("object_id"):
            o = ent[c["object_id"]]
            mentions = mentions or any(n.lower() in span for n in [o["canonical_name"]] + o.get("aliases", []))
        elif c.get("value") is not None:
            v = c["value"]
            vs = [str(v)]
            if isinstance(v, (int, float)):
                vs += [f"{v:g}", f"{v:,}", str(int(v)) if float(v).is_integer() else f"{v}"]
            mentions = mentions or any(x.lower() in span for x in vs)
        if not mentions:
            bad.append(f"{c['claim_id']}: span mentions neither subject nor value: {span[:60]!r}")
    return Result("02", not bad, f"{len(tables['claims'])} spans inside their source text and mention subject/value" if not bad else f"{len(bad)} bad spans: {bad[:5]}")


def inv03_coverage(tables, **_) -> Result:
    inst = {c.get("truth_claim_id") for c in tables["claims"]}
    facts_missing = [f["fact_id"] for f in tables["facts"] if f["fact_id"] not in inst]
    per_src = {}
    for c in tables["claims"]:
        per_src[c["source_id"]] = per_src.get(c["source_id"], 0) + 1
    docs_missing = [s["source_id"] for s in tables["sources"] if s["doc_type"] not in PRODUCT_ONLY and per_src.get(s["source_id"], 0) == 0]
    ok = not facts_missing and not docs_missing
    return Result("03", ok, "every fact instantiated by >= 1 claim; every intelligence-bearing document yields >= 1 claim" if ok
                  else f"facts without claims: {facts_missing[:5]}; docs without claims: {docs_missing[:5]}")


def inv04_valid_time(tables, **_) -> Result:
    bad = []
    by = {}
    for c in tables["claims"]:
        if c["status"] == "approved":
            by.setdefault((c["subject_id"], c["predicate"]), []).append(c)
    for key, rows in by.items():
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                a0, a1 = date.fromisoformat(a["valid_from"]), (date.fromisoformat(a["valid_to"]) if a.get("valid_to") else date.max)
                b0, b1 = date.fromisoformat(b["valid_from"]), (date.fromisoformat(b["valid_to"]) if b.get("valid_to") else date.max)
                if a0 <= b1 and b0 <= a1 and a.get("truth_claim_id") != b.get("truth_claim_id"):
                    bad.append(f"{a['claim_id']}~{b['claim_id']}")
    # supersession chains acyclic
    nxt = {c["claim_id"]: c.get("supersedes_claim_id") for c in tables["claims"]}
    for start in nxt:
        seen, cur = set(), start
        while cur:
            if cur in seen:
                bad.append(f"cycle at {start}")
                break
            seen.add(cur)
            cur = nxt.get(cur)
    return Result("04", not bad, "no conflicting approved claims overlap in valid time; supersession acyclic" if not bad else f"{bad[:5]}")


def inv05_rule_probabilities(tables, **_) -> Result:
    import json
    groups = {}
    for r in tables["policy_rules"]:
        groups.setdefault((r["strategy_id"], json.dumps(r["condition"], sort_keys=True), r["priority"]), []).append(r["probability"])
    bad = [k for k, ps in groups.items() if abs(sum(ps) - 1.0) > 1e-9]
    return Result("05", not bad, f"{len(groups)} (strategy, condition) groups sum to 1" if not bad else f"bad groups: {bad[:3]}")


def inv06_weights(tables, **_) -> Result:
    w = {}
    for so in tables["strategy_objectives"]:
        w[so["strategy_id"]] = w.get(so["strategy_id"], 0.0) + so["weight"]
    bad = [s for s, t in w.items() if abs(t - 1.0) > 1e-9]
    bad += [om["opponent_model_id"] for om in tables["opponent_models"] if abs(sum(m["probability"] for m in om["distribution"]) - 1.0) > 1e-9]
    missing = [s["strategy_id"] for s in tables["strategies"] if s["strategy_id"] not in w]
    return Result("06", not bad and not missing, "weights and opponent distributions sum to 1" if not (bad or missing) else f"bad: {bad[:3]} missing weights: {missing[:3]}")


def inv07_payoff_coverage(tables, **_) -> Result:
    from eval.engine import objective_order, opponent_dist
    from eval.value import world_bits
    expected = set()
    ulen = {}
    for s in tables["strategies"]:
        ks = {a["index_k"] for a in tables["assumptions"] if a["strategy_id"] in {x["strategy_id"] for x in tables["strategies"] if x["actor_id"] == s["actor_id"] and x["game_id"] == s["game_id"]}}
        K = (max(ks) + 1) if ks else 0
        for osid in opponent_dist(tables, s["opponent_model_id"]):
            for w in world_bits(K):
                expected.add((s["strategy_id"], osid, w))
        ulen[s["strategy_id"]] = len(objective_order(tables, s["game_id"], s["actor_id"]))
    have = [(p["strategy_id"], p["opponent_strategy_id"], p["world"]) for p in tables["payoffs"]]
    dup = len(have) - len(set(have))
    missing = expected - set(have)
    extra = set(have) - expected
    badlen = [p["strategy_id"] for p in tables["payoffs"] if len(p["utility"]) != ulen.get(p["strategy_id"])]
    ok = not missing and not extra and dup == 0 and not badlen
    return Result("07", ok, f"payoffs cover all {len(expected)} (strategy, opponent, world) triples exactly once" if ok
                  else f"missing {len(missing)} extra {len(extra)} dup {dup} bad utility length {badlen[:3]}")


def inv08_dag(tables, **_) -> Result:
    try:
        topological_order([h["he_id"] for h in tables["harmful_events"]], [(e["from_he_id"], e["to_he_id"]) for e in tables["escalation_edges"]])
        return Result("08", True, f"escalation edges ({len(tables['escalation_edges'])}) form a DAG")
    except ValueError as ex:
        return Result("08", False, str(ex))


def inv09_grounding(tables, **_) -> Result:
    keys = {(f["subject_id"], f["predicate"]) for f in tables["facts"]}
    bad = [a["assumption_id"] for a in tables["assumptions"] if (a["subject_id"], a["predicate"]) not in keys]
    return Result("09", not bad, "every assumption's (subject, predicate) has >= 1 fact" if not bad else f"ungrounded: {bad}")


COMPUTED_TOL = 1e-9


def _close(a, b) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        try:
            return abs(float(a) - float(b)) <= COMPUTED_TOL
        except (TypeError, ValueError):
            return False
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_close(a[k], b[k]) for k in a)
    return a == b


def inv10_recomputation(tables, as_of: date, world_version: int, **_) -> Result:
    fresh = recompute(tables, as_of, world_version)
    bad = []
    for t in TABLES:
        if not t.computed:
            continue
        a, b = tables[t.name], fresh[t.name]
        if t.name in ("risk_assessments", "problem_set_assessments", "distinguishability"):
            key = lambda r: tuple(r[c] for c in t.pk)
            am, bm = {key(r): r for r in a}, {key(r): r for r in b}
            if am.keys() != bm.keys():
                bad.append(f"{t.name}: row set differs ({len(am)} vs {len(bm)})")
                continue
            pairs = [(am[k], bm[k]) for k in am]
        else:
            if len(a) != len(b):
                bad.append(f"{t.name}: row count differs")
                continue
            pairs = list(zip(a, b))
        for ra, rb in pairs:
            for col in t.computed:
                if not _close(ra.get(col), rb.get(col)):
                    bad.append(f"{t.name}.{col} pk={[ra.get(c) for c in t.pk]}: stored {str(ra.get(col))[:40]} vs recomputed {str(rb.get(col))[:40]}")
    return Result("10", not bad, "every computed column reproduces from truth to 1e-9" if not bad else f"{len(bad)} mismatches: {bad[:4]}")


def _corpus_violations(tables, dataset_dir: Path, codes: set[str]) -> tuple[dict[str, list], list[str]]:
    acr = style_check.load_acronyms()
    invalid_names = [s["name"] for s in tables["strategies"] if s.get("status") in ("invalid", "infeasible")]
    asm_by_strategy = {}
    for a in tables["assumptions"]:
        asm_by_strategy.setdefault(a["strategy_id"], []).append(a["assumption_id"])
    coa_src = {}
    for s in tables["sources"]:
        if s["doc_type"] == "coa_statement":
            sid = s.get("title", "")
            coa_src[s["source_id"]] = [a for st in tables["strategies"] if st["name"] in sid for a in asm_by_strategy.get(st["strategy_id"], [])]
    out = {}
    negatives = []
    for s in tables["sources"]:
        v = style_check.check_file(Path(dataset_dir) / s["path"], s["doc_type"], acr, invalid_names=invalid_names, assumption_ids=coa_src.get(s["source_id"], []))
        v = [x for x in v if x.code.rstrip("abcL") in codes or x.code in codes]
        if "mixed_scale" in s.get("perturbations", []):
            negatives.append(s["source_id"])
            if not any(x.code == "13" for x in v):
                out[s["source_id"]] = [style_check.Violation(1, "13", "deliberate mixed_scale negative example was NOT caught")]
            continue
        if v:
            out[s["source_id"]] = v
    return out, negatives


def inv11_markings(tables, dataset_dir, **_) -> Result:
    bad, _ = _corpus_violations(tables, dataset_dir, {"11"})
    return Result("11", not bad, f"all {len(tables['sources'])} products carry the markings and no other marking string" if not bad else f"{list(bad.items())[:3]}")


def inv12_likelihood_confidence(tables, dataset_dir, **_) -> Result:
    bad, _ = _corpus_violations(tables, dataset_dir, {"12"})
    return Result("12", not bad, "no sentence mixes a likelihood term with a confidence term" if not bad else f"{list(bad.items())[:3]}")


def inv13_mixed_scale(tables, dataset_dir, **_) -> Result:
    bad, neg = _corpus_violations(tables, dataset_dir, {"13"})
    return Result("13", not bad, f"no product mixes ICD 203 and JRAM vocabularies (deliberate negatives caught: {neg})" if not bad else f"{list(bad.items())[:3]}")


def inv14_risk_statement_slots(tables, **_) -> Result:
    bad = [r["he_id"] for r in tables["risk_assessments"] if parse_risk_statement(r["statement_text"]) is None or len(r["statement_text"].split()) > 90]
    return Result("14", not bad, f"all {len(tables['risk_assessments'])} risk statements match the Fig. 11 slot order and are <= 90 words" if not bad else f"bad: {bad[:5]}")


def inv15_decision_matrix(tables, dataset_dir, **_) -> Result:
    bad = [a["assumption_id"] for a in tables["assumptions"] if not a.get("in_decision_matrix")]
    doc_bad, _ = _corpus_violations(tables, dataset_dir, {"15"})
    ok = not bad and not doc_bad
    return Result("15", ok, "every assumption is in the decision matrix; every COA statement lists its assumptions" if ok else f"not in matrix: {bad[:5]}; docs: {list(doc_bad.items())[:3]}")


def inv16_validity_entries(tables, dataset_dir, **_) -> Result:
    need = {"suitable", "feasible", "acceptable", "distinguishable", "complete"}
    bad = [s["strategy_id"] for s in tables["strategies"] if not s.get("validity") or set(s["validity"]) != need or s.get("status") is None]
    doc_bad, _ = _corpus_violations(tables, dataset_dir, {"16"})
    ok = not bad and not doc_bad
    return Result("16", ok, "every strategy carries the five validity entries and a status; invalid COAs absent from comparison tables" if ok else f"{bad[:5]} {list(doc_bad.items())[:3]}")


def inv17_caution(tables, dataset_dir, **_) -> Result:
    bad, _ = _corpus_violations(tables, dataset_dir, {"17"})
    return Result("17", not bad, "every comparison table is followed by the App. F caution sentence" if not bad else f"{list(bad.items())[:3]}")


def inv18_msr_mr_fields(tables, **_) -> Result:
    bad = []
    for he in tables["harmful_events"]:
        if he["risk_type"] == "MSR" and not (he.get("strategic_value") and he.get("damage_degree")):
            bad.append(he["he_id"])
        if he["risk_type"] == "MR" and not (he.get("risk_subset") and he.get("fig28_row") and he.get("fig28_cell")):
            bad.append(he["he_id"])
    return Result("18", not bad, "MSR rows carry strategic_value/damage_degree; MR rows carry risk_subset/fig28_row" if not bad else f"{bad}")


def inv19_posture_rationale(tables, **_) -> Result:
    bad = [(r["he_id"], r["jsps_horizon"]) for r in tables["risk_assessments"] if r.get("forced_choice_applied") and not r.get("posture_rationale")]
    n = sum(1 for r in tables["risk_assessments"] if r.get("forced_choice_applied"))
    return Result("19", not bad, f"{n} forced-choice assessments all carry posture_rationale" if not bad else f"{bad}")


def inv20_acronyms(tables, dataset_dir, **_) -> Result:
    bad, _ = _corpus_violations(tables, dataset_dir, {"20", "02", "03", "05", "15L"})
    return Result("20", not bad, "acronyms glossary-only, spelled out at first use, listed at the end; paragraph scheme, dates, synonyms and lengths conform" if not bad else f"{[(k, [str(x) for x in v[:2]]) for k, v in list(bad.items())[:3]]}")


ALL: list[Callable[..., Result]] = [inv01_referential_integrity, inv02_spans, inv03_coverage, inv04_valid_time, inv05_rule_probabilities,
                                    inv06_weights, inv07_payoff_coverage, inv08_dag, inv09_grounding, inv10_recomputation, inv11_markings,
                                    inv12_likelihood_confidence, inv13_mixed_scale, inv14_risk_statement_slots, inv15_decision_matrix,
                                    inv16_validity_entries, inv17_caution, inv18_msr_mr_fields, inv19_posture_rationale, inv20_acronyms]


def run_all(tables: dict, dataset_dir: Path, as_of: date, world_version: int, only: set[str] | None = None) -> list[Result]:
    out = []
    for fn in ALL:
        r = fn(tables=tables, dataset_dir=dataset_dir, as_of=as_of, world_version=world_version)
        if only is None or r.id in only:
            out.append(r)
    return out


def schema_load(tables: dict) -> Result:
    """Every row validates against its pydantic model (= its JSON Schema)."""
    bad = []
    for t in TABLES:
        for r in tables[t.name]:
            try:
                t.model(**r)
            except Exception as ex:  # noqa: BLE001
                bad.append(f"{t.name}: {str(ex)[:80]}")
    return Result("schema", not bad, f"all rows of {len(TABLES)} tables validate" if not bad else f"{bad[:3]}")
