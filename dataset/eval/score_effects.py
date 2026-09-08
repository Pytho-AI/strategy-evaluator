"""Compare application effects after an inject with its manifest's computed effects."""


def _set(rows, keys):
    return {tuple(row.get(k) for k in keys) for row in rows}


def _exact(expected, actual, key):
    return 1.0 if _set(expected.get(key, []), tuple(sorted(set().union(*(r.keys() for r in expected.get(key, []) or [{}]))))) == \
                  _set(actual.get(key, []), tuple(sorted(set().union(*(r.keys() for r in actual.get(key, []) or [{}]))))) else 0.0


def _spearman(expected, actual):
    common = [x for x in expected if x in actual]
    if not common:
        return 1.0 if expected == actual else 0.0
    if len(common) == 1:
        return 1.0
    a = {x: i for i, x in enumerate(expected)}
    b = {x: i for i, x in enumerate(actual)}
    n = len(common)
    return round(1 - 6 * sum((a[x] - b[x]) ** 2 for x in common) / (n * (n * n - 1)), 6)


def score_effects(expected, actual):
    keys = ['assumptions_changed', 'strategies_restated', 'requirements_closed', 'problem_sets_moved',
            'risk_assessments_changed', 'validity_changed', 'jipcl_changed']
    metrics = {f'{key}_exact': _exact(expected, actual, key) for key in keys}
    metrics['strategy_rank_spearman'] = _spearman(expected.get('ranking_after', []), actual.get('ranking_after', []))
    expected_risk = {(r['he_id'], r['horizon']): r for r in expected.get('risk_assessments_changed', [])}
    actual_risk = {(r['he_id'], r['horizon']): r for r in actual.get('risk_assessments_changed', [])}
    pillar5 = []
    for key, row in expected_risk.items():
        observed = actual_risk.get(key, {}).get('p_after')
        direction = 'missing' if observed is None else ('equal' if abs(observed - row['p_after']) <= 1e-9 else
                    ('overestimated' if row['p_after'] > observed else 'underestimated'))
        pillar5.append({'he_id': key[0], 'horizon': key[1], 'expected_probability': row['p_after'],
                        'observed_probability': observed, 'assessment': direction})
    metrics['pillar5'] = pillar5
    numeric = [value for value in metrics.values() if isinstance(value, float)]
    metrics['overall'] = round(sum(numeric) / len(numeric), 6)
    return metrics
