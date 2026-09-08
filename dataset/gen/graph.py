"""Typed grounding and action-to-effect-to-objective dependency edges."""


def claim_for(ctx, subject, predicate):
    rows = [c for c in ctx.tables['claims'] if (c['subject_id'], c['predicate']) == (subject, predicate)]
    if not rows:
        return None
    return max(rows, key=lambda c: (c['status'] == 'approved', c['valid_from'], c['asserted_at']))


def edge(ctx, from_type, from_id, to_type, to_id, kind, mechanism, evidence=()):
    row = ctx.add('dependencies', dict(edge_id=ctx.next_id('dep'), from_type=from_type, from_id=from_id,
        to_type=to_type, to_id=to_id, kind=kind, weight=1.0, mechanism=mechanism, evidence_claim_ids=list(evidence)))
    return row['edge_id']


def build(ctx):
    for a in ctx.tables['assumptions']:
        c = claim_for(ctx, a['subject_id'], a['predicate'])
        if c is not None:
            edge(ctx, 'claim', c['claim_id'], 'assumption', a['assumption_id'], 'grounds',
                 'The sourced proposition is tested against the planning assumption.', [c['claim_id']])
        edge(ctx, 'assumption', a['assumption_id'], 'strategy', a['strategy_id'], 'requires',
             'This course of action depends on the planning assumption.')
    paths = [
        ('combined_patrol', 'unit_ilm_patrol_sqn', 'readiness', 'obj_eff_partner_integration', 'obj_deter', 'obj_nms_deter_partners'),
        ('combined_patrol', 'inf_kestrel_lane', 'throughput_per_day', 'obj_eff_transits', 'obj_navigation', 'obj_nms_commons'),
        ('preposition_stocks', 'unit_meridian_log_group', 'munitions_stock_days', 'obj_eff_sustainment', 'obj_preserve_force', 'obj_nms_deter_partners'),
        ('strategic_messaging', 'ent_sondria', 'displaced_persons', 'obj_eff_civil', 'obj_limit_escalation', 'obj_nms_deter_partners'),
    ]
    for s in ctx.tables['strategies']:
        if s['game_id'] != 'meridian':
            continue
        chain = []
        if s['actor_id'] == 'ent_blue':
            for action, subject, predicate, effect, objective, national in paths:
                c = claim_for(ctx, subject, predicate)
                cid = c['claim_id']
                chain.append(edge(ctx, 'action', f'act_blue_{action}', 'claim', cid, 'enables', 'The action sustains the observed condition.', [cid]))
                chain.append(edge(ctx, 'claim', cid, 'objective', effect, 'supports', 'The observed condition supports the planned effect.', [cid]))
                chain.append(edge(ctx, 'objective', effect, 'objective', objective, 'supports', 'The effect contributes to the campaign objective.'))
                chain.append(edge(ctx, 'objective', objective, 'objective', 'obj_end_state', 'supports', 'The objective contributes to the military end state.'))
                chain.append(edge(ctx, 'objective', objective, 'objective', national, 'supports', 'The campaign objective supports national military guidance.'))
        else:
            c = claim_for(ctx, 'unit_var_northern_fleet', 'readiness')
            action = next(r['action_id'] for r in ctx.tables['policy_rules'] if r['strategy_id'] == s['strategy_id'])
            chain.append(edge(ctx, 'action', action, 'claim', c['claim_id'], 'enables', 'The action uses available Varenian forces.', [c['claim_id']]))
            for oid in ('obj_red_coerce', 'obj_red_preserve'):
                chain.append(edge(ctx, 'claim', c['claim_id'], 'objective', oid, 'supports', 'Available forces support this objective.', [c['claim_id']]))
                chain.append(edge(ctx, 'objective', oid, 'objective', 'obj_red_end_state', 'supports', 'The objective supports the end state.'))
        s['theory_of_victory'] = chain
        evidence = [ctx.get('dependencies', edge_id=e)['from_id'] for e in chain
                    if ctx.get('dependencies', edge_id=e)['from_type'] == 'claim']
        for rule in ctx.tables['policy_rules']:
            if rule['strategy_id'] == s['strategy_id']:
                rule['rationale_claim_ids'] = list(dict.fromkeys(evidence))
