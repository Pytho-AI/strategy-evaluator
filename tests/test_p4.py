"""P4: rendered corpus and doctrinal products; P5 collection inputs."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DS = ROOT / 'dataset'
sys.path.insert(0, str(DS))


def generated(tmp_path):
    from gen.__main__ import generate
    out = tmp_path / 'dataset'
    out.mkdir()
    return generate(20260908, out)


def test_collection_and_product_gate(tmp_path):
    from eval import style_check
    from gen import validate
    ctx = generated(tmp_path)
    assert 50 <= len([s for s in ctx.tables['sources'] if s['batch'] == 0]) <= 75
    t0_requirements = [r for r in ctx.tables['collection_requirements'] if r['created_at'] <= '2026-09-08']
    assert len(t0_requirements) == 6
    top = min(t0_requirements, key=lambda r: r['jipcl_rank'] or 999)
    assert top['req_id'] == 'req_01'
    assert {s['doc_type'] for s in ctx.tables['sources']} >= {
        'risk_context', 'collection_plan', 'coa_statement', 'guidance'}
    for fn in (validate.inv02_spans, validate.inv03_coverage, validate.inv04_valid_time,
               validate.inv11_markings,
               validate.inv12_likelihood_confidence, validate.inv13_mixed_scale,
               validate.inv14_risk_statement_slots, validate.inv15_decision_matrix,
               validate.inv16_validity_entries, validate.inv17_caution,
               validate.inv20_acronyms):
        result = fn(ctx.tables, dataset_dir=ctx.dataset_dir)
        assert result.passed, f'{result.id}: {result.detail}'
    acronyms = style_check.load_acronyms()
    for source in ctx.tables['sources']:
        violations = style_check.check_file(ctx.dataset_dir / source['path'], source['doc_type'], acronyms)
        if 'mixed_scale' in source['perturbations']:
            assert any(v.code == '13' for v in violations)
            violations = [v for v in violations if v.code != '13']
        assert not violations, (source['source_id'], [str(v) for v in violations])
    facts = {fact['fact_id']: fact for fact in ctx.tables['facts']}
    assert all(
        claim.get('valid_to') == facts[claim['truth_claim_id']]['valid_to']
        for claim in ctx.tables['claims']
        if claim.get('truth_claim_id') and facts[claim['truth_claim_id']].get('valid_to')
    )


def test_perturbation_coverage(tmp_path):
    ctx = generated(tmp_path)
    t0 = [s for s in ctx.tables['sources'] if s['batch'] == 0]
    covered = [s for s in t0 if len(s['perturbations']) >= 2]
    assert len(covered) / len(t0) >= .60
