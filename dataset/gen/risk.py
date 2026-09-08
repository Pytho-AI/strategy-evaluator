"""P3: scenario risk inputs from scenario.md §§9–11; calculations live in eval/jram.py."""
from gen.graph import claim_for, edge

PROBLEMS = [
    ('chokepoint', 'Maritime chokepoint', ['obj_navigation', 'obj_preserve_force'],
     'Freedom of navigation and protection of the task group support campaign and national military objectives.',
     'Kestrel Strait, Southern Passage and Port Auberon; linked to energy and displacement.',
     'Range and throughput assumptions apply. Maintain combined patrols with Ilmara.',
     'Accept Moderate trending down risk to the task group in the near-term to protect navigation in the mid-term.'),
    ('energy', 'Energy infrastructure', ['obj_preserve_force'],
     'Ilmaran energy supply supports partner security and Blue sustainment.',
     'Aldis terminal, Veyra station and grid control; linked to cyber and maritime access.',
     'Munitions availability and power supply underpin sustainment.',
     'Accept Moderate risk to partner supply in the near-term; Significant sustainment risk requires mitigation.'),
    ('cyber', 'Cyber', ['obj_preserve_force'],
     'Logistics and grid networks sustain campaign operations.',
     'Blue logistics and Ilmaran grid control networks; linked to energy supply.',
     'The limited cyber-capacity assumption requires validation. Preserve logistics continuity.',
     'Accept Moderate network risk in the near-term; Significant sustainment risk requires mitigation.'),
    ('humanitarian', 'Humanitarian', ['obj_limit_escalation'],
     'Civilian protection and Blue readiness support the campaign end state.',
     'Ravel Crossing and Sondrian camps; linked to strait closure and mobilization.',
     'Mobilization and displacement assumptions apply. No Blue forces enter Sondria.',
     'Accept Moderate diversion risk in the near-term to protect civilians.'),
]
# event, problem, harmful phrase, value, probability, MSR strategic value/damage OR MR subset/row/cell
EVENTS = [
    ('he_01', 'chokepoint', 'Varenia closes the Kestrel Strait', 'obj_navigation', .20, 'MSR', 'ally_global', 'catastrophic'),
    ('he_02', 'chokepoint', 'Task Group Kestrel suffers coastal missile losses', 'obj_preserve_force', .15, 'MR', 'operational', 'Achieve Objectives (CCMD Daily Ops)', 'major'),
    ('he_03', 'energy', 'Varenia strikes or sabotages Ilmaran energy infrastructure', 'obj_preserve_force', .12, 'MSR', 'partner_regional', 'catastrophic'),
    ('he_04', 'energy', 'a blackout disrupts Blue sustainment at Port Auberon', 'obj_preserve_force', .10, 'MR', 'projected_mission', 'Resources Meet Required Timelines', 'major'),
    ('he_05', 'cyber', 'Varenia disrupts the Blue logistics network', 'obj_preserve_force', .12, 'MR', 'force_management', 'Meet CCDR Requirements (Contingency Sourcing)', 'major'),
    ('he_06', 'cyber', 'Varenia compromises Ilmaran grid control', 'obj_preserve_force', .15, 'MSR', 'partner_regional', 'considerable'),
    ('he_07', 'humanitarian', 'displacement overwhelms the Sondrian camps', 'obj_limit_escalation', .15, 'MSR', 'other_local', 'catastrophic'),
    ('he_08', 'humanitarian', 'relief operations divert Blue forces from their primary mission', 'obj_limit_escalation', .10, 'MR', 'operational', 'Achieve Objectives (CCMD Daily Ops)', 'modest'),
    ('he_09', 'chokepoint', 'combined patrols fail to sustain daily transits', 'obj_navigation', .15, 'MR', 'operational', 'Partnerships', 'modest'),
]
# event, subject, predicate, operator, threshold, delta, kind, locus, label, horizons
DRIVERS = [
    (1, 'sys_dorne_asm', 'range_km', '>=', 300, .20, 'accessibility', 'external', 'missile reach', None),
    (1, 'ent_varenia', 'mobilized_brigades', '>=', 2, .15, 'response', 'external', 'mobilized brigades', None),
    (1, 'ent_varenia', 'intent', '==', 'coercive', .05, 'frequency', 'external', 'coercive intent', None),
    (1, 'sys_dorne_asm', 'count', '>=', 16, .10, 'accessibility', 'external', 'projected launcher growth', ['mid', 'long']),
    (2, 'sys_dorne_asm', 'range_km', '>=', 300, .25, 'accessibility', 'external', 'missile reach', None),
    (2, 'unit_tg_kestrel', 'posture_state', '==', 'vulnerable', .15, 'vulnerability', 'internal', 'exposed posture', None),
    (2, 'sys_vigil_frigate', 'readiness', '<', .7, .10, 'resilience', 'internal', 'reduced ship readiness', None),
    (2, 'inf_dorne_radar', 'status', '==', 'operational', .05, 'recognition', 'external', 'coastal radar coverage', None),
    (3, 'sys_serath_lrs', 'count', '>=', 10, .10, 'accessibility', 'external', 'available strike systems', None),
    (3, 'ent_varenia', 'intent', '==', 'coercive', .08, 'frequency', 'external', 'coercive intent', None),
    (3, 'inf_veyra_station', 'status', '==', 'degraded', .10, 'vulnerability', 'external', 'station degradation', None),
    (3, 'sys_serath_lrs', 'count', '>=', 20, .10, 'accessibility', 'external', 'projected strike growth', ['long']),
    (4, 'inf_veyra_station', 'outage_hours', '>=', 48, .20, 'impact', 'external', 'extended outages', None),
    (4, 'inf_ilmara_grid_control', 'posture_state', '==', 'unmitigated', .10, 'vulnerability', 'external', 'unmitigated grid exposure', None),
    (4, 'inf_aldis_terminal', 'status', '==', 'degraded', .10, 'criticality', 'external', 'fuel terminal degradation', None),
    (5, 'ent_varenia', 'cyber_capacity', '==', 'extensive', .30, 'accessibility', 'external', 'extensive cyber capacity', None),
    (5, 'inf_blue_logistics_network', 'posture_state', '==', 'unmitigated', .10, 'vulnerability', 'internal', 'unmitigated logistics exposure', None),
    (5, 'unit_var_directorate_nine', 'intent', '==', 'coercive', .05, 'frequency', 'external', 'coercive network activity', None),
    (6, 'ent_varenia', 'cyber_capacity', '==', 'extensive', .20, 'accessibility', 'external', 'extensive cyber capacity', None),
    (6, 'inf_ilmara_grid_control', 'posture_state', '==', 'unmitigated', .10, 'vulnerability', 'external', 'unmitigated grid exposure', None),
    (7, 'ent_sondria', 'displaced_persons', '>=', 20000, .25, 'impact', 'external', 'camp demand', None),
    (7, 'ent_varenia', 'mobilized_brigades', '>=', 2, .10, 'response', 'external', 'mobilization pressure', None),
    (7, 'unit_son_border_guard', 'readiness', '<', .5, .10, 'resilience', 'external', 'border guard readiness', None),
    (8, 'ent_sondria', 'displaced_persons', '>=', 20000, .25, 'response', 'external', 'relief demand', None),
    (8, 'unit_halden_brigade', 'readiness', '<', .75, .10, 'resilience', 'internal', 'brigade readiness', None),
    (9, 'unit_ilm_patrol_sqn', 'readiness', '<', .7, .10, 'resilience', 'external', 'partner patrol readiness', None),
    (9, 'unit_ilm_patrol_sqn', 'status', '==', 'operational', -.05, 'resources', 'external', 'operational partner patrols', None),
]
ESCALATION = [(2, 1, .5, 'Missile losses precede strait closure'), (1, 7, .4, 'Closure drives displacement'),
              (7, 8, .6, 'Displacement diverts Blue forces'), (6, 3, .3, 'Grid compromise enables sabotage'),
              (3, 4, .6, 'Energy strikes cause a blackout'), (5, 4, .5, 'Network disruption degrades sustainment')]


