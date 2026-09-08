"""Render T0 guidance, risk, collection and course-of-action products from computed truth."""
from datetime import date
from eval.engine import recompute
from gen.render_common import product_header, product_footer, fmt_date, locate_span

GUIDANCE_NAMES = {
    'NSS': 'National Security Strategy', 'NDS': 'National Defense Strategy',
    'NMS': 'National Military Strategy', 'JSCP': 'Joint Strategic Campaign Plan',
    'GCP': 'Global Campaign Plan', 'CCP': 'Combatant Command Campaign Plan',
    'contingency_plan': 'contingency plan', 'OPORD': 'operation order',
}


def _text(lines, acronyms=()):
    return product_header() + '\n'.join(lines) + '\n' + product_footer(list(acronyms))


def _date(value):
    return value if isinstance(value, date) else date.fromisoformat(value)


def _source(ctx, doc_type, title, text, author, perturbations):
    source_id = ctx.next_id('src')
    rel = f'corpus/{doc_type}_{source_id[4:]}.md'
    sha = ctx.add_doc(rel, text.replace('{SOURCE_ID}', source_id))
    ctx.add('sources', dict(source_id=source_id, doc_type=doc_type, title=title,
        published_at=ctx.t0, author_org=author, reliability='B', credibility='2',
        real_world=False, path=rel, batch=0, text_sha256=sha, perturbations=perturbations))
    return source_id, rel


def _evidence_sentence(ctx, he_id):
    driver_ids = {d['driver_id'] for d in ctx.tables['risk_drivers'] if d['he_id'] == he_id}
    candidate = []
    for d in ctx.tables['dependencies']:
        if d['kind'] != 'drives' or d['to_id'] != he_id or d['from_type'] != 'claim':
            continue
        c = ctx.get('claims', claim_id=d['from_id'])
        if not c['estimative']:
            candidate.append(c)
    c = candidate[0]
    entity = ctx.get('entities', entity_id=c['subject_id'])['canonical_name']
    value = ctx.get('entities', entity_id=c['object_id'])['canonical_name'] if c.get('object_id') else c['value']
    label = c['predicate'].replace('_', ' ')
    return c, f'{entity} has a reported {label} value of {value}. [src: {{SOURCE_ID}}]'


