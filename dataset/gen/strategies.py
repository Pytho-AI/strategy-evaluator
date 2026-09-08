"""P2: authored COA inputs. Values, validity and information values are computed later."""
from gen.context import Ctx
from gen import scenario_data as S

# index, subject, predicate, comparison, threshold, proposition, role
ASSUMPTIONS = [
    ('sys_dorne_asm', 'range_km', '<=', 300, 'Dorne-3 range does not reach Port Auberon', 'state'),
    ('ent_varenia', 'mobilization_days', '>=', 45, 'Varenia requires at least forty-five days to mobilize two brigades', 'opponent'),
    ('ent_corvane', 'basing_access', '==', True, 'Corvane grants basing access at Halden', 'state'),
    ('inf_kestrel_lane', 'throughput_per_day', '>=', 80, 'Strait throughput remains at least eighty transits per day', 'transition'),
    ('ent_varenia', 'cyber_capacity', '==', 'limited', 'Varenian cyber capacity against Blue logistics is limited', 'opponent'),
    ('unit_meridian_log_group', 'munitions_stock_days', '>=', 30, 'Blue munitions stocks cover at least thirty days', 'means'),
]
BLUE = [
    ('str_blue_1', 'Anchor', 'maritime presence', 'simultaneous', 'forward reserve at Port Auberon',
     ['unit_tg_kestrel', 'unit_lantern_battery'], [0, 2, 3, 5],
     ['forward_deploy_tg', 'combined_patrol', 'isr_surge', 'air_defense_auberon', 'preposition_stocks', 'basing_negotiation', 'strike_coastal_battery', 'strategic_messaging']),
    ('str_blue_2', 'Lattice', 'distributed denial', 'simultaneous', 'dispersed maritime reserve',
     ['unit_tg_kestrel', 'unit_cyber_protection_team', 'unit_auberon_wing'], [0, 3, 4, 5],
     ['disperse_tg', 'combined_patrol', 'isr_surge', 'cyber_harden', 'air_defense_auberon', 'preposition_stocks', 'strike_coastal_battery', 'strategic_messaging']),
    ('str_blue_3', 'Bulwark', 'delay and reinforcement', 'sequential', 'Halden Brigade held for reinforcement',
     ['unit_halden_brigade', 'unit_ilm_coastal_div'], [1, 2, 5],
     ['hold_corvane', 'combined_patrol', 'isr_surge', 'basing_negotiation', 'reinforce_halden', 'preposition_stocks', 'relief_ops', 'strategic_messaging']),
]
RED = [
    ('str_red_ml', 'Coercive pressure', 'most_likely', 'maritime coercion', ['harass_shipping', 'mobilize', 'info_ops', 'hold']),
    ('str_red_md', 'Strait seizure', 'most_dangerous', 'seize the approaches', ['seize_approaches', 'missile_strike_port', 'mobilize', 'hold']),
    ('str_red_alt', 'Energy coercion', 'alternative', 'energy coercion', ['strike_energy', 'cyber_logistics', 'info_ops', 'hold']),
]