def build(ctx):
    for key, name, values, strategic, scope, assumptions, tolerance in PROBLEMS:
        ctx.add('problem_sets', dict(problem_set_id=f'ps_{key}', entity_id=f'ent_ps_{key}', name=name,
            tier=0, thing_of_value_ids=values, risk_owner_role='the supported combatant commander',
            strategic_context=strategic, scope_and_boundaries=scope, assumptions_and_constraints=assumptions,
            tolerance_statement=tolerance, expected_outputs='Risk statements, mitigations and collection priorities inform the decision.'))
    for hid, ps, statement, value, base, typ, *basis in EVENTS:
        row = dict(he_id=hid, problem_set_id=f'ps_{ps}', statement=statement, thing_of_value_id=value,
            base_p=base, risk_type=typ, condition='posture',
            posture_subject_ids=['inf_blue_logistics_network', 'unit_cyber_protection_team'] if ps == 'cyber'
            else ['unit_tg_kestrel', 'unit_lantern_battery'])
        if typ == 'MSR':
            row.update(strategic_value=basis[0], damage_degree=basis[1])
        else:
            row.update(risk_subset=basis[0], fig28_row=basis[1], fig28_cell=basis[2])
        if hid == 'he_01':
            row['beneficial_counterpart_he_id'] = 'he_09'
        if hid == 'he_09':
            row.update(beneficial_statement='combined patrols sustain eighty daily transits',
                       key_actions='combined patrol rotations and shared maritime surveillance')
        ctx.add('harmful_events', row)
        ctx.add('risk_sources', dict(rs_id=f'rs_{hid[3:]}', he_id=hid,
            source_kind='hazard' if ps == 'humanitarian' else 'threat',
            entity_id='loc_sondria_camps' if ps == 'humanitarian' else 'ent_varenia',
            description='Scenario source of this harmful event.'))
    for n, subject, predicate, op, value, delta, kind, locus, label, horizons in DRIVERS:
        hid = f'he_{n:02d}'
        ctx.add('risk_drivers', dict(driver_id=ctx.next_id('rd'), he_id=hid, claim_subject_id=subject,
            claim_predicate=predicate, op=op, value=value, delta=delta, driver_kind=kind,
            locus=locus, label=label, horizons=horizons if horizons is not None else ['near', 'mid', 'long']))
        c = claim_for(ctx, subject, predicate)
        if c is not None:
            edge(ctx, 'claim', c['claim_id'], 'harmful_event', hid, 'drives', label, [c['claim_id']])
    for a, b, lift, mechanism in ESCALATION:
        c = claim_for(ctx, 'ent_varenia', 'intent')
        ctx.add('escalation_edges', dict(edge_id=ctx.next_id('ee'), from_he_id=f'he_{a:02d}',
            to_he_id=f'he_{b:02d}', lift=lift, mechanism=mechanism, evidence_claim_ids=[c['claim_id']]))
        edge(ctx, 'harmful_event', f'he_{a:02d}', 'harmful_event', f'he_{b:02d}', 'escalates', mechanism, [c['claim_id']])
