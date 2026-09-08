"""P2: finite worlds, meaningful assumptions, validity and the first demo beat."""
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dataset'))

from gen.context import Ctx
from eval.engine import recompute, ranking


def theater():
    from gen import scaffold, facts, plan_docs, render, strategies, payoffs, graph
    ctx = Ctx(seed=20260908)
    for module in (scaffold, facts, plan_docs, render, strategies, payoffs, graph):
        module.build(ctx)
    return ctx


def test_theater_strategy_gate():
    from gen import validate
    ctx = theater()
    t = recompute(ctx.tables, ctx.t0, 0)
    for fn in (validate.inv05_rule_probabilities, validate.inv06_weights,
               validate.inv07_payoff_coverage, validate.inv09_grounding):
        result = fn(t)
        assert result.passed, result.detail
    blue = [s for s in t['strategies'] if s['actor_id'] == 'ent_blue']
    assert len(blue) == 3
    assert all(s['status'] == 'valid' for s in blue), [(s['name'], s['validity']) for s in blue]
    assert ranking(t, 'meridian', 'ent_blue')[0] == 'str_blue_1'
    assert len({a['index_k'] for a in t['assumptions'] if a['evpi'] > 0.001}) >= 2
    assert sum(not a['jp50_realistic'] for a in t['assumptions']) == 1
    assert {p['world'] for p in t['payoffs'] if p['strategy_id'] == 'str_blue_1'} == {
        format(i, '06b') for i in range(64)}


def test_batch_one_changes_value_ranking_and_acceptability():
    ctx = theater()
    before = recompute(ctx.tables, ctx.t0, 0)
    changed = deepcopy(ctx.tables)
    for c in changed['claims']:
        if (c['subject_id'], c['predicate']) == ('sys_dorne_asm', 'range_km'):
            c['value'] = 340
    after = recompute(changed, ctx.t0 + timedelta(days=20), 1)
    old = {s['strategy_id']: s for s in before['strategies']}
    new = {s['strategy_id']: s for s in after['strategies']}
    assert old['str_blue_1']['validity']['acceptable']['pass']
    assert not new['str_blue_1']['validity']['acceptable']['pass']
    assert old['str_blue_1']['value'] - new['str_blue_1']['value'] > 0.2
    assert ranking(after, 'meridian', 'ent_blue')[0] == 'str_blue_2'