def build(ctx: Ctx) -> None:
    ctx.add('guidance', dict(guidance_id='gd_red_plan', product_type='contingency_plan',
        title='Varenian campaign directive', issuing_role='Varenian commander',
        objective_ids=list(S.RED_WEIGHTS), parent_guidance_id=None, source_id=None))
    for om, actor, distribution in [
        ('om_blue', 'ent_varenia', [('str_red_ml', .55), ('str_red_md', .25), ('str_red_alt', .20)]),
        ('om_red', 'ent_blue', [('str_blue_1', 1/3), ('str_blue_2', 1/3), ('str_blue_3', 1/3)]),
    ]:
        ctx.add('opponent_models', dict(opponent_model_id=om, actor_id=actor,
            distribution=[dict(strategy_id=s, probability=p) for s, p in distribution]))
    for sid, name, effort, sequence, reserve, units, indices, actions in BLUE:
        ctx.add('strategies', dict(strategy_id=sid, game_id='meridian', actor_id='ent_blue', name=name,
            summary=f'{name} uses {effort} to preserve navigation and deter coercion.', echelon='theater_strategic',
            guidance_source='gd_ccp_meridian', mission_who='Joint Task Force Meridian',
            mission_what=f'conducts {effort}', mission_when='from 08 September 2026 through six planning periods',
            mission_where='in the Meridian Sea and Ilmara', mission_why='to deter coercion and preserve freedom of navigation',
            end_state_objective_id='obj_end_state', main_effort=effort, sequencing=sequence,
            task_org=units, reserve_policy=reserve, risk_functional='expected', opponent_model_id='om_blue',
            constraints=['Maintain combined patrols with Ilmara', 'Keep Lantern Battery at Port Auberon'],
            restraints=['No strikes on Varenian territory before strait closure', 'No forces into Sondria']))
        for oid, weight in S.BLUE_WEIGHTS.items():
            ctx.add('strategy_objectives', dict(strategy_id=sid, objective_id=oid, weight=weight))
        for k in indices:
            subject, predicate, op, value, statement, role = ASSUMPTIONS[k]
            ctx.add('assumptions', dict(assumption_id=f'asm_{sid[4:]}_k{k}', strategy_id=sid, index_k=k,
                statement=statement, subject_id=subject, predicate=predicate, tolerance=dict(op=op, value=value),
                role=role, jp50_logical=True, jp50_realistic=k != 1, jp50_essential=True,
                origin='higher_hq' if k == 1 else 'own', in_decision_matrix=True))
        for i, action in enumerate(actions):
            condition = True
            if action == 'strike_coastal_battery':
                condition = dict(var='strait_status', op='==', value='closed')
            elif action == 'reinforce_halden':
                condition = dict(var='corvane_basing', op='==', value='granted')
            elif i != len(actions) - 1:
                condition = dict(var='red_mobilized_brigades', op='==', value=i % 4)
            rule_id = f'rule_{sid[4:]}_{i}'
            dp = f'dp_{sid[4:]}_{i}' if i in (0, 6) else None
            # Duplicate conditions at different periods are disambiguated by the period schedule.
            ctx.add('policy_rules', dict(rule_id=rule_id, strategy_id=sid, priority=i,
                condition=condition, action_id=f'act_blue_{action}', probability=1.0,
                periods=[i % 6 + 1] if i != len(actions)-1 else None, decision_point_id=dp))
            if dp is not None:
                pir = 'pir_01' if i == 0 else ('pir_02' if sid == 'str_blue_3' else 'pir_03')
                ctx.add('decision_points', dict(dp_id=dp, strategy_id=sid, name=f'{name} decision {i+1}',
                    condition=condition, branch_rule_ids=[rule_id], pir_id=pir, latest_period=i % 6 + 1))
                ctx.get('pirs', pir_id=pir)['decision_point_ids'].append(dp)
        for resource, budget in zip(S.RESOURCES, [240, 144, 240, 360, 60]):
            ctx.add('strategy_resources', dict(strategy_id=sid, resource_id=resource[0], budget=budget))
    for sid, name, label, effort, actions in RED:
        ctx.add('strategies', dict(strategy_id=sid, game_id='meridian', actor_id='ent_varenia', name=name,
            summary=f'Varenian {effort}.', echelon='operational', guidance_source='gd_red_plan',
            adversary_coa_label=label, mission_who='Varenian forces', mission_what=f'conduct {effort}',
            mission_when='during the six planning periods', mission_where='in the Meridian region',
            mission_why='to coerce Ilmara into concessions', end_state_objective_id='obj_red_end_state',
            main_effort=effort, sequencing='sequential', task_org=['unit_var_northern_fleet'],
            reserve_policy=f'reserve supports {effort}', risk_functional='expected', opponent_model_id='om_red',
            constraints=['Preserve Varenian forces'], restraints=['Avoid general war']))
        for oid, weight in S.RED_WEIGHTS.items():
            ctx.add('strategy_objectives', dict(strategy_id=sid, objective_id=oid, weight=weight))
        ctx.add('assumptions', dict(assumption_id=f'asm_{sid[4:]}_k0', strategy_id=sid, index_k=0,
            subject_id='unit_meridian_log_group', predicate='munitions_stock_days',
            statement='Blue stocks remain at least thirty days', tolerance=dict(op='>=', value=30),
            role='opponent', jp50_logical=True, jp50_realistic=True, jp50_essential=True, origin='own'))
        for i, action in enumerate(actions):
            ctx.add('policy_rules', dict(rule_id=f'rule_{sid[4:]}_{i}', strategy_id=sid, priority=i,
                condition=True if i == 3 else dict(var='blue_posture', op='==', value=['forward', 'distributed', 'holding'][i]),
                action_id=f'act_red_{action}', probability=1.0))
        for resource, budget in zip(S.RESOURCES, [240, 144, 240, 360, 60]):
            ctx.add('strategy_resources', dict(strategy_id=sid, resource_id=resource[0], budget=budget))