def build(ctx):
    ctx.tables = recompute(ctx.tables, ctx.t0, 0)
    ctx.computed = True
    objectives = {o['objective_id']: o for o in ctx.tables['objectives']}

    for guidance in ctx.tables['guidance']:
        title = f"Guidance: {GUIDANCE_NAMES[guidance['product_type']]}"
        parent = guidance.get('parent_guidance_id') or 'none'
        stated = [objectives[o]['name'] for o in guidance['objective_ids']]
        lines = [title, f"1. Date. {fmt_date(ctx.t0)}.",
                 f"2. Purpose. {guidance['title']}.",
                 f"3. Direction. This product descends from {parent}.",
                 '4. Objectives. ' + ('; '.join(stated) if stated else 'No new objectives; execute the parent direction.'),
                 '5. Execution. Subordinate plans trace their objectives to this direction.']
        sid, _ = _source(ctx, 'guidance', title, _text(lines), guidance['issuing_role'], ['paraphrase', 'implicit'])
        guidance['source_id'] = sid

    for ps in ctx.tables['problem_sets']:
        title = f"Risk Context Statement: {ps['name']}"
        lines = [title,
            f"1. Context.", f"a. Strategic context. {ps['strategic_context']}",
            'b. Time horizons. Near-term (0-3 years), mid-term (2-7 years), and long-term (5-15 years).',
            f"c. Scope and boundaries. {ps['scope_and_boundaries']}",
            f"d. Risk owner. {ps['risk_owner_role']}.",
            f"e. Assumptions, constraints, and dependencies. {ps['assumptions_and_constraints']}",
            f"f. Expected outputs and tolerance. {ps['expected_outputs']} {ps['tolerance_statement']}"]
        sid, _ = _source(ctx, 'risk_context', title, _text(lines), ps['risk_owner_role'], ['paraphrase', 'alias'])
        ps['risk_context_source_id'] = sid

    for pir in ctx.tables['pirs']:
        reqs = [r for r in ctx.tables['collection_requirements'] if r['pir_id'] == pir['pir_id']]
        route_names = {
            'JIOC': 'joint intelligence operations center (JIOC)',
            'JCMB': 'joint collection management board (JCMB)',
            'component J-2': 'component Joint Staff Directorate for Intelligence (J-2)',
        }
        route_acronyms = list(dict.fromkeys(code for r in reqs for code in ('JIOC', 'JCMB', 'J-2') if code in r['routing']))
        title = f"Collection Plan: Commander Priority {pir['priority_rank']}"
        lines = [title, f"1. Period covered. From {fmt_date(ctx.t0)} to {fmt_date(_date(max(r['ltiov'] for r in reqs)))}.",
                 f"2. Priority intelligence requirement. {pir['statement']}",
                 '3. Collection plan.',
                 '| Priority or Other Intelligence Requirements | Indications | Specific Information Sought | Assets to Be Tasked/Resources to Be Required | Place and Time to Report | Remarks |',
                 '|---|---|---|---|---|---|']
        for r in reqs:
            remarks = f"{r['gap_type']}; {r['rfi_disposition']}; rank {r['jipcl_rank']}"
            lines.append(f"| {r['req_id']}: {r['eei']} | {'; '.join(r['indicators'])} | {r['sir']} | {route_names[r['routing']]} | Report to {pir['commander_role']} by {fmt_date(_date(r['ltiov']))} | {remarks} |")
        lines.append('4. Reporting instructions. Report changes immediately and cite the source and observation time.')
        _source(ctx, 'collection_plan', title, _text(lines, route_acronyms), 'the joint collection management board', ['paraphrase', 'implicit'])

    effects = [o for o in ctx.tables['objectives'] if o['kind'] == 'effect']
    blue = [s for s in ctx.tables['strategies'] if s['actor_id'] == 'ent_blue']
    for strategy in blue:
        title = f"Course of Action Statement: {strategy['name']}"
        assumptions = [a for a in ctx.tables['assumptions'] if a['strategy_id'] == strategy['strategy_id']]
        rules = [r for r in ctx.tables['policy_rules'] if r['strategy_id'] == strategy['strategy_id']]
        end = objectives[strategy['end_state_objective_id']]['name']
        lines = [title,
            f"1. Mission. {strategy['mission_who']} {strategy['mission_what']} {strategy['mission_when']} {strategy['mission_where']} {strategy['mission_why']}.",
            f"2. Military end state. {end}.",
            '3. Objectives. ' + '; '.join(objectives[x['objective_id']]['name'] for x in ctx.tables['strategy_objectives'] if x['strategy_id'] == strategy['strategy_id']),
            '4. Effects. ' + '; '.join(e['name'] for e in effects),
            '5. Validity tests.', '| Test | Result | Evidence |', '|---|---|---|']
        for name, result in strategy['validity'].items():
            evidence_text = result['evidence'].replace("COA's", "course of action's").replace('COA', 'course of action')
            lines.append(f"| {name.title()} | {'Pass' if result['pass'] else 'Fail'} | {evidence_text} |")
        lines.extend(['6. Decision matrix assumptions.'] +
                     [f"{i + 1}. {a['assumption_id']}: {a['statement']} Status: {a['status']}." for i, a in enumerate(assumptions)])
        lines.extend(['7. Constraints.'] + [f"{i + 1}. Must do: {x}." for i, x in enumerate(strategy['constraints'])])
        lines.extend(['8. Restraints.'] + [f"{i + 1}. Cannot do: {x}." for i, x in enumerate(strategy['restraints'])])
        lines.append('9. Ways and decision points. ' + '; '.join(f"{r['rule_id']} uses {r['action_id']}" for r in rules))
        _source(ctx, 'coa_statement', title, _text(lines), 'the supported combatant command J-5', ['paraphrase', 'implicit'])

    valid = [s for s in blue if s['status'] == 'valid']
    title = 'Course of Action Weighted Numerical Comparison'
    lines = [title, '1. Weighted numerical comparison.']
    for strategy in valid:
        lines.extend([f"2. {strategy['name']}.", '| Criterion | Weight | Rating | Product | Course of action |', '|---|---:|---:|---:|---|'])
        for row in [x for x in ctx.tables['strategy_objectives'] if x['strategy_id'] == strategy['strategy_id']]:
            lines.append(f"| {objectives[row['objective_id']]['name']} | {row['weight']:.2f} | {row['rating_1_to_3']} | {row['weight'] * row['rating_1_to_3']:.2f} | {strategy['name']} |")
        lines.append(f"Common numerical basis: value {strategy['value']:.3f}; uncertainty interval {strategy['value_ci'][0]:.3f} to {strategy['value_ci'][1]:.3f}.")
    from eval.style_check import CAUTION
    lines.extend(['3. Caution.', CAUTION])
    _source(ctx, 'coa_statement', title, _text(lines), 'the supported combatant command J-5', ['paraphrase', 'implicit'])

    for he in ctx.tables['harmful_events']:
        title = f"Risk Assessment: {he['he_id']}"
        rows = [r for r in ctx.tables['risk_assessments'] if r['he_id'] == he['he_id']]
        claim, evidence = _evidence_sentence(ctx, he['he_id'])
        lines = [title, f"1. Purpose. Assess risk from {he['statement']} as of {fmt_date(ctx.t0)}.",
                 f"2. Evidence. {evidence}", '3. Risk statements.']
        lines.extend(r['statement_text'] for r in rows)
        if he.get('beneficial_statement'):
            from eval.jram import render_opportunity_statement
            r = rows[0]
            lines.extend(['4. Opportunity.', render_opportunity_statement(r['p_level'], he['beneficial_statement'],
                'near', he['key_actions'], r['c_level'], objectives[he['thing_of_value_id']]['name'],
                r['risk_level'], he['risk_type'], he.get('risk_subset'))])
        text = _text(lines)
        sid, rel = _source(ctx, 'assessment', title, text, 'the supported combatant command J-2', ['paraphrase', 'implicit'])
        rendered = ctx.docs[rel]
        sentence = evidence.replace('{SOURCE_ID}', sid)
        start, end = locate_span(rendered, sentence)
        copied = {k: claim.get(k) for k in ('subject_id', 'predicate', 'object_id', 'value', 'value_type', 'unit',
                  'valid_from', 'valid_to', 'estimative', 'likelihood_icd203', 'confidence_icd203', 'confidence', 'truth_claim_id')}
        ctx.add('claims', dict(claim_id=ctx.next_id('clm'), source_id=sid, span_start=start, span_end=end,
            asserted_at=ctx.t0, status='approved', supersedes_claim_id=None, likelihood_surface_term=None, **copied))
