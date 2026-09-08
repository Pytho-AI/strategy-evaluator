"""P3: doctrine slots, risk contours, forced choice and an isolated downstream cascade."""
from copy import deepcopy
from test_p2 import theater
from eval.engine import recompute
from gen import validate


def risk_theater():
    from gen import risk
    ctx = theater()
    risk.build(ctx)
    return ctx


def test_risk_gate():
    ctx = risk_theater()
    t = recompute(ctx.tables, ctx.t0, 0)
    assert len(t['harmful_events']) == 9
    assert len(t['risk_assessments']) == 27
    for fn in (validate.inv08_dag, validate.inv14_risk_statement_slots, validate.inv18_msr_mr_fields,
               validate.inv19_posture_rationale):
        result = fn(t)
        assert result.passed, result.detail


def test_cyber_forced_choice_moves_energy_without_local_changes():
    ctx = risk_theater()
    before = recompute(ctx.tables, ctx.t0, 0)
    changed = deepcopy(ctx.tables)
    for c in changed['claims']:
        if (c['subject_id'], c['predicate']) == ('ent_varenia', 'cyber_capacity'):
            c.update(value='extensive', likelihood_icd203='roughly_even_chance')
    after = recompute(changed, ctx.t0, 3)
    old = {(r['he_id'], r['jsps_horizon']): r for r in before['risk_assessments']}
    new = {(r['he_id'], r['jsps_horizon']): r for r in after['risk_assessments']}
    cyber = new['he_05', 'near']
    assert cyber['forced_choice_applied'] and cyber['posture_rationale']
    assert cyber['p_level'] == 'likely'
    assert old['he_04', 'near']['risk_level'] == 'moderate'
    assert new['he_04', 'near']['risk_level'] == 'significant'
